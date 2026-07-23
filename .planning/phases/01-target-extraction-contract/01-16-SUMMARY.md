---
phase: 01-target-extraction-contract
plan: 16
subsystem: data-processing
tags: [profilometry, boundary-tracking, numpy, gap-closure]

# Dependency graph
requires:
  - phase: 01-target-extraction-contract (plan 14, Amendment A7)
    provides: merge_adjacent_runs + MIN_TRACKED_LENGTH_RATIO same-column plausibility gate
provides:
  - halfmax_edges clip-exclusion applied to raw runs before merging (Mechanism A fix)
  - history-based joint far-AND-small plausibility gate using previous_length_mm (Mechanism B fix)
  - Amendment A8 in 01-CONTEXT.md
  - regenerated 4-track target artifacts and honest fragmentation/jump-statistic/crop-edge report (01-16-ORDERING-OUTCOME.md)
affects: [phase 2 alignment, any future revisit of boundary-tracking robustness]

# Tech tracking
tech-stack:
  added: []
  patterns: [clip-before-merge candidate filtering, history-threaded joint distance-and-size plausibility gate]

key-files:
  created:
    - .planning/phases/01-target-extraction-contract/01-16-ORDERING-OUTCOME.md
  modified:
    - src/targets.py
    - tests/test_targets.py
    - .planning/phases/01-target-extraction-contract/01-CONTEXT.md

key-decisions:
  - "Reordered halfmax_edges to apply D-01/D-03 clip-exclusion to raw runs before merge_adjacent_runs, closing Mechanism A (65-90% of no_candidates invalidations)."
  - "Added a history-based joint far-AND-small gate reusing MIN_TRACKED_LENGTH_RATIO and runtime-derived previous_length_mm, closing Mechanism B (14-72% of tracked selections in single-candidate columns) with zero new constants."
  - "Mechanism C (greedy nearest-to-previous_center hopping) re-examined and again found not tractable within scope; explicitly not implemented, residual effect reported honestly."
  - "Regenerated all 4 tracks under Amendment A8; did not tune any locked constant in response to the outcome, and did not reopen the already-accepted 10-vs-14 width-ordering FLAG (UAT Test 7)."

patterns-established:
  - "Clip-exclusion-before-merge: any future run-fragmentation-merging logic must filter boundary-touching runs before merging, never after."
  - "History-threaded joint gate: reuse an already-locked ratio constant against a runtime-derived prior-state quantity rather than introducing a new tunable number."

requirements-completed: [TARGET-01, TARGET-02]

coverage:
  - id: D1
    description: "halfmax_edges applies clip-exclusion to raw runs before merging (Mechanism A), verified against leading- and trailing-edge swallow reconstructions"
    requirement: "TARGET-01"
    verification:
      - kind: unit
        ref: "tests/test_targets.py#test_halfmax_edges_recovers_leading_edge_swallowed_interior_run"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_halfmax_edges_recovers_trailing_edge_swallowed_interior_run"
        status: pass
    human_judgment: false
  - id: D2
    description: "History-based joint far-AND-small plausibility gate (Mechanism B), verified against far+small/close+small/far+large and full-pipeline single-candidate-trigger-column cases"
    requirement: "TARGET-01"
    verification:
      - kind: unit
        ref: "tests/test_targets.py#test_halfmax_edges_rejects_lone_candidate_far_and_small_versus_tracked_history"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_halfmax_edges_accepts_lone_candidate_small_but_close_to_tracked_history"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_halfmax_edges_accepts_lone_candidate_far_but_large_versus_tracked_history"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_extract_targets_from_arrays_rejects_track8_style_single_candidate_trigger_column"
        status: pass
    human_judgment: false
  - id: D3
    description: "Real 4-track pipeline regenerated under Amendment A8; fragmentation/jump-statistic/crop-edge outcome reported honestly, 10-vs-14 FLAG not re-litigated"
    requirement: "TARGET-02"
    verification:
      - kind: other
        ref: ".venv/bin/python scripts/check_targets.py --project_dir . (exit 0, ALL CHECKS PASSED)"
        status: pass
    human_judgment: true
    rationale: "Full visual sign-off on the 12 regenerated QA figures (overlay/width plots) requires human judgment per this project's human_verify_mode: end-of-phase configuration -- deferred to the next /gsd-verify-work round, consistent with every prior plan in this phase."

duration: ~25min
completed: 2026-07-22
status: complete
---

# Phase 1 Plan 16: Clip-Before-Merge Reordering and History-Based Plausibility Gate (G-01-6) Summary

**Reordered halfmax_edges to clip-exclude boundary-touching raw runs before merging (Mechanism A) and added a history-based joint far-AND-small plausibility gate reusing MIN_TRACKED_LENGTH_RATIO and runtime-derived previous_length_mm (Mechanism B), then regenerated all 4 tracks with valid-bin coverage up on every track and fragmentation improved on 3 of 4.**

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-07-22
- **Tasks:** 2
- **Files modified:** 3 (src/targets.py, tests/test_targets.py, .planning/phases/01-target-extraction-contract/01-CONTEXT.md); 1 created (01-16-ORDERING-OUTCOME.md)

## Accomplishments
- Closed Mechanism A (merge-before-clip ordering defect, 65-90% of `no_candidates` invalidations): `halfmax_edges` now applies D-01/D-03 clip-exclusion to raw runs before `merge_adjacent_runs`, so a merged candidate can structurally never touch a y-strip boundary.
- Closed Mechanism B (same-column gate blind spot in single-candidate columns, 14-72% of tracked selections): added a history-based joint far-AND-small gate that reuses `MIN_TRACKED_LENGTH_RATIO` and derives its distance scale from runtime `previous_length_mm`, introducing zero new constants.
- Regenerated all 4 tracks under Amendment A8: valid-bin coverage increased on every track (368/232/309/338 vs Amendment A7's 361/202/301/308), contiguous-run fragmentation improved on tracks 8/14/21 (track 21 dropped 51%, from 43 to 21 runs), and both UAT-Test-8-cited crop-edge symptoms (track 10's isolated valid run, track 21's near-zero terminal drop) resolved.
- Honestly reported that Mechanism C's residual jitter persists at both tracks' far edges (not chased) and that the 10-vs-14 width-ordering FLAG persists and widened (0.2404mm -> 0.3182mm), without reopening the already-accepted FLAG (UAT Test 7).

## Task Commits

Each task was committed atomically:

1. **Task 1: Reorder clip-exclusion before merging and gate tracked selection by tracked-history plausibility (G-01-6)**
   - `a51c57b` (test) - added 6 failing regressions reproducing the diagnosed episodes, removed the superseded `test_merged_run_touching_boundary_remains_excluded`
   - `fbc22af` (fix) - reordered `halfmax_edges`, added the history-based joint gate, threaded `previous_length_mm` through `extract_targets_from_arrays`, recorded Amendment A8 in 01-CONTEXT.md
2. **Task 2: Regenerate all 4 tracks, report the fragmentation/jump-statistic/crop-edge outcome honestly** - `a9dbf7a` (docs) - single atomic regeneration run, `check_targets.py` exit 0, wrote `01-16-ORDERING-OUTCOME.md`

_TDD task-level RED/GREEN verified directly: with `src/targets.py` reverted to its pre-fix content, the new tests failed (`test_halfmax_edges_recovers_leading_edge_swallowed_interior_run` failed at the RED checkpoint); with the fix restored, all tests passed under both `.venv/bin/python tests/test_targets.py` and `-O`._

## Files Created/Modified
- `src/targets.py` - `halfmax_edges` reordered (clip-exclusion before merge), new `previous_length_mm` parameter and history-based joint gate; `extract_targets_from_arrays` threads `previous_length_mm` alongside `previous_center`
- `tests/test_targets.py` - removed `test_merged_run_touching_boundary_remains_excluded` (its fixture's correct outcome reverses under this fix); added 6 new regressions for Mechanisms A and B
- `.planning/phases/01-target-extraction-contract/01-CONTEXT.md` - Amendment A8 documenting both mechanisms, the no-new-constant rationale, and Mechanism C's reaffirmed deferral
- `.planning/phases/01-target-extraction-contract/01-16-ORDERING-OUTCOME.md` (created) - regeneration report: verbatim `check_targets.py` output, coverage table, fragmentation/jump-statistic before/after table, crop-edge last-6-grid-point inspection, honest 10-vs-14 verdict

## Decisions Made
- Applied D-01/D-03 clip-exclusion to raw runs (not merged runs) as the structural fix for Mechanism A -- a merged candidate can now never touch a boundary, by construction, not by a separate post-merge filter.
- Introduced the Mechanism B gate as a joint AND (far AND small) rather than either condition alone, verified directly against all three combinations plus a full-pipeline single-candidate reproduction, so plausible narrowing and plausible drift are both protected from over-rejection.
- Reused `MIN_TRACKED_LENGTH_RATIO` and the runtime-derived `previous_length_mm` for Mechanism B rather than inventing a new named constant -- `extraction_params()`'s 19-key set and its provenance digest tests are correctly left unchanged.
- Did not implement Mechanism C (DP/Viterbi joint-tracker) and did not adjust any locked constant in response to the regenerated outcome, per the plan's HONEST-OUTCOME GUARD.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected the trailing-edge-recovery test fixture's insufficient baseline/peak separation**
- **Found during:** Task 1 RED-phase verification
- **Issue:** The plan's suggested reuse of the exact `test_merged_run_touching_boundary_remains_excluded` fixture (`prof[5:15]=0.02`, `prof[20:480]=0.02`) has only 10 zero-valued pixels out of 480 (2.1%), so the 5th/95th percentile baseline/peak separation check (`MIN_PEAK_BASELINE_SEPARATION_MM`) itself returns `peak-base=0`, making `halfmax_edges` return `None` for an unrelated reason (insufficient separation) before ever reaching the clip-exclusion/merge logic this test exists to exercise -- the original test coincidentally passed for the wrong reason.
- **Fix:** Redesigned the fixture with the same structural shape (interior run + trailing-boundary-touching run separated by a mergeable gap) but with enough zero-valued baseline pixels (`prof[100:150]=0.02`, `prof[155:480]=0.02`, 105 zeros/21.9%) that the percentile separation check passes and the test genuinely exercises Mechanism A's fix. Verified separation numerically (`base=0.0, peak=0.02`) before finalizing.
- **Files modified:** tests/test_targets.py
- **Verification:** Confirmed RED (fails against unmodified src/targets.py) and GREEN (passes with the fix) directly by temporarily reverting/restoring src/targets.py.
- **Committed in:** a51c57b (Task 1 test commit)

**2. [Rule 1 - Bug] Enlarged the Mechanism-B lone-candidate test fixtures to clear the same separation floor**
- **Found during:** Task 1 RED/GREEN verification
- **Issue:** The plan's suggested tiny lone-candidate length (5 pixels, ~1% of the 480-sample column) also falls below the ~5% threshold needed for the 5th/95th percentile separation check to distinguish baseline from peak, so `halfmax_edges` returned `None` from the separation check rather than the intended far-AND-small history gate -- both the "reject" and "accept" test variants would have passed/failed for the wrong reason.
- **Fix:** Increased the lone-candidate length to 30 pixels (0.116mm) in all three Mechanism-B lone-candidate tests, keeping it comfortably below the `MIN_TRACKED_LENGTH_RATIO * previous_length_mm` (0.4mm) "small" threshold while clearing the percentile separation floor, and preserving clear distance margins for the "far"/"close" conditions.
- **Files modified:** tests/test_targets.py
- **Verification:** Confirmed each of the three tests exercises the intended gate branch by direct numeric computation before finalizing, then via the full test-suite RED/GREEN run.
- **Committed in:** a51c57b (Task 1 test commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 - test fixture bugs discovered during RED-phase verification, not implementation bugs)
**Impact on plan:** Both fixes were necessary to make the regression tests actually exercise the mechanisms they were designed to test, rather than passing/failing for an unrelated reason (insufficient percentile separation). No change to the plan's intended behavior or scope.

## Issues Encountered
None beyond the two test-fixture corrections documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- TARGET-01/TARGET-02 boundary-tracking robustness improved with two regression-tested, zero-new-constant mechanism fixes; both UAT-Test-8-cited crop-edge symptoms resolved.
- Mechanism C's residual tail jitter and the 10-vs-14 width-ordering FLAG (widened, not resolved) remain honestly disclosed open items for the next `/gsd-verify-work` round -- neither blocks this plan's own completion, per its frontmatter's explicit scope boundary.
- Full visual sign-off on the regenerated QA figures is deferred to the next human verification round, consistent with this project's `human_verify_mode: end-of-phase` setting.

---
*Phase: 01-target-extraction-contract*
*Completed: 2026-07-22*

## Self-Check: PASSED

All created/modified files verified present on disk (src/targets.py, tests/test_targets.py, 01-CONTEXT.md, 01-16-ORDERING-OUTCOME.md, 01-16-SUMMARY.md). All task commit hashes (a51c57b, fbc22af, a9dbf7a) verified present in `git log --oneline --all`.
