# Architecture Research

**Domain:** Small-N (4-track) spatial-sequence prediction with uncertainty, thermal-to-geometry, leave-one-group-out validated research pipeline (NSF FMRG DED Data Challenge)
**Researched:** 2026-07-19
**Confidence:** HIGH (structure, data flow, build order — grounded in the organizer's own README requirements plus established ML-pipeline/leakage-prevention practice) / MEDIUM (specific model architecture choice — intentionally left generic here, resolved in STACK.md and at phase-plan time)

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     EXISTING: Raw Data Access Layer                       │
│                     src/nsf_fmrg_data.py (unchanged)                      │
│  extract_final_thermal_frames | load_wyko_asc | get_sem_tile_paths/load   │
└───────────────────────────────────┬────────────────────────────────────┘
                                     │ per-track: thermal cube + x_mm_center,
                                     │ Z_mm height map + x_actual_mm/y_mm, SEM tiles
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  NEW: Target Extraction          │  NEW: SEM Mosaic + Masking (stretch)   │
│  src/targets.py                  │  src/sem_mask.py                       │
│  Z_mm(x,y) → w_i(x) local width  │  stitch tiles → flip → mask track path │
│  (+ optional y_upper/y_lower)    │  → masked substrate patch per x_j      │
│  cached to data/processed/targets│  (isolated: thermal-only path never    │
└───────────────────┬───────────────  imports this module)                 │
                    │                └───────────────────┬────────────────┘
                    ▼                                     │ (stretch only)
┌──────────────────────────────────────────────────────────────────────────┐
│              NEW: Dataset / Sample Construction                           │
│              src/datasets.py                                              │
│  Per track i: align thermal x_mm_center grid with target x-grid via       │
│  interpolation → per-position sample {track_id, power, x_j,               │
│  thermal_window T_ij (2K+1 frames), target w_i(x_j), [masked SEM patch]}  │
│  cached to data/processed/samples/track_<id>.npz                          │
└───────────────────────────────────┬────────────────────────────────────┘
                                     │ per-track sample sets (4 total)
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│         NEW: Cross-Track (LOTO) Evaluation Harness                        │
│         src/evaluate.py                                                   │
│  For each held-out track h in {8,10,14,21}: train_tracks = other 3        │
│  → fit model (src/models.py) on train_tracks → predict on track h         │
│  → compute MAE, spatial-variation preservation, calibration/coverage      │
│  Fold splitting is track-atomic — never splits within a track             │
└───────────────────────────────────┬────────────────────────────────────┘
                                     │ per-fold predictions + metrics
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│              NEW: Submission / Reporting Module                           │
│              scripts/make_submission_figures.py                           │
│  Aggregate metrics across folds → prediction-vs-ground-truth curves with  │
│  uncertainty bands, calibration plots, cross-track summary table          │
│  → results/figures/*.png, results/metrics.json, results/predictions/*.npz │
│  (feeds the separately-authored report/slide deck — out of pipeline scope)│
└──────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|-------------------------|
| Raw data access (existing) | Load/orient/align one modality for one track to the shared 20-100mm coordinate | Pure functions returning dicts, already in `src/nsf_fmrg_data.py` — do not modify |
| Target extraction | Derive `w_i(x)` (and optionally boundary functions) from each track's height map at a well-defined resampled x-grid; document the method (edge-detection threshold on `Z_mm` cross-sections, or similar) so it is reproducible | Module of pure functions, one "extract" entry point per track, results cached to disk as versioned artifacts |
| Dataset/sample construction | Reconcile the thermal frame grid (0.2 mm/frame) with the target x-grid (height-map pixel resolution, ~3.98 µm/pixel) via interpolation onto one canonical `x_j` grid per track; assemble `(T_ij, x_j, track_id, power, target)` tuples; optionally attach masked SEM patch | A `build_track_samples(track_id)` function + a thin `Dataset`/array wrapper for the model framework |
| SEM masking utility (stretch) | Stitch SEM tiles per organizer-confirmed procedure (ascending order → `np.fliplr` mosaic), then mask the processed-track region with a documented, track-invariant physical-coordinate rule + safety margin | Isolated module; only imported by the stretch dataset path, never by the thermal-only baseline |
| Model | Map a thermal window (and optionally masked SEM patch + metadata) to a predicted distribution over local geometry (mean + uncertainty) | A small `predict(inputs) -> (mean, uncertainty)` interface; internals (CNN, GP, quantile regressor) are swappable behind this boundary |
| Training loop | Fit one model instance given an explicit list of training tracks; save checkpoint + the exact config/track-split/target-extraction-version used | Plain imperative training function, not a generic `Trainer` framework |
| Cross-track evaluation harness | Own the leave-one-track-out fold definition, invoke training loop per fold, run inference on the held-out track, compute and store metrics | One `run_cv()` entry point iterating `for held_out in TRACK_IDS`, track-atomic splits enforced structurally (never row-level) |
| Submission/reporting | Turn stored per-fold predictions/metrics into final figures and a results table; does not retrain anything | Script(s) consuming `results/` artifacts only, matplotlib figures matching report requirements |

## Recommended Project Structure

```
src/
├── nsf_fmrg_data.py       # existing — raw loaders, untouched
├── targets.py             # NEW — height-map -> w_i(x)/boundary extraction, versioned/cached
├── datasets.py            # NEW — x-grid alignment + per-track sample assembly
├── sem_mask.py            # NEW (stretch) — SEM stitching + track-region masking, isolated
├── models.py              # NEW — model definitions behind predict(...) -> (mean, uncertainty)
├── evaluate.py            # NEW — LOTO fold harness + metrics (MAE, variation preservation, calibration)
└── viz.py                 # NEW (optional) — shared plotting helpers (target QA, prediction curves)

scripts/
├── run_thermal_video_export.py   # existing
├── extract_targets.py            # NEW CLI — run target extraction for all 4 tracks + QA plots
├── build_dataset.py              # NEW CLI — build cached per-track sample manifests
├── run_cv.py                     # NEW CLI — run one or all LOTO folds, save checkpoints/predictions/metrics
└── make_submission_figures.py    # NEW CLI — aggregate results/ into final report-ready figures

notebooks/
├── 01_*.ipynb, 02_*.ipynb        # existing — untouched
└── 03_exploration_*.ipynb        # NEW, exploration-only — nothing pipeline-critical may live only here

data/
├── raw/                          # existing, immutable
└── processed/                    # NEW, gitignored, fully regenerable from raw
    ├── targets/track_<id>.npz    # cached target-extraction output
    └── samples/track_<id>.npz    # cached aligned sample manifests

results/                          # NEW (mirrors existing processed_data/ convention)
├── checkpoints/<held_out_track>/
├── predictions/<held_out_track>.npz
├── metrics.json
└── figures/*.png
```

### Structure Rationale

- **New `src/*.py` modules, not a `src/nsf_fmrg_data/` package rewrite:** the existing flat-module convention (per `.planning/codebase/STRUCTURE.md`) is preserved; splitting only the *new* concerns into their own files keeps each file single-purpose without a packaging migration the 8-day timeline doesn't need.
- **`sem_mask.py` isolated from `datasets.py`:** the PROJECT.md scope explicitly sequences thermal-only baseline before SEM fusion (stretch). Keeping the masking utility in its own module means the core dataset builder has zero import-time dependency on it — the stretch work literally cannot break the baseline path.
- **`data/processed/` and `results/` are caches/outputs, not source:** target extraction and sample construction are the most fragile, hand-rolled steps in this pipeline (no organizer-provided ground-truth extractor exists). Caching their output to disk (a) avoids re-deriving them on every experiment iteration, (b) makes it possible to diff/inspect the exact target values a model trained against, and (c) lets the evaluation harness assert it is scoring against the same cached target version used in training.
- **No `pyproject.toml`/packaging added:** the existing `sys.path`-manipulation pattern in `scripts/` is a known anti-pattern but fixing it has no payoff within an 8-day research-competition sprint with one developer. Continue the existing convention for new scripts rather than introducing installable-package overhead.
- **No generic `Trainer`/config-framework abstraction:** with 4 tracks and a handful of experiment variants, a plain function-per-fold training loop with explicit arguments is easier to debug under deadline pressure than a configurable experiment-management framework (Hydra, PyTorch Lightning `Trainer`, etc.). Introduce such tooling only if iteration volume later demands it — it currently would not.

## Architectural Patterns

### Pattern 1: Cached, Versioned Intermediate Artifacts

**What:** Every expensive or hand-designed derivation (target extraction, sample alignment) writes its output to `data/processed/` once, and all downstream steps read from that cache rather than recomputing from raw files.
**When to use:** Any step whose correctness cannot be checked by construction (e.g., target extraction is a judgment call, not a deterministic unit-testable transform) — caching turns it into an inspectable, diffable artifact you can visually QA once and then treat as ground truth for the rest of the sprint.
**Trade-offs:** Requires discipline to invalidate/regenerate the cache when the extraction method changes (a version tag or filename suffix is enough at this scale) — but the alternative (recomputing inline every run) hides bugs and makes it easy to accidentally evaluate against a different target definition than the model was trained on.

**Example:**
```python
# scripts/extract_targets.py
for track_id in TRACK_IDS:
    hm = load_wyko_asc(HEIGHT_DIR, track_id)
    target = extract_local_width(hm)          # src/targets.py
    save_target(target, PROCESSED_DIR / f"targets/track_{track_id}.npz")
    plot_target_qa(hm, target, out=f"processed_data/qa/track_{track_id}_target.png")
```

### Pattern 2: Track-Atomic Fold Splitting Enforced Structurally

**What:** The evaluation harness never operates on a flat table of rows that happens to contain a `track_id` column filtered post hoc. Instead, samples are constructed and stored *per track* (`track_<id>.npz`), and a fold is simply "3 of these files for training, 1 for testing." There is no code path that can accidentally mix rows from the held-out track into training, because the held-out track's file is never opened during fitting.
**When to use:** Any small-N, spatially/temporally correlated dataset where the failure mode is "technically excluded the right rows, but leaked information anyway" (e.g., via global normalization statistics computed across all 4 tracks before splitting, or via hyperparameters tuned while glancing at held-out-track performance).
**Trade-offs:** Slightly less flexible than a single global dataframe with a `.filter()` call, but the rigidity is the point — it makes leakage structurally harder, not just procedurally discouraged. Any normalization statistics (e.g., thermal intensity scaling) must be computed only from the 3 training tracks' files inside the fold loop, never precomputed globally.

**Example:**
```python
# src/evaluate.py
def run_cv(track_ids=(8, 10, 14, 21)):
    results = {}
    for held_out in track_ids:
        train_ids = [t for t in track_ids if t != held_out]
        norm_stats = fit_normalization(train_ids)          # from train tracks only
        model = train_model(train_ids, norm_stats)          # src/models.py
        preds = model.predict(load_samples(held_out), norm_stats)
        results[held_out] = compute_metrics(preds, load_target(held_out))
    return results
```

### Pattern 3: Baseline-First Harness Validation

**What:** Before any real model is written, the evaluation harness is exercised end-to-end with a trivial, intentionally-dumb predictor (e.g., predict each training track's mean width, or nearest-neighbor lookup by laser power). This produces a first set of metrics/figures through the *entire* pipeline (targets → samples → folds → metrics → figures) using only components that are already trusted.
**When to use:** Whenever the evaluation harness itself is new and non-trivial (track-atomic LOTO + calibration metrics + figure generation) — the goal is to catch harness bugs (e.g., an off-by-one in x-grid alignment, a metric computed on the wrong array shape, a leaked normalization) using a predictor with obvious, hand-checkable expected output, before that bug gets misattributed to "the model needs more work."
**Trade-offs:** Costs a small amount of upfront time that could feel like it's not "real model progress" — but the alternative (finding the harness bug after spending days tuning a real model against it) is the single biggest risk this 8-day sprint faces.

## Data Flow

### End-to-End Flow (raw files → submission figures)

```
data/raw/{thermal,sem,height_maps}/  (per track: 8, 10, 14, 21)
    ↓  src/nsf_fmrg_data.py loaders (existing, unchanged)
per-track: thermal cube + x_mm_center | Z_mm height map + x_actual_mm | SEM tile paths
    ↓  src/targets.py  (NEW — Phase 1, must be validated first)
per-track target curve  w_i(x)  [+ optional y_upper(x), y_lower(x)]
    ↓  cached: data/processed/targets/track_<id>.npz  +  QA plot per track
    ↓  src/datasets.py  (NEW — Phase 2)
per-track aligned samples: {track_id, power, x_j, T_ij (thermal window), target(x_j), [masked SEM patch]}
    ↓  cached: data/processed/samples/track_<id>.npz
    ↓  src/evaluate.py: run_cv()  (NEW — Phase 3, validated with dummy predictor BEFORE Phase 4)
        for held_out in {8,10,14,21}:
            train on other 3 tracks  →  src/models.py (NEW — Phase 4)
            predict on held_out track
    ↓  per-fold predictions + metrics
results/predictions/<held_out>.npz, results/metrics.json
    ↓  scripts/make_submission_figures.py  (NEW — Phase 5, last)
results/figures/*.png  (prediction-vs-ground-truth curves w/ uncertainty bands,
                        calibration/coverage plots, cross-track summary table)
    ↓  (consumed externally, out of pipeline scope)
report PDF + slide deck (authored separately by the user)
```

### Key Data Flows

1. **Target-extraction flow (height map → training/eval label):** This is the *only* place the "ground truth" is defined, and it feeds both model training (as the label) and evaluation (as the comparison target). Because there is no organizer-provided extractor, this flow must be built, visually sanity-checked against all 4 tracks (including track 21's incomplete profilometry — decide and document a NaN/gap-handling rule), and frozen/cached before it is trusted as either a training label or an evaluation ground truth.
2. **Coordinate-alignment flow (thermal grid ↔ target grid):** Thermal frames arrive on a 0.2 mm/frame grid; the target arrives on the height map's much finer native pixel grid. `src/datasets.py` is the single place these are reconciled onto one canonical per-track `x_j` grid via interpolation — if this alignment is subtly wrong (e.g., a coordinate direction flip, as already called out for SEM tiles in the README), every downstream training signal is corrupted silently. Validate with an overlay plot (thermal frame's `x_mm_center` vs. target curve's `x` at the same physical location) before proceeding to Phase 3.
3. **Fold-isolation flow (train tracks → held-out track):** No information (raw data, cached targets, cached samples, normalization statistics, or hyperparameter choices) may cross from a held-out track into the training side of its own fold. This is enforced by the per-track file boundary described in Pattern 2, not by post hoc filtering.
4. **Reporting flow (metrics/predictions → figures):** Strictly one-directional and read-only against `results/` — regenerating figures never re-triggers training, keeping the "make the report figures" step fast and safe to re-run repeatedly during the final packaging days.

## Recommended Build Order (Risk-Minimizing Sequence for the 8-Day Deadline)

This is the most decision-relevant output for roadmap phase sequencing. Dependencies flow strictly downward — do not start a later step before the one above it is validated, because every later step's correctness is conditioned on the one before it being right.

1. **Target extraction (`src/targets.py` + `scripts/extract_targets.py`) — build and visually validate against all 4 height maps FIRST, before writing any model code.**
   Validation gate: for each of the 4 tracks, the extracted `w_i(x)` curve is plotted against the raw height-map cross-section and passes a sanity check (higher laser power ⇒ visibly wider track, consistent with the README's stated 400W>350W>300W>200W ordering; track 21's incomplete-coverage gaps are handled by an explicit, documented rule, not silently dropped/interpolated).
   *Why first:* every downstream number (training label, evaluation ground truth) depends on this. A wrong extractor invalidates the entire pipeline retroactively — there is no way to "fix it later" without redoing every subsequent step.

2. **Dataset/sample construction (`src/datasets.py` + `scripts/build_dataset.py`) — align thermal and target grids, cache per-track samples.**
   Validation gate: an overlay plot per track confirming thermal `x_mm_center` and target `x` refer to the same physical location at the same index; spot-check that the frame windows (`2K+1` around `x_j`) don't run off the 20-100mm window edges without an explicit boundary policy.
   *Why second:* depends on step 1's cached target; must be right before any model sees data, since a coordinate misalignment here produces a model that appears to "work" (loss decreases) while learning a spatially shifted, wrong relationship.

3. **Cross-track (LOTO) evaluation harness (`src/evaluate.py`) — build and validate with a trivial dummy predictor BEFORE any real model exists.**
   Validation gate: run all 4 folds with a mean-baseline or nearest-neighbor-by-power predictor; confirm (a) track-atomic isolation holds (inspect that held-out track's data never appears in the training call), (b) metrics (MAE, spatial-variation preservation, calibration/coverage) compute without error and produce non-degenerate, hand-checkable numbers, (c) the figure-generation step runs end-to-end on this dummy output.
   *Why third, and why before modeling:* this is the harness the real model will be judged and iterated against. If it is leaky or buggy, every subsequent hour spent "improving the model" is optimizing against a broken signal — the single highest-risk failure mode for this 8-day sprint. **This step must be complete and validated before Phase 4 (model training) begins.**

4. **Model + training loop (`src/models.py` + training entry point) — start with the simplest probabilistic model that fits the harness's `predict(...) -> (mean, uncertainty)` interface.**
   Given only 3 tracks' worth of training data per fold (~1,200 positions), favor a low-capacity architecture (e.g., a small CNN or handcrafted thermal descriptors feeding a shallow probabilistic head with a Gaussian NLL or quantile loss) over a deep model — overfitting risk is high at this sample size, and model-architecture depth is a lower priority than getting one correct, well-calibrated baseline through the validated harness.
   *Why fourth:* only meaningful once 1-3 are trustworthy; the harness from step 3 is reused unchanged, so iterating on model choice here is cheap and safe.

5. **SEM masking + fused model variant (`src/sem_mask.py`) — stretch, only after step 4's thermal-only baseline is complete and evaluated end-to-end.**
   *Why last before reporting:* explicitly deprioritized in PROJECT.md scope; isolating it in its own module (Pattern above) means it can be dropped entirely if time runs out without touching the working baseline.

6. **Submission/reporting (`scripts/make_submission_figures.py`) — last, and re-run cheaply as many times as needed.**
   Consumes only `results/` artifacts from steps 3-5; never retrains. Safe to iterate on figure polish in the final day(s) without re-running the expensive steps.

**Summary of the non-negotiable gate:** steps 1-3 (target extraction → alignment → leak-free harness, each independently validated) must all be done *before* step 4 (model training) starts. Given the 8-day window, budget roughly the first third of the sprint for steps 1-3 even though they produce no "model results" yet — this is deliberate front-loading of risk, not lost time.

## Scaling Considerations

There is no user-scale axis here; the relevant "scale" axis is *how much of the stretch scope gets attempted* given the fixed 4-track, 8-day constraints.

| Scope level | Architecture Adjustments |
|-------|--------------------------|
| Thermal-only baseline (MVP, steps 1-4 above) | Single modality input to `models.py`; `sem_mask.py` never imported; simplest viable probabilistic head |
| + SEM-fused variant (stretch) | `datasets.py` gains an optional masked-SEM-patch field (already designed for in Pattern above); `models.py` gains a second model variant behind the same `predict(...)` interface so the evaluation harness needs zero changes |
| + Additional geometry descriptors (roughness, waviness, boundary asymmetry) | Extend `targets.py`'s output schema (additional named fields alongside `w_i(x)`) and `evaluate.py`'s metrics dict; harness fold-splitting logic is unaffected since it operates on tracks, not descriptor count |

### Scaling Priorities

1. **First bottleneck: sample count (~1,200 training positions per fold).** Addressed by preferring low-capacity/regularized models and by treating each fold's metrics as noisy (4 folds is a small sample of folds too) — report per-fold spread, not just a mean, in the final figures.
2. **Second bottleneck: iteration time for target-extraction QA.** If the extraction method needs revision mid-sprint, the cached-artifact pattern (Pattern 1) keeps this cheap — only `scripts/extract_targets.py` reruns, not the whole pipeline — but every downstream cache becomes stale and must be regenerated; keep the cache regeneration path (`extract_targets.py` → `build_dataset.py` → `run_cv.py`) scriptable as a single sequence for exactly this reason.

## Anti-Patterns

### Anti-Pattern 1: Tuning Hyperparameters or Target-Extraction Parameters Against the Held-Out Track

**What people do:** Peek at how well the model does on track 21 (or whichever track is held out in a given fold) while still adjusting the target-extraction thresholds, model hyperparameters, or normalization scheme.
**Why it's wrong:** This silently converts the held-out track into a validation set the model (and the human) has fit to, defeating the entire purpose of leave-one-track-out validation and inflating reported performance in a way the organizers' standardized evaluation will not reproduce.
**Instead:** Fix target-extraction parameters and model hyperparameters using only comparisons across the 3-track LOTO sub-folds (i.e., treat one of the 3 training tracks as a dev/validation track while iterating, never the track that will be the actual held-out report figure), then run the true held-out evaluation once parameters are frozen.

### Anti-Pattern 2: Global Normalization Statistics Computed Before Fold Splitting

**What people do:** Compute thermal-intensity mean/std, or target-value min/max, once across all 4 tracks, then reuse those constants inside every fold's training and inference.
**Why it's wrong:** The held-out track's data literally contributed to the numbers the model is normalized/trained against — a subtle but real leakage channel, especially given only 4 tracks where each one has outsized influence on any global statistic.
**Instead:** Compute normalization statistics inside the fold loop, from the 3 training tracks only (see Pattern 2's code example), and apply those same fold-specific statistics to the held-out track at inference time.

### Anti-Pattern 3: Treating a Notebook as the Pipeline's Source of Truth

**What people do:** Iterate the target-extraction logic, model, and evaluation directly inside a notebook cell, with no corresponding `src/`/`scripts/` version — "it works in the notebook" becomes the only record of how results were produced.
**Why it's wrong:** The submission requires reproducible, executable code; a notebook-only pipeline is fragile to cell-execution-order bugs and hard to re-run identically for the required end-to-end reproducibility. It also makes the cached-artifact/versioning pattern above impossible to enforce.
**Instead:** Keep notebooks (`notebooks/03_exploration_*.ipynb`) strictly for exploration/visualization/scratch work; anything that produces a cached artifact, a trained model, or a reported figure must live in `src/` + `scripts/` and be runnable non-interactively (`python scripts/run_cv.py`).

### Anti-Pattern 4: Building a General Experiment-Configuration Framework

**What people do:** Introduce Hydra/OmegaConf-style hierarchical configs, a plugin/registry system for models, or a generic `BaseModel`/`BaseTrainer` class hierarchy up front, anticipating many future model variants.
**Why it's wrong:** With 4 tracks, one baseline model, and at most one stretch variant (SEM-fused), this is speculative generality that consumes sprint time without a payoff — the actual variation the project needs (thermal-only vs. SEM-fused) is already handled by the `predict(...) -> (mean, uncertainty)` interface boundary in Pattern above.
**Instead:** Plain functions/small classes with explicit arguments; a simple `argparse` CLI per script (matching the existing `scripts/run_thermal_video_export.py` convention) is sufficient configuration surface for this timeline.

## Integration Points

### External Services

None. This is a fully local, offline pipeline — no APIs, no cloud services, no databases. (Data-use license also prohibits any external service that would move the competition-restricted dataset off local infrastructure.)

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `nsf_fmrg_data.py` ↔ `targets.py` | Direct function call, in-memory dicts (existing return-dict convention) | `targets.py` consumes `load_wyko_asc()`'s output dict directly; no new data contract needed |
| `targets.py` ↔ `datasets.py` | Cached `.npz` file (`data/processed/targets/track_<id>.npz`) | Decouples the two steps so target re-extraction doesn't require reloading/rebuilding thermal windows, and vice versa |
| `datasets.py` ↔ `evaluate.py` | Cached `.npz` file (`data/processed/samples/track_<id>.npz`), one file per track | The fold-isolation contract lives here: `evaluate.py` only ever opens 3 of the 4 files for training |
| `evaluate.py` ↔ `models.py` | In-process function call: `predict(inputs) -> (mean, uncertainty)` | Framework-agnostic boundary; the concrete modeling library (deferred to `STACK.md`) is swappable without touching the harness |
| `sem_mask.py` ↔ `datasets.py` | Optional field in the sample dict, populated only if the stretch path is enabled | Keeps the stretch feature additive and structurally unable to break the thermal-only baseline |
| `evaluate.py`/`results/` ↔ `make_submission_figures.py` | Read-only file consumption of `results/predictions/*.npz` and `results/metrics.json` | One-directional; regenerating figures never re-triggers training |

## Sources

- Organizer-confirmed task, alignment, masking, and evaluation requirements — `README.md` (this repo; primary source, HIGH confidence, authoritative per PROJECT.md)
- Existing codebase structure/conventions — `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md` (this repo; direct inspection, HIGH confidence)
- Spatial/grouped cross-validation leakage prevention (buffered/spatial leave-one-out, track-atomic fold isolation): [The problematic case of data leakage: leave-profile-out cross-validation](https://www.sciencedirect.com/science/article/pii/S0016706125000618) (peer-reviewed, MEDIUM-HIGH confidence); [Assessing spatial cross-validation approaches for spatially structured data](https://arxiv.org/pdf/2303.07334) (preprint, MEDIUM confidence); [Iterative spatial leave-one-out cross-validation](https://www.tandfonline.com/doi/full/10.1080/15481603.2022.2107113) (peer-reviewed, MEDIUM-HIGH confidence)
- Data-science project layout conventions (src/scripts/notebooks separation, cached intermediate data): [Cookiecutter Data Science](https://cookiecutter-data-science.drivendata.org/) / [drivendataorg/cookiecutter-data-science](https://github.com/drivendataorg/cookiecutter-data-science) (widely-adopted community standard, MEDIUM-HIGH confidence — adapted, not adopted wholesale, given the 8-day scope)

---
*Architecture research for: thermal-to-geometry prediction pipeline, NSF FMRG DED Data Challenge*
*Researched: 2026-07-19*
