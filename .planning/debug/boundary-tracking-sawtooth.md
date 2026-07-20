---
status: diagnosed
trigger: "G-01-2: Track-boundary detection in the NSF FMRG target-extraction pipeline produces unacceptably jagged/sawtoothed boundary curves on all four real tracks, while invalid-region gap handling itself is correct."
created: 2026-07-19T00:00:00Z
updated: 2026-07-19T00:20:00Z
---

## Current Focus

hypothesis: CONFIRMED — halfmax_edges() selects the single "largest contiguous above-threshold run" per independently-processed 0.2mm column as the bead location, with no cross-column continuity constraint. Because on-track bead signal (peak-baseline separation, median 11.8-18.5um) is comparable in magnitude to off-track substrate roughness (p95-p5, median 9.6-20.1um; RESEARCH.md Finding 4), the vast majority of columns contain MULTIPLE separate above-threshold blobs, not one. Which blob is "largest" flips unpredictably from column to column, so the detected edge jumps between distinct, spatially-separated y-locations rather than tracking one continuously-varying edge. The post-hoc nan_savgol smoother (D-08-D-12) is implemented exactly as contracted (5-pt/~1mm window, order-2, NaN-aware) but is an ordinary non-robust least-squares local fit with no outlier rejection, so it damps but cannot eliminate these large blob-flip jumps.
test: Empirically measured on all 4 real tracks: count columns with >1 above-threshold run; measure pre- and post-smoothing step-to-step jump statistics on y_lower_raw/y_upper_raw vs finalized y_lower/y_upper.
expecting: Near-100% multi-run columns, large (>0.1mm, some >0.5-1.3mm) raw jumps that only partially shrink after smoothing.
next_action: Report root cause (find_root_cause_only mode — do not fix).

## Symptoms

expected: Boundaries follow the bead without unacceptable sawtooth or high-frequency excursions, and invalid regions are visibly masked rather than bridged or dropped.
actual: Reviewer inspected QA boundary-overlay figures for all 4 tracks: Track 8 lower boundary jagged with repeated sharp downward spikes (upper smoother); Track 10 highly fragmented/locally jagged especially lower boundary; Track 14 repeated abrupt spikes in lower boundary, some upper jitter; Track 21 strongest sawtooth/EKG behavior, both boundaries (especially lower) jump rapidly by large cross-track distances. Gap handling (explicit breaks, no bridging) confirmed correct on all tracks and explicitly OUT of scope for this investigation.
errors: None (visual QA finding, not a crash)
reproduction: Regenerate QA figures via scripts/run_target_extraction.py (src/targets.py boundary logic) and inspect processed_data/targets/qa/track_{8,10,14,21}_width.png / overlay pngs.
started: Discovered during UAT Test 2 of Phase 01 target-extraction-contract (2026-07-20 verification cycle).

## Eliminated

## Evidence

- timestamp: 2026-07-19T00:05:00Z
  checked: src/targets.py full source (233 lines)
  found: Boundary detection pipeline per x-grid bin (0.2mm): bin_profile() takes nanmedian of Z_mm over native columns falling in the bin (requires >= MIN_COLUMNS_PER_BIN=10) -> fill_small_gaps() linear-interpolates NaN runs <=10 along y within that single binned profile -> halfmax_edges() computes baseline=5th pct/peak=95th pct of the *entire* column's finite values, threshold = base+0.5*(peak-base), finds the SINGLE largest contiguous run of samples above threshold via largest_true_run(), then linearly interpolates the exact y-crossing at both ends of that run. This entire detection is done completely independently per x-bin, with zero information sharing across neighboring x-bins during detection itself.
  implication: Each of the 400 grid columns gets an independent half-max estimate. Any per-bin idiosyncrasy (median profile shape noise, an unlucky secondary above-threshold blob elsewhere in the column that happens to be the largest run, or a threshold that sits right at a noisy shoulder) can cause a large boundary excursion for that one column, unconstrained by neighbors.

- timestamp: 2026-07-19T00:06:00Z
  checked: nan_savgol() (src/targets.py:144-162), applied AFTER independent per-column detection, per D-08/D-09/D-10
  found: For each grid index i, fits a degree<=2 polynomial (degree = min(SG_POLYORDER, finite_count-1)) to the up-to-5-point window [i-2, i+2] of y_lower_raw or y_upper_raw (only over finite neighbors), evaluated at offset 0. This is a legitimate NaN-aware local Savitzky-Golay-style smoother matching D-08/D-09/D-10 exactly (5 points ~= 1mm at 0.2mm grid, order 2). However it performs an ordinary (non-robust) least-squares polyfit with NO outlier down-weighting/rejection — a single wildly-wrong raw boundary sample within the 5-point window pulls the fit toward it (least-squares is not resistant to outliers), unlike robust_plane_detrend() which explicitly iterates with percentile trimming for exactly this reason.
  implication: The contract *does* include the smoothing step exactly as locked in D-08–D-10 — it is not missing or disabled. But because it is a small (~1mm), non-robust window, it can only partially damp a single-bin misdetection outlier, not eliminate it. A single bad raw boundary value will still show up as a visible (reduced-magnitude but still sharp) spike after smoothing, especially since a real spike inside a 5-point window pulls a degree-2 fit substantially.

- timestamp: 2026-07-19T00:15:00Z
  checked: 01-RESEARCH.md Finding 4 (noise-floor grounding, already-known-and-documented risk) + a direct empirical re-run of the full extraction pipeline (bin_profile -> fill_small_gaps -> halfmax_edges -> nan_savgol/finalize_smoothed_boundaries) against all 4 real .ASC files, instrumented to count per-column above-threshold "runs" and to compare y_lower_raw/y_upper_raw (pre-smoothing) jump statistics against the final smoothed y_lower/y_upper.
  found: |
    Finding 4 (already in RESEARCH.md, written before implementation) states the bead's on-track peak-baseline separation (median 11.8-18.5um per track) is the same order of magnitude as off-track substrate roughness (p95-p5, median 9.6-20.1um) -- "signal and background magnitudes overlap; the extraction works because the bead is localized in y, not because it towers over the noise." Empirical re-run confirms the consequence: columns with MORE THAN ONE separate contiguous above-half-max-threshold run:
      Track 8:  345/348 valid columns (99.1%)
      Track 10: 172/175 valid columns (98.3%)
      Track 14: 299/299 valid columns (100%)
      Track 21: 311/311 valid columns (100%)
    i.e. essentially every column's binned y-profile has multiple separate blobs crossing the half-max threshold (bead + one or more substrate-texture blobs), not a single clean peak. halfmax_edges() takes the single largest such run via largest_true_run() with zero information from neighboring columns.
    Pre-smoothing (y_lower_raw/y_upper_raw) step-to-step diff stats (max|diff|, count of |diff|>0.1mm out of ~300-350 valid steps):
      Track 8:  lower max 0.674mm, 134 steps >0.1mm; upper max 0.893mm, 33 steps >0.1mm
      Track 10: lower max 0.729mm, 48 steps >0.1mm;  upper max 1.091mm, 13 steps >0.1mm
      Track 14: lower max 1.165mm, 74 steps >0.1mm;  upper max 1.114mm, 120 steps >0.1mm
      Track 21: lower max 1.295mm, 220 steps >0.1mm; upper max 1.376mm, 192 steps >0.1mm
    After nan_savgol + finalize_smoothed_boundaries (the exact production path in extract_targets_from_arrays), the same steps roughly halve in std-dev but a large fraction of >0.1mm jumps remain, e.g. Track 21 lower: std 0.416mm->0.209mm, count(>0.1mm) 220->158; Track 8 lower: std 0.210mm->0.114mm, count(>0.1mm) 134->86. Concrete example: Track 21 grid step x=97.9->98.1mm, y_lower raw 0.371->1.177mm (a ~0.8mm jump, ~40% of the 1.907mm measured y-window) with the candidate-run count changing 12->14 in that column pair; smoothing only partially reduces this to 0.604->1.287mm — the spike remains clearly visible.
    Cross-checked against reviewer's qualitative report: Track 8's y_upper is measurably smoother than y_lower in this data too (upper count>0.1mm=33 vs lower=134), matching "Track 8: lower boundary noticeably jagged ... upper comparatively smoother" exactly. Track 21 has the largest max|diff| and highest jump counts of all 4 tracks on both boundaries, matching "Track 21: strongest sawtooth/EKG behavior."
  implication: The sawtooth/EKG boundary behavior is a direct, mechanistic, and now-quantified consequence of the currently-locked D-01-D-04 edge-selection rule (independent per-column relative-threshold + "pick the single largest above-threshold run") applied to a signal whose on-track/off-track separation margin is small (Finding 4, known and documented pre-implementation), combined with a smoothing step (D-08-D-12) that is implemented correctly per contract but is narrow and non-robust, so it cannot suppress large, multi-column-persistent blob-selection flips. This is NOT a coding bug: nan_savgol, finalize_smoothed_boundaries, bin_profile, fill_small_gaps, and halfmax_edges all match their locked D-01-D-16/A1/A2 specifications exactly (confirmed by 01-VERIFICATION.md's 14/14 passing contract-invariant tests and by direct code re-reading in this session — no off-by-one, no disabled step, no misapplied constant found). It is a scientific/robustness gap in the current contract: the locked algorithm has no cross-column continuity/tracking prior (e.g. constraining the next column's edge to stay near the previous column's edge, a robust/outlier-rejecting boundary tracker, or a wider smoothing window) to resolve the ambiguity when a column's y-profile contains multiple competing above-threshold regions -- which RESEARCH.md's own Finding 4 already flagged as a risk before any code was written.

## Resolution

root_cause: |
  halfmax_edges() in src/targets.py selects the boundary as the single largest contiguous
  run of samples above a per-column relative half-max threshold (D-01-D-04), computed
  completely independently for each of the 400 output columns, with zero continuity
  constraint linking a column's chosen edge to its neighbors. Because the bead's on-track
  height signal (median peak-baseline separation 11.8-18.5um) is the same order of
  magnitude as off-track substrate roughness (median p95-p5 9.6-20.1um; documented in
  01-RESEARCH.md Finding 4 before implementation began), nearly every column (98-100%,
  measured on all 4 real tracks) contains MULTIPLE separate above-threshold blobs rather
  than one clean bead peak. Which blob is "largest" -- and therefore selected as the
  boundary -- flips unpredictably from column to column as ordinary substrate texture
  varies along x, producing raw boundary jumps of up to ~0.7-1.4mm in a single 0.2mm grid
  step (measured directly). The only anti-jitter mechanism in the pipeline is nan_savgol(),
  a narrow (5-point/~1mm), ordinary (non-robust, no outlier down-weighting) local
  polynomial smoother applied after detection exactly per D-08-D-12 -- it roughly halves
  the jump magnitude/std but cannot eliminate jumps that are large and/or persist across
  multiple adjacent columns, leaving the visually obvious sawtooth/EKG spikes the reviewer
  reported. All extraction code was independently verified to match its locked D-01-D-16/
  A1/A2 contract exactly (no bug); this is a robustness gap in the currently-locked
  algorithm design, not an implementation defect.
fix: []
verification: []
files_changed: []
