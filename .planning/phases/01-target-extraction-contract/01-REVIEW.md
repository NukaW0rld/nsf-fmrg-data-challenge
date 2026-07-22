---
phase: 01-target-extraction-contract
reviewed: 2026-07-22T23:53:52Z
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
  warning: 1
  info: 3
  total: 4
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-22T23:53:52Z
**Depth:** standard
**Files Reviewed:** 29
**Status:** issues_found

## Summary

This phase implements the local-width target-extraction contract: `src/targets.py` (boundary tracking via half-max edges, gap filling, run merging, Savitzky-Golay-style smoothing, bead-masked polynomial detrending) plus `src/nsf_fmrg_data.py` changes (stricter `find_track_file` matching, higher-order/masked `robust_plane_detrend`), a hardened `scripts/run_target_extraction.py` publish pipeline (symlink rejection, raw-tree integrity snapshotting, atomic staging/publish), a `scripts/check_targets.py` artifact-contract auditor, three diagnostic scripts, and a large, well-targeted regression-test suite.

This is unusually rigorous for a first-pass implementation: extensive amendment history (A3-A7) documents each locked constant's provenance, the raw-tree integrity auditor is fuzz-tested against symlink attacks and TOCTOU-style races, and the numeric edge cases in the boundary-tracking algorithm (division-by-zero in threshold interpolation, boundary-clipped runs, stale-history resets, post-smoothing crossings) all have dedicated tests. All 33 + 13 + 10 tests in the three suites pass locally, and `scripts/check_targets.py` passes against the committed artifacts.

No blocking correctness or security defects were found in the shipped extraction/publish path itself. The findings below are a real but narrower set: a diagnostic script that has drifted out of sync with the production algorithm it claims to mirror (misleading if consulted later), a dead import, and two silent-fallback/ambiguity footguns in `nsf_fmrg_data.py`'s file-resolution and header-parsing helpers.

Note: `processed_data/targets/qa/*_width.png` curves for all four tracks show high-frequency, large-amplitude (0.1-1.2mm) width oscillation over sub-mm x-steps. This is consistent with the extensively diagnosed track-10 fragmentation/noise investigation already documented in the codebase (Amendments A4-A7) rather than a newly-introduced defect, so it is not filed as a separate finding here — flagging it for awareness in case downstream phases assume a smoother target signal than what this extraction currently produces.

## Warnings

### WR-01: `diagnose_track10_coverage.py`'s rejection-histogram and "production" detrend helper have drifted from the actual production algorithm they claim to mirror

**File:** `scripts/diagnose_track10_coverage.py:61-67, 105-161`

**Issue:** `classify_column` carries an explicit contract in its own comment: "Mirrors targets.halfmax_edges' rejection branches so this diagnostic can attribute a reason to each bin; must be kept in step with that function." It is not kept in step:

- It builds `candidates` directly from `all_true_runs(above)` and never calls `merge_adjacent_runs` (targets.py:204), so it does not model the Amendment A7 run-merging behavior that `targets.halfmax_edges` (targets.py:186-256) applies before candidate selection.
- When `previous_center` is not `None`, it picks the nearest candidate with no `MIN_TRACKED_LENGTH_RATIO` plausibility gate (targets.py:222-226), unlike `halfmax_edges`.

Separately, `production_residual_profile` (line 61) — named after "production" — calls `robust_plane_detrend` with `max_y_degree=DETREND_MAX_Y_DEGREE` but omits `max_xy_degree=DETREND_MAX_XY_DEGREE` (line 63-67), even though `targets.extract_track_targets` (targets.py:371-379) passes both. `DETREND_MAX_XY_DEGREE` is not even imported in this script.

This is measurable: the committed `processed_data/diagnostics/track10_coverage_diagnosis.csv` reports `rejection_ok=255` for track 10, while the actual production artifact `processed_data/targets/track_10_targets.npz` has `valid_mask.sum() == 202` (confirmed by running `scripts/check_targets.py` against the committed artifacts). A ~21% discrepancy for the exact track this diagnostic exists to characterize. Anyone consulting this diagnostic to reason about the current production pipeline will draw conclusions that do not match what actually ships.

**Fix:** Either import and thread `merge_adjacent_runs`, `MIN_TRACKED_LENGTH_RATIO`, and `DETREND_MAX_XY_DEGREE` through so `classify_column`/`production_residual_profile` genuinely mirror `targets.halfmax_edges`/`targets.extract_track_targets`, or (if this diagnostic is intentionally frozen as a historical snapshot from before Amendment A7) add the same kind of explicit "historical baseline, do not mistake for current production" disclaimer that `scripts/diagnose_width_regression.py:39-43` already uses for its `bead_mask=False` rows, and rename `production_residual_profile` to something that doesn't imply it matches production today.

## Info

### IN-01: Unused `import json` in `src/nsf_fmrg_data.py`

**File:** `src/nsf_fmrg_data.py:3`
**Issue:** `json` is imported at module scope but never referenced anywhere in the file (verified via AST-based unused-import scan across all reviewed `src/`/`scripts/` files — this was the only hit).
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
**Issue:** `find_track_file` collects every file under `root` whose suffix matches and whose name matches the anchored track-id regex, sorts by `natural_key`, and silently returns `matches[0]`. If the raw data tree ever contains more than one file with the exact same expected basename for a track (e.g. an accidental backup copy, a `.bak`/nested-directory duplicate introduced by a sync tool), the function will silently pick whichever sorts first by path string with no warning that a choice was made — and since `extract_final_thermal_frames`/`load_wyko_asc` only check the resolved file's *basename* against the expected name (not uniqueness), a genuine duplicate with the identical expected basename would pass that check too and be used without any signal that ambiguity existed.
**Fix:** Raise if `len(matches) > 1` (or at minimum log a warning identifying all candidates), rather than silently discarding all but the first:
```python
matches = sorted(matches, key=natural_key)
if len(matches) > 1:
    raise ValueError(f'Ambiguous match for track {track_id} under {root}: {matches}')
return matches[0] if matches else None
```

### IN-03: `load_wyko_asc` silently falls back to a hardcoded default pixel size before the missing-header case is caught

**File:** `src/nsf_fmrg_data.py:175-221` (default at line 184); guarded downstream at `src/targets.py:367-368`
**Issue:** `load_wyko_asc` computes `pixel = float(header.get('pixel_size_mm', 0.003982))` and then uses `pixel` to build `x_local_mm`/`y_mm`/`x_actual_mm` for the *entire* returned geometry, silently substituting a hardcoded default if the `.ASC` header lacks `pixel_size` at all. `targets.extract_track_targets` does guard against this (`if 'pixel_size_mm' not in data['header']: raise ValueError(...)`), so the production pipeline is safe — but that check happens only after `load_wyko_asc` has already done the (now-discarded) work of building wrongly-scaled coordinate arrays, and any other caller of `load_wyko_asc` directly (a notebook, a future script) gets a plausible-looking but silently mis-scaled height map with no error at all.
**Fix:** Move the missing-`pixel_size_mm` check into `load_wyko_asc` itself (fail before computing geometry from the assumed default), or drop the default and require the header to supply it explicitly:
```python
if 'pixel_size_mm' not in header:
    raise ValueError(f'{path} header is missing pixel_size_mm.')
pixel = float(header['pixel_size_mm'])
```

---

_Reviewed: 2026-07-22T23:53:52Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
