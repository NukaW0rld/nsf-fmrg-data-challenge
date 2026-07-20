---
phase: 01-target-extraction-contract
reviewed: 2026-07-20T01:13:36Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - scripts/check_targets.py
  - scripts/run_target_extraction.py
  - src/targets.py
  - tests/test_run_target_extraction.py
  - tests/test_targets.py
findings:
  critical: 2
  warning: 5
  info: 2
  total: 9
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-20T01:13:36Z
**Depth:** standard
**Files Reviewed:** 5 (plus generated artifacts under `processed_data/targets/` reviewed as read-only QA context)
**Status:** issues_found

## Summary

This is a fresh, independent adversarial pass over the current HEAD state of the target-extraction contract (`src/targets.py`, `scripts/run_target_extraction.py`, `scripts/check_targets.py`) and their test suites — not a re-assertion of the prior review pass.

I traced the full call chain (`run_target_extraction.main → run_pipeline → run_track → extract_track_targets → extract_targets_from_arrays → bin_profile/fill_small_gaps/halfmax_edges/finalize_smoothed_boundaries`) against `nsf_fmrg_data.py`'s `load_wyko_asc`/`robust_plane_detrend`/`largest_true_run`, hand-verified the interpolation arithmetic in `halfmax_edges` for division-by-zero and off-by-one boundary conditions, and confirmed the post-smoothing crossing revalidation, symlink/TOCTOU guards, and fail-closed raw-audit `finally` block all behave correctly as implemented (matching their test coverage).

**Important correction to the review-scoping assumption:** the task briefing states the prior `01-REVIEW.md` (2 critical, 2 warning) "was subsequently addressed per commit history." I checked this against `git log` rather than assuming it, and it does not hold. The only commits after the second review pass (`05fdcb7`) that touch this phase are `bec8aa2`, `00fb1d4`, `152b0a1`, `70aac0e` — all of which are `.planning/` documentation/tracking commits (`01-VALIDATION.md`, `01-UAT.md`, `ROADMAP.md`, `STATE.md`). **No commit after `8771323` (the last `feat(01-03)` commit, before either review pass ran) modified `src/targets.py`, `scripts/check_targets.py`, or `scripts/run_target_extraction.py`.** I independently reproduced both previously reported blockers against the current file contents (reproduction steps below) and both are still live defects. I also reproduced one of the two previously reported warnings. I did not carry forward findings I could not reproduce myself.

QA PNGs spot-checked (`track_8`, `track_10`, `track_14`, `track_21` — overlay/width/residual) render sensible, non-empty height maps, boundaries, and width curves; no broken-plot artifacts observed.

## Critical Issues

### CR-01: `check_targets.py`'s entire validation contract is `assert`-based and is silently disabled under `python -O`

**File:** `scripts/check_targets.py:26-131`
**Issue:** All 19 correctness checks in `check_track()` (dtype, shape, grid alignment, finite-mask-equals-valid-mask, width-equals-upper-minus-lower, `y_upper > y_lower`, positive/bounded width) and the provenance check in `main()` (`assert persisted_params == extraction_params()`) are plain `assert` statements. Python strips all `assert` statements when run with `-O` (or `PYTHONOPTIMIZE=1`), and nothing in this script checks `__debug__` or otherwise fails closed if optimizations are active. `01-VALIDATION.md`'s "Optimization-safe command" row only lists `tests/test_targets.py` and `tests/test_run_target_extraction.py` under `-O` — it does **not** cover `scripts/check_targets.py`, so this gap is invisible to the phase's own validation matrix.

I reproduced this against the current code: I wrote deliberately corrupted `.npz` artifacts for all four tracks with `y_lower_mm > y_upper_mm` everywhere (crossed/negative-width, which the contract requires to be invalid) and ran the real `scripts/check_targets.py` unmodified.

```
$ .venv/bin/python scripts/check_targets.py --project_dir .
AssertionError: Track 8: width does not equal upper minus lower boundary.   # normal mode: fails correctly

$ .venv/bin/python -O scripts/check_targets.py --project_dir .
track  power_W  valid_bins  median_mm  mean_mm
    8      400         400     0.5000   0.5000
   10      350         400     0.5000   0.5000
   14      300         400     0.5000   0.5000
   21      200         400     0.5000   0.5000
ALL CHECKS PASSED                                                          # -O mode: prints success anyway, exit 0
```
This is the exact artifact validator whose entire purpose is to be the last line of defense before these `.npz` files are treated as trustworthy ground truth for downstream model training; it is fail-open under a supported Python invocation mode.
**Fix:** Replace runtime `assert` with an explicit helper that always raises, independent of optimization flags:
```python
def require(condition, message):
    if not bool(condition):
        raise ValueError(message)
```
and use `require(...)` in place of every `assert ...` in `check_track()` and `main()`. Add a regression (or CI step) that runs `python -O scripts/check_targets.py` against a deliberately corrupted artifact and asserts it exits non-zero.

### CR-02: A pipeline run that fails partway leaves a silently mixed generation of stale and fresh artifacts, and `check_targets.py` cannot detect it

**File:** `scripts/run_target_extraction.py:308-372` (`run_pipeline`), `238-284` (`run_track`)
**Issue:** `run_pipeline()` writes each track's `.npz`/QA PNGs directly into the live `processed_data/targets/` (and `qa/`) directories in sequence (`summaries = [track_runner(...) for track_id in track_ids]`, line 342-345), with no staging directory, run/generation ID, or completion manifest. The `finally` block only audits `data/raw/` immutability — it never checks or repairs the output directory's completeness. If a later track fails (real extraction can fail per-track, e.g. `extract_track_targets` raising on a malformed `.ASC` file or `finalize_smoothed_boundaries` raising `ValueError` on zero-valid tracks), the tracks processed before the failure have already been overwritten with new data while the untouched tracks retain whatever was on disk from a previous run — a mixed generation — and the process exits non-zero with no indication in `processed_data/targets/` itself that this happened. Because `check_targets.py` validates each `.npz` file independently against only static, per-file invariants, it cannot tell a mixed generation from a complete, self-consistent one and will report `ALL CHECKS PASSED`.

I reproduced this directly against the real `run_pipeline()` using stub `track_runner`s (isolated temp repo, no real data touched):
```
Generation A (complete, all 4 tracks succeed):
  track_8_targets.txt  -> generation=A track=8
  track_10_targets.txt -> generation=A track=10
  track_14_targets.txt -> generation=A track=14
  track_21_targets.txt -> generation=A track=21

Generation B (re-run; fails on track 14 after refreshing 8 and 10, never reaches 21):
  run_pipeline raises RuntimeError("simulated failure on track 14 during generation B")  [correctly propagates]

Resulting on-disk state in processed_data/targets/ after the failed run:
  track_8_targets.txt  -> generation=B track=8    # fresh
  track_10_targets.txt -> generation=B track=10   # fresh
  track_14_targets.txt -> generation=A track=14   # STALE (from generation A, never touched by B)
  track_21_targets.txt -> generation=A track=21   # STALE (from generation A, never touched by B)
```
Each individual file is well-formed, so `check_targets.py` would certify this mixed set as passing even though tracks 8/10 and tracks 14/21 do not come from the same extraction run (potentially different code version, different upstream `data/raw/` state, etc.). For a pipeline whose stated purpose is producing scientific ground truth for cross-track validation, silently mixing generations across tracks is a correctness/provenance defect, not just cosmetic.
**Fix:** Write every `.npz`/`.json`/`.png` into a fresh staging directory per run (e.g. `processed_data/targets/.staging-<run-id>/`), track completion of all `track_ids` plus the final raw-integrity audit, and only then atomically publish (`os.replace`/directory rename) the staged output over the live `processed_data/targets/`. Have `check_targets.py` require and verify a manifest (run ID / timestamp / code+params digest) that ties all four `.npz` files to the same completed run, and reject any output directory lacking one.

## Warnings

### WR-01: `check_targets.py` does not require `NaN` (as opposed to any other non-finite value) in invalid slots — reproducible even without `-O`

**File:** `scripts/check_targets.py:60-68`
**Issue:** The checker only verifies `np.isfinite(w_mm) == valid_mask` (and the same for `y_upper_mm`/`y_lower_mm`). `+inf`/`-inf` are also non-finite, so an artifact with `+inf` in every invalid slot instead of `NaN` satisfies every one of these equality checks. I reproduced this in **normal** (non-optimized) mode against the real script:
```
$ .venv/bin/python scripts/check_targets.py --project_dir .   # artifact has +inf in 399/400 invalid slots per track
...
ALL CHECKS PASSED   # exit 0
```
The real production pipeline (`finalize_smoothed_boundaries` in `src/targets.py:141-154`) always writes `np.nan` for invalid slots today, so this does not currently produce a wrong *value* in the shipped artifacts — but the checker's contract ("invalid numeric slots must be NaN," matching what downstream consumers will likely assume when doing `np.nanmean`/`np.nanmedian` style aggregation) is not actually enforced, so a future extraction-code regression that leaves `inf` behind (e.g. a division that should have been guarded) would pass silently.
**Fix:**
```python
for key, values in (("w_mm", w_mm), ("y_upper_mm", y_upper_mm), ("y_lower_mm", y_lower_mm)):
    assert np.isnan(values[~valid_mask]).all(), (
        f"Track {track_id}: {key} invalid slots must be NaN, not merely non-finite."
    )
```
(and see CR-01 — this should be a `require(...)` call, not a new `assert`).

### WR-02: The no-per-track-tuning structural guard only catches a narrow syntactic pattern

**File:** `tests/test_targets.py:131-137`
**Issue:** `test_single_parameterization_has_no_track_conditionals` regex-scans `src/targets.py` for `\bif\s+track_id\b` or direct comparison/membership operators on the literal token `track_id`. This is meant to be the regression guard for the phase's core "no per-track tuning" invariant (TARGET-02), but it would not catch equally-effective track-dependent parameterization such as `PARAMS_BY_TRACK[track_id]`, `get_params(track_id)`, a `match track_id:` statement, or simply renaming the parameter before branching on it. Today `src/targets.py` genuinely contains no track-dependent logic, so this is not a live bug in the shipped code, but the regression test itself provides much weaker protection against a future violation than its name/intent implies.
**Fix:** Either assert the behavioral invariant directly (call `extract_targets_from_arrays`/`extract_track_targets` twice with the same array data but different `track_id` values and require bit-identical numeric output apart from the returned `track_id`/`file` metadata fields), or replace the regex with an AST walk that flags any use of `track_id` inside `extract_targets_from_arrays`, `bin_profile`, `fill_small_gaps`, `halfmax_edges`, `nan_savgol`, and `finalize_smoothed_boundaries` (i.e. everywhere except the I/O wrapper `extract_track_targets`).

### WR-03: `TARGET_GRID_STEP_MM` is duplicated in `run_target_extraction.py` instead of being sourced from `targets.py`, with no test enforcing consistency

**File:** `scripts/run_target_extraction.py:24`
**Issue:** `src/targets.py:8` defines `TARGET_GRID_STEP_MM = 0.2` as part of the locked extraction parameterization (persisted to `extraction_params.json` and asserted verbatim by `tests/test_targets.py::test_extraction_params_provenance`). `scripts/run_target_extraction.py:24` redefines the same value as an independent literal used only for QA overlay shading (`shade_invalid_slots`, line 104). Nothing validates that this second copy stays in sync with `src/targets.py`'s locked constant — a future change to the step size would still pass the provenance test (which only checks whatever value is currently baked into `extraction_params()`) while silently desynchronizing the QA overlay's invalid-slot shading from the real bin half-width, producing misleading QA images with no test failure.
**Fix:**
```python
from targets import extract_track_targets, extraction_params

TARGET_GRID_STEP_MM = extraction_params()["TARGET_GRID_STEP_MM"]
```

### WR-04: `print_results` and the `TRACK_POWER_W`/`TRACK_IDS` tables are duplicated verbatim across `run_target_extraction.py` and `check_targets.py`

**File:** `scripts/run_target_extraction.py:22-23, 287-305` and `scripts/check_targets.py:16-17, 95-112`
**Issue:** The ~15-line ordering-check function `print_results` (median-width monotonicity check against laser power) and the `TRACK_POWER_W = {8: 400, 10: 350, 14: 300, 21: 200}` / `TRACK_IDS` tables are copy-pasted between the two scripts with no shared source and no test cross-checking them for consistency. A future change to the track set, power mapping, or ordering-check wording made in one copy but not the other would silently diverge.
**Fix:** Move `TRACK_POWER_W`, `TRACK_IDS`, and `print_results` into `src/targets.py` (or a small shared module) and import them from both CLI entry points.

### WR-05: `check_targets.py` performs no repository-root / raw-tree validation, unlike its sibling `run_target_extraction.py`

**File:** `scripts/check_targets.py:115-131`
**Issue:** `run_target_extraction.py` was hardened with `resolve_repository_root`, `resolve_raw_dir`, and `resolve_output_path` to prevent `--project_dir` from resolving outside the canonical repository or into `data/raw/`. `check_targets.py:119` (`targets_dir = args.project_dir.resolve() / "processed_data" / "targets"`) applies none of that — `--project_dir` can point anywhere on disk. This script never writes, so it cannot corrupt `data/raw/`, but it is inconsistent with the security posture established elsewhere in the same phase: a mistaken `--project_dir` would silently validate and print a "PASSED" summary for artifacts from an unrelated directory against the *current* code's `extraction_params()`, which could be misread as validating the intended dataset.
**Fix:** Reuse `resolve_repository_root`/`resolve_raw_dir` (or a shared subset) from `run_target_extraction.py` in `check_targets.py`'s `main()` before deriving `targets_dir`.

## Info

### IN-01: `Y_STRIP_EXTENT_MM = 1.907` is an undocumented magic number

**File:** `scripts/check_targets.py:21`
**Issue:** This sanity bound (`w_mm[valid_mask] < Y_STRIP_EXTENT_MM`, lines 76-78) is not derived from `extraction_params.json`, from any height-map header field, or from an inline comment explaining its origin (it appears to be an empirically observed y-strip extent, e.g. `y_size * pixel_size_mm`, for the current four `.ASC` files). If a future track's Wyko scan uses a different `y_size`/`pixel_size_mm`, this bound silently stops being a meaningful sanity check with no indication in the code of how to recompute it.
**Fix:** Derive the bound at runtime from the loaded `.ASC` header per track, or add a comment recording the source track/header values it was derived from.

### IN-02: `bin_profile`'s half-open bin interval can silently drop the last physical column at `x_actual_mm == 100.0`

**File:** `src/targets.py:42-48`
**Issue:** Bins select columns with `x_actual_mm >= x_center - half_step` and `x_actual_mm < x_center + half_step` (strict upper bound). `load_wyko_asc` crops to `x_actual <= COMMON_X_END_MM` (100.0 mm, inclusive) in `nsf_fmrg_data.py`. For the last grid slot (`x_center = 99.9`, `half_step = 0.1`), the bin range is `[99.8, 100.0)`, so a raw column landing exactly at `x_actual_mm == 100.0` falls outside every bin and is silently excluded. In practice this drops at most a single native column, well under `MIN_COLUMNS_PER_BIN`, so it does not change validity outcomes today — a minor, low-impact asymmetry.
**Fix:** Not urgent; if addressed, make the last bin's upper bound inclusive or note the intentional half-open convention with a comment.

---

_Reviewed: 2026-07-20T01:13:36Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
