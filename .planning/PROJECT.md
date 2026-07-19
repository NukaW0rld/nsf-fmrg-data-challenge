# NSF FMRG Data Challenge — Thermal-to-Geometry Prediction Pipeline

## What This Is

A reproducible, end-to-end pipeline for the NSF Future Manufacturing Data Challenge. It converts raw thermal, SEM, and profilometry data into spatially aligned samples, derives a physically defensible local track-geometry target from the height maps, predicts that geometry and its uncertainty from thermal history (optionally fused with masked SEM context), validates generalization across held-out tracks, and produces the code and figures required for competition submission.

## Core Value

A thermal-only baseline that runs end-to-end — raw data in, cross-track-validated local-width predictions with calibrated uncertainty out — must work before anything else matters. Given the 8-day runway to the deadline, a complete simple pipeline beats an incomplete ambitious one.

## Business Context

- **Customer**: Competition judges/organizers — NSF Future Manufacturing Data Challenge, Texas A&M Institute of Data Science
- **Revenue model**: N/A — prize-based competition ($1,000 / $500 / $300 + $100 Best Presentation + $100 Most Innovative Approach)
- **Success metric**: Quantitative evaluation (local width/boundary error, preservation of spatial variation, uncertainty calibration) plus finalist selection (top 3-5 teams present to judges)
- **Strategy notes**: Full rules and organizer clarifications in `README.md` (repo root)

## Requirements

### Validated

- ✓ Thermal `.mat` loading with HDF5 fallback, laser-on segment detection, physical-coordinate assignment — existing (`src/nsf_fmrg_data.py`)
- ✓ SEM tile path listing/loading per track — existing (`src/nsf_fmrg_data.py`)
- ✓ Wyko `.ASC` height-map parsing, coordinate reorientation/cropping to 20-100mm window, robust plane detrending — existing (`src/nsf_fmrg_data.py`)
- ✓ Thermal video export CLI for visualization/QA — existing (`scripts/run_thermal_video_export.py`)

### Active

- [ ] Extract a local track-width target `w_i(x)` from height maps, with a documented, reproducible method (no organizer-provided extractor exists)
- [ ] Build a multimodal-aligned sample dataset: thermal video tensor (`2K+1` frames centered on position `x_j`) + physical coordinate + track id + laser power, across the shared 20-100mm window
- [ ] Cross-track validation harness — leave-one-track-out, with track 21 (200W, least-complete profilometry) as the recommended conservative held-out case
- [ ] Uncertainty-aware model predicting local width from thermal history (thermal-only baseline)
- [ ] Evaluation metrics: MAE for local width, spatial-variation preservation, calibration/coverage of predicted uncertainty
- [ ] Reproducible submission-ready code (executable end-to-end) + required figures
- [ ] SEM stitching + track-masking utility, preventing target leakage (stretch — only pursued once the thermal-only baseline is complete)
- [ ] SEM-fused model variant combining thermal + masked SEM context (stretch)

### Out of Scope

- Written report and slide deck — produced separately by the user outside this pipeline; this project covers code, pipeline, and figures only
- Boundary-function prediction (separate left/right boundary curves) — deferred past v1; width is the simpler target that satisfies the minimum submission requirement
- Building full multimodal (thermal+SEM) fusion as the initial/core model — explicitly deprioritized in favor of a complete thermal-only baseline first, given the 8-day timeline
- Raw data acquisition/download tooling — Zenodo data for all 4 tracks is already downloaded locally under `data/raw/`

## Context

- Existing codebase is a data-science utility library, not a packaged app: single flat module `src/nsf_fmrg_data.py`, two starter notebooks, one CLI script. No `pyproject.toml`/`setup.py`, no tests, unpinned `requirements.txt` (numpy, scipy, matplotlib, pillow, pandas).
- Raw dataset already present locally for all 4 track conditions (8, 10, 14, 21) under `data/raw/{thermal,sem,height_maps}/` — no download step needed.
- Track ↔ laser power: 8=400W, 10=350W, 14=300W, 21=200W (held out, organizer-recommended test track).
- No modeling framework selected yet — left open, to be resolved during phase-level research given the local-GPU constraint.
- Data is restricted to competition use only (see `DATA_USE_LICENSE.md`) — no reuse outside the competition.
- Organizer clarifications (SEM stitching/masking, evaluation framework, validation strategy) are already captured in `README.md` and should be treated as authoritative requirements, not suggestions.

## Constraints

- **Timeline**: 8 days to submission deadline (today 2026-07-19, due 2026-07-27) — favors coarse phases and a working baseline before polish
- **Compute**: Local GPU available — model choices should fit that budget; no requirement for distributed/cloud-scale training
- **Data volume**: Only 4 track conditions exist — cross-track (leave-one-out) validation is required; random/neighboring-sample splits within a track are invalid due to spatial correlation
- **Data licensing**: Dataset is competition-restricted per `DATA_USE_LICENSE.md` — no external reuse or sharing
- **Methodology**: SEM input (if used) must mask the processed track region — target leakage is an explicit failure mode called out by organizers
- **Reproducibility**: Submission requires executable code — the pipeline must run end-to-end from raw data to figures/predictions, not just a describe-only report

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Thermal-only baseline before SEM fusion | 8-day deadline; de-risk by shipping one complete, validated pipeline before adding complexity | — Pending |
| Local width `w_i(x)` as the v1 geometry target | Simplest target that satisfies the minimum submission requirement; boundary functions are richer but deferred | — Pending |
| Leave-one-track-out cross-validation | Only 4 tracks total; random splits leak spatially correlated neighboring samples | — Pending |
| Report and slide deck out of scope for this pipeline | User handles those separately; this project's scope is code/pipeline/figures | — Pending |
| Modeling framework left open | Not yet decided; resolved via phase research against the local-GPU constraint | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-19 after initialization*
