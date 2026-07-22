---
phase: 01-target-extraction-contract
plan: 14
subsystem: data
tags: [profilometry, boundary-tracking, numpy, tdd]

# Dependency graph
requires:
  - phase: 01-target-extraction-contract
    provides: Amendment A6 (DETREND_MAX_XY_DEGREE=2, plan 01-13) and the confirmed root cause in .planning/debug/boundary-fragmentation-post-continuity-fix.md (self-reinforcing wrong-lock mechanism in halfmax_edges' tracked selection)
provides:
  - "merge_adjacent_runs(runs, max_gap): merges noise-fragmented above-half-max sub-runs before D-01/D-03 clip-exclusion and candidate selection"
  - "halfmax_edges' tracked-selection branch gated by MIN_TRACKED_LENGTH_RATIO relative to the largest same-column candidate before nearest-to-previous_center tie-break"
  - "MAX_RUN_MERGE_GAP_PIXELS=MAX_GAP_PIXELS and MIN_TRACKED_LENGTH_RATIO=HALF_MAX_FRACTION (Amendment A7), both reused from already-locked constants"
  - "01-14-ORDERING-OUTCOME.md: honest, quantified fragmentation/jump-statistic before/after comparison and 10-vs-14 ordering outcome under the regenerated 4-track pipeline"
affects: [phase-1-verification-signoff]

# Tech tracking
tech-stack:
  added: []
  patterns: ["task-level RED/GREEN TDD for a single non-tdd-typed src fix (mirrors 01-05/01-13's discipline)"]

key-files:
  created:
    - .planning/phases/01-target-extraction-contract/01-14-ORDERING-OUTCOME.md
  modified:
    - src/targets.py
    - tests/test_targets.py
    - .planning/phases/01-target-extraction-contract/01-CONTEXT.md

key-decisions:
  - "MAX_RUN_MERGE_GAP_PIXELS = MAX_GAP_PIXELS (10) and MIN_TRACKED_LENGTH_RATIO = HALF_MAX_FRACTION (0.5) both reuse already-locked contract values for the same underlying judgment, fixed before any regeneration -- neither was chosen from the resulting fragmentation count or width ordering."
  - "merge_adjacent_runs is applied to all_true_runs' output BEFORE the D-01/D-03 boundary-clip exclusion filter, so a merged run that now spans to a boundary is correctly excluded exactly as an originally-clipped run would be."
  - "extract_targets_from_arrays' previous_center update was left unchanged: because halfmax_edges now never returns an implausibly-small tracked candidate, the existing unconditional anchor update always advances to a plausible location by construction -- no redundant second check was added."
  - "The DP/Viterbi joint sequence tracker the diagnosis also named was considered and explicitly deferred (not silently dropped): the diagnosis itself states it is 'not required to implement, if scope is too large,' and the project's 8-day runway does not justify it when the two adopted mechanisms fully address both traced failure mechanisms."
  - "Regenerated all 4 tracks in one atomic run and reported the fragmentation/jump-statistic before/after comparison honestly: the outcome is MIXED, not a uniform improvement -- contiguous-run counts worsened on tracks 8/10/21 and only marginally improved on track 14; jump statistics improved on some boundaries (notably track 10's near-continuous post-70mm collapse is resolved) but worsened on others (notably track 8's both boundaries roughly doubled). No constant was changed in response."

requirements-completed: [TARGET-01, TARGET-02]

coverage:
  - id: D1
    description: "merge_adjacent_runs helper and plausibility-gated halfmax_edges/extract_targets_from_arrays directly close the diagnosed TRIGGER (noise-fragmented true beads split into competing tiny candidates) and PROPAGATION (implausibly-small candidates winning tracked selection, corrupting the anchor) mechanisms, verified against the exact diagnosed Track 8 and Track 10 episodes; D-01/D-03 and 01-05's original ambiguous-candidate tie-break behavior are fully preserved; no per-track branch introduced"
    requirement: "TARGET-01"
    verification:
      - kind: unit
        ref: "tests/test_targets.py#test_merge_adjacent_runs_bridges_short_below_threshold_gaps"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_merge_adjacent_runs_does_not_bridge_large_gaps"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_halfmax_edges_rejects_implausibly_narrow_tracked_candidate"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_merged_run_touching_boundary_remains_excluded"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_extract_targets_from_arrays_recovers_from_track8_style_propagating_wrong_lock"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_extract_targets_from_arrays_merges_track10_style_fragmented_bead"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_extraction_params_provenance"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_provenance_digest_is_change_sensitive"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_single_parameterization_has_no_track_conditionals"
        status: pass
    human_judgment: false
  - id: D2
    description: "All 4 tracks regenerated atomically under Amendment A7; check_targets.py exits 0 (ALL CHECKS PASSED); fragmentation-count and jump-statistic before/after comparison against the diagnosed pre-fix numbers is reported honestly (MIXED outcome, not uniform improvement); track 10's valid fraction dropped to a razor-thin 50.50% margin above the 50% floor; 10-vs-14 width-ordering FLAG persists with substantially reshaped median widths"
    requirement: "TARGET-02"
    verification:
      - kind: integration
        ref: "scripts/run_target_extraction.py --project_dir . && scripts/check_targets.py --project_dir . (exit 0, ALL CHECKS PASSED)"
        status: pass
    human_judgment: true
    rationale: "Whether the mixed fragmentation/jump-statistic outcome, track 10's razor-thin 50.50% coverage margin, and the persisting (reshaped) 10-vs-14 ordering FLAG are acceptable for Phase 1 sign-off are domain/scientific judgment calls for the human verification round (/gsd-verify-work), not something an automated test can certify."

# Metrics
duration: 15min
completed: 2026-07-22
status: complete
---

# Phase 1 Plan 14: Boundary-Fragmentation Merge and Plausibility Gate (G-01-5) Summary

**Merged noise-fragmented half-max runs and gated tracked-candidate selection by length plausibility (Amendment A7), fixing the diagnosed self-reinforcing wrong-lock mechanism in isolation, but the real 4-track fragmentation/jump-statistic metrics show a mixed, not uniformly improved, outcome.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-07-22T03:19:00Z
- **Completed:** 2026-07-22T03:34:14Z
- **Tasks:** 2 completed
- **Files modified:** 4 (1 created, 3 modified; excludes gitignored `processed_data/targets/` regenerated artifacts)

## Accomplishments
- Diagnosed defect (`.planning/debug/boundary-fragmentation-post-continuity-fix.md`): `halfmax_edges`' tracked-selection rule had no maximum-distance gate or effective size/plausibility weighting, and `extract_targets_from_arrays` unconditionally advanced `previous_center` regardless of plausibility -- together producing a multi-column self-reinforcing wrong lock, directly traced on Track 8 (8-column/1.4mm episode) and Track 10 (near-continuous narrow lock from x~68mm through beyond x~82mm).
- Added `merge_adjacent_runs(runs, max_gap)`, applied to `all_true_runs`' output BEFORE the D-01/D-03 boundary-clip exclusion filter, so noise-fragmented true beads are treated as one candidate rather than several competing tiny ones -- fixing the TRIGGER.
- Gated `halfmax_edges`' tracked-selection branch to candidates at least `MIN_TRACKED_LENGTH_RATIO` of the largest same-column candidate's length before the nearest-to-`previous_center` tie-break -- fixing the PROPAGATION, since a length-1-pixel noise spike can no longer out-rank a length-hundreds true bead purely by midpoint proximity.
- Both new constants (`MAX_RUN_MERGE_GAP_PIXELS=MAX_GAP_PIXELS=10`, `MIN_TRACKED_LENGTH_RATIO=HALF_MAX_FRACTION=0.5`) reuse already-locked contract values, recorded as Amendment A7 in `01-CONTEXT.md`, including an explicit deferral rationale for the diagnosis's optional DP/Viterbi joint-tracker direction.
- Regenerated all 4 tracks atomically under Amendment A7 and reported the fragmentation/jump-statistic before/after comparison and the 10-vs-14 ordering outcome honestly in `01-14-ORDERING-OUTCOME.md`: the two specific diagnosed mechanisms are directly regression-tested and fixed (confirmed via targeted synthetic reproductions of the exact Track 8/Track 10 episodes), but the real-data aggregate metrics are MIXED -- contiguous-run counts worsened on 3 of 4 tracks, jump statistics improved on some boundaries and worsened on others, and track 10's valid-fraction margin above the 50% floor narrowed materially (60.75% -> 50.50%).

## Task Commits

Each task was committed atomically:

1. **Task 1: Merge fragmented candidates and gate tracked selection by length plausibility (G-01-5)** - `442ec07` (test, RED) then `265982a` (fix, GREEN)
2. **Task 2: Regenerate all 4 tracks, report the fragmentation/jump-statistic improvement, and honestly report the ordering outcome** - `7392105` (docs) then `db06876` (docs, visual QA addendum)

**Plan metadata:** committed after this summary (see final metadata commit).

## Files Created/Modified
- `src/targets.py` - Adds `merge_adjacent_runs`, plausibility-gated `halfmax_edges` tracked-selection branch, `MAX_RUN_MERGE_GAP_PIXELS`/`MIN_TRACKED_LENGTH_RATIO` constants, extends `extraction_params()` to 19 keys
- `tests/test_targets.py` - Adds 6 new regressions (merge bridging/non-bridging, plausibility rejection, boundary-clip preservation under merge, Track 8/Track 10 diagnosed-episode reproductions); bumps provenance/digest tests to the 19-key set
- `.planning/phases/01-target-extraction-contract/01-CONTEXT.md` - Records Amendment A7
- `.planning/phases/01-target-extraction-contract/01-14-ORDERING-OUTCOME.md` - Honest regeneration, fragmentation/jump-statistic, coverage, and ordering-outcome report, plus visual QA confirmation

## Decisions Made
- `MAX_RUN_MERGE_GAP_PIXELS = MAX_GAP_PIXELS` and `MIN_TRACKED_LENGTH_RATIO = HALF_MAX_FRACTION` -- both reused from already-locked constants for the same underlying judgment (D-05/D-06's short-gap tolerance; D-01/D-03's half-max convention), fixed before any regeneration, mirroring Amendment A4/A5/A6's discipline.
- Merging happens before clip-exclusion so a merged run spanning to a boundary is correctly excluded -- verified directly by `test_merged_run_touching_boundary_remains_excluded`.
- `extract_targets_from_arrays`'s unconditional `previous_center` update was left unchanged: since `halfmax_edges` now never returns an implausible tracked candidate, the existing update always advances to a plausible location by construction, avoiding a redundant second gate.
- The diagnosis's optional DP/Viterbi joint-tracker direction was considered and explicitly deferred (not silently dropped), per its own stated "not required... if scope is too large" language and the project's 8-day runway.
- Regenerated exactly once and reported the fragmentation/jump-statistic outcome honestly, including the caveat that the pre-fix baseline numbers (22/65/63/34 valid runs) were measured under Amendment A5, before Amendment A6 changed every track's detrended surface -- disclosed rather than silently used as an apples-to-apples comparison.
- No locked constant was adjusted in response to the mixed fragmentation/jump-statistic outcome, the persisting 10-vs-14 FLAG, or track 10's narrowed coverage margin.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Own-test synthetic decoy length insufficient for peak-baseline separation check**
- **Found during:** Task 1, while confirming `test_extract_targets_from_arrays_recovers_from_track8_style_propagating_wrong_lock` reproduces the pre-fix wrong lock with the gate disabled
- **Issue:** The initially-written synthetic `tiny_decoy` profile (20/480 samples above threshold) fell below the 5th/95th-percentile baseline/peak split needed to clear `MIN_PEAK_BASELINE_SEPARATION_MM` on its own (a 4.2% count doesn't lift the 95th percentile off the zero baseline), so `halfmax_edges` returned `None` for the trigger column instead of selecting the tiny candidate -- silently failing to reproduce the diagnosed scenario at all.
- **Fix:** Widened the decoy to 30/480 samples (indices 10:40), which clears the percentile-based separation check while remaining far below `MIN_TRACKED_LENGTH_RATIO * max_len` (30 vs. required >=100), preserving the test's intent.
- **Files modified:** `tests/test_targets.py`
- **Commit:** `265982a` (part of the GREEN implementation commit, since this was a self-test correction discovered while verifying the fix, not a src defect)

---

**Total deviations:** 1 auto-fixed (Rule 1, own-test bug in newly-authored synthetic scenario).
**Impact on plan:** No scope creep; the fix corrected a test-construction error so the regression actually exercises the diagnosed scenario, matching the plan's own intent.

## Issues Encountered
None beyond the auto-fixed test-construction issue above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The two mechanisms the diagnosis (`.planning/debug/boundary-fragmentation-post-continuity-fix.md`) identified for G-01-5 are directly closed and regression-tested against the exact Track 8 and Track 10 episodes.
- The real 4-track regeneration's fragmentation/jump-statistic outcome is MIXED, not a uniform improvement (worsened contiguous-run counts on 3 of 4 tracks; jump statistics improved on some boundaries, worsened on others). `01-14-ORDERING-OUTCOME.md` reports this honestly, including that track 10's valid-fraction margin above the `MIN_VALID_FRACTION=0.5` floor narrowed to a razor-thin 50.50% (still passing, not silently proceeding past a floor breach since none occurred).
- The 10-vs-14 width-ordering FLAG persists, with substantially reshaped median widths across all four tracks (largest shifts on tracks 14 and 21, consistent with their diagnosed wrong-narrow-pick rates of 34.3%/43.1%).
- These outcomes -- the mixed fragmentation result, the narrowed track 10 coverage margin, and the persisting/reshaped 10-vs-14 FLAG -- are all presented for the next human verification round (`/gsd-verify-work 1`) to evaluate, since they involve domain/scientific judgment this plan's own scope does not authorize resolving via further tuning.

---
*Phase: 01-target-extraction-contract*
*Completed: 2026-07-22*

## Self-Check: PASSED

All 5 key files found on disk; all 4 task commit hashes (`442ec07`, `265982a`, `7392105`, `db06876`) found in git history.
