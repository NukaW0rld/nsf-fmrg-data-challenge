---
phase: 01-target-extraction-contract
plan: 12
subsystem: docs
tags: [requirements-traceability, human-signoff, gap-closure]

# Dependency graph
requires:
  - phase: 01-target-extraction-contract (plan 11)
    provides: "Regenerated per-track valid fractions, ordering verdicts, and check_targets.py output under Amendment A5"
provides:
  - "REQUIREMENTS.md corrected so TARGET-02 no longer contradicts 01-VERIFICATION.md"
  - "01-SIGNOFF-REQUEST.md: an unsigned, actionable handoff naming all 12 QA figures and the exact decisions requested"
affects: [phase-2-planning, gsd-verify-work]

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created:
    - .planning/phases/01-target-extraction-contract/01-SIGNOFF-REQUEST.md
  modified:
    - .planning/REQUIREMENTS.md

key-decisions:
  - "TARGET-02 flipped from [x]/Complete to [ ]/awaiting-human-sign-off; TARGET-01 left unchanged (still Complete) since 01-VERIFICATION.md verified its two truths."
  - "This plan explicitly does not run requirements.mark-complete for TARGET-02 during state_updates — doing so would immediately reverse Task 1's correction and violate the plan's own T-01-30 mitigation (no self-certification)."

patterns-established: []

requirements-completed: [TARGET-01]  # TARGET-02 intentionally NOT marked complete — see "Deviations from Plan" and threat model T-01-30. Sign-off must come from /gsd-verify-work, not this plan.

coverage:
  - id: D1
    description: "REQUIREMENTS.md's TARGET-02 checkbox and traceability row corrected to state 'awaiting human visual sign-off' instead of the false 'Complete', with a dated correction note citing 01-VERIFICATION.md and 01-11-ORDERING-OUTCOME.md"
    requirement: "TARGET-02"
    verification:
      - kind: other
        ref: "grep -q '^- \\[ \\] \\*\\*TARGET-02\\*\\*' .planning/REQUIREMENTS.md && grep -E '^\\| TARGET-02 \\| Phase 1 \\|' .planning/REQUIREMENTS.md | grep -qvi complete"
        status: pass
    human_judgment: false
  - id: D2
    description: "01-SIGNOFF-REQUEST.md handoff document produced, naming all 12 QA figures with acceptance questions, quoting regenerated numbers, presenting the override-vs-investigate choice, with zero pre-ticked checkboxes"
    requirement: "TARGET-02"
    verification:
      - kind: other
        ref: "grep -c 'processed_data/targets/qa/track_' 01-SIGNOFF-REQUEST.md == 12; grep -c '\\[x\\]' == 0; grep -c '\\[ \\]' == 5"
        status: pass
    human_judgment: true
    rationale: "The document's substance (whether the QA figures are actually sane) requires a human to open and visually judge 12 images — verification truth 4 explicitly reserves this for a human, not an automated check."

duration: 2min
completed: 2026-07-21
status: complete
---

# Phase 01 Plan 12: Requirements Correction and Human Sign-Off Handoff Summary

**Corrected REQUIREMENTS.md's false TARGET-02 "Complete" status and produced an unsigned 12-figure sign-off request document, closing the phase's two remaining non-code gaps without self-certifying anything.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-07-21T17:04:27Z
- **Completed:** 2026-07-21T17:05:54Z
- **Tasks:** 2
- **Files modified:** 2 (1 modified, 1 created)

## Accomplishments

- Corrected `.planning/REQUIREMENTS.md`: TARGET-02's checkbox flipped from `[x]` to `[ ]`, its traceability row changed from `Complete` to a factual statement naming the outstanding human visual sign-off and pointing at `01-SIGNOFF-REQUEST.md`, and a dated correction note added beneath the table citing `01-VERIFICATION.md` and `01-11-ORDERING-OUTCOME.md` as the basis. TARGET-01 and the 12/12 coverage counts left untouched.
- Produced `.planning/phases/01-target-extraction-contract/01-SIGNOFF-REQUEST.md`: a single handoff quoting the regenerated per-track summary table, all three ordering verdicts, all four valid fractions against the 50% floor, and `check_targets.py`'s exit code verbatim from `01-11-ORDERING-OUTCOME.md`; naming all 12 QA figures under `processed_data/targets/qa/` with a concrete acceptance question per figure, grouped by type (residual maps, boundary overlays, width curves); re-surfacing the three prior UAT findings (residual curvature, boundary sawtooth, track-10 crop-edge spike) as explicit re-judgment items; and presenting the still-open 10-vs-14 ordering override-vs-investigate choice from `01-08-ORDERING-OUTCOME.md` as two unselected options.

## Task Commits

Each task was committed atomically:

1. **Task 1: Correct the REQUIREMENTS.md record so it stops contradicting the verification** - `3379422` (docs)
2. **Task 2: Produce the human visual sign-off handoff for all 12 regenerated QA figures** - `97e6475` (docs)

**Plan metadata:** committed in this same commit sequence (see below)

## Files Created/Modified

- `.planning/REQUIREMENTS.md` - TARGET-02 checkbox/traceability corrected to name the outstanding human sign-off; TARGET-01 unchanged
- `.planning/phases/01-target-extraction-contract/01-SIGNOFF-REQUEST.md` - New unsigned handoff document naming all 12 QA figures, the current regenerated numbers, the constants and their a-priori basis, and the decisions requested

## Decisions Made

- TARGET-02's traceability status was written as a specific, factual state ("Awaiting human visual sign-off on regenerated QA figures — see `01-SIGNOFF-REQUEST.md`") rather than a generic "Blocked" or "Pending", per the plan's must_haves requirement that the row "names the specific outstanding condition."
- The override-vs-investigate decision checkbox in `01-SIGNOFF-REQUEST.md` was scoped with an explicit caveat that it applies only while the 10-vs-14 ordering pair FLAGs, so it does not become stale/misleading if a future regeneration clears the FLAG.
- Elected not to run `gsd-tools query requirements.mark-complete` for TARGET-02 during the state_updates step (see Deviations below) — running it would tick the checkbox this plan just corrected to `[ ]`, directly reversing Task 1's work and violating the plan's own prohibition against self-certifying sign-off (threat T-01-30).

## Deviations from Plan

None in the two tasks themselves - both executed exactly as written and both automated `<verify>` blocks passed on the first attempt.

One deliberate departure from the generic executor `state_updates` step, which is not a deviation from *this plan* but a necessary adherence to it:

**1. [Plan-mandated, not a Rule 1-4 deviation] Skipped `requirements.mark-complete` for TARGET-02**
- **Context:** The generic execute-plan workflow instructs the executor to run `requirements mark-complete` for every requirement ID in the plan's frontmatter (`requirements: [TARGET-01, TARGET-02]`) after each plan completes.
- **Conflict:** This plan's entire Task 1 deliverable is to correct TARGET-02 from a false `[x]`/Complete to an honest `[ ]`/awaiting-sign-off. Running the generic mark-complete step for TARGET-02 would immediately re-tick it, erasing Task 1's committed correction in the very same plan execution and self-certifying the one gate (`T-01-30` in this plan's own threat model) that must come from a human via `/gsd-verify-work`.
- **Resolution:** `requirements.mark-complete` was not invoked for TARGET-02. TARGET-01 is listed in `requirements-completed` frontmatter above for traceability continuity (it was already `[x]`/Complete before this plan and remains so, unaffected by this plan's changes) but was likewise not re-run through mark-complete since it needed no change.
- **Files affected:** None beyond the two task commits already made.
- **Verification:** `grep -q "^- \[ \] \*\*TARGET-02\*\*" .planning/REQUIREMENTS.md` after both task commits confirms the checkbox remains unticked.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Phase 1 is NOT complete.** This plan closed the two non-code gaps it targeted (requirements-record honesty, and producing the sign-off handoff), but the phase's actual completion gate — a human opening the 12 figures listed in `01-SIGNOFF-REQUEST.md` and recording a decision via `/gsd-verify-work` — has not occurred and cannot be performed by this executor.

**Outstanding before Phase 2 begins:**
1. A human must open all 12 QA figures under `processed_data/targets/qa/` and answer the questions in `01-SIGNOFF-REQUEST.md`'s "Decisions requested" section, recording the outcome via `/gsd-verify-work` (not by editing `01-SIGNOFF-REQUEST.md` or `REQUIREMENTS.md` directly).
2. Because the 10-vs-14 width-ordering pair still FLAGs (track 10 median 0.3713mm < track 14 median 0.4765mm per `01-11-ORDERING-OUTCOME.md`), the reviewer must also make the override-vs-further-investigation choice from `01-08-ORDERING-OUTCOME.md` — either accept the FLAG as a documented limitation and proceed, or commission a new gap-closure plan.
3. Only after that human record exists does `TARGET-02`'s checkbox/traceability row in `REQUIREMENTS.md` flip to complete, and only then can Phase 1 be considered closed for Phase 2 planning to safely consume `processed_data/targets/` as ground truth.

## Self-Check

FOUND: .planning/REQUIREMENTS.md
FOUND: .planning/phases/01-target-extraction-contract/01-SIGNOFF-REQUEST.md
FOUND commit: 3379422
FOUND commit: 97e6475

## Self-Check: PASSED

---
*Phase: 01-target-extraction-contract*
*Completed: 2026-07-21*
