# Phase 1 Plan 11 Task 1: Track 10 Coverage-Collapse Diagnosis

**Diagnosed:** 2026-07-21
**Diagnostic script:** `scripts/diagnose_track10_coverage.py`
**Evidence CSV:** `processed_data/diagnostics/track10_coverage_diagnosis.csv` (sibling of `processed_data/targets/`, survives `publish_staging_dir`)

## 1. The measured table

One row per track, computed under one uniform code path (`measure_track`) with no per-track special casing. Full precision values are in the committed CSV; rounded here for readability.

| measurement | track 8 | track 10 | track 14 | track 21 |
|---|---:|---:|---:|---:|
| `raw_min_mm` | -0.1815 | -0.3790 | -0.1805 | -0.1474 |
| `raw_max_mm` | -0.1628 | 0.4974 | -0.1593 | -0.1357 |
| `raw_span_mm` | 0.0187 | **0.8765** | 0.0212 | 0.0117 |
| `raw_argmax_y_index` (of 480) | 285 | 380 | 136 | 339 |
| `raw_argmax_near_edge` (within 5% of y0 or y479) | False | **False** | False | False |
| `raw_finite_fraction` | 0.631 | 0.484 | 0.489 | 0.445 |
| `residual_peak_mm` (post-detrend) | 0.00865 | 0.2334 | 0.00550 | 0.00886 |
| `residual_peak_y_index` | 281 | **0** | 246 | 349 |
| `residual_run_extent_points` | 163 | 73 | 108 | 170 |
| `residual_run_touches_y0` | False | **True** | False | False |
| `residual_run_touches_yN` | False | False | False | True |
| `fitted_surface_y0_mm` | -0.1756 | -0.0132 | -0.1720 | -0.1495 |
| `fitted_surface_ymid_mm` | -0.1699 | 0.1094 | -0.1726 | -0.1464 |
| `fitted_surface_yN_mm` | -0.1697 | 0.0502 | -0.1761 | -0.1457 |
| `fitted_surface_span_mm` | 0.01245 | **0.8842** | 0.02446 | 0.00568 |
| `fitted_span / raw_span` | 0.67 | **1.01** | 1.15 | 0.49 |
| `rejection_no_columns` | 1 | 0 | 7 | 3 |
| `rejection_gap_fail` | 25 | 112 | 79 | 37 |
| `rejection_no_baseline_sep` | 0 | 0 | 3 | 0 |
| `rejection_clipped_run_only` | 3 | **267** | 0 | 5 |
| `rejection_crossed` | 0 | 0 | 0 | 0 |
| `rejection_ok` (pre-smoothing) | 371 | **21** | 311 | 355 |
| `design_cond_unscaled` | 1.718e7 | 1.746e7 | 1.624e7 | 1.677e7 |
| `design_norm_ratio_unscaled` | 3.04e6 | 3.09e6 | 2.87e6 | 2.97e6 |
| `design_cond_scaled` | 21.13 | 21.11 | 21.10 | 21.13 |
| `design_norm_ratio_scaled` | 4.97 | 4.96 | 4.96 | 4.97 |

`data/raw/` was audited read-only before and after the run and reported integrity PASS. `git diff --stat -- src/targets.py src/nsf_fmrg_data.py` is empty at this task's commit — no extraction source was touched.

### Reproducing the CR-01 per-bin histogram (track 10)

`{'no_columns': 0, 'gap_fail': 112, 'no_baseline_sep': 0, 'clipped_run_only': 267, 'ok': 21}` — this diagnostic's `rejection_reason_histogram` reproduces this row exactly, matching `01-REVIEW.md` CR-01's instrumented figures and accounting for all 400 bins (0+112+0+267+0+21=400).

### Discrepancy note: pre-smoothing `ok` counts vs. published `valid_count` for tracks 8/14/21

The acceptance criteria for this task expect tracks 8, 14, 21 to show `ok` counts of 359, 301, 324 (the currently-published `valid_count` values from `01-08-ORDERING-OUTCOME.md`). This diagnostic's `rejection_ok` column instead reports 371, 311, 355 for those three tracks — track 10 alone matches exactly (21 == 21).

This is explained, not a bug: `rejection_reason_histogram` classifies each bin from the **raw per-column half-max candidate selection only** (mirroring `halfmax_edges`), before `extract_targets_from_arrays` hands the raw boundary arrays to `finalize_smoothed_boundaries`. That final step applies NaN-aware Savitzky-Golay smoothing to `y_upper_raw`/`y_lower_raw` and then **re-validates** — a bin that passed raw half-max classification can still be invalidated afterward if the smoothed boundaries end up non-finite or crossed (`y_upper <= y_lower`) at that position. Running `extract_track_targets` end-to-end for all four tracks confirms this exactly accounts for the gap:

```
track  pre-smoothing 'ok'  published valid_count  smoothing-induced loss
    8                 371                    359                      12
   10                  21                     21                       0
   14                 311                    301                      10
   21                 355                    324                      31
```

Track 10 loses zero additional bins to post-smoothing revalidation (21 pre- and post-), while tracks 8/14/21 each lose 10-31 bins there. This is expected and orthogonal to the coverage-collapse mechanism under investigation: it is a second, much smaller-magnitude effect (smoothing-boundary revalidation, not the boundary-clipped-run exclusion) and this task's hard constraint against computing width medians or ordering means it is not further pursued here. It does not change the diagnosis below, which is about *why 267/400 of track 10's bins hit `clipped_run_only` in the first place*.

## 2. Root-cause reading: is track 10's bead interior or edge-located in the RAW data?

**Track 10's bead is interior in the raw, undetrended data — the post-detrend edge ridge is a detrend-fitting artifact, not a physically truncated bead.**

The raw row-median profile's argmax sits at y-index 380 of 480 (`raw_argmax_near_edge = False`), roughly 79% of the way across the 1.911 mm y-strip and well clear of both the y=0 and y=479 boundaries — the same "not near an edge" result the other three tracks also show (indices 285, 136, 339, none flagged `near_edge`). If track 10's bead were genuinely truncated or beyond the profilometer's y-window, the raw argmax would sit at or adjacent to a strip edge; it does not.

What changes dramatically between the raw data and the production-path detrended residual is where the *elevated* structure sits. After the shipped `bead_exclusion_mask` + `robust_plane_detrend(order=4, fit_mask=...)` path runs, track 10's residual row-median profile peaks at y-index **0** — the very edge of the strip — with the above-half-max run touching y0. No other track's residual peak sits at an edge. This is the direct mechanism `halfmax_edges` then rejects via the D-01/D-03 boundary-clipped-run exclusion: 267/400 bins have their only above-threshold run touching a y boundary.

Two further measurements point at *why* the peak moved to the edge, and both implicate the fitted background surface rather than the raw substrate:

- **The fitted surface itself absorbs almost the entire raw span.** `fitted_surface_span_mm` for track 10 is 0.8842 mm against a raw span of 0.8765 mm — a ratio of 1.01, i.e. the order-4 background surface reproduces essentially all of the raw data's own dynamic range. Tracks 8/14/21 show ratios of 0.67, 1.15, and 0.49 — none showing this near-1:1 "surface equals substrate" signature at track 10's scale of absolute raw span (track 10's raw span is 37-75x larger than the other three tracks'). A background surface that faithfully reproduces essentially the whole signal, rather than only its low-order component, is a surface that has fit the bead itself, not just the substrate curvature underneath it — the residual left behind (the true bead signal, minus what the surface stole) then only shows its remaining spike where the fit is worst, which for an unscaled quartic-in-y basis over a 1.911 mm strip is at the boundary.
- **The design matrix is severely ill-conditioned before y-scaling and this is track-independent** — `design_cond_unscaled` is ~1.6-1.7e7 for all four tracks (it depends only on the shared x/y sampling grid geometry, not per-track height values), while `design_cond_scaled` (dividing each centered coordinate by its half-span before building the monomial basis) collapses to ~21 for all four tracks, a ~6-order-of-magnitude improvement. This is exactly the geometry `01-11-CRITERION.md`'s basis-conditioning candidate describes: the mapped strip is ~80 mm along-track against ~1.91 mm cross-track, so an unscaled `y**4` term is astronomically larger in raw units than an unscaled `x**4` term at the same physical extent, and `np.linalg.lstsq(..., rcond=None)` is free to place large, oscillatory coefficients on the poorly-scaled y-terms without being penalized relative to the well-scaled x-terms. Because the conditioning defect is present identically on all four tracks' design matrices but only track 10's fitted surface visibly reproduces the substrate at a 1:1 ratio, the manifestation (not the underlying ill-conditioning) is track-specific — consistent with track 10 having the least well-behaved residual signal-to-noise ratio for the y-basis to be regularized against, exactly the kind of track-dependent *symptom* of a track-independent *defect* this plan's criterion is designed to fix without per-track tuning.

**Conclusion:** the evidence supports the RECOVERABLE reading. Track 10's bead is not beyond the profilometer's y-window; its raw argmax is comfortably interior. The edge-touching residual peak that `halfmax_edges` correctly discards is a manufactured artifact of the shared, unscaled order-4 detrend basis, not a property of the raw substrate. Task 2 will pre-register a criterion targeting this mechanism, and Task 3 will apply whichever uniform, track-independent correction that criterion selects.

## 3. Relationship to the pre-registration probe

This reading **confirms**, on measured evidence, the working hypothesis already embedded in this plan's own `key_links` ("the fitted background surface's behavior at the y-strip edge determines whether `halfmax_edges` sees real bead runs or a **manufactured edge ridge**") and in its `must_haves` truths ("states plainly whether track 10's bead is a detrend artifact... or physically truncated... and does not force the recoverable conclusion"). It also **narrows** the more cautious, two-sided hedge `01-REVIEW.md` CR-01 offered ("Track 10's bead is not fully captured within the profilometer's y-scan window (**or** the strip is misaligned for this file)") — CR-01 did not have raw-argmax or fitted-surface-span evidence available and left physical truncation on the table as a live alternative; this diagnosis's raw-data argmax measurement (interior, not edge-adjacent) rules that alternative out for track 10 specifically, without needing to guess at a "strip misalignment" explanation.

This conclusion was reached without computing, printing, or persisting any width median, mean, or ordering verdict for any candidate fix, per this task's hard constraint (`grep -Ein "median_width|ordering|verdict" scripts/diagnose_track10_coverage.py` finds no match).
