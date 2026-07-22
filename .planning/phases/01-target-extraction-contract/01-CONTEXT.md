# Phase 1: Target Extraction & Contract - Context

**Gathered:** 2026-07-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Define and implement the height-map → local-width extraction method `w_i(x) = y_upper,i(x) - y_lower,i(x)` (per README's formula), lock it as a documented contract (TARGET-01), then implement and visually QA it against all 4 tracks (8, 10, 14, 21) with one identical, non-per-track-tuned parameterization (TARGET-02). No organizer-provided extractor exists — this phase's output becomes the ground truth every downstream phase depends on.

</domain>

<decisions>
## Implementation Decisions

### Edge-detection method (how y_upper/y_lower are found per x-column)
- **D-01:** Use a relative half-max threshold: for each x-column's (already-detrended) y-profile `Z(y)`, estimate a local baseline and peak height, then set each edge where `Z` crosses `baseline + 0.5*(peak - baseline)`. Never a fixed absolute height value — track heights vary too much across the 4 laser powers (per PITFALLS.md Pitfall 6).
- **D-02:** Baseline = 5th percentile, peak = 95th percentile of that column's `Z(y)` values (per-column percentile split, not a track-wide baseline or a parametric peak/shoulder fit).
- **D-03:** Half-max fraction locked at 0.5 (50%) with the 5th/95th percentile baseline/peak — the classic half-max/FWHM-style convention.
- **D-04:** Add a minimum peak-baseline separation validity check: if `(peak - baseline)` for a column falls below a fixed minimum (tied to the profilometer's noise floor), that x position is marked invalid rather than reporting a spurious noise-driven edge. This check feeds directly into the valid-coordinate mask.

### Track 21 gap-handling rule (applies identically to all tracks, triggers mostly on 21)
- **D-05:** Small gaps (≤10 consecutive NaN/'bad' pixels within a column) are linearly interpolated along `y` only, within that single x-column — never 2D/cross-column interpolation, to avoid smearing real x-direction (scan-direction) structure across columns.
- **D-06:** If a gap in a column exceeds 10 consecutive NaNs (in the region relevant to edge detection), that entire x-column is marked invalid via the valid-coordinate mask rather than guessed/interpolated.
- **D-07:** Output `w_i(x)` stays on a fixed shared 0.2mm x-grid with the **same length/positions across all 4 tracks**. Invalid x positions keep their grid slot with `width = NaN` and a `False` entry in the boolean valid-coordinate mask — never a ragged/dropped-position array. This directly matters for Phase 2's alignment step, which will consume this same grid.

### Smoothing scale & method
- **D-08:** Use a Savitzky-Golay filter (NaN-aware), not a plain moving average and not "grid-binning only" — SG preserves local peaks/slopes better, which matters directly for the organizer's "preservation of spatial variation" evaluation criterion.
- **D-09:** Window ≈1mm of scan distance (≈5 points at the 0.2mm grid spacing), polynomial order 2-3.
- **D-10:** Smoothing is applied to `y_upper(x)` and `y_lower(x)` **separately**, and `w(x)` is derived from the smoothed boundaries afterward — not smoothing the raw width curve directly. This also keeps boundary curves available if boundary-function output (TARGET-03/v2 stretch) is pursued later.
- **D-11:** The SG fit skips invalid/masked x positions rather than interpolating through them first — a position already invalidated by D-04/D-06 stays NaN in the smoothed output too. No fabricated values for excluded positions (matches TARGET-02's "no silently dropped gaps" success criterion, interpreted as "no silently fabricated data" for excluded positions).
- **D-12:** Edge effects at the 20mm/100mm crop boundaries (Pitfall 7): use SG's edge/interp boundary mode (shrinking window near the crop edges rather than assuming out-of-crop data exists) — no exclusion of boundary positions from output, but the QA plots must make this edge behavior visually inspectable/documented rather than silent.

### Detrending approach
- **D-13:** Keep `robust_plane_detrend()` from `src/nsf_fmrg_data.py` as-is (existing, working infrastructure) — do not upgrade to a higher-order polynomial surface preemptively.
- **D-14:** Add a mandatory QA step: visually inspect post-detrend residual maps for all 4 tracks, confirming no obvious remaining bow/curvature (Pitfall 6's concern) before the target extractor is trusted. If curvature is visible in this check, escalate to a fix at that point — don't pre-solve an unconfirmed problem.
- **D-15:** Detrending happens once per full (cropped) track, before edge detection runs — not per-column or per-local-window. Keeps detrending and edge-detection as separate, independently testable steps.
- **D-16:** Keep `robust_plane_detrend()`'s existing default stride (`stride_x=40, stride_y=2`) unchanged. Don't symmetrize preemptively; revisit only if the D-14 residual-curvature QA check surfaces an actual problem.

### Amendment A3 (post-UAT escalation — plan 01-04)

Amendment A3 supersedes D-13's and D-16's instruction to keep `robust_plane_detrend()` as-is now that D-14's mandatory residual QA check surfaced exactly the anticipated bow in UAT Test 1 (`.planning/debug/residual-curvature-after-detrend.md`). `robust_plane_detrend()` gains a configurable bivariate-polynomial `order` parameter whose default remains `order=1`, preserving the original three-term affine fit for every other caller, including the notebooks. `src/targets.py` locks `DETREND_POLY_ORDER = 4` and applies it identically to all four tracks. The three-pass percentile-trim scheme and existing `stride_x=40, stride_y=2` sampling remain unchanged because the root-cause investigation implicated model order, not sampling density.

The order was fixed from measured evidence before any new QA figure was generated: quadratic fits explained 97.7% and 96.3% of the post-linear-detrend residual variance for tracks 8 and 14, but only 46.9% and 29.5% for tracks 10 and 21; quartic fits raised track 10 to 64.0% and track 21 to 44.9%. Track 21's more demanding alternating-lobe case therefore set the shared order to 4 a priori. Any residual unexplained by that shared quartic surface is treated as genuine local width/process variation rather than chased with per-track special-casing, which would violate TARGET-02's one-shared-parameterization constraint.

### Amendment A4 (gap-closure — plan 01-07)

Amendment A4 completes the record of two behavior-changing parameters that were previously implemented but left out of the canonical contract, and adds one new methodological fix. It supersedes nothing in A3.

First, it canonicalizes plan 01-05's continuity/stale-history boundary-tracking rule, applied identically to all four tracks: `halfmax_edges()` enumerates every non-boundary-clipped half-max run in a column's profile; while tracking history is fresh (a `previous_center` from the most recently successful column exists), it selects the candidate run nearest that center, breaking ties by run length then position; with no usable history it falls back to the largest-run selection that predates continuity tracking. `extract_targets_from_arrays()` updates `previous_center` only after a successful column and expires it — resetting to `None` — after `MAX_TRACKING_GAP_COLUMNS = 10` consecutive invalid columns, so a long gap cannot leave a stale anchor to silently capture an unrelated resumed boundary.

Second, it records the Gap-2 methodological fix chosen by the pre-registered, outcome-independent criterion in `01-06-DIAGNOSIS.md` Section 3 (residual structure and physical plausibility — the fitted detrend background must not follow the elevated bead corridor). The endorsed leading remedy was implemented: `robust_plane_detrend()` gains a `fit_mask` keyword (default `None`, preserving every other caller including the affine `order=1` path and the notebooks) that excludes flagged pixels from the least-squares fit and its iterative percentile trimming while still subtracting the fitted surface from every pixel. `targets.bead_exclusion_mask(Z_mm)` computes this mask with one shared, per-column baseline/peak-relative rule mirroring D-01/D-02's `BASELINE_PCT`/`PEAK_PCT` convention: a pixel is excluded only if it exceeds `baseline + BEAD_MASK_HEIGHT_FRACTION * (peak - baseline)` for its own column, so the same fraction excludes bead corridors of differing absolute height across tracks rather than an absolute value. `BEAD_MASK_HEIGHT_FRACTION` is fixed at the already-locked `HALF_MAX_FRACTION` (0.5): a pixel this contract already classifies as "bead" by the half-max width convention (D-01/D-03) is, by that same definition, not background, so it must not be allowed to bias the fitted surface. `extract_track_targets()` computes this mask from each track's raw `Z_mm` and passes it into the shared `DETREND_POLY_ORDER = 4` detrend call identically for all four tracks — no per-track mask geometry or per-track-tuned constant. This parameter was fixed from the D-01/D-03 half-max definition already in the contract, not from the resulting width ordering, and the no-outcome-driven-per-track-tuning prohibition (reaffirmed by Amendment A3) applies identically here: neither `BEAD_MASK_HEIGHT_FRACTION` nor any other constant in this fix may be adjusted in response to whether `8 > 10 > 14 > 21` passes.

Both `MAX_TRACKING_GAP_COLUMNS` and `BEAD_MASK_HEIGHT_FRACTION` are now returned by `extraction_params()` alongside the previously-recorded constants, so the current extraction contract's complete parameter set is machine-readable and its SHA-256 provenance digest is sensitive to a change in either value.

### Amendment A5 (gap-closure — plan 01-11)

Amendment A5 fixes track 10's valid-fraction collapse (21/400, 5.2%), diagnosed in `01-11-DIAGNOSIS.md`: 267/400 of track 10's bins failed `clipped_run_only` because the fitted detrend background surface manufactured a height feature at the y-strip edge that track 10's raw, undetrended data does not contain — evidenced by the raw row-median profile's argmax sitting well interior (y-index 380/480, not edge-adjacent) while the production-path detrended residual's peak sat at the edge (y-index 0). This is a detrend-fitting artifact, not a physically truncated bead, so it is recoverable by a uniform change to the shared detrend basis; it supersedes nothing in A3 or A4.

`01-11-CRITERION.md` pre-registered, before any change existed in `src/targets.py` or `src/nsf_fmrg_data.py`, a falsifiable residual/physical/numerical test (the fitted surface's row-median value at each y-strip edge must lie within `0.05 mm` of its own interior-midpoint value) and two candidate mechanisms, each with named rejection evidence and a fixed tie-break rule. Implementation (Task 3) then applied that criterion's own fallback provision: Candidate A (basis conditioning, rescaling the centered coordinates by their half-span before building the monomial design matrix) was measured to produce a *mathematically identical* fitted surface to the unscaled basis for a full-rank least-squares fit — column rescaling cannot change the fitted values of a linear regression, only the conditioning of solving for its coefficients — so it was rejected by the criterion's own Section 4 evidence, not by its resulting effect on any width or ordering. The criterion's pre-registered tie-break rule then directed implementation to Candidate B.

`robust_plane_detrend()` gains a `max_y_degree` keyword (default `None`, preserving every other caller including the affine `order=1` path, the notebooks, and `scripts/diagnose_width_regression.py`'s historical rows bit-for-bit) that drops any `(x_exponent, y_exponent)` monomial term whose `y_exponent` exceeds the cap from the fitted basis, while the along-track (`x`) exponent range is left fully intact at every degree — so Amendment A3's along-track bow removal is structurally unaffected by this cap. `src/targets.py` locks `DETREND_MAX_Y_DEGREE = 2`: measured against `01-11-CRITERION.md`'s tolerance on all four tracks, this is the *largest* cross-track degree cap that clears it (cap 3 leaves one track's edge departure at `0.0665 mm`, still above tolerance; cap 2 brings every track's largest edge departure to `0.0238 mm`), so it preserves the maximum cross-track fitting capacity the criterion permits rather than being the smallest cap that happens to work. `extract_track_targets()` passes `max_y_degree=DETREND_MAX_Y_DEGREE` into the shared detrend call identically for all four tracks — no per-track mask geometry or per-track-tuned constant. This value was fixed from `01-11-CRITERION.md`'s pre-registered tolerance test applied to Task 1's measured fitted-surface-edge evidence, not from the resulting width ordering or valid fractions, and the no-outcome-driven-per-track-tuning prohibition (reaffirmed by Amendments A3 and A4) applies identically here: neither `DETREND_MAX_Y_DEGREE` nor any other constant in this fix may be adjusted in response to whether `8 > 10 > 14 > 21` passes.

`DETREND_MAX_Y_DEGREE` is now returned by `extraction_params()` alongside the previously-recorded constants (16 keys total), so the current extraction contract's complete parameter set remains machine-readable and its SHA-256 provenance digest is sensitive to a change in this value.

### Amendment A6 (gap-closure -- plan 01-13, dated 2026-07-21)

Amendment A6 closes UAT gap G-01-4: after Amendment A5, the `8>10>14>21` width-ordering criterion still FLAGged on the 10-vs-14 pair (track 10 median `0.3713mm` < track 14 median `0.4765mm`). `.planning/debug/track10-14-ordering-tail-collapse.md` -- the one bounded, diagnosis-only investigation the user explicitly authorized -- confirmed this is an EXTRACTION ARTIFACT, not genuine physical narrowing: track 10's raw within-column bead contrast stays flat across the whole 20-100mm scan, but its raw along-track baseline drift (`~1.7mm`, `~40-85x` larger than the other three tracks) forces the shared quartic-in-x detrend surface to nearly reproduce that entire drift, and the fit's own y-shape prediction error grows systematically toward the domain's far edge (`x=100mm`) -- a Runge-type polynomial edge effect along x, analogous to the y-direction risk `DETREND_MAX_Y_DEGREE` already caps, but here (until now) uncapped in x.

`01-13-CRITERION.md` pre-registered, before any change existed in `src/targets.py` or `src/nsf_fmrg_data.py` for this plan, a falsifiable x-direction shape-gap test (the fitted surface's own low-y-band-vs-bead-band value at the domain's far edge, `x~99mm`, must not depart from its own interior-midpoint value, `x~60mm`, by more than `SHAPE_GAP_EDGE_TOLERANCE_MM=0.012mm`, on all four tracks under one shared constant) and named `DETREND_MAX_XY_DEGREE`/`max_xy_degree` as the sole candidate mechanism -- basis conditioning was not re-considered, since `01-11-CRITERION.md` already measured it to be mathematically incapable of changing a full-rank least-squares fit's fitted values for any axis.

`robust_plane_detrend()` gains a `max_xy_degree` keyword (default `None`, preserving every other caller including the affine `order=1` path, the notebooks, and every existing test bit-for-bit) that further filters the basis to drop any cross/interaction term (`y_exponent >= 1`) whose x-exponent exceeds the cap, while every pure along-track term (`y_exponent == 0`) is left fully intact at every x-degree up to `DETREND_POLY_ORDER` -- so Amendment A3's quartic bow-removal capacity is structurally unaffected -- and every pure cross-track term (`x_exponent == 0`) remains governed only by the existing `DETREND_MAX_Y_DEGREE` cap. `src/targets.py` locks `DETREND_MAX_XY_DEGREE = 2`: measured against `01-13-CRITERION.md`'s tolerance on all four tracks' real data (`processed_data/diagnostics/track10_tail_collapse_diagnosis.csv`), this is the *largest* cross-term x-exponent cap that clears it -- cap 3 (a no-op versus uncapped, since `DETREND_MAX_Y_DEGREE=2` already limits the highest surviving cross-term x-exponent to 3) leaves track 10's departure at `0.0212mm`, still above tolerance, while cap 2 brings it to `0.0118mm`, comfortably under -- so it preserves the maximum cross-track fitting capacity the criterion permits. `extract_track_targets()` passes `max_xy_degree=DETREND_MAX_XY_DEGREE` into the shared detrend call identically for all four tracks -- no per-track mask geometry or per-track-tuned constant. This value was fixed from `01-13-CRITERION.md`'s pre-registered tolerance test applied to Task 1's measured shape-gap evidence, not from the resulting width ordering or valid fractions, and the no-outcome-driven-per-track-tuning prohibition (reaffirmed by Amendments A3, A4, and A5) applies identically here: neither `DETREND_MAX_XY_DEGREE` nor any other constant in this fix may be adjusted in response to whether `8 > 10 > 14 > 21` passes. This amendment supersedes nothing in A3, A4, or A5.

`DETREND_MAX_XY_DEGREE` is now returned by `extraction_params()` alongside the previously-recorded constants (17 keys total), so the current extraction contract's complete parameter set remains machine-readable and its SHA-256 provenance digest is sensitive to a change in this value.

### Amendment A7 (gap-closure -- plan 01-14, dated 2026-07-22)

Amendment A7 closes UAT gap G-01-5: boundary overlays remained fragmented and physically implausible even after the 01-05 continuity-tracking fix for G-01-2. `.planning/debug/boundary-fragmentation-post-continuity-fix.md` diagnosed the defect directly on the real 4-track data: `halfmax_edges`' tracked-candidate selection rule had NO maximum-distance gate and NO effective size/plausibility weighting -- length was only an unreachable exact-float-tie tiebreak -- so a 1-native-pixel noise spike and a 300-pixel true bead run were treated as equally legitimate candidates, decided purely by whichever midpoint happened to be marginally closer to `previous_center`. Combined with `extract_targets_from_arrays` unconditionally overwriting `previous_center` with whatever run was just selected, correct or wrong, ONE spurious column (a local noise dip briefly fragmenting or suppressing the true bead's above-threshold run) corrupted the anchor and triggered a MULTI-COLUMN self-reinforcing wrong lock -- a new failure mode the pre-01-05 independent-per-column algorithm did not have. Directly traced on Track 8 (x=24.9-26.5mm, an 8-column/1.4mm episode) and, far more severely, on Track 10 (a near-continuous narrow lock from x~68mm through beyond x~82mm). Measured wrong-narrow-pick rates: Track 8 5.7%, Track 10 7.1%, Track 14 34.3%, Track 21 43.1% of tracked selections. This supersedes nothing in A3-A6.

Two jointly-required mechanisms were adopted, both fixing a concrete, distinct half of the diagnosed failure: (1) `merge_adjacent_runs(runs, max_gap)` merges adjacent above-half-max-threshold sub-runs separated by only a few below-threshold samples into one candidate before clip-exclusion and selection -- fixing the TRIGGER (e.g. Track 10's x~67.1mm 3-way fragmentation into sub-runs of length 5/18/20, now merged into one candidate spanning the full bead). `halfmax_edges` calls this on `all_true_runs(above)`'s output and applies the existing D-01/D-03 boundary-clip exclusion filter to the *merged* run list, not the original unmerged runs, so a merged run that now spans to a boundary is correctly excluded exactly as an originally-clipped run would be. (2) When tracking history exists, `halfmax_edges` restricts selection to candidates whose length is at least `MIN_TRACKED_LENGTH_RATIO` of the largest candidate present in that same column, then selects nearest-to-`previous_center` among only that plausible subset -- fixing the PROPAGATION (e.g. Track 8's 8-column wrong lock), since a length-1-pixel noise spike can no longer out-rank a length-hundreds true bead purely by midpoint proximity. This plausible subset is never empty, since the run achieving the column's max length always satisfies its own inequality. `extract_targets_from_arrays`'s `previous_center` update itself did not need to change: because `halfmax_edges` now never returns an implausibly-small candidate while tracking history exists, the existing unconditional `previous_center = 0.5 * (edges[0] + edges[1])` on a successful column now always advances the anchor to a plausible location by construction.

Both new constants are reused from already-locked contract values, not new arbitrary numbers, mirroring Amendment A4/A5's discipline: `MAX_RUN_MERGE_GAP_PIXELS = MAX_GAP_PIXELS` (10) reuses the already-locked D-05/D-06 judgment that a short (<=10 native-pixel) below-criterion stretch should not be treated as a genuine break/separation, now applied to post-threshold run fragmentation instead of raw NaN gaps. `MIN_TRACKED_LENGTH_RATIO = HALF_MAX_FRACTION` (0.5) reuses the already-locked D-01/D-03 half-max convention's own fraction: a tracked candidate whose length falls below half of the largest same-column alternative is not a plausible competing feature under that same convention. Neither value was chosen from the resulting width ordering or fragmentation count.

A third direction the diagnosis also named -- a full DP/Viterbi joint sequence tracker -- was considered and explicitly deferred, not silently dropped: the diagnosis itself states it is "not required to implement, if scope is too large," and given the project's 8-day runway, mechanisms (1) and (2) directly and fully address both traced failure mechanisms (trigger and propagation) without it. This is a missing-information/context-cost tradeoff, not a scope reduction of a locked decision.

Both mechanisms apply identically to all four tracks with no per-track constant or conditional -- `extract_track_targets()` and `extract_targets_from_arrays()` are unchanged in this respect, and `test_single_parameterization_has_no_track_conditionals` remains green. The no-outcome-driven-tuning prohibition (reaffirmed by Amendments A3, A4, A5, and A6) applies identically here: neither `MAX_RUN_MERGE_GAP_PIXELS` nor `MIN_TRACKED_LENGTH_RATIO` nor any other locked constant may be adjusted in response to the resulting fragmentation count, jump statistics, or the `8 > 10 > 14 > 21` width ordering.

`MAX_RUN_MERGE_GAP_PIXELS` and `MIN_TRACKED_LENGTH_RATIO` are now returned by `extraction_params()` alongside the previously-recorded constants (19 keys total), so the current extraction contract's complete parameter set remains machine-readable and its SHA-256 provenance digest is sensitive to a change in either value.

### Claude's Discretion
- Exact noise-floor value used for the D-04 minimum peak-baseline separation threshold (should be grounded in the profilometer's stated vertical resolution/noise characteristics, determined during implementation/research).
- Precise scipy `savgol_filter` boundary-mode parameter choice satisfying D-12 (e.g. `mode='interp'` vs `'nearest'`) — pick during implementation, verify visually per D-12.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Organizer requirements (authoritative)
- `README.md` §"Task, alignment, masking, and evaluation guidance" — organizer-confirmed width formula `w_i(x) = y_upper,i(x) - y_lower,i(x)`, ground-truth clarification ("no separate label file or official extractor exists — participants must define and justify their own"), Bruker/Wyko height-map file conventions
- `.planning/REQUIREMENTS.md` — TARGET-01 (contract) and TARGET-02 (implementation + visual QA) requirement text, locked acceptance criteria
- `.planning/ROADMAP.md` §"Phase 1: Target Extraction & Contract" — phase goal and 4 success criteria (contract written, expected width ordering 400W(8)>350W(10)>300W(14)>200W(21), QA plots on raw+detrended maps for all 4 tracks incl. track 21 gaps, single shared parameterization with no per-track tuning)

### Risk grounding (informs the decisions above)
- `.planning/research/PITFALLS.md` Pitfall 6 — noise-sensitive/inconsistent width extraction (relative vs absolute threshold, detrending stride asymmetry, gap-handling consistency across tracks) — directly drove D-01, D-13/D-14/D-16, D-05/D-06
- `.planning/research/PITFALLS.md` Pitfall 7 — edge effects near the 20mm/100mm window boundaries — directly drove D-12
- `.planning/research/PITFALLS.md` Pitfall 9 — silent thermal-window misalignment specifically on track 21 (relevant context for Phase 2, not this phase's extraction logic itself, but explains why track 21's data quality gets extra scrutiny here too)
- `.planning/research/SUMMARY.md` §"Phase 1: Target Extraction" — rationale for why this phase blocks everything downstream

### Existing code (build on, don't replace)
- `src/nsf_fmrg_data.py:144-202` (`load_wyko_asc`) — Wyko `.ASC` loader returning `Z_mm` (y,x grid), `x_actual_mm`, `y_mm`, already cropped/reoriented to the shared 20-100mm window
- `src/nsf_fmrg_data.py:205-227` (`robust_plane_detrend`) — kept as-is per D-13; new target-extraction code calls this before edge detection (D-15)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `load_wyko_asc()` (`src/nsf_fmrg_data.py:160-202`): already handles unit conversion (nm→mm), coordinate reorientation to increasing 20-100mm, and optional cropping. New target-extraction code consumes its output (`Z_mm`, `x_actual_mm`, `y_mm`) directly rather than re-parsing `.ASC` files.
- `robust_plane_detrend()` (`src/nsf_fmrg_data.py:205-227`): outlier-resistant iterative plane fit, reused unchanged per D-13.

### Established Patterns
- Loader functions return plain `dict`s with consistent keys (`'file'`, coordinate arrays, primary data array) rather than custom classes — new target-extraction function(s) should follow this same dict-return convention (e.g. a `w_x_mm`, `w_mm`, `valid_mask`, `y_upper_mm`, `y_lower_mm` bundle).
- No type hints in `src/nsf_fmrg_data.py` library code; no docstrings anywhere in the codebase; SCREAMING_SNAKE_CASE for module-level physical constants (e.g. a new `TARGET_GRID_STEP_MM = 0.2`, `SG_WINDOW_MM`, `MIN_PEAK_BASELINE_SEPARATION_MM`, `MAX_GAP_PIXELS` should follow this convention).

### Integration Points
- New code will likely live in a new module (`src/targets.py`, per `research/ARCHITECTURE.md`'s suggested structure) that imports `load_wyko_asc` and `robust_plane_detrend` from `src/nsf_fmrg_data.py`, following the existing manual-`sys.path`-or-run-from-repo-root convention (no packaging).
- Output feeds Phase 2's dataset alignment step, which will consume the same fixed 0.2mm x-grid (D-07) to pair with thermal samples.

</code_context>

<specifics>
## Specific Ideas

No specific "I want it like X" references beyond what's captured in the Decisions section above — all specifics were locked interactively as numbered decisions (D-01 through D-16) since this phase's discussion *is* the TARGET-01 contract itself.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope (implementation decisions for the locked TARGET-01/TARGET-02 requirements). No new capabilities were proposed during discussion.

</deferred>

---

*Phase: 1-Target Extraction & Contract*
*Context gathered: 2026-07-19*
