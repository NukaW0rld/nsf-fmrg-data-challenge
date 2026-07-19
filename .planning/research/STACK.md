# Stack Research

**Domain:** Uncertainty-aware regression from short thermal-video-tensor sequences to a continuous spatial target (local track width), small-N (4 tracks) manufacturing process-monitoring dataset
**Researched:** 2026-07-19
**Confidence:** MEDIUM (core library facts verified against official docs/PyPI/GitHub; architecture-choice guidance synthesized from multiple cross-referenced manufacturing-ML papers and general small-data DL literature — see per-row confidence)

## The Small-N Framing (read this first)

This project has **only 4 independent groups** (track 8/400W, 10/350W, 14/300W, 21/200W). Leave-one-track-out (LOTO) cross-validation is mandatory (per `PROJECT.md`) and yields **only 4 folds** — a weak estimate of generalization no matter what model is used. Each track does contribute many spatially-correlated samples (roughly one per thermal-video window centered at each x-position across the 20-100mm crop, likely low-hundreds per track), so within-fold sample counts are moderate, but **the effective degrees of freedom for generalization is 4, not "hundreds."**

Every recommendation below is chosen to be conservative against this constraint: simple/shallow architectures, strong regularization, ensembles built from the LOTO folds themselves rather than extra held-out splits, and no method that assumes large calibration sets or large pretraining corpora (none exist for this domain).

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12+ (already in use, per `.planning/codebase/STACK.md`) | Language | Matches existing `src/nsf_fmrg_data.py`; no reason to change. |
| scikit-learn | 1.9.0 (current stable) | Classical regression, `GaussianProcessRegressor`, train/test utilities, `GroupKFold`/manual LOTO splitting | Gives `GroupKFold` for clean leave-one-track-out splitting, and a native-uncertainty `GaussianProcessRegressor` (posterior mean+std via `return_std=True`) usable directly on engineered features — zero extra UQ code needed for the feature-based baseline. MEDIUM confidence (verified via official docs). |
| LightGBM | 4.7.0 (current stable, released 2026-07-18) | Gradient-boosted-tree baseline + native quantile-regression UQ | Manufacturing precedent (see Pitfalls/precedent section) shows gradient-boosted trees (LightGBM/CatBoost/XGBoost/RandomForest) match or beat deep nets for bead/track geometry prediction from engineered process/thermal features, with far less overfitting risk on tiny N. LightGBM supports the pinball/quantile-loss objective natively, so a 3-quantile-model ensemble (q0.1/q0.5/q0.9) is the fastest path to a working uncertainty-aware baseline. MEDIUM confidence. |
| PyTorch | 2.13 (current stable, released 2026-07-08) | Deep-learning path: CNN / CNN-LSTM on the thermal-video tensor | ~85% of current DL research uses PyTorch over TensorFlow; dynamic graphs make debugging small custom architectures fast, which matters most under an 8-day deadline. TensorFlow's advantages (TPU, mobile/edge deployment, TF Serving) are irrelevant here — single local GPU, no deployment target. MEDIUM confidence. |
| torch (raw training loop) — **not PyTorch Lightning** | — | Model training/eval loop | For a single small model trained on 4 GPU-sized folds, a plain ~80-line PyTorch loop is faster to get *correct* than learning Lightning's config/callback surface under time pressure, and removes a whole class of "framework version mismatch" debugging risk this week. Revisit only if the team is already fluent in Lightning. LOW confidence (opinion, not benchmarked) — flagged explicitly as a judgment call, not a verified fact. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| MAPIE (`mapie`) | 1.4.1 (current stable) | Conformal prediction intervals (`ConformalizedQuantileRegressor`) | Use to wrap either the LightGBM quantile models or a PyTorch point-predictor and produce calibrated prediction intervals with a distribution-free coverage guarantee — *in the large-sample regime*. With only 4 LOTO folds, treat MAPIE's coverage numbers as a **useful diagnostic, not a rigorous guarantee** (see Alternatives/caveats below). scikit-learn-compatible; also wraps arbitrary PyTorch models via its regressor interface. MEDIUM confidence. |
| `properscoring` | latest (pip, numpy/scipy-only, numba optional) | CRPS computation for evaluation | Small, stable, dependency-light library for `crps_ensemble`/`crps_gaussian`. Prefer this over hand-rolling CRPS math. MEDIUM confidence. |
| `uncertainty-toolbox` | 0.1.1 (PyPI, released Jan 2023 — **stale release**, GitHub sporadically active through 2025) | Calibration curves, miscalibration/coverage metrics, plotting | Useful for its calibration-diagnostic plots (predicted vs. empirical coverage) and miscalibration-area metric so you don't have to write plotting code from scratch. Because the PyPI release is stale, pin the exact version you test with and do NOT rely on it for anything beyond metrics/plots — reimplement any metric it can't produce cleanly (a coverage-at-quantile check is ~5 lines of numpy anyway). MEDIUM confidence, but flagged as a maintenance risk. |
| NGBoost (`ngboost`) | latest (Stanford ML Group) | Alternative single-model probabilistic-regression option | Gives full predictive distributions from gradient boosting directly (no separate quantile models to fit/calibrate). Reasonable fallback if the 3-quantile-LightGBM approach proves awkward to calibrate, but adds a second boosting library to learn — only reach for it if time remains after the primary stack works. LOW confidence (found via search, not independently verified against current PyPI release). |
| `h5py` | already a transitive dependency (per `.planning/codebase/STACK.md`) | v7.3 `.mat` fallback loading | Already required by existing code; add explicitly to `requirements.txt` (currently an undeclared gap). Not new research — noted because it's a real dependency gap. |
| `numpy`, `scipy`, `pandas`, `matplotlib` | already pinned/used | Array ops, feature engineering, plotting | Unchanged from existing stack; no version-compatibility concerns identified with the additions above. |

## Installation

```bash
# Core (add to requirements.txt alongside existing numpy/scipy/pillow/pandas/matplotlib)
pip install scikit-learn==1.9.0
pip install lightgbm==4.7.0
pip install torch --index-url https://download.pytorch.org/whl/cu121   # match to local CUDA version
pip install mapie==1.4.1
pip install properscoring
pip install h5py   # currently an undeclared transitive dependency — pin it explicitly

# Optional / only if primary quantile approach is awkward to calibrate
pip install ngboost
pip install uncertainty-toolbox==0.1.1   # pin exact version; stale on PyPI, verify behavior before relying on it
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|--------------------------|
| LightGBM quantile regression on engineered thermal features (primary baseline) | 2D-CNN or CNN-LSTM directly on the raw thermal-video tensor | Use the CNN/CNN-LSTM path once the feature-engineered baseline works end-to-end and there is time left in the 8 days — manufacturing literature shows CNN-BiLSTM hybrids are the dominant published architecture for melt-pool/track-width prediction from monitoring video, so it is a legitimate stretch goal, not just novelty. Treat it as phase 2, not phase 1, given deadline risk. |
| MC dropout + deep ensemble (3-5 seeds) for the deep-learning UQ path | Full Bayesian neural network (variational inference, MCMC) | Only if there is a specific requirement for a principled Bayesian posterior; BNN training/tuning is a multi-week effort in itself and is not justified by an 8-day deadline or a 4-group dataset. |
| GaussianProcessRegressor (scikit-learn) on engineered features for the classical UQ path | Gaussian Process on raw video tensor / deep kernel learning | GP kernels operate on low-dimensional feature vectors, not raw high-dimensional video tensors — deep kernel learning would require building and tuning a feature extractor first, which is strictly more work than the CNN path for no clear benefit here. |
| MAPIE conformal wrapping (as a diagnostic layer) | Full "formal" conformal prediction with guaranteed marginal coverage | Formal conformal coverage guarantees assume a reasonably large, exchangeable calibration set. With 4 tracks as the only source of genuinely independent data, do not present conformal coverage numbers as a proven guarantee — report them as one more calibration diagnostic alongside CRPS and empirical coverage plots. |
| 3D-CNN / video transformer on the raw thermal tensor | — (not recommended as the primary path) | Only consider if there is significant leftover time and a strong reason; see "What NOT to Use." |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|--------------|
| Transformer / video-transformer architectures (ViT-style, temporal attention) as the primary model | Transformers need large data or pretraining to avoid the FFN memorizing noise; there is no pretrained thermal-video transformer to fine-tune from, and 4 tracks is nowhere near enough data to train one from scratch. Cross-referenced across multiple small-data-DL sources. | Small regularized CNN or CNN-LSTM, or the LightGBM feature-based baseline. |
| Large 3D-CNN (many layers/channels) over the full raw video tensor as the *first* model to build | High parameter count relative to 4 independent tracks is a direct overfitting risk; also slower to get working correctly within 8 days than a feature-based baseline. | Start with engineered per-window features (percentile temperature stats, time-to-peak, cooling-rate slope, simple image moments) into LightGBM/GP; only add a *small*, heavily-regularized CNN/CNN-LSTM once that baseline is validated. |
| PyTorch Lightning (or any new training framework) if the team isn't already using it | Adds a framework-learning-curve risk with only 8 days; framework-config debugging is time you don't have. | Plain PyTorch training loop — fully transparent, easy to debug, ~80-100 lines. |
| Treating MAPIE/conformal coverage as a rigorous statistical guarantee in the writeup | With only 4 LOTO folds as the source of independent calibration data, formal conformal-coverage assumptions (exchangeability, sufficient calibration-set size) are not well satisfied. Overclaiming this risks credibility with judges who understand UQ. | Report conformal intervals alongside CRPS and empirical coverage-at-quantile as a triangulated set of diagnostics, and be explicit in the writeup that N=4 groups limits how strong any generalization/calibration claim can be. |
| Building a custom deep uncertainty method (e.g., a from-scratch Bayesian layer) | Reinventing UQ machinery under an 8-day deadline is the highest-risk path available; well-supported library methods (quantile regression, deep ensembles, MC dropout, GP posterior) already cover the practical UQ space needed here. | Pick one of the above library-backed methods and get it working end-to-end before considering anything custom. |
| `uncertainty-toolbox` as a hard runtime dependency for anything beyond metrics/plots | Its PyPI release is stale (Jan 2023); relying on it for core pipeline logic risks depending on unmaintained code. | Use it only for calibration plots/metrics, and keep a manual/numpy fallback ready for any metric it doesn't compute cleanly. |

## Stack Patterns by Variant

**If time is very tight (realistic default given 8 days and this being one of several deliverables):**
- Ship the LightGBM-quantile-regression + engineered-features baseline as the complete, submitted pipeline.
- Use LOTO out-of-fold residuals pooled across all 4 folds as your conformal-calibration/coverage evaluation set (this reuses the required CV harness rather than needing a separate calibration split).
- Report CRPS (`properscoring`) + empirical coverage-at-quantile (numpy, or `uncertainty-toolbox` if it behaves) as your calibration evidence.

**If the baseline finishes early and time remains:**
- Add a small 2D-CNN or CNN-LSTM over the thermal-video tensor as a second model, trained with either MC dropout or a 3-5-seed deep ensemble for uncertainty.
- Compare its LOTO MAE / CRPS / coverage against the LightGBM baseline in the same evaluation harness — this "two independent model families agree" comparison is itself useful generalization evidence given N=4.

**If SEM-fusion (stretch goal) is pursued:**
- Keep the SEM branch as a small additional feature/CNN branch fused late (concatenated with thermal features/embedding before the final regression head), not a from-scratch multimodal architecture — minimizes new failure surface given the deadline, and keeps target-leakage masking (organizer-flagged risk) easy to reason about at a single fusion point.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|------------------|-------|
| scikit-learn 1.9.0 | MAPIE 1.4.1 | MAPIE is built as a scikit-learn-contrib package and tracks current scikit-learn; no conflict identified in current docs. |
| PyTorch 2.13 | Local GPU / CUDA | Match the `--index-url` CUDA build to the locally installed CUDA/driver version; verify with `nvidia-smi` before installing the GPU wheel, since installing the wrong CUDA build is a common first-hour time sink. |
| LightGBM 4.7.0 | numpy/scipy already in `requirements.txt` | No known conflicts; LightGBM's Python package depends only on numpy/scipy/scikit-learn, all already present. |
| `uncertainty-toolbox` 0.1.1 | numpy | Simple enough (regression-metrics-only scope) that a numpy-version conflict is unlikely, but pin the version and smoke-test immediately since it's the one stale/lower-confidence dependency in this stack. |

## Sources

- PyTorch vs TensorFlow 2026 research-share and small-dataset framework comparison — web search synthesis across multiple 2026 sources (tech-insider.org, arxiv.org/abs/2508.04035, blog.jetbrains.com) — MEDIUM confidence
- MAPIE official docs (mapie.readthedocs.io, current stable 1.4.1) — MEDIUM confidence
- Uncertainty Toolbox official docs/GitHub (uncertainty-toolbox.github.io, github.com/uncertainty-toolbox) + PyPI release-history check — MEDIUM confidence, staleness explicitly flagged
- LightGBM official docs/PyPI (lightgbm.readthedocs.io, pypi.org/project/lightgbm, v4.7.0 release 2026-07-18) — MEDIUM confidence
- scikit-learn official docs (scikit-learn.org, GaussianProcessRegressor, v1.9.0) — MEDIUM confidence
- properscoring GitHub/README (github.com/properscoring/properscoring) — MEDIUM confidence
- Deep ensembles vs. MC dropout comparison — web search synthesis across multiple arXiv sources (arxiv.org/pdf/2212.07118 and related) — MEDIUM confidence
- Manufacturing/DED precedent: CNN-BiLSTM for melt-pool/track-width prediction, GBM (RandomForest/XGBoost/LightGBM/CatBoost) for bead-geometry prediction from process data — web search synthesis across multiple 2024-2026 papers (tandfonline.com/doi/10.1080/17452759.2025.2592732, sciencedirect.com/science/article/pii/S2588840425000319, link.springer.com/article/10.1007/s00170-026-17911-2, link.springer.com/article/10.1007/s10853-024-10276-5) — MEDIUM confidence
- Small-sample overfitting risk for Transformers/LSTMs/CNNs — web search synthesis across multiple sources — MEDIUM confidence
- Cross-conformal / small-sample conformal-calibration validity considerations — web search synthesis (arxiv.org/pdf/1910.10562 and related conformal-prediction literature) — MEDIUM confidence
- NGBoost official GitHub/PyPI (github.com/stanfordmlgroup/ngboost) — LOW confidence (not cross-verified against current release)
- PyTorch Lightning vs. raw PyTorch judgment call — LOW confidence, explicitly an opinion/risk-tradeoff call for this deadline, not a verified library fact

---
*Stack research for: thermal-to-geometry uncertainty-aware prediction pipeline, DED manufacturing*
*Researched: 2026-07-19*
