---
phase: 01-target-extraction-contract
reviewed: 2026-07-21T00:00:00Z
depth: standard
files_reviewed: 25
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
  warning: 4
  info: 4
  total: 8
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-21T00:00:00Z
**Depth:** standard
**Files Reviewed:** 25 (source + tests + checked-in data/QA artifacts)
**Status:** issues_found

## Summary

This phase adds a locked, heavily contract-tested target-extraction pipeline
(`src/targets.py`), an extended `robust_plane_detrend` in `src/nsf_fmrg_data.py`
(arbitrary total-degree polynomial with an optional per-column `fit_mask` and
`max_y_degree` cap), a security-hardened publish pipeline
(`scripts/run_target_extraction.py`), a strict artifact validator
(`scripts/check_targets.py`), and two diagnostic scripts. I read every
listed source file, ran all three test suites (`tests/test_nsf_fmrg_data.py`,
`tests/test_targets.py`, `tests/test_run_target_extraction.py` — all 47 tests
pass), ran `scripts/check_targets.py` against the checked-in npz artifacts
(passes, with the width-ordering "FLAG" the code itself documents as
expected), and inspected the checked-in QA figures.

The core extraction/detrend logic and the symlink/raw-integrity hardening in
`run_target_extraction.py` are well tested and I found no correctness or
security defect in them severe enough to block. The findings below are real
defects nonetheless: a diagnostic script whose output actively misrepresents
production behavior, two spots where input validation is either bypassed or
missing (inconsistent with this same phase's own newly-added validation
conventions), and an edge case that would surface as an unhelpful `TypeError`
instead of the codebase's established `ValueError`-with-message pattern.

## Warnings

### WR-01: `diagnose_track10_coverage.py`'s "production" path does not use the actual production detrend parameters

**File:** `scripts/diagnose_track10_coverage.py:60-64`
**Issue:** `production_residual_profile()` is documented as exercising "the
production detrend path" and its result feeds the checked-in
`processed_data/diagnostics/track10_coverage_diagnosis.csv`. It calls:

```python
Zd, coef = robust_plane_detrend(
    Z_mm, x_actual_mm, y_mm, order=DETREND_POLY_ORDER, fit_mask=fit_mask,
)
```

but the actual production call in `src/targets.py:308-315`
(`extract_track_targets`) additionally passes
`max_y_degree=DETREND_MAX_Y_DEGREE` (locked at `2` per Amendment A5).
`DETREND_MAX_Y_DEGREE` is never imported into this diagnostic script at all
(compare its import list, `scripts/diagnose_track10_coverage.py:17-31`,
against `src/targets.py`'s constants).

The practical effect is large: the checked-in CSV row for track 10 reports
`rejection_ok=21` (i.e., only 21/400 = 5% of columns pass under the
diagnostic's stale, uncapped fit), while the actual production artifact
`processed_data/targets/track_10_targets.npz` has `valid_mask.sum() == 242`
(60.5%, verified by loading the npz directly and independently by running
`scripts/check_targets.py`, which reports `10  350  242  0.3713  0.3234`).
A future engineer reading this diagnostic CSV to characterize track 10's
health would be told the production pipeline salvages ~12x fewer columns
than it actually does. `scripts/diagnose_track10_coverage.py:102-104`
explicitly acknowledges the twin function `classify_column` "must be kept
in step with" `targets.halfmax_edges` — this is exactly the kind of drift
that acknowledgment was meant to prevent, and it has already happened for
the `robust_plane_detrend` call itself.

**Fix:** Import `DETREND_MAX_Y_DEGREE` from `targets` and pass it through,
matching the production call exactly:
```python
from targets import (
    BASELINE_PCT, DETREND_MAX_Y_DEGREE, DETREND_POLY_ORDER, HALF_MAX_FRACTION,
    ...
)

def production_residual_profile(Z_mm, x_actual_mm, y_mm):
    fit_mask = bead_exclusion_mask(Z_mm)
    Zd, coef = robust_plane_detrend(
        Z_mm, x_actual_mm, y_mm,
        order=DETREND_POLY_ORDER, fit_mask=fit_mask,
        max_y_degree=DETREND_MAX_Y_DEGREE,
    )
```
Then regenerate `processed_data/diagnostics/track10_coverage_diagnosis.csv`
so the checked-in artifact matches current production output.

### WR-02: `robust_plane_detrend`'s `order`/`max_y_degree` validation is bypassed on degenerate data

**File:** `src/nsf_fmrg_data.py:230-236`
**Issue:** The early-return degenerate-data guard runs before parameter
validation:
```python
if valid.sum() < 100:
    return Z_mm.copy(), None

if not isinstance(order, (int, np.integer)) or order < 0:
    raise ValueError('order must be a non-negative integer.')
if max_y_degree is not None and (not isinstance(max_y_degree, (int, np.integer)) or max_y_degree < 0):
    raise ValueError('max_y_degree must be a non-negative integer or None.')
```
A caller that passes a malformed `order` (e.g. `-1`, `"4"`, `4.5`) against a
degenerate/sparse map (fewer than 100 valid fit points after masking, which
`tests/test_nsf_fmrg_data.py::test_degenerate_fallback_is_preserved_for_all_orders`
deliberately exercises for *valid* orders) will silently get the
`(Z_mm.copy(), None)` fallback instead of the `ValueError` it would get on a
normal-sized map. This means the same programming error is caught in one
code path and silently swallowed in another, depending only on how much of
the input height map happens to be finite/unmasked — a trap for anyone
extending this function or wiring up a new caller.
**Fix:** Move the two validation blocks above the `valid.sum() < 100` check
so invalid `order`/`max_y_degree` values always raise, regardless of data
shape:
```python
if not isinstance(order, (int, np.integer)) or order < 0:
    raise ValueError('order must be a non-negative integer.')
if max_y_degree is not None and (not isinstance(max_y_degree, (int, np.integer)) or max_y_degree < 0):
    raise ValueError('max_y_degree must be a non-negative integer or None.')
if valid.sum() < 100:
    return Z_mm.copy(), None
```

### WR-03: `load_wyko_asc` raises an unhelpful `KeyError` instead of a `ValueError` when the `.ASC` header is missing X/Y size fields

**File:** `src/nsf_fmrg_data.py:178-179`
**Issue:**
```python
x_size = int(header['x_size'])
y_size = int(header['y_size'])
```
`parse_wyko_header` (`src/nsf_fmrg_data.py:157-170`) only populates
`header['x_size']`/`header['y_size']` if the corresponding lines are present
in the file; if a malformed or unexpected `.ASC` file is fed in, this raises
a bare `KeyError: 'x_size'` with no context about which file or track failed.
This is inconsistent with the project's documented "fail-fast with explicit
messages" convention (`CLAUDE.md` → Error Handling) and with the very next
consumer in this same phase, `extract_track_targets`
(`src/targets.py:304-305`), which explicitly guards the analogous
`pixel_size_mm` field with a clear `ValueError` before using it:
```python
if 'pixel_size_mm' not in data['header']:
    raise ValueError(f'{expected_name} header is missing pixel_size_mm.')
```
`x_size`/`y_size` get no equivalent guard even though they are used earlier,
inside `load_wyko_asc` itself, to allocate `z_mm_flat = np.empty(x_size * y_size, ...)`.
**Fix:** Validate before use, mirroring the `pixel_size_mm` pattern already
established in this phase:
```python
if 'x_size' not in header or 'y_size' not in header:
    raise ValueError(f'{path} header is missing X Size/Y Size fields.')
x_size = int(header['x_size'])
y_size = int(header['y_size'])
```

### WR-04: `extract_final_thermal_frames` raises an opaque `TypeError` (not `ValueError`) when no laser-on interval is found

**File:** `src/nsf_fmrg_data.py:127-128`
**Issue:**
```python
on_start, on_stop, score, threshold = detect_laser_on_interval(frames)
stop_idx = int(on_stop)
```
`detect_laser_on_interval` delegates to `largest_true_run`
(`src/nsf_fmrg_data.py:92-101`), which returns `(None, None)` when the
above-threshold mask is empty (`if not mask.any(): return None, None`).
If a thermal cube ever fails to register a detectable laser-on interval
(e.g. a corrupted/truncated `.mat` file, or a threshold miscalibration on
an unusual track), `int(on_stop)` raises `TypeError: int() argument must be
a string, a bytes-like object or a real number, not 'NoneType'`. Every
other failure mode in this same function (`find_track_file` returning
`None`, filename mismatch) is guarded with a clear `ValueError` and message
(`src/nsf_fmrg_data.py:120-124`, added in this phase); this remaining path
was not given the same treatment.
**Fix:**
```python
on_start, on_stop, score, threshold = detect_laser_on_interval(frames)
if on_stop is None:
    raise ValueError(f'No laser-on interval detected for track {track_id} in {path}.')
stop_idx = int(on_stop)
```

## Info

### IN-01: Unused `import json` in `src/nsf_fmrg_data.py`

**File:** `src/nsf_fmrg_data.py:3`
**Issue:** `json` is imported but never referenced anywhere in the module
(`grep -n "json\." src/nsf_fmrg_data.py` finds nothing).
**Fix:** Remove the unused import.

### IN-02: `classify_column` duplicates `targets.halfmax_edges` and has already drifted (see WR-01)

**File:** `scripts/diagnose_track10_coverage.py:102-158` vs. `src/targets.py:137-193`
**Issue:** The diagnostic re-implements the production edge-selection logic
line-for-line rather than importing and instrumenting `halfmax_edges`
directly. The file's own comment (`scripts/diagnose_track10_coverage.py:103-104`)
flags the coupling risk, and WR-01 shows the risk has already materialized
for the surrounding detrend call. The duplication makes this kind of
silent divergence structurally likely to recur.
**Fix:** Consider having the diagnostic call `targets.halfmax_edges`
directly (perhaps wrapping it to also return a rejection reason) instead of
maintaining a parallel copy, so the two can never diverge.

### IN-03: `Y_STRIP_EXTENT_MM` in `scripts/check_targets.py` is a hardcoded constant, not derived from each track's actual header

**File:** `scripts/check_targets.py:24-30`
**Issue:** The 1.907 mm bound is documented as being derived from
`y_size * pixel_size_mm = 480 * 0.003982 mm` "for all four current
Heightmap_*.ASC headers." This is correct today, but the check does not
read each track's actual header to confirm the assumption still holds; if
a future dataset revision changes `y_size`/`pixel_size_mm` for any track,
this bound would silently become wrong (too loose or too strict) rather
than failing loudly.
**Fix:** Optional hardening — derive the per-track bound from
`load_wyko_asc`'s header (`y_size * pixel_size_mm`) at check time instead
of a single global constant, or add an explicit comment/assertion that
re-derives and cross-checks the constant against the persisted header
values.

### IN-04: Track 10 vs. Track 14 median width violates the expected power-monotonic ordering (documented, not a code defect)

**File:** `processed_data/targets/track_10_targets.npz`, `processed_data/targets/track_14_targets.npz`; surfaced via `src/targets.py:print_results` (`scripts/check_targets.py` output)
**Issue:** Track 10 (350 W) has a smaller median width (0.3713 mm) than
Track 14 (300 W, 0.4765 mm), which inverts the expected "higher laser power
→ wider track" relationship that holds for every other adjacent pair
(8 vs 10, 14 vs 21). The code already classifies and prints this as a
`FLAG` and explicitly states such flags are "documented and never used to
tune locked extraction constants," so this is not treated as a code bug.
Flagging here only so a reader of this review is aware that downstream
consumers of these four artifacts (e.g. a model trained on laser-power vs.
width) will encounter this known non-monotonicity in the ground truth if
they don't also read the pipeline's console output.
**Fix:** None required for this phase; carry the caveat forward into any
downstream documentation/spec that consumes these four `.npz` files as
ground truth.

---

_Reviewed: 2026-07-21T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
