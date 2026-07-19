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
