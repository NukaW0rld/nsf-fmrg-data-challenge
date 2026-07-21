---
phase: 01-target-extraction-contract
fixed_at: 2026-07-21T21:59:31Z
review_path: .planning/phases/01-target-extraction-contract/01-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 01: Code Review Fix Report

**Fixed at:** 2026-07-21T21:59:31Z
**Source review:** .planning/phases/01-target-extraction-contract/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 4 (0 Critical + 4 Warning; `fix_scope: critical_warning`)
- Fixed: 4
- Skipped: 0

IN-01 through IN-04 (Info tier) were intentionally excluded — out of scope for this fix pass.

## Fixed Issues

### WR-01: `diagnose_track10_coverage.py`'s "production" path does not use the actual production detrend parameters

**Files modified:** `scripts/diagnose_track10_coverage.py`, `processed_data/diagnostics/track10_coverage_diagnosis.csv`
**Commit:** `1ccfe09`
**Applied fix:** Imported `DETREND_MAX_Y_DEGREE` from `targets` and passed it through to the `robust_plane_detrend` call inside `production_residual_profile`, matching the production call in `src/targets.py`'s `extract_track_targets` exactly. Regenerated `processed_data/diagnostics/track10_coverage_diagnosis.csv` by re-running `scripts/diagnose_track10_coverage.py --project_dir .` against the checked-in raw height-map data, so the checked-in diagnostic artifact reflects the corrected code path (track 10's `rejection_ok` moved from 21 to 255, much closer to the true production `valid_mask.sum() == 242` reported by `scripts/check_targets.py`; the small residual gap traces to the `classify_column`/`halfmax_edges` duplication separately tracked as IN-02, out of scope for this fix pass).

### WR-02: `robust_plane_detrend`'s `order`/`max_y_degree` validation is bypassed on degenerate data

**Files modified:** `src/nsf_fmrg_data.py`
**Commit:** `3400c77`
**Applied fix:** Moved the `order`/`max_y_degree` type/range validation blocks above the `valid.sum() < 100` degenerate-data early-return, so malformed `order`/`max_y_degree` values always raise `ValueError` regardless of how much of the input height map is finite/unmasked.

### WR-03: `load_wyko_asc` raises an unhelpful `KeyError` instead of a `ValueError` when the `.ASC` header is missing X/Y size fields

**Files modified:** `src/nsf_fmrg_data.py`
**Commit:** `48a9a22`
**Applied fix:** Added an explicit guard before `x_size`/`y_size` are read from the parsed header (`if 'x_size' not in header or 'y_size' not in header: raise ValueError(...)`), mirroring the existing `pixel_size_mm` validation pattern used by `extract_track_targets` in `src/targets.py`.

### WR-04: `extract_final_thermal_frames` raises an opaque `TypeError` (not `ValueError`) when no laser-on interval is found

**Files modified:** `src/nsf_fmrg_data.py`
**Commit:** `4592f50`
**Applied fix:** Added an explicit `on_stop is None` check immediately after `detect_laser_on_interval` returns, raising a `ValueError` with track/file context before `int(on_stop)` would otherwise raise an opaque `TypeError`.

## Skipped Issues

None — all in-scope findings were fixed.

---

_Fixed: 2026-07-21T21:59:31Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
