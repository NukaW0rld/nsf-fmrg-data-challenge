---
status: complete
phase: 01-target-extraction-contract
source: [01-VERIFICATION.md]
started: 2026-07-20T00:54:17Z
updated: 2026-07-20T01:35:00Z
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

## Summary

total: 4
passed: 1
issues: 3
pending: 0
skipped: 0
blocked: 0

## Gaps

- gap_id: G-01-1
  truth: "No scientifically significant bow or curvature remains after detrending."
  status: failed
  reason: "User reported: plane fit removes tilt but not quadratic curvature; tracks 8, 10, and 14 show a coherent track-wide red-blue-red (end-positive/center-negative) residual bow, and track 21 shows systematic long-wavelength alternating lobes. This is too spatially coherent to be local substrate roughness."
  severity: major
  test: 1
  artifacts: []
  missing: []

- gap_id: G-01-2
  truth: "Boundaries follow the bead without unacceptable sawtooth or high-frequency excursions, and invalid regions are visibly masked rather than bridged or dropped."
  status: failed
  reason: "User reported: boundary tracking is unacceptably jagged/sawtoothed on all four tracks (worst on Track 21 with EKG-like jumps, and Track 10's lower boundary), while gap/invalid-region handling correctly shows explicit breaks rather than smoothed-over interpolation on all tracks."
  severity: major
  test: 2
  artifacts: []
  missing: []

- gap_id: G-01-3
  truth: "Real-data edge behavior is scientifically plausible and free of crop-edge artifacts."
  status: failed
  reason: "User reported: Track 10's right edge shows a sharp terminal V/spike (~0.228 -> 0.147 -> 0.800 mm, ~5.4x final jump) consistent with edge instability. Track 14's right edge passes; Track 8 and most of Track 21 are masked/disconnected and not assessable. Requested investigation of Track 10's final three grid points against raw (pre-smoothed) boundaries."
  severity: minor
  test: 3
  artifacts: []
  missing: []
