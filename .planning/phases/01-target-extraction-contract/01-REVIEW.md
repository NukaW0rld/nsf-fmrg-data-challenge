---
phase: 01-target-extraction-contract
reviewed: 2026-07-22T00:00:00Z
depth: deep
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
  warning: 9
  info: 7
  total: 16
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-22T00:00:00Z
**Depth:** deep
**Files Reviewed:** 10 source/test files read in full, cross-traced call-chain by call-chain
against every call site of `robust_plane_detrend`, `halfmax_edges`, `extract_track_targets`, and
`resolve_output_path`; 15 checked-in data/QA artifacts (`.npz`, `.png`, `.csv`, `.json`) inspected
for cross-consistency with the code that produced them (re-run against the real, checked-in
`data/raw/height_maps/*.ASC` data), not reviewed as code.
**Status:** issues_found

## Summary

`git log --oneline -- src/nsf_fmrg_data.py src/targets.py scripts/ tests/` confirms the source tree
in scope is byte-identical to the commit the prior `01-REVIEW.md` (standard depth) reviewed — the
only commits since then (`31303e7`, `8b40214`, `d4605b3`) touch only planning docs. All 7 warnings
and 6 info items from that prior pass were independently re-verified against the live code (all
tests re-run: 33 + 13 + 10, all pass; `scripts/check_targets.py` re-run against the real artifacts:
`ALL CHECKS PASSED`) and are **confirmed still open**, unchanged in substance.

This pass goes further than the prior standard-depth review by tracing numeric behavior across
module boundaries rather than reading each file in isolation. Two new issues came out of that
deeper trace:

- **WR-08 (new):** `robust_plane_detrend`'s 3-round trim/refit loop (`src/nsf_fmrg_data.py:263-273`)
  silently discards its final trim decision — the coefficients it returns come from the fit
  *before* the last outlier-exclusion set is computed, not after. Recomputing the fit on the real,
  checked-in height-map data with one additional refit shifts the fitted detrend plane by up to
  ~0.009mm (Track 21) — a meaningful fraction of the 0.012mm `DETREND_MAX_XY_DEGREE` tolerance this
  same phase locked via measurement in Amendment A6.
- **WR-09 (new):** `scripts/diagnose_width_regression.py`'s sweep never passes
  `max_y_degree`/`max_xy_degree` in any of its 12 rows, so none of the checked-in
  `width_regression_sweep.csv` rows reproduce the actual shipped `extract_track_targets` numbers —
  including the row an unwary reader would assume is "the production config" (`order=4,
  continuity=True, bead_mask=True`). Verified numerically: that row's Track 10/21 medians
  (0.2509mm / 0.2412mm) diverge substantially from the real production values in
  `track_10_targets.npz`/`track_21_targets.npz` (0.3770mm / 0.3825mm).

Also added: **IN-07 (new)**, a minor magic-number duplication in `scripts/check_targets.py`
parallel to the already-flagged `IN-05`.

**No critical/blocker-severity findings.** No hardcoded secrets, injection vectors, or unsafe
deserialization were found anywhere in scope; the symlink/path-escape/raw-integrity hardening in
`scripts/run_target_extraction.py` is thorough and test-covered for its stated threat model
(accidental/malicious writes into `data/raw/` during a local, single-user pipeline run).

## Warnings

### WR-01: `diagnose_track10_coverage.py`'s `classify_column` remains out of sync with `targets.halfmax_edges` after Amendments A6/A7 (confirmed still open)

**File:** `scripts/diagnose_track10_coverage.py:105-161`
**Issue:** `classify_column`'s own comment ("Mirrors targets.halfmax_edges' rejection branches...
must be kept in step with that function") is false: it builds `candidates` directly from
`all_true_runs(above)` with no `merge_adjacent_runs(..., MAX_RUN_MERGE_GAP_PIXELS)` step (lines
121-126), and in the tracked branch (`previous_center is not None`) selects `min(candidates,
key=...)` with no `MIN_TRACKED_LENGTH_RATIO` plausibility filter (lines 129-139), while the real
`targets.halfmax_edges` (`src/targets.py:200-234`) does both. Neither `merge_adjacent_runs` nor
`MAX_RUN_MERGE_GAP_PIXELS`/`MIN_TRACKED_LENGTH_RATIO` are imported (lines 17-32).
**Re-verified with live numbers:** re-running the script against the real height-map data
reproduces the checked-in CSV exactly (`rejection_ok=255` for track 10), while
`scripts/check_targets.py` against the real, production-generated `track_10_targets.npz` reports
`valid_count=202` — a 53-column discrepancy between what this diagnostic calls "ok" and what the
actual production pipeline treats as valid for the identical input data.
**Fix:** Import and call the real helpers (`merge_adjacent_runs`, `MAX_RUN_MERGE_GAP_PIXELS`,
`MIN_TRACKED_LENGTH_RATIO`) instead of a hand-copied, unmaintained duplicate, or delete
`classify_column` and call `targets.halfmax_edges` directly (as `diagnose_width_regression.py`
already does), attributing `None` to a generic "rejected" bucket.

### WR-02: `diagnose_track10_coverage.py`'s `production_residual_profile` still omits the Amendment A6 `max_xy_degree` cap (confirmed still open)

**File:** `scripts/diagnose_track10_coverage.py:61-67`
**Issue:** `production_residual_profile` calls `robust_plane_detrend(...,
max_y_degree=DETREND_MAX_Y_DEGREE)` without `max_xy_degree=DETREND_MAX_XY_DEGREE`, while the real
production call in `targets.extract_track_targets` (`src/targets.py:371-379`) passes both.
`DETREND_MAX_XY_DEGREE` is not in this file's import list (lines 17-32).
**Fix:** Add `DETREND_MAX_XY_DEGREE` to the import list and the `robust_plane_detrend` call so the
function's name ("production" residual profile) matches what it measures.

### WR-03: `bin_profile`'s half-open binning window still silently drops the domain's exact trailing-edge sample (confirmed still open)

**File:** `src/targets.py:124-130`
**Issue:** `columns = (x_actual_mm >= x_center - half_step) & (x_actual_mm < x_center + half_step)`
is asymmetric (`>=` lower bound, `<` upper bound).
**Re-verified directly against real data:** `load_wyko_asc('data/raw/height_maps', 8)['x_actual_mm'][-1] == 100.0`
exactly, and for the last bin center `x_center=99.9`, the current half-open test selects one fewer
native column than an inclusive test would — the single native column at exactly
`x_actual_mm == 100.0` is structurally unreachable by any bin. Practical impact remains negligible
today (well above `MIN_COLUMNS_PER_BIN=10`), but the asymmetry is a real, unintentional boundary
artifact in an otherwise deliberately-conventioned codebase.
**Fix:** Make the window symmetric/inclusive (`x_actual_mm <= x_center + half_step`), then
re-verify no native column becomes double-counted between adjacent bins.

### WR-04: `load_wyko_asc` still never validates that the RAW_DATA body actually supplied `x_size * y_size` rows (confirmed still open)

**File:** `src/nsf_fmrg_data.py:186-203`
**Issue:** `z_mm_flat` is NaN-filled up front; the read loop only ever `break`s early when `count >=
n_expected` — there is no check that a truncated/malformed file supplied *at least* `n_expected`
rows before the `for line in f` loop exhausts the file. A short/corrupted `.ASC` body silently
produces a mostly-NaN height map instead of failing closed, inconsistent with the guard
immediately above it (lines 180-181) for missing header fields.
**Fix:** Validate `count == n_expected` (or `>=`) after the loop and raise `ValueError` on a
shortfall.

### WR-05: `extract_final_thermal_frames` can still silently return fewer than `EXTRACTED_THERMAL_FRAMES` frames (confirmed still open)

**File:** `src/nsf_fmrg_data.py:130-134`
**Issue:** `start_idx = max(0, stop_idx - EXTRACTED_THERMAL_FRAMES)` clamps to `0` with no length
check on `segment = frames[start_idx:stop_idx]`; a short laser-on interval silently returns fewer
than 400 frames.
**Fix:** Raise `ValueError` if `stop_idx - start_idx < EXTRACTED_THERMAL_FRAMES`.

### WR-06: `publish_staging_dir` still has no rollback if the final `staging_dir.rename(targets_dir)` step fails (confirmed still open)

**File:** `scripts/run_target_extraction.py:309-329`
**Issue:** The rename sequence (backup old `targets_dir` aside, then `staging_dir.rename(targets_dir)`)
has no `try/except` around the second rename. If it raises after the first rename has already
succeeded, `processed_data/targets` is left absent entirely, with the previous generation stranded
at `targets.previous` and no automatic restore. `tests/test_run_target_extraction.py` does not
exercise this specific failure window.
**Fix:** Wrap the second rename so a failure restores the backup to its original name before
re-raising.

### WR-07: `diagnose_track10_tail_collapse.py`'s "exact CURRENT production path" claim is stale and its checked-in CSV reports pre-Amendment-A6 numbers (confirmed still open)

**File:** `scripts/diagnose_track10_tail_collapse.py:57-63`
**Issue:** `measure_track`'s comment reads: `# The exact CURRENT production path (Amendment A5, no
new parameter, since none exists yet): observe only the currently-shipped fit.` This predates
Amendments A6/A7. Amendment A6 added `DETREND_MAX_XY_DEGREE`/`max_xy_degree` to the real production
call (`targets.extract_track_targets`, `src/targets.py:371-379`), but this diagnostic's
`robust_plane_detrend` call (lines 60-63) still omits `max_xy_degree`, and `DETREND_MAX_XY_DEGREE`
is not imported (lines 17-22).
**Re-verified with live numbers** (recomputing `measure_track`'s `departure` metric with and
without `max_xy_degree=DETREND_MAX_XY_DEGREE` against the real height-map data):

| track | as currently coded (no `max_xy_degree`) | actual production path (`max_xy_degree=2`) |
|---|---|---|
| 8  | 0.006038 | 0.003761 |
| 10 | 0.021200 | 0.011843 |
| 14 | 0.0000539 | 0.0001700 |
| 21 | 0.006166 | 0.005772 |

The checked-in `processed_data/diagnostics/track10_tail_collapse_diagnosis.csv` row for track 10
(`departure=0.021199873273603273`) exactly matches the *stale, pre-Amendment-A6* column, not the
real production value (`0.011843`) — the number Amendment A6's own doc comment in
`src/targets.py:50-56` cites as clearing the 0.012mm criterion tolerance. The checked-in diagnostic
artifact for the exact metric that justified Amendment A6 is one full amendment out of date.
**Fix:** Import `DETREND_MAX_XY_DEGREE` and pass `max_xy_degree=DETREND_MAX_XY_DEGREE` in the
`robust_plane_detrend` call at lines 60-63; update the stale comment; and regenerate
`track10_tail_collapse_diagnosis.csv` from the corrected code.

### WR-08 (new): `robust_plane_detrend`'s 3-round trim/refit loop discards its final trim decision, delivering a fit one iteration short of what the code implies

**File:** `src/nsf_fmrg_data.py:263-273`
**Issue:**
```python
keep = valid.copy()
coef = None
for _ in range(3):
    coef, *_ = np.linalg.lstsq(A[keep], z[keep], rcond=None)
    resid = z - A @ coef
    rv = resid[valid]
    lo, hi = np.nanpercentile(rv, [5, 95])
    keep_new = valid & (resid >= lo) & (resid <= hi)
    if keep_new.sum() < 100:
        break
    keep = keep_new
```
Each loop iteration fits with the *current* `keep`, then computes a *new* `keep_new` for the *next*
iteration. After the loop's third and final iteration, `keep` is updated to that iteration's
`keep_new`, but the loop ends — `coef` is never recomputed against that final, most-aggressively-
trimmed `keep`. The function therefore returns coefficients from a fit that reflects only 2 of the
3 apparent trim cycles; the third trim's entire purpose (informing a refit) is computed and then
discarded. This is a genuine off-by-one in the iteration's control flow, not a deliberate "use
penultimate fit" design — nothing in the function or its call sites documents an intent to stop one
short.
**Measured impact on the real, checked-in data** (recomputing with the fix — i.e., one additional
refit against the final `keep_new` — for all four tracks' actual production
`order=4, max_y_degree=2, max_xy_degree=2` fit):

| track | max |plane(fixed) − plane(shipped)| (mm) |
|---|---|
| 8  | 0.0017 |
| 10 | 0.0050 |
| 14 | 0.0036 |
| 21 | 0.0090 |

Track 21's discrepancy (0.009mm) is 75% of the 0.012mm `DETREND_MAX_XY_DEGREE` edge-shape-gap
tolerance this same phase locked via measurement in Amendment A6 (`src/targets.py:42-57`), and
Track 10's (0.005mm) is 10% of the 0.05mm `DETREND_MAX_Y_DEGREE` tolerance from Amendment A4
(`src/targets.py:21-41`). The Amendments' own "measured, not tuned" justification depends on the
shipped algorithm's actual behavior — which is self-consistent with today's tests (they measure
what the code does, not what it was meant to do) — but a future maintainer who "fixes" this loop to
genuinely perform 3 trim/refit cycles would silently shift every locked tolerance margin computed
against the current (short-by-one) fit, by amounts that are not negligible next to those margins.
**Fix:** Either perform an explicit final refit after the loop using the last `keep` value (`if
keep is not valid: coef, *_ = np.linalg.lstsq(A[keep], z[keep], rcond=None)`), or reduce the loop to
`range(2)` to make the actually-effective iteration count match the code's apparent behavior. Either
way, re-measure and re-lock the Amendment A4/A5/A6 tolerance margins against the corrected fit
before shipping the change, since the fix itself measurably moves the fitted surface.

### WR-09 (new): `diagnose_width_regression.py`'s sweep never applies the shipped `DETREND_MAX_Y_DEGREE`/`DETREND_MAX_XY_DEGREE` caps, so no row in its output reproduces the actual production configuration

**File:** `scripts/diagnose_width_regression.py:107-131`
**Issue:** `run_sweep` calls `robust_plane_detrend(data['Z_mm'], data['x_actual_mm'], data['y_mm'],
order=order, fit_mask=fit_mask)` for every `(order, bead_mask)` combination in the sweep — it never
passes `max_y_degree` or `max_xy_degree`, and neither `DETREND_MAX_Y_DEGREE` nor
`DETREND_MAX_XY_DEGREE` is imported (lines 17-22), unlike `diagnose_track10_coverage.py` (which at
least imports and partially applies `DETREND_MAX_Y_DEGREE`, per WR-02) and
`diagnose_track10_tail_collapse.py` (per WR-07). This means the checked-in
`processed_data/diagnostics/width_regression_sweep.csv` has no row corresponding to what
`targets.extract_track_targets` actually ships, including the row a reader would most naturally
mistake for "the production config": `order=4, continuity=True, bead_mask=True`.
**Verified numerically:** that row's medians (`track_8=0.741112, track_10=0.250938,
track_14=0.526432, track_21=0.241159`) diverge substantially from the real production values in
the checked-in `processed_data/targets/track_*_targets.npz` (`track_8=0.7401, track_10=0.3770,
track_14=0.6174, track_21=0.3825`, per `scripts/check_targets.py`'s own printed summary) — a >30%
relative difference on track 10 and track 21's medians. The file's module docstring
("Diagnose the Phase 1 width-ordering regression via a uniform detrend-order x continuity sweep")
gives no indication that none of its 12 rows use the caps that were the actual fix for that
regression (Amendments A5/A6, both authored after this sweep script per `git log`).
**Fix:** Either add a 13th "actual production" row (or a dedicated print line) that applies
`DETREND_MAX_Y_DEGREE`/`DETREND_MAX_XY_DEGREE` alongside `order=DETREND_POLY_ORDER`, or add an
explicit code comment/CSV column noting that every row in this sweep is deliberately uncapped and
therefore not comparable to the shipped artifacts.

## Info

### IN-01: Unused `import json` in `src/nsf_fmrg_data.py` (confirmed still open)

**File:** `src/nsf_fmrg_data.py:3`
**Issue:** `json` is imported and never referenced (`grep -n "json\." src/nsf_fmrg_data.py` finds
nothing).
**Fix:** Remove the unused import.

### IN-02: Diagnostic scripts still duplicate `write_csv`/table-printing helpers verbatim (confirmed still open)

**File:** `scripts/diagnose_track10_coverage.py:253-266`, `scripts/diagnose_track10_tail_collapse.py:78-91`, `scripts/diagnose_width_regression.py:150-161`
**Issue:** All three scripts define near-identical `print_measurement_table`/`write_csv` (or
`print_sweep_table`/`write_sweep_csv`) helpers plus a verbatim-repeated "sibling directory" comment.
**Fix:** Extract a shared `scripts/_diagnostic_io.py` helper module.

### IN-03: Redundant `.copy()` calls in `finalize_smoothed_boundaries` (confirmed still open)

**File:** `src/targets.py:285-286`
**Issue:** `y_lower`/`y_upper` are already freshly allocated by `nan_savgol` before being copied
again.
**Fix:** Remove the redundant `.copy()` calls.

### IN-04: `_loadmat_any`'s HDF5 fallback still swallows all conversion exceptions (confirmed still open)

**File:** `src/nsf_fmrg_data.py:46-51`
**Issue:** `except Exception: pass` inside the `h5py.visititems` callback discards any error, not
just the narrowly expected "not convertible" case. Documented in `CLAUDE.md` as an accepted, scoped
pattern; re-flagged per the adversarial mandate, not a new defect.
**Fix (optional):** Narrow to `(TypeError, ValueError)`.

### IN-05: `Y_STRIP_EXTENT_MM` in `scripts/check_targets.py` remains a hardcoded constant, not derived per-track (confirmed still open)

**File:** `scripts/check_targets.py:24-27`
**Issue:** The 1.907mm bound is a global constant documented as derived from all four current
headers, not re-derived from each track's actual header at check time.
**Fix (optional):** Derive per-track from `load_wyko_asc`'s header at check time.

### IN-06: Track 10 vs. Track 14 median width still violates the expected power-monotonic ordering (documented, not a code defect) (confirmed still open)

**File:** `processed_data/targets/track_10_targets.npz`, `processed_data/targets/track_14_targets.npz`
**Issue:** Reconfirmed by re-running `scripts/check_targets.py` against the live artifacts: Track 10
(350W) median width 0.3770mm is still less than Track 14 (300W) 0.6174mm, printed as `FLAG` by the
code's own ordering check, and explicitly documented as never used to tune locked extraction
constants.
**Fix:** None required for this phase; carry the caveat forward into downstream documentation.

### IN-07 (new): `scripts/check_targets.py` duplicates the target-grid start value as a bare literal alongside its own authoritative check

**File:** `scripts/check_targets.py:67-73`
**Issue:** `require(np.isclose(x_grid_mm[0], 20.1), ...)` hardcodes `20.1` even though the very next
check three lines later (`require(np.allclose(x_grid_mm, target_grid()), ...)`) already validates
the persisted grid against the authoritative `targets.target_grid()`/`TARGET_GRID_START_MM`. If
`TARGET_GRID_START_MM` were ever changed, this literal would silently drift out of sync with the
constant it's meant to be checking (the redundant `target_grid()` check would still catch a real
mismatch, but the specific, more readable error message on line 67-69 would fire for the wrong
reason). Same class of issue as the already-flagged `IN-05` (`Y_STRIP_EXTENT_MM`), in the same file.
**Fix (optional):** Replace the literal with `targets.TARGET_GRID_START_MM` (already importable
from `src/targets.py`, already imported indirectly via `target_grid`).

---

_Reviewed: 2026-07-22T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
