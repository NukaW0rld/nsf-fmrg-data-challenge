# Phase 1: Target Extraction & Contract - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-19
**Phase:** 1-Target Extraction & Contract
**Areas discussed:** Edge-detection method, Track 21 gap-handling rule, Smoothing scale/method, Detrending approach

---

## Edge-detection method

| Option | Description | Selected |
|--------|-------------|----------|
| Relative half-max threshold | Detrended per-column y-profile, edge at baseline + 0.5*(peak-baseline); relative rule generalizes across 4 differing bead heights (Pitfall 6) | ✓ |
| Fixed absolute height threshold | Single absolute z-value cutoff for all tracks | |
| Max-gradient (steepest slope) edge | Edge at steepest |dZ/dy| point | |

**User's choice:** Relative half-max threshold

| Option | Description | Selected |
|--------|-------------|----------|
| Per-column percentile split | baseline=5th pct, peak=95th pct, per x-column | ✓ |
| Track-wide baseline, per-column peak | One global baseline for whole track | |
| Fit-based (Gaussian/plateau) model | Parametric profile-shape fit | |

**User's choice:** Per-column percentile split

| Option | Description | Selected |
|--------|-------------|----------|
| 5th/95th percentile, 50% fraction | Classic half-max/FWHM convention | ✓ |
| 10th/90th percentile, 50% fraction | More conservative trim | |
| You decide — tune empirically | Defer exact numbers to QA pass | |

**User's choice:** 5th/95th percentile, 50% fraction

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — minimum separation threshold | Weak peak-baseline separation invalidates that x position | ✓ |
| No — always detect, rely on downstream smoothing/gaps | | |

**User's choice:** Yes — minimum separation threshold
**Notes:** Feeds directly into the valid-coordinate mask (TARGET-01).

---

## Track 21 gap-handling rule

| Option | Description | Selected |
|--------|-------------|----------|
| Max-gap interpolation + mask beyond it | ≤N consecutive NaN interpolated, larger gaps invalidate the column | ✓ |
| NaN-aware percentile only, no interpolation | nanpercentile directly, no interpolation | |
| Exclude any column with any gap | Most conservative, likely excludes too much of track 21 | |

**User's choice:** Max-gap interpolation + mask beyond it

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed pixel count, e.g. ≤10 consecutive NaNs | Simple, deterministic | ✓ |
| Fraction of column length, e.g. ≤10% of y_size | Scales with y-resolution | |
| You decide empirically after inspecting track 21's gaps | Defer to gap-size histogram | |

**User's choice:** Fixed pixel count, ≤10 consecutive NaNs

| Option | Description | Selected |
|--------|-------------|----------|
| 1D along y only, per column | Independent per-column interpolation | ✓ |
| 2D interpolation using neighboring x-columns | Borrow from adjacent columns | |

**User's choice:** 1D along y only, per column

| Option | Description | Selected |
|--------|-------------|----------|
| Keep grid position, width=NaN, mask=False | Fixed-length shared 0.2mm grid across all tracks | ✓ |
| Drop invalid x positions entirely | Ragged per-track arrays | |

**User's choice:** Keep grid position, width=NaN, mask=False
**Notes:** Matters directly for Phase 2's alignment step, which will consume this same grid.

---

## Smoothing scale/method

| Option | Description | Selected |
|--------|-------------|----------|
| Savitzky-Golay filter | Local polynomial fit, preserves peaks/slopes better than moving average | ✓ |
| Simple moving average | Rolling mean, tends to flatten real local variation | |
| No explicit smoothing — grid binning only | Rely on 0.2mm grid averaging alone | |

**User's choice:** Savitzky-Golay filter

| Option | Description | Selected |
|--------|-------------|----------|
| ~1mm window, order 2-3 | Preserves mm-scale variation, smooths sub-mm noise | ✓ |
| ~2-3mm window, order 2-3 | More aggressive, risks over-smoothing real variation | |
| You decide — pick empirically from visual QA | Defer to QA pass | |

**User's choice:** ~1mm window, order 2-3 polynomial

| Option | Description | Selected |
|--------|-------------|----------|
| Smooth boundaries separately, then subtract | Smooth y_upper/y_lower independently, width derived after | ✓ |
| Smooth the raw width curve directly | Single-pass on w(x) | |

**User's choice:** Smooth boundaries separately, then subtract
**Notes:** Keeps the option open for boundary-function output later (TARGET-03/v2 stretch).

| Option | Description | Selected |
|--------|-------------|----------|
| Skip invalid points in the fit, keep NaN in output | Never fabricates values for excluded positions | ✓ |
| Interpolate through invalid points before smoothing | Produces visually continuous curve but blurs measured vs. estimated | |

**User's choice:** Skip invalid points in the fit, keep NaN in output

---

## Detrending approach

| Option | Description | Selected |
|--------|-------------|----------|
| Keep as-is, but visually verify residual curvature per track | Reuse robust_plane_detrend() unchanged + mandatory QA check | ✓ |
| Upgrade now to a higher-order (quadratic) surface fit | Preemptive fix, unvalidated new component | |
| Keep as-is, no extra verification needed | Skips Pitfall 6's recommended check | |

**User's choice:** Keep as-is, but visually verify residual curvature per track

| Option | Description | Selected |
|--------|-------------|----------|
| Once per full track, before edge detection | Matches current architecture | ✓ |
| Local per-column baseline removal instead of/in addition | Conflates two different corrections | |

**User's choice:** Once per full track, before edge detection

| Option | Description | Selected |
|--------|-------------|----------|
| Keep existing defaults (stride_x=40, stride_y=2) | Don't touch working code without evidence of a problem | ✓ |
| Symmetrize the stride | Preemptive balance change | |

**User's choice:** Keep existing defaults

| Option | Description | Selected |
|--------|-------------|----------|
| Truncated/edge-mode SG filter, no exclusion | Boundary-mode shrinks window near crop edges, documented in QA plots | ✓ |
| Exclude first/last ~1mm from reported metrics | Deliberate margin exclusion | |
| You decide after visual QA on all 4 tracks | Defer to QA pass | |

**User's choice:** Truncated/edge-mode SG filter, no exclusion
**Notes:** Addresses Pitfall 7 (edge effects near 20mm/100mm crop boundaries).

---

## Claude's Discretion

- Exact noise-floor value for the minimum peak-baseline separation threshold (D-04) — to be grounded in profilometer vertical resolution during implementation.
- Precise `scipy.signal.savgol_filter` boundary-mode parameter (D-12) — chosen during implementation, verified visually.

## Deferred Ideas

None — discussion stayed within phase scope.
