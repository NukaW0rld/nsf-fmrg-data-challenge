# Feature Research

**Domain:** Applied ML for manufacturing process monitoring — thermal-to-geometry prediction in directed energy deposition (DED) / laser bead-on-plate, for the NSF FMRG Data Challenge
**Researched:** 2026-07-19
**Confidence:** MEDIUM overall (HIGH for organizer-derived requirements, sourced directly from the in-repo `README.md`/organizer clarifications; MEDIUM for general methodology, sourced from adjacent literature — laser cladding, weld-bead profilometry, melt-pool ML, spatial-CV/UQ best practices — via web search, since no paper addresses this exact organizer-built dataset/task)

**Research infra note:** The `gsd-tools query research-plan` / `classify-confidence` seam commands are not registered in this environment's installed `gsd-tools.cjs` (`Unknown command: research-plan`). Research below was gathered with direct `WebSearch` calls instead, and confidence is assigned manually per the standard hierarchy (organizer/repo primary source = HIGH; multiple independent secondary web sources converging = MEDIUM; single unverified secondary source = LOW). No LOW-confidence claim below is presented as authoritative without a caveat.

## Feature Landscape

### Table Stakes (Submission Must Have These)

These are non-negotiable for a *valid, competitive* submission per the organizer's stated evaluation framework (README.md) and the physical/statistical realities of an n=4-track dataset. Missing any of these makes the submission incomplete or scientifically invalid, independent of model sophistication.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Documented height-map → local geometry target extraction (`w_i(x)` or boundary functions) | Organizer explicitly provides no extractor; README states participants "must define and consistently apply their own post-processing method, justify why the resulting representation is physically meaningful, and document it for reproducibility." Without this, there is no ground truth to train or evaluate against. | MEDIUM | Build on existing `robust_plane_detrend` + `load_wyko_asc`. Must be deterministic, reproducible, and visually QA'd (overlay extracted boundary on the height map) before it's trusted downstream. |
| Aligned multimodal sample dataset (thermal video tensor `T_ij` of `2K+1` frames centered on `x_j`, paired with geometry target at `x_j`, plus track ID + laser power metadata) | This *is* the organizer's prescribed "modeling framework" (input/output pair definition in README). Any model needs this before it can train. | MEDIUM | Depends on target extraction existing first (need a target value per `x_j` on the shared coordinate grid) and on existing thermal/height-map loaders. |
| Leave-one-track-out cross-validation harness (train on 3 tracks, test on the 4th; track 21/200W recommended primary case) | Organizer explicitly calls out that random/neighboring-sample splits are invalid due to spatial autocorrelation within a track — this is stated as a required methodology, not a suggestion. A submission using in-track random splits is arguably non-compliant/misleading. | LOW–MEDIUM | Easy to implement (partition by track ID) but easy to get *subtly* wrong — e.g. any preprocessing (normalization, feature scaling, PCA) fit on all 4 tracks before splitting is leakage. Must fit all data-dependent transforms train-only. |
| Uncertainty-aware model output (mean/point estimate + a distribution or interval, not just a point prediction) | One of the challenge's three explicit "guiding principles" ("quantify uncertainty... aim for calibrated uncertainty"). A deterministic-only model does not satisfy the stated task. | MEDIUM | Cheapest compliant options: Gaussian NLL head (predict mean + log-variance), quantile regression (pinball loss, e.g. 10/50/90th percentile), or a simple ensemble of a few models for spread. Any of these is sufficient for table-stakes; sophistication is a differentiator (see below). |
| Basic calibration/coverage reporting | Organizer evaluation explicitly includes "calibration and usefulness of uncertainty estimates." Producing an uncertainty band with no calibration check is not credible. | LOW | A coverage plot (e.g., % of true values falling inside the predicted 80% interval, ideally reported per test track) plus one calibration metric (PICP, or a reliability diagram) is enough to be "reported," even if imperfectly calibrated. |
| Thermal-only baseline model that runs end-to-end | This is the project's own stated Core Value ("A thermal-only baseline... must work before anything else matters") and matches the organizer's minimum bar (thermal→geometry is the base task; SEM is explicitly optional/additive). | MEDIUM | A working simple model (e.g., gradient-boosted trees or ridge regression on engineered melt-pool descriptors, or a small 3D-CNN/CNN-LSTM on the raw video tensor) beats an ambitious model that doesn't finish. Given only 3 training tracks, a simpler model with strong regularization is *lower risk*, not just "good enough" — see Differentiators for the accuracy/robustness trade-off. |
| Standard quantitative evaluation metrics computed and reported | Organizer states final ranking is quantitative, against these exact criteria: error vs. measured local width/boundary, preservation of spatial variation, overall geometric agreement, calibration/usefulness of uncertainty. A submission that doesn't report these in the organizer's own terms is harder to score favorably. | LOW | Concretely: MAE (and/or RMSE) for local width; a spatial-variation-preservation metric (e.g., correlation coefficient or normalized cross-correlation between predicted and true `w_i(x)` curve shape, not just point error — captures whether the model reproduces *where* variation occurs, not just its average level); a calibration metric (PICP / coverage error, optionally CRPS or NLL). |
| Reproducible, executable end-to-end code + required figures | Explicit submission requirement: "Executable code... Reuse is OK." The report also requires visualizations of predicted vs. measured geometry with uncertainty. A pipeline that only runs in a specific notebook cell order, or requires manual data-massaging, fails this bar. | LOW–MEDIUM | Given the existing repo's `sys.path` hack anti-pattern (per `.planning/codebase/ARCHITECTURE.md`), a *minimal* fix (e.g., a `pyproject.toml`/editable install, or a single well-documented run script) is enough — do not over-invest here (see Anti-Features). |
| Physical justification for the chosen geometry target (why `w_i(x)` is meaningful, why the extraction threshold/method is defensible) | Explicitly a *qualitative* judging criterion ("physical justification of the chosen geometry representation... reproducibility and consistency of geometry extraction"). A target that works numerically but has no stated rationale loses points even if MAE is good. | LOW | This is mostly a documentation/report task once the extraction method exists — a few sentences plus a QA figure (extracted boundary overlaid on raw height map for 2-3 tracks) satisfies it. |

### Differentiators (What Separates Working from Winning)

Not required for validity, but these map directly onto the organizer's *qualitative* judging criteria (novelty, interpretability, distinguishing process vs. substrate variation, uncertainty usefulness) and the two special prizes ("Best Presentation," "Most Innovative Approach"). Prioritize these only after every Table Stakes item works end-to-end.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Interpretable thermal-descriptor analysis (melt-pool size/shape/intensity/asymmetry/cooling-rate features engineered from thermal frames, then correlated with or SHAP-ranked against predicted width) | Directly answers the organizer's stated goal #5 ("provide interpretable links... explain which thermal features are most strongly related to track formation... Accuracy matters, but so does insight") and the explicit judging criterion "interpretability of thermal descriptors or learned features." Literature (SHAP on ANN/GBM melt-pool models) shows this is a well-trodden, cheap technique. | LOW–MEDIUM | Cheap if the baseline model already uses engineered features (tree-based model): SHAP or permutation importance comes almost for free. If using a raw-video CNN instead, this differentiator gets *more* expensive (saliency maps, attention visualization) — a reason to prefer a feature-engineered baseline given the time budget. |
| Process- vs. substrate-driven variation decomposition | Explicitly named in the challenge prompt as something "a strong submission tries to distinguish" and is a named qualitative judging criterion. Full SEM fusion is a stretch goal, but a *cheap proxy* — e.g. per-tile or per-position roughness/topology statistics from raw (unmasked, pre-fusion) SEM tiles correlated against thermal-model residuals — gets most of the interpretive value without building a fused model. | MEDIUM | Key insight: this doesn't require the full SEM masking + stitching + fusion pipeline. A lightweight "does local substrate roughness correlate with where the thermal-only model's error is largest?" analysis is achievable in a few hours and produces a compelling narrative figure. |
| Rigorous, well-calibrated uncertainty (beyond a naive fixed-variance assumption) | Calibration quality is an explicit quantitative + qualitative judging axis. A Gaussian-NLL head with poor calibration is table stakes; wrapping it (or any point model) in split conformal prediction gives distribution-free, provably-valid coverage with very little extra engineering — a genuine "innovative but cheap" move. | LOW–MEDIUM | Conformal prediction is attractive here specifically because n=4 tracks means Bayesian/ensemble UQ is data-starved; a conformal wrapper calibrated on a held-out slice of the *training* tracks (not the test track) sidesteps needing a fully probabilistic model architecture. |
| Robustness ablation across all 4 tracks (rotate which track is held out, not just track 21) | Organizer's quantitative criteria explicitly include "robustness across different laser powers." Reporting only one held-out result (21) is compliant but reporting all 4 rotations is stronger evidence of robustness and costs little once the CV harness exists. | LOW | Nearly free once the leave-one-track-out harness is built — it's the same code run 4 times. High value-to-effort ratio; recommended if any time slack exists. |
| Sensitivity/ablation studies (thermal window size `K`, feature set variants, model architecture comparison) | Demonstrates methodological rigor, which is judged qualitatively ("reproducibility and consistency"), and produces natural report figures. | LOW–MEDIUM | Keep ablations narrow and purposeful (e.g., 3-5 values of `K`, 2-3 model families) — do not turn this into an open-ended hyperparameter search (see Anti-Features: chasing marginal gains). |
| Boundary asymmetry / centerline displacement as a secondary target (beyond plain width) | README explicitly notes width only captures size changes, while boundary functions additionally capture lateral shift and asymmetry — richer signal, explicitly invited as "beyond the minimum." | MEDIUM–HIGH | Explicitly deferred in `PROJECT.md` past v1. Only attempt after the width baseline is fully validated and time remains — treat as v1.x, not core v1. |
| Presentation-quality figures (predicted vs. measured `w_i(x)` curve with uncertainty band across 20-100mm, calibration/reliability plot, thermal-descriptor-vs-width correlation heatmap, residual-vs-substrate-roughness scatter) | Directly supports the "Best Presentation" special prize and the report's explicit (optional but scored) visualization section. Reuses figures already needed for Table Stakes evaluation reporting — low marginal cost once the underlying analysis exists. | LOW | Treat figure polish as a final pass over already-computed results, not a separate workstream. |
| Comparison of modeling paradigms (e.g., feature-engineered classical ML vs. raw-video deep model) as an explicit ablation/discussion | Given n=3 training tracks, a documented argument for *why* a simpler, feature-engineered model generalizes better than an end-to-end deep model (or vice versa, if it demonstrably doesn't) is itself a novel/insightful contribution judges can credit, and it's a natural byproduct of building the baseline carefully. | LOW–MEDIUM | Don't build two full model families for their own sake — but if the "baseline" naturally invites a 1-line contrast (e.g., tried a CNN, it overfit with 3 tracks, fell back to GBM on engineered features — here's why), document it. |

### Anti-Features (Tempting But Wrong for This 8-Day Sprint)

Things that sound like they'd strengthen the submission but are traps given the timeline, the data volume (n=4 tracks), and the organizer's explicit scope guidance.

| Feature | Why Tempting | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Full SEM mosaic stitching + track-masking + a fused thermal+SEM model as a first-class (non-stretch) deliverable | SEM fusion is explicitly part of the challenge's "modeling framework" and feels like "using all the data" | Multi-tile stitching (overlap alignment across ~13 tiles/track, per organizer's clarification) plus building/validating a leak-free mask is its own multi-day project; doing it before a working thermal-only baseline risks shipping *nothing* complete by the deadline. `PROJECT.md` already scopes this correctly as a stretch goal. | Ship the thermal-only baseline completely first. If time remains, do the cheap substrate-variation *analysis* proxy (see Differentiators) instead of a full fusion model — it captures most of the interpretive value for a fraction of the engineering cost. |
| Perfecting/over-engineering the target-extraction algorithm (sub-pixel spline boundary fitting, learned segmentation network, exhaustive threshold search) before validating a simple method | The organizer's language ("physically defensible," "justify") can be read as demanding sophistication | This is *infrastructure* for everything downstream — time spent here doesn't show up as a model result. A simple, well-documented method (robust detrend → threshold or slope-based edge detection on the cross-track profile, as used in analogous weld-bead/laser-cladding profilometry literature) is defensible if justified and visually validated; a fancier method only wins if it's demonstrably more robust, and that's very hard to prove with no ground-truth labels to validate against. | Implement the simplest defensible method (threshold or first/second-derivative edge detection on the detrended height profile), visually QA it on all 4 tracks, document the choice in 3-4 sentences, and move on. Revisit only if it visibly fails on track 21 (least-complete profilometry). |
| Chasing marginal MAE/accuracy gains via extensive hyperparameter search, architecture search, or ensembling many models | Accuracy is part of the quantitative score, and "more tuning = better score" is the default ML instinct | With only 3 training tracks and 1 held-out test track, aggressive tuning overfits to whichever 3 tracks are in training — any accuracy gain from heavy search is likely noise, not signal, and the time is better spent on the qualitative axes (interpretability, calibration, distinguishing variation sources) which are *explicitly* judged and are not subject to this overfitting risk. | Pick one reasonably strong, well-regularized model family, validate it works via leave-one-track-out, and stop tuning once results are stable. Redirect saved time to Differentiators. |
| Predicting every possible geometry descriptor (width + boundary + roughness + waviness + centerline displacement, all in v1) | README lists many valid descriptors and it's tempting to "cover all bases" | Organizer explicitly states "participants do not need to predict every possible geometry descriptor" — spreading effort across many under-validated targets yields several mediocre outputs instead of one well-evaluated, well-justified, well-calibrated one, which is worse for both quantitative and qualitative scoring. | Ship local width `w_i(x)` as the single, fully-validated v1 target (per `PROJECT.md`). Add boundary asymmetry only as a stretch, after width is done. |
| Building general-purpose data pipeline infrastructure (packaging, CI, plugin architecture, config-driven experiment framework, extensive test suite) | The existing codebase's lack of packaging/tests is a real, documented anti-pattern (`.planning/codebase/ARCHITECTURE.md`), and "do it properly" is a natural instinct | This is a solo/small-team 8-day research sprint producing a fixed deliverable (code + figures + report elsewhere), not a maintained product — investment in reusability/extensibility has near-zero payoff against the actual judging criteria and directly competes for time against Table Stakes and Differentiators. | Fix only what blocks reproducible execution (e.g., a minimal `pyproject.toml`/editable install or a single documented entry-point script replacing the `sys.path` hack). Skip CI, plugin systems, and comprehensive test suites entirely. |
| Auto-generating or heavily engineering the report/slide deck within this codebase | Feels like "finishing the whole submission" | Explicitly out of scope per `PROJECT.md` ("Written report and slide deck — produced separately by the user outside this pipeline"). Building tooling for this here duplicates effort and risks scope creep into a deliverable this pipeline isn't responsible for. | Produce clean, labeled, publication-ready figures and a short markdown/notebook summary of numeric results the user can paste into the report — nothing more. |
| Real-time/closed-loop control features, full melt-pool physics simulation, or other tangential ML/engineering work not scored by the challenge | Adjacent literature (e.g., closed-loop melt-pool-height control) makes these look like "natural extensions" and can seem impressive | None of this is part of the evaluation criteria (accuracy, spatial-variation preservation, calibration, robustness, interpretability, process/substrate distinction) — it's pure time sink relative to the prize criteria. | Ignore entirely. If physical intuition from this literature is useful, cite it briefly in interpretability discussion — don't implement it. |
| A complex non-parametric ground-truth model (e.g., full 2D Gaussian Process over the height map with learned kernel hyperparameters) presented as "the" target extractor | Sounds statistically rigorous and defensible | This is solving a much harder inverse problem than needed (denoising a smooth surface, not just finding a threshold/edge), is slow, and its own hyperparameters would need justification — trading one under-specified problem for another, more opaque one. | Use `robust_plane_detrend` (already implemented) for detrending, then a simple deterministic threshold/derivative-based boundary rule on the resulting profile. |

## Feature Dependencies

```
Height-map target extraction: w_i(x) / boundary(x)
    └──requires──> robust_plane_detrend (existing) + load_wyko_asc (existing)

Aligned multimodal sample dataset (thermal video tensor @ x_j + target + metadata)
    └──requires──> Height-map target extraction (defines target grid + values)
    └──requires──> Thermal loader (existing: extract_final_thermal_frames)
    └──requires──> Shared 20-100mm coordinate alignment (existing)

Leave-one-track-out CV harness
    └──requires──> Aligned multimodal sample dataset

Thermal-only baseline model (uncertainty-aware)
    └──requires──> Aligned multimodal sample dataset
    └──requires──> Leave-one-track-out CV harness (to be evaluated meaningfully)

Evaluation metrics (MAE, spatial-variation preservation, calibration/coverage)
    └──requires──> Baseline model output (point + uncertainty)
    └──requires──> Leave-one-track-out CV harness

Interpretability / feature-importance analysis ──enhances──> Thermal-only baseline model
    (cheap if baseline uses engineered features + tree model; expensive if raw-video CNN)

Process- vs substrate-variation analysis (cheap SEM-roughness proxy) ──enhances──> Baseline model residual analysis
    (does NOT require full SEM stitching/masking pipeline)

Robustness ablation (rotate all 4 tracks as held-out) ──enhances──> Leave-one-track-out CV harness
    (near-zero marginal cost once harness exists)

Rigorous calibration (conformal wrapper, reliability diagrams) ──enhances──> Basic uncertainty output
    (requires a held-out calibration slice of *training* tracks, not the test track)

SEM masking utility + SEM-fused model (stretch)
    └──requires──> Thermal-only baseline complete and validated (per PROJECT.md ordering)
    └──conflicts with──> 8-day time budget if pursued before core pipeline is proven

Boundary asymmetry / centerline target (stretch)
    └──requires──> Width target extraction validated first
    └──conflicts with──> "ship one complete target" principle if pursued in v1
```

### Dependency Notes

- **Target extraction is the hard blocking dependency for everything.** No sample dataset, no evaluation, no model can exist without a documented, QA'd `w_i(x)` (or boundary) extractor — this must be the first work item of the sprint, even before model-framework selection.
- **The CV harness and evaluation metrics are cheap but must be built before believing any model result** — a "working" model evaluated with an in-track random split produces a number that is actively misleading (organizer-flagged spatial-autocorrelation leakage), so this cannot be deferred to "polish."
- **Interpretability and the process/substrate decomposition enhance rather than block** the baseline — they can be layered on after the baseline is proven, which is exactly the right order given the 8-day constraint (working pipeline first, insight second).
- **SEM fusion and boundary-asymmetry targets both explicitly conflict with the time budget if front-loaded** — both require the thermal-only width baseline to already be complete and validated; this ordering is already correctly captured in `PROJECT.md`'s Active requirements.

## MVP Definition

### Launch With (v1 — must ship within the 8-day window)

- [ ] Documented, QA'd height-map → local width `w_i(x)` extraction — without this nothing else is possible
- [ ] Aligned multimodal sample dataset (thermal video tensor + physical coordinate + track ID + laser power, thermal-only)
- [ ] Leave-one-track-out CV harness (track 21 as primary held-out case)
- [ ] Thermal-only uncertainty-aware baseline model (mean + variance, or quantiles)
- [ ] Core evaluation metrics: MAE for width, a spatial-variation-preservation metric, a calibration/coverage metric
- [ ] Reproducible, executable end-to-end code (single documented entry point) + required figures (predicted-vs-measured width with uncertainty band; calibration plot)
- [ ] Brief written justification of the target-extraction method (for the report, produced as a doc/notebook cell, not a separate report deliverable)

### Add After Validation (v1.x — only once the above is fully working)

- [ ] Interpretable thermal-descriptor analysis (feature importance / SHAP on engineered melt-pool features) — triggered once the baseline model is trained and stable
- [ ] Process- vs. substrate-driven variation analysis via a cheap SEM-roughness proxy (no full stitching) — triggered once baseline residuals exist to analyze
- [ ] Robustness ablation rotating all 4 tracks as the held-out case — triggered once the CV harness works for track 21
- [ ] Rigorous calibration upgrade (e.g., conformal wrapper) — triggered if the basic calibration check shows poor coverage
- [ ] Narrow, targeted ablations (thermal window size `K`, 2-3 model family comparison) — triggered only if time remains after the above

### Future Consideration (v2+ — only pursue if far ahead of schedule)

- [ ] Full SEM tile stitching + track-masking + fused thermal+SEM model — defer; large engineering cost, explicit stretch per `PROJECT.md`
- [ ] Left/right boundary functions (asymmetry, centerline displacement) as a secondary/richer target beyond width — defer; width alone satisfies the minimum submission requirement
- [ ] Additional descriptors (edge roughness, waviness signal) — defer; organizer explicitly does not require covering every descriptor

## Feature Prioritization Matrix

| Feature | User Value (judging weight) | Implementation Cost | Priority |
|---------|------------------------------|----------------------|----------|
| Height-map target extraction (`w_i(x)`) | HIGH | MEDIUM | P1 |
| Aligned multimodal sample dataset | HIGH | MEDIUM | P1 |
| Leave-one-track-out CV harness | HIGH | LOW–MEDIUM | P1 |
| Thermal-only uncertainty-aware baseline model | HIGH | MEDIUM | P1 |
| Core evaluation metrics (MAE, variation preservation, calibration) | HIGH | LOW | P1 |
| Executable end-to-end code + core figures | HIGH | LOW–MEDIUM | P1 |
| Interpretability / thermal-descriptor feature importance | HIGH | LOW–MEDIUM | P2 |
| Process- vs. substrate-variation analysis (cheap proxy) | HIGH | MEDIUM | P2 |
| Robustness ablation (all 4 tracks rotated) | MEDIUM | LOW | P2 |
| Rigorous calibration (conformal wrapper) | MEDIUM | LOW–MEDIUM | P2 |
| Narrow ablations (window size `K`, model family) | MEDIUM | LOW–MEDIUM | P2 |
| Presentation-quality figures | MEDIUM (Best Presentation prize) | LOW | P2 |
| Full SEM fusion model | MEDIUM (if it works) | HIGH | P3 |
| Boundary asymmetry / centerline target | MEDIUM | MEDIUM–HIGH | P3 |
| Additional descriptors (roughness, waviness) | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have — submission is invalid or non-competitive without these
- P2: Should have — these are what separates a working submission from one that can win a prize (accuracy, presentation, "most innovative approach")
- P3: Nice to have — pursue only if the 8-day schedule allows, in the order listed

## Competitor / Reference-Approach Analysis

No literature addresses this exact organizer-built dataset (thermal camera + Wyko profilometry + SEM on single-bead DED, with a challenge-specific train/test split). The closest reference points, and how they inform our approach:

| Reference approach | How they do it | Our approach |
|---------------------|-----------------|----------------|
| Weld-bead / laser-cladding profilometry geometry extraction (classical) | Polynomial/EM surface-curvature removal, then threshold or first/second-derivative ("slope mutation") edge detection on the cross-track height profile to find bead shoulders/width | Adopt the same pattern: existing `robust_plane_detrend` for curvature removal, then a threshold or derivative-based rule per cross-track slice to get `w_i(x)` — simple, documented, visually validated, not a novel segmentation model |
| End-to-end deep learning on raw melt-pool thermal/vision (Vision Transformers, CNNs) for bead-geometry/defect prediction | Large labeled datasets, often multi-layer PBF, sometimes self-supervised (MAE) pretraining to cope with label scarcity | With only 3 training tracks, prefer engineered melt-pool descriptors (size, shape, intensity, asymmetry, cooling-tail features) + a classical/tree-based regressor over a full deep video model, to reduce overfitting risk and to make interpretability (SHAP/feature importance) cheap; keep a small CNN/CNN-LSTM as an optional comparison point, not the primary deliverable, given the time and data constraints |
| Conformal prediction / conformalized quantile regression for calibrated intervals (general ML, several 2025-era papers) | Wrap any point or quantile model with a distribution-free calibration step using a held-out calibration split | Use this as the low-cost path to genuinely calibrated uncertainty rather than trusting an unvalidated parametric (Gaussian NLL) output, especially valuable given the very small number of tracks available for calibration |
| Spatial leave-one-out / leave-profile-out CV literature (remote sensing, digital soil mapping) | Explicitly warns that naive random or radius-based spatial CV can still leak autocorrelated signal; recommends leaving out entire spatial units/profiles | Confirms the organizer's own guidance: leave out *entire tracks*, not spatially-buffered neighborhoods within a track — track-level leave-one-out is the correct unit of held-out data here |
| SHAP/feature-importance studies on melt-pool ML models (MeltpoolNet, spatter-prediction, porosity-classification papers) | Apply SHAP or permutation importance post-hoc on tree/ANN models trained on engineered thermal/process features to link features to outcomes | Directly reusable pattern for our Differentiator "interpretable thermal-descriptor analysis" — cheap if the baseline is feature-engineered |

## Sources

- [Weld bead recognition using laser vision with model-based classification (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/S0736584517300169) — MEDIUM confidence (adjacent domain: weld beads, not DED profilometry, but directly analogous threshold/derivative-based extraction methodology)
- [Dynamic Modeling of Weld Bead Geometry Features in Thick Plate GMAW Based on Machine Vision and Learning (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7763434/) — MEDIUM confidence
- [Systematic evaluation of process parameter maps for laser cladding and directed energy deposition (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/S2214860417302841) — MEDIUM confidence
- [In-Situ Melt Pool Characterization via Thermal Imaging for Defect Detection in DED Using Vision Transformers (arXiv 2411.12028)](https://arxiv.org/abs/2411.12028) — MEDIUM confidence
- [Multimodal deep learning-based on/off-axis melt pool monitoring for layer height and surface metrology predictions in DED (Journal of Intelligent Manufacturing, Springer)](https://link.springer.com/article/10.1007/s10845-025-02714-1) — MEDIUM confidence
- [Deep Learning for Melt Pool Depth Contour Prediction From Surface Thermal Images via Vision Transformers (arXiv 2404.17699)](https://arxiv.org/html/2404.17699v1) — MEDIUM confidence
- [Enhanced geometric accuracy in DED via closed-loop melt pool height control using real-time thermal imaging (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/S2214860425002106) — MEDIUM confidence (control-focused; cited only for melt-pool-width accuracy figures, not adopted as a feature)
- [Calibrated Uncertainty Quantification overview (EmergentMind)](https://www.emergentmind.com/topics/calibrated-uncertainty-quantification) — MEDIUM confidence, secondary aggregator
- [Conformalized Quantile Regression explainer (Medium, Valeriy Manokhin)](https://valeman.medium.com/conformalized-quantile-regression-smarter-uncertainty-prediction-for-data-scientists-6389bea7a7c4) — MEDIUM confidence, practitioner source
- [Uncertainty quantification for probabilistic ML in earth observation using conformal prediction (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11246475/) — MEDIUM confidence
- [Calibration in Machine Learning Uncertainty Quantification: beyond consistency to target adaptivity (arXiv 2309.06240)](https://arxiv.org/pdf/2309.06240) — MEDIUM confidence
- [The problematic case of data leakage: leave-profile-out cross-validation in 3D digital soil mapping (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/S0016706125000618) — MEDIUM confidence, directly supports track-level (not radius-based) leave-one-out
- [Distributional bias compromises leave-one-out cross-validation (PMC)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11177965/) — MEDIUM confidence, general LOOCV caveat
- [Iterative spatial leave-one-out CV and gap-filling for supervised learning in marine remote sensing (Taylor & Francis)](https://www.tandfonline.com/doi/full/10.1080/15481603.2022.2107113) — MEDIUM confidence
- [Discovery of Spatter Constitutive Models in Additive Manufacturing Using Machine Learning (arXiv 2501.08922)](https://arxiv.org/html/2501.08922v2) — MEDIUM confidence, source for SHAP-on-melt-pool-features pattern
- [MeltpoolNet: Melt pool characteristic prediction in Metal AM using ML (ResearchGate)](https://www.researchgate.net/publication/360351639_MeltpoolNet_Melt_pool_characteristic_prediction_in_Metal_Additive_Manufacturing_using_machine_learning) — MEDIUM confidence
- **Primary/authoritative source for all organizer requirements, evaluation criteria, and scope decisions:** `/home/khoa2/nsf-fmrg-data-challenge/README.md` (in-repo, incorporates organizer Discord clarifications dated 2026-07-17) — HIGH confidence
- **Primary source for existing codebase capabilities and current architecture:** `.planning/PROJECT.md`, `.planning/codebase/ARCHITECTURE.md` — HIGH confidence

---
*Feature research for: applied ML thermal-to-geometry prediction in DED laser manufacturing*
*Researched: 2026-07-19*
