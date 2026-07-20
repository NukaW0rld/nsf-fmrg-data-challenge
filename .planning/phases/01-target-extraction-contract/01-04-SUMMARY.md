---
phase: 01-target-extraction-contract
plan: 04
subsystem: data-processing
tags: [profilometry, detrending, polynomial-surface, numpy, tdd]

requires:
  - phase: 01-target-extraction-contract
    provides: locked target extraction contract, real-data QA pipeline, and diagnosed residual-curvature gap
provides:
  - Configurable robust total-degree polynomial surface detrending with an affine-compatible default
  - Shared order-4 target-extraction parameter with persisted provenance
  - Amendment A3 traceability and regenerated four-track QA evidence
affects: [target-extraction, dataset-alignment, model-training, submission-qa]

tech-stack:
  added: []
  patterns: [centered bivariate-polynomial basis, shared extraction parameterization, TDD red-green regression]

key-files:
  created: [tests/test_nsf_fmrg_data.py]
  modified: [src/nsf_fmrg_data.py, src/targets.py, tests/test_targets.py, .planning/phases/01-target-extraction-contract/01-CONTEXT.md]

key-decisions:
  - "Amendment A3 fixes DETREND_POLY_ORDER=4 a priori from the diagnosed per-track R² evidence and applies it identically to all tracks."
  - "The affine-compatible order=1 default, three-pass percentile trimming, and stride_x=40/stride_y=2 sampling remain unchanged for existing callers."
  - "Post-fix ordering FLAGS are reported without changing any locked extraction constant."

patterns-established:
  - "Polynomial surface fit: enumerate all total-degree <= order terms and center coordinates before exponentiation."
  - "Contract amendment: append superseding evidence and rationale directly to the phase CONTEXT decisions block."

requirements-completed: [TARGET-01, TARGET-02]

coverage:
  - id: D1
    description: "robust_plane_detrend supports affine-compatible order=1 and quartic order=4 surface fits."
    requirement: TARGET-01
    verification:
      - kind: unit
        ref: "tests/test_nsf_fmrg_data.py (4 tests)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Target extraction applies one shared DETREND_POLY_ORDER=4 parameter and persists it in provenance."
    requirement: TARGET-02
    verification:
      - kind: integration
        ref: ".venv/bin/python tests/test_targets.py and scripts/check_targets.py --project_dir ."
        status: pass
    human_judgment: false
  - id: D3
    description: "Regenerated residual maps remove the original global bow while honestly retaining visible localized/process-scale structure."
    requirement: TARGET-02
    verification:
      - kind: manual_procedural
        ref: "processed_data/targets/qa/track_{8,10,14,21}_residual_map.png"
        status: pass
    human_judgment: true
    rationale: "Distinguishing removable systematic curvature from genuine process texture requires scientific visual judgment."

duration: 4min
completed: 2026-07-20
status: complete
---

# Phase 01 Plan 04: Quartic Surface Detrending Summary

**Centered robust quartic surface detrending now removes the diagnosed global bow under one shared, provenance-locked four-track parameterization.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-07-20T05:19:21Z
- **Completed:** 2026-07-20T05:23:02Z
- **Tasks:** 2
- **Files modified:** 5 committed source/planning files plus regenerated local target artifacts

## Accomplishments

- Generalized `robust_plane_detrend()` from a fixed affine plane to a configurable centered total-degree polynomial basis while preserving `order=1` as the backward-compatible default.
- Locked `DETREND_POLY_ORDER = 4` into the single shared extraction parameterization and recorded Amendment A3 directly in `01-CONTEXT.md`.
- Regenerated all four real-track target/QA artifact sets; all persisted artifact checks passed and all residual maps have post-plan mtimes.
- Re-ran the pre-fix residual-curve methodology and visually inspected all four regenerated residual maps without adjusting constants afterward.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Add polynomial detrend regressions** - `62276b2` (test)
2. **Task 1 GREEN: Implement shared order-4 surface fit and Amendment A3** - `78b6314` (fix)
3. **Task 2: Regenerate and validate local four-track artifacts** - `d836083` (chore; empty by design because generated artifacts are excluded from source history)

## Files Created/Modified

- `tests/test_nsf_fmrg_data.py` - Four plain-Python regressions for affine equivalence, quartic recovery, degenerate fallback, and basis sizes.
- `src/nsf_fmrg_data.py` - Configurable centered bivariate-polynomial robust detrending.
- `src/targets.py` - Shared `DETREND_POLY_ORDER=4` constant, provenance, and call-site wiring.
- `tests/test_targets.py` - Updated exact extraction-parameter provenance contract.
- `.planning/phases/01-target-extraction-contract/01-CONTEXT.md` - Amendment A3 with pre-regeneration R² grounding.
- `processed_data/targets/` - Regenerated local `.npz`, manifest/provenance, and QA artifacts; intentionally not committed.

## Quantitative Residual Re-check

The diagnostic exactly repeated the debug session's method: load each real height map, detrend it, take the per-x-column median residual, and fit degree 1, 2, and 4 polynomials to that curve.

| Track | Pre-fix linear R² | Pre-fix quadratic R² | Pre-fix quartic R² | Post-fix linear R² | Post-fix quadratic R² | Post-fix quartic R² |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 0.036 | 0.977 | n/a | 0.019 | 0.060 | 0.178 |
| 10 | 0.086 | 0.469 | 0.640 | 0.051 | 0.111 | 0.348 |
| 14 | 0.001 | 0.963 | n/a | 0.054 | 0.063 | 0.114 |
| 21 | 0.004 | 0.295 | 0.449 | 0.001 | 0.104 | 0.353 |

The dominant quadratic bow signal fell from 0.977 to 0.060 on track 8 and from 0.963 to 0.063 on track 14. Track 10's quartic-explainable fraction fell from 0.640 to 0.348, and track 21's fell from 0.449 to 0.353. These post-fit R² values are not expected to be exactly zero because the diagnostic is fit to column medians of the full two-dimensional residual after robust trimming, and genuine bead/process structure remains.

## Visual Re-check

The original coherent, full-map end-positive/center-negative bow is dramatically reduced on tracks 8, 10, and 14; the clean symmetric basin previously reported for track 14 is no longer present. Track 21's original broad alternating pattern is also reduced, although a weaker blue-to-red structure remains near roughly 70-95 mm. The regenerated maps still show vertical/local texture and track-band lobes—most visibly on tracks 14 and 21—so the outcome is not described as featureless random noise. Those remnants are spatially tied to the processed band and are retained as plausible local process/width variation rather than chased with a higher or per-track detrend order.

## Post-fix Width Ordering

| Comparison | Median widths | Outcome |
|---|---|---|
| Track 8 vs 10 | 0.5514 mm > 0.5415 mm | PASS |
| Track 10 vs 14 | 0.5415 mm > 0.5817 mm | FLAG |
| Track 14 vs 21 | 0.5817 mm > 0.5999 mm | FLAG |

The two new ordering FLAGS were recorded exactly as produced. No constant or source file changed after regeneration.

## Amendment A3

Amendment A3 supersedes the instruction to keep the affine detrend unchanged after D-14's mandatory QA check surfaced its anticipated limitation. It establishes a configurable `order` with a backward-compatible affine default, fixes the target pipeline to shared order 4 based on the already-measured track 21 evidence, preserves the existing robust trimming and stride, and prohibits outcome-driven per-track special-casing.

## Decisions Made

- Used the full total-degree-≤4 bivariate basis (15 coefficients) rather than x-only terms so the surface contract covers coupled x/y curvature.
- Centered both coordinate axes at full-grid midpoints before exponentiation to control conditioning without changing the representable fitted surface.
- Preserved and reported post-regeneration ordering FLAGS instead of tuning the locked extractor against expected power ordering.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Validate polynomial order inputs**
- **Found during:** Task 1 implementation
- **Issue:** A configurable public order without validation could fail obscurely inside basis generation.
- **Fix:** Reject non-integer or negative orders with a clear `ValueError` after preserving the existing degenerate-data fallback.
- **Files modified:** `src/nsf_fmrg_data.py`
- **Verification:** All four new regressions and all fifteen target tests pass.
- **Committed in:** `78b6314`

---

**Total deviations:** 1 auto-fixed (1 missing critical validation)
**Impact on plan:** Input validation is local to the new configuration seam; no scope or dependency expansion.

## Issues Encountered

- NumPy emitted the existing `All-NaN slice encountered` warning while binning columns containing no finite samples; the pipeline handled those bins through its established mask path and completed successfully.
- Generated target/QA artifacts are intentionally excluded from source commits, so Task 2 is represented by an empty audit commit after successful regeneration and verification.

## Known Stubs

None. Empty-list/dict initializations and `coef = None` in modified/scanned files are normal accumulators or the documented degenerate-fit sentinel, not user-facing placeholders.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Gap G-01-1's model-order limitation is closed with tests, provenance, real-data regeneration, and visual evidence.
- The post-fix 10>14 and 14>21 ordering FLAGS remain explicit scientific QA concerns; no parameter was tuned to hide them.
- Plans addressing boundary continuity and crop-edge smoothing remain scoped to 01-05.

## Self-Check: PASSED

- Created/modified source and planning files exist.
- Commits `62276b2`, `78b6314`, and `d836083` exist.
- Four detrend tests, fifteen target tests, and `scripts/check_targets.py --project_dir .` pass.

---
*Phase: 01-target-extraction-contract*
*Completed: 2026-07-20*
