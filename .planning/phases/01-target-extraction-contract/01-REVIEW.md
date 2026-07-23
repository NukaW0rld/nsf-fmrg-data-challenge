---
phase: 01-target-extraction-contract
reviewed: 2026-07-23T00:00:00Z
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
  warning: 2
  info: 5
  total: 7
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-23T00:00:00Z
**Depth:** standard
**Files Reviewed:** 29
**Status:** issues_found

## Summary

This is a re-review of the target-extraction contract deliverable against its current state
(latest commit `3f87937`, which comment-only disclosed the prior review's WR-01 finding). I
re-verified the whole surface rather than trusting the prior pass: `src/targets.py` (extraction
pipeline: binning, half-max boundary tracking with continuity/history gating, run merging, bead
masking, Savitzky-Golay-style smoothing, provenance), the `src/nsf_fmrg_data.py` diff (fail-fast
validation additions, and the centered/degree-capped polynomial `robust_plane_detrend` basis),
`scripts/run_target_extraction.py`'s atomic-publish/symlink/raw-integrity pipeline,
`scripts/check_targets.py`'s persisted-artifact contract checks, all three `scripts/diagnose_*`
investigation tools, and the full test suite.

All 68 tests pass (`tests/test_nsf_fmrg_data.py` 13/13, `tests/test_targets.py` 38/38,
`tests/test_run_target_extraction.py` 10/10, run under `.venv`). Re-running
`scripts/check_targets.py` against the committed `processed_data/targets/` artifacts passes
end-to-end, including the documented `10 vs 14` width-ordering `FLAG` (explicitly accepted by the
project and not re-litigated here). The four `.npz` files have the expected keys/dtypes/shapes,
`manifest.json`'s digest matches `extraction_params.json`, and the 12 QA PNGs are well-formed
non-empty images. The symlink/path-traversal hardening in `run_target_extraction.py` (CR-02/CR-03)
is exercised by a thorough dedicated test file and I found no bypass. The centered/capped
polynomial basis in `robust_plane_detrend` is internally consistent (fit and reconstruction share
the same exponent list and center point), and its validation-before-degenerate-fallback ordering
matches the documented WR-02 history.

**The prior review's WR-01** (`diagnose_track10_coverage.py`'s `classify_column` drifting out of
sync with `targets.halfmax_edges` after the Amendment A8 Mechanism A/B fix) **is now resolved** —
commit `3f87937` added an explicit, accurate disclosure comment (`scripts/diagnose_track10_coverage.py:110-125`)
stating the diagnostic and its committed CSV are a stale historical baseline that must never be
read as live production characterization. I verified the comment's factual claims against the
current `src/targets.py:212-261` and they are correct.

Three of the prior review's Info-level findings remain unaddressed in the current file state and
are restated below (IN-01, IN-02, IN-03 below correspond to the prior pass's IN-02, IN-03, IN-01).
I additionally found one new Warning (thermal frame-count validation gap, not previously reviewed)
and elevated the prior pass's IN-04 (`pixel_size_mm` silent fallback) to Warning on independent
review, since it is reachable, unguarded, silent-wrong-output territory in three shipped scripts,
not just a theoretical future caller. One new Info item is added for an inconsistency in symlink
defense depth.

## Warnings

### WR-01: `load_wyko_asc`'s silent `pixel_size_mm` fallback is unguarded in every direct caller except the one that persists targets

**File:** `src/nsf_fmrg_data.py:184` (fallback); guarded only at `src/targets.py:409-410`
**Issue:** `load_wyko_asc` computes physical coordinate arrays (`x_local_mm`, `x_actual_mm`,
`y_mm`) using `pixel = float(header.get('pixel_size_mm', 0.003982))`. If a `Heightmap_*.ASC`
header is missing the `pixel_size_mm` field, this silently substitutes a hardcoded legacy default
instead of raising, and returns an otherwise normal-looking result dict — the function never
signals that a fallback was used. The *only* guard against this anywhere in the codebase is in
`targets.extract_track_targets` (`if 'pixel_size_mm' not in data['header']: raise
ValueError(...)`), which runs after `load_wyko_asc` has already done the (potentially wrong-scale)
coordinate math, and which only protects the single call site that ultimately writes
`processed_data/targets/*.npz`. `scripts/diagnose_track10_coverage.py`,
`scripts/diagnose_track10_tail_collapse.py`, and `scripts/diagnose_width_regression.py` all call
`nsf_fmrg_data.load_wyko_asc(height_dir, track_id)` directly and never check for the field's
presence. If a future or malformed `Heightmap_*.ASC` omits `pixel_size_mm`, these three
diagnostics would silently compute every downstream mm-scaled quantity (widths, shape-gap
departures, design-matrix conditioning) at the wrong physical scale with no error — the exact
class of silent-wrong-number failure the rest of this phase's hardening work (the `x_size`/`y_size`
guard two lines above this one, WR-02/WR-03 on `robust_plane_detrend`, WR-04 on the laser-on
interval) was specifically written to eliminate.
**Fix:** Move the presence check into `load_wyko_asc` itself, next to the existing
`x_size`/`y_size` guard:
```python
if 'x_size' not in header or 'y_size' not in header:
    raise ValueError(f'{path} header is missing X Size/Y Size fields.')
if 'pixel_size_mm' not in header:
    raise ValueError(f'{path} header is missing pixel_size_mm.')
x_size = int(header['x_size'])
y_size = int(header['y_size'])
pixel = float(header['pixel_size_mm'])
```
This also makes `targets.extract_track_targets`'s own downstream check (`src/targets.py:409-410`)
redundant but harmless, or lets it be removed.

### WR-02: `extract_final_thermal_frames` does not validate the extracted segment actually has `EXTRACTED_THERMAL_FRAMES` (400) frames

**File:** `src/nsf_fmrg_data.py:118-141`, specifically line 131
**Issue:** `start_idx = max(0, stop_idx - EXTRACTED_THERMAL_FRAMES)` clamps to 0 without checking
`stop_idx >= EXTRACTED_THERMAL_FRAMES`. If a thermal `.mat` file's detected laser-on interval ends
before frame 400 (`on_stop < 400`), the returned `segment`/`x_mm_center` arrays are silently
shorter than 400 samples instead of raising. Every consumer in this codebase assumes a fixed
400-element correspondence between thermal frames and `targets.target_grid()`
(`tests/test_targets.py::test_target_grid_matches_thermal_centers` derives its expected grid
directly from `nsf_fmrg_data.EXTRACTED_THERMAL_FRAMES`, and the module comment added in this same
diff at `src/nsf_fmrg_data.py:13-16` explicitly documents that this constant's value is load-bearing
for that correspondence). This function received three new fail-fast guards in this same diff
(missing file, unresolved laser-on interval, filename mismatch) but the short-segment case was not
covered, and no test exercises `on_stop < EXTRACTED_THERMAL_FRAMES`. Not exercised by this phase's
shipped pipeline (target extraction only touches height maps), so it has zero current blast
radius, but it is part of the exact same hardening pass and will be load-bearing the moment a
later phase aligns thermal frames against the target grid.
**Fix:**
```python
if on_stop is None:
    raise ValueError(f'No laser-on interval detected for track {track_id} in {path}.')
stop_idx = int(on_stop)
if stop_idx < EXTRACTED_THERMAL_FRAMES:
    raise ValueError(
        f'Laser-on interval for track {track_id} ends at frame {stop_idx}, '
        f'fewer than the required {EXTRACTED_THERMAL_FRAMES} frames.'
    )
start_idx = stop_idx - EXTRACTED_THERMAL_FRAMES
```

## Info

### IN-01: Unused `import json` in `src/nsf_fmrg_data.py`

**File:** `src/nsf_fmrg_data.py:3`
**Issue:** `json` is imported at module scope but never referenced anywhere in the file. Carried
over from the prior review pass; still unaddressed in the current file state.
**Fix:**
```python
from pathlib import Path
import re
import numpy as np
from scipy.io import loadmat
from PIL import Image, ImageOps
```

### IN-02: `find_track_file` silently resolves ambiguous multi-match cases instead of erroring

**File:** `src/nsf_fmrg_data.py:25-35`
**Issue:** `find_track_file` collects every file whose suffix and anchored track-id regex match,
sorts by `natural_key`, and silently returns `matches[0]`. If the raw tree ever contains more than
one file resolving to the same track (e.g. a stray backup/duplicate), the function picks one with
no signal that a choice was made. Downstream basename checks (`extract_final_thermal_frames`,
`load_wyko_asc`'s callers) only catch the case where the *chosen* match has the wrong basename,
not the case where a duplicate silently shadows the correct file. Carried over from the prior
review pass; still unaddressed.
**Fix:**
```python
matches = sorted(matches, key=natural_key)
if len(matches) > 1:
    raise ValueError(f'Ambiguous match for track {track_id} under {root}: {matches}')
return matches[0] if matches else None
```

### IN-03: `diagnose_width_regression.py`'s continuity sweep silently omits Amendment A8's Mechanism B history gate, and — unlike its sibling — was never given a disclosure comment

**File:** `scripts/diagnose_width_regression.py:46-78`, specifically line 67
**Issue:** `extract_swept` calls `targets.halfmax_edges(prof, y_mm, previous_center=query_center)`
without `previous_length_mm`, so it always defaults to `previous_length_mm=None`, disabling the
Mechanism B far-AND-small history gate that `targets.extract_targets_from_arrays` (the real
production path) applies via `previous_length_mm` (`src/targets.py:377-388`). This script calls
the genuine `targets.halfmax_edges` (not a reimplementation, so it can never diverge into *wrong*
output the way `diagnose_track10_coverage.py`'s hand-rolled `classify_column` did), but every
`continuity=True` row in its sweep still measures a materially different tracking variant than
what `src/targets.py` runs today. Notably, the sibling diagnostic
(`scripts/diagnose_track10_coverage.py`) had the *same* category of staleness and was just given
an explicit disclosure comment in the most recent commit (`3f87937`); this file was not similarly
updated, so the inconsistency between the two diagnostics' documentation is now more visible, not
less. `processed_data/diagnostics/width_regression_sweep.csv` (this script's output) is also
currently untracked in git, unlike its two sibling diagnostic CSVs which are committed.
**Fix:** Thread `previous_length_mm` through `extract_swept` (or call
`targets.extract_targets_from_arrays` directly for the `continuity=True` rows), or at minimum add
a one-line comment stating the sweep's continuity rows exclude the Mechanism B history gate — then
either commit `width_regression_sweep.csv` alongside its siblings or add it to `.gitignore`.

### IN-04: `get_sem_tile_paths`'s symlink defense is shallower than the rest of the codebase's path hardening

**File:** `src/nsf_fmrg_data.py:144-152`
**Issue:** This phase hardened `get_sem_tile_paths` with `if root.is_symlink() or
root.parent.is_symlink(): raise ValueError(...)`, checking only the SEM tile directory and its
immediate parent. `scripts/run_target_extraction.py`'s `reject_symlink_path` (used for every
output path in the target-extraction pipeline) instead walks the entire ancestor chain up to the
project root. A symlink planted higher up the tree (e.g. at the `sem_dir` argument itself, or an
ancestor above `SEM_<id>/`) would not be caught by `get_sem_tile_paths`. Not currently exploitable
within this phase's actual pipeline — `get_sem_tile_paths` isn't called anywhere in
`scripts/run_target_extraction.py` or `scripts/check_targets.py` — but it is an inconsistent depth
of protection for nominally the same "don't silently read through a symlinked data directory"
threat model this phase otherwise took seriously (CR-03).
**Fix:** If/when a later phase wires SEM loading into a similarly hardened pipeline, reuse
`reject_symlink_path`'s full-ancestor-walk pattern rather than the current two-level check.

### IN-05: `resolve_raw_dir` is validated twice on every invocation

**File:** `scripts/run_target_extraction.py:35-49`
**Issue:** `resolve_repository_root` calls `resolve_raw_dir(candidate)` at line 48 purely for its
validating side effect and discards the result; every caller (`run_pipeline` at line 339,
`scripts/check_targets.py:120`, and all three `diagnose_*` scripts) then calls
`resolve_raw_dir(project_root)` again immediately afterward. Harmless (idempotent, cheap — one
`Path.resolve(strict=True)` plus one `is_dir()` check) but is duplicated validation work with no
comment explaining the intentional redundancy.
**Fix:** Either have `resolve_repository_root` return `(project_root, raw_dir)` so callers reuse
the already-validated `raw_dir`, or drop the internal call and document that raw-dir validation is
the caller's responsibility.

---

_Reviewed: 2026-07-23T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
