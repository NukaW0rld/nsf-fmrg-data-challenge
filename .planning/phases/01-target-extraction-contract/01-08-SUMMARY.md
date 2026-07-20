---
phase: 01-target-extraction-contract
plan: 08
subsystem: data-processing
tags: [profilometry, provenance, regeneration, honest-reporting, numpy]

requires:
  - phase: 01-target-extraction-contract
    provides: Amendment A4's bead-mask detrend fix and complete extraction_params() provenance (plan 01-07)
provides:
  - "A regenerated, provenance-complete processed_data/targets/ tree (four NPZs, extraction_params.json, manifest.json, 12 qa/*.png) produced by one atomic staged run of the Amendment A4 extraction path"
  - "scripts/check_targets.py ALL CHECKS PASSED confirmation (normal and -O) with matching persisted-params/manifest-digest provenance and a clean data/raw/ integrity audit"
  - "01-08-ORDERING-OUTCOME.md: the honest, non-tuned 8>10>14>21 ordering outcome (NOT restored — 10-vs-14 FLAGs) with an escalation for a separate human-override decision"
affects: [target-extraction, dataset-alignment, phase-1-verification-signoff, model-training]

tech-stack:
  added: []
  patterns: [honest-outcome-guard reporting without parameter tuning, atomic staged regeneration as the only publication path]

key-files:
  created: [.planning/phases/01-target-extraction-contract/01-08-ORDERING-OUTCOME.md]
  modified: []

key-decisions:
  - "Regenerated all four artifacts via the single staged run (scripts/run_target_extraction.py) exactly once; no per-track invocation, no hand-editing of generated artifacts."
  - "The 8>10>14>21 ordering is NOT restored under the corrected Amendment A4 extraction: 8-vs-10 and 14-vs-21 pass, but 10-vs-14 FLAGs (track 10 median 0.2509mm < track 14 median 0.5264mm)."
  - "No extraction parameter was changed in response to this outcome — git diff on src/targets.py remained empty throughout Task 2."
  - "Escalated the unresolved ordering to a separate human decision (override the criterion vs. diagnose track 10's valid-fraction collapse as a new defect) rather than tuning any constant."

patterns-established:
  - "Honest-outcome reporting: an ordering/acceptance criterion is checked and reported as a fact from a correctly-executed pipeline, never adjusted by re-tuning parameters to make the report look better."

requirements-completed: [TARGET-01, TARGET-02]

coverage:
  - id: D1
    description: "All four target NPZs, extraction_params.json, manifest.json, and 12 QA PNGs are regenerated in one atomic staged run carrying Amendment A4's complete, change-sensitive provenance."
    requirement: TARGET-01
    verification:
      - kind: other
        ref: ".venv/bin/python scripts/run_target_extraction.py --project_dir . (prints data/raw/ integrity PASS; publishes 4 NPZs + extraction_params.json + manifest.json + 12 qa/*.png)"
        status: pass
    human_judgment: false
  - id: D2
    description: "scripts/check_targets.py confirms persisted params equal extraction_params(), the manifest SHA-256 matches, and every track passes the float64/NaN-mask/strict-ordering/positive-width structural contract, normally and under python -O."
    requirement: TARGET-01
    verification:
      - kind: other
        ref: ".venv/bin/python scripts/check_targets.py --project_dir . -> ALL CHECKS PASSED"
        status: pass
      - kind: other
        ref: ".venv/bin/python -O scripts/check_targets.py --project_dir . -> ALL CHECKS PASSED"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py (26/26 PASS)"
        status: pass
      - kind: unit
        ref: "tests/test_nsf_fmrg_data.py (5/5 PASS)"
        status: pass
    human_judgment: false
  - id: D3
    description: "data/raw/ integrity audit passes: the regeneration created, modified, and deleted zero files under data/raw/."
    requirement: TARGET-01
    verification:
      - kind: other
        ref: "git status --porcelain -- data/raw (empty) + run_target_extraction.py's own snapshot_raw before/after audit printing PASS"
        status: pass
    human_judgment: false
  - id: D4
    description: "The 8>10>14>21 width ordering is re-checked and reported as an honest outcome of the corrected uniform extraction (not forced); since it is NOT restored, execution stopped and escalated for a separate human-override decision with zero extraction-parameter changes."
    requirement: TARGET-02
    verification:
      - kind: manual_procedural
        ref: ".planning/phases/01-target-extraction-contract/01-08-ORDERING-OUTCOME.md"
        status: pass
    human_judgment: true
    rationale: "Deciding between a documented human override of the ordering criterion and diagnosing a new defect (track 10's valid-fraction collapse to 5.2%) is a scientific-integrity judgment call this plan explicitly reserves for a human, not something an automated check can resolve."

duration: 8min
completed: 2026-07-20
status: complete
---

# Phase 01 Plan 08: Regeneration and Honest Ordering-Outcome Report Summary

**Regenerated the full provenance-complete processed_data/targets/ tree via the Amendment A4 bead-mask extraction path; the 8>10>14>21 width ordering is NOT restored (10-vs-14 FLAGs), reported honestly with zero parameter tuning and escalated for a separate human decision.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-07-20T21:32:00Z (approx.)
- **Completed:** 2026-07-20T21:40:00Z (approx.)
- **Tasks:** 2
- **Files modified:** 1 tracked (`01-08-ORDERING-OUTCOME.md`); 18 gitignored runtime artifacts regenerated under `processed_data/targets/` (not committed — see Deviations)

## Accomplishments

- Ran `.venv/bin/python scripts/run_target_extraction.py --project_dir .` once: printed `data/raw/ integrity PASS: no files created, modified, or deleted.` and atomically published a fresh `processed_data/targets/` tree — four NPZs, `extraction_params.json`, `manifest.json`, and 12 `qa/*.png` figures — carrying plan 01-07's Amendment A4 bead-mask detrend fix and its complete 15-key provenance.
- Confirmed `.venv/bin/python scripts/check_targets.py --project_dir .` prints `ALL CHECKS PASSED` both normally and under `python -O`: persisted `extraction_params.json` equals the code's `extraction_params()`, the manifest `extraction_params_sha256` matches, and every track passes the float64 dtype, NaN-only-invalid-slot, finite==mask, strict boundary ordering, and positive-width structural checks.
- Re-ran both test suites: `tests/test_targets.py` (26/26 PASS) and `tests/test_nsf_fmrg_data.py` (5/5 PASS), confirming the corrected contract holds under the regenerated artifacts.
- Verified `extraction_params.json` contains `MAX_TRACKING_GAP_COLUMNS` and `BEAD_MASK_HEIGHT_FRACTION`, and that the manifest digest is computed correctly from the persisted params.
- Verified `git status --porcelain -- data/raw` is empty — no raw file created, modified, or deleted by the regeneration.
- Captured the regenerated per-track results (median widths, valid-bin counts, three adjacent ordering verdicts) and wrote `.planning/phases/01-target-extraction-contract/01-08-ORDERING-OUTCOME.md`: the ordering `8 > 10 > 14 > 21` is **NOT fully restored** — 8-vs-10 (0.7411mm > 0.2509mm) and 14-vs-21 (0.5264mm > 0.2412mm) PASS, but 10-vs-14 FLAGs (0.2509mm is not > 0.5264mm), driven by track 10's valid-bin fraction collapsing to 5.2% (21/400, down from the previously observed ~43.8%) under the bead-mask fix.
- Per the plan's HONEST-OUTCOME GUARD: made zero changes to `src/targets.py` or any locked extraction constant (`git diff --stat -- src/targets.py` empty throughout). Escalated the residual ordering failure as a separate human decision — either (a) a documented human override of the roadmap ordering criterion, or (b) a new diagnosed defect investigating track 10's valid-fraction collapse in a follow-up plan — and recommended halting Phase 1 human verification sign-off until that decision is made.

## Task Commits

Task 1 produced no git-trackable diff (see Deviations); Task 2 was committed atomically:

1. **Task 1: Atomically regenerate all four-track artifacts and re-run the checker** - no commit (all files under `processed_data/targets/` are gitignored per `.gitignore:7`; regeneration verified in place, not committed — see Deviations)
2. **Task 2: Report the ordering as an honest outcome; escalate if not restored (no tuning)** - `c37c492` (docs)

**Plan metadata:** (this commit, docs: complete plan)

## Files Created/Modified

- `.planning/phases/01-target-extraction-contract/01-08-ORDERING-OUTCOME.md` - Verbatim regenerated per-track results, the three PASS/FLAG ordering verdicts, the honest "not restored" verdict, and the human-decision escalation (option a: override; option b: new diagnosed defect).
- `processed_data/targets/track_{8,10,14,21}_targets.npz`, `processed_data/targets/extraction_params.json`, `processed_data/targets/manifest.json`, `processed_data/targets/qa/*.png` (12 files) - Regenerated in place via the single atomic staged run; gitignored, not committed (matches the project's existing convention: "Generated target artifacts remain local and reproducible under processed_data/targets/").

## Decisions Made

- Confirmed via `.gitignore:7` (`/processed_data/targets/`) that Task 1's regenerated artifacts are intentionally out of git history — this matches the pre-existing STATE.md decision that the committed runner/checker recreate and validate outputs without adding runtime data to source history. No `git add -f` was used to force them in.
- Reported the ordering outcome exactly as printed by `check_targets.py`/`print_results`, without rounding, reframing, or omitting the FLAG.
- Surfaced track 10's valid-fraction collapse (43.8% -> 5.2%) as material context for the human decision, without diagnosing or fixing it in this plan, per 01-06-DIAGNOSIS.md Section 4's explicit scope note that plan 01-08 reports the outcome rather than re-diagnosing.

## Deviations from Plan

**1. [Process, not Rule 1-4] Task 1 produced no git commit**
- **Found during:** Preparing to commit Task 1's regenerated artifacts
- **Issue:** The plan's frontmatter lists `processed_data/targets/track_*.npz`, `extraction_params.json`, `manifest.json`, and `qa/` as `files_modified`, but `.gitignore:7` (`/processed_data/targets/`) excludes this entire tree from git — it is intentionally local-only generated output, consistent with the project's established convention (STATE.md: "Generated target artifacts remain local and reproducible under processed_data/targets/. Committed runner and checker recreate and validate outputs without adding runtime data to source history.").
- **Resolution:** Regenerated and fully verified the artifacts in place (all `<verify>` commands for Task 1 passed) but did not force-add them to git, since doing so would contradict both `.gitignore` and the documented project convention, and the task_commit_protocol explicitly forbids force-staging gitignored content. No source code changed in Task 1 (the runner/checker themselves were not modified — only their gitignored output was regenerated), so there is nothing else to commit for this task.
- **Files affected:** None committed; `processed_data/targets/*` regenerated on disk only.
- **Verification:** All of Task 1's `<verify>` and `<acceptance_criteria>` checks passed as run directly (see Accomplishments) — `ALL CHECKS PASSED`, 12 QA PNGs present with fresh mtimes, provenance digest match, empty `data/raw` diff.

---

**Total deviations:** 1 process deviation (no scope creep; no code/parameter changes).
**Impact on plan:** None on correctness — Task 1's actual deliverable (regenerated, provenance-complete, checker-validated artifacts) was fully produced and verified; only the git-commit mechanics differed from the plan's literal `files_modified` list, and that difference is dictated by the project's own `.gitignore` and prior documented convention, not an oversight.

## Issues Encountered

- `bin_profile()` emitted a `RuntimeWarning: All-NaN slice encountered` (via `np.nanmedian`) during Task 1's regeneration run, for bins where every column in a 0.2mm x-slot was invalid after masking/gap-handling. This is consistent with (and helps explain) track 10's severe valid-fraction collapse documented in `01-08-ORDERING-OUTCOME.md`; it did not affect correctness (NaN propagates correctly into the invalid-slot mask, confirmed by `check_targets.py`'s NaN/mask-equality checks passing), so it was left as observed evidence for the human decision rather than silenced or investigated further, per this plan's scope.

## Known Stubs

None. No new code was written in this plan; it only regenerated data artifacts and wrote a documentation/decision-record file.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 1's provenance-complete artifacts and 12 QA figures are ready for the outstanding human verification items in `01-VERIFICATION.md` (#1 residual maps, #2 boundary/gap overlays, #3 crop-edge widths) — the underlying data now reflects Amendment A4's corrected extraction.
- **Phase 1 is NOT ready for sign-off on the ordering success criterion.** `01-08-ORDERING-OUTCOME.md` explicitly recommends halting Phase 1 verification until a human makes the override-vs-diagnose decision documented there. Downstream phases (2+) should not proceed past Phase 1 completion until that decision is recorded.
- If the human chooses option (b) (diagnose track 10's valid-fraction collapse), a follow-up plan should investigate `bead_exclusion_mask()` and `MIN_PEAK_BASELINE_SEPARATION_MM`/`MIN_VALID_Y_POINTS` interaction specifically for track 10's lower-amplitude bead signal, using the same pre-registered, outcome-independent diagnosis discipline as `01-06-DIAGNOSIS.md`.

## Self-Check: PASSED

- `.planning/phases/01-target-extraction-contract/01-08-ORDERING-OUTCOME.md` exists and contains the verbatim regenerated results and the escalation.
- Commit `c37c492` exists in `git log`.
- `processed_data/targets/track_{8,10,14,21}_targets.npz`, `extraction_params.json`, `manifest.json`, and 12 `qa/*.png` files exist with post-run mtimes (~2026-07-20T21:34-21:35Z).
- `.venv/bin/python scripts/check_targets.py --project_dir .` and `.venv/bin/python -O scripts/check_targets.py --project_dir .` both print `ALL CHECKS PASSED`.
- `tests/test_targets.py` (26/26) and `tests/test_nsf_fmrg_data.py` (5/5) pass.
- `git status --porcelain -- data/raw` is empty; `git diff --stat -- src/targets.py` is empty.

---
*Phase: 01-target-extraction-contract*
*Completed: 2026-07-20*
