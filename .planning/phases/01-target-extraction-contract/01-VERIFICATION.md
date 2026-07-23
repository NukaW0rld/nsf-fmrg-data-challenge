---
phase: 01-target-extraction-contract
verified: 2026-07-22T22:30:00Z
status: gaps_found
score: 3/4 must-haves verified
behavior_unverified: 0
overrides_applied: 1
overrides:
  - must_have: "Running the extractor on all 4 tracks produces the expected width ordering 400W(8) > 350W(10) > 300W(14) > 200W(21)"
    reason: "The 10-vs-14 pair has FLAGged across five extraction amendments (A5-A8) and four independently-diagnosed investigation cycles (01-06→08, 01-11, 01-13, 01-16). A human reviewer explicitly recorded acceptance of this residual FLAG as a documented, investigated, known limitation via /gsd-verify-work Test 7 (01-UAT.md), with the project's own HONEST-OUTCOME GUARD prohibiting further open-ended tuning absent a new independently-diagnosed root cause. 01-16-ORDERING-OUTCOME.md (Amendment A8) explicitly does not reopen this decision. Accepted here on the same basis, not re-litigated -- but flagged below (Gap 1) because the sign-off document describing this decision now quotes stale (pre-Amendment-A8) numbers and the gap widened materially (0.2404mm -> 0.3182mm, +32%) since the decision was recorded."
    accepted_by: "human reviewer via /gsd-verify-work 1, Test 7 (01-UAT.md)"
    accepted_at: "2026-07-22"
re_verification:
  previous_status: human_needed
  previous_score: 3/4
  gaps_closed:
    - "G-01-6 (UAT Test 8, boundary fragmentation/crop-edge): Amendment A8 (plan 01-16) closed Mechanism A (merge-before-clip ordering defect, 65-90% of no_candidates invalidations) and Mechanism B (same-column gate blind spot in single-candidate columns, 14-72% of tracked selections). Both specific crop-edge symptoms UAT Test 8 named (track 10's isolated valid run, track 21's near-zero terminal drop) are confirmed resolved on the regenerated artifacts. Coverage increased on every track (368/232/309/338 vs 361/202/301/308) and contiguous-run fragmentation improved on 3 of 4 tracks (track 21 -51%)."
  gaps_remaining:
    - "01-SIGNOFF-REQUEST.md was NOT regenerated after Amendment A8 -- it still describes the superseded Amendment A7 generation (run_id 99a4e8472f0a4164938363af0725f31b, 361/202/301/308 valid bins) while the live production artifacts are Amendment A8 (run_id b3f79f207cc1431fa238bb153c04419b, 368/232/309/338 valid bins). This is the exact class of staleness previously found and fixed by plan 01-15 for the A6->A7 transition, now recurred for A7->A8."
    - "No human visual sign-off round has occurred against the Amendment A8 QA figures. UAT Test 8's visual review was performed against Amendment-A7-era images; all 12 PNGs under processed_data/targets/qa/ have since been regenerated with materially different fragmentation counts and crop-edge behavior. G-01-6's status in 01-UAT.md's own Gaps section is still 'failed' (not updated to 'resolved')."
  regressions: []
gaps:
  - truth: "QA plots overlay the extracted width/boundary on both the raw and detrended height map for all 4 tracks, including track 21's gap-heavy regions, and are visually confirmed sane (no sawtooth/high-frequency jitter, no silently dropped gaps)."
    status: failed
    reason: "The vehicle this project uses to request/record human visual sign-off (01-SIGNOFF-REQUEST.md) is stale relative to the current production artifacts, and no fresh visual review round has occurred against the current (Amendment A8) images. G-01-6 (the UAT gap this success criterion maps to) remains 'status: failed' in 01-UAT.md's own gap-tracking, not updated to 'resolved', despite plan 01-16's code-level fixes."
    artifacts:
      - path: ".planning/phases/01-target-extraction-contract/01-SIGNOFF-REQUEST.md"
        issue: "Describes run_id 99a4e8472f0a4164938363af0725f31b (Amendment A7: valid bins 361/202/301/308; medians 0.7401/0.3770/0.6174/0.3825mm; 10-vs-14 gap 0.2404mm), but processed_data/targets/manifest.json's live run_id is b3f79f207cc1431fa238bb153c04419b (Amendment A8: valid bins 368/232/309/338; medians 0.7653/0.3940/0.7122/0.6308mm; 10-vs-14 gap 0.3182mm, +32%). A human granting sign-off against this document today would be confirming a superseded narrative even though the linked image files on disk are current."
    missing:
      - "Regenerate 01-SIGNOFF-REQUEST.md against the live Amendment A8 check_targets.py output and manifest.json (mirroring plan 01-15's precedent for the A6->A7 transition): update run_id, published timestamp, extraction_params_sha256 cross-check, the summary table, the coverage table, the plain-language state paragraphs (including the widened 10-vs-14 gap and Amendment A8's fragmentation/coverage before/after), and the 'Contract in effect' table (Amendment A8's clip-before-merge reorder and history-based gate)."
      - "Run a fresh human visual sign-off round (/gsd-verify-work 1) against the regenerated document and the current 12 QA PNGs, since the prior visual review (UAT Test 8) was performed against Amendment-A7-era images that have since changed materially on every track."
      - "Update G-01-6's status in 01-UAT.md's Gaps section from 'failed' to 'resolved' (or a new gap, if the fresh visual review still finds issues) once that round completes."
---

# Phase 1: Target Extraction & Contract Verification Report

**Phase Goal:** A documented, reproducible local-width extraction method is specified and then implemented, and is visually validated against all 4 tracks before anything downstream trusts it as ground truth.
**Verified:** 2026-07-22T22:30:00Z
**Status:** gaps_found
**Re-verification:** Yes — after gap-closure plan 01-16 (Amendment A8, closed UAT gap G-01-6's two tractable mechanisms), following the 2026-07-22T12:00:00Z VERIFICATION.md (previous status: human_needed, 3/4)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---:|---|---|---|
| 1 | The TARGET-01 contract (width definition, threshold rule, smoothing scale, 0.2mm grid, valid-coordinate mask, track-21 gap rule) is written and reviewed before extraction code is trusted | VERIFIED | `.planning/phases/01-target-extraction-contract/01-CONTEXT.md` records D-01 through D-16 plus Amendments A1-A8 (A8 added by plan 01-16, confirmed present via `grep -q "Amendment A8"`). Unchanged in substance from the prior verification pass; the phase's own history shows the contract was locked and reviewed before every extraction/fix cycle. |
| 2 | Running the extractor on all 4 tracks produces the expected width ordering 400W(8) > 350W(10) > 300W(14) > 200W(21) | PASSED (override) | Live re-run of `.venv/bin/python scripts/check_targets.py --project_dir .` today (exit 0, `ALL CHECKS PASSED`): 8=0.7653mm > 10=0.3940mm (PASS), 10=0.3940mm vs 14=0.7122mm (FLAG), 14=0.7122mm > 21=0.6308mm (PASS). The 10-vs-14 FLAG is an already-accepted known limitation (UAT Test 7, four independent diagnosis cycles); see override entry in frontmatter. Flagged: the gap widened from 0.2404mm to 0.3182mm (+32%) since that decision was recorded, and the sign-off document describing the decision is now stale (see Gap 1). |
| 3 | QA plots overlay extracted width/boundary on raw+detrended maps for all 4 tracks, incl. track 21's gaps, and are visually confirmed sane (no sawtooth/high-frequency jitter, no silently dropped gaps) | FAILED | Plan 01-16 (Amendment A8) measurably improved fragmentation on 3/4 tracks and resolved both crop-edge symptoms UAT Test 8 cited, but NO fresh human visual sign-off has occurred against these regenerated (Amendment A8) figures -- the prior visual review (UAT Test 8) judged Amendment-A7-era images, which have since changed materially (coverage +7/+30/+8/+30 bins per track; fragmentation counts changed on every track). `01-UAT.md`'s own Gaps section still records G-01-6 as `status: failed`, not updated to `resolved`. The sign-off vehicle (`01-SIGNOFF-REQUEST.md`) was not regenerated to reflect Amendment A8 (see Gap 1) -- confirmed by comparing its quoted `run_id` (`99a4e847...`) against the live `processed_data/targets/manifest.json` (`b3f79f20...`). |
| 4 | The identical extraction rule is applied across all 4 tracks with no per-track-tuned thresholds (single shared parameterization) | VERIFIED | `grep -n "track_id =="` across `src/targets.py`, `src/nsf_fmrg_data.py`, `scripts/run_target_extraction.py` returns nothing (re-confirmed live). `tests/test_targets.py::test_single_parameterization_has_no_track_conditionals` and `test_track_id_does_not_affect_numeric_output` both PASS in a full local run of all 38 tests in `tests/test_targets.py` (plus 13 in `tests/test_nsf_fmrg_data.py`, 10 in `tests/test_run_target_extraction.py`), executed directly this pass — all green. |

**Score:** 3/4 truths verified (2 fully VERIFIED, 1 PASSED via documented override); 1 truth FAILED (blocking).

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | ----------- | ------ | ------- |
| `src/targets.py` | Contract implementation incl. Amendments A1-A8 | VERIFIED | `halfmax_edges` reorders clip-exclusion before merging (`grep -c 'merge_adjacent_runs(non_edge_runs' src/targets.py` = 1) and gates tracked selection with the history-based joint far-AND-small check (Amendment A8). `extraction_params()` unchanged at 19 keys (no new constant introduced, as designed). |
| `tests/test_targets.py`, `tests/test_nsf_fmrg_data.py`, `tests/test_run_target_extraction.py` | Regression coverage for all amendments incl. A8's 6 new Mechanism A/B regressions | VERIFIED | Full local run this pass: all tests PASS (38/13/10), including `test_halfmax_edges_recovers_leading_edge_swallowed_interior_run`, `test_halfmax_edges_recovers_trailing_edge_swallowed_interior_run`, `test_halfmax_edges_rejects_lone_candidate_far_and_small_versus_tracked_history`, `test_halfmax_edges_accepts_lone_candidate_small_but_close_to_tracked_history`, `test_halfmax_edges_accepts_lone_candidate_far_but_large_versus_tracked_history`, `test_extract_targets_from_arrays_rejects_track8_style_single_candidate_trigger_column`. |
| `processed_data/targets/track_{8,10,14,21}_targets.npz` | Persisted per-track extraction output | VERIFIED | Regenerated by plan 01-16's Task 2. `manifest.json`'s `run_id` (`b3f79f207cc1431fa238bb153c04419b`), published `2026-07-23T02:43:48Z`, confirmed live this pass matching `check_targets.py`'s live output. |
| `processed_data/targets/qa/` (12 PNGs) | QA figures (residual/overlay/width × 4 tracks) | VERIFIED (present, current Amendment A8 generation); visual sanity NOT YET REVIEWED | File timestamps (2026-07-22 21:43-21:44) match the Amendment A8 regeneration. No human has yet opened these specific files for sign-off (see Gap 1). |
| `.planning/phases/01-target-extraction-contract/01-CONTEXT.md` | Amendments A1-A8 documented | VERIFIED | Amendment A8 present, dated, names both mechanisms and the no-new-constant rationale, reaffirms Mechanism C's deferral. |
| `.planning/phases/01-target-extraction-contract/01-SIGNOFF-REQUEST.md` | Standing human sign-off request, accurate as of the current QA generation | **STUB (stale)** | Still describes Amendment A7's generation (`run_id 99a4e8472f0a4164938363af0725f31b`, 361/202/301/308 valid bins, 0.2404mm 10-vs-14 gap) — confirmed via direct read and diff against the live Amendment A8 numbers (368/232/309/338 valid bins, 0.3182mm gap). This is the same staleness defect class plan 01-15 previously fixed for the A6->A7 transition; it was not caught for the A7->A8 (plan 01-16) transition. |
| `.planning/REQUIREMENTS.md` | TARGET-02 checkbox agrees with its traceability row | VERIFIED | `- [ ] **TARGET-02**` agrees with its traceability row ("Awaiting human visual sign-off... see `01-SIGNOFF-REQUEST.md`"). A 2026-07-22 correction note (plan 01-16) explains an automated tooling step incorrectly re-ticked this checkbox and it was manually reverted to `[ ]`, consistent with no sign-off having actually occurred. TARGET-01 correctly remains `[x]` / `Complete`. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `processed_data/targets/manifest.json` + live `check_targets.py` output | `01-SIGNOFF-REQUEST.md` "## Current state" | narrative/numeric accuracy | **NOT_WIRED (stale)** | Live re-derivation this pass (`run_id b3f79f207cc1431fa238bb153c04419b`, 368/232/309/338 valid bins) does NOT match the document's quoted `run_id 99a4e8472f0a4164938363af0725f31b` / 361/202/301/308 figures. Confirmed by direct string comparison. |
| `01-16-ORDERING-OUTCOME.md`'s honest fragmentation/coverage report | `01-UAT.md`'s G-01-6 gap entry | gap-closure status update | **PARTIAL** | 01-16-ORDERING-OUTCOME.md and 01-16-SUMMARY.md both document the fix and its measured (mixed-but-largely-improved) outcome, but `01-UAT.md`'s own Gaps section still records `G-01-6: status: failed` — not reconciled to `resolved` pending the fresh visual round this gap requires. |
| `src/targets.py`'s Amendment A8 signature/behavior | `scripts/diagnose_track10_coverage.py`'s `classify_column` reimplementation | mirrored rejection-reason logic | **NOT_WIRED (drifted, pre-existing warning)** | Per `01-REVIEW.md`'s WR-01: the diagnostic script still applies merge-then-clip (the pre-A8 order) and has no history-based gate, so its committed `track10_coverage_diagnosis.csv` reports rejection counts (361/202/301/312-style) that don't match current production `valid_mask` sums (368/232/309/338). Does not affect the shipped extraction pipeline (diagnostic-only), but is a real, unresolved drift. |
| `.planning/REQUIREMENTS.md` TARGET-02 row | `01-SIGNOFF-REQUEST.md` | flip-on-record-only | WIRED | Document and REQUIREMENTS.md agree TARGET-02 flips to complete only after a recorded `/gsd-verify-work 1` sign-off exists; confirmed the checkbox is still `[ ]`, not prematurely flipped. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| `check_targets.py` passes and reports live ordering/coverage numbers | `.venv/bin/python scripts/check_targets.py --project_dir .` | exit 0, `ALL CHECKS PASSED`; 368/232/309/338 valid bins, 0.7653/0.3940/0.7122/0.6308mm medians | PASS |
| No per-track branching exists in production code | `grep -n "track_id ==" src/targets.py src/nsf_fmrg_data.py scripts/run_target_extraction.py` | no matches | PASS |
| Full local regression suite passes | `.venv/bin/python tests/test_targets.py`, `tests/test_nsf_fmrg_data.py`, `tests/test_run_target_extraction.py` | 38/13/10 PASS, 0 fail | PASS |
| `01-SIGNOFF-REQUEST.md` numbers vs. live artifacts | Compared live `manifest.json`/`check_targets.py` output against document's quoted numbers | MISMATCH: run_id, valid-bin counts, medians, 10-vs-14 gap all differ (A7 vs A8) | **FAIL** |
| No debt markers in production source | `grep -nE "TBD\|FIXME\|XXX\|TODO\|HACK\|PLACEHOLDER" src/targets.py src/nsf_fmrg_data.py scripts/run_target_extraction.py scripts/check_targets.py` | no matches | PASS |
| G-01-6 reconciliation | Read `01-UAT.md` Gaps section | `status: failed`, unchanged since Test 8; not updated after plan 01-16 | **FAIL (unreconciled)** |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| TARGET-01 | 01-01 (+ amendments in 01-04, 01-07, 01-11, 01-13, 01-14, 01-16) | Contract specified before extraction code trusted | SATISFIED | D-01–D-16 + Amendments A1-A8 in `01-CONTEXT.md`; `REQUIREMENTS.md` checkbox `[x]` and traceability row `Complete` agree; single shared parameterization confirmed by test + grep. |
| TARGET-02 | 01-02, 01-05, 01-06–01-16 | Extractor implements contract, visually QA'd against all 4 tracks | **BLOCKED** | Extraction/coverage mechanically verified (all tests pass, artifacts present and current); however the visual-QA acceptance criterion is not satisfied: the sign-off vehicle is stale (describes a superseded generation) and no human has reviewed the current Amendment A8 figures. `REQUIREMENTS.md`'s checkbox (`[ ]`) and traceability row ("Awaiting human visual sign-off") correctly reflect this unresolved state. |

No orphaned requirements found — TARGET-01/TARGET-02 are the only IDs mapped to Phase 1 across all 16 plans' `requirements:` frontmatter and `REQUIREMENTS.md`'s traceability table.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `.planning/phases/01-target-extraction-contract/01-SIGNOFF-REQUEST.md` | 15, 21 | Document describes a superseded artifact generation (Amendment A7) while production has moved to Amendment A8 | 🛑 Blocker | Directly blocks Success Criterion 3 — a human cannot meaningfully grant visual sign-off against numbers that no longer match the live pipeline output. See Gap 1. |
| `.planning/phases/01-target-extraction-contract/01-UAT.md` | Gaps section, G-01-6 | Gap status not reconciled after gap-closure plan 01-16 completed | Warning | `status: failed` persists even though code-level fixes landed; correct per project design (visual gaps require a fresh human round to close), but leaves the phase's own gap ledger looking unresolved until that round happens. |
| `scripts/diagnose_track10_coverage.py` | 110-175 (per `01-REVIEW.md` WR-01) | Diagnostic tooling drifted out of sync with production `halfmax_edges` a second time (post-Amendment-A8) | Warning (pre-existing, carried from code review) | Does not affect the shipped extraction pipeline; affects only a diagnostic script's own committed CSV output. |
| `.planning/STATE.md` | 8-11 | Shows "Plan: 2 of 16" / "Status: Ready to execute", stale relative to plan 16 having completed | Info | Tracking/dashboard drift, not a pipeline defect; does not affect TARGET-01/02 correctness. |

No debt markers (`TBD`/`FIXME`/`XXX`) or unreferenced `TODO`/`HACK`/`PLACEHOLDER` found in `src/targets.py`, `src/nsf_fmrg_data.py`, `scripts/run_target_extraction.py`, or `scripts/check_targets.py`.

### Human Verification Required

Once Gap 1 (regenerating `01-SIGNOFF-REQUEST.md` against the live Amendment A8 run) is closed, a human reviewer still needs to:

### 1. Visual sign-off on the 12 regenerated (Amendment A8) QA figures

**Test:** Open all 12 figures under `processed_data/targets/qa/` (regenerated 2026-07-22 21:43-21:44, run_id `b3f79f207cc1431fa238bb153c04419b`) — residual maps, boundary overlays, width curves for tracks 8/10/14/21 — focusing on: track 8's previously-cited excursion regions (~24-27, 48-55, 81-86, 97-100mm); track 10's overall fragmentation and its right crop-edge band (68 contiguous runs, +1 vs A7); track 21's right crop-edge terminal region (now 0.740→0.877→0.713→0.650→0.403→0.405mm, milder taper vs the prior near-zero collapse).
**Expected:** A recorded yes/no per figure-category via `/gsd-verify-work 1`, closing G-01-6 for the current Amendment A8 generation (or, if issues remain, a new gap recording exactly what's still wrong).
**Why human:** Boundary-overlay "sanity" (no unacceptable sawtooth/jitter) is an explicit domain judgment call this phase's own design defers to a human reviewer — mechanical fragmentation/jump-statistic counts (already computed in `01-16-ORDERING-OUTCOME.md`) inform but do not substitute for this judgment.

### 2. Reaffirm (not reopen) the 10-vs-14 width-ordering FLAG acceptance given the widened gap

**Test:** Confirm that UAT Test 7's acceptance of the 10-vs-14 FLAG as a documented known limitation still stands now that the gap has widened from 0.2404mm to 0.3182mm (+32%) under Amendment A8, and that the regenerated `01-SIGNOFF-REQUEST.md` states this current number rather than the stale 0.2404mm figure.
**Expected:** A brief recorded confirmation (not a new investigation cycle) that the already-accepted rationale still applies at the new magnitude, carried into `ROADMAP.md`/`REQUIREMENTS.md` as a caveat before Phase 2 begins.
**Why human:** This phase's own HONEST-OUTCOME GUARD reserves this "accept vs. investigate further" call for a human, and a materially widened gap is not something a mechanical override-carry-forward should silently absorb without at least a brief reaffirmation.

### Gaps Summary

One blocking gap: **`01-SIGNOFF-REQUEST.md` is stale.** It still describes Amendment A7's artifact generation (run_id `99a4e8472f0a4164938363af0725f31b`; 361/202/301/308 valid bins; 0.2404mm 10-vs-14 gap) while the live production artifacts are Amendment A8 (run_id `b3f79f207cc1431fa238bb153c04419b`, regenerated by gap-closure plan 01-16; 368/232/309/338 valid bins; 0.3182mm gap). This is precisely the staleness defect class the project already found and fixed once before (plan 01-15, for the A6→A7 transition) — it recurred for the A7→A8 transition and was not caught before this verification pass.

Because the sign-off document is the vehicle this project uses to request and record human visual approval, its staleness means Success Criterion 3 ("QA plots ... visually confirmed sane") cannot yet be considered satisfied even though the underlying code fix (plan 01-16, Amendment A8) is real, tested, and measurably improves fragmentation on 3 of 4 tracks. `01-UAT.md`'s own gap ledger agrees: G-01-6 is still recorded as `status: failed`, not `resolved`.

Success Criteria 1 and 4 are fully VERIFIED (contract documented and reviewed; single shared parameterization confirmed by code inspection and passing tests). Success Criterion 2 (width ordering) is PASSED via a documented, previously-recorded human override (UAT Test 7) — not re-litigated here per the project's own HONEST-OUTCOME GUARD — but flagged because the sign-off document describing that decision is part of the same staleness gap.

**Recommended next step:** a small gap-closure plan (regenerate `01-SIGNOFF-REQUEST.md` against the live Amendment A8 `check_targets.py`/`manifest.json` output, following plan 01-15's exact precedent) followed by one fresh `/gsd-verify-work 1` round to grant or withhold visual sign-off on the current 12 QA figures and reaffirm the widened 10-vs-14 FLAG acceptance.

---

_Verified: 2026-07-22T22:30:00Z_
_Verifier: Claude (gsd-verifier)_
