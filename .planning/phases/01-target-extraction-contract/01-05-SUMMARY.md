---
phase: 01-target-extraction-contract
plan: 05
subsystem: data-processing
tags: [profilometry, boundary-tracking, smoothing, numpy, tdd]

requires:
  - phase: 01-target-extraction-contract
    provides: locked extraction contract, quartic detrending, and diagnosed boundary/smoothing gaps
provides:
  - Continuity-tracked half-max candidate selection with clipped-run exclusion
  - Ten-column stale-history reset for long invalid gaps
  - Residual-degree-preserving smoothing for three-point finite windows
  - Regenerated four-track QA with quantitative before/after evidence
affects: [target-extraction, dataset-alignment, model-training, submission-qa]

tech-stack:
  added: []
  patterns: [sequential boundary-state tracking, stale-anchor expiry, residual-degree-preserving local fits, TDD red-green regression]

key-files:
  created: []
  modified: [src/targets.py, tests/test_targets.py]

key-decisions:
  - "Enumerate every non-clipped half-max run, use the largest candidate without fresh history, and otherwise select the candidate nearest the previous successful boundary center."
  - "Expire previous_center after ten consecutive invalid columns so long-gap resumptions cannot silently lock to a stale location."
  - "Use degree min(SG_POLYORDER, finite_count - 2) so every fitted smoothing window retains at least one residual degree of freedom."
  - "Address sawtooth behavior at candidate selection rather than widening the smoothing window; only the confirmed three-point degeneracy changes smoothing behavior."

patterns-established:
  - "Boundary continuity: state updates only after successful extraction and survives short, but not long, invalid runs."
  - "Candidate safety: boundary-clipped runs are filtered before either tracked or untracked selection."

requirements-completed: [TARGET-01, TARGET-02]

coverage:
  - id: D1
    description: "Half-max extraction tracks the nearest non-clipped candidate across columns and resets stale history after long gaps."
    requirement: TARGET-01
    verification:
      - kind: unit
        ref: "tests/test_targets.py#six continuity-tracking regressions"
        status: pass
    human_judgment: false
  - id: D2
    description: "Three-finite-point nan_savgol windows perform real damping with one residual degree of freedom."
    requirement: TARGET-01
    verification:
      - kind: unit
        ref: "tests/test_targets.py#test_nan_savgol_no_longer_exact_interpolates_three_point_window"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_nan_savgol_track10_crop_edge_regression"
        status: pass
    human_judgment: false
  - id: D3
    description: "Four-track artifacts were regenerated and boundary-jump frequency fell on every track and boundary."
    requirement: TARGET-02
    verification:
      - kind: integration
        ref: ".venv/bin/python scripts/check_targets.py --project_dir ."
        status: pass
      - kind: manual_procedural
        ref: "processed_data/targets/qa/track_{8,10,14,21}_{overlay,width}.png"
        status: pass
    human_judgment: true
    rationale: "The figures show a substantial quantitative reduction but retain visible fragmentation and occasional large excursions; scientific adequacy still requires reviewer judgment."

duration: 6min
completed: 2026-07-20
status: complete
---

# Phase 01 Plan 05: Boundary Continuity and Sparse-Window Smoothing Summary

**Continuity-tracked half-max boundaries and residual-degree-preserving sparse-window smoothing reduce large boundary jumps across all four real tracks without per-track tuning.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-07-20T05:28:26Z
- **Completed:** 2026-07-20T05:34:55Z
- **Tasks:** 2 TDD tasks / 4 atomic commits
- **Files modified:** 2 committed files plus regenerated local target/QA artifacts

## Accomplishments

- Added `all_true_runs()` and continuity-aware `halfmax_edges()`: fresh history selects the nearest non-clipped candidate, while absent or expired history preserves the original largest-run fallback.
- Added a shared `MAX_TRACKING_GAP_COLUMNS = 10` expiry rule, with synthetic long-gap/drift/decoy coverage proving a stale anchor cannot capture the resumed boundary.
- Changed the three-finite-point smoothing fit from degree 2 to degree 1, guaranteeing real damping, and regenerated/validated all four real-track artifacts.

## Task Commits

Each TDD stage was committed atomically:

1. **Task 1 RED: Add continuity-tracking regressions** - `98ba3c3` (test)
2. **Task 1 GREEN: Implement continuity tracking and stale reset** - `1a4ea88` (fix)
3. **Task 2 RED: Add degenerate-window regressions** - `b68e03c` (test)
4. **Task 2 GREEN: Preserve residual degrees of freedom** - `beea484` (fix)

## Files Created/Modified

- `src/targets.py` - Candidate enumeration, continuity selection, stale-history reset, and corrected smoothing degree.
- `tests/test_targets.py` - Six continuity regressions, two new sparse-window regressions, and corrected crop-edge/gap references.
- `processed_data/targets/` - Regenerated local `.npz`, manifest/provenance, and QA figures; intentionally excluded from source history.

## Continuity Design and Proof

`halfmax_edges()` now filters every boundary-clipped run before selection. With no usable history it selects the greatest-length run with the original earliest-first tie behavior. With fresh history it selects the run nearest the previous successful boundary center, breaking ties by length and then position. The full-pipeline decoy test first proves an untracked call picks the larger decoy, then proves sequential extraction stays on the smaller continuous bead.

`extract_targets_from_arrays()` updates `previous_center` only after a successful column. Invalid columns retain the anchor for short gaps; once ten consecutive columns have elapsed, the anchor is cleared before the next selection. The long-gap regression proves a stale center would pick a planted decoy directly, while the full pipeline expires that center and selects the larger genuinely drifted bead.

## Smoothing Design and Proof

`nan_savgol()` now uses `min(SG_POLYORDER, finite_count - 2)`. A three-point window therefore fits degree 1, leaving one residual degree of freedom, rather than fitting a degree-2 exact interpolant. Four- and five-point behavior is unchanged. Independent degree-one references pin the corrected crop-edge and masked-gap expectations, and a Track-10-shaped three-column-gap/final-three-point-run regression proves every terminal point is damped.

The G-01-2 “and/or” choice was resolved in favor of candidate continuity, not a wider or more aggressive smoothing pass: the diagnosed defect was upstream blob ambiguity, while the contracted five-point smoother was otherwise functioning as designed. The only smoothing change is the mathematically degenerate three-point case confirmed by G-01-3.

## Real-Data Jump Comparison

For an apples-to-apples causal comparison, the “before” values below were recomputed from immediate pre-plan commit `8d0cfb9` against the same raw files and order-4 detrend. Statistics use adjacent finalized finite boundary pairs.

| Track | Boundary | Max abs step before → after (mm) | Step std before → after (mm) | Count abs step >0.1 mm before → after |
|---:|:---|:---|:---|:---|
| 8 | lower | 1.420 → 0.676 | 0.279 → 0.100 | 229 → 63 |
| 8 | upper | 1.425 → 0.646 | 0.345 → 0.135 | 218 → 79 |
| 10 | lower | 1.143 → 0.553 | 0.262 → 0.124 | 119 → 56 |
| 10 | upper | 0.946 → 0.490 | 0.266 → 0.152 | 114 → 72 |
| 14 | lower | 0.758 → 0.729 | 0.220 → 0.162 | 92 → 77 |
| 14 | upper | 0.871 → 0.686 | 0.218 → 0.166 | 95 → 70 |
| 21 | lower | 0.644 → 0.518 | 0.186 → 0.146 | 150 → 99 |
| 21 | upper | 0.861 → 0.646 | 0.202 → 0.140 | 154 → 95 |

Every track/boundary improved in jump count and standard deviation. Seven of eight also improved materially in maximum step; Track 14 lower improved modestly from 0.758 to 0.729 mm.

The original debug-session raw-boundary baseline remains part of the audit trail: Track 8 lower/upper max-count pairs were 0.674/134 and 0.893/33; Track 10 0.729/48 and 1.091/13; Track 14 1.165/74 and 1.114/120; Track 21 1.295/220 and 1.376/192. Those numbers are not directly paired with the final table because the intervening order-4 detrend changed candidate populations and valid adjacent-step counts; `8d0cfb9` supplies the controlled immediate-before comparison.

## Track 10 Crop-Edge Re-check

| Evidence point | Index 397 | Index 398 | Index 399 |
|---|---:|---:|---:|
| Original UAT final width (mm) | 0.228 | 0.147 | 0.800 |
| Immediate pre-plan `8d0cfb9` final width (mm) | 0.2074 | 0.2072 | 0.5433 |
| Post-plan raw tracked width (mm) | 0.0087 | 0.0243 | 0.5433 |
| Post-plan finalized width (mm) | invalid | 0.0982 | 0.4593 |

Index 397 is now honestly remasked because separate boundary smoothing produced a crossed/negative width (`-0.0413 mm`), invoking the existing post-smoothing validity contract. The connected final jump from index 398 to 399 is 0.3611 mm, versus 0.6531 mm in the original UAT sequence, a 44.7% reduction. The terminal excursion is substantially reduced but not eliminated.

## Visual Re-check

All eight regenerated overlay/width figures were inspected. Compared with the original UAT failure language, rapid EKG-like switching is visibly less frequent and the quantitative reduction is strong on Track 8 and Track 21. Track 10's original three-point terminal V is no longer present as a fully connected three-point segment because index 397 is invalid and the remaining final jump is smaller. However, the curves remain fragmented and retain occasional large excursions on every track—especially Track 10 and Track 14—so this result should be described as a substantial reduction, not a fully smooth or visually pristine boundary solution.

## Decisions Made

- Kept the new history state local to the deterministic left-to-right extraction pass; no global or per-track mutable state was introduced.
- Fixed `MAX_TRACKING_GAP_COLUMNS` uniformly at ten based on the diagnosed stale-anchor risk, without tuning against regenerated outcomes.
- Preserved Amendment A2 by excluding clipped runs before all candidate ranking.
- Did not change any constant or source after real-data regeneration; ordering and visual outcomes are reported as observed.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- NumPy emitted the existing `All-NaN slice encountered` warning for empty native bins; the established invalid-mask path handled those bins and the pipeline completed.
- The regenerated width ordering is Track 8 < Track 10 < Track 14 > Track 21, producing FLAGS for 8-vs-10 and 10-vs-14. No parameter was changed in response.
- Visual roughness is reduced but not eliminated; remaining fragmentation and spikes require phase-level scientific UAT rather than being hidden by stronger post-hoc smoothing.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- G-01-2 and G-01-3's confirmed mechanisms are closed by direct regressions and passing real-data artifact checks.
- Phase 1 should undergo final human UAT using the regenerated figures, with explicit attention to the remaining fragmentation and ordering FLAGS before Phase 2 treats these widths as ground truth.

## Self-Check: PASSED

- `src/targets.py` and `tests/test_targets.py` exist and all four `01-05` task commits are present.
- `.venv/bin/python tests/test_targets.py` reports 23 PASS lines.
- `.venv/bin/python scripts/check_targets.py --project_dir .` reports `ALL CHECKS PASSED`.
- All four regenerated `.npz` targets and eight reviewed overlay/width QA figures exist.
- `git diff --stat -- src/targets.py` remained empty throughout real-data regeneration.

---
*Phase: 01-target-extraction-contract*
*Completed: 2026-07-20*
