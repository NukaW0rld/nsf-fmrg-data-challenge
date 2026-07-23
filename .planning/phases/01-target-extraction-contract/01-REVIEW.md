---
phase: 01-target-extraction-contract
reviewed: 2026-07-22T00:00:00Z
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
  info: 4
  total: 5
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-22T00:00:00Z
**Depth:** standard
**Files Reviewed:** 29
**Status:** issues_found

## Summary

This pass focuses on plan 01-16's change to `src/targets.py` (Amendment A8): `halfmax_edges` now applies the boundary-clip-exclusion test to each raw above-threshold run *before* `merge_adjacent_runs` (Mechanism A fix), and gains a history-based joint far-AND-small plausibility gate (`_is_implausible_versus_history`) that rejects a lone same-column-plausible tracked candidate only when it is both farther from `previous_center` than `previous_length_mm` and smaller than `MIN_TRACKED_LENGTH_RATIO * previous_length_mm` (Mechanism B fix). `extract_targets_from_arrays` now threads `previous_length_mm` alongside `previous_center`, resetting both together after a long invalid-column gap.

I traced both mechanisms line-by-line against the pre-change diff (`git diff a51c57b^ fbc22af -- src/targets.py`) and verified the following invariants hold: (1) because `non_edge_runs` is filtered from `raw_runs` before `merge_adjacent_runs` runs, a merged candidate's `start`/`stop` are always drawn from an originally non-edge-touching run, so `start >= 1` and `stop <= len(prof) - 1` always hold — the downstream `prof[start - 1]` / `prof[stop]` interpolation lookups can never index out of bounds or silently re-admit a boundary-touching span; (2) the same-column `MIN_TRACKED_LENGTH_RATIO` filter always contains at least the max-length candidate, so `plausible` is never empty before the history gate runs; (3) the history gate's `and` (not `or`) means a candidate close to `previous_center` is never rejected on size alone and a candidate as large as recent history is never rejected on distance alone, matching the accompanying comments. All 38 tests in `tests/test_targets.py`, 13 in `tests/test_nsf_fmrg_data.py`, and 10 in `tests/test_run_target_extraction.py` pass locally (ran under `.venv`), including the six new/changed Mechanism A/B regression tests (`test_halfmax_edges_recovers_leading_edge_swallowed_interior_run`, `test_halfmax_edges_recovers_trailing_edge_swallowed_interior_run`, `test_halfmax_edges_rejects_lone_candidate_far_and_small_versus_tracked_history`, `test_halfmax_edges_accepts_lone_candidate_small_but_close_to_tracked_history`, `test_halfmax_edges_accepts_lone_candidate_far_but_large_versus_tracked_history`, `test_extract_targets_from_arrays_rejects_track8_style_single_candidate_trigger_column`). I did not find a correctness defect in `halfmax_edges` or `extract_targets_from_arrays` itself.

The 10-vs-14 width-ordering FLAG documented in `01-16-ORDERING-OUTCOME.md` is a known, previously-accepted limitation (Mechanism C, the deferred DP/Viterbi joint tracker) and is not re-litigated here.

What I did find is a **regression of a previously-fixed issue**: `scripts/diagnose_track10_coverage.py`'s `classify_column` was explicitly synced with `targets.halfmax_edges` earlier in this same day's work (commit `44ac9dc`, "WR-01 sync..."), but plan 01-16's subsequent change to `halfmax_edges` (commit `fbc22af`, ~3 hours later) was never propagated to this diagnostic, so it has drifted out of sync again — and the committed `track10_coverage_diagnosis.csv` was last regenerated between those two commits, so it now reports rejection-reason counts from neither the current production algorithm nor even the diagnostic script's own (already-stale) reimplementation of it as currently loaded. Three carried-over `Info`-level findings from the prior review pass (unused `import json`, silent ambiguous-match resolution in `find_track_file`, silent hardcoded-default `pixel_size_mm` fallback in `load_wyko_asc`) remain unaddressed in the current file state and are restated below for completeness.

## Warnings

### WR-01: `diagnose_track10_coverage.py`'s `classify_column` has drifted out of sync with `targets.halfmax_edges` again, after plan 01-16's Mechanism A/B fix

**File:** `scripts/diagnose_track10_coverage.py:110-175`

**Issue:** `classify_column`'s own docstring-comment states: "Mirrors targets.halfmax_edges' rejection branches so this diagnostic can attribute a reason to each bin; must be kept in step with that function." It was synced once (commit `44ac9dc`, same day, `18:56:59`) to match the Amendment A7 (`01-14`) behavior — but plan 01-16 (commit `fbc22af`, `21:43:42`, ~3 hours later) changed `targets.halfmax_edges` again and this diagnostic was not updated to match:

- It still does `merged_runs = merge_adjacent_runs(all_true_runs(above), MAX_RUN_MERGE_GAP_PIXELS)` and *then* filters `start != 0 and stop != len(prof)` on the merged result (`diagnose_track10_coverage.py:127-132`). Production `halfmax_edges` now filters non-edge-touching raw runs *before* merging (`src/targets.py:212-217`, Amendment A8 / Mechanism A). These two orderings produce different candidate sets whenever an edge-touching raw run sits within `MAX_RUN_MERGE_GAP_PIXELS` of an otherwise-valid interior run — exactly the scenario Mechanism A was written to fix.
- It has no equivalent of the new history-based `_is_implausible_versus_history` gate (`src/targets.py:247-261`, Mechanism B): when `previous_center is not None`, `classify_column` applies only the same-column `MIN_TRACKED_LENGTH_RATIO` filter (`diagnose_track10_coverage.py:141-145`) and picks the nearest candidate with no far-AND-small history check at all.

This is measurable, not hypothetical: the committed `processed_data/diagnostics/track10_coverage_diagnosis.csv` (last regenerated at commit `cba53f2`, `18:58:53`, between the two `halfmax_edges` changes) reports `rejection_ok` = 361/202/301/312 for tracks 8/10/14/21. The current production artifacts (`processed_data/targets/track_{8,10,14,21}_targets.npz`, regenerated after `fbc22af` at `21:43-21:44`) have `valid_mask.sum()` = 368/232/309/338 for the same four tracks — a mismatch on every single track (verified directly: `np.load(...)['valid_mask'].mean()` against the CSV's `rejection_ok` column). Anyone consulting this diagnostic — including a future re-run of the exact same episode this file exists to characterize — will draw conclusions about track 10's rejection-reason breakdown that do not match what the shipped pipeline currently does or produces.

**Fix:** Either (a) update `classify_column` to filter non-edge raw runs before calling `merge_adjacent_runs`, and add the same `previous_length_mm`-based history gate `targets.halfmax_edges` now uses (ideally by importing and calling `targets.halfmax_edges` directly instead of hand-duplicating its candidate-selection logic, which is what created this drift twice in one day), and regenerate `track10_coverage_diagnosis.csv`; or (b) if this diagnostic is intentionally frozen as a point-in-time snapshot, add an explicit "historical baseline as of commit X — does not reflect current `halfmax_edges`" disclaimer (matching the pattern `scripts/diagnose_width_regression.py` already uses for its `bead_mask=False` rows) so nobody mistakes it for a live characterization of production behavior.

## Info

### IN-01: `diagnose_width_regression.py`'s continuity sweep silently disables the new Mechanism-B history gate

**File:** `scripts/diagnose_track10_coverage.py` is not the only diagnostic affected by the Amendment A8 signature change; `scripts/diagnose_width_regression.py:67` calls `halfmax_edges(prof, y_mm, previous_center=query_center)` without passing `previous_length_mm`. Unlike `diagnose_track10_coverage.py`, this script calls the real `targets.halfmax_edges` (not a reimplementation), so it can never silently diverge in a way that produces *wrong* output — but every "continuity=True" row in the sweep now measures a variant of production tracking with Mechanism B permanently switched off (the function's default `previous_length_mm=None` disables the history gate entirely), which is a materially different tracking behavior than what `extract_targets_from_arrays` actually runs today.
**Fix:** Thread `previous_length_mm` through `extract_swept` the same way `extract_targets_from_arrays` does, or add a one-line comment noting that this sweep's "continuity" rows intentionally exclude the Mechanism B history gate, so a future reader doesn't assume this sweep characterizes the exact current production tracking behavior.

### IN-02: Unused `import json` in `src/nsf_fmrg_data.py`

**File:** `src/nsf_fmrg_data.py:3`
**Issue:** `json` is imported at module scope but never referenced anywhere in the file (still true in the current file state; carried over from the prior review pass, unaddressed).
**Fix:**
```python
from pathlib import Path
import re
import numpy as np
from scipy.io import loadmat
from PIL import Image, ImageOps
```

### IN-03: `find_track_file` silently resolves ambiguous multi-match cases instead of erroring

**File:** `src/nsf_fmrg_data.py:25-35`
**Issue:** `find_track_file` collects every file whose suffix and anchored track-id regex match, sorts by `natural_key`, and silently returns `matches[0]`. If the raw tree ever contains more than one file resolving to the same track (e.g. a stray backup/duplicate), the function picks one with no signal that a choice was made, and downstream basename checks (`extract_final_thermal_frames`, `load_wyko_asc`) would not catch a duplicate sharing the exact expected basename. Still present in the current file state; carried over from the prior review pass, unaddressed.
**Fix:**
```python
matches = sorted(matches, key=natural_key)
if len(matches) > 1:
    raise ValueError(f'Ambiguous match for track {track_id} under {root}: {matches}')
return matches[0] if matches else None
```

### IN-04: `load_wyko_asc` silently falls back to a hardcoded default pixel size before the missing-header case is caught

**File:** `src/nsf_fmrg_data.py:175-221` (default at line 184); guarded downstream at `src/targets.py:409-410`
**Issue:** `load_wyko_asc` computes `pixel = float(header.get('pixel_size_mm', 0.003982))` and uses it to build the entire returned coordinate geometry before any check that `pixel_size_mm` was actually present in the header. `targets.extract_track_targets` guards this after the fact (`if 'pixel_size_mm' not in data['header']: raise ValueError(...)`), so the production pipeline is safe, but any other direct caller of `load_wyko_asc` (a notebook, a future script) silently gets a plausible-looking but wrongly-scaled height map with no error. Still present in the current file state; carried over from the prior review pass, unaddressed.
**Fix:**
```python
if 'pixel_size_mm' not in header:
    raise ValueError(f'{path} header is missing pixel_size_mm.')
pixel = float(header['pixel_size_mm'])
```

---

_Reviewed: 2026-07-22T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
