---
phase: 01-target-extraction-contract
fixed_at: 2026-07-22T23:59:00Z
review_path: .planning/phases/01-target-extraction-contract/01-REVIEW.md
iteration: 1
findings_in_scope: 1
fixed: 1
skipped: 3
status: partial
---

# Phase 01: Code Review Fix Report

**Fixed at:** 2026-07-22T23:59:00Z
**Source review:** .planning/phases/01-target-extraction-contract/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 1 (0 Critical + 1 Warning; `fix_scope: critical_warning`)
- Fixed: 1
- Skipped: 3 (Info tier, out of scope for this fix pass)

## Fixed Issues

### WR-01: `diagnose_track10_coverage.py`'s rejection-histogram and "production" detrend helper have drifted from the actual production algorithm they claim to mirror

**Files modified:** `scripts/diagnose_track10_coverage.py`, `processed_data/diagnostics/track10_coverage_diagnosis.csv`
**Commits:** `44ac9dc`, `cba53f2`
**Applied fix:** Imported `DETREND_MAX_XY_DEGREE`, `MAX_RUN_MERGE_GAP_PIXELS`, `MIN_TRACKED_LENGTH_RATIO`, and `merge_adjacent_runs` from `targets`. `production_residual_profile` now passes `max_xy_degree=DETREND_MAX_XY_DEGREE` to `robust_plane_detrend`, matching `targets.extract_track_targets`. `classify_column` now applies `merge_adjacent_runs` (Amendment A7 run-merging) before building candidates, and applies the `MIN_TRACKED_LENGTH_RATIO` plausibility gate when `previous_center` is set — mirroring `targets.halfmax_edges` exactly. Regenerated the checked-in `processed_data/diagnostics/track10_coverage_diagnosis.csv` by re-running the corrected script against the checked-in raw height-map data: track 10's `rejection_ok` moved from 255 to 202, now exactly matching the production `valid_mask.sum() == 202` the review used as ground truth (previously a ~21% discrepancy).

## Skipped Issues (out of scope: Info tier, not requested by `--fix` without `--all`)

### IN-01: Unused `import json` in `src/nsf_fmrg_data.py`
Not fixed — Info-tier finding, out of scope for `critical_warning` fix scope. Re-run with `--all` to include.

### IN-02: `find_track_file` silently resolves ambiguous multi-match cases instead of erroring
Not fixed — Info-tier finding, out of scope for `critical_warning` fix scope. Re-run with `--all` to include.

### IN-03: `load_wyko_asc` silently falls back to a hardcoded default pixel size before the missing-header case is caught
Not fixed — Info-tier finding, out of scope for `critical_warning` fix scope. Re-run with `--all` to include.

---

_Fixed: 2026-07-22T23:59:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
