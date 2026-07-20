---
status: diagnosed
trigger: "G-01-1: Residual bow/curvature remains on real height-map data after the current plane-detrending step, for tracks 8, 10, 14, 21 in the NSF FMRG target-extraction pipeline."
created: 2026-07-19T00:00:00Z
updated: 2026-07-19T01:00:00Z
---

## Current Focus
<!-- OVERWRITE on each update - reflects NOW -->

hypothesis: CONFIRMED — `robust_plane_detrend()` fits a strictly first-order affine model `z = a*x + b*y + c` (design matrix columns are exactly `[x, y, 1]`, no quadratic/cross terms). This is a locked methodology decision (D-13/D-16), not an implementation bug: a plane can only remove tilt, never real 2nd-order-or-higher curvature/bow, so any genuine bow present in the real substrate/instrument geometry necessarily survives as residual. D-14 explicitly anticipated this exact outcome and named it the trigger to escalate to a model-order fix, rather than something to pre-solve.
test: (1) Read SPEC/CONTEXT/PATTERNS/PITFALLS for documented design intent. (2) Read src/nsf_fmrg_data.py:205-227 (robust_plane_detrend) and src/targets.py/run_target_extraction.py for how it's invoked and plotted, checking for an alternate implementation bug (wrong axis, wrong region/masking, weighting/outlier-exclusion not working). (3) Quantitatively fit linear vs. quadratic vs. quartic models to the real per-track column-median post-detrend residual for all 4 tracks.
expecting: If design-limitation hypothesis is correct, a quadratic (or higher) term should explain dramatically more residual variance than the linear term already removed by the plane fit, on real data, for all 4 tracks.
next_action: Root cause confirmed with code + data evidence — proceed to return_diagnosis (goal: find_root_cause_only, no fix applied).

## Symptoms
<!-- Written during gathering, then IMMUTABLE -->

expected: No scientifically significant bow or curvature remains after detrending (per Phase 01's target-extraction contract for local track-geometry targets).
actual: Reviewer visually inspected the real QA residual plots (processed_data/targets/qa/ - residual-vs-x-y or similar detrend QA figures per track) and reported: "Track 8: Clear broad U-shaped residual: positive at both x ends and negative through the middle. It is coherent across most of the track width, so it does not look like local substrate roughness. Track 10: Same strong end-positive / center-negative pattern, with especially high residuals at the left end. Clear leftover bow. Track 14: The cleanest symmetric bow signature: red at both ends and a broad blue basin around x = 55-75 mm. This is unmistakably systematic curvature. Track 21: No simple symmetric bow. It has broad alternating x-direction lobes-positive near 30 and 55 mm, negative near 40 and 80-88 mm, then strongly positive near 95 mm. That looks like long-wavelength waviness or process variation rather than a single quadratic bow, although it is still systematic rather than fine noise. The narrow vertical streaking is plausibly measurement/process texture, but the smooth, track-wide red-blue-red structure in tracks 8, 10, and 14 is much too spatially coherent to classify as ordinary local roughness. A plane fit can remove tilt but cannot remove quadratic curvature; visually, those three retain substantial bow after plane detrending."
errors: None reported (this is a QA/scientific-validity finding, not a crash).
reproduction: Regenerate the detrend QA figures via the target-extraction pipeline (scripts/run_target_extraction.py, using src/targets.py's robust_plane_detrend or equivalent) and inspect processed_data/targets/qa/ residual plots for tracks 8, 10, 14, 21.
started: Discovered during UAT (Test 1) of Phase 01 "target-extraction-contract".

## Eliminated
<!-- APPEND only - prevents re-investigating -->

- hypothesis: Implementation bug — wrong axis assignment in the plane fit (x/y swapped).
  evidence: "src/nsf_fmrg_data.py:205-227 — `Xs, Ys = np.meshgrid(xs, ys)`; design matrix `A = np.c_[Xs.ravel(), Ys.ravel(), np.ones(...)]`; plane reconstruction `coef[0]*x_mm[None,:] + coef[1]*y_mm[:,None] + coef[2]` — coef[0] consistently maps to x, coef[1] to y, matching meshgrid convention. No axis swap."
  timestamp: 2026-07-19T00:00:00Z

- hypothesis: Implementation bug — 'robust' outlier trimming isn't actually excluding outliers, so the fit is biased by real track-bump geometry making it look worse than a plane fit should.
  evidence: "src/nsf_fmrg_data.py:212-225 — `valid = np.isfinite(z)`; iterative loop 3x: `lstsq` on `A[keep]`,`z[keep]`, then `resid = z - A@coef`, trims to 5th-95th percentile of residual, refits. This is a genuine iteratively-reweighted plane fit; trimming does work as intended. Percentile-trim mechanics are not the source of the bow — a 2nd-order surface, even fit on the same trimmed sample set, would remove far more residual (see quantitative check below)."
  timestamp: 2026-07-19T00:00:00Z

- hypothesis: Implementation bug — fit region includes invalid/masked samples that bias the plane (e.g., NaN 'Bad' pixels not excluded, or fit region should be restricted to the track/bump area only, not full y-range).
  evidence: "`valid = np.isfinite(z)` already excludes NaN before every lstsq call and every percentile computation — no invalid samples enter the fit. D-15 (01-CONTEXT.md) explicitly locks 'detrending happens once per full (cropped) track... not per-column or per-local-window' — fitting the whole cropped x-window/full y-range in one shot is the intended design, not an oversight."
  timestamp: 2026-07-19T00:00:00Z

- hypothesis: Implementation bug — detrend applied per-track when it should be applied per-track-and-region (e.g. separate baseline/track-bump regions).
  evidence: "D-15 explicitly locks a single whole-track plane fit before edge detection, as a deliberate simplicity choice, independently testable from edge detection (D-15 rationale). No code path applies detrend differently across tracks (targets.py:220 calls `robust_plane_detrend(data['Z_mm'], data['x_actual_mm'], data['y_mm'])` identically for all 4 tracks, default stride_x=40/stride_y=2 per D-16)."
  timestamp: 2026-07-19T00:00:00Z

## Evidence
<!-- APPEND only - facts discovered -->

- timestamp: 2026-07-19T00:00:00Z
  checked: .planning/phases/01-target-extraction-contract/01-SPEC.md Boundaries section
  found: "Out of scope: 'Upgrading `robust_plane_detrend()` to a higher-order surface fit — deferred unless the D-14 residual-curvature QA check surfaces an actual problem (per CONTEXT.md, not preemptive).'"
  implication: The SPEC already anticipated and explicitly scoped-out exactly this scenario; a visible residual bow surfacing in the D-14 QA check is the documented, expected trigger condition for a follow-up fix — not evidence of an unanticipated defect.

- timestamp: 2026-07-19T00:00:00Z
  checked: .planning/phases/01-target-extraction-contract/01-CONTEXT.md decisions D-13, D-14, D-16
  found: "D-13: Keep `robust_plane_detrend()` as-is, do not upgrade to higher-order polynomial preemptively. D-14: Add mandatory QA step to visually inspect post-detrend residual maps for bow/curvature; if curvature is visible, escalate to a fix at that point. D-16: Keep existing stride (`stride_x=40, stride_y=2`) unchanged; revisit only if D-14 surfaces an actual problem."
  implication: Confirms the plane-only model and its coarse/asymmetric stride were deliberate, risk-accepted choices with a named contingency plan (fix-on-QA-failure) — matching the current situation exactly.

- timestamp: 2026-07-19T00:00:00Z
  checked: .planning/research/PITFALLS.md Pitfall 6
  found: "'Detrending artifacts: `robust_plane_detrend` fits a single global tilt plane per track using a coarsely and asymmetrically strided grid (stride_x=40, stride_y=2). A linear-plane fit only removes tilt, not any real low-frequency bow/curvature in the substrate; residual curvature can then be misread as local width variation that is actually leftover detrending artifact, not true track geometry signal. The asymmetric stride... also means the fit is more sensitive to y-direction structure than x.'"
  implication: This exact failure mode (linear fit leaving bow, asymmetric stride biasing sensitivity toward y) was predicted by name during research, before implementation — strong corroboration this is a known, named methodology risk rather than a surprise bug.

- timestamp: 2026-07-19T00:00:00Z
  checked: src/nsf_fmrg_data.py:205-227 (`robust_plane_detrend` implementation)
  found: "Design matrix `A = np.c_[Xs.ravel(), Ys.ravel(), np.ones(Xs.size)]` — exactly 3 columns (x, y, intercept). Model is `z = coef[0]*x + coef[1]*y + coef[2]`. No `x**2`, `y**2`, or `x*y` term exists anywhere in the function. Iterative refit (3 passes) only re-weights which samples are `kept` via residual percentile trimming — it never changes the model order."
  implication: By construction this function is mathematically incapable of representing or removing any 2nd-order-or-higher spatial curvature, regardless of how well the linear coefficients are estimated or how good the outlier rejection is.

- timestamp: 2026-07-19T00:00:00Z
  checked: src/targets.py:220 (`extract_track_targets`) and scripts/run_target_extraction.py:116-154 (`save_residual_map`)
  found: "`extract_track_targets` calls `robust_plane_detrend(data['Z_mm'], data['x_actual_mm'], data['y_mm'])` with default args (stride_x=40, stride_y=2) identically for all 4 tracks — one shared parameterization, no per-track branching. `save_residual_map` plots `result['Zd_mm']` directly (the literal `Z_mm - plane` output) with no additional transform, so the QA figure is a faithful, undistorted view of the actual post-detrend residual — no plotting-layer bug."
  implication: Confirms the pipeline invokes the detrend function exactly as designed and the QA figure the reviewer inspected is a true representation of the residual; the bow visible in the QA plots is the actual output of the locked plane-fit, not a display artifact.

- timestamp: 2026-07-19T00:00:00Z
  checked: Live re-derivation from real data — loaded all 4 real `data/raw/height_maps/Heightmap_{8,10,14,21}.ASC` files via `load_wyko_asc`, ran the actual `robust_plane_detrend()`, computed per-x-column median of `Zd_mm`, then fit linear vs. quadratic vs. quartic polynomials in x to that residual curve and compared R².
  found: "Track 8: linear R2=0.036, quadratic R2=0.977. Track 10: linear R2=0.086, quadratic R2=0.469, quartic R2=0.640. Track 14: linear R2=0.001, quadratic R2=0.963, quartic R2=0.974. Track 21: linear R2=0.004, quadratic R2=0.295, quartic R2=0.449. Track 8/14 residual range ~0.09-0.18mm peak-to-peak; a 2nd-order term alone explains 96-98% of the residual pattern's variance on these two tracks."
  implication: Quantitatively confirms the reviewer's visual read for every track. Tracks 8 and 14 show a near-pure quadratic bow (a 2nd-order term the plane model structurally lacks explains nearly all residual variance while the linear term the model does fit explains almost none — consistent with the plane fit already correctly zeroing out the true tilt component). Track 10 needs quadratic+ (higher residual at one end, matching reviewer's 'especially high residuals at the left end' — likely an added local effect, e.g. an edge artifact or an additional cubic asymmetry, on top of the core bow). Track 21 needs quartic-or-higher to meaningfully improve on quadratic, consistent with reviewer's 'alternating lobes... long-wavelength waviness... not a single quadratic bow.' All 4 confirm: a first-order model cannot capture what's actually there.

## Resolution
<!-- OVERWRITE as understanding evolves -->

root_cause: >
  `robust_plane_detrend()` (src/nsf_fmrg_data.py:205-227) fits only a first-order affine surface
  `z = a*x + b*y + c` — its design matrix has exactly 3 columns (x, y, 1) with no quadratic or
  cross terms. This is by design and locked via Phase 01 decisions D-13/D-16 ("keep as-is, do not
  upgrade preemptively") with D-14 explicitly naming the mandatory residual QA check as the trigger
  to escalate to a fix if bow is visible. The current, real-data QA finding (visible bow on tracks
  8/10/14, alternating long-wavelength waviness on 21) is exactly the anticipated contingency
  described in D-14 and pre-flagged in research/PITFALLS.md Pitfall 6 before implementation began.
  No implementation bug was found in the fit (axis mapping, NaN masking, outlier-trimming, fit
  region, or per-track parameterization all check out correctly) and no bug was found in the QA
  plotting path — the figures faithfully show the real output of a genuinely first-order fit against
  real substrate/instrument geometry that contains real 2nd-order-and-higher structure. Live
  re-derivation on the actual 4 track height maps confirms quantitatively that a quadratic term
  explains 96-98% of the per-x residual pattern's variance on tracks 8 and 14 (vs. 0.1-3.6% for the
  linear term the current model already fits), 47% on track 10, and that track 21 needs quartic-or-
  higher terms to meaningfully improve on quadratic — matching the reviewer's visual read exactly.
  Root cause classification: methodology/model-order limitation (the plane-only fit is functioning
  exactly as coded and as decided), not a code defect.
fix: (not applied — goal: find_root_cause_only; SPEC.md already scopes the follow-up as "upgrading robust_plane_detrend() to a higher-order surface fit," deferred to a dedicated fix once D-14's QA check surfaced a problem, which it now has)
verification: (n/a — diagnose-only mode)
files_changed: []
