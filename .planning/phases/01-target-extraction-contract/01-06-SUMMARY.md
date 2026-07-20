---
phase: 01-target-extraction-contract
plan: 06
subsystem: data-processing
tags: [profilometry, detrending, diagnostics, root-cause-analysis, numpy]

requires:
  - phase: 01-target-extraction-contract
    provides: quartic-order detrending (Amendment A3), boundary continuity tracking, and the diagnosed Gap 2 width-ordering regression
provides:
  - A committed, reusable detrend-order x continuity sweep diagnostic that reuses the published extraction helpers read-only
  - A machine-readable 6-configuration sweep table isolating detrend_order=4 as the necessary condition for the ordering regression
  - A pre-registered, outcome-independent fix-selection criterion for plan 01-07 (residual/physical, not ordering-outcome)
affects: [target-extraction, dataset-alignment, model-training, submission-qa]

tech-stack:
  added: []
  patterns: [uniform parameter sweep diagnostic reusing shared numeric contract, read-only raw snapshot audit, pre-registered outcome-independent selection criterion]

key-files:
  created: [scripts/diagnose_width_regression.py, .planning/phases/01-target-extraction-contract/01-06-DIAGNOSIS.md]
  modified: []

key-decisions:
  - "The width-ordering regression is caused by DETREND_POLY_ORDER=4, not continuity tracking — verdict flips PASS to FLAG exactly at order=4 under both continuity settings."
  - "Continuity tracking has a real, uniform, order-independent effect that shrinks track 21's magnitude 3-4x, but never by itself flips the ordering verdict."
  - "Pre-registered the fix-selection criterion (residual structure / physical plausibility — the detrend background must not follow the bead) before any fix is chosen or applied, naming bead-masking as the endorsed remedy."

patterns-established:
  - "Diagnostic sweep scripts reuse the published extraction helpers (bin_profile, fill_small_gaps, halfmax_edges, finalize_smoothed_boundaries) and the runner's resolve_repository_root/resolve_raw_dir/resolve_output_path/snapshot_raw containment path rather than re-deriving them."
  - "Root-cause diagnosis is separated from fix selection: a pre-registered criterion is written down before the fix is chosen, and the fix is explicitly not required to be one of the swept cells."

requirements-completed: [TARGET-02]

coverage:
  - id: D1
    description: "A uniform detrend-order x continuity sweep diagnostic exists, reuses shared extraction helpers, and runs read-only against data/raw/."
    requirement: TARGET-02
    verification:
      - kind: integration
        ref: ".venv/bin/python scripts/diagnose_width_regression.py --project_dir ."
        status: pass
    human_judgment: false
  - id: D2
    description: "The sweep table isolates detrend_order=4 as the necessary condition for the width-ordering regression (verdict flips only at order=4, under both continuity settings)."
    requirement: TARGET-02
    verification:
      - kind: integration
        ref: "processed_data/targets/diagnostics/width_regression_sweep.csv (6 rows, 4 PASS at order 1/2, 2 FLAG at order 4)"
        status: pass
    human_judgment: false
  - id: D3
    description: "A pre-registered, outcome-independent fix-selection criterion is committed in 01-06-DIAGNOSIS.md before any fix is applied."
    requirement: TARGET-02
    verification:
      - kind: manual_procedural
        ref: ".planning/phases/01-target-extraction-contract/01-06-DIAGNOSIS.md Section 3"
        status: pass
    human_judgment: true
    rationale: "Confirming the criterion is genuinely outcome-independent (phrased in residual/physical terms, not ordering-outcome terms) and faithfully reflects the sweep evidence requires scientific/editorial judgment, not just a passing command."

duration: 7min
completed: 2026-07-20
status: complete
---

# Phase 01 Plan 06: Width-Regression Diagnosis Summary

**A committed detrend-order x continuity sweep isolates DETREND_POLY_ORDER=4 (not continuity tracking) as the cause of the Gap 2 width-ordering regression, and pre-registers a residual/physical fix-selection criterion for plan 01-07.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-07-20T21:14:00Z
- **Completed:** 2026-07-20T21:21:59Z
- **Tasks:** 2
- **Files modified:** 2 committed files (script + diagnosis doc) plus one local, gitignored diagnostic CSV artifact

## Accomplishments

- Authored `scripts/diagnose_width_regression.py`: a local `extract_swept(Zd, x_actual_mm, y_mm, continuity)` that mirrors the published `extract_targets_from_arrays` loop exactly when `continuity=True`, and forces `previous_center=None` on every column when `continuity=False` (the pre-01-05 largest-run behavior) — built entirely from the imported shared helpers (`bin_profile`, `fill_small_gaps`, `halfmax_edges`, `finalize_smoothed_boundaries`, `target_grid`), with zero re-derivation of their internals.
- Ran the full 6-configuration sweep (order in {1, 2, 4} x continuity in {True, False}) against all 4 real tracks and wrote `processed_data/targets/diagnostics/width_regression_sweep.csv`.
- Isolated the cause: the ordering verdict is PASS at order 1 and order 2 under *both* continuity settings, and FLAG at order 4 under *both* continuity settings — the order axis alone determines the verdict.
- Documented a second, real, order-independent effect: continuity tracking shrinks track 21's median 3-4x uniformly across all three orders, but never by itself flips PASS to FLAG.
- Pre-registered an outcome-independent, residual/physical fix-selection criterion in `01-06-DIAGNOSIS.md`, naming bead-masking as the endorsed remedy for plan 01-07 and two fallback conditions, before any fix is chosen.
- Verified `data/raw/` integrity PASS (read-only), and confirmed `processed_data/targets/{extraction_params,manifest}.json` and all four published `track_*_targets.npz` files remained byte-identical (hash-checked) before and after the sweep.

## Task Commits

Each task was committed atomically:

1. **Task 1: Author the uniform detrend-order x continuity sweep diagnostic** - `e9c3465` (feat)
2. **Task 2: Run the sweep and pre-register the outcome-independent fix-selection criterion** - `86aef23` (docs)

## Files Created/Modified

- `scripts/diagnose_width_regression.py` - New diagnostic script: swept `extract_swept()` extractor, 6-configuration sweep runner reusing shared extraction helpers and the runner's raw-containment/audit path, CSV writer, and PASS/FLAG ordering-verdict logic.
- `.planning/phases/01-target-extraction-contract/01-06-DIAGNOSIS.md` - Sweep table, root-cause reading (order-4 bead-corridor absorption vs. continuity's track-21-only effect), and the pre-registered fix-selection criterion.
- `processed_data/targets/diagnostics/width_regression_sweep.csv` - Generated diagnostic artifact (gitignored under `processed_data/targets/`, matches the established pattern for this phase's other generated outputs; reproducible via the committed script).

## Sweep Results

| detrend_order | continuity | median_width_8 | median_width_10 | median_width_14 | median_width_21 | ordering_verdict |
|---:|:---|---:|---:|---:|---:|:---|
| 1 | True  | 0.8015 | 0.6954 | 0.5520 | 0.1260 | PASS |
| 1 | False | 0.8127 | 0.7097 | 0.6369 | 0.5654 | PASS |
| 2 | True  | 0.6435 | 0.5645 | 0.4127 | 0.1657 | PASS |
| 2 | False | 0.6737 | 0.5772 | 0.5427 | 0.5309 | PASS |
| 4 | True  | 0.2357 | 0.2927 | 0.3607 | 0.1558 | FLAG |
| 4 | False | 0.5333 | 0.5379 | 0.5589 | 0.5635 | FLAG |

## Decisions Made

- Named `DETREND_POLY_ORDER=4` (not continuity tracking) as the isolated root cause, based directly on where the verdict column flips in the sweep, not on any preference for a simpler explanation.
- Wrote the fix-selection criterion in residual/physical terms (the detrend background must not follow the bead corridor) rather than in terms of which sweep cell passes ordering, per the plan's explicit no-outcome-shopping prohibition.
- Explicitly scoped the sweep to establish cause only — bead-masking (the endorsed remedy) is intentionally not one of the swept axes; its efficacy is deferred to a synthetic regression test in plan 01-07, not to sweep evidence.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- `numpy` emitted the existing `All-NaN slice encountered` RuntimeWarning while binning empty native-column bins during the sweep; this is the same established, harmless warning already handled by the invalid-mask path in `src/targets.py` and observed in prior plans' real-data runs.

## Known Stubs

None. All sentinel handling (`None` for a track/config cell with a failed detrend fit or zero valid columns) is an intentional, documented degenerate-case marker per the plan's must-haves, not a user-facing placeholder.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-07 has a committed, pre-registered, outcome-independent criterion to select and justify exactly one uniform correction (bead-masking is the endorsed remedy) without outcome-shopping among sweep cells.
- Plan 01-07 should add the synthetic regression `test_robust_plane_detrend_fit_mask_excludes_bead_from_fit` referenced in the diagnosis to prove the mask remedy's mechanism, since the sweep intentionally does not cover the mask axis.
- Plan 01-08 can report the resulting `8 > 10 > 14 > 21` ordering as an honest outcome of the 01-07 fix, referencing this diagnosis for why the fix was chosen.

## Self-Check: PASSED

- `scripts/diagnose_width_regression.py` and `.planning/phases/01-target-extraction-contract/01-06-DIAGNOSIS.md` exist on disk.
- Commits `e9c3465` and `86aef23` exist in `git log`.
- `processed_data/targets/diagnostics/width_regression_sweep.csv` exists with 6 configuration rows (verified via `grep -Ec '(PASS|FLAG)'` = 6).
- `processed_data/targets/extraction_params.json` and `manifest.json` are byte-identical (md5-checked) before and after the diagnostic run; `data/raw/` integrity PASS printed on both runs.
- Full test suite (`tests/test_nsf_fmrg_data.py`, `tests/test_run_target_extraction.py`, `tests/test_targets.py`) remains 44/44 PASS after this plan.

---
*Phase: 01-target-extraction-contract*
*Completed: 2026-07-20*
