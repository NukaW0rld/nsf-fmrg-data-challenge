---
phase: 01-target-extraction-contract
reviewed: 2026-07-21T00:00:00Z
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
  warning: 6
  info: 6
  total: 12
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-21T00:00:00Z
**Depth:** standard
**Files Reviewed:** 10 source/test files read and analyzed in full; 15 checked-in data/QA
artifacts (`.npz`, `.png`, `.csv`, `.json`) skimmed only for cross-consistency with the code, per
the task's scoping note, not reviewed as code.
**Status:** issues_found

## Summary

This is a fresh, complete replacement review produced after plans 01-13/01-14 landed Amendments A6
(cross-track/x interaction-degree cap, `DETREND_MAX_XY_DEGREE`) and A7 (run-merging +
tracked-candidate plausibility gate, `MAX_RUN_MERGE_GAP_PIXELS` / `MIN_TRACKED_LENGTH_RATIO`) on
top of the already-locked A1-A5 detrend/boundary-tracking contract. It does not diff against the
prior `01-REVIEW.md`; several items from that earlier pass (order/max_y_degree validation ordering,
the `KeyError`→`ValueError` fix for missing x_size/y_size, the `TypeError`→`ValueError` fix for a
missing laser-on interval, and passing `max_y_degree` through the coverage diagnostic) have since
been fixed in the codebase and are not repeated here; the `import json` dead-import finding has
not been fixed and is carried forward.

All three test suites (`tests/test_targets.py`, `tests/test_nsf_fmrg_data.py`,
`tests/test_run_target_extraction.py`) were executed in a fresh virtualenv and pass in full (33 + 13
+ 10 tests). `scripts/check_targets.py` was run against the real, checked-in
`processed_data/targets/*.npz` artifacts and passes all contract checks (including the documented
"FLAG" for the 10-vs-14 width ordering, which the codebase explicitly treats as a known,
un-tuned-for limitation rather than a defect).

The core `src/targets.py` extraction logic (`halfmax_edges`, `merge_adjacent_runs`,
`fill_small_gaps`, `bead_exclusion_mask`, `finalize_smoothed_boundaries`) and the
security/integrity hardening in `scripts/run_target_extraction.py` (symlink rejection,
`data/raw` snapshot-and-diff auditing, staged atomic publish) are well tested and internally
consistent with their own doc comments.

The main new defect class found in this pass is **drift between the production contract and the
diagnostic tooling that is supposed to mirror it**: `scripts/diagnose_track10_coverage.py`'s
`classify_column` and `production_residual_profile` predate Amendments A6/A7 and were never
updated after those amendments landed, despite an explicit in-code comment asserting the former
"must be kept in step" with `targets.halfmax_edges`. A second finding is a genuine, provable
off-by-one at the domain's trailing edge in `bin_profile`'s half-open binning window (confirmed
against the real track 8 height map, not just synthetic data). Neither is currently changing
pass/fail outcomes for the four shipped tracks, but both are real correctness gaps.

## Warnings

### WR-01: `diagnose_track10_coverage.py`'s `classify_column` has drifted out of sync with `targets.halfmax_edges` after Amendments A6/A7

**File:** `scripts/diagnose_track10_coverage.py:105-161`
**Issue:** The function's own comment states: "Mirrors targets.halfmax_edges' rejection branches
so this diagnostic can attribute a reason to each bin; must be kept in step with that function."
`targets.halfmax_edges` (Amendment A7, `src/targets.py:200-234`) now (1) merges
noise-fragmented above-threshold sub-runs via
`merge_adjacent_runs(all_true_runs(above), MAX_RUN_MERGE_GAP_PIXELS)` before building candidates,
and (2) when tracking (`previous_center is not None`), restricts selection to a `plausible` subset
of candidates whose length is at least `MIN_TRACKED_LENGTH_RATIO` of the largest same-column
candidate. `classify_column` does neither: it builds `candidates` directly from
`all_true_runs(above)` (no merge step, `scripts/diagnose_track10_coverage.py:122-126`) and, in the
tracked branch, selects `min(candidates, key=...)` over the raw candidate list with no plausibility
filter (`scripts/diagnose_track10_coverage.py:132-139`). The module's own import list confirms the
drift — it imports `all_true_runs` (line 27) but never imports `merge_adjacent_runs`,
`MAX_RUN_MERGE_GAP_PIXELS`, or `MIN_TRACKED_LENGTH_RATIO` from `targets`, even though these are now
load-bearing parts of the function it claims to mirror. Any rejection-reason histogram this
diagnostic produces today (e.g. `rejection_clipped_run_only`, `rejection_ok` counts) can therefore
diverge from what the actual production `extract_targets_from_arrays` path does for
noise-fragmented or ambiguous bead columns — precisely the failure mode A7 was written to fix.
**Fix:** Import and call the real helpers instead of re-implementing a stale copy:
```python
from targets import (
    ...,
    MAX_RUN_MERGE_GAP_PIXELS,
    MIN_TRACKED_LENGTH_RATIO,
    merge_adjacent_runs,
)

def classify_column(prof, y_mm, previous_center):
    ...
    above = np.where(finite, prof > threshold, False)
    merged_runs = merge_adjacent_runs(all_true_runs(above), MAX_RUN_MERGE_GAP_PIXELS)
    candidates = [(s, e) for s, e in merged_runs if s != 0 and e != len(prof)]
    if not candidates:
        return 'clipped_run_only', None
    if previous_center is None:
        start, stop = min(candidates, key=lambda run: (-(run[1] - run[0]), run[0]))
    else:
        max_len = max(stop - start for start, stop in candidates)
        plausible = [r for r in candidates if (r[1] - r[0]) >= MIN_TRACKED_LENGTH_RATIO * max_len]
        start, stop = min(plausible, key=lambda run: (...))
```
Better still, delete the re-implementation entirely and call `targets.halfmax_edges` directly (as
`diagnose_width_regression.py` already does), attributing `None` results to a generic "rejected"
bucket instead of maintaining a hand-synced copy.

### WR-02: `diagnose_track10_coverage.py`'s `production_residual_profile` omits the Amendment A6 `max_xy_degree` cap

**File:** `scripts/diagnose_track10_coverage.py:61-67`
**Issue:** `production_residual_profile` calls:
```python
Zd, coef = robust_plane_detrend(
    Z_mm, x_actual_mm, y_mm,
    order=DETREND_POLY_ORDER, fit_mask=fit_mask,
    max_y_degree=DETREND_MAX_Y_DEGREE,
)
```
without `max_xy_degree=DETREND_MAX_XY_DEGREE`. The actual production call in
`targets.extract_track_targets` (`src/targets.py:371-379`) passes both `max_y_degree` and
`max_xy_degree=DETREND_MAX_XY_DEGREE`. Amendment A6 landed after this diagnostic's one prior update
(which added only `max_y_degree`), so the function no longer measures the surface the pipeline
actually ships — despite its name explicitly claiming to produce the "production" residual
profile. Contrast with `diagnose_track10_tail_collapse.py`, whose equivalent omission is explicitly
documented in-line as intentional ("The exact CURRENT production path (Amendment A5, no new
parameter, since none exists yet)"); no such disclaimer exists in `diagnose_track10_coverage.py`,
so this reads as unintentional drift rather than a deliberate historical snapshot.
**Fix:** Add `DETREND_MAX_XY_DEGREE` to the import list (line 17-32) and pass it through:
```python
Zd, coef = robust_plane_detrend(
    Z_mm, x_actual_mm, y_mm,
    order=DETREND_POLY_ORDER, fit_mask=fit_mask,
    max_y_degree=DETREND_MAX_Y_DEGREE,
    max_xy_degree=DETREND_MAX_XY_DEGREE,
)
```

### WR-03: `bin_profile`'s half-open binning window silently drops the domain's exact trailing-edge sample

**File:** `src/targets.py:124-130`
**Issue:** `columns = (x_actual_mm >= x_center - half_step) & (x_actual_mm < x_center + half_step)`
is a half-open interval `[center-half_step, center+half_step)`. The target grid's last slot is
`x_center = 99.9` (`TARGET_GRID_START_MM + TARGET_GRID_STEP_MM * 399`), giving a window of
`[99.8, 100.0)` — which excludes any native column at exactly `x_actual_mm == 100.0`. Verified
directly against the real track 8 height map (`load_wyko_asc('data/raw/height_maps', 8)`):
`x_actual_mm[-1] == 100.0` exactly (because `x_actual_raw = 100.0 - x_local` and the native pixel
at `x_local == 0.0` maps to exactly `100.0`), and exactly one native column sits at that value. Its
window-boundary count confirms the drop: 50 columns match with the current half-open test
(`< 100.0`), versus 51 with an inclusive test (`<= 100.0`). Because no bin's window ever reaches
`>= 100.0`, that single native column is structurally unreachable by any bin — a real, systematic,
silent boundary bug. The leading edge does not exhibit the mirror-image problem in practice (real
native x starts at `20.264432`, not exactly `20.0`), but the asymmetry (`>=` on the lower bound,
`<` on the upper bound) is present in the code regardless of whether it currently bites on both
ends. Practical impact today is negligible (one fewer column out of ~50-51 in the last bin, well
above `MIN_COLUMNS_PER_BIN=10`), but it would matter more on lower-density data or if
`MIN_COLUMNS_PER_BIN` were ever raised, and it is inconsistent with a codebase that otherwise
prides itself on validated, deliberate boundary conventions (see the extensive A1-A7 doc comments).
**Fix:** Make the window symmetric/inclusive on both sides, or explicitly special-case the last
bin so the convention is deliberate rather than an accidental artifact of `<` vs `>=`:
```python
columns = (x_actual_mm >= x_center - half_step) & (x_actual_mm <= x_center + half_step)
```
(Re-verify afterward that no native column can now be double-counted between two adjacent bins.)

### WR-04: `load_wyko_asc` never validates that the RAW_DATA body actually supplied `x_size * y_size` rows

**File:** `src/nsf_fmrg_data.py:175-221`
**Issue:** `z_mm_flat` is pre-filled with `NaN` (line 187) and `count` is only ever compared against
`n_expected` to `break` early if the body has *enough* rows (lines 202-203:
`if count >= n_expected: break`). If the RAW_DATA section has *fewer* rows than `x_size * y_size`
implies (a truncated, corrupted, or header/body-mismatched `.ASC` file), the `for line in f` loop
simply exhausts the file and returns with `count < n_expected` — no exception is raised, and the
untouched tail of `z_mm_flat` stays silently `NaN`. This directly contradicts the "fail closed"
posture this same function otherwise enforces (e.g. the guard at lines 180-181 that raises
`ValueError` when `x_size`/`y_size` are missing from the header). A truncated or malformed file
would silently degrade into a mostly-NaN height map that only surfaces later, if at all, via
`check_targets.py`'s downstream `MIN_VALID_FRACTION` floor — several steps removed from the actual
root cause, and only if the shortfall happens to be large enough to trip that floor.
**Fix:** Validate the row count after the read loop and fail closed on a shortfall:
```python
if count < n_expected:
    raise ValueError(
        f'{path}: RAW_DATA body supplied {count} rows, expected {n_expected} '
        f'(x_size={x_size} * y_size={y_size}).'
    )
```

### WR-05: `extract_final_thermal_frames` can silently return fewer than `EXTRACTED_THERMAL_FRAMES` frames with no validation

**File:** `src/nsf_fmrg_data.py:130-134`
**Issue:** `start_idx = max(0, stop_idx - EXTRACTED_THERMAL_FRAMES)`. If the detected laser-on
interval ends (`stop_idx`) before 400 frames have elapsed since recording start, `start_idx` clamps
to `0` and `segment = frames[start_idx:stop_idx]` silently returns fewer than
`EXTRACTED_THERMAL_FRAMES` (400) frames, with no error raised and no field in the returned dict
flagging the shortfall. `tests/test_targets.py::test_target_grid_matches_thermal_centers` assumes
exactly 400 frames map 1:1 onto `targets.target_grid()`'s 400 slots; a short segment would silently
break that correspondence for any downstream consumer that assumes
`len(result['frames']) == 400` without checking.
**Fix:** Validate the segment length and fail closed, consistent with this function's other guards:
```python
if stop_idx - start_idx < EXTRACTED_THERMAL_FRAMES:
    raise ValueError(
        f'Track {track_id}: only {stop_idx - start_idx} frames available before the laser-on '
        f'stop index {stop_idx}, need {EXTRACTED_THERMAL_FRAMES}.'
    )
```

### WR-06: `publish_staging_dir` has no rollback if the final `staging_dir.rename(targets_dir)` step fails

**File:** `scripts/run_target_extraction.py:309-329`
**Issue:** The publish sequence is: (1) remove any stale `.previous` backup, (2) rename the live
`targets_dir` to the backup path, (3) rename `staging_dir` into `targets_dir`, (4) remove the
backup. If step (3) raises (e.g. `OSError` from a cross-device rename, permission error, or disk
full) after step (2) has already succeeded, the process is left with **no** live
`processed_data/targets` directory at all — it was renamed away in step (2), and the new generation
in `staging_dir` was never moved into place. The previous generation still exists at
`targets_dir.previous`, but nothing in this function (or its caller) restores it automatically;
`check_targets.py` and any other consumer of `processed_data/targets` would find the directory
missing until a human intervenes. `tests/test_run_target_extraction.py` covers many adjacent
failure modes (symlinks at every touched path, integrity-audit failures) but does not exercise this
specific rename-order failure window.
**Fix:** Wrap step (3) so a failure restores the backup to its original name before re-raising:
```python
try:
    staging_dir.rename(targets_dir)
except BaseException:
    if not targets_dir.exists() and backup_dir.exists():
        backup_dir.rename(targets_dir)  # restore the previous generation
    raise
```

## Info

### IN-01: Unused `import json` in `src/nsf_fmrg_data.py`

**File:** `src/nsf_fmrg_data.py:3`
**Issue:** `json` is imported but never referenced anywhere in the module (`grep -n "json\."
src/nsf_fmrg_data.py` finds nothing; `json` only appears in the `import json` line itself). This
was flagged in the prior review pass and has not been fixed.
**Fix:** Remove the unused import.

### IN-02: Diagnostic scripts duplicate `write_csv`/table-printing helpers verbatim

**File:** `scripts/diagnose_track10_coverage.py:253-266`, `scripts/diagnose_track10_tail_collapse.py:78-91`, `scripts/diagnose_width_regression.py:150-161` (`write_sweep_csv`/`print_sweep_table`, same shape)
**Issue:** All three diagnostic scripts define nearly identical `print_measurement_table`/
`write_csv` helpers (field-name-driven CSV writer + comma-joined console table), along with a
verbatim-repeated multi-line comment explaining why `processed_data/diagnostics/` must be a
sibling of `processed_data/targets/`. This is one-off diagnostic tooling so the duplication is
low-risk, but it increases the chance that a future fix (e.g. to the "sibling directory" invariant,
or to CSV formatting) is applied to only one of the three copies.
**Fix:** Extract a small shared helper module (e.g. `scripts/_diagnostic_io.py`) with
`write_csv(csv_path, rows)` and `print_measurement_table(rows)`, and import it from all three
scripts.

### IN-03: Redundant `.copy()` calls in `finalize_smoothed_boundaries`

**File:** `src/targets.py:280-289`
**Issue:** `y_lower = nan_savgol(y_lower_raw)` already returns a freshly allocated array
(`nan_savgol` builds `out = np.full(...)` internally), so the subsequent `y_lower = y_lower.copy()`
/ `y_upper = y_upper.copy()` (lines 285-286) copy an array that is already private to this
function. Harmless, but it is a needless allocation that obscures that no aliasing concern exists
at this point.
**Fix:** Remove the redundant `.copy()` calls; the arrays returned by `nan_savgol` are already safe
to mutate in place.

### IN-04: `_loadmat_any`'s HDF5 fallback silently swallows all conversion exceptions

**File:** `src/nsf_fmrg_data.py:38-53`
**Issue:** `except Exception: pass` inside the `h5py.visititems` callback (lines 49-51) discards
*any* error converting a dataset to a NumPy array, not just the narrowly expected "not convertible"
case. `CLAUDE.md` documents this as an accepted, scoped pattern ("best-effort array conversion...
only used when skipping a single non-convertible dataset entry is safe"), so this is not a new
defect introduced by this phase, but it is worth re-flagging under the adversarial review mandate:
a future MAT v7.3 file with an unexpected dataset structure could have its real thermal array
silently dropped from the `out` dict with no diagnostic trace of why it was skipped.
**Fix (optional):** Narrow the catch to the specific conversion failure modes actually expected
(e.g. `TypeError, ValueError`) so unrelated errors (e.g. `OSError` from a corrupted HDF5 chunk)
still propagate.

### IN-05: `Y_STRIP_EXTENT_MM` in `scripts/check_targets.py` is a hardcoded constant, not derived from each track's actual header

**File:** `scripts/check_targets.py:24-30`
**Issue:** The 1.907 mm bound is documented as derived from
`y_size * pixel_size_mm = 480 * 0.003982 mm` "for all four current Heightmap_*.ASC headers." This
is correct today, but the check does not read each track's actual header to confirm the assumption
still holds; if a future dataset revision changes `y_size`/`pixel_size_mm` for any track, this
bound would silently become wrong (too loose or too strict) rather than failing loudly.
**Fix:** Optional hardening — derive the per-track bound from `load_wyko_asc`'s header
(`y_size * pixel_size_mm`) at check time instead of a single global constant, or add an explicit
re-derivation/assertion against the persisted header values.

### IN-06: Track 10 vs. Track 14 median width still violates the expected power-monotonic ordering (documented, not a code defect)

**File:** `processed_data/targets/track_10_targets.npz`, `processed_data/targets/track_14_targets.npz`; surfaced via `scripts/check_targets.py` output
**Issue:** Track 10 (350 W) has a smaller median width (0.3770 mm, measured directly against the
checked-in artifacts in this pass) than Track 14 (300 W, 0.6174 mm), inverting the expected "higher
laser power → wider track" relationship that holds for the other adjacent pairs (8 vs 10, 14 vs
21). The code already classifies and prints this as a `FLAG` and explicitly states such flags are
"documented and never used to tune locked extraction constants," so this is not treated as a code
bug in this review either. Noted for continuity with the prior review pass, since the underlying
numbers shifted materially after Amendments A6/A7 (previously 0.3713 mm vs. 0.4765 mm) but the
ordering violation itself persists.
**Fix:** None required for this phase; carry the caveat forward into any downstream
documentation/spec that consumes these four `.npz` files as ground truth.

---

_Reviewed: 2026-07-21T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
