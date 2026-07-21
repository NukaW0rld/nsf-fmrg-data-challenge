---
phase: 01-target-extraction-contract
plan: 11
subsystem: data
tags: [numpy, scipy-lstsq, detrend, wyko-height-maps, provenance]

# Dependency graph
requires:
  - phase: 01-target-extraction-contract
    provides: "Amendment A4 bead-masked order-4 detrend (plan 01-07), the MIN_VALID_FRACTION=0.5 coverage gate (plan 01-10)"
provides:
  - "Track 10's coverage collapse (21/400, 5.2%) diagnosed as a detrend-fitting artifact and fixed to 242/400 (60.5%)"
  - "robust_plane_detrend max_y_degree keyword and src/targets.py's DETREND_MAX_Y_DEGREE=2 (Amendment A5)"
  - "A committed, re-runnable diagnostic (scripts/diagnose_track10_coverage.py) for future cross-track coverage investigations"
affects: [phase-02-alignment, phase-01-12-human-signoff]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pre-registered fix-selection criterion committed to git before any extraction-source change, with a documented fallback provision that let Task 3 pivot to a second candidate mechanism when the first was falsified by a priori measurement rather than by outcome"

key-files:
  created:
    - scripts/diagnose_track10_coverage.py
    - processed_data/diagnostics/track10_coverage_diagnosis.csv
    - .planning/phases/01-target-extraction-contract/01-11-DIAGNOSIS.md
    - .planning/phases/01-target-extraction-contract/01-11-CRITERION.md
    - .planning/phases/01-target-extraction-contract/01-11-ORDERING-OUTCOME.md
  modified:
    - src/nsf_fmrg_data.py
    - src/targets.py
    - scripts/check_targets.py
    - tests/test_nsf_fmrg_data.py
    - tests/test_targets.py
    - .planning/phases/01-target-extraction-contract/01-CONTEXT.md

key-decisions:
  - "Track 10's raw row-median argmax is interior (y-index 380/480, not edge-adjacent) — the post-detrend edge-touching residual is a detrend-fitting artifact, recoverable by a uniform change, not a physically truncated bead."
  - "01-11-CRITERION.md pre-registered a 0.05mm fitted-surface edge-vs-midpoint tolerance and two candidate mechanisms (basis conditioning, per-axis degree cap) before any source change existed."
  - "Candidate A (DETREND_NORMALIZE_BASIS, basis conditioning) was rejected by a priori measurement: rescaling monomial columns cannot change a full-rank least-squares fit's predicted surface, only the conditioning of solving for its coefficients — confirmed numerically bit-identical against real track data."
  - "Candidate B (DETREND_MAX_Y_DEGREE=2) selected per the criterion's own fallback provision: the largest cross-track degree cap that clears the 0.05mm tolerance on all four tracks (cap 3 leaves one track at 0.0665mm; cap 2 brings every track's worst departure to 0.0238mm)."
  - "The 10-vs-14 width-ordering FLAG is a separate, unaddressed question from the coverage-collapse defect this plan targeted — reported honestly in 01-11-ORDERING-OUTCOME.md without tuning any constant, and left open for plan 01-12's human sign-off."

requirements-completed: [TARGET-01, TARGET-02]

coverage:
  - id: D1
    description: "Track 10's coverage collapse is characterized by committed, re-runnable diagnostic code (scripts/diagnose_track10_coverage.py) reproducing the exact per-bin rejection histogram, without computing any width/ordering outcome"
    requirement: TARGET-01
    verification:
      - kind: unit
        ref: "scripts/diagnose_track10_coverage.py run against real data#reproduces {'no_columns':0,'gap_fail':112,'no_baseline_sep':0,'clipped_run_only':267,'ok':21} for track 10"
        status: pass
    human_judgment: false
  - id: D2
    description: "Outcome-independent fix-selection criterion (01-11-CRITERION.md) committed to git strictly before any change exists in src/targets.py or src/nsf_fmrg_data.py"
    requirement: TARGET-01
    verification:
      - kind: unit
        ref: "git log --oneline -- 01-11-CRITERION.md precedes the src/targets.py change commit; git diff HEAD --stat on both files empty at that commit"
        status: pass
    human_judgment: false
  - id: D3
    description: "Exactly one uniform, track-independent detrend fix (DETREND_MAX_Y_DEGREE) applied, provenance-locked in extraction_params() (16 keys), and canonicalized as Amendment A5"
    requirement: TARGET-02
    verification:
      - kind: unit
        ref: "tests/test_targets.py#test_extraction_params_provenance, test_provenance_digest_is_change_sensitive, test_single_parameterization_has_no_track_conditionals"
        status: pass
      - kind: unit
        ref: "tests/test_nsf_fmrg_data.py#test_detrend_does_not_diverge_at_strip_edge, test_detrend_edge_fix_preserves_default_behavior, test_polynomial_basis_sizes_are_stable"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_edge_divergence_fix_is_track_independent"
        status: pass
    human_judgment: false
  - id: D4
    description: "All four tracks regenerated atomically in one run_target_extraction.py invocation; track 10 clears the 50% MIN_VALID_FRACTION floor (242/400, 60.5%); ordering outcome reported honestly with no constant changed"
    requirement: TARGET-02
    verification:
      - kind: integration
        ref: "scripts/check_targets.py --project_dir . (exit 0, ALL CHECKS PASSED); 01-11-ORDERING-OUTCOME.md"
        status: pass
    human_judgment: true
    rationale: "The 10-vs-14 width-ordering FLAG remains unresolved and requires a human decision (override vs. further investigation) per plan 01-12's escalation handoff — this plan resolved coverage, not ordering."

# Metrics
duration: 45min
completed: 2026-07-21
status: complete
---

# Phase 1 Plan 11: Track 10 Coverage-Collapse Diagnosis and Fix Summary

**Diagnosed track 10's 5.2%-valid-fraction collapse as a Runge-type edge divergence in the shared order-4-in-y detrend basis, and fixed it with a pre-registered, criterion-selected `DETREND_MAX_Y_DEGREE=2` cap (Amendment A5), restoring track 10 to 60.5% valid coverage without tuning to the still-unresolved 8>10>14>21 width ordering.**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-07-21 (context loading + Task 1 diagnosis)
- **Completed:** 2026-07-21T16:59Z
- **Tasks:** 4 completed
- **Files modified:** 11 (5 new, 6 modified)

## Accomplishments

- Built `scripts/diagnose_track10_coverage.py`, a committed, re-runnable diagnostic reproducing the exact per-bin rejection histogram from `01-REVIEW.md` CR-01 for all four tracks under one uniform code path, with a hard constraint (verified by grep) against computing any width/ordering outcome.
- Established, on measured evidence, that track 10's bead is interior in the raw data (not physically truncated) and that the production detrend's fitted background surface manufactures a large edge divergence — a fitting artifact, recoverable by a uniform change.
- Pre-registered `01-11-CRITERION.md` (a 0.05mm fitted-surface edge-vs-midpoint tolerance, two candidate mechanisms with named rejection evidence, a non-recoverable branch, and a tie-break rule) and committed it before any extraction-source change existed.
- Implemented `robust_plane_detrend`'s `max_y_degree` keyword and locked `DETREND_MAX_Y_DEGREE=2` in `src/targets.py`, selected via the criterion's own pre-registered fallback after Candidate A (basis conditioning) was measured to be mathematically incapable of changing a full-rank least-squares fit.
- Regenerated all four tracks atomically; track 10's valid-bin count rose from 21/400 (5.2%) to 242/400 (60.5%), clearing the `MIN_VALID_FRACTION` floor plan 01-10 installed — `check_targets.py` now exits 0.
- Reported the 8>10>14>21 ordering outcome honestly: still FLAGs on the 10-vs-14 pair (0.3713mm vs 0.4765mm), narrower than before but not crossed, with no constant changed in response.

## Task Commits

Each task was committed atomically:

1. **Task 1: Diagnose track 10's coverage collapse** — `c0ef888` (feat)
2. **Task 2: Pre-register the fix-selection criterion** — `ee3511f` (docs)
3. **Task 3: Apply the uniform fix and record Amendment A5** — TDD: `0856db9` (test, RED) → `428af20` (feat, GREEN)
4. **Task 4: Regenerate and report the outcome** — `c9b066a` (docs)

**Plan metadata:** (this commit)

## Files Created/Modified

- `scripts/diagnose_track10_coverage.py` - Committed diagnostic reproducing raw substrate profile, production residual profile, fitted-surface edge report, per-bin rejection histogram, and design-matrix conditioning for all four tracks
- `processed_data/diagnostics/track10_coverage_diagnosis.csv` - Evidence CSV, sibling of `processed_data/targets/` so `publish_staging_dir` cannot destroy it
- `.planning/phases/01-target-extraction-contract/01-11-DIAGNOSIS.md` - Root-cause reading: track 10's bead is interior, edge divergence is a fitting artifact
- `.planning/phases/01-target-extraction-contract/01-11-CRITERION.md` - Pre-registered, outcome-independent fix-selection criterion
- `.planning/phases/01-target-extraction-contract/01-11-ORDERING-OUTCOME.md` - Honest regeneration and ordering-outcome report
- `src/nsf_fmrg_data.py` - `robust_plane_detrend` gains `max_y_degree=None` keyword (bit-for-bit unchanged default); IN-01 derivation comment on `EXTRACTED_THERMAL_FRAMES`
- `src/targets.py` - `DETREND_MAX_Y_DEGREE=2` constant, threaded into `extract_track_targets`, added to `extraction_params()` (16 keys)
- `scripts/check_targets.py` - IN-01 derivation comment on `Y_STRIP_EXTENT_MM`
- `tests/test_nsf_fmrg_data.py` - `test_detrend_does_not_diverge_at_strip_edge`, `test_detrend_edge_fix_preserves_default_behavior`, extended `test_polynomial_basis_sizes_are_stable`
- `tests/test_targets.py` - `test_edge_divergence_fix_is_track_independent`, updated `test_extraction_params_provenance` / `test_provenance_digest_is_change_sensitive`
- `.planning/phases/01-target-extraction-contract/01-CONTEXT.md` - Amendment A5

## Decisions Made

- Track 10's raw row-median argmax sits at y-index 380/480 (79% across the strip, not edge-adjacent) — this rules out the physical-truncation reading and establishes the recoverable/fitting-artifact reading on measured evidence, per the plan's `must_haves` requirement to not force either conclusion.
- The pre-registered criterion (0.05mm fitted-surface edge-vs-midpoint tolerance) was derived from Task 1's own measurements: the three healthy tracks show departures of 0.0002-0.0057mm while track 10 shows 0.0592-0.1226mm — a tolerance with margin on both sides of the two populations, not tuned to a single number.
- Candidate A (basis conditioning / `DETREND_NORMALIZE_BASIS`) was implemented and tested against real track data during investigation and found to produce bit-identical fitted surfaces to the unscaled basis (max abs diff ~1.3e-11mm) — a mathematical consequence of least-squares scale-invariance for full-rank fits, not an implementation bug. This is a priori, falsifiable evidence under the criterion's own Section 4, not an outcome (width/ordering) observation, so using it to move to Candidate B does not violate the no-outcome-driven-tuning prohibition.
- `DETREND_MAX_Y_DEGREE=2` was chosen as the *largest* cap that clears the criterion on all four tracks (cap 3 fails on track 10 at 0.0665mm), preserving maximal cross-track fitting capacity rather than picking the smallest cap that happens to work.
- The 10-vs-14 width-ordering FLAG was left unresolved and unaddressed by design — the plan's own `must_haves` and `prohibitions` scope this plan to the coverage-collapse defect only; the ordering criterion itself is plan 01-12's human-decision item.

## Deviations from Plan

**1. [Criterion's own fallback provision, not a Rule 1-4 deviation] Pivoted from Candidate A to Candidate B during Task 3**

`01-11-CRITERION.md` (committed in Task 2) named two candidates and an explicit fallback: "If Task 3's implementation reveals Candidate A does not clear Section 4's rejection evidence, Task 3 falls back to Candidate B under this same document's Section 3/4 terms rather than inventing a new mechanism." During Task 3's implementation, Candidate A (`DETREND_NORMALIZE_BASIS`) was measured against real track data and found to be a mathematical no-op — column rescaling cannot change a full-rank least-squares fit's predicted surface. This falsification is itself a priori/numerical evidence (not a width, valid-fraction, or ordering observation), so invoking the pre-registered fallback and implementing Candidate B instead is the criterion's own contingency operating as designed, not a deviation requiring a new decision. Documented for transparency since it changed which constant ultimately shipped (`DETREND_MAX_Y_DEGREE` instead of `DETREND_NORMALIZE_BASIS`), matching what `01-11-CRITERION.md` itself already anticipated and authorized before any source change existed.
- **Found during:** Task 3 implementation/investigation, before any test or source commit
- **Resolution:** Implemented `DETREND_MAX_Y_DEGREE=2` per the criterion's Section 4/6 fallback; recorded in Amendment A5 and in `01-11-CRITERION.md`'s own text (which already named this exact contingency)
- **Committed in:** `428af20`

---

**Total deviations:** 0 Rule 1-4 auto-fixes; 1 criterion-anticipated fallback exercised as designed.
**Impact on plan:** None outside the plan's own scope — the pre-registered criterion's fallback mechanism is precisely what prevented this pivot from being outcome-driven tuning.

## Issues Encountered

- Constructing a synthetic regression scenario that reliably reproduces the real track-10 mechanism (an uncapped order-4-in-y fit manufacturing an edge divergence under masked, strided real data) required iterative empirical tuning of a synthetic "near-edge shelf" feature's amplitude/extent — pure noise or a purely-polynomial synthetic substrate did not reproduce the effect, since least-squares fits are insensitive to column scaling and exactly-representable data has no fitting error to manufacture. Resolved by explicitly measuring candidate synthetic parameters against the criterion's own tolerance before finalizing the test code (see `tests/test_nsf_fmrg_data.py::_track10_shaped_edge_scenario`).
- `tests/test_targets.py::test_edge_divergence_fix_is_track_independent` initially used `targets.bead_exclusion_mask` for masking, which also excluded the deliberately-planted near-edge shelf feature (since it's per-column-percentile-relative, not location-aware), hiding the divergence the test exists to exercise. Fixed by using an explicit bead-only mask (matching the `test_nsf_fmrg_data.py` scenario) while still exercising the production `targets.DETREND_POLY_ORDER` / `targets.DETREND_MAX_Y_DEGREE` constants.

## Next Phase Readiness

- All four track conditions (8, 10, 14, 21) now produce usable (>50% valid) target artifacts under one shared parameterization — restoring track 10's eligibility for Phase 3's mandatory leave-one-track-out cross-validation.
- The 10-vs-14 width-ordering FLAG remains open and blocks Phase 1's final human verification sign-off pending plan 01-12's human decision, per `01-11-ORDERING-OUTCOME.md`'s escalation.

---
*Phase: 01-target-extraction-contract*
*Completed: 2026-07-21*
