---
phase: 01-target-extraction-contract
fixed_at: 2026-07-23T19:09:11Z
review_path: .planning/phases/01-target-extraction-contract/01-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 01: Code Review Fix Report

**Fixed at:** 2026-07-23T19:09:11Z
**Source review:** .planning/phases/01-target-extraction-contract/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 7 (fix_scope: critical_warning — WR-01 through WR-07; the 7 Info findings were out of scope and not touched)
- Fixed: 7
- Skipped: 0

All fixes were applied in an isolated git worktree, verified (syntax check + full checked-in test
suites, plus a real end-to-end run against the committed `data/raw/height_maps/*.ASC` files for the
two scripts that lacked dedicated tests), committed one finding per commit, then fast-forwarded onto
`main`.

**Final test suite state:** 50/51 tests pass across all three suites (`test_nsf_fmrg_data.py` 12/13,
`test_targets.py` 38/39, `test_run_target_extraction.py` 10/10). The one failure
(`test_detrend_caps_xy_interaction_degree_at_domain_edge` / its sibling
`test_xy_interaction_cap_is_track_independent`) is the exact, reviewer-predicted consequence of the
WR-01 fix and is flagged below for human follow-up — it is not a new regression.

## Fixed Issues

### WR-01: `robust_plane_detrend`'s 3-round trim/refit loop discards its final trim decision

**Files modified:** `src/nsf_fmrg_data.py`
**Commit:** `66dbdf4`
**Status:** fixed: requires human verification
**Applied fix:** Added a final `coef, *_ = np.linalg.lstsq(A[keep], z[keep], rcond=None)` refit after
the trim loop, exactly as suggested, so the returned coefficients reflect the loop's actual final
`keep` set.

**IMPORTANT — human follow-up required:** This fix reproduces the exact consequence the reviewer
measured and warned about: it moves the fitted plane enough that Amendment A6's locked
`DETREND_MAX_XY_DEGREE=2` tolerance check now fails on the real data.
- `tests/test_nsf_fmrg_data.py::test_detrend_caps_xy_interaction_degree_at_domain_edge` and
  `tests/test_targets.py::test_xy_interaction_cap_is_track_independent` both now fail (confirmed
  reproducible before AND after every subsequent commit in this run — isolated by stashing/unstashing
  each later change).
- Regenerating `processed_data/diagnostics/track10_tail_collapse_diagnosis.csv` (WR-06, below)
  against the corrected production code shows track 10's far-edge shape-gap departure at
  `0.01574mm` with `max_xy_degree=2` applied — above the `SHAPE_GAP_EDGE_TOLERANCE_MM=0.012mm`
  criterion cited by Amendment A6 (which was measured `0.0118mm` against the pre-fix, buggy code).
- This was explicitly flagged in REVIEW.md: "Re-measure and re-lock the Amendment A4/A5/A6 tolerance
  margins after this fix, since it moves the fitted surface by amounts comparable to those margins."
  Deciding how to re-lock (raise the tolerance, lower the cap, or otherwise revise 01-13-CRITERION.md)
  is a domain-science judgment call outside this fixer's mandate — it was deliberately **not** made
  here. A human must review `src/targets.py:42-57` (Amendment A6 comment), the regenerated CSV, and
  `tests/test_nsf_fmrg_data.py:346-368` / `tests/test_targets.py:737-...` before this phase's test
  suite can be considered green again.

### WR-02: `bin_profile`'s half-open binning window silently drops the domain's exact trailing-edge sample

**Files modified:** `src/targets.py`
**Commit:** `4c3f083`
**Applied fix:** Added an `inclusive_upper` parameter to `bin_profile` (default `False`, preserving
existing behavior for all other bins/callers) and passed `inclusive_upper=True` only for the final
grid slot (`i == TARGET_GRID_N - 1`) in `extract_targets_from_arrays`, so the native column at
`x_actual_mm == 100.0mm` is now captured by the last bin without double-counting any interior
boundary. Verified isolated from WR-01's regression by stashing/unstashing: identical pass/fail
counts with or without this change.

### WR-03: `load_wyko_asc` never validates that the `RAW_DATA` body actually supplied `x_size * y_size` rows

**Files modified:** `src/nsf_fmrg_data.py`
**Commit:** `70aeac5`
**Applied fix:** Added the exact `ValueError` guard suggested, raised when `count < n_expected` after
the read loop. Verified against all four real `data/raw/height_maps/*.ASC` files (tracks 8/10/14/21)
— all still load cleanly with unchanged shapes, confirming no false-positive on well-formed data.

### WR-04: `extract_final_thermal_frames` does not validate the extracted segment actually reaches 400 frames

**Files modified:** `src/nsf_fmrg_data.py`
**Commit:** `f5f1a20`
**Applied fix:** Added the suggested `ValueError` guard when `stop_idx < EXTRACTED_THERMAL_FRAMES`,
replacing the silent `max(0, ...)` clamp. Full `test_nsf_fmrg_data.py` suite (13/13) passes with this
change in isolation (confirmed before WR-01 was layered on top).

### WR-05: `publish_staging_dir` has no rollback if the final `staging_dir.rename(targets_dir)` step fails

**Files modified:** `scripts/run_target_extraction.py`
**Commit:** `d6ccfbe`
**Applied fix:** Wrapped the final rename in `try/except BaseException`, restoring `backup_dir` back
onto `targets_dir` if the rename fails and `backup_dir` still exists while `targets_dir` is absent,
then re-raising. `tests/test_run_target_extraction.py` (10/10) passes unchanged.

### WR-06: `diagnose_track10_tail_collapse.py`'s stale comment/CSV omit `DETREND_MAX_XY_DEGREE`

**Files modified:** `scripts/diagnose_track10_tail_collapse.py`,
`processed_data/diagnostics/track10_tail_collapse_diagnosis.csv`
**Commit:** `e0a0059`
**Applied fix:** Imported `DETREND_MAX_XY_DEGREE`, passed `max_xy_degree=DETREND_MAX_XY_DEGREE` in
the `robust_plane_detrend` call, corrected the stale "Amendment A5" comment to reference the real
Amendment A6 production configuration, and regenerated the CSV by running the script end-to-end
against the real `data/raw/height_maps/*.ASC` files (data/raw integrity check passed — no raw files
touched). The regenerated track-10 departure (`0.01574mm`, using the now also WR-01-fixed
`robust_plane_detrend`) directly evidences the WR-01 follow-up flagged above.

### WR-07: `diagnose_width_regression.py`'s sweep never reproduces the real production configuration

**Files modified:** `scripts/diagnose_width_regression.py`,
`processed_data/diagnostics/width_regression_sweep.csv`
**Commit:** `f4914c6`
**Applied fix:**
- Threaded `previous_length_mm` through `extract_swept` (mirroring
  `extract_targets_from_arrays`'s Mechanism B history tracking) so continuity-on sweep rows now
  exercise the same implausible-candidate history gate production uses.
- Also applied WR-02's `inclusive_upper` trailing-bin fix inside `extract_swept` for consistency with
  the now-corrected `bin_profile`.
- Added a dedicated `production=True` row (via a new `_medians_for_config` helper) that exactly
  mirrors `targets.extract_track_targets`'s detrend call: `order=DETREND_POLY_ORDER`,
  `fit_mask=bead_exclusion_mask(...)`, `max_y_degree=DETREND_MAX_Y_DEGREE`,
  `max_xy_degree=DETREND_MAX_XY_DEGREE`, with continuity always on. Added `production`,
  `max_y_degree`, `max_xy_degree` columns to both the printed table and the CSV schema.
- Ran the script end-to-end against real raw data (data/raw integrity check passed) and committed
  `processed_data/diagnostics/width_regression_sweep.csv` alongside its sibling diagnostic CSVs, per
  the reviewer's explicit instruction that it was "neither" committed nor gitignored.

**Note:** the main repository working tree had a pre-existing **untracked**, stale copy of
`processed_data/diagnostics/width_regression_sweep.csv` (dated 2026-07-21, missing the new
`production`/`max_y_degree`/`max_xy_degree` columns, generated by an earlier ad-hoc run) that blocked
this fix's `git worktree` fast-forward merge onto `main`. It was not part of any commit and was not
authored by this fix run. It was backed up (not deleted) to
`/tmp/claude-1000/-home-khoa2-nsf-fmrg-data-challenge/a742cbf6-c1fe-4448-843b-a3ea9301f566/scratchpad/stale_untracked_width_regression_sweep.csv`
before the merge, and removed from the working tree so the properly regenerated, tested, and
committed version could land. No tracked history was altered by this step.

## Skipped Issues

None — all 7 in-scope findings (WR-01 through WR-07) were fixed.

---

_Fixed: 2026-07-23T19:09:11Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
