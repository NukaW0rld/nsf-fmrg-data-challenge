# Phase 1 Human Sign-Off Request: Target Extraction QA Figures

**Requested:** 2026-07-22
**Requested by:** Plan 01-15 (gap-closure regeneration of the plan 01-12 original)
**This document REQUESTS sign-off. It does not grant it.** No checkbox below is ticked, and none may be inferred as approved from this document's existence. Approvals are recorded separately, per the "How to record the outcome" section below.

---

## Current state

Re-derived live in this execution by running `.venv/bin/python scripts/check_targets.py --project_dir .` against the checked-in `processed_data/targets/` artifacts and reading `processed_data/targets/manifest.json` — not transcribed from any prior plan or outcome report.

**Extraction contract in effect:** Amendment A7 on top of A3/A4/A5/A6 — `DETREND_POLY_ORDER=4`, `fit_mask=bead_exclusion_mask(...)`, `BEAD_MASK_HEIGHT_FRACTION=HALF_MAX_FRACTION=0.5`, `MAX_TRACKING_GAP_COLUMNS=10`, `max_y_degree=DETREND_MAX_Y_DEGREE=2`, `max_xy_degree=DETREND_MAX_XY_DEGREE=2` on the shared `robust_plane_detrend` call, plus `halfmax_edges` merging adjacent above-half-max sub-runs separated by at most `MAX_RUN_MERGE_GAP_PIXELS=10` samples and gating tracked selection to candidates at least `MIN_TRACKED_LENGTH_RATIO=0.5` of the largest same-column candidate — applied identically to all four tracks with no per-track branch.

**Artifact generation this document describes:** `run_id` `99a4e8472f0a4164938363af0725f31b`, published `2026-07-22T03:30:49.258468+00:00`, `extraction_params_sha256` `773a25a388dae2954495e4b6f67b2a8c1c7664de01bbb56c005a8bc0e3051c08` (from `processed_data/targets/manifest.json`, read live in this execution).

**Live results (verbatim from `.venv/bin/python scripts/check_targets.py --project_dir .`, run in this execution):**

```
track  power_W  valid_bins  median_mm  mean_mm
    8      400         361     0.7401   0.7414
   10      350         202     0.3770   0.3744
   14      300         301     0.6174   0.6529
   21      200         308     0.3825   0.4130
Ordering 8 vs 10: 0.7401 mm > 0.3770 mm — PASS
Ordering 10 vs 14: 0.3770 mm > 0.6174 mm — FLAG
Ordering 14 vs 21: 0.6174 mm > 0.3825 mm — PASS
Ordering FLAG outcomes are documented and never used to tune locked extraction constants.
```

**`check_targets.py --project_dir .` exit code: 0** (`ALL CHECKS PASSED` printed, confirmed live in this execution).

**Coverage against the 50% `MIN_VALID_FRACTION` floor (all four tracks clear it):**

| track | power (W) | valid bins | valid fraction | vs 50% floor |
|---|---:|---:|---:|---|
| 8 | 400 | 361 | 90.25% | PASS |
| 10 | 350 | 202 | 50.50% | PASS (razor-thin margin — see below) |
| 14 | 300 | 301 | 75.25% | PASS |
| 21 | 200 | 308 | 77.00% | PASS |

Track 10's 50.50% clears the hard `MIN_VALID_FRACTION = 0.5` floor by only 0.5 percentage points — a margin of 2 bins (202 valid bins against the 200-bin floor) — a **razor-thin margin**, materially tighter than the 60.75% track 10 held under Amendment A6 (`01-13-ORDERING-OUTCOME.md`). This follows `01-14-ORDERING-OUTCOME.md`'s measured 41-bin drop (243 → 202) under Amendment A7's merge-and-plausibility-gate fix.

**Plain-language state:**
- The 8 > 10 > 14 > 21 width ordering does **not** hold. 8-vs-10 PASSes and 14-vs-21 PASSes, but the 10-vs-14 pair FLAGs: track 10's median (0.3770 mm) remains below track 14's median (0.6174 mm).
- The current absolute 10-vs-14 gap is **0.2404 mm**, and this gap has **roughly doubled** under Amendments A6 and A7 — from 0.1052 mm at the Amendment-A5 generation this document previously described — rather than narrowing. The gap is not described as narrowing, closing, or improving anywhere in this document.
- `check_targets.py` passes (exit 0, `ALL CHECKS PASSED`) because the coverage-floor gate — the only hard gate it enforces — is cleared by all four tracks. It does not gate on the width-ordering FLAG; that is reported as diagnostic output, not a pass/fail check.
- Track 10's coverage is **not** a closed concern. It moved from a collapse (21/400, 5.2%), through a comfortable margin under Amendments A5 and A6 (Amendment A6's margin was 60.75%, per `01-13-ORDERING-OUTCOME.md`), to **50.50%** under Amendment A7 — still passing the floor, but now the tightest margin of the four tracks and the one most at risk from any future change.
- Boundary fragmentation is a **MIXED** outcome, not uniformly improved, under Amendment A7 (`01-14-ORDERING-OUTCOME.md`): contiguous valid-run counts worsened on track 8 (22→25), track 10 (65→67), and track 21 (34→43), and improved only marginally on track 14 (63→61); max adjacent-column jump statistics improved on some boundaries (e.g. both of track 10's) while worsening on others (including both of track 8's). Baseline caveat: the pre-fix numbers above were measured under Amendment A5, so part of this delta reflects Amendment A6's already-accepted effect rather than Amendment A7 alone.

---

## Contract in effect

The following constants govern extraction identically across all four tracks (no per-track branch or tuned value exists anywhere in `src/targets.py`, `src/nsf_fmrg_data.py`, or `scripts/run_target_extraction.py` — confirmed by `grep -n "track_id =="` returning nothing):

| Constant | Value | Fixed from |
|---|---|---|
| `DETREND_POLY_ORDER` | 4 | Amendment A3 — measured per-track residual-variance evidence (quadratic explained 97.7%/96.3% of track 8/14 residual variance but only 46.9%/29.5% for tracks 10/21; quartic raised those to 64.0%/44.9%), fixed a priori from that evidence before any new QA figure was generated. |
| `BEAD_MASK_HEIGHT_FRACTION` | 0.5 (= `HALF_MAX_FRACTION`) | Amendment A4 — fixed from the D-01/D-03 half-max definition already in the contract (a pixel classified "bead" by the half-max width convention must not bias the detrend fit), not from the resulting width ordering. |
| `MAX_TRACKING_GAP_COLUMNS` | 10 | Amendment A4 — continuity-tracking stale-anchor expiry rule, applied identically to all four tracks. |
| `DETREND_MAX_Y_DEGREE` (Amendment A5 constant) | 2 | Amendment A5 — fixed from `01-11-CRITERION.md`'s pre-registered 0.05mm fitted-surface edge-departure tolerance, measured against Task 1's fitted-surface evidence: cap 2 is the *largest* cross-track degree cap that clears the tolerance on all four tracks (cap 3 leaves one track at 0.0665mm, still above tolerance; cap 2 brings every track's largest departure to 0.0238mm). |

Each of these four constants was fixed from residual, physical, or numerical evidence recorded in `01-CONTEXT.md`'s Amendments A3/A4/A5 **before** the ordering outcome above was inspected, and none has been adjusted in response to whether `8 > 10 > 14 > 21` passes. This is the judgment-tier prohibition from `01-SPEC.md` ("Extraction contract constants must NOT be adjusted based on whether the resulting width ordering or QA plots look correct") that this sign-off request asks the reviewer to confirm, alongside the figure-specific questions below.

---

## Figures to inspect

All 12 regenerated QA figures live under `processed_data/targets/qa/`. Each path below has its own concrete acceptance question — please open each image at full resolution.

### Residual maps

- `processed_data/targets/qa/track_8_residual_map.png`
- `processed_data/targets/qa/track_10_residual_map.png`
- `processed_data/targets/qa/track_14_residual_map.png`
- `processed_data/targets/qa/track_21_residual_map.png`

**Question for each:** Is the remaining post-detrend structure acceptable process and substrate variation, rather than the coherent track-wide end-positive / centre-negative bow reported in UAT Test 1? Is there no manufactured height feature hugging the y-strip edge (the specific artifact plan 01-11 diagnosed and fixed on track 10)?

### Boundary overlays

- `processed_data/targets/qa/track_8_overlay.png`
- `processed_data/targets/qa/track_10_overlay.png`
- `processed_data/targets/qa/track_14_overlay.png`
- `processed_data/targets/qa/track_21_overlay.png`

**Question for each:** Do the upper and lower boundary traces follow the physical bead continuously across the 20-100 mm span on every track including track 10, without the sawtooth or EKG-like cross-track jumps reported in UAT Test 2? Are invalid regions shown as explicit grey shading rather than silently bridged or dropped?

### Width curves

- `processed_data/targets/qa/track_8_width.png`
- `processed_data/targets/qa/track_10_width.png`
- `processed_data/targets/qa/track_14_width.png`
- `processed_data/targets/qa/track_21_width.png`

**Question for each:** Inside the orange-shaded 0.5 mm crop-edge bands at 20 mm and 100 mm, is the edge behaviour physically plausible, and specifically is track 10's terminal V-spike from UAT Test 3 gone?

---

## Decisions requested

Every checkbox below is unticked. Ticking one is a human action taken outside this document, recorded per "How to record the outcome" below — not something this plan may do on the reviewer's behalf.

- [ ] **Residual maps acceptable for all four tracks.** Closes UAT Test 1 and Human Verification item 2 from `01-VERIFICATION.md`.
  - Yes = the remaining post-detrend structure on all four tracks is scientifically acceptable process/substrate variation, with no coherent track-wide bow and no manufactured edge feature.
  - No = at least one track still shows unacceptable systematic residual structure; a new gap-closure plan is needed.

- [ ] **Boundary overlays acceptable for all four tracks including track 10.** Closes UAT Test 2 and verification truth 4 from `01-VERIFICATION.md`.
  - Yes = all four boundary traces are continuous and physically plausible, with no sawtooth/EKG-like jumps, and invalid regions are explicitly shaded rather than bridged or dropped.
  - No = at least one track's boundary trace is still unacceptably jagged, fragmented, or silently bridges a gap; a new gap-closure plan is needed.

- [ ] **Crop-edge behaviour acceptable for all four tracks.** Closes UAT Test 3.
  - Yes = the 0.5 mm crop-edge bands at 20 mm and 100 mm show physically plausible behaviour on all four tracks, and track 10's terminal V-spike is confirmed gone.
  - No = at least one track still shows an implausible crop-edge artifact; a new gap-closure plan is needed.

- [ ] **Constants confirmed fixed independently of outcome inspection.** Closes the `01-SPEC.md` judgment-tier prohibition and UAT Test 4.
  - Yes = the reviewer confirms, from `01-CONTEXT.md`'s Amendments A3/A4/A5 and this document's "Contract in effect" section, that `DETREND_POLY_ORDER`, `BEAD_MASK_HEIGHT_FRACTION`, `MAX_TRACKING_GAP_COLUMNS`, and `DETREND_MAX_Y_DEGREE` were each fixed from residual/physical/numerical evidence before the ordering outcome was inspected, and none was tuned to force `8 > 10 > 14 > 21` to pass.
  - No = the reviewer finds evidence that a constant was chosen or adjusted because of its effect on the ordering outcome; this is an integrity finding, not a normal gap-closure item, and should be escalated accordingly.

- [ ] **Width-ordering override vs. further investigation** (applies **only** because the 10-vs-14 pair currently FLAGs — see "Current state" above; this decision is not applicable if a future regeneration clears it). Per `01-08-ORDERING-OUTCOME.md`'s original escalation, choose exactly one:
  - **(a) Human override** — accept the 10-vs-14 FLAG as a documented, known limitation of the current contract (track 10's median width, even from its now-representative 242/400 valid positions, remains below track 14's), record the rationale, and proceed to Phase 2 with this caveat carried in `ROADMAP.md`/`REQUIREMENTS.md`.
  - **(b) Further diagnosed-defect investigation** — commission a new gap-closure plan to investigate the 10-vs-14 relationship further before accepting it as a limitation.
  - Neither option is selected here. This document presents both without recommending one.

---

## How to record the outcome

Approvals, rejections, or issues found while reviewing these figures are recorded through `/gsd-verify-work` run against this phase (Phase 1), not by editing this document. `TARGET-02`'s checkbox and traceability row in `.planning/REQUIREMENTS.md` flip from their current "awaiting human visual sign-off" state to complete only after that record exists — this plan (01-12) does not and cannot make that change itself.

---

## Closing note

If any item above is rejected, the correct response is a new gap-closure plan targeting the specific rejected item — not an edit to this document and not a retry of the extraction pipeline hoping for a different outcome. Under no circumstances may a locked extraction constant (`DETREND_POLY_ORDER`, `BEAD_MASK_HEIGHT_FRACTION`, `MAX_TRACKING_GAP_COLUMNS`, `DETREND_MAX_Y_DEGREE`), the `MIN_VALID_FRACTION` floor, or the boundary-clipped-run exclusion in `halfmax_edges` be adjusted to make a figure look better in response to this sign-off request. Any such change must instead be justified independently, on residual/physical/numerical evidence, following the same pre-registered, outcome-independent discipline documented in Amendments A3, A4, and A5.
