---
phase: 01-target-extraction-contract
reviewed: 2026-07-22T00:00:00Z
depth: standard
files_reviewed: 25
files_reviewed_list:
  - processed_data/diagnostics/track10_coverage_diagnosis.csv
  - processed_data/diagnostics/track10_tail_collapse_diagnosis.csv
  - processed_data/targets/extraction_params.json
  - processed_data/targets/qa/track_10_overlay.png
  - processed_data/targets/qa/track_10_residual_map.png
  - processed_data/targets/qa/track_10_width.png
  - processed_data/targets/qa/track_14_overlay.png
  - processed_data/targets/qa/track_14_residual_map.png
  - processed_data/targets/qa/track_14_width.png
  - processed_data/targets/qa/track_21_overlay.png
  - processed_data/targets/qa/track_21_residual_map.png
  - processed_data/targets/qa/track_21_width.png
  - processed_data/targets/qa/track_8_overlay.png
  - processed_data/targets/qa/track_8_residual_map.png
  - processed_data/targets/qa/track_8_width.png
  - processed_data/targets/track_10_targets.npz
  - processed_data/targets/track_14_targets.npz
  - processed_data/targets/track_21_targets.npz
  - processed_data/targets/track_8_targets.npz
  - scripts/check_targets.py
  - scripts/diagnose_track10_coverage.py
  - scripts/diagnose_track10_tail_collapse.py
  - scripts/diagnose_width_regression.py
  - scripts/run_target_extraction.py
  - src/nsf_fmrg_data.py
  - src/targets.py
  - tests/test_nsf_fmrg_data.py
  - tests/test_run_target_extraction.py
  - tests/test_targets.py
findings:
  critical: 0
  warning: 7
  info: 6
  total: 13
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-22T00:00:00Z
**Depth:** standard
**Files Reviewed:** 10 source/test files read and analyzed in full; 15 checked-in data/QA
artifacts (`.npz`, `.png`, `.csv`, `.json`) inspected for cross-consistency with the code (re-run
against the real, checked-in `data/raw/height_maps/*.ASC` data), not reviewed as code.
**Status:** issues_found

## Summary

This is a re-verification pass, not a fresh review from a blank slate. `git diff --stat` confirms
zero changes to any file in this review's scope between the prior `01-REVIEW.md` commit (`43a6e02`)
and the current `HEAD` — the only work since that review (plan 01-15) touched exclusively
`.planning/phases/01-target-extraction-contract/01-SIGNOFF-REQUEST.md` and
`.planning/REQUIREMENTS.md`, both out of this review's scope. Because the source tree is
byte-identical to what `43a6e02`'s `01-REVIEW.md` reviewed, this pass independently re-verified
every one of that review's 12 findings against the live code and data rather than assuming they
still apply, and additionally re-ran the full test matrix and diagnostic scripts against the real,
checked-in raw dataset.

Separately, `.planning/phases/01-target-extraction-contract/01-REVIEW-FIX.md` (committed as
`050e300`, *before* `43a6e02`) documents a fix pass for a **different, earlier** set of four
warnings (production-path `max_y_degree` passthrough, `order`/`max_y_degree` validation ordering,
`load_wyko_asc`'s `KeyError`→`ValueError`, and the laser-on `TypeError`→`ValueError`). Those four
fixes are real and confirmed still present in the current code (validation blocks in
`robust_plane_detrend` sit above the degenerate-data early return at `src/nsf_fmrg_data.py:234-241`;
`load_wyko_asc` raises `ValueError` for missing `x_size`/`y_size` at
`src/nsf_fmrg_data.py:180-181`; `extract_final_thermal_frames` raises `ValueError` for a missing
laser-on interval at `src/nsf_fmrg_data.py:128-129`). They are the same four items `43a6e02`'s
`01-REVIEW.md` already accounted for as "fixed... and not repeated" in its own summary, so no
further action is needed there.

**Verification method:** all three test suites were executed in the repo's checked-in `.venv`
(33 + 13 + 10 tests, all pass); `scripts/check_targets.py` was run against the real
`processed_data/targets/*.npz` artifacts (`ALL CHECKS PASSED`); `scripts/diagnose_track10_coverage.py`
was re-run against the real `data/raw/height_maps/` data and its output byte-matches the checked-in
CSV (confirming the artifact is reproducible, not stale); and several of the prior review's specific
numeric claims (the `bin_profile` boundary drop, the `classify_column`/`halfmax_edges` divergence
magnitude, and — newly — the tail-collapse diagnostic's now-stale departure numbers) were
independently recomputed against the live code rather than taken on faith.

**Result: all 6 warnings and all 6 info items from the prior `01-REVIEW.md` are confirmed still
open**, unchanged in substance, since none of the underlying code changed. One **new** warning
(WR-07) was found: `scripts/diagnose_track10_tail_collapse.py`'s in-line claim to be "the exact
CURRENT production path" is now false — Amendment A6/A7 added `DETREND_MAX_XY_DEGREE`/
`max_xy_degree` to the real production detrend call, but this diagnostic was never updated to pass
it, and the checked-in `track10_tail_collapse_diagnosis.csv` numbers are demonstrably the
pre-Amendment-A6 values, not what the pipeline ships today.

## Warnings

### WR-01: `diagnose_track10_coverage.py`'s `classify_column` remains out of sync with `targets.halfmax_edges` after Amendments A6/A7 (confirmed still open)

**File:** `scripts/diagnose_track10_coverage.py:105-161`
**Issue:** Unchanged from the prior review. `classify_column`'s own comment ("Mirrors
targets.halfmax_edges' rejection branches... must be kept in step with that function") is still
false: it builds `candidates` directly from `all_true_runs(above)` with no
`merge_adjacent_runs(..., MAX_RUN_MERGE_GAP_PIXELS)` step (lines 121-126), and in the tracked branch
(`previous_center is not None`) selects `min(candidates, key=...)` with no
`MIN_TRACKED_LENGTH_RATIO` plausibility filter (lines 129-139), while the real
`targets.halfmax_edges` (`src/targets.py:200-234`) does both. Neither `merge_adjacent_runs` nor
`MAX_RUN_MERGE_GAP_PIXELS`/`MIN_TRACKED_LENGTH_RATIO` are imported (`scripts/diagnose_track10_coverage.py:17-32`).
**Re-verified with live numbers:** re-running `scripts/diagnose_track10_coverage.py` against the
real height-map data reproduces the checked-in CSV exactly (`rejection_ok=255` for track 10), while
`scripts/check_targets.py` against the real, production-generated `track_10_targets.npz` reports
`valid_count=202` — a 53-column discrepancy between what this diagnostic calls "ok" and what the
actual production pipeline (`extract_targets_from_arrays`) treats as valid for the identical input
data. Some of that gap is attributable to post-smoothing crossing invalidation in
`finalize_smoothed_boundaries` (which `classify_column` also does not model), but the
merge/plausibility-gate drift this finding targets is a real, additional, and directly
attributable contributor to it.
**Fix:** Unchanged from the prior review — import and call the real helpers
(`merge_adjacent_runs`, `MAX_RUN_MERGE_GAP_PIXELS`, `MIN_TRACKED_LENGTH_RATIO`) instead of a
hand-copied, unmaintained duplicate, or delete `classify_column` and call
`targets.halfmax_edges` directly (as `diagnose_width_regression.py` already does), attributing
`None` to a generic "rejected" bucket.

### WR-02: `diagnose_track10_coverage.py`'s `production_residual_profile` still omits the Amendment A6 `max_xy_degree` cap (confirmed still open)

**File:** `scripts/diagnose_track10_coverage.py:61-67`
**Issue:** Unchanged from the prior review. `production_residual_profile` still calls
`robust_plane_detrend(..., max_y_degree=DETREND_MAX_Y_DEGREE)` without
`max_xy_degree=DETREND_MAX_XY_DEGREE`, while the real production call in
`targets.extract_track_targets` (`src/targets.py:371-379`) passes both. `DETREND_MAX_XY_DEGREE` is
still not in this file's import list (lines 17-32).
**Fix:** Unchanged — add `DETREND_MAX_XY_DEGREE` to the import list and the `robust_plane_detrend`
call so the function's name ("production" residual profile) matches what it measures.

### WR-03: `bin_profile`'s half-open binning window still silently drops the domain's exact trailing-edge sample (confirmed still open)

**File:** `src/targets.py:124-130`
**Issue:** Unchanged. `columns = (x_actual_mm >= x_center - half_step) & (x_actual_mm < x_center + half_step)`
is asymmetric (`>=` lower bound, `<` upper bound).
**Re-verified directly against real data:** `load_wyko_asc('data/raw/height_maps', 8)['x_actual_mm'][-1] == 100.0`
exactly, and for the last bin center `x_center=99.9`, the current half-open test selects 50 native
columns (`< 100.0`) versus 51 with an inclusive test (`<= 100.0`) — the single native column at
exactly `x_actual_mm == 100.0` is structurally unreachable by any bin. Practical impact remains
negligible today (one column out of 50-51, well above `MIN_COLUMNS_PER_BIN=10`), but the asymmetry
is a real, unintentional boundary artifact in an otherwise deliberately-conventioned codebase.
**Fix:** Unchanged — make the window symmetric/inclusive
(`x_actual_mm <= x_center + half_step`), then re-verify no native column becomes double-counted
between adjacent bins.

### WR-04: `load_wyko_asc` still never validates that the RAW_DATA body actually supplied `x_size * y_size` rows (confirmed still open)

**File:** `src/nsf_fmrg_data.py:186-203`
**Issue:** Unchanged. `z_mm_flat` is NaN-filled up front; the read loop only ever `break`s early when
`count >= n_expected` (line 202-203) — there is still no check that a truncated/malformed file
supplied *at least* `n_expected` rows before the `for line in f` loop exhausts the file. A
short/corrupted `.ASC` body silently produces a mostly-NaN height map instead of failing closed,
inconsistent with the guard immediately above it (lines 180-181) for missing header fields.
**Fix:** Unchanged — validate `count == n_expected` (or `>=`) after the loop and raise `ValueError`
on a shortfall.

### WR-05: `extract_final_thermal_frames` can still silently return fewer than `EXTRACTED_THERMAL_FRAMES` frames (confirmed still open)

**File:** `src/nsf_fmrg_data.py:130-134`
**Issue:** Unchanged. `start_idx = max(0, stop_idx - EXTRACTED_THERMAL_FRAMES)` still clamps to `0`
with no length check on `segment = frames[start_idx:stop_idx]`; a short laser-on interval silently
returns fewer than 400 frames.
**Fix:** Unchanged — raise `ValueError` if `stop_idx - start_idx < EXTRACTED_THERMAL_FRAMES`.

### WR-06: `publish_staging_dir` still has no rollback if the final `staging_dir.rename(targets_dir)` step fails (confirmed still open)

**File:** `scripts/run_target_extraction.py:309-329`
**Issue:** Unchanged. The rename sequence (backup old `targets_dir` aside at line 322, then
`staging_dir.rename(targets_dir)` at line 325) still has no `try/except` around the second rename.
If it raises after the first rename has already succeeded, `processed_data/targets` is left absent
entirely (renamed away, never replaced), with the previous generation stranded at
`targets_dir.previous` and no automatic restore. `tests/test_run_target_extraction.py` still does
not exercise this specific failure window (its symlink/integrity tests cover different failure
modes).
**Fix:** Unchanged — wrap the second rename so a failure restores the backup to its original name
before re-raising.

### WR-07 (new): `diagnose_track10_tail_collapse.py`'s "exact CURRENT production path" claim is stale and its checked-in CSV reports pre-Amendment-A6 numbers

**File:** `scripts/diagnose_track10_tail_collapse.py:57-63`
**Issue:** `measure_track`'s comment reads: `# The exact CURRENT production path (Amendment A5, no
new parameter, since none exists yet): observe only the currently-shipped fit.` This was accurate
when the file was authored in plan 01-13 (`git log` shows exactly one commit touching this file:
`53bcb1e`), before Amendments A6/A7 landed. It is no longer true: Amendment A6 added
`DETREND_MAX_XY_DEGREE`/`max_xy_degree` to the real production call
(`targets.extract_track_targets`, `src/targets.py:371-379`), but this diagnostic's
`robust_plane_detrend` call (lines 60-63) still omits `max_xy_degree` and `DETREND_MAX_XY_DEGREE` is
not imported (lines 17-22) — exactly the same drift class as WR-02, in the sibling file, but here
the in-line comment actively asserts the opposite of what is now true.

This is not just a stale comment: it changes the numbers this diagnostic reports. Recomputing
`measure_track`'s `departure` metric with and without `max_xy_degree=DETREND_MAX_XY_DEGREE` against
the real height-map data:

| track | as currently coded (no `max_xy_degree`) | actual production path (`max_xy_degree=2`) |
|---|---|---|
| 8  | 0.006038 | 0.003761 |
| 10 | 0.021200 | 0.011843 |
| 14 | 0.0000539 | 0.0001700 |
| 21 | 0.006166 | 0.005772 |

The checked-in `processed_data/diagnostics/track10_tail_collapse_diagnosis.csv` row for track 10
(`departure=0.021199873273603273`) exactly matches the *stale, pre-Amendment-A6* column above, not
the real production value (`0.011843`) — which is itself the number the Amendment A6 doc comment in
`src/targets.py:50-56` cites as clearing the 0.012mm criterion tolerance ("cap 2 brings it to
0.0118mm, comfortably under"). In other words, the checked-in diagnostic artifact for the exact
metric that justified Amendment A6 is reporting the pre-fix number, one full amendment out of date,
directly contradicting its own "exact CURRENT production path" claim.
**Fix:** Import `DETREND_MAX_XY_DEGREE` and pass `max_xy_degree=DETREND_MAX_XY_DEGREE` in the
`robust_plane_detrend` call at lines 60-63; update the stale comment; and regenerate
`processed_data/diagnostics/track10_tail_collapse_diagnosis.csv` from the corrected code so the
checked-in artifact reflects the surface the pipeline actually ships.

## Info

### IN-01: Unused `import json` in `src/nsf_fmrg_data.py` (confirmed still open)

**File:** `src/nsf_fmrg_data.py:3`
**Issue:** Unchanged — `json` is still imported and never referenced (`grep -n "json\."
src/nsf_fmrg_data.py` finds nothing).
**Fix:** Remove the unused import.

### IN-02: Diagnostic scripts still duplicate `write_csv`/table-printing helpers verbatim (confirmed still open)

**File:** `scripts/diagnose_track10_coverage.py:253-266`, `scripts/diagnose_track10_tail_collapse.py:78-91`, `scripts/diagnose_width_regression.py:150-161`
**Issue:** Unchanged — all three scripts still define near-identical
`print_measurement_table`/`write_csv` (or `print_sweep_table`/`write_sweep_csv`) helpers plus a
verbatim-repeated "sibling directory" comment.
**Fix:** Extract a shared `scripts/_diagnostic_io.py` helper module; unchanged from prior review.

### IN-03: Redundant `.copy()` calls in `finalize_smoothed_boundaries` (confirmed still open)

**File:** `src/targets.py:285-286`
**Issue:** Unchanged — `y_lower`/`y_upper` are already freshly allocated by `nan_savgol` before
being copied again.
**Fix:** Remove the redundant `.copy()` calls.

### IN-04: `_loadmat_any`'s HDF5 fallback still swallows all conversion exceptions (confirmed still open)

**File:** `src/nsf_fmrg_data.py:46-51`
**Issue:** Unchanged — `except Exception: pass` inside the `h5py.visititems` callback still
discards any error, not just the narrowly expected "not convertible" case. Documented in
`CLAUDE.md` as an accepted, scoped pattern; re-flagged per the adversarial mandate, not a new
defect.
**Fix (optional):** Narrow to `(TypeError, ValueError)`.

### IN-05: `Y_STRIP_EXTENT_MM` in `scripts/check_targets.py` remains a hardcoded constant, not derived per-track (confirmed still open)

**File:** `scripts/check_targets.py:24-27`
**Issue:** Unchanged — the 1.907mm bound is a global constant documented as derived from all four
current headers, not re-derived from each track's actual header at check time.
**Fix (optional):** Derive per-track from `load_wyko_asc`'s header at check time.

### IN-06: Track 10 vs. Track 14 median width still violates the expected power-monotonic ordering (documented, not a code defect) (confirmed still open)

**File:** `processed_data/targets/track_10_targets.npz`, `processed_data/targets/track_14_targets.npz`
**Issue:** Unchanged and reconfirmed by re-running `scripts/check_targets.py` against the live
artifacts this pass: Track 10 (350W) median width 0.3770mm is still less than Track 14 (300W)
0.6174mm, printed as `FLAG` by the code's own ordering check, and explicitly documented as never
used to tune locked extraction constants.
**Fix:** None required for this phase; carry the caveat forward into downstream documentation.

---

_Reviewed: 2026-07-22T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
