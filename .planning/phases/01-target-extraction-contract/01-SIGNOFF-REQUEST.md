# Phase 1 Human Sign-Off Request: Target Extraction QA Figures

**Requested:** 2026-07-23
**Requested by:** Plan 01-17 (gap-closure regeneration of the plan 01-15 original)
**This document REQUESTS sign-off. It does not grant it.** No checkbox below is ticked, and none may be inferred as approved from this document's existence. Approvals are recorded separately, per the "How to record the outcome" section below.

---

## Current state

Re-derived live in this execution by running `.venv/bin/python scripts/check_targets.py --project_dir .` against the checked-in `processed_data/targets/` artifacts and reading `processed_data/targets/manifest.json` — not transcribed from any prior plan or outcome report.

**Extraction contract in effect:** Amendment A8 on top of Amendments A3 through A7 — `DETREND_POLY_ORDER=4`, `fit_mask=bead_exclusion_mask(...)`, `BEAD_MASK_HEIGHT_FRACTION=HALF_MAX_FRACTION=0.5`, `MAX_TRACKING_GAP_COLUMNS=10`, `max_y_degree=DETREND_MAX_Y_DEGREE=2`, `max_xy_degree=DETREND_MAX_XY_DEGREE=2` on the shared `robust_plane_detrend` call, `MAX_RUN_MERGE_GAP_PIXELS=10`, `MIN_TRACKED_LENGTH_RATIO=0.5` (both unchanged from Amendment A7), plus (new in Amendment A8) `halfmax_edges` applies the D-01/D-03 clip-exclusion test to each raw run BEFORE `merge_adjacent_runs` is called, and gates tracked selection of a lone same-column-plausible candidate by a joint far-AND-small check against the runtime-derived `previous_length_mm` — applied identically to all four tracks with no per-track branch.

**Artifact generation this document describes:** `run_id` `b3f79f207cc1431fa238bb153c04419b`, published `2026-07-23T02:43:48.290492+00:00`, `extraction_params_sha256` `773a25a388dae2954495e4b6f67b2a8c1c7664de01bbb56c005a8bc0e3051c08` (from `processed_data/targets/manifest.json`, read live in this execution). This `extraction_params_sha256` value is UNCHANGED from the prior (Amendment A7) generation's digest, because Amendment A8 introduced no new named constant (per `01-CONTEXT.md`'s Amendment A8 record) — so the digest alone cannot distinguish this generation from the previous one; `run_id` is the field that identifies which generation a reader is looking at, and a reader must not infer currency from a matching digest.

**Live results (verbatim from `.venv/bin/python scripts/check_targets.py --project_dir .`, run in this execution):**

```
track  power_W  valid_bins  median_mm  mean_mm
    8      400         368     0.7653   0.7889
   10      350         232     0.3940   0.4044
   14      300         309     0.7122   0.7396
   21      200         338     0.6308   0.6512
Ordering 8 vs 10: 0.7653 mm > 0.3940 mm — PASS
Ordering 10 vs 14: 0.3940 mm > 0.7122 mm — FLAG
Ordering 14 vs 21: 0.7122 mm > 0.6308 mm — PASS
Ordering FLAG outcomes are documented and never used to tune locked extraction constants.
ALL CHECKS PASSED
```

**Exit code: 0**, confirmed live in this execution — `check_targets.py` printed `ALL CHECKS PASSED` as the final line of its own stdout, reproduced verbatim above.

**Coverage against the 50% `MIN_VALID_FRACTION` floor (all four tracks clear it):**

| track | power (W) | valid bins | valid fraction | vs 50% floor |
|---|---:|---:|---:|---|
| 8 | 400 | 368 | 92.00% | PASS |
| 10 | 350 | 232 | 58.00% | PASS (margin widened from Amendment A7's razor-thin 50.50%) |
| 14 | 300 | 309 | 77.25% | PASS |
| 21 | 200 | 338 | 84.50% | PASS |

Track 10's margin above the hard `MIN_VALID_FRACTION = 0.5` floor is **58.00%** — 32 bins clear of the 200-bin floor. This is a materially more comfortable margin than the razor-thin 50.50% (202/400, 2 bins clear) that the prior (Amendment A7) generation held, per `01-16-ORDERING-OUTCOME.md`'s coverage table, which measured track 10's valid-bin count rising from 202 to 232 (+30 bins) under Amendment A8. The live number is honestly better than the prior generation's, and is reported at its live value rather than kept pessimistic for continuity.

**Plain-language state:**
- The 8 > 10 > 14 > 21 width ordering does **not** hold. 8-vs-10 PASSes (0.7653 mm > 0.3940 mm) and 14-vs-21 PASSes (0.7122 mm > 0.6308 mm), but the 10-vs-14 pair FLAGs: track 10's median (0.3940 mm) remains below track 14's median (0.7122 mm).
- The current absolute 10-vs-14 gap is **0.3182 mm** (0.7122 mm − 0.3940 mm), and this gap **WIDENED** under Amendment A8 rather than narrowing or closing — up from 0.2404 mm at the prior (Amendment A7) generation this document previously described. `01-16-ORDERING-OUTCOME.md`'s "## Verdict" section is the source of this before-to-after comparison. The gap is not described as narrowing, closing, or improving anywhere in this document.
- `check_targets.py` passes (exit 0, `ALL CHECKS PASSED`) because the coverage-floor gate — the only hard gate it enforces — is cleared by all four tracks. It does not gate on the width-ordering FLAG; that is reported as diagnostic output, not a pass/fail check.
- Track 10's coverage is **not** a closed concern, but it did improve honestly: it moved from a razor-thin 50.50% margin under Amendment A7 to **58.00%** under Amendment A8 (per `01-16-ORDERING-OUTCOME.md`'s coverage table) — still the tightest margin of the four tracks, but no longer razor-thin.
- Boundary fragmentation improved under Amendment A8 on three of four tracks and got marginally worse on one, per `01-16-ORDERING-OUTCOME.md`'s fragmentation-count table: contiguous valid-run counts improved on track 21 (43→21, the largest improvement, −51%), track 8 (25→19), and track 14 (61→56), while track 10 got marginally worse (67→68, +1 run). Max adjacent-column jump statistics improved on 7 of the 8 track/boundary pairs measured, worsening only on track 8's lower boundary and track 10's upper boundary. This is not a uniform improvement and fragmentation is not fixed.
- Mechanism C (the greedy nearest-to-`previous_center` selection among simultaneously-plausible candidates) was **not** addressed by Amendment A8. It remains the explicitly-deferred DP/Viterbi joint-tracker gap, and its residual effect is still visible as column-to-column width instability at both domain far edges, per `01-16-ORDERING-OUTCOME.md`'s "## Mechanism C's residual effect" section.

---

## Contract in effect

The following constants govern extraction identically across all four tracks (no per-track branch or tuned value exists anywhere in `src/targets.py`, `src/nsf_fmrg_data.py`, or `scripts/run_target_extraction.py` — confirmed by `grep -n "track_id =="` returning nothing):

| Constant | Value | Fixed from |
|---|---|---|
| `DETREND_POLY_ORDER` | 4 | Amendment A3 — measured per-track residual-variance evidence (quadratic explained 97.7%/96.3% of track 8/14 residual variance but only 46.9%/29.5% for tracks 10/21; quartic raised those to 64.0%/44.9%), fixed a priori from that evidence before any new QA figure was generated. |
| `BEAD_MASK_HEIGHT_FRACTION` | 0.5 (= `HALF_MAX_FRACTION`) | Amendment A4 — fixed from the D-01/D-03 half-max definition already in the contract (a pixel classified "bead" by the half-max width convention must not bias the detrend fit), not from the resulting width ordering. |
| `MAX_TRACKING_GAP_COLUMNS` | 10 | Amendment A4 — continuity-tracking stale-anchor expiry rule, applied identically to all four tracks. |
| `DETREND_MAX_Y_DEGREE` | 2 | Amendment A5 — fixed from `01-11-CRITERION.md`'s pre-registered 0.05mm fitted-surface edge-departure tolerance, measured against Task 1's fitted-surface evidence: cap 2 is the *largest* cross-track degree cap that clears the tolerance on all four tracks (cap 3 leaves one track at 0.0665mm, still above tolerance; cap 2 brings every track's largest departure to 0.0238mm). |
| `DETREND_MAX_XY_DEGREE` | 2 | Amendment A6 — fixed from `01-13-CRITERION.md`'s pre-registered 0.012 mm x-direction shape-gap tolerance measured on all four tracks' real data: cap 2 is the largest cross-term x-exponent cap that clears it (cap 3 leaves track 10 at 0.0212 mm, above tolerance; cap 2 brings it to 0.0118 mm). Fixed before the ordering outcome was inspected. |
| `MAX_RUN_MERGE_GAP_PIXELS` | 10 | Amendment A7 — not a new number: reused from the already-locked `MAX_GAP_PIXELS`, applying the D-05/D-06 judgment that a stretch of at most 10 native pixels below criterion is not a genuine break, now applied to post-threshold run fragmentation instead of raw NaN gaps. |
| `MIN_TRACKED_LENGTH_RATIO` | 0.5 | Amendment A7 — not a new number: reused from the already-locked `HALF_MAX_FRACTION`, applying the D-01/D-03 half-max convention's own fraction to candidate plausibility — a tracked candidate shorter than half the largest same-column alternative is not a plausible competing feature. |
| Clip-before-merge reordering in `halfmax_edges` | Reordering of two existing steps — introduces no new named constant | Amendment A8 — the D-01/D-03 boundary-clip-exclusion test is now applied to each raw run (`all_true_runs(above)`'s output) BEFORE `merge_adjacent_runs` is called, so a merged candidate can structurally never itself touch a y-strip boundary. |
| History-based joint far-AND-small gate in `halfmax_edges` | Reuses `MIN_TRACKED_LENGTH_RATIO` against the runtime-derived `previous_length_mm` — introduces no new named constant | Amendment A8 — a lone same-column-plausible candidate is rejected only when it is BOTH farther from `previous_center` than the recently-tracked run's own physical width (`previous_length_mm`) AND smaller than `MIN_TRACKED_LENGTH_RATIO` of that same width. |

Each of these nine rows was fixed from residual, physical, numerical, or already-locked-contract evidence recorded in `01-CONTEXT.md`'s Amendments A3 through A8 **before** the ordering outcome above was inspected, and none has been adjusted in response to whether `8 > 10 > 14 > 21` passes. This is the judgment-tier prohibition from `01-SPEC.md` ("Extraction contract constants must NOT be adjusted based on whether the resulting width ordering or QA plots look correct") that this sign-off request asks the reviewer to confirm — for Amendments A3 through A8 — alongside the figure-specific questions below. Amendment A8 deliberately introduced no new named constant, which is why `extraction_params()` still returns the same 19 keys (matching `processed_data/targets/extraction_params.json` exactly) and this document's `extraction_params_sha256` (`773a25a388dae2954495e4b6f67b2a8c1c7664de01bbb56c005a8bc0e3051c08`) is unchanged from the previous generation.

---

## Figures to inspect

Before opening any figure: `01-16-ORDERING-OUTCOME.md` measured, under Amendment A8: valid-bin coverage increased on every track (368/232/309/338, up from the prior generation's 361/202/301/308); contiguous-run fragmentation improved on three of four tracks (track 21 −51%, the largest improvement; track 8 −6; track 14 −5) and got marginally worse on track 10 (+1, 67→68); jump statistics are mixed (7 of 8 track/boundary pairs improved or held steady, 2 worsened); and both crop-edge symptoms UAT gap G-01-6 named (track 10's isolated valid run, track 21's near-zero terminal drop) are resolved. Mechanism C's residual far-edge column-to-column width instability was **NOT** addressed by Amendment A8 and remains visible. Your job below is to judge whether that residual jitter is acceptable under the D-14 / success-criterion-3 standard — not to confirm that Amendment A8 fixed it.

All 12 regenerated QA figures live under `processed_data/targets/qa/`. Each path below has its own concrete acceptance question — please open each image at full resolution.

### Residual maps

- `processed_data/targets/qa/track_8_residual_map.png`
- `processed_data/targets/qa/track_10_residual_map.png`
- `processed_data/targets/qa/track_14_residual_map.png`
- `processed_data/targets/qa/track_21_residual_map.png`

**Question for each:** Is the remaining post-detrend structure acceptable process and substrate variation, rather than the coherent track-wide end-positive / centre-negative bow reported in UAT Test 1? Is there no manufactured height feature hugging the y-strip edge (the specific artifact plan 01-11 diagnosed and fixed on track 10)? Amendment A8 touched candidate selection in `halfmax_edges`, not the detrend surface fit — all four surfaces are still produced under the Amendment A6 cross-term cap (`DETREND_MAX_XY_DEGREE=2`) unchanged since the last review, so a difference here versus the previously-reviewed generation would itself be a finding.

### Boundary overlays

- `processed_data/targets/qa/track_8_overlay.png`
- `processed_data/targets/qa/track_10_overlay.png`
- `processed_data/targets/qa/track_14_overlay.png`
- `processed_data/targets/qa/track_21_overlay.png`

**Question for each:** Do the upper and lower boundary traces follow the physical bead continuously across the 20-100 mm span on every track including track 10, without the sawtooth or EKG-like cross-track jumps reported in UAT Test 2? Are invalid regions shown as explicit grey shading rather than silently bridged or dropped? `01-16-ORDERING-OUTCOME.md` reports, under Amendment A8: contiguous valid-run counts improved on tracks 21 (43→21, −51%, the largest improvement), 8 (25→19), and 14 (61→56), and got marginally worse on track 10 (67→68, +1); track 8 retains the excursion regions UAT gap G-01-6's `reason:` field named (~24-27, 48-55, 81-86, 97-100mm). Please confirm or dispute these specific observations.

### Width curves

- `processed_data/targets/qa/track_8_width.png`
- `processed_data/targets/qa/track_10_width.png`
- `processed_data/targets/qa/track_14_width.png`
- `processed_data/targets/qa/track_21_width.png`

**Question for each:** Inside the orange-shaded 0.5 mm crop-edge bands at 20 mm and 100 mm, is the edge behaviour physically plausible? `01-16-ORDERING-OUTCOME.md`'s crop-edge last-6-grid-point inspection found both previously-cited symptoms resolved: track 10's isolated-valid-run in the right band is gone (all 6 of the last grid points, x=98.9-99.9mm, are now valid with no surrounding gaps), and track 21's near-zero terminal drop is gone (the terminal three points now read 0.650/0.403/0.405mm, a milder taper rather than a near-total collapse). However, column-to-column width instability persists at both far edges as Mechanism C's residual, explicitly-deferred effect (track 10: 0.126→0.124→0.257→0.343→0.318→0.036mm; track 21: 0.740→0.877→0.713→0.650→0.403→0.405mm) — please judge whether this residual jitter is acceptable, not whether it has been eliminated. All four tracks' left crop-edge bands remain an expected, already-locked native-data-availability limitation (`MIN_COLUMNS_PER_BIN` / `MAX_GAP_PIXELS`), not a defect — please do not re-report it as one.

---

## Decisions requested

All decision items below are unticked except the one already-recorded human decision preserved verbatim below. Ticking a new item is a human action taken outside this document, recorded per "How to record the outcome" below — not something this plan may do on the reviewer's behalf.

- [ ] **Residual maps acceptable for all four tracks.** Closes UAT Test 1 and Human Verification item 1 (visual sign-off on the 12 regenerated Amendment A8 QA figures) from `01-VERIFICATION.md`.
  - Yes = the remaining post-detrend structure on all four tracks (regenerated under Amendment A8) is scientifically acceptable process/substrate variation, with no coherent track-wide bow and no manufactured edge feature.
  - No = at least one track still shows unacceptable systematic residual structure; a new gap-closure plan is needed.

- [ ] **Boundary overlays acceptable for all four tracks including track 10.** Closes UAT Test 2, UAT gap G-01-6, and Human Verification item 1 (visual sign-off on the 12 regenerated Amendment A8 QA figures) from `01-VERIFICATION.md`.
  - Yes = all four boundary traces (regenerated under Amendment A8) are continuous and physically plausible, with no unacceptable sawtooth/EKG-like jumps, invalid regions are explicitly shaded rather than bridged or dropped, and the residual far-edge jitter documented above (Mechanism C, not fixed by A8) is judged acceptable.
  - No = at least one track's boundary trace is still unacceptably jagged, fragmented, or silently bridges a gap; a new gap-closure plan is needed.

- [ ] **Crop-edge behaviour acceptable for all four tracks.** Closes UAT Test 3, UAT gap G-01-6, and Human Verification item 1 (visual sign-off on the 12 regenerated Amendment A8 QA figures) from `01-VERIFICATION.md`.
  - Yes = the 0.5 mm crop-edge bands at 20 mm and 100 mm show physically plausible behaviour on all four tracks (regenerated under Amendment A8); track 10's isolated-valid-run symptom and track 21's near-zero terminal drop are confirmed gone; and the residual far-edge width instability documented above (Mechanism C) is judged acceptable.
  - No = at least one track still shows an implausible crop-edge artifact; a new gap-closure plan is needed.

- [ ] **Constants confirmed fixed independently of outcome inspection.** Closes the `01-SPEC.md` judgment-tier prohibition, UAT Test 4, and Human Verification item 1 (visual sign-off on the 12 regenerated Amendment A8 QA figures) from `01-VERIFICATION.md`.
  - Yes = the reviewer confirms, from `01-CONTEXT.md`'s Amendments A3 through A8 and this document's "Contract in effect" section, that all seven locked constants (`DETREND_POLY_ORDER`, `BEAD_MASK_HEIGHT_FRACTION`, `MAX_TRACKING_GAP_COLUMNS`, `DETREND_MAX_Y_DEGREE`, `DETREND_MAX_XY_DEGREE`, `MAX_RUN_MERGE_GAP_PIXELS`, `MIN_TRACKED_LENGTH_RATIO`) plus Amendment A8's two no-new-constant behavioral rules were each fixed from residual/physical/numerical/already-locked-contract evidence before the ordering outcome was inspected, and none was tuned to force `8 > 10 > 14 > 21` to pass.
  - No = the reviewer finds evidence that a constant or behavioral rule was chosen or adjusted because of its effect on the ordering outcome; this is an integrity finding, not a normal gap-closure item, and should be escalated accordingly.

- [x] **Width-ordering override vs. further investigation** (applies because the 10-vs-14 pair currently FLAGs — see "Current state" above). Closes Human Verification item 2 (the 10-vs-14 decision) from `01-VERIFICATION.md`. Current position (updated live in this execution — see "Current state" above): track 10's median (0.3940 mm) remains below track 14's (0.7122 mm); the absolute gap is now **0.3182 mm**; track 10's coverage is now 232/400 (58.00%), no longer razor-thin. The gap has widened further, from the 0.2404 mm magnitude this override was originally selected against, per `01-16-ORDERING-OUTCOME.md`'s "## Verdict" section — see the new reaffirmation item below for the human's response to that widened magnitude. **Both `01-13-ORDERING-OUTCOME.md` and `01-14-ORDERING-OUTCOME.md` explicitly recommend option (a)** — stated here immediately alongside the worsened gap number, not separately. Choose exactly one:
  - **(a) Human override — SELECTED (2026-07-22, via `/gsd-verify-work 1` Test 7).** Accept the 10-vs-14 FLAG as a documented, known limitation of the current contract, record the rationale, and proceed to Phase 2 with this caveat carried in `ROADMAP.md`/`REQUIREMENTS.md`. Reviewer's rationale: four investigation cycles have addressed independently diagnosed defect classes; the latest two (01-13, 01-14) produced genuine, verified fixes without outcome-driven tuning; the expected ordering still does not hold and the gap increased to 0.2404 mm; track 10 coverage remains technically valid but marginal at 50.50%. Recorded as FLAG-accepted, not PASS — valid detrending and boundary-tracker fixes are retained, further ordering-related tuning is frozen, and this is reopened only if a new independently-supported root-cause hypothesis emerges. Track 10's near-floor coverage remains explicitly noted as an open risk, not a closed concern.
  - (b) Further diagnosed-defect investigation — commission a new gap-closure plan to investigate the 10-vs-14 relationship further before accepting it as a limitation. Note: the phase's HONEST-OUTCOME GUARD states no further open-ended tuning cycle is authorized absent a new, independently-diagnosed root cause.

- [ ] **Reaffirm the 10-vs-14 width-ordering acceptance at the widened magnitude.** Closes Human Verification item 2 (reaffirm, not reopen, the 10-vs-14 FLAG acceptance given the widened gap) from `01-VERIFICATION.md`. This is NOT a new investigation cycle and NOT a reopening of the decision above — it asks for a brief recorded confirmation that the already-accepted rationale (option (a), 2026-07-22) still applies now that the gap has widened to 0.3182 mm (from 0.2404 mm) and track 10's coverage has moved to 58.00% (from 50.50%) under Amendment A8. The phase's HONEST-OUTCOME GUARD authorizes no further open-ended tuning absent a new, independently-diagnosed root cause; four such investigation cycles (01-06 through 01-08, 01-11, 01-13, 01-16) have already been run.
  - Yes = the reviewer reaffirms the option (a) acceptance stands at the widened magnitude; no further investigation is commissioned.
  - No = the reviewer finds the widened magnitude changes their assessment; this reopens Human Verification item 2 and requires a new, independently-diagnosed root cause before any further tuning, per the HONEST-OUTCOME GUARD.

---

## How to record the outcome

Approvals, rejections, or issues found while reviewing these figures are recorded through `/gsd-verify-work 1` run against this phase (Phase 1), not by editing this document. `TARGET-02`'s checkbox and traceability row in `.planning/REQUIREMENTS.md` flip from their current "awaiting human visual sign-off" state to complete only after that record exists — this plan (01-17) does not and cannot make that change itself. `01-UAT.md`'s G-01-6 gap entry likewise moves off its current `status: failed` state only as an outcome of that same human round.

---

## Closing note

If any item above is rejected, the correct response is a new gap-closure plan targeting the specific rejected item — not an edit to this document and not a retry of the extraction pipeline hoping for a different outcome. Under no circumstances may a locked extraction constant (`DETREND_POLY_ORDER`, `BEAD_MASK_HEIGHT_FRACTION`, `MAX_TRACKING_GAP_COLUMNS`, `DETREND_MAX_Y_DEGREE`, `DETREND_MAX_XY_DEGREE`, `MAX_RUN_MERGE_GAP_PIXELS`, `MIN_TRACKED_LENGTH_RATIO`), Amendment A8's clip-before-merge reordering or history-based joint gate, the `MIN_VALID_FRACTION` floor, or the boundary-clipped-run exclusion in `halfmax_edges` be adjusted to make a figure look better in response to this sign-off request. Any such change must instead be justified independently, on residual/physical/numerical or already-locked-contract evidence, following the same pre-registered, outcome-independent discipline documented in Amendments A3 through A8.
