# Roadmap: NSF FMRG Data Challenge — Thermal-to-Geometry Prediction Pipeline

## Overview

An 8-day sprint (2026-07-19 → 2026-07-27) that builds a thermal-only, cross-track-validated,
uncertainty-aware local-width prediction pipeline, in strict horizontal-layer pipeline-stage
order: lock and visually validate the height-map → width target extraction first, then align
thermal and target coordinate grids into cached per-track samples, then build and validate a
leak-free leave-one-track-out (LOTO) harness with a dummy predictor, then — and only then — train
the real thermal-only model, and finally package everything into one reproducible, submission-ready
entry point with required figures. Each phase is a hard gate for the next: a later phase may not
start until the phase before it has been independently, visually/numerically validated. This
front-loads the sprint's risk (target correctness, alignment correctness, harness leak-safety)
into the first ~3 days rather than discovering it late against a tuned model.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Target Extraction & Contract** - Lock and visually validate the height-map → local-width `w_i(x)` extraction method against all 4 tracks
- [ ] **Phase 2: Dataset Alignment & Sample Construction** - Reconcile thermal and target coordinate grids into cached, leak-safe per-track samples
- [ ] **Phase 3: LOTO Evaluation Harness & Metrics** - Build the leave-one-track-out harness and metrics, proven leak-free with a dummy predictor before any real model exists
- [ ] **Phase 4: Thermal-Only Uncertainty-Aware Baseline Model** - Train and evaluate the thermal-only model through the validated harness
- [ ] **Phase 5: Submission Packaging & Reporting** - End-to-end reproducible entry point producing all required competition figures

## Phase Details

### Phase 1: Target Extraction & Contract

**Goal**: A documented, reproducible local-width extraction method is specified and then implemented, and is visually validated against all 4 tracks before anything downstream trusts it as ground truth.
**Depends on**: Nothing (first phase)
**Requirements**: TARGET-01, TARGET-02
**Success Criteria** (what must be TRUE):

  1. The TARGET-01 contract (width definition `w_i(x)` = upper − lower boundary, relative-not-absolute threshold rule, spatial smoothing scale, 0.2mm output grid, valid-coordinate mask, and an explicit track-21 gap-handling rule) is written and reviewed before any extraction code is trusted.
  2. Running the extractor on all 4 tracks (8, 10, 14, 21) produces a `w_i(x)` curve per track showing the expected width ordering 400W(8) > 350W(10) > 300W(14) > 200W(21).
  3. QA plots overlay the extracted width/boundary on both the raw and detrended height map for all 4 tracks, including track 21's gap-heavy regions, and are visually confirmed sane (no sawtooth/high-frequency jitter, no silently dropped gaps).
  4. The identical extraction rule is applied across all 4 tracks with no per-track-tuned thresholds — confirmed by code inspection showing one shared parameterization.

**Plans:** 18/18 plans executed

Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Wave 0 env + `src/targets.py` contract module (D-01–D-16 as one shared parameterization) with synthetic contract-invariant tests

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — 4-track extraction runner, `.npz` + params persistence, QA figures (residual/overlay/width), raw-data prohibition check, artifact assertions, ordering investigation

**Wave 3** *(blocked on Wave 1 and Wave 2 completion)*

- [x] 01-03-PLAN.md — Gap closure for post-smoothing boundary validity, canonical raw/output containment, and success/failure raw-integrity verification

**Wave 4** *(gap closure, blocked on Wave 1–3 completion)*

- [x] 01-04-PLAN.md — G-01-1: upgrade `robust_plane_detrend` to a configurable-order robust surface fit (Amendment A3), regenerate real 4-track residual-map QA

**Wave 5** *(gap closure, blocked on Wave 4 completion)*

- [x] 01-05-PLAN.md — G-01-2/G-01-3: cross-column continuity tracking in `halfmax_edges` and a degenerate-window fix in `nan_savgol`, regenerate real 4-track boundary/width QA

**Wave 6** *(gap closure, blocked on Wave 5 completion)*

- [x] 01-06-PLAN.md — Gap 2 diagnostic: uniform detrend-order {1,2,4} × continuity on/off sweep on all 4 tracks; isolate the width-collapse root cause and pre-register an outcome-independent fix-selection criterion

**Wave 7** *(gap closure, blocked on Wave 6 completion)*

- [x] 01-07-PLAN.md — Gap 2 + Gap 1: apply ONE uniform track-independent fix (bead-mask before detrend), complete `extraction_params()` (MAX_TRACKING_GAP_COLUMNS + fix param) with change-sensitive provenance, and record Amendment A4

**Wave 8** *(gap closure, blocked on Wave 7 completion)*

- [x] 01-08-PLAN.md — Gap 2 outcome: atomically regenerate 4 NPZs + 12 QA PNGs + params/manifest, re-run `check_targets.py`, and report the 8>10>14>21 ordering honestly (escalate, never tune, if not restored)

**Wave 9** *(gap closure, blocked on Wave 8 completion)*

- [x] 01-09-PLAN.md — WR-03/WR-01/WR-02: give the width-regression sweep a bead-mask axis so it matches production, make `find_track_file`'s anchored regex load-bearing, and add exact-resolution guards to the thermal and SEM loaders
- [x] 01-10-PLAN.md — CR-03/CR-02: reject symlinks at every publish path (rmtree/rename) with victim-survival regressions, and promote the coverage check to a hard `MIN_VALID_FRACTION = 0.5` gate that fails closed

**Wave 10** *(gap closure, blocked on Wave 9 completion)*

- [x] 01-11-PLAN.md — Track 10's coverage collapse, end to end in one plan: committed diagnostic, git-committed outcome-independent fix criterion, ONE uniform track-independent fix + Amendment A5, atomic 4-track regeneration, honest ordering report

**Wave 11** *(gap closure, blocked on Wave 10 completion)*

- [x] 01-12-PLAN.md — Correct the `REQUIREMENTS.md` TARGET-02 record and produce the human visual sign-off handoff for all 12 regenerated QA figures

**Wave 12** *(gap closure, blocked on Wave 11 completion)*

- [x] 01-13-PLAN.md — G-01-4: pre-register an outcome-independent criterion for the x-direction (along-track) detrend edge effect, cap cross-track interaction degree (Amendment A6) if the criterion selects it, regenerate all 4 tracks, and report the 10-vs-14 ordering outcome honestly with an option-(a) fallback discussion

**Wave 13** *(gap closure, blocked on Wave 12 completion)*

- [x] 01-14-PLAN.md — G-01-5: merge noise-fragmented boundary candidates and gate tracked selection by length plausibility in `halfmax_edges` (Amendment A7), regenerate all 4 tracks, and report the fragmentation/jump-statistic improvement honestly

**Wave 14** *(gap closure, blocked on Wave 13 completion)*

- [x] 01-15-PLAN.md — Regenerate the stale `01-SIGNOFF-REQUEST.md` against the live Amendment-A7 run (razor-thin 50.50% track-10 margin, doubled 10-vs-14 gap, MIXED fragmentation outcome, all 7 amendment constants) and reconcile `REQUIREMENTS.md`'s TARGET-02 checkbox with its traceability row — documentation only, no source/test/constant/pipeline change

**Wave 15** *(gap closure, blocked on Wave 14 completion)*

- [x] 01-16-PLAN.md — G-01-6: reorder halfmax_edges' D-01/D-03 clip-exclusion before merge_adjacent_runs (Mechanism A) and gate tracked selection by a history-based far-AND-small plausibility check (Mechanism B, Amendment A8), regenerate all 4 tracks, and report the fragmentation/jump-statistic/crop-edge outcome honestly without re-litigating the accepted 10-vs-14 FLAG or implementing the out-of-scope Mechanism C

**Wave 16** *(gap closure, blocked on Wave 15 completion)*

- [x] 01-17-PLAN.md — Regenerate the stale `01-SIGNOFF-REQUEST.md` against the live Amendment-A8 run, with every number re-derived at execution time from `check_targets.py` and `manifest.json` (never transcribed): live run_id/timestamp, the disclosure that the provenance digest is unchanged because A8 added no new constant, live coverage table, the widened 10-vs-14 gap, A8's two behavioral contract rules, refreshed figure questions, the preserved human width-ordering override plus one new unticked reaffirmation item — documentation only, no source/test/constant/pipeline/requirements change

**Wave 17** *(gap closure, blocked on Wave 16 completion)*

- [x] 01-18-PLAN.md — Phase-seal hygiene with no verdict changes: reasoned no-external-API `COVERAGE.md` declaration verified against the real api-coverage gate, a dated G-01-6 annotation in `01-UAT.md` whose pass condition is that the verdict is provably unchanged, and a comment-only WR-01 historical-baseline disclaimer on the drifted `scripts/diagnose_track10_coverage.py`

### Phase 2: Dataset Alignment & Sample Construction

**Goal**: Thermal and target coordinate grids are reconciled onto one canonical per-track x-grid, producing cached sample sets that are structurally safe from cross-fold leakage.
**Depends on**: Phase 1
**Requirements**: DATA-01, DATA-02
**Success Criteria** (what must be TRUE):

  1. Each of the 4 tracks has a cached per-track sample manifest (`2K+1`-frame thermal window + width target + track id + laser power + physical x), restricted to Phase 1's valid-coordinate mask.
  2. An overlay QA plot per track confirms thermal `x_mm_center` and target `x` refer to the same physical location, with a numeric assertion that both ranges span ≈[20,100]mm for all 4 tracks — with extra scrutiny on track 21's laser on/off detection.
  3. Code inspection confirms every normalization/feature-selection transform is fit only inside a per-fold loop over that fold's training tracks — no transform is fit on pooled all-track data before any split exists.

**Plans**: TBD

### Phase 3: LOTO Evaluation Harness & Metrics

**Goal**: A leak-free, track-atomic cross-validation harness with correctly implemented evaluation metrics exists and is proven trustworthy using a trivial dummy predictor, before any real model is trained.
**Depends on**: Phase 2
**Requirements**: EVAL-01, EVAL-02, EVAL-03, METRIC-01, METRIC-02
**Success Criteria** (what must be TRUE):

  1. `run_cv()` executes all 4 leave-one-track-out folds (track 21 as the primary held-out case), with normalization, feature selection, hyperparameter tuning, and calibration fit only within each fold's training tracks — code inspection confirms the held-out track's file is never opened during fitting.
  2. Running a dummy/trivial predictor (e.g., training-fold mean) through the full harness produces 4 separate track-level metric results (not one pooled number across ~400 spatially-correlated positions) with plausible, hand-checkable values — proving the harness itself works before any real model exists.
  3. The spatial-variation-preservation metric (METRIC-01: centered-curve correlation + first-difference/total-variation agreement) is defined, documented, and computes without error on the dummy predictor's output for all 4 folds.
  4. Per-held-out-track reporting includes MAE, spatial-variation preservation, and paired sharpness + calibration metrics (coverage/calibration error always reported alongside mean interval width or CRPS/NLL, never coverage alone) — verified on dummy-predictor output.

**Plans**: TBD

### Phase 4: Thermal-Only Uncertainty-Aware Baseline Model

**Goal**: A thermal-only model predicts local width with a genuine uncertainty estimate for every position in every held-out track, evaluated exclusively through the already-validated harness.
**Depends on**: Phase 3
**Requirements**: MODEL-01
**Success Criteria** (what must be TRUE):

  1. The model produces both a mean/point prediction and an uncertainty estimate (variance or quantiles) for every position in each of the 4 held-out tracks.
  2. Running the model through the unchanged `run_cv()` harness produces per-track MAE, spatial-variation-preservation, and calibration/sharpness results for all 4 folds.
  3. Track 21 (primary held-out case) results are reviewed and confirmed not to be the product of any hyperparameter tuned while observing track 21's own score (anti-leakage/anti-peeking check).

**Plans**: TBD

### Phase 5: Submission Packaging & Reporting

**Goal**: The complete pipeline runs end-to-end from raw data to final metrics/figures via one documented entry point, verified reproducible and ready for competition submission.
**Depends on**: Phase 4
**Requirements**: SUBMIT-01, SUBMIT-02
**Success Criteria** (what must be TRUE):

  1. A single documented entry point (script or notebook) runs the entire pipeline from raw data files to final metrics/figures with no manual data massaging between steps — verified via a fresh-clone/fresh-environment dry run completed at least one day before the deadline.
  2. Per-held-out-track figures are produced for all 4 tracks: predicted-vs-measured width curve with uncertainty band, and a calibration/sharpness plot.
  3. `requirements.txt` lists every dependency actually exercised (including `h5py` if any track needs the HDF5 fallback path), and `git log --all -- data/raw` is confirmed empty before a GitHub-link submission path is chosen.

**Plans**: TBD

## Stretch / v2 (Not Yet Scheduled)

The following v2 requirements are explicitly deferred and are **not** assigned to a phase in this
roadmap. They are pursued only after all 5 v1 phases above are complete and validated, and only if
time remains before the 2026-07-27 deadline. Add them via `/gsd-phase --insert` or a follow-on
milestone when/if that time exists — do not pull them forward into v1 phases:

- **INSIGHT-01 / INSIGHT-02** — feature-importance/SHAP analysis; cheap substrate-variation proxy from fixed off-track SEM bands
- **ROBUST-01** — robustness ablation rotating all 4 tracks as the held-out case
- **CALIB-01** — conformal-prediction (MAPIE) calibration wrapper
- **ABL-01** — thermal-window-size and model-family ablations
- **FUSION-01 / FUSION-02** — SEM stitching + masking utility, and a SEM-fused thermal+SEM model variant compared against the thermal-only baseline
- **TARGET-03** — boundary-function (left/right) secondary target

If pursued, natural follow-on ordering (informed by `research/SUMMARY.md`): differentiators
(interpretability, robustness ablation, calibration upgrade) before stretch multimodal work
(SEM masking + fusion), since SEM fusion carries an explicit target-leakage risk (Pitfall 1) and
must never be started before its own mandatory visual mask-verification gate.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Target Extraction & Contract | 18/18 | In Progress|  |
| 2. Dataset Alignment & Sample Construction | 0/TBD | Not started | - |
| 3. LOTO Evaluation Harness & Metrics | 0/TBD | Not started | - |
| 4. Thermal-Only Uncertainty-Aware Baseline Model | 0/TBD | Not started | - |
| 5. Submission Packaging & Reporting | 0/TBD | Not started | - |
