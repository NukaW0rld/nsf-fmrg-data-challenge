---
phase: 01-target-extraction-contract
plan: 13
subsystem: data
tags: [profilometry, detrending, polynomial-fit, numpy, tdd]

# Dependency graph
requires:
  - phase: 01-target-extraction-contract
    provides: Amendment A5 (DETREND_MAX_Y_DEGREE=2, plan 01-11) and the confirmed root cause in .planning/debug/track10-14-ordering-tail-collapse.md (plan 01-12)
provides:
  - "01-13-CRITERION.md: pre-registered, outcome-independent x-direction shape-gap criterion (SHAPE_GAP_EDGE_TOLERANCE_MM=0.012mm) committed before any src change"
  - "DETREND_MAX_XY_DEGREE=2 (Amendment A6) capping cross-track interaction-term x-exponents in robust_plane_detrend"
  - "scripts/diagnose_track10_tail_collapse.py: committed, re-runnable measurement of the fitted surface's own x-direction shape-gap departure"
  - "01-13-ORDERING-OUTCOME.md: honest report that the 10-vs-14 width-ordering FLAG persists (and widened) under the corrected contract, recommending option (a) acceptance"
affects: [01-14-boundary-fragmentation, phase-1-verification-signoff]

# Tech tracking
tech-stack:
  added: []
  patterns: ["pre-registered outcome-independent fix-selection criterion committed to git before any src change (mirrors 01-11-CRITERION.md)"]

key-files:
  created:
    - scripts/diagnose_track10_tail_collapse.py
    - processed_data/diagnostics/track10_tail_collapse_diagnosis.csv
    - .planning/phases/01-target-extraction-contract/01-13-CRITERION.md
    - .planning/phases/01-target-extraction-contract/01-13-ORDERING-OUTCOME.md
  modified:
    - src/nsf_fmrg_data.py
    - src/targets.py
    - tests/test_nsf_fmrg_data.py
    - tests/test_targets.py
    - .planning/phases/01-target-extraction-contract/01-CONTEXT.md

key-decisions:
  - "Pre-registered SHAPE_GAP_EDGE_TOLERANCE_MM=0.012mm from this plan's own measured departures (healthy tracks max 0.006166mm, track 10 0.021200mm), not reused from 01-11-CRITERION.md's 0.05mm since this metric's natural scale differs."
  - "DETREND_MAX_XY_DEGREE=2 selected as the largest shared cap clearing the criterion on all 4 real tracks without regressing the quartic-bow-removal or y-edge-divergence regressions -- fixed before running the extractor or inspecting any width/ordering result."
  - "Recorded Amendment A6 in 01-CONTEXT.md, superseding nothing in A3/A4/A5."
  - "Regenerated all 4 tracks in a single atomic run; the 10-vs-14 ordering FLAG persists (and widened: track 10's median dropped further, from 0.3713mm under A5 to 0.2589mm under A6). No constant was changed in response."
  - "Recommended accepting the 10-vs-14 FLAG as a documented, investigated, known limitation (option a) for the next human verification round -- this was the phase's last authorized bounded, criterion-driven cycle for this defect class per 01-UAT.md Test 5."

patterns-established:
  - "Task-level RED/GREEN TDD discipline for a single non-tdd-typed plan: failing tests committed before implementation, even though the plan frontmatter is type=execute rather than type=tdd."

requirements-completed: [TARGET-01, TARGET-02]

coverage:
  - id: D1
    description: "DETREND_MAX_XY_DEGREE cap added to robust_plane_detrend, capping only cross/interaction terms (y-exponent>=1) by x-exponent, defaulting to None (bit-for-bit unchanged for every other caller), selected via a criterion pre-registered before any src change"
    requirement: "TARGET-01"
    verification:
      - kind: unit
        ref: "tests/test_nsf_fmrg_data.py#test_polynomial_basis_sizes_are_stable"
        status: pass
      - kind: unit
        ref: "tests/test_nsf_fmrg_data.py#test_detrend_caps_xy_interaction_degree_at_domain_edge"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_xy_interaction_cap_is_track_independent"
        status: pass
      - kind: unit
        ref: "tests/test_nsf_fmrg_data.py#test_order_four_removes_quartic_bow"
        status: pass
      - kind: unit
        ref: "tests/test_nsf_fmrg_data.py#test_detrend_does_not_diverge_at_strip_edge"
        status: pass
    human_judgment: false
  - id: D2
    description: "All 4 tracks regenerated atomically under Amendment A6 in a single run; extraction_params()/manifest.json provenance intact (17 keys, digest change-sensitive), MIN_VALID_FRACTION floor cleared by all tracks, diagnostics CSV survives publish_staging_dir"
    requirement: "TARGET-02"
    verification:
      - kind: integration
        ref: "scripts/run_target_extraction.py --project_dir . && scripts/check_targets.py --project_dir . (exit 0, ALL CHECKS PASSED)"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_extraction_params_provenance"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_provenance_digest_is_change_sensitive"
        status: pass
    human_judgment: false
  - id: D3
    description: "10-vs-14 width-ordering FLAG persists (and widened) after the corrected Amendment A6 contract; report recommends accepting it as a documented, investigated, known limitation (option a) for the next human verification round"
    verification: []
    human_judgment: true
    rationale: "Whether to ratify the 8>10>14>21 ordering FLAG as a permanent, accepted known limitation is a domain/scientific judgment call for the human sign-off round (/gsd-verify-work), not something an automated test can certify."

# Metrics
duration: 18min
completed: 2026-07-21
status: complete
---

# Phase 1 Plan 13: X-Direction Shape-Gap Criterion and DETREND_MAX_XY_DEGREE Cap Summary

**Pre-registered an outcome-independent x-direction shape-gap criterion, implemented the sole DETREND_MAX_XY_DEGREE=2 cap it selected (Amendment A6), and regenerated all 4 tracks -- the 10-vs-14 width-ordering FLAG persists and widened, honestly reported with a recommendation to accept it as a documented known limitation.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-07-22T03:02:21Z
- **Completed:** 2026-07-22T03:21:36Z
- **Tasks:** 3 completed
- **Files modified:** 9 (4 created, 5 modified; excludes gitignored `processed_data/targets/` regenerated artifacts)

## Accomplishments
- Measured the fitted surface's own x-direction shape-gap departure (far edge x~99mm vs interior midpoint x~60mm) for all 4 real tracks via a new committed, re-runnable diagnostic (`scripts/diagnose_track10_tail_collapse.py`), and pre-registered a falsifiable `SHAPE_GAP_EDGE_TOLERANCE_MM=0.012mm` criterion in `01-13-CRITERION.md` before any source change existed.
- Implemented `max_xy_degree` on `robust_plane_detrend` (caps cross/interaction-term x-exponents only, leaving pure along-track terms fully intact) and locked `DETREND_MAX_XY_DEGREE=2` in `src/targets.py` as the largest value clearing the criterion on all 4 real tracks, verified via task-level RED/GREEN TDD.
- Recorded Amendment A6 in `01-CONTEXT.md`, superseding nothing in A3/A4/A5.
- Regenerated all 4 tracks atomically and reported the 10-vs-14 ordering outcome verbatim in `01-13-ORDERING-OUTCOME.md`: the FLAG persists (track 10's median dropped from 0.3713mm under A5 to 0.2589mm under A6 -- the gap widened, not narrowed), with an explicit recommendation to accept it as a documented, investigated, known limitation (option a) since this was the phase's last authorized bounded cycle for this defect class.

## Task Commits

Each task was committed atomically:

1. **Task 1: Measure the x-direction shape-gap evidence and pre-register the fix-selection criterion** - `53bcb1e` (feat)
2. **Task 2: Implement the DETREND_MAX_XY_DEGREE cap, verify against the criterion, and record Amendment A6** - `6034203` (test, RED) then `8e7f7ff` (fix, GREEN)
3. **Task 3: Regenerate all 4 tracks and report the 10-vs-14 ordering outcome honestly** - `652e410` (docs)

**Plan metadata:** committed after this summary (see final metadata commit).

## Files Created/Modified
- `scripts/diagnose_track10_tail_collapse.py` - Measures the fitted surface's own x-direction shape-gap departure for all 4 tracks under the exact production detrend path; computes no fix-outcome candidate, width, or ordering verdict
- `processed_data/diagnostics/track10_tail_collapse_diagnosis.csv` - Measured shape_gap(x) at 9 sampled positions plus interior/far-edge/departure per track (sibling of `processed_data/targets/`, survives publish)
- `.planning/phases/01-target-extraction-contract/01-13-CRITERION.md` - Pre-registered, outcome-independent criterion; committed before any src change
- `.planning/phases/01-target-extraction-contract/01-13-ORDERING-OUTCOME.md` - Honest, verbatim regeneration report and option-(a) recommendation
- `src/nsf_fmrg_data.py` - `robust_plane_detrend` gains `max_xy_degree=None` keyword (bit-for-bit unchanged default)
- `src/targets.py` - Locks `DETREND_MAX_XY_DEGREE=2` (Amendment A6), passes it through `extract_track_targets`, adds it to `extraction_params()` (17 keys)
- `tests/test_nsf_fmrg_data.py` - Extends `test_polynomial_basis_sizes_are_stable`; adds `test_detrend_caps_xy_interaction_degree_at_domain_edge`
- `tests/test_targets.py` - Adds `test_xy_interaction_cap_is_track_independent`; bumps provenance test to 17 keys; extends digest-sensitivity test
- `.planning/phases/01-target-extraction-contract/01-CONTEXT.md` - Records Amendment A6

## Decisions Made
- `SHAPE_GAP_EDGE_TOLERANCE_MM=0.012mm` derived from this plan's own measured departures (healthy tracks' largest departure 0.006166mm, track 10's 0.021200mm) -- not reused verbatim from `01-11-CRITERION.md`'s `0.05mm`, since this metric's natural scale is narrower.
- `DETREND_MAX_XY_DEGREE=2` selected as the largest shared cap clearing the criterion on all 4 real tracks while keeping `test_order_four_removes_quartic_bow` and `test_detrend_does_not_diverge_at_strip_edge` green -- fixed before running the extractor or inspecting any width/ordering result (verified via a local synthetic/real-data probe before touching `src/`, per the plan's `<action>` step).
- No fallback/non-recoverable branch was needed: a shared value (2) existed clearing the criterion, so Amendment A6 was applied.
- The regenerated 10-vs-14 ordering outcome is reported exactly as measured (FLAG persists, gap widened) with no reinterpretation; recommended accepting it as a documented known limitation (option a) since this was the phase's last authorized bounded cycle.

## Deviations from Plan

None - plan executed exactly as written, including its explicit anticipation that clearing the criterion would not necessarily flip the resulting width ordering. The plan's non-recoverable branch (no fix applied) was not triggered because a shared `DETREND_MAX_XY_DEGREE` value did clear the criterion; the persisting FLAG in Task 3 is the honestly-reported outcome the plan's `<action>` explicitly required regardless of direction.

## TDD Gate Compliance

Task 2's task-level TDD discipline is confirmed compliant: `test(01-13): add failing xy-interaction-degree regressions` (`6034203`, RED) precedes `fix(01-13): cap cross-track interaction degree in robust_plane_detrend` (`8e7f7ff`, GREEN) in git history, and both new tests (`test_detrend_caps_xy_interaction_degree_at_domain_edge`, `test_xy_interaction_cap_is_track_independent`) failed before the implementation and pass after it.

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- UAT gap G-01-4's authorized bounded investigation-and-fix cycle is complete. `01-13-ORDERING-OUTCOME.md` recommends the human verification round (`/gsd-verify-work 1`) ratify option (a) -- accept the 10-vs-14 FLAG as a documented, investigated, known limitation -- since no further open-ended tuning cycle is authorized for this defect class.
- G-01-5 (boundary-overlay fragmentation) remains out of scope for this plan and is addressed by `01-14-PLAN.md`, the next wave.
- `processed_data/targets/` artifacts are regenerated and current under the Amendment A6 contract; `check_targets.py` exits 0.

---
*Phase: 01-target-extraction-contract*
*Completed: 2026-07-21*

## Self-Check: PASSED

All 9 key files found on disk; all 4 task commit hashes (`53bcb1e`, `6034203`, `8e7f7ff`, `652e410`) found in git history.
