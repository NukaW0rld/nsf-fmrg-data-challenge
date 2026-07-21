---
phase: 01-target-extraction-contract
reviewed: 2026-07-21T21:31:10Z
depth: deep
files_reviewed: 27
files_reviewed_list:
  - processed_data/diagnostics/track10_coverage_diagnosis.csv
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
  info: 2
  total: 11
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-21T21:31:10Z
**Depth:** deep
**Files Reviewed:** 27
**Status:** issues_found

## Summary

This phase implements the local-track-width target extraction contract (`src/targets.py`), its supporting height-map/detrend loaders (`src/nsf_fmrg_data.py`), the atomic-publish extraction pipeline (`scripts/run_target_extraction.py`), a persisted-artifact checker (`scripts/check_targets.py`), two diagnostic scripts, and their test suites. The commit history shows this code has already been through several review-and-fix cycles (CR-01..CR-03, WR-01..WR-05 fixes visible in `git log`), and it shows: all 27 in-scope tests pass, `scripts/check_targets.py` passes against the persisted artifacts, path/symlink handling around the atomic publish step is unusually well hardened and well tested, and the numeric boundary-tracking logic (`halfmax_edges`, `nan_savgol`, gap filling, post-smoothing crossing invalidation) is covered by targeted regression tests that I traced by hand and found correct.

No BLOCKER-level defects were found — I could not construct a reachable path in this codebase's actual call sites that produces incorrect target values, a security vulnerability, or a crash under the four real tracks' data. I did find several WARNING-level correctness/robustness gaps in code paths that are either currently unreachable (masked by upstream conditions) or reachable only under conditions this phase does not fully test, plus a stale/misleadingly-named diagnostic artifact that is committed to git and could mislead a future reader about what the current production pipeline actually does. I verified this last point empirically (see WR-08) by re-running the detrend both with and without the production `max_y_degree` cap against `data/raw/height_maps/Heightmap_10.ASC`.

## Warnings

### WR-01: `robust_plane_detrend` validates `order`/`max_y_degree` after the early-return path, so invalid arguments can be silently swallowed

**File:** `src/nsf_fmrg_data.py:220-236`
**Issue:** The degenerate-data early return happens before argument validation:
```python
if valid.sum() < 100:
    return Z_mm.copy(), None

if not isinstance(order, (int, np.integer)) or order < 0:
    raise ValueError('order must be a non-negative integer.')
if max_y_degree is not None and (not isinstance(max_y_degree, (int, np.integer)) or max_y_degree < 0):
    raise ValueError('max_y_degree must be a non-negative integer or None.')
```
If a caller passes an invalid `order` (e.g. a negative int, a float, or a typo'd string) together with a height map/mask combination that happens to leave fewer than 100 valid fit points, the function returns `(Z_mm.copy(), None)` instead of raising — the caller's bug is masked as an ordinary "degenerate fallback" instead of surfacing as the intended fail-fast `ValueError`. This currently never triggers for the four production tracks (they always clear the 100-point floor with `order=DETREND_POLY_ORDER=4`), but it is a live gap in the function's own contract that any future caller (or a future amendment reusing `robust_plane_detrend` with an odd `order`) can hit silently.
**Fix:** Validate `order`/`max_y_degree` before the `valid.sum() < 100` early return:
```python
if not isinstance(order, (int, np.integer)) or order < 0:
    raise ValueError('order must be a non-negative integer.')
if max_y_degree is not None and (not isinstance(max_y_degree, (int, np.integer)) or max_y_degree < 0):
    raise ValueError('max_y_degree must be a non-negative integer or None.')

if valid.sum() < 100:
    return Z_mm.copy(), None
```

### WR-02: `load_wyko_asc` hardcodes `100.0` instead of reusing `COMMON_X_END_MM`

**File:** `src/nsf_fmrg_data.py:204`
**Issue:** `x_actual_raw = 100.0 - x_local` duplicates the value of `COMMON_X_END_MM = 100.0` (line 9) as a bare literal. If `COMMON_X_END_MM` is ever changed (e.g. to extend/shrink the physical scan window, which the module-level docstring at line 13-16 already anticipates for `THERMAL_MM_PER_FRAME`/`EXTRACTED_THERMAL_FRAMES`), this coordinate-flip line silently keeps using the old value, desynchronizing the height-map coordinate system from the thermal/common coordinate system it is supposed to share. This is exactly the kind of cross-cutting physical-alignment concern the project's own CLAUDE.md calls out as central ("Physical-coordinate alignment ... is the central cross-cutting concern threaded through all three loaders").
**Fix:**
```python
x_actual_raw = COMMON_X_END_MM - x_local
```

### WR-03: The `pixel_size_mm` presence guard lives only in `extract_track_targets`, not in `load_wyko_asc` itself

**File:** `src/nsf_fmrg_data.py:166-167,180`, `src/targets.py:304-305`
**Issue:** `parse_wyko_header` only writes `pixel_size_mm` into the returned header dict if the line is actually present in the `.ASC` file. `load_wyko_asc` then uses `header.get('pixel_size_mm', 0.003982)` (line 180) to compute `x_local_mm`/`y_mm`/`x_actual_mm` — silently falling back to a hardcoded default pixel size if the header field is missing — but never writes that fallback back into the returned `header` dict. The only place that actually checks for the field's presence and fails closed is `extract_track_targets` (`src/targets.py:304-305`), which is one specific caller. Any other caller of `load_wyko_asc` — `scripts/diagnose_track10_coverage.py:measure_track`, `scripts/diagnose_width_regression.py:run_sweep`, or a future notebook — gets no such protection and will silently compute physically wrong coordinates (using a made-up pixel size) for any `.ASC` file missing `pixel_size`, with no warning or error.
**Fix:** Move the presence check into `load_wyko_asc` itself (fail closed at the loader boundary, not just at one downstream caller), or have `parse_wyko_header`/`load_wyko_asc` write the fallback value back into the header so at least the provenance is visible:
```python
if 'pixel_size_mm' not in header:
    raise ValueError(f'{Path(path).name} header is missing pixel_size_mm.')
pixel = float(header['pixel_size_mm'])
```

### WR-04: `get_sem_tile_paths` only checks two levels of symlink ancestry, unlike the full-chain walk used elsewhere in this phase

**File:** `src/nsf_fmrg_data.py:142-150`
**Issue:**
```python
root = Path(sem_dir) / f'SEM_{track_id}' / 'PlainImages'
if not root.is_dir():
    raise ValueError(...)
if root.is_symlink() or root.parent.is_symlink():
    raise ValueError(f'SEM path must not be a symlink: {root}.')
```
This checks only `PlainImages` and its immediate parent (`SEM_<id>`). `scripts/run_target_extraction.py:reject_symlink_path` (lines 62-73), written in this same phase, walks the *entire* ancestor chain up to the project root for exactly this class of bug. If `sem_dir` itself (or any directory between it and `SEM_<id>`) were a symlink, `get_sem_tile_paths` would not catch it, inconsistent with the symlink-hardening standard the rest of this phase applies.
**Fix:** Reuse (or mirror) the ancestor-walking pattern from `reject_symlink_path` here, checking every parent between `root` and a caller-supplied trust boundary, not just the immediate parent.

### WR-05: `find_track_file`'s regex interpolates `track_id` without `re.escape`

**File:** `src/nsf_fmrg_data.py:32`
**Issue:**
```python
if re.search(rf'(^|[_\-\s]){track_id}($|[_\-\s\.])', name):
```
`track_id` is spliced directly into the regex pattern. Every current call site passes `track_id` from the fixed `TRACK_IDS = (8, 10, 14, 21)` tuple, so this is not exploitable today, but `find_track_file` is a general-purpose utility with no type constraint on `track_id`; a future caller passing a string containing regex metacharacters (e.g. `"1."`, `"(21)"`) would get silently wrong/undefined matching behavior instead of a clear error.
**Fix:**
```python
if re.search(rf'(^|[_\-\s]){re.escape(str(track_id))}($|[_\-\s\.])', name):
```

### WR-06: `publish_staging_dir`'s two-phase rename is not transactional — a mid-publish failure can leave `processed_data/targets/` entirely absent

**File:** `scripts/run_target_extraction.py:309-329`
**Issue:** The comment above the call site (`run_target_extraction.py:425-427`) states: "Only a fully successful, raw-audit-clean run is published atomically; a partial run's staging directory is discarded so the live processed_data/targets/ tree never mixes generations." The implementation is a two-step rename with no rollback:
```python
if targets_dir.exists():
    ...
    targets_dir.rename(backup_dir)          # step 1: old generation -> backup
if targets_dir.is_symlink() or staging_dir.is_symlink():
    raise ValueError(...)
staging_dir.rename(targets_dir)              # step 2: new generation -> live
```
Between step 1 and step 2, `targets_dir` does not exist at all. If `staging_dir.rename(targets_dir)` itself raises for any legitimate OS-level reason (e.g. `EXDEV` if `processed_data/` ever spans a filesystem/mount boundary, permission changes, a concurrent process interfering with the directory) after step 1 has already succeeded, the exception propagates out of `publish_staging_dir` uncaught by `run_pipeline` (the call at line 429 is not wrapped in `try/except`), leaving `processed_data/targets/` **missing entirely** rather than either the old generation (safe) or the new one (also safe) — a stronger failure mode than the "mixed generation" the code explicitly guards against. The previous generation is still recoverable from `targets_dir.previous`, but only manually; nothing in the code detects or reports this state.
**Fix:** Wrap the publish call in a try/except that, on any failure between the two renames, attempts to rename `backup_dir` back to `targets_dir` (best-effort restore), or perform the swap via a single `os.replace`-based directory swap / a symlink-indirection scheme so there is never a window where the live directory does not exist.

### WR-07: `extract_final_thermal_frames` raises an unhelpful `TypeError` instead of a clear `ValueError` when no laser-on interval is detected

**File:** `src/nsf_fmrg_data.py:104-129`
**Issue:** `detect_laser_on_interval` returns `(None, None, score, threshold)` from `largest_true_run` (line 92-101) when the laser-on score mask is never `True` for any frame. `extract_final_thermal_frames` then does `stop_idx = int(on_stop)` (line 128) unconditionally, which raises `TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'` — a confusing, implementation-leaking error instead of the module's own established fail-fast pattern (`raise ValueError('No thermal-like array found in MAT file.')`, line 71; `raise ValueError(f'No thermal file found for track {track_id} under {thermal_dir}.')`, line 121).
**Fix:**
```python
on_start, on_stop, score, threshold = detect_laser_on_interval(frames)
if on_start is None:
    raise ValueError(f'No laser-on interval detected for track {track_id}.')
stop_idx = int(on_stop)
```

### WR-08: `diagnose_track10_coverage.py`'s "production" residual profile omits the production `max_y_degree` cap, making the committed CSV stale/misleading

**File:** `scripts/diagnose_track10_coverage.py:60-65` (feeds into the committed `processed_data/diagnostics/track10_coverage_diagnosis.csv`)
**Issue:**
```python
def production_residual_profile(Z_mm, x_actual_mm, y_mm):
    fit_mask = bead_exclusion_mask(Z_mm)
    Zd, coef = robust_plane_detrend(
        Z_mm, x_actual_mm, y_mm, order=DETREND_POLY_ORDER, fit_mask=fit_mask,
    )
```
This omits `max_y_degree=DETREND_MAX_Y_DEGREE`, unlike the real production call in `src/targets.py:extract_track_targets` (lines 308-315), which was introduced by the later "Amendment A5" fix (commit `428af20`, after this diagnostic script was authored in commit `c0ef888`). The function is named `production_residual_profile` and its output feeds `rejection_reason_histogram`/the committed `track10_coverage_diagnosis.csv`, but it measures the **pre-fix, uncapped** detrend behavior, not what the pipeline actually ships today. I verified this directly: re-running the detrend for track 10 without `max_y_degree` reproduces the CSV's `rejection_ok=21`, while adding the production `max_y_degree=DETREND_MAX_Y_DEGREE` cap (as `extract_track_targets` actually does) yields 255 "ok" bins pre-smoothing, consistent with the 242/400 valid slots actually persisted in `processed_data/targets/track_10_targets.npz`. A reader (human or agent) who trusts the committed CSV or the "production" function name to reflect current behavior will draw the wrong conclusion about track 10's real coverage and about why bins are rejected.
**Fix:** Either update `production_residual_profile` to pass `max_y_degree=DETREND_MAX_Y_DEGREE` so it genuinely mirrors production, or rename it (e.g. `pre_fix_residual_profile`) and add a comment stating it intentionally reproduces the historical, pre-Amendment-A5 behavior for root-cause documentation purposes — then regenerate/annotate the committed CSV so it's clear which pipeline generation its numbers correspond to.

### WR-09: `bin_profile`'s `np.nanmedian` over an all-NaN column selection raises an unguarded `RuntimeWarning` on every production run

**File:** `src/targets.py:93-99`
**Issue:**
```python
def bin_profile(Zd, x_actual_mm, x_center):
    half_step = TARGET_GRID_STEP_MM / 2.0
    columns = (x_actual_mm >= x_center - half_step) & (x_actual_mm < x_center + half_step)
    if columns.sum() < MIN_COLUMNS_PER_BIN:
        return None
    return np.nanmedian(Zd[:, columns], axis=1)
```
`columns.sum() >= MIN_COLUMNS_PER_BIN` only guarantees enough *columns*, not that any of them are non-NaN for a given row; some rows in the selected slice can be entirely NaN (verified empirically — running `scripts/run_target_extraction.py` under `python -W error::RuntimeWarning` raises `RuntimeWarning: All-NaN slice encountered` from this exact line during the real track-10 extraction). The resulting NaN rows are handled correctly downstream (via `fill_small_gaps`/`halfmax_edges`), so this is not a correctness bug, but the warning is unguarded and will print on every production run for at least track 10, which is exactly the kind of "known, anticipated condition producing uncontrolled log noise" this project's own logging convention (print-based, deliberate CLI output) would want suppressed.
**Fix:** Suppress the anticipated warning explicitly rather than leaving it to fire silently into stderr:
```python
import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore', category=RuntimeWarning)
    return np.nanmedian(Zd[:, columns], axis=1)
```

## Info

### IN-01: Unnamed `1e-6` unit-conversion magic number in `load_wyko_asc`

**File:** `src/nsf_fmrg_data.py:196`
**Issue:** `z_mm_flat[count] = np.nan if z_tok.lower() == 'bad' else float(z_tok) * 1e-6` converts the raw Wyko `.ASC` z-value into millimeters via a bare `1e-6` literal with no named constant or comment explaining the source unit (presumably microns-times-something, or nanometers with an extra factor — not obvious from the code alone).
**Fix:** Extract to a named constant, e.g. `WYKO_RAW_Z_TO_MM = 1e-6  # raw ASC units -> mm`, and use it in place of the literal.

### IN-02: Track 10 barely clears the project-wide `MIN_VALID_FRACTION` coverage floor

**File:** `processed_data/targets/track_10_targets.npz`, `scripts/check_targets.py:30`
**Issue:** Track 10 persists at 242/400 = 60.5% valid coverage against a locked `MIN_VALID_FRACTION = 0.5` floor — the smallest margin of the four tracks (8: 91%, 14: 75%, 21: 81.25%) — and its median width (0.371 mm) is lower than track 14's (0.477 mm) despite track 10 having higher laser power (350W vs 300W), which `scripts/run_target_extraction.py`'s own `print_results` correctly flags as `FLAG` on the `10 vs 14` ordering check. This is a known, documented, and already-litigated data-quality condition per the codebase's own comments (Amendment A3/A4/A5, `01-11-*` decision references) and is explicitly *not* something the project wants used to further tune locked extraction constants — noted here only for completeness/visibility, not as a code defect.

---

_Reviewed: 2026-07-21T21:31:10Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
