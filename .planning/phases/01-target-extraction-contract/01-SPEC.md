# Phase 1: Target Extraction & Contract — Specification

**Created:** 2026-07-19
**Ambiguity score:** 0.17 (gate: ≤ 0.20)
**Requirements:** 2 locked

## Goal

A single, documented local-width extraction rule (`w_i(x) = y_upper,i(x) − y_lower,i(x)`) is applied identically to all 4 height-map tracks (8, 10, 14, 21), producing a per-track cached target artifact on a shared 0.2mm x-grid that is visually confirmed sane before any downstream phase depends on it as ground truth.

## Background

No organizer-provided width extractor or label file exists (README §"Ground-truth clarification") — participants must define and justify their own post-processing method. `src/nsf_fmrg_data.py` currently provides `load_wyko_asc()` (loads/crops/reorients Wyko `.ASC` height maps to the shared 20–100mm window) and `robust_plane_detrend()` (outlier-resistant plane fit), but no width/boundary extraction code exists yet — no `src/targets.py` or equivalent module is present in the repo. A prior discuss-phase session already locked 16 implementation decisions (D-01–D-16, `01-CONTEXT.md`) covering the edge-detection method, Track 21 gap-handling, smoothing, and detrending approach; this SPEC captures the what/why these decisions serve and adds the falsifiable acceptance layer, output-artifact boundary, and anti-circularity/raw-data-safety guards that CONTEXT.md's implementation-decision format doesn't itself state as pass/fail checks.

## Requirements

1. **TARGET-01 — Extraction contract locked**: The local-width target contract is specified and documented before extraction code is written.
   - Current: No contract exists in a standalone document; the width formula is only stated informally in the organizer's README.
   - Target: The contract — width definition `w_i(x) = y_upper,i(x) − y_lower,i(x)`; relative half-max threshold rule (per-column 5th/95th percentile baseline/peak, 0.5 fraction); minimum peak-baseline separation validity check; Savitzky-Golay smoothing on boundaries separately (~1mm window, order 2–3, edge/interp boundary mode); fixed 0.2mm output x-grid shared across all 4 tracks; boolean valid-coordinate mask; Track 21 gap-handling rule (≤10 consecutive NaN interpolated along y per-column, else invalidate that x-column) — is fully captured in `01-CONTEXT.md`'s decisions D-01 through D-16, which stand as the reviewed, locked contract. No separate contract document is required.
   - Acceptance: `01-CONTEXT.md` exists, is committed, and its D-01–D-16 decisions collectively answer: width definition, threshold rule, smoothing scale/method, output grid resolution, valid-coordinate mask definition, and the Track 21 gap rule — verified by checklist review against this list.

2. **TARGET-02 — Extractor implemented, persisted, and visually QA'd**: The height-map target extractor implements the locked TARGET-01 contract, persists results to disk, and is visually validated against all 4 tracks before being trusted downstream.
   - Current: No extraction code exists. No `processed_data/targets/` directory or per-track cached artifact exists.
   - Target: A new module (e.g. `src/targets.py`) implements the D-01–D-16 contract using `load_wyko_asc()` and `robust_plane_detrend()` from `src/nsf_fmrg_data.py`, applying the identical rule/parameterization to all 4 tracks with no per-track-tuned thresholds. For each track, it persists `w_i(x)`, `y_upper(x)`, `y_lower(x)`, the x-grid, and the boolean valid-coordinate mask to disk under `processed_data/targets/` (one file per track, float64 dtype) on the shared 0.2mm grid. QA overlay plots (extracted width/boundary on both raw and detrended height maps) are produced and visually reviewed for all 4 tracks, including Track 21's gap-heavy regions.
   - Acceptance: Running the extractor on tracks 8, 10, 14, and 21 (a) produces a `processed_data/targets/` file per track containing `w_i(x)`, boundaries, x-grid, and valid mask at float64 precision; (b) produces a per-track mean/median width ordering of 400W(8) > 350W(10) > 300W(14) > 200W(21), confirmed by visual/numeric inspection; (c) produces QA overlay plots for all 4 tracks that a human reviewer confirms show no sawtooth/high-frequency jitter and no silently dropped gaps; (d) uses one identical parameterization across all 4 tracks, confirmed by code inspection.

## Boundaries

**In scope:**
- The `01-CONTEXT.md` D-01–D-16 decision set, serving as the reviewed TARGET-01 contract (no separate contract document produced)
- A new extraction module implementing that contract against all 4 tracks with one shared parameterization
- Per-track persisted output artifacts under `processed_data/targets/` (float64, shared 0.2mm grid) — this phase owns caching, not Phase 2
- QA overlay plots (raw + detrended height map with extracted width/boundary) for all 4 tracks, including Track 21's gaps
- A mandatory visual check of post-detrend residual maps for all 4 tracks (D-14) before the extractor is trusted

**Out of scope:**
- Boundary-function *prediction* (TARGET-03) — this phase only *extracts* ground-truth boundaries from height maps, it does not predict them from thermal data (that's Phase 4, v1 modeling)
- Thermal/target coordinate-grid alignment and sample construction — that is Phase 2 (DATA-01, DATA-02)
- Any leave-one-track-out splitting, normalization, or model fitting — that is Phase 3/4; Phase 1 produces ground truth only, independent of any train/test split
- Upgrading `robust_plane_detrend()` to a higher-order surface fit — deferred unless the D-14 residual-curvature QA check surfaces an actual problem (per CONTEXT.md, not preemptive)
- Roughness, waviness, or any geometry descriptor beyond width/boundary — explicitly out of v1 scope per `REQUIREMENTS.md`

## Constraints

- Output x-grid is fixed at 0.2mm spacing, identical length/positions across all 4 tracks (D-07) — Phase 2 depends on this exact grid for thermal alignment.
- Persisted target arrays use float64 dtype, matching `load_wyko_asc()`'s existing output precision.
- Extraction parameters (percentile split, half-max fraction, noise-floor minimum, gap limit, SG window/order) are single scalar constants applied uniformly to all 4 tracks — no per-track branching or tuned values.
- Extraction and persistence code must not write to, delete, or modify any file under `data/raw/` — that data is unversioned in git and irreplaceable; outputs only go to `processed_data/targets/`.

## Acceptance Criteria

- [ ] `01-CONTEXT.md` (D-01–D-16) is committed and covers width definition, threshold rule, smoothing, grid resolution, valid-coordinate mask, and Track 21 gap rule
- [ ] A new extraction module runs against all 4 tracks (8, 10, 14, 21) using one identical parameterization (confirmed by code inspection — no per-track branches or tuned constants)
- [ ] Each of the 4 tracks has a persisted `processed_data/targets/` artifact containing `w_i(x)`, `y_upper(x)`, `y_lower(x)`, x-grid, and valid-coordinate mask at float64 precision
- [ ] Per-track mean/median width ordering is 400W(8) > 350W(10) > 300W(14) > 200W(21) (visual/numeric inspection)
- [ ] QA overlay plots (raw + detrended) exist for all 4 tracks and are visually confirmed to show no sawtooth/high-frequency jitter and no silently dropped gaps
- [ ] Post-detrend residual maps for all 4 tracks are visually inspected and confirmed to show no obvious remaining bow/curvature (D-14)
- [ ] A checksum/mtime check confirms no file under `data/raw/` was modified by running the extraction pipeline

## Edge Coverage

**Coverage:** 8/10 applicable edges resolved · 0 unresolved (2 dismissed — not applicable)

| Category | Requirement | Status | Resolution / Reason |
|----------|-------------|--------|---------------------|
| boundary | R1 (TARGET-01) | ✅ covered | D-04/D-06 already define exact threshold semantics: exactly at the noise-floor minimum is valid (only *below* invalidates); exactly 10 consecutive NaNs is still interpolated (only *exceeding* 10 invalidates). |
| adjacency | R1 (TARGET-01) | ✅ covered | SG smoothing window is allowed to blend valid points from both sides of a masked gap (standard `savgol_filter` NaN-skip behavior) — resolved via interview. |
| empty | R1 (TARGET-01) | ✅ covered | A track with zero valid x-positions after masking raises a hard error rather than silently producing an all-NaN artifact — resolved via interview. |
| ordering | R1 (TARGET-01) | ⛔ dismissed | No data-dependent sort/ordering operation exists in the extraction algorithm — the output x-grid order is fixed by construction (D-07), not computed from comparisons. |
| precision | R1 (TARGET-01) | ✅ covered | Percentile calculation uses numpy's default (linear interpolation) convention; a crossed-boundary case (`y_upper < y_lower`, negative width) marks that x-column invalid in the mask rather than reporting a negative or clipped-to-zero width — resolved via interview. |
| boundary | R2 (TARGET-02) | ✅ covered | Crop-edge (20mm/100mm) behavior is D-12's SG edge/interp boundary mode, documented as visually inspectable in QA plots. |
| adjacency | R2 (TARGET-02) | ✅ covered | D-07: invalid x-positions keep their grid slot with `width=NaN`, `mask=False` — no ragged/dropped positions at valid/invalid boundaries. |
| empty | R2 (TARGET-02) | ✅ covered | Same as R1: all-invalid track raises a hard error (Acceptance Criteria, Requirement 2). |
| ordering | R2 (TARGET-02) | ⛔ dismissed | Same as R1 — persisted output grid order is fixed by construction, not data-dependent. |
| precision | R2 (TARGET-02) | ✅ covered | Persisted arrays use float64 dtype (Constraints) — resolved via interview. |

## Prohibitions (must-NOT)

**Coverage:** 2/2 applicable prohibitions resolved · 0 unresolved

| Prohibition (must-NOT statement) | Requirement | Status | Verification / Reason |
|-----------------------------------|-------------|--------|------------------------|
| Extraction contract constants (noise-floor threshold, gap limit, percentile split) must NOT be adjusted based on whether the resulting width ordering or QA plots look correct — they must be grounded in profilometer noise characteristics and fixed independently of outcome inspection. | TARGET-01 | resolved | judgment — not mechanically testable; routes to human judgment review during QA sign-off (reviewer confirms constants were set before/independent of viewing the ordering result). |
| Extraction and persistence code must NOT write to, delete, or modify any file under `data/raw/`. | TARGET-02 | resolved | test — mechanically verifiable via checksum/mtime comparison of `data/raw/` files before and after running the extraction pipeline. |

## Ambiguity Report

| Dimension          | Score | Min  | Status | Notes                              |
|--------------------|-------|------|--------|------------------------------------|
| Goal Clarity       | 0.88  | 0.75 | ✓      | Roadmap's 4 success criteria + README's width formula give a specific, measurable outcome. |
| Boundary Clarity   | 0.85  | 0.70 | ✓      | CONTEXT.md-as-contract and disk-persistence-in-Phase-1 decisions resolved the two largest open boundary questions. |
| Constraint Clarity | 0.75  | 0.65 | ✓      | Grid resolution, dtype, and raw-data-safety constraints now explicit; CONTEXT.md D-01–D-16 cover the extraction-parameter constraints. |
| Acceptance Criteria| 0.80  | 0.70 | ✓      | 7 pass/fail checkboxes, all traceable to roadmap success criteria or interview decisions. |
| **Ambiguity**      | 0.17  | ≤0.20| ✓      |                                    |

## Interview Log

| Round | Perspective    | Question summary         | Decision locked                    |
|-------|----------------|--------------------------|-------------------------------------|
| 1     | Boundary Keeper| Is a separate TARGET_CONTRACT.md doc required beyond CONTEXT.md's D-01–D-16? | CONTEXT.md is sufficient — no separate doc. |
| 1     | Boundary Keeper| Should Phase 1 persist extracted targets to disk, or leave caching to Phase 2? | Phase 1 saves to disk under `processed_data/targets/` (float64, shared 0.2mm grid). |
| 1     | Boundary Keeper| Should QA acceptance stay visual-only or add a quantitative backstop? | Visual sign-off checkboxes only, matching roadmap's own phrasing. |
| Edge probe | Failure Analyst | SG smoothing near a masked gap — blend across both sides, or strict same-side only? | Allow blending across small gaps (standard savgol_filter behavior). |
| Edge probe | Failure Analyst | Crossed boundaries (y_upper < y_lower, negative width) — invalidate or clip to zero? | Mark x-column invalid. |
| Edge probe | Failure Analyst | All-invalid track (zero valid x-positions) — hard error or silent all-NaN output? | Raise a hard error. |
| Edge probe | Failure Analyst | Persisted output dtype — float32 or float64? | float64, matching the existing loader pipeline. |
| Prohibition probe | Failure Analyst | Could extraction constants be silently tuned to match the expected width ordering? | Yes — add as a judgment-reviewed prohibition. |
| Prohibition probe | Failure Analyst | Could extraction/persistence code silently write into `data/raw/`? | Yes — add as a test-verified prohibition. |

---

*Phase: 01-target-extraction-contract*
*Spec created: 2026-07-19*
*Next step: /gsd-discuss-phase 1 — implementation decisions (how to build what's specified above; note most "how" is already locked in 01-CONTEXT.md D-01–D-16)*
