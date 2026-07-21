---
status: complete
phase: 01-target-extraction-contract
source: [01-VERIFICATION.md]
started: 2026-07-20T00:54:17Z
updated: 2026-07-21T19:30:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Residual curvature on all four tracks

expected: No scientifically significant bow or curvature remains after detrending.
result: issue
reported: "The maps do not pass the \"no significant leftover bow/curvature\" criterion. Track 8: Clear broad U-shaped residual: positive at both x ends and negative through the middle. It is coherent across most of the track width, so it does not look like local substrate roughness. Track 10: Same strong end-positive / center-negative pattern, with especially high residuals at the left end. Clear leftover bow. Track 14: The cleanest symmetric bow signature: red at both ends and a broad blue basin around x ≈ 55–75 mm. This is unmistakably systematic curvature. Track 21: No simple symmetric bow. It has broad alternating x-direction lobes—positive near 30 and 55 mm, negative near 40 and 80–88 mm, then strongly positive near 95 mm. That looks like long-wavelength waviness or process variation rather than a single quadratic bow, although it is still systematic rather than fine noise. The narrow vertical streaking is plausibly measurement/process texture, but the smooth, track-wide red–blue–red structure in tracks 8, 10, and 14 is much too spatially coherent to classify as ordinary local roughness. A plane fit can remove tilt but cannot remove quadratic curvature; visually, those three retain substantial bow after plane detrending."
severity: major

### 2. Boundary overlay sanity and explicit gaps

expected: Boundaries follow the bead without unacceptable sawtooth or high-frequency excursions, and invalid regions are visibly masked rather than bridged or dropped.
result: issue
reported: "The boundary smoothness check does not pass; gap handling does. Track 8: lower boundary noticeably jagged with repeated sharp downward spikes, upper boundary comparatively smoother. Track 10: highly fragmented and locally jagged, especially the lower boundary, not clean enough to call acceptable. Track 14: repeated abrupt spikes in the lower boundary, some upper-boundary jitter. Track 21: strongest sawtooth/EKG behavior, both boundaries (especially lower) jump rapidly by large cross-track distances. Gap handling passes on all tracks: masked/invalid data appear as explicit breaks/gaps (e.g. Track 10 at 175/400 valid positions, Track 21 known missing regions), echoed consistently in the width curve, with no evidence of long smooth interpolation through invalid regions. The width plots preserve gaps correctly but their valid segments are also very high-frequency and spiky, consistent with the boundary jaggedness."
severity: major

### 3. Crop-edge smoothing

expected: Real-data edge behavior is scientifically plausible and free of crop-edge artifacts.
result: issue
reported: "One clear crop-edge QA failure: Track 10's right edge shows a sharp terminal V/spike (approx 0.228 -> 0.147 -> 0.800 mm, a ~5.4x final jump) that looks like edge instability. Track 14's right edge passes with a mild rebound (0.328 -> 0.434 -> 0.760 mm), entering the band continuously and staying within the track's normal range. Track 8's bands and Track 21's left band are fully gapped (OK, not assessable). Track 21's right band is effectively masked/disconnected with only one isolated valid point, so no connected edge segment can be judged. Would not sign off on crop-edge smoothing without investigating Track 10's final three grid points against the raw (pre-smoothed) boundaries."
severity: minor

### 4. A1/A2 and no-tuning judgment

expected: Amendments A1 and A2 remain scientifically acceptable after reviewing the real QA, and the locked constants were fixed before ordering inspection and were not tuned afterward.
result: pass

### 5. Decide the 10-vs-14 width-ordering FLAG
expected: A recorded decision — accept the residual FLAG as a documented known limitation (option a, with rationale), or commission further diagnosed-defect investigation (option b). Current numbers (per `01-11-ORDERING-OUTCOME.md`): track 10 median 0.3713mm vs track 14 median 0.4765mm — narrower gap than before Amendment A5's coverage fix, but still not crossed into the expected 8>10>14>21 order. Two independent, pre-registered, outcome-independent diagnostic/fix cycles (01-06→08, then 01-11) have already targeted this defect class without forcing the outcome; the phase's HONEST-OUTCOME GUARD declines further automated tuning.
result: issue
reported: "Choose (b): commission one more targeted investigation—but make it bounded and diagnosis-only. The reason is not simply that 10 < 14. The inversion is strongly localized: through 20–70 mm, tracks 10 and 14 are essentially tied on common valid positions (0.4493 vs 0.4495 mm); from 70–100 mm, track 10 collapses to 0.0213 mm versus track 14's 0.4843 mm, and track 10 exceeds track 14 at only 8.3% of common positions in that final region. processed_data/targets/qa/track_10_overlay.png shows the extracted boundaries becoming narrow and fragmented after roughly 70 mm, while visible track structure appears to continue. That is a specific, testable anomaly, not yet persuasive evidence for a genuinely non-monotonic power-width relationship — with only one physical track per power, the project also cannot reliably separate a power effect from track-to-track experimental variability. The investigation should answer only: does track 10 physically narrow/disappear after 70 mm, or does extraction stop following the physical bead? Compare raw cross-sections, candidate half-max runs, rejection reasons, and boundary reacquisition before and after 70 mm. Pre-register the assessment criteria and prohibit choosing constants based on whether 10 > 14. If independent raw-data evidence confirms genuine narrowing or inadequate observability, accept option (a) immediately and proceed. Do not authorize another open-ended tuning cycle."
severity: major

### 6. Visual sign-off on 12 regenerated QA figures
expected: Open all 12 figures under `processed_data/targets/qa/` (residual maps, boundary overlays, width curves for tracks 8/10/14/21) and answer the four questions in `01-SIGNOFF-REQUEST.md`: residual structure is scientifically acceptable process/substrate variation on all 4 tracks; boundary overlays are continuous and physically plausible with explicit (not silently bridged) gap shading, including track 10; track 10's terminal V-spike from Test 3 above is confirmed gone; the four locked constants (DETREND_POLY_ORDER, BEAD_MASK_HEIGHT_FRACTION, MAX_TRACKING_GAP_COLUMNS, DETREND_MAX_Y_DEGREE) are confirmed fixed independently of the ordering outcome. Note: this verification round's own inspection of track_10_overlay.png/track_10_width.png found a real, continuous boundary trace now exists (a major improvement over Test 3's prior near-total absence), but it is visibly more jagged than tracks 8/21 and the width curve trails toward near-zero past x≈70mm — flagged as a domain judgment call, not something automated checks can certify.
result: issue
reported: "Would not grant full visual sign-off because the boundary overlays still fail. 1) Residual structure: Yes — tracks 8, 10, 14 no longer show the earlier coherent end-positive/center-negative bow; track 21 retains broader alternating lobes but they read as substrate/process variation, not a systematic bow; no manufactured feature hugs track 10's cross-track edge. 2) Boundary overlays: No — gap handling passes (grey shading and NaN-broken traces, no interpolation), but boundaries remain fragmented and physically implausible: track 10 has 65 separate valid runs and collapses toward near-zero width after ~70mm; tracks 8, 14, 21 also retain abrupt excursions; maximum adjacent boundary jumps are ~0.62-0.88mm across the four tracks. 3) Track 10 terminal V-spike: Yes, narrowly — old final widths ~0.228/0.147/0.800mm are now ~0.0244/0.0028/0.0175mm; the 0.800mm spike is gone, but the replacement near-zero segment is still scientifically suspicious and consistent with the broader track-10 tracking problem (see track_10_width.png). 4) Constants fixed independently: Yes — DETREND_POLY_ORDER=4, BEAD_MASK_HEIGHT_FRACTION=0.5, MAX_TRACKING_GAP_COLUMNS=10, DETREND_MAX_Y_DEGREE=2, each introduced once under its documented criterion with no later changes or per-track branches (src/targets.py:14, 01-CONTEXT.md:40); check_targets.py reports ALL CHECKS PASSED. Overall: residual curvature passes, the track-10 terminal-spike fix passes, provenance/no-tuning passes, but boundary-overlay sign-off fails — mechanical checks passing should not override that visual failure."
severity: major

## Summary

total: 6
passed: 1
issues: 5
pending: 0
skipped: 0
blocked: 0

## Gaps

- gap_id: G-01-1
  truth: "No scientifically significant bow or curvature remains after detrending."
  status: resolved
  resolved_by: "01-04-PLAN.md"
  resolved_at: "2026-07-21"
  reason: "User reported: plane fit removes tilt but not quadratic curvature; tracks 8, 10, and 14 show a coherent track-wide red-blue-red (end-positive/center-negative) residual bow, and track 21 shows systematic long-wavelength alternating lobes. This is too spatially coherent to be local substrate roughness."
  severity: major
  test: 1
  root_cause: "robust_plane_detrend() (src/nsf_fmrg_data.py:205-227) fits only a first-order affine surface (z = a*x + b*y + c) by design -- this is the documented, anticipated escalation trigger from Phase 01's own D-14 decision ('add a mandatory QA step; if curvature is visible, escalate to a fix at that point -- don't pre-solve an unconfirmed problem') and PITFALLS.md Pitfall 6. Not an implementation bug: axis mapping, invalid-sample exclusion, and iterative outlier trimming are all correct, and all 4 tracks use one identical call/parameterization. Quantitative re-derivation on the real .ASC files: quadratic model explains 96-98% of post-detrend residual variance on tracks 8/14 (vs 0.1-3.6% for linear), confirming the visual bow; track 21 needs quartic-or-higher (matches its reported alternating-lobe/long-wavelength pattern)."
  artifacts:
    - path: "src/nsf_fmrg_data.py:205-227"
      issue: "robust_plane_detrend design matrix has only 3 columns (x, y, intercept) -- structurally cannot remove quadratic/higher-order curvature"
    - path: "src/targets.py:220"
      issue: "extract_track_targets calls the plane detrend identically for all 4 tracks (no per-track workaround exists)"
  missing:
    - "Escalate per D-14/SPEC boundaries: upgrade robust_plane_detrend (or add a follow-up step) to a higher-order surface fit (e.g. quadratic design matrix [x^2, y^2, xy, x, y, 1]) while keeping the same robust/iterative outlier-trimming scheme"
    - "Track 21 may need a higher-order polynomial or smoothed non-parametric long-wavelength baseline beyond pure quadratic, without breaking the shared-parameterization constraint (TARGET-02)"
  debug_session: ".planning/debug/residual-curvature-after-detrend.md"

- gap_id: G-01-2
  truth: "Boundaries follow the bead without unacceptable sawtooth or high-frequency excursions, and invalid regions are visibly masked rather than bridged or dropped."
  status: resolved
  resolved_by: "01-05-PLAN.md"
  resolved_at: "2026-07-21"
  reason: "User reported: boundary tracking is unacceptably jagged/sawtoothed on all four tracks (worst on Track 21 with EKG-like jumps, and Track 10's lower boundary), while gap/invalid-region handling correctly shows explicit breaks rather than smoothed-over interpolation on all tracks."
  severity: major
  test: 2
  root_cause: "halfmax_edges() (src/targets.py:99-141) selects each column's boundary as the single largest contiguous above-half-max-threshold run, computed completely independently per column with zero cross-column continuity constraint. 98-100% of valid columns on every track contain more than one above-threshold blob (bead + substrate-texture blobs of similar magnitude, per RESEARCH.md Finding 4's pre-implementation warning), so which blob 'wins' flips unpredictably column-to-column -- raw single-step jumps up to 0.67-1.38mm measured directly. nan_savgol() (src/targets.py:144-162), the only anti-jitter step, is an ordinary non-robust least-squares 5-point filter with no outlier rejection; it roughly halves jump std-dev but cannot eliminate large/persistent blob-flip jumps. Confirmed NOT a coding bug -- all functions match their locked D-01-D-16/A1/A2 contract exactly (consistent with 01-VERIFICATION.md's 14/14 passing mechanical tests). This is a scientific/robustness gap in the currently-locked algorithm design, not an implementation defect."
  artifacts:
    - path: "src/targets.py:99-141"
      issue: "halfmax_edges: per-column independent 'largest run' selection with no continuity constraint linking neighboring columns"
    - path: "src/targets.py:144-162"
      issue: "nan_savgol: ordinary least-squares smoother, not robust/outlier-rejecting, insufficient to suppress blob-flip jumps produced upstream"
  missing:
    - "Algorithm-level amendment (like A1/A2, not a silent patch): add a cross-column continuity/tracking constraint (e.g. constrain each column's selected run to stay near the previous valid column's location, or a dynamic-programming/Viterbi-style boundary tracker) instead of independent per-column largest-run selection"
    - "And/or widen and robustify the post-hoc smoother (robust/iteratively-reweighted local fit with outlier down-weighting, similar in spirit to robust_plane_detrend's trimming) rather than an ordinary least-squares 5-point window"
  debug_session: ".planning/debug/boundary-tracking-sawtooth.md"

- gap_id: G-01-3
  truth: "Real-data edge behavior is scientifically plausible and free of crop-edge artifacts."
  status: resolved
  resolved_by: "01-05-PLAN.md"
  resolved_at: "2026-07-21"
  reason: "User reported: Track 10's right edge shows a sharp terminal V/spike (~0.228 -> 0.147 -> 0.800 mm, ~5.4x final jump) consistent with edge instability. Track 14's right edge passes; Track 8 and most of Track 21 are masked/disconnected and not assessable. Requested investigation of Track 10's final three grid points against raw (pre-smoothed) boundaries."
  severity: minor
  test: 3
  root_cause: "Degenerate zero-smoothing condition in nan_savgol() (src/targets.py:144-162), triggered by Track 10's specific data pattern at the crop edge -- not a masking bug. Track 10 has a legitimate, ratified Amendment A2 invalidation at grid indices 394-396 (largest run touches y=0, correctly returns None). This 3-column gap sits immediately before the final valid run (indices 397-399, the true end of the 400-point grid), so nan_savgol's 5-point window (half-width 2) can only ever find exactly 3 finite neighbors there. Its degree formula min(SG_POLYORDER=2, finite_count-1) then gives degree=2 with finite_count=3: a quadratic fit through exactly 3 points is an exact interpolant (zero residual degrees of freedom) -- smoothing is a silent no-op. Verified bit-identical raw vs 'smoothed' w_mm at indices 393/397/398/399, vs real damping at 390-392 (full window). Track 14 escapes this because its preceding A2 gap is 1 column shorter, leaving a full window at 397/398."
  artifacts:
    - path: "src/targets.py:144-162"
      issue: "nan_savgol degree-selection formula min(SG_POLYORDER, finite_count-1) allows zero residual degrees of freedom when a window has exactly SG_POLYORDER+1 (=3) finite points, silently disabling smoothing with no flag for the under-supported position"
  missing:
    - "Require strictly more finite points than degree+1 before treating a window as a real smoothing fit (e.g. only allow degree-2 fits when finite_count >= 4), falling back to a lower-order/linear fit or explicitly flagging low-confidence positions when finite_count <= SG_POLYORDER+1"
  debug_session: ".planning/debug/track10-crop-edge-spike.md"

- gap_id: G-01-4
  truth: "The 10-vs-14 width-ordering FLAG is resolved on evidence: either track 10 physically narrows/disappears after x≈70mm, or extraction is losing the physical bead there."
  status: failed
  reason: "User reported: the 10-vs-14 inversion is strongly localized, not a uniform gap. Through 20-70mm tracks 10 and 14 are tied on common valid positions (0.4493 vs 0.4495mm); from 70-100mm track 10 collapses to 0.0213mm vs track 14's 0.4843mm, and track 10 exceeds track 14 at only 8.3% of common positions in that region. track_10_overlay.png shows boundaries becoming narrow and fragmented past ~70mm while visible track structure appears to continue. User authorized exactly one further bounded, diagnosis-only investigation: compare raw cross-sections, candidate half-max runs, rejection reasons, and boundary reacquisition before/after 70mm on track 10; pre-register assessment criteria and prohibit choosing constants based on whether 10 > 14. If raw-data evidence confirms genuine physical narrowing or inadequate observability, accept option (a) (documented known limitation) immediately — no further open-ended tuning cycle is authorized."
  severity: major
  test: 5
  root_cause: ""     # Filled by diagnosis
  artifacts: []      # Filled by diagnosis
  missing: []        # Filled by diagnosis
  debug_session: ""  # Filled by diagnosis

- gap_id: G-01-5
  truth: "Boundary overlays are continuous and physically plausible (no unacceptable fragmentation or abrupt excursions), confirmed on the regenerated QA figures under the Amendment A5 contract."
  status: failed
  reason: "User reported (visual sign-off, Test 6): gap handling passes (grey shading, NaN-broken traces, no interpolation), but boundaries remain fragmented and physically implausible even after the continuity-tracking fix (01-05/G-01-2). Track 10 has 65 separate valid runs and collapses toward near-zero width after ~70mm; tracks 8, 14, and 21 also retain abrupt excursions; maximum adjacent boundary jumps are ~0.62-0.88mm across the four tracks. This is a regression/still-open finding against G-01-2's truth after its fix — recorded as a new gap per verify-work's reconciliation rule rather than reopening the resolved gap."
  severity: major
  test: 6
  root_cause: ""     # Filled by diagnosis
  artifacts: []      # Filled by diagnosis
  missing: []        # Filled by diagnosis
  debug_session: ""  # Filled by diagnosis
