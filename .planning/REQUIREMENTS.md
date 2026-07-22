# Requirements: NSF FMRG Data Challenge — Thermal-to-Geometry Prediction Pipeline

**Defined:** 2026-07-19
**Core Value:** A thermal-only baseline that runs end-to-end — raw data in, cross-track-validated local-width predictions with calibrated uncertainty out — must work before anything else matters.

## v1 Requirements

Requirements for the must-ship, 8-day pipeline. Each maps to roadmap phases.

### Target Contract & Extraction

- [x] **TARGET-01**: The local-width target contract is specified and documented before extraction code is written — width definition (`w_i(x)` = upper − lower boundary at each `x`), extraction threshold rule, spatial smoothing scale, output grid resolution (0.2mm, matching thermal frame spacing), the valid-coordinate mask, and an explicit, consistent rule for handling Track 21's incomplete profilometry coverage. One rule is applied across all 4 tracks — no per-track tuning of the extraction method.
- [x] **TARGET-02**: The height-map target extractor implements the locked TARGET-01 contract and is visually QA'd (extracted width/boundary overlaid on the raw + detrended height map) against all 4 tracks before being trusted downstream.

### Data Pipeline

- [ ] **DATA-01**: Pipeline constructs aligned thermal-video-tensor samples (`2K+1` frames centered on `x_j`) paired with the width target on the shared 0.2mm output grid, with track id, laser power, and physical `x` coordinate metadata, restricted to the valid-coordinate mask from TARGET-01.
- [ ] **DATA-02**: All data-dependent transforms (normalization, feature selection) are fit only on the training-fold tracks of a given leave-one-track-out split — never on pooled all-track data before splitting.

### Validation

- [ ] **EVAL-01**: Leave-one-track-out cross-validation harness trains on 3 tracks and evaluates on the held-out 4th, with track 21 as the primary held-out case. Normalization, feature selection, hyperparameter tuning, and calibration are all fit only within the current split's training tracks (nested, group-safe — no leakage from the held-out track into any fitting step).
- [ ] **EVAL-02**: The harness is validated leak-free using a dummy/trivial baseline predictor (e.g., predict the training-fold mean) before any real model is trained — this validates the harness itself, not model quality.
- [ ] **EVAL-03**: Metrics are aggregated per held-out track (4 track-level results), not computed by pooling ~400 spatially-correlated positions per track as if they were independent samples.

### Modeling

- [ ] **MODEL-01**: A thermal-only model predicts local width with an uncertainty estimate (mean + variance, or quantiles) for each position in each held-out track.

### Metrics & Reporting

- [ ] **METRIC-01**: "Spatial-variation preservation" is defined and documented before model development, computed as centered-curve correlation plus a first-difference/total-variation agreement metric between predicted and measured `w_i(x)`.
- [ ] **METRIC-02**: Pipeline computes and reports, per held-out track: MAE for local width, the spatial-variation-preservation metric (METRIC-01), and paired sharpness + calibration metrics — coverage/calibration error is always reported alongside mean interval width or CRPS/NLL, never coverage alone (wide intervals trivially win on coverage).

### Submission

- [ ] **SUBMIT-01**: The entire pipeline runs end-to-end from raw data files to final metrics/figures via a single documented entry point (script or notebook), without manual data massaging between steps.
- [ ] **SUBMIT-02**: Pipeline produces the required figures: predicted-vs-measured width curve with uncertainty band, and a calibration/sharpness plot, per held-out track.

## v2 Requirements

Deferred to future work — only pursued once all v1 requirements are complete and validated, and time remains before the deadline.

### Interpretability

- **INSIGHT-01**: Feature-importance/SHAP analysis linking engineered thermal descriptors to predicted width
- **INSIGHT-02**: A cheap process-vs-substrate variation proxy using fixed off-track bands from individual, unstitched SEM tiles (not the processed track region) correlated against baseline model residuals — deliberately not a full-mosaic or unmasked-roughness approach, to avoid any leakage risk from the processed track being visible

### Robustness & Calibration

- **ROBUST-01**: Robustness ablation rotating all 4 tracks as the held-out case, not just track 21
- **CALIB-01**: Conformal-prediction calibration wrapper for rigorous, distribution-free coverage guarantees
- **ABL-01**: Narrow ablations over thermal window size `K` and 2-3 model family comparisons

### Stretch Multimodal

- **FUSION-01**: SEM tile stitching + track-masking utility preventing target leakage
- **FUSION-02**: SEM-fused thermal+SEM model variant, compared against the thermal-only baseline using the same LOTO harness
- **TARGET-03**: Boundary function (left/right) prediction as a secondary target beyond width, capturing lateral shift/asymmetry

## Out of Scope

Explicitly excluded. Documented to prevent scope creep during the 8-day sprint.

| Feature | Reason |
|---------|--------|
| Written report and slide deck | Produced separately by the user outside this pipeline; this project's scope is code, pipeline, and figures only |
| Covering every geometry descriptor (roughness, waviness) in v1 | Organizer explicitly does not require it; spreads effort across several under-validated targets instead of one well-evaluated one |
| Unmasked full-SEM-mosaic roughness as a substrate proxy | The processed track is visible in an unmasked mosaic and would contaminate the proxy — replaced by INSIGHT-02's fixed off-track-band approach |
| General-purpose pipeline infrastructure (CI, plugin architecture, config-driven experiment framework, comprehensive test suite) | Near-zero payoff against judging criteria for a one-shot 8-day research sprint; only fix what blocks reproducible execution |
| Real-time/closed-loop control, melt-pool physics simulation | Not part of the evaluation criteria |
| Complex non-parametric ground-truth extractor (e.g., full 2D Gaussian Process over the height map) | Solves a harder inverse problem than needed and is itself hard to justify with no ground-truth labels to validate against |
| Full multimodal (thermal+SEM) fusion as the initial/core model | Explicitly deprioritized in favor of a complete thermal-only baseline first, per `PROJECT.md` |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| TARGET-01 | Phase 1 | Complete |
| TARGET-02 | Phase 1 | Awaiting human visual sign-off on regenerated QA figures — see `01-SIGNOFF-REQUEST.md` |
| DATA-01 | Phase 2 | Pending |
| DATA-02 | Phase 2 | Pending |
| EVAL-01 | Phase 3 | Pending |
| EVAL-02 | Phase 3 | Pending |
| EVAL-03 | Phase 3 | Pending |
| METRIC-01 | Phase 3 | Pending |
| METRIC-02 | Phase 3 | Pending |
| MODEL-01 | Phase 4 | Pending |
| SUBMIT-01 | Phase 5 | Pending |
| SUBMIT-02 | Phase 5 | Pending |

*Correction (2026-07-21):* TARGET-02 was previously marked `Complete`, contradicting `01-VERIFICATION.md` (2026-07-20T22:10:00Z), which found it BLOCKED. Corrected here to reflect the actual state: the extraction contract is implemented and its coverage floor is cleared per `01-11-ORDERING-OUTCOME.md`, but TARGET-02's own acceptance criterion requires a human reviewer to confirm the QA figures — that confirmation has not occurred. Basis: `01-VERIFICATION.md`, `01-11-ORDERING-OUTCOME.md`.

**Coverage:**

- v1 requirements: 12 total
- Mapped to phases: 12/12 ✓
- Unmapped: 0 ✓

---
*Requirements defined: 2026-07-19*
*Last updated: 2026-07-19 after roadmap creation (5 phases, full v1 coverage)*
