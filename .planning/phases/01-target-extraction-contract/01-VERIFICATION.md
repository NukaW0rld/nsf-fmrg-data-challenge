---
phase: 01-target-extraction-contract
verified: 2026-07-23T10:30:00Z
status: human_needed
score: 3/4 must-haves verified
behavior_unverified: 0
overrides_applied: 1
overrides:
  - must_have: "Running the extractor on all 4 tracks produces the expected width ordering 400W(8) > 350W(10) > 300W(14) > 200W(21)"
    reason: "The 10-vs-14 pair has FLAGged across five extraction amendments (A5-A8) and four independently-diagnosed investigation cycles (01-06->08, 01-11, 01-13, 01-16). A human reviewer explicitly recorded acceptance of this residual FLAG as a documented, investigated, known limitation via /gsd-verify-work Test 7 (01-UAT.md), reaffirmed at the widened magnitude in 01-SIGNOFF-REQUEST.md's preserved override record. Carried forward unchanged from the prior VERIFICATION.md pass (2026-07-22T22:30:00Z); not re-litigated."
    accepted_by: "human reviewer via /gsd-verify-work 1, Test 7 (01-UAT.md); reaffirmation item pending in 01-SIGNOFF-REQUEST.md"
    accepted_at: "2026-07-22"
re_verification:
  previous_status: gaps_found
  previous_score: 3/4
  gaps_closed:
    - "01-SIGNOFF-REQUEST.md staleness (Gap 1 of the prior pass): plan 01-17 regenerated the document end-to-end against live Amendment A8 artifacts (run_id b3f79f207cc1431fa238bb153c04419b re-verified live this pass via check_targets.py; matches every number quoted in the document). The prior gap's specific reason -- a superseded run_id/coverage/median narrative -- no longer applies."
    - "api-coverage seal-gate false positive: plan 01-18 added a reasoned COVERAGE.md declaration; re-ran the live gate this pass (`node gsd-tools.cjs check api-coverage-verify-pre 01`) and confirmed `block: false`."
    - "01-UAT.md's G-01-6 entry now carries a post_fix_note describing what Amendment A8 changed, without touching its status field (re-confirmed `status: failed` unchanged, gap ledger still 6 entries / 5 resolved / 1 failed, exactly as plan 01-18 intended)."
    - "scripts/diagnose_track10_coverage.py's WR-01 drift (targets.py's Amendment A8 vs the hand-duplicated classify_column) is now disclosed in-file; re-confirmed the diff (commit 3f87937) is comment-only, zero executable lines changed."
  gaps_remaining:
    - "No human visual sign-off round has occurred against the regenerated (and now-current) 01-SIGNOFF-REQUEST.md and the 12 Amendment A8 QA figures. This is the actual, substantive blocker TARGET-02's own acceptance criterion requires -- plans 01-17/01-18 explicitly did not attempt it (by design: it is a human decision, not an executor task). All four visual sign-off items and the width-ordering reaffirmation item in 01-SIGNOFF-REQUEST.md remain unticked `[ ]`; only the original 2026-07-22 width-ordering override retains its `[x]`. 01-UAT.md's G-01-6 status is unchanged at `failed`. REQUIREMENTS.md's TARGET-02 checkbox is correctly still unticked."
  regressions: []
gaps: []
human_verification:
  - test: "Open the 12 QA figures under processed_data/targets/qa/ (residual map, boundary overlay, width curve x4 tracks) alongside .planning/phases/01-target-extraction-contract/01-SIGNOFF-REQUEST.md's '## Figures to inspect' guidance and the live check_targets.py numbers it quotes (368/232/309/338 valid bins; medians 0.7653/0.3940/0.7122/0.6308mm)."
    expected: "Residual maps show no obviously wrong plane-fit; boundary overlays are visually continuous and track the true bead edge (track 10's fragmentation and tracks 8/14/21's jump/excursion behavior judged acceptable per Amendment A8's measured improvement, or explicitly rejected with a new gap if still unacceptable); crop-edge behavior at the 20mm/100mm domain boundaries is plausible; the seven locked constants plus Amendment A8's two behavioral rules are confirmed unchanged from what the document states."
    why_human: "Visual sanity of overlay continuity, jitter, and crop-edge plausibility is exactly the judgment call TARGET-02's acceptance criterion assigns to a human reviewer -- grep/file presence checks can confirm the figures exist, are current, and are well-formed images, but cannot judge whether the boundary tracking 'looks right' against the raw height map."
  - test: "Reaffirm (or reopen) the already-recorded 10-vs-14 width-ordering override at its widened magnitude (0.3182mm, up from 0.2404mm; track 10 coverage now 58.00%, up from 50.50%) per 01-SIGNOFF-REQUEST.md's unticked reaffirmation item."
    expected: "A recorded human decision (tick the reaffirmation item, or open a new investigation gap) reflecting the current magnitude -- not a silent carry-forward of the original 2026-07-22 acceptance without acknowledging the gap widened."
    why_human: "This is a judgment call about whether a known, already-investigated limitation is still acceptable at a materially different (wider) magnitude -- not a code defect verifiable by inspection. The override in this VERIFICATION.md's frontmatter carries the ORIGINAL acceptance forward per Step 3b, but the phase's own sign-off document flags this as needing a fresh reviewer nod, which has not yet been recorded."
---

# Phase 1: Target Extraction & Contract Verification Report

**Phase Goal:** A documented, reproducible local-width extraction method is specified and then implemented, and is visually validated against all 4 tracks before anything downstream trusts it as ground truth.
**Verified:** 2026-07-23T10:30:00Z
**Status:** human_needed
**Re-verification:** Yes — after gap-closure plans 01-17 (regenerate stale sign-off doc) and 01-18 (seal-gate + UAT annotation + WR-01 disclosure), following the 2026-07-22T22:30:00Z VERIFICATION.md (previous status: gaps_found, 3/4)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---:|---|---|---|
| 1 | The TARGET-01 contract (width definition, threshold rule, smoothing scale, 0.2mm grid, valid-coordinate mask, track-21 gap rule) is written and reviewed before extraction code is trusted | VERIFIED | `01-CONTEXT.md` records D-01 through D-16 plus Amendments A1-A8 (`grep -c "Amendment A8" 01-CONTEXT.md` = 1, dated, names both Amendment A8 mechanisms). Unchanged since the prior pass. |
| 2 | Running the extractor on all 4 tracks produces the expected width ordering 400W(8) > 350W(10) > 300W(14) > 200W(21) | PASSED (override) | Live re-run this pass of `.venv/bin/python scripts/check_targets.py --project_dir .`: exit 0, `ALL CHECKS PASSED`; 8=0.7653mm > 10=0.3940mm (PASS), 10=0.3940mm vs 14=0.7122mm (FLAG), 14=0.7122mm > 21=0.6308mm (PASS) — identical to the numbers `01-SIGNOFF-REQUEST.md` and `01-16-ORDERING-OUTCOME.md` report. The 10-vs-14 FLAG is a carried-forward accepted known limitation (see override entry); a fresh human reaffirmation at the widened magnitude is still outstanding (see Human Verification item 2). |
| 3 | QA plots overlay extracted width/boundary on raw+detrended maps for all 4 tracks, incl. track 21's gaps, and are visually confirmed sane (no sawtooth/high-frequency jitter, no silently dropped gaps) | UNCERTAIN (needs human) | All prerequisite artifacts are now current and accurate: `01-SIGNOFF-REQUEST.md` was regenerated by plan 01-17 against live Amendment A8 output (re-verified this pass: the document's only 32-hex token, `b3f79f207cc1431fa238bb153c04419b`, matches `manifest.json`'s live `run_id`; its only 64-hex token matches the live `extraction_params_sha256`; all 4 rows' valid-bin counts/fractions match today's `check_targets.py` output verbatim). The 12 QA PNGs under `processed_data/targets/qa/` are current (Amendment A8 generation, unchanged since the prior pass). But the actual human visual review this truth requires has NOT occurred: every visual sign-off item in `01-SIGNOFF-REQUEST.md` remains unticked `[ ]` (only the pre-existing width-ordering override is ticked), and `01-UAT.md`'s G-01-6 entry is still `status: failed` (a `post_fix_note` was added describing Amendment A8's fix, but the note itself states "This is NOT a sign-off... this gap keeps its current unresolved verdict until a human records a /gsd-verify-work 1 round"). This is not a codebase defect — it is the human judgment call the acceptance criterion assigns to a reviewer, not resolvable by grep/inspection. |
| 4 | The identical extraction rule is applied across all 4 tracks with no per-track-tuned thresholds (single shared parameterization) | VERIFIED | `grep -n "track_id =="` across `src/targets.py`, `src/nsf_fmrg_data.py`, `scripts/run_target_extraction.py` returns nothing (re-confirmed live). All 61 tests across `tests/test_targets.py` (38), `tests/test_nsf_fmrg_data.py` (13), `tests/test_run_target_extraction.py` (10) pass, executed directly this pass via `.venv/bin/python tests/test_*.py` (exit 0, every `PASS:` line printed, including `test_single_parameterization_has_no_track_conditionals` and `test_track_id_does_not_affect_numeric_output`). |

**Score:** 3/4 truths verified (2 fully VERIFIED, 1 PASSED via documented override); 1 truth UNCERTAIN pending human visual review (not a codebase gap).

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | ----------- | ------ | ------- |
| `src/targets.py` | Contract implementation incl. Amendments A1-A8 | VERIFIED | Unchanged since prior pass (`git diff --stat` between the prior VERIFICATION commit and HEAD touches only docs/`scripts/diagnose_track10_coverage.py` comments). `halfmax_edges` still reorders clip-exclusion before merging; Amendment A8's history-based gate intact. |
| `tests/test_targets.py`, `tests/test_nsf_fmrg_data.py`, `tests/test_run_target_extraction.py` | Regression coverage incl. A8's 6 new regressions | VERIFIED | Full local run this pass: 61/61 tests PASS (38+13+10), executed directly (no pytest module in `.venv`, run as plain scripts per the repo's existing convention — each file's own `__main__` block). |
| `processed_data/targets/track_{8,10,14,21}_targets.npz` | Persisted per-track extraction output | VERIFIED | `manifest.json`'s `run_id` (`b3f79f207cc1431fa238bb153c04419b`) confirmed live via `check_targets.py`, unchanged since plan 01-16 (no regeneration since; git status clean under `processed_data/`). |
| `processed_data/targets/qa/` (12 PNGs) | QA figures (residual/overlay/width × 4 tracks) | VERIFIED (present, current Amendment A8 generation); visual sanity STILL NOT REVIEWED | Unchanged since prior pass. No human has opened these files for sign-off yet (see Human Verification item 1). |
| `.planning/phases/01-target-extraction-contract/01-SIGNOFF-REQUEST.md` | Standing human sign-off request, accurate as of the current QA generation | VERIFIED (regenerated, now current) | Plan 01-17 rewrote it end-to-end against live Amendment A8 output. Re-verified this pass: run_id, sha256, per-track valid-bin counts/fractions, and 10-vs-14 gap (0.3182mm, stated as widened) all match today's live `check_targets.py`/`manifest.json` output. This closes the prior pass's Gap 1 (staleness) — the document itself is no longer the blocker; the missing human review round is. |
| `.planning/phases/01-target-extraction-contract/COVERAGE.md` | Reasoned no-external-API declaration (new, plan 01-18) | VERIFIED | Present; re-ran the live gate (`node gsd-tools.cjs check api-coverage-verify-pre 01`) this pass — returns `block: false`, `coverage_present: true`, `none_declared: true`. Content matches the plan's 191-character reason verbatim. |
| `scripts/diagnose_track10_coverage.py` | WR-01 in-file disclaimer (plan 01-18) | VERIFIED | Disclaimer present above `classify_column` (lines ~106-121); `git show 3f87937` confirms the diff is comment-only (16 insertions, all `#`-prefixed or blank, zero executable-line changes). |
| `.planning/phases/01-target-extraction-contract/01-UAT.md` | G-01-6 annotated with Amendment A8 outcome, verdict unchanged | VERIFIED | `post_fix_note` present under G-01-6; `status: failed` unchanged; gap ledger re-counted this pass: 6 `gap_id:` entries, 5 `status: resolved`, 1 `status: failed` — matches plan 01-18's claimed shape exactly. |
| `.planning/REQUIREMENTS.md` | TARGET-02 checkbox agrees with its traceability row (still unticked pending sign-off) | VERIFIED | `- [ ] **TARGET-02**` and traceability row "Awaiting human visual sign-off... see `01-SIGNOFF-REQUEST.md`" agree. TARGET-01's checkbox is also currently `[ ]` (traceability row: "Gaps Found") — a conservative blanket revert recorded in commit `d2c6a22` alongside TARGET-02's revert, even though truths 1 and 4 above (TARGET-01's own substance) are independently VERIFIED in this pass. This is a documentation-bookkeeping choice tied to the phase's overall gaps_found/human_needed status, not a code defect; flagged for awareness, not as a gap. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------ |
| `processed_data/targets/manifest.json` + live `check_targets.py` output | `01-SIGNOFF-REQUEST.md` "## Current state" | narrative/numeric accuracy | WIRED (fixed this cycle) | Live re-derivation this pass (`run_id b3f79f207cc1431fa238bb153c04419b`, 368/232/309/338 valid bins, medians 0.7653/0.3940/0.7122/0.6308mm) matches the document's quoted values exactly. This was the prior pass's NOT_WIRED finding; now resolved by plan 01-17. |
| `01-16-ORDERING-OUTCOME.md`'s honest fragmentation/coverage report | `01-UAT.md`'s G-01-6 gap entry | gap-closure status update (annotation, not flip) | WIRED (as designed) | `post_fix_note` added under G-01-6 accurately summarizing Amendment A8's outcome; `status:` field deliberately left `failed` pending the human round. This matches plan 01-18's intent (annotate, don't flip) exactly. |
| `src/targets.py`'s Amendment A8 signature/behavior | `scripts/diagnose_track10_coverage.py`'s `classify_column` reimplementation | mirrored rejection-reason logic | NOT_WIRED (disclosed, pre-existing, accepted debt) | Still drifted per `01-REVIEW.md`'s WR-01 finding — diagnostic-only, does not affect the shipped extraction pipeline, now explicitly disclosed in-file so it cannot mislead a future reader. |
| `01-SIGNOFF-REQUEST.md`'s visual sign-off checklist | Human reviewer's `/gsd-verify-work 1` decision record | recorded outcome | NOT_WIRED (the actual remaining gap) | All four visual-review items and the reaffirmation item remain unticked. No `/gsd-verify-work` round has been run against this document since it was regenerated. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| `check_targets.py` passes and reports live ordering/coverage numbers matching the sign-off document | `.venv/bin/python scripts/check_targets.py --project_dir .` | exit 0, `ALL CHECKS PASSED`; 368/232/309/338 valid bins, 0.7653/0.3940/0.7122/0.6308mm medians | PASS |
| Full local regression suite passes (61 tests across 3 files) | `.venv/bin/python tests/test_targets.py`, `tests/test_nsf_fmrg_data.py`, `tests/test_run_target_extraction.py` | exit 0 all three; every test printed `PASS:` | PASS |
| api-coverage seal gate no longer blocks the phase | `node ~/.claude/gsd-core/bin/gsd-tools.cjs check api-coverage-verify-pre 01` | `{"block": false, "coverage_present": true, "none_declared": true, ...}` | PASS |
| No per-track conditional branches in the extraction/loader/runner code | `grep -n "track_id ==" src/targets.py src/nsf_fmrg_data.py scripts/run_target_extraction.py` | no matches | PASS |
| `scripts/diagnose_track10_coverage.py` disclaimer diff is comment-only | `git show 3f87937 -- scripts/diagnose_track10_coverage.py` | 16 insertions, all comment/blank lines | PASS |
| No source/test/script/artifact/raw-data drift since prior gap-closure plans besides the intended docs/diagnostic-comment changes | `git diff --stat 4134654..HEAD -- src/ tests/ scripts/ processed_data/ data/raw/` | only `scripts/diagnose_track10_coverage.py` (+16 comment lines) | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| TARGET-01 | 01-01 through 01-18 (locked contract, amendments A1-A8) | Local-width target contract specified/documented before extraction code trusted | SATISFIED (substance verified; checkbox conservatively unticked pending phase-level sign-off) | `01-CONTEXT.md` D-01–D-16 + Amendments A1-A8; single shared parameterization confirmed via grep + full test suite (truths 1 and 4 above). REQUIREMENTS.md checkbox remains `[ ]` / "Gaps Found" as a conservative phase-status bookkeeping choice (commit `d2c6a22`), not because the underlying contract work is incomplete. |
| TARGET-02 | 01-02 through 01-18 (extractor + QA + gap-closure) | Extractor implements the locked contract and is visually QA'd against all 4 tracks | NEEDS HUMAN | Extractor implementation and current, accurate QA artifacts are VERIFIED. The visual QA sign-off itself — TARGET-02's own explicit acceptance criterion — has not been recorded by any human reviewer. This is the single remaining blocker for both TARGET-02 and the phase overall. |

No orphaned requirements: `.planning/REQUIREMENTS.md`'s traceability table maps both TARGET-01 and TARGET-02 to Phase 1, and both are addressed by the plans reviewed above.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `src/nsf_fmrg_data.py` | 184 (fallback), guarded only at `src/targets.py:409-410` | `load_wyko_asc`'s `pixel_size_mm` silent fallback unguarded in 3 direct diagnostic-script callers (`01-REVIEW.md` WR-01) | Warning | Not exercised by the shipped target-extraction pipeline (guarded at the one call site that persists targets); would silently mis-scale diagnostic output if a malformed `.ASC` header were ever encountered. Pre-existing, documented, not introduced by this verification cycle's plans. |
| `src/nsf_fmrg_data.py` | 118-141 | `extract_final_thermal_frames` does not validate segment length hits 400 frames before clamping (`01-REVIEW.md` WR-02) | Warning | Zero blast radius in this phase (thermal frames aren't touched by target extraction); will matter once Phase 2 aligns thermal frames to the target grid. Pre-existing, documented. |
| `processed_data/diagnostics/width_regression_sweep.csv` | n/a | Untracked diagnostic output file (git status: `??`), inconsistent with its two sibling diagnostic CSVs which are committed (`01-REVIEW.md` IN-03) | Info | Diagnostic-only, does not affect the shipped pipeline. Pre-existing, documented in the code review, not addressed by plans 01-17/01-18 (out of their scope). |

No new debt markers (`TBD`/`FIXME`/`XXX`) introduced by this cycle's changes. `scripts/diagnose_track10_coverage.py`'s new disclaimer comment and `COVERAGE.md` were checked and contain none.

### Gaps Summary

No codebase gaps remain. The prior pass's single gap (stale `01-SIGNOFF-REQUEST.md`) is closed: the document was regenerated end-to-end by plan 01-17 against live Amendment A8 artifacts and every number was re-verified live in this pass. Plan 01-18 additionally unblocked the api-coverage seal gate with a reasoned declaration, annotated (without flipping) `01-UAT.md`'s G-01-6 gap, and disclosed a pre-existing diagnostic-script drift — all three re-confirmed live.

What remains is not a codebase defect: TARGET-02's own acceptance criterion requires a human reviewer to open the 12 current QA figures and the regenerated sign-off document and record a `/gsd-verify-work 1` outcome. That round has not occurred. Every prerequisite for it — current artifacts, an accurate sign-off document, an unblocked seal gate — is now in place. This routes to `human_needed`, not `gaps_found`: nothing here is fixable by further executor/planning work; it is the human decision the entire gap-closure sequence (plans 01-16 through 01-18) was structured to protect and enable.

---

_Verified: 2026-07-23T10:30:00Z_
_Verifier: Claude (gsd-verifier)_
