---
phase: 01-target-extraction-contract
reviewed: 2026-07-23T02:15:00Z
depth: standard
files_reviewed: 29
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
  info: 7
  total: 14
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-23T02:15:00Z
**Depth:** standard
**Files Reviewed:** 29
**Status:** issues_found

## Summary

I read every file in scope in full, ran all three checked-in test suites against the real `.venv`
(`test_nsf_fmrg_data.py` 13/13, `test_targets.py` 38/38, `test_run_target_extraction.py` 10/10 —
all pass), and independently loaded the four committed `processed_data/targets/*.npz` artifacts to
confirm their shapes/dtypes/valid-counts match what `scripts/check_targets.py` asserts (8→368/400,
10→232/400, 14→309/400, 21→338/400 valid slots). No hardcoded secrets, injection vectors, unsafe
deserialization, or `eval`/`exec` usage anywhere in scope; the symlink/path-escape/raw-integrity
hardening in `run_target_extraction.py` is thorough and exercised by dedicated tests. No
Critical/Blocker-severity finding is warranted.

This codebase has already been through several review-and-fix cycles for this phase (visible in
git log and in `.planning/phases/01-target-extraction-contract/01-REVIEW-FIX.md`), and most of the
files in scope are unchanged since the last pass. I independently re-derived (rather than copied)
the two most consequential remaining issues to confirm they still reproduce on the current tree:

- **WR-01** (`robust_plane_detrend`'s trim/refit loop discards its final trim decision): I
  reproduced this directly against the real, checked-in height-map data by adding an explicit final
  refit against the loop's last `keep` set and diffing the resulting fitted plane against the
  shipped configuration (`order=4, max_y_degree=2, max_xy_degree=2`). Max absolute plane difference:
  track 8 = 0.0017mm, track 10 = 0.0050mm, track 14 = 0.0036mm, track 21 = 0.0090mm — the largest of
  these is ~75% of the 0.012mm `DETREND_MAX_XY_DEGREE` edge-shape-gap tolerance that was locked via
  precise measurement (`src/targets.py:42-57`, Amendment A6). This is not a documented "stop one
  short" design choice; it is a genuine control-flow off-by-one that measurably moves the fitted
  surface by amounts comparable to the margins the phase's own locked amendments were tuned
  against.
- **WR-02** (`bin_profile`'s asymmetric half-open binning window): I confirmed
  `load_wyko_asc(...)['x_actual_mm'][-1] == 100.0` exactly for all four tracks, and the target
  grid's last slot is centered at `x=99.9` with `half_step=0.1`, so the strict `<` upper bound
  structurally excludes the one native column at `x=100.0mm` from ever being binned. Practical
  impact is currently negligible (the last bin still has far more than `MIN_COLUMNS_PER_BIN=10`
  native columns) but it is a real, unintentional boundary asymmetry.

Everything else below was independently re-read against the current file contents (not assumed from
prior review prose) and is still present on this tree.

## Warnings

### WR-01: `robust_plane_detrend`'s 3-round trim/refit loop discards its final trim decision

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
Each iteration fits with the *current* `keep`, then computes `keep_new` for the *next* iteration.
After the final iteration, `keep` is updated to `keep_new` but the loop ends — `coef` is never
refit against that final, most-trimmed `keep`. The returned coefficients reflect a fit against the
second-to-last trim, not the third one the loop appears to perform. Independently reproduced against
the real `data/raw/height_maps/*.ASC` data with the shipped production parameters (see Summary):
max plane deltas of 0.0017–0.0090mm across the four tracks, the largest being ~75% of the 0.012mm
tolerance Amendment A6 was measured against.
**Fix:**
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
coef, *_ = np.linalg.lstsq(A[keep], z[keep], rcond=None)  # final refit against the last trim
```
Re-measure and re-lock the Amendment A4/A5/A6 tolerance margins after this fix, since it moves the
fitted surface by amounts comparable to those margins.

### WR-02: `bin_profile`'s half-open binning window silently drops the domain's exact trailing-edge sample

**File:** `src/targets.py:124-130`
**Issue:** `columns = (x_actual_mm >= x_center - half_step) & (x_actual_mm < x_center + half_step)`
is asymmetric (inclusive lower bound, strict upper bound). `x_actual_mm` reaches exactly `100.0mm`
for every track (confirmed against the real data), and the last target-grid slot is centered at
`99.9mm` with `half_step=0.1`, making the upper bound exactly `100.0`. The strict `<` means the
native column at `x_actual_mm == 100.0` can never be selected by any bin. Currently harmless
(comfortably above `MIN_COLUMNS_PER_BIN=10`) but is an unintentional inconsistency in a codebase
that is otherwise deliberate about inclusive/exclusive conventions elsewhere.
**Fix:** Make the window symmetric for the final bin (e.g. `x_actual_mm <= x_center + half_step`
combined with a strict lower bound on the *next* bin to avoid double-counting), or explicitly
document the exclusion as intentional.

### WR-03: `load_wyko_asc` never validates that the `RAW_DATA` body actually supplied `x_size * y_size` rows

**File:** `src/nsf_fmrg_data.py:186-204`
**Issue:** `z_mm_flat` is NaN-filled up front, and the read loop only breaks early via
`if count >= n_expected: break`. There is no check that a truncated/malformed `.ASC` file actually
supplied at least `n_expected` data rows. A short or corrupted height-map file would silently
produce a mostly-NaN `Z_mm` array (reshaped to the *declared* `x_size`/`y_size` regardless of how
many rows were actually read) instead of failing closed — inconsistent with the guard three lines
above it (`if 'x_size' not in header or 'y_size' not in header: raise ValueError(...)`).
**Fix:**
```python
Z_x_y = z_mm_flat.reshape((x_size, y_size))
if count < n_expected:
    raise ValueError(
        f'{path} RAW_DATA body supplied {count} rows, expected {n_expected} '
        f'(x_size={x_size} * y_size={y_size}).'
    )
```

### WR-04: `extract_final_thermal_frames` does not validate the extracted segment actually reaches `EXTRACTED_THERMAL_FRAMES` (400) frames

**File:** `src/nsf_fmrg_data.py:118-141`, specifically line 131
**Issue:** `start_idx = max(0, stop_idx - EXTRACTED_THERMAL_FRAMES)` clamps to `0` without checking
`stop_idx >= EXTRACTED_THERMAL_FRAMES`. If a thermal `.mat` file's detected laser-on interval ends
before frame 400, `segment`/`x_mm_center` are silently shorter than 400 samples instead of raising.
Not exercised by the currently-shipped target-extraction pipeline (which only touches height maps),
so zero current blast radius, but every downstream consumer assumes a fixed 400-frame
correspondence with `targets.target_grid()` (see `tests/test_targets.py::test_target_grid_matches_thermal_centers`
and the module comment at `src/nsf_fmrg_data.py:13-16`).
**Fix:**
```python
stop_idx = int(on_stop)
if stop_idx < EXTRACTED_THERMAL_FRAMES:
    raise ValueError(
        f'Laser-on interval for track {track_id} ends at frame {stop_idx}, '
        f'fewer than the required {EXTRACTED_THERMAL_FRAMES} frames.'
    )
start_idx = stop_idx - EXTRACTED_THERMAL_FRAMES
```

### WR-05: `publish_staging_dir` has no rollback if the final `staging_dir.rename(targets_dir)` step fails

**File:** `scripts/run_target_extraction.py:309-329`
**Issue:** The publish sequence backs up the old `targets_dir` to `targets_dir.previous`, then
renames `staging_dir` onto `targets_dir` with no `try/except` around the second rename. If that
rename raises after the first rename has already succeeded (cross-device rename, disk full,
permission error), `processed_data/targets` is left **absent entirely**, with the previous
generation stranded at `targets.previous` and no automatic restore.
**Fix:**
```python
if targets_dir.is_symlink() or staging_dir.is_symlink():
    raise ValueError(f"Refusing to rename a symlinked path: {staging_dir} -> {targets_dir}.")
try:
    staging_dir.rename(targets_dir)
except BaseException:
    if backup_dir.exists() and not targets_dir.exists():
        backup_dir.rename(targets_dir)
    raise
```

### WR-06: `diagnose_track10_tail_collapse.py`'s "exact CURRENT production path" comment and committed CSV are stale — they omit `DETREND_MAX_XY_DEGREE`

**File:** `scripts/diagnose_track10_tail_collapse.py:17-22,57-63`
**Issue:** The comment at lines 57-59 reads `# The exact CURRENT production path (Amendment A5, no
new parameter, since none exists yet): observe only the currently-shipped fit.` This predates
Amendment A6, which added `DETREND_MAX_XY_DEGREE`/`max_xy_degree` to the real production call in
`targets.extract_track_targets` (`src/targets.py:412-421`). This script's `robust_plane_detrend`
call still omits `max_xy_degree`, and `DETREND_MAX_XY_DEGREE` is absent from its import list (only
`DETREND_MAX_Y_DEGREE` is imported). The committed
`processed_data/diagnostics/track10_tail_collapse_diagnosis.csv` row for track 10
(`departure=0.021199873273603273`) reflects this uncapped-in-x fit, not the actual shipped
production value — the module-level comment block in `src/targets.py:42-57` (Amendment A6) cites a
different measured number (`0.0118mm`) as what clears the 0.012mm criterion. The checked-in
diagnostic artifact for the exact metric that justified a locked, load-bearing constant is one
amendment out of date, and its own inline comment affirmatively (and incorrectly) claims otherwise.
**Fix:** Import `DETREND_MAX_XY_DEGREE`, pass `max_xy_degree=DETREND_MAX_XY_DEGREE` in the
`robust_plane_detrend` call, correct the stale comment, and regenerate the CSV.

### WR-07: `diagnose_width_regression.py`'s sweep never applies the shipped `DETREND_MAX_Y_DEGREE`/`DETREND_MAX_XY_DEGREE` caps or the Mechanism B continuity gate, so no row reproduces the real production configuration

**File:** `scripts/diagnose_width_regression.py:107-131`
**Issue:** `run_sweep` calls `robust_plane_detrend(..., order=order, fit_mask=fit_mask)` for every
`(order, bead_mask)` combination — neither `max_y_degree` nor `max_xy_degree` is ever passed, and
neither constant is imported. Separately, `extract_swept` (lines 46-78) calls
`halfmax_edges(prof, y_mm, previous_center=query_center)` without ever passing
`previous_length_mm`, so the sweep also never exercises the Mechanism B history-plausibility gate
that `targets.extract_targets_from_arrays` uses in production. As a result, no row of the
(currently untracked, unlike its sibling diagnostic CSVs) `width_regression_sweep.csv` corresponds
to what `targets.extract_track_targets` actually ships — including the row a reader would most
naturally mistake for "the production config" (`order=4, continuity=True, bead_mask=True`).
**Fix:** Add a dedicated "actual production" row/column that applies
`DETREND_MAX_Y_DEGREE`/`DETREND_MAX_XY_DEGREE` alongside `order=DETREND_POLY_ORDER` and threads
`previous_length_mm` through `extract_swept`, or at minimum add an explicit comment/CSV column
stating every row is deliberately simplified and therefore not comparable to the shipped artifacts.
Commit `width_regression_sweep.csv` alongside its siblings or add it to `.gitignore` — right now it
is neither.

## Info

### IN-01: Unused `import json` in `src/nsf_fmrg_data.py`

**File:** `src/nsf_fmrg_data.py:3`
**Issue:** `json` is imported at module scope and never referenced anywhere in the file.
**Fix:** Remove the unused import.

### IN-02: The three `scripts/diagnose_*.py` files duplicate `write_csv`/table-printing helpers and a verbatim explanatory comment

**File:** `scripts/diagnose_track10_coverage.py:283-296`, `scripts/diagnose_track10_tail_collapse.py:78-91`, `scripts/diagnose_width_regression.py:150-161`
**Issue:** All three scripts define near-identical `print_measurement_table`/`write_csv` (or
`print_sweep_table`/`write_sweep_csv`) helpers, plus a verbatim-repeated "diagnostics/ is a SIBLING
of targets/, not a child" comment explaining the same publish-collision hazard.
**Fix:** Extract a shared `scripts/_diagnostic_io.py` helper module.

### IN-03: Redundant `.copy()` calls in `finalize_smoothed_boundaries`

**File:** `src/targets.py:315-323`
**Issue:** `y_lower = nan_savgol(y_lower_raw)` already returns a freshly allocated array (`nan_savgol`
builds `out = np.full(...)` internally); the subsequent `y_lower = y_lower.copy()` /
`y_upper = y_upper.copy()` copy arrays nothing else references.
**Fix:** Remove the redundant `.copy()` calls.

### IN-04: `Y_STRIP_EXTENT_MM` in `scripts/check_targets.py` is a hardcoded constant, not derived per-track from the header at check time

**File:** `scripts/check_targets.py:24-30`
**Issue:** The `1.907mm` bound is documented as derived from `y_size * pixel_size_mm` for all four
current `Heightmap_*.ASC` headers, but is not re-derived from each track's actual header at check
time. A future track with a different `pixel_size_mm`/`y_size` would silently be checked against
the wrong bound instead of failing loudly or adapting.
**Fix (optional):** Derive per-track from `load_wyko_asc`'s header at check time.

### IN-05: `scripts/check_targets.py` duplicates the target-grid start value as a bare literal alongside its own authoritative check

**File:** `scripts/check_targets.py:67-73`
**Issue:** `require(np.isclose(x_grid_mm[0], 20.1), ...)` hardcodes `20.1` even though the very next
check already validates the persisted grid against the authoritative `targets.target_grid()`. If
`TARGET_GRID_START_MM` changed, this literal would silently produce a misleadingly-worded failure
message rather than staying in sync with the constant it is meant to describe.
**Fix (optional):** Replace the literal with `targets.TARGET_GRID_START_MM`.

### IN-06: `resolve_raw_dir` is validated twice on every invocation

**File:** `scripts/run_target_extraction.py:35-59`
**Issue:** `resolve_repository_root` calls `resolve_raw_dir(candidate)` purely for its validating
side effect and discards the result; every caller (`run_pipeline`, `check_targets.py`, all three
`diagnose_*` scripts) then calls `resolve_raw_dir(project_root)` again immediately afterward.
Harmless (idempotent, cheap) but undocumented duplicated validation work.
**Fix:** Have `resolve_repository_root` return `(project_root, raw_dir)` so callers reuse the
already-validated `raw_dir`, or document the intentional redundancy.

### IN-07: Amendment A8's Mechanism B history gate estimates a candidate's length one grid step shorter than how `previous_length_mm` itself is computed

**File:** `src/targets.py:248-254`
**Issue:** `_is_implausible_versus_history` computes `length_mm = y_mm[stop - 1] - y_mm[start]` for a
half-open candidate run `[start, stop)`, i.e. `(stop - start - 1) * dy`. The caller
(`extract_targets_from_arrays`) derives `previous_length_mm` from the actual returned, linearly
interpolated edges (`edges[1] - edges[0]`), which approximate `(stop - start) * dy` — one grid step
longer. With `dy ≈ 0.004mm` and observed `previous_length_mm` values roughly `0.1–1.4mm`, this is a
small (~0.3–4%) systematic underestimate of every candidate's length versus
`MIN_TRACKED_LENGTH_RATIO * previous_length_mm`, which could tip a genuinely borderline candidate
from "plausible" to "implausible" purely due to this internal inconsistency. Not exercised by any
Amendment A8 regression test (all use candidates far from the 0.5x boundary).
**Fix:** Use the same span convention as the caller, e.g. `length_mm = y_mm[stop] - y_mm[start]`
(safe: `stop < len(y_mm)` is guaranteed by the earlier non-edge-run filter).

---

_Reviewed: 2026-07-23T02:15:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
