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

Each of these seven constants was fixed from residual, physical, numerical, or already-locked-contract evidence recorded in `01-CONTEXT.md`'s Amendments A3 through A7 **before** the ordering outcome above was inspected, and none has been adjusted in response to whether `8 > 10 > 14 > 21` passes. This is the judgment-tier prohibition from `01-SPEC.md` ("Extraction contract constants must NOT be adjusted based on whether the resulting width ordering or QA plots look correct") that this sign-off request asks the reviewer to confirm, alongside the figure-specific questions below. `extraction_params()` now returns 19 keys, matching `processed_data/targets/extraction_params.json` exactly, and this document's `extraction_params_sha256` (`773a25a388dae2954495e4b6f67b2a8c1c7664de01bbb56c005a8bc0e3051c08`) is the provenance digest of exactly that set.

---

## Figures to inspect

Before opening any figure: `01-14-ORDERING-OUTCOME.md` and `01-VERIFICATION.md` already found that gap handling is correct on every track (explicit grey shading, no silently bridged invalid regions), but fragmentation and abrupt single-column jumps persist, and the aggregate fragmentation and jump-statistic metrics did **NOT** uniformly improve under Amendment A7. Your job below is to judge whether that residual jitter is acceptable under the D-14 / success-criterion-3 standard — not to confirm that A7 fixed it.

All 12 regenerated QA figures live under `processed_data/targets/qa/`. Each path below has its own concrete acceptance question — please open each image at full resolution.

### Residual maps

- `processed_data/targets/qa/track_8_residual_map.png`
- `processed_data/targets/qa/track_10_residual_map.png`
- `processed_data/targets/qa/track_14_residual_map.png`
- `processed_data/targets/qa/track_21_residual_map.png`

**Question for each:** Is the remaining post-detrend structure acceptable process and substrate variation, rather than the coherent track-wide end-positive / centre-negative bow reported in UAT Test 1? Is there no manufactured height feature hugging the y-strip edge (the specific artifact plan 01-11 diagnosed and fixed on track 10)? All four surfaces are now produced under the Amendment A6 cross-term cap (`DETREND_MAX_XY_DEGREE=2`), so you are judging the A6/A7 surface, not the A5 one.

### Boundary overlays

- `processed_data/targets/qa/track_8_overlay.png`
- `processed_data/targets/qa/track_10_overlay.png`
- `processed_data/targets/qa/track_14_overlay.png`
- `processed_data/targets/qa/track_21_overlay.png`

**Question for each:** Do the upper and lower boundary traces follow the physical bead continuously across the 20-100 mm span on every track including track 10, without the sawtooth or EKG-like cross-track jumps reported in UAT Test 2? Are invalid regions shown as explicit grey shading rather than silently bridged or dropped? `01-14-ORDERING-OUTCOME.md` reports: track 10's post-70mm sustained near-zero-width lock is gone, but its trace remains heavily fragmented across the full 28-80mm span; tracks 8 and 14 retain frequent abrupt near-zero-width excursions (track 8 near x=24-27mm and x=97-99mm). Please confirm or dispute these specific observations.

### Width curves

- `processed_data/targets/qa/track_8_width.png`
- `processed_data/targets/qa/track_10_width.png`
- `processed_data/targets/qa/track_14_width.png`
- `processed_data/targets/qa/track_21_width.png`

**Question for each:** Inside the orange-shaded 0.5 mm crop-edge bands at 20 mm and 100 mm, is the edge behaviour physically plausible, and specifically is track 10's terminal V-spike from UAT Test 3 gone? Tracks 14 and 21 were substantially reshaped under Amendment A7 (track 14's median rose to 0.6174 mm, track 21's to 0.3825 mm), so their curves differ materially from the generation previously reviewed.

---

## Decisions requested

Every checkbox below is unticked. Ticking one is a human action taken outside this document, recorded per "How to record the outcome" below — not something this plan may do on the reviewer's behalf.

- [ ] **Residual maps acceptable for all four tracks.** Closes UAT Test 1 and Human Verification item 2 (visual sign-off across all 12 QA figures) from `01-VERIFICATION.md`.
  - Yes = the remaining post-detrend structure on all four tracks is scientifically acceptable process/substrate variation, with no coherent track-wide bow and no manufactured edge feature.
  - No = at least one track still shows unacceptable systematic residual structure; a new gap-closure plan is needed.

- [ ] **Boundary overlays acceptable for all four tracks including track 10.** Closes UAT Test 2 and Human Verification item 2 (visual sign-off across all 12 QA figures) from `01-VERIFICATION.md`.
  - Yes = all four boundary traces are continuous and physically plausible, with no sawtooth/EKG-like jumps, and invalid regions are explicitly shaded rather than bridged or dropped.
  - No = at least one track's boundary trace is still unacceptably jagged, fragmented, or silently bridges a gap; a new gap-closure plan is needed.

- [ ] **Crop-edge behaviour acceptable for all four tracks.** Closes UAT Test 3 and Human Verification item 2 (visual sign-off across all 12 QA figures) from `01-VERIFICATION.md`.
  - Yes = the 0.5 mm crop-edge bands at 20 mm and 100 mm show physically plausible behaviour on all four tracks, and track 10's terminal V-spike is confirmed gone.
  - No = at least one track still shows an implausible crop-edge artifact; a new gap-closure plan is needed.

- [ ] **Constants confirmed fixed independently of outcome inspection.** Closes the `01-SPEC.md` judgment-tier prohibition, UAT Test 4, and Human Verification item 2 (visual sign-off across all 12 QA figures) from `01-VERIFICATION.md`.
  - Yes = the reviewer confirms, from `01-CONTEXT.md`'s Amendments A3-A7 and this document's "Contract in effect" section, that all seven locked constants (`DETREND_POLY_ORDER`, `BEAD_MASK_HEIGHT_FRACTION`, `MAX_TRACKING_GAP_COLUMNS`, `DETREND_MAX_Y_DEGREE`, `DETREND_MAX_XY_DEGREE`, `MAX_RUN_MERGE_GAP_PIXELS`, `MIN_TRACKED_LENGTH_RATIO`) were each fixed from residual/physical/numerical/already-locked-contract evidence before the ordering outcome was inspected, and none was tuned to force `8 > 10 > 14 > 21` to pass.
  - No = the reviewer finds evidence that a constant was chosen or adjusted because of its effect on the ordering outcome; this is an integrity finding, not a normal gap-closure item, and should be escalated accordingly.

- [x] **Width-ordering override vs. further investigation** (applies because the 10-vs-14 pair currently FLAGs — see "Current state" above). Closes Human Verification item 1 (the 10-vs-14 decision) from `01-VERIFICATION.md`. Current position: track 10's median (0.3770 mm) remains below track 14's (0.6174 mm); the absolute gap is **0.2404 mm** and **roughly doubled** under Amendments A6/A7 rather than narrowing; track 10's coverage is now 202/400 (50.50%), a razor-thin margin above the 50% floor. **Both `01-13-ORDERING-OUTCOME.md` and `01-14-ORDERING-OUTCOME.md` explicitly recommend option (a)** — stated here immediately alongside the worsened gap number, not separately. Choose exactly one:
  - **(a) Human override — SELECTED (2026-07-22, via `/gsd-verify-work 1` Test 7).** Accept the 10-vs-14 FLAG as a documented, known limitation of the current contract, record the rationale, and proceed to Phase 2 with this caveat carried in `ROADMAP.md`/`REQUIREMENTS.md`. Reviewer's rationale: four investigation cycles have addressed independently diagnosed defect classes; the latest two (01-13, 01-14) produced genuine, verified fixes without outcome-driven tuning; the expected ordering still does not hold and the gap increased to 0.2404 mm; track 10 coverage remains technically valid but marginal at 50.50%. Recorded as FLAG-accepted, not PASS — valid detrending and boundary-tracker fixes are retained, further ordering-related tuning is frozen, and this is reopened only if a new independently-supported root-cause hypothesis emerges. Track 10's near-floor coverage remains explicitly noted as an open risk, not a closed concern.
  - (b) Further diagnosed-defect investigation — commission a new gap-closure plan to investigate the 10-vs-14 relationship further before accepting it as a limitation. Note: the phase's HONEST-OUTCOME GUARD states no further open-ended tuning cycle is authorized absent a new, independently-diagnosed root cause.

---

## How to record the outcome

Approvals, rejections, or issues found while reviewing these figures are recorded through `/gsd-verify-work 1` run against this phase (Phase 1), not by editing this document. `TARGET-02`'s checkbox and traceability row in `.planning/REQUIREMENTS.md` flip from their current "awaiting human visual sign-off" state to complete only after that record exists — this plan (01-15) does not and cannot make that change itself.

---

## Closing note

If any item above is rejected, the correct response is a new gap-closure plan targeting the specific rejected item — not an edit to this document and not a retry of the extraction pipeline hoping for a different outcome. Under no circumstances may a locked extraction constant (`DETREND_POLY_ORDER`, `BEAD_MASK_HEIGHT_FRACTION`, `MAX_TRACKING_GAP_COLUMNS`, `DETREND_MAX_Y_DEGREE`, `DETREND_MAX_XY_DEGREE`, `MAX_RUN_MERGE_GAP_PIXELS`, `MIN_TRACKED_LENGTH_RATIO`), the `MIN_VALID_FRACTION` floor, or the boundary-clipped-run exclusion in `halfmax_edges` be adjusted to make a figure look better in response to this sign-off request. Any such change must instead be justified independently, on residual/physical/numerical or already-locked-contract evidence, following the same pre-registered, outcome-independent discipline documented in Amendments A3 through A7.
