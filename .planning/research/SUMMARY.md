# Project Research Summary

**Project:** NSF FMRG Data Challenge — Thermal-to-Geometry Uncertainty-Aware Prediction Pipeline
**Domain:** Applied ML for manufacturing process monitoring (DED laser additive manufacturing), small-N (4-track) research competition sprint
**Researched:** 2026-07-19
**Confidence:** MEDIUM-HIGH

## Executive Summary

This is an 8-day research-competition sprint to build a pipeline that predicts local track width `w_i(x)` from short thermal-video windows for a directed-energy-deposition (DED) laser process, with calibrated uncertainty, validated via mandatory leave-one-track-out (LOTO) cross-validation across only 4 tracks (8/400W, 10/350W, 14/300W, 21/200W). Experts building this kind of small-N, spatially-autocorrelated manufacturing-ML pipeline converge on the same shape: engineer interpretable per-window thermal features, feed them into a shallow, heavily-regularized model (gradient-boosted trees or a small CNN/CNN-LSTM) with a native uncertainty output (quantile regression, Gaussian NLL, or GP posterior), and validate exclusively with track-atomic splits — never in-track random splits, which are explicitly flagged by the organizer as invalid due to spatial autocorrelation.

The recommended approach is risk-minimizing and sequential: first build and visually validate the height-map → width extractor (no organizer-provided ground truth exists), then align thermal/height-map coordinate grids into per-track cached sample sets, then build and validate the LOTO evaluation harness with a trivial dummy predictor *before* any real model is trained, and only then train a model — starting with LightGBM quantile regression on engineered features as the primary baseline, with a CNN/CNN-LSTM deep-learning path as a stretch comparison. SEM fusion and richer geometry descriptors (boundary asymmetry, roughness) are explicitly deferred past the thermal-only baseline.

The dominant risk category is silent, undetected leakage or misalignment rather than model quality: (1) target-extraction noise/inconsistency across the 4 very different track widths, (2) preprocessing/normalization statistics computed globally before the fold split, (3) track-identity/laser-power acting as a trivial shortcut feature given N=4, (4) silent cross-sensor coordinate/orientation bugs (especially the thermal on/off detection heuristic being least reliable on track 21, which is also the recommended held-out test track), and (5) overconfident uncertainty calibration reported from only 3-4 independent folds. All of these must be mitigated with visual QA gates and structural (not just procedural) safeguards *before* model training begins — the single biggest risk to this sprint is spending days tuning a model against a harness that is quietly broken.

## Key Findings

### Recommended Stack

The stack is intentionally conservative given N=4 independent groups: `scikit-learn` for `GroupKFold`/LOTO splitting and a GP baseline, `LightGBM` for a quantile-regression baseline (primary path), `PyTorch` (plain training loop, not Lightning) for an optional CNN/CNN-LSTM stretch model, `MAPIE` for conformal-interval wrapping (treated as a diagnostic, not a rigorous guarantee given the tiny fold count), and `properscoring`/`uncertainty-toolbox` for CRPS and calibration-diagnostic plotting.

**Core technologies:**
- scikit-learn 1.9.0 — LOTO splitting (`GroupKFold`) + `GaussianProcessRegressor` baseline with native posterior std — zero extra UQ code needed for a classical baseline
- LightGBM 4.7.0 — primary uncertainty-aware baseline via native quantile-loss objective; manufacturing precedent shows GBTs match/beat deep nets on tiny-N bead/track-geometry tasks with much lower overfitting risk
- PyTorch 2.13 (raw training loop) — optional CNN/CNN-LSTM stretch model over the raw thermal-video tensor, once the baseline works
- MAPIE 1.4.1 — conformal interval wrapping as a calibration diagnostic layer (not a proven statistical guarantee at N=4 folds)
- `properscoring` — CRPS computation for evaluation

**Explicitly avoid:** transformer/video-transformer architectures, large 3D-CNNs as the *first* model, PyTorch Lightning, custom from-scratch Bayesian UQ — all high-effort/high-risk relative to an 8-day, N=4 constraint.

### Expected Features

**Must have (table stakes):**
- Documented, QA'd height-map → local width `w_i(x)` extraction (no organizer-provided extractor exists)
- Aligned multimodal sample dataset (thermal window + physical x + track ID + power, thermal-only for v1)
- Leave-one-track-out CV harness (track 21 as primary held-out case, organizer-mandated)
- Uncertainty-aware baseline model (mean/point + distribution or interval — deterministic-only is non-compliant)
- Basic calibration/coverage reporting
- Core evaluation metrics: MAE, spatial-variation-preservation, calibration/coverage
- Reproducible, executable end-to-end code + required figures
- Physical justification of the chosen geometry target

**Should have (competitive differentiators):**
- Interpretable thermal-descriptor / SHAP feature-importance analysis
- Process- vs. substrate-driven variation decomposition via a cheap SEM-roughness proxy (not full fusion)
- Rigorous calibration upgrade (conformal wrapper) beyond a naive fixed-variance assumption
- Robustness ablation rotating all 4 tracks as held-out (near-free once harness exists)
- Presentation-quality figures (Best Presentation prize)

**Defer (v2+):**
- Full SEM tile stitching + masking + fused thermal+SEM model
- Boundary asymmetry / centerline-displacement secondary target
- Additional descriptors (roughness, waviness) — organizer explicitly does not require covering every descriptor
- General-purpose pipeline infrastructure (packaging, CI, plugin architecture) — no payoff in a fixed-deliverable sprint

### Architecture Approach

The pipeline extends the existing flat-module `src/*.py` convention with new single-purpose modules rather than a packaging rewrite: `targets.py` (height map → width), `datasets.py` (thermal/target grid alignment + per-track sample caching), `evaluate.py` (LOTO harness + metrics), `models.py` (swappable `predict(inputs) -> (mean, uncertainty)` interface), and an isolated, stretch-only `sem_mask.py` that the thermal-only path never imports. Intermediate artifacts (targets, samples) are cached to `data/processed/` as versioned, diffable artifacts since their correctness can't be checked by construction. Fold splitting is track-atomic by construction (per-track `.npz` files, not a filterable global dataframe), structurally preventing leakage rather than just discouraging it procedurally.

**Major components:**
1. Target extraction (`src/targets.py`) — height map → `w_i(x)`, cached and visually QA'd against all 4 tracks; the hard blocking dependency for everything downstream
2. Dataset/sample construction (`src/datasets.py`) — reconciles thermal (0.2mm/frame) and target (µm-pixel) grids onto one canonical per-track x-grid
3. Cross-track (LOTO) evaluation harness (`src/evaluate.py`) — validated with a trivial dummy predictor *before* any real model exists
4. Model + training loop (`src/models.py`) — simplest probabilistic model first (engineered features → LightGBM/GP), CNN/CNN-LSTM as later stretch
5. SEM masking + fused variant (`src/sem_mask.py`, stretch) — isolated so it cannot break the thermal-only baseline
6. Submission/reporting (`scripts/make_submission_figures.py`) — read-only consumer of `results/`, never retrains

### Critical Pitfalls

1. **Spatial-correlation leakage from in-track splits** — LOTO must be the *only* validation split, including nested/inner validation for hyperparameter tuning; never shuffle-split positions within a track.
2. **Noisy/inconsistent target extraction across 4 very different track widths** — use a relative (not fixed-absolute) edge-detection criterion, smooth deliberately, and visually validate against all 4 tracks including track 21's gap-heavy regions before trusting any target as final.
3. **Silent thermal-window misalignment specifically on track 21** — the laser on/off detection heuristic is plausibly least reliable on the lowest-power, least-complete, *and* designated held-out track; cross-check thermal vs. height-map x-ranges numerically for all 4 tracks, with extra scrutiny on 21.
4. **Preprocessing/normalization statistics computed globally before the fold split** — fit all normalization/scaling only on the 3 training tracks per fold, never pooled across all 4.
5. **Overconfident uncertainty calibration from only 3-4 independent folds** — report calibration per held-out track (not just pooled), never tune calibration hyperparameters on the fold being reported, and present calibration qualitatively (visual bands) alongside any scalar metric.
6. **Track identity / laser power as a trivially leaky feature** — with N=4, power and track_id are statistically indistinguishable; treat power as an interpretive/report feature, not one tuned to maximize LOTO score, and run an explicit metadata-only ablation to check for this.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Target Extraction
**Rationale:** No organizer-provided ground truth exists; every downstream label and evaluation metric depends on this being correct. A wrong extractor invalidates everything retroactively with no way to "fix later" without redoing all subsequent phases.
**Delivers:** `src/targets.py` + `scripts/extract_targets.py`; cached, versioned `w_i(x)` per track; QA plots for all 4 tracks (including track 21's gaps) showing the expected 400W>350W>300W>200W width ordering.
**Addresses:** "Documented height-map → local geometry target extraction" (table stakes), "physical justification of the chosen geometry representation" (table stakes)
**Avoids:** Pitfall 6 (noisy/inconsistent width extraction), Pitfall 7 (edge effects at 20/100mm window boundaries)

### Phase 2: Dataset Alignment & Sample Construction
**Rationale:** Must reconcile thermal, height-map, and (optionally) SEM coordinate conventions onto one canonical per-track x-grid before any model can see data; a subtle misalignment here produces a model that appears to work while learning a spatially-shifted, wrong relationship.
**Delivers:** `src/datasets.py` + `scripts/build_dataset.py`; per-track cached `.npz` sample manifests; tri-modal visual QA overlay for all 4 tracks; numeric assertion that thermal/height-map x-ranges both span ≈[20,100]mm.
**Uses:** existing `src/nsf_fmrg_data.py` loaders (unchanged)
**Implements:** Coordinate-alignment data flow; Pattern 1 (cached, versioned artifacts)

### Phase 3: LOTO Evaluation Harness (validated with dummy predictor)
**Rationale:** This harness is what every subsequent model will be judged and iterated against — if it's leaky or buggy, every hour spent "improving the model" optimizes against a broken signal. Must be built and validated with a trivial dumb predictor *before* real model code exists.
**Delivers:** `src/evaluate.py` (`run_cv()`), track-atomic fold splitting enforced structurally; MAE, spatial-variation-preservation, and calibration/coverage metrics computing correctly on dummy-predictor output across all 4 folds.
**Addresses:** "Leave-one-track-out cross-validation harness" (table stakes), "core evaluation metrics" (table stakes)
**Avoids:** Pitfall 2 (spatial-correlation leakage), Pitfall 5 (preprocessing leakage), Pitfall 3 (track-identity leakage — bake the metadata ablation in here)

### Phase 4: Thermal-Only Uncertainty-Aware Baseline Model
**Rationale:** Only meaningful once Phases 1-3 are trustworthy; reuses the harness unchanged so iterating on model choice is cheap and safe. Given ~3 tracks of training data per fold, favor low-capacity/regularized models.
**Delivers:** `src/models.py` with `predict(inputs) -> (mean, uncertainty)` interface; primary LightGBM-quantile-regression baseline on engineered thermal features; LOTO results (MAE, CRPS, coverage) across all 4 folds.
**Uses:** LightGBM 4.7.0, scikit-learn `GaussianProcessRegressor` (alternative), `properscoring` for CRPS
**Avoids:** Pitfall 11 (over-investing in model complexity before harness is trustworthy), Pitfall 8 (overconfident calibration — report per-fold from the start)

### Phase 5: Differentiators (interpretability, substrate-variation proxy, robustness ablation, calibration upgrade)
**Rationale:** Enhances rather than blocks the baseline; correctly sequenced after a working, validated pipeline exists, matching the 8-day time budget.
**Delivers:** SHAP/feature-importance analysis on engineered features; cheap SEM-roughness-vs-residual proxy analysis (no full stitching); all-4-tracks-rotated robustness ablation; optional MAPIE conformal-wrapper calibration upgrade.
**Addresses:** FEATURES.md Differentiators (interpretability, process/substrate decomposition, robustness, calibration rigor) — P2 priority items

### Phase 6: Stretch — CNN/Deep Model & SEM Fusion (only if time remains)
**Rationale:** Explicitly deferred per PROJECT.md; isolating in its own module means it can be dropped entirely without risk to the working baseline.
**Delivers:** Optional small CNN/CNN-LSTM comparison model; optional SEM masking utility (`src/sem_mask.py`) + fused model variant behind the same `predict()` interface.
**Avoids:** Pitfall 1 (SEM target leakage — mandatory visual mask-verification gate before any SEM-fused model trains)

### Phase 7: Submission Packaging
**Rationale:** Packaging/reproducibility is unglamorous and easy to underestimate; must be a dedicated phase with buffer time, not a same-day last-minute task.
**Delivers:** Fresh-clone/fresh-environment dry run; `requirements.txt` completeness check (incl. `h5py`); confirmed `data/raw/` absent from git history; final figures via `scripts/make_submission_figures.py`.
**Avoids:** Pitfall 12 (no buffer for reproducible artifact), Pitfall 13 (accidental raw-data exposure via public repo)

### Phase Ordering Rationale

- Steps 1-3 (target extraction → alignment → leak-free harness) must each be independently validated *before* Phase 4 (model training) begins — this is a hard, non-negotiable gate, not a suggestion, because every later step's correctness is conditioned on the ones before it being right.
- Roughly the first third of the 8-day sprint should go to Phases 1-3 even though they produce no "model results" yet — this is deliberate front-loading of risk.
- Differentiators (Phase 5) and stretch scope (Phase 6) are strictly additive and reversible — they can be dropped without touching the working baseline, by architectural design (isolated `sem_mask.py`, swappable `predict()` interface).
- Packaging (Phase 7) is scheduled with fixed buffer near, but not on, the final day, per Pitfall 12.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1 (Target Extraction):** No organizer-provided extractor exists; the specific relative-threshold/edge-detection method and gap-handling rule for track 21 will need phase-specific research/validation against the actual height-map data.
- **Phase 2 (Dataset Alignment):** Track 21's laser on/off detection heuristic is flagged as a likely failure point; may need targeted investigation/manual override logic once real data is inspected.
- **Phase 4 (Baseline Model):** Choice between quantile LightGBM vs. Gaussian-NLL vs. GP posterior as the primary UQ mechanism should be revisited once engineered features exist and initial results are seen.

Phases with standard patterns (skip research-phase):
- **Phase 3 (LOTO Harness):** Well-established `GroupKFold`/track-atomic splitting pattern, directly specified by organizer and architecture research.
- **Phase 7 (Submission Packaging):** Standard reproducibility checklist (fresh-clone test, dependency pinning, git-history audit) — no novel research needed.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Core library facts (scikit-learn, LightGBM, PyTorch, MAPIE versions/APIs) verified against official docs/PyPI; architecture-choice guidance (e.g., raw PyTorch vs. Lightning, GBT-over-DL for small-N) is synthesized/opinion-based judgment calls, explicitly flagged as LOW-confidence where applicable |
| Features | MEDIUM (HIGH for organizer requirements) | Organizer-derived requirements sourced directly from in-repo README/organizer clarifications (HIGH); general methodology guidance drawn from adjacent literature (weld-bead profilometry, melt-pool ML) since no paper addresses this exact dataset (MEDIUM) |
| Architecture | HIGH (structure/build order) / MEDIUM (specific model choice) | Structure and data flow grounded directly in organizer README requirements and existing codebase inspection; specific model architecture intentionally deferred to STACK.md |
| Pitfalls | MEDIUM-HIGH | Codebase-grounded pitfalls (file-matching fallback, detrend stride asymmetry, thermal on/off heuristic) verified directly against `src/nsf_fmrg_data.py` source (HIGH); general ML/small-N/spatial-leakage pitfalls from web search (MEDIUM); a few forward-looking predictions (e.g., track 21 misalignment risk) are explicitly flagged as reasoned but unverified |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- No literature addresses this exact organizer-built dataset/task — all methodology guidance is adjacent-domain synthesis (weld-bead/laser-cladding profilometry, melt-pool ML), not a direct precedent; validate assumptions empirically against the actual 4 tracks as early as possible.
- The `gsd-tools query research-plan`/`classify-confidence` seam commands were not available in this environment; research was gathered via direct web search with manual confidence assignment — no impact on quality but noted as an infra gap.
- Whether track 21's thermal on/off detection heuristic is actually unreliable (Pitfall 9) is a prediction, not yet empirically confirmed — this must be checked directly against real data early in Phase 2, since it's the single highest-leverage unresolved risk to the final reported score.
- The exact choice of UQ mechanism (quantile GBT vs. Gaussian NLL vs. GP posterior vs. deep ensemble) is left open pending how the engineered-feature baseline performs — expect this decision to firm up during Phase 4 planning/execution, not before.

## Sources

### Primary (HIGH confidence)
- `README.md` (this repo) — organizer-confirmed task definition, evaluation criteria, SEM stitching/masking procedure, track↔power mapping, validation-strategy requirements
- `DATA_USE_LICENSE.md` (this repo) — data-restriction terms
- `.planning/PROJECT.md`, `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md` (this repo) — existing codebase conventions and scope decisions
- Direct source inspection of `src/nsf_fmrg_data.py` (`find_track_file`, `detect_laser_on_interval`, `extract_final_thermal_frames`, `load_wyko_asc`, `robust_plane_detrend`)
- scikit-learn official docs (`GaussianProcessRegressor`, cross-validation/`GroupKFold`, v1.9.0)
- LightGBM official docs/PyPI (v4.7.0)
- MAPIE official docs (v1.4.1)

### Secondary (MEDIUM confidence)
- Manufacturing/DED precedent for CNN-BiLSTM and GBT bead/melt-pool-geometry prediction (multiple 2024-2026 papers, tandfonline/sciencedirect/springer)
- Spatial leave-one-out / leave-profile-out CV leakage literature (digital soil mapping, marine remote sensing, general geospatial ML)
- Weld-bead / laser-cladding profilometry geometry-extraction methodology (ScienceDirect, PMC)
- Conformal prediction / conformalized quantile regression practitioner and academic sources
- SHAP/feature-importance-on-melt-pool-ML precedent (MeltpoolNet, spatter-prediction papers)
- Cookiecutter Data Science project-layout convention (adapted, not adopted wholesale)

### Tertiary (LOW confidence)
- NGBoost as a fallback UQ library — found via search, not independently verified against current release
- PyTorch Lightning vs. raw PyTorch judgment call — explicitly an opinion/risk-tradeoff, not a verified fact
- Track 21 thermal-misalignment-risk prediction (Pitfall 9) — reasoned inference from codebase inspection, not yet empirically confirmed against real data

---
*Research completed: 2026-07-19*
*Ready for roadmap: yes*
