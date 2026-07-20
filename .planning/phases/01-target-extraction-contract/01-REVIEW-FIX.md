---
phase: 01-target-extraction-contract
fixed_at: 2026-07-20T01:45:00Z
review_path: .planning/phases/01-target-extraction-contract/01-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 01: Code Review Fix Report

**Fixed at:** 2026-07-20T01:45:00Z
**Source review:** .planning/phases/01-target-extraction-contract/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 7 (2 Critical + 5 Warning; `fix_scope: critical_warning`)
- Fixed: 7
- Skipped: 0

IN-01 and IN-02 (Info tier) were intentionally excluded — out of scope for this fix pass.

## Fixed Issues

### CR-01: `check_targets.py`'s entire validation contract is `assert`-based and is silently disabled under `python -O`

**Files modified:** `scripts/check_targets.py`
**Commit:** `9ddf9f6`
**Applied fix:** Added a `require(condition, message)` helper that always raises `ValueError`, independent of optimization flags, and replaced every `assert` in `check_track()` and `main()` with `require(...)`.
**Verification:** Reproduced the review's exact scenario (four corrupted `.npz` artifacts with `y_lower_mm > y_upper_mm`) and confirmed `require(...)` now raises `ValueError` under both normal Python and `python -O` — the checker no longer fails open under optimized execution. Also validated against the real, freshly-generated pipeline output for all four tracks under `-O` (`ALL CHECKS PASSED`, exit 0, on genuinely valid data).

### CR-02: A pipeline run that fails partway leaves a silently mixed generation of stale and fresh artifacts, and `check_targets.py` cannot detect it

**Files modified:** `scripts/run_target_extraction.py`, `scripts/check_targets.py`, `tests/test_run_target_extraction.py`
**Commit:** `f8dcf01`
**Applied fix:** `run_pipeline()` now writes every `.npz`/`.json`/QA `.png` into a fresh, per-run staging directory (`processed_data/.targets-staging-<run-id>/`) instead of the live `processed_data/targets/`. A `manifest.json` (run ID, UTC timestamp, track ID set, and a SHA-256 digest of `extraction_params()`) is written into the staging directory alongside `extraction_params.json`. Only after all tracks succeed *and* the final `data/raw/` integrity audit passes is the staging directory atomically published over the live `targets/` directory (`publish_staging_dir`, using a rename-swap-cleanup pattern). Any run that fails partway (track error, raw-mutation detection, or an unavailable final audit snapshot) discards its staging directory via `shutil.rmtree` and never touches the live directory, so the live tree can no longer contain a mix of generations. `check_targets.py`'s `main()` now requires `manifest.json` to exist and verifies its `extraction_params_sha256` and `track_ids` match the currently persisted parameters/expected track set, rejecting any output directory lacking a manifest or with a manifest not tied to the current run.
**Verification:** Extended `tests/test_run_target_extraction.py`'s `clean_stub` and three failure-path tests to assert the new staging/publish contract (staging directory shape passed to track runners, no leftover staging directories after a successful publish, and no live `targets/` directory created at all after any failure path). Ran the full existing `tests/test_run_target_extraction.py` and `tests/test_targets.py` suites (both pass). Additionally reproduced the review's exact "generation A / generation B partial failure" scenario directly against the real `run_pipeline()` with stub track runners — confirmed all four tracks remain consistently generation A after a simulated mid-run failure, with zero leftover staging directories. Also ran the real end-to-end pipeline (`scripts/run_target_extraction.py --project_dir .`) against the actual raw height-map data for all four tracks, followed by `scripts/check_targets.py --project_dir .` (including under `python -O`) — both passed cleanly against the manifest-gated output.

### WR-01: `check_targets.py` does not require `NaN` (as opposed to any other non-finite value) in invalid slots

**Files modified:** `scripts/check_targets.py`
**Commit:** `09e6ff2`
**Applied fix:** Added an explicit `np.isnan(values[~valid_mask]).all()` check (via `require`) for `w_mm`, `y_upper_mm`, and `y_lower_mm`, as suggested in the review.
**Verification:** Reproduced the review's scenario (`+inf` in invalid slots instead of `NaN`) and confirmed `check_track` now correctly raises `ValueError` identifying the offending key. Full test suites still pass.

### WR-02: The no-per-track-tuning structural guard only catches a narrow syntactic pattern

**Files modified:** `tests/test_targets.py`
**Commit:** `21d0f7e`
**Applied fix:** Kept the existing regex-based structural guard and added `test_track_id_does_not_affect_numeric_output`, a behavioral test (per the review's Option 1) that monkeypatches `targets.load_wyko_asc` to return identical synthetic height-map data for two different `track_id`s, calls `extract_track_targets` for both, and requires bit-identical numeric output across every array field (`x_grid_mm`, `w_mm`, `y_upper_mm`, `y_lower_mm`, `valid_mask`, `Z_mm`, `Zd_mm`, `x_actual_mm`, `y_mm`). This catches track-dependent parameterizations that dodge the regex (e.g. `PARAMS_BY_TRACK[track_id]`, `match track_id:`), not just the literal syntactic pattern.
**Verification:** New test passes against current code; full `tests/test_targets.py` suite passes (15 tests).

### WR-03: `TARGET_GRID_STEP_MM` is duplicated in `run_target_extraction.py` instead of being sourced from `targets.py`

**Files modified:** `scripts/run_target_extraction.py`
**Commit:** `22fc0e5`
**Applied fix:** `TARGET_GRID_STEP_MM = extraction_params()["TARGET_GRID_STEP_MM"]` replaces the independent literal `0.2`, as specified in the review's fix.
**Verification:** Confirmed `runner.TARGET_GRID_STEP_MM == 0.2` post-fix; `tests/test_run_target_extraction.py` suite still passes.

### WR-04: `print_results` and the `TRACK_POWER_W`/`TRACK_IDS` tables are duplicated verbatim across `run_target_extraction.py` and `check_targets.py`

**Files modified:** `src/targets.py`, `scripts/run_target_extraction.py`, `scripts/check_targets.py`
**Commit:** `258b8c4`
**Applied fix:** Moved `TRACK_POWER_W`, `TRACK_IDS`, and the more complete `print_results(summaries, track_ids=TRACK_IDS)` (including the ordering-flag disclaimer line) into `src/targets.py` as the single shared source, and imported them from both CLI entry points, removing the duplicate local definitions.
**Verification:** Both scripts import successfully and expose the same `TRACK_IDS`/`print_results` objects sourced from `targets`. Confirmed `test_single_parameterization_has_no_track_conditionals` still passes (the added `TRACK_IDS`/`print_results` code does not introduce any `track_id`-branching pattern). Full `tests/test_targets.py` and `tests/test_run_target_extraction.py` suites pass.

### WR-05: `check_targets.py` performs no repository-root / raw-tree validation, unlike its sibling `run_target_extraction.py`

**Files modified:** `scripts/check_targets.py`
**Commit:** `adb186d`
**Applied fix:** `check_targets.py` now imports and calls `resolve_repository_root`/`resolve_raw_dir` from `run_target_extraction.py` (added `scripts/` to `sys.path` alongside the existing `src/` append) before deriving `targets_dir` in `main()`, matching the security posture already established for the writer script.
**Verification:** Ran the real `scripts/check_targets.py --project_dir .` (and under `python -O`) against the freshly-published real pipeline output — both passed cleanly with the new validation in place.

## Skipped Issues

None — all 7 in-scope findings were fixed.

---

_Fixed: 2026-07-20T01:45:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
