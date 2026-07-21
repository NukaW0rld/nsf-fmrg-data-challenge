# Phase 1 Plan 11 Task 2: Pre-Registered Fix-Selection Criterion

**Registered:** 2026-07-21, before any change exists in `src/targets.py` or `src/nsf_fmrg_data.py` for this plan. At the moment this document is committed, `git status --porcelain src/targets.py src/nsf_fmrg_data.py` and `git diff HEAD --stat -- src/targets.py src/nsf_fmrg_data.py` are both empty.

This mirrors `01-06-DIAGNOSIS.md` Section 3's discipline: written down before the fix is implemented, and not re-derived or adjusted after seeing Task 4's resulting width ordering.

## 1. The criterion

**The fitted background surface must reproduce the raw substrate's own low-frequency cross-track structure across the full y extent without manufacturing a height feature at the y-strip edge that the raw data does not contain.**

Concretely, measured against the fitted surface's row-median profile (`fitted_surface_edge_report` from `scripts/diagnose_track10_coverage.py`, Task 1):

> For a track whose raw substrate signal is interior — i.e. `raw_argmax_near_edge == False` in `01-11-DIAGNOSIS.md`'s Task 1 measurements, true for all four tracks — the fitted surface's row-median value at the y=0 edge and at the y=N-1 edge must each lie within **`MANUFACTURED_EDGE_TOLERANCE_MM = 0.05 mm`** of the fitted surface's own row-median value at the interior midpoint:
>
> `abs(fitted_surface_y0_mm - fitted_surface_ymid_mm) <= 0.05` and `abs(fitted_surface_yN_mm - fitted_surface_ymid_mm) <= 0.05`

This is a property of the fitted surface relative to itself — never a property of the resulting width, valid fraction, or ordering. `0.05 mm` was chosen from Task 1's already-committed measurements, not from any candidate fix's outcome: under today's (broken) contract, the three healthy tracks (8, 14, 21) show edge-to-midpoint departures of 0.0002-0.0057 mm — roughly one to two orders of magnitude below the tolerance — while track 10 shows departures of 0.0592-0.1226 mm, two to twenty-five times the tolerance. The tolerance sits with a comfortable margin (~9x) above the healthy tracks' largest observed departure and well below (~1.2x-2.5x) track 10's smallest observed violation, so it is not a threshold tuned to a single track's number; it separates the two populations Task 1 already measured with room on both sides.

## 2. Rejection clause — no outcome-shopping

A candidate is **NOT** acceptable merely because it restores `8 > 10 > 14 > 21`, merely because it raises track 10's valid fraction, or merely because a QA plot looks better. Outcome-shopping among candidate variants — implementing one, running the extractor, checking whether the ordering happens to pass, and keeping it only if it does — is explicitly prohibited by this criterion, matching the plan's no-tuning prohibition and Amendment A3/A4's precedent.

The boundary-clipped-run exclusion in `halfmax_edges` (D-01/D-03) is correct and is **not** an admissible candidate to relax, weaken, or bypass. `01-11-DIAGNOSIS.md` establishes that track 10's edge-touching residual peak is a manufactured artifact of the shared detrend basis, not a genuine physical feature — so the fix targets the CAUSE (the basis producing that manufactured feature), never the symptom (the exclusion that correctly discards it).

## 3. Candidate mechanisms

Both are uniform and track-independent; both are drawn from `robust_plane_detrend`'s two concrete intervention points named in this plan (`src/nsf_fmrg_data.py:220-232`).

### Candidate A — Basis conditioning (`DETREND_NORMALIZE_BASIS`)

`robust_plane_detrend` centers `x` and `y` but does not scale them, so at `DETREND_POLY_ORDER = 4` the design-matrix columns span roughly x-to-the-fourth on the order of 2.5e6 against y-to-the-fourth on the order of 1, and `np.linalg.lstsq(..., rcond=None)` truncates against that spread.

**Deciding measurement (already gathered, a priori, in Task 1):** `design_matrix_condition`'s unscaled-vs-scaled comparison. All four tracks show `design_cond_unscaled` in the narrow band 1.62e7-1.75e7 (this depends only on the shared x/y sampling grid, not on any track's height data) collapsing to `design_cond_scaled` of 21.10-21.13 once each centered coordinate is divided by its own half-span — a ~6-order-of-magnitude conditioning improvement, uniform across all four tracks. This is a property of the shared grid geometry and the basis construction, not of any track's resulting width or ordering.

**Constant of record:** `DETREND_NORMALIZE_BASIS` (bool). **Keyword:** `normalize_basis` on `robust_plane_detrend`, defaulting to `False` (today's behavior).

### Candidate B — Per-axis degree cap (`DETREND_MAX_Y_DEGREE`)

The mapped strip is roughly 80 mm along-track against 1.91 mm cross-track, so a total-degree-4 basis carries a degree-4 cross-track polynomial over a strip 42 times shorter than the along-track extent — the classic setting for Runge-type divergence at the strip edge.

**Deciding measurement:** whether capping the cross-track exponent removes the manufactured edge feature (Section 1's edge-vs-midpoint test) on all four tracks while preserving the along-track bow removal Amendment A3 established (`test_order_four_removes_quartic_bow` must stay green). Task 1 gathered no direct a priori numeric measurement isolating a specific cap value for this candidate — establishing it requires implementing the cap and re-checking Section 1's criterion, which Task 3's regression test does.

**Constant of record:** `DETREND_MAX_Y_DEGREE` (int). **Keyword:** `max_y_degree` on `robust_plane_detrend`, defaulting to `None` (today's behavior).

## 4. Evidence that would REJECT each candidate

- **Candidate A is rejected** if, after dividing each centered coordinate by its half-span, track 10's fitted surface still shows `abs(fitted_surface_y0_mm - fitted_surface_ymid_mm) > 0.05` or `abs(fitted_surface_yN_mm - fitted_surface_ymid_mm) > 0.05` (the manufactured edge feature survives normalization), or if it changes the order=1 affine path's output for any other caller (violates the "default reproduces today's behavior" requirement), or if it regresses `test_order_four_removes_quartic_bow` (the normalized fit removes less of the genuine along-track bow than the unnormalized order-4 fit did).
- **Candidate B is rejected** if some choice of `DETREND_MAX_Y_DEGREE` cannot be identified for which track 10 clears Section 1's edge-vs-midpoint tolerance on all four tracks simultaneously under one shared value, or if the chosen cap re-introduces on tracks 8 and 14 the global bow Amendment A3 was adopted to remove (i.e. `test_order_four_removes_quartic_bow`'s ≥100x residual-magnitude-reduction assertion fails), or if it requires a track-specific cap to work (which would violate TARGET-02's single shared parameterization).

## 5. The non-recoverable branch

This branch does **not** apply here: `01-11-DIAGNOSIS.md` (Task 1) measured track 10's raw row-median argmax at y-index 380/480 — 79% across the strip, `raw_argmax_near_edge == False` — with no raw-data evidence of a boundary-adjacent or beyond-window bead. Had Task 1 instead reported a raw argmax at or adjacent to a y-strip edge with no interior maximum, that would have established the bead is genuinely truncated by the profilometer's y-window; in that case Task 3 would apply NO fix, introduce no constant, write no Amendment A5, and Task 4 would report the unchanged outcome and escalate to the human sign-off handoff in plan 01-12. Because the measured evidence instead supports the recoverable (fitting-artifact) reading, this branch is recorded here for completeness but is not taken.

## 6. Tie-break rule (fixed now)

If both candidates satisfy Section 1's criterion, **prefer Candidate A (basis conditioning)** — it alters no basis term (every monomial exponent pair `robust_plane_detrend` already constructs stays in the fit; only the coordinate scale changes) and is a pure numerical correction, whereas Candidate B removes basis terms entirely (changing what the model is capable of representing). The less invasive change is preferred under no-outcome-driven-tuning: this rule is fixed here, before implementation, and is not to be revisited by comparing resulting widths, valid fractions, or ordering.

**Selection for this plan:** Candidate A (basis conditioning, `DETREND_NORMALIZE_BASIS` / `normalize_basis`) is selected. Task 1's a priori design-matrix-conditioning evidence (Section 3 above) already isolates the mechanism — a uniform, track-independent, ~6-order-of-magnitude ill-conditioning defect present identically on all four tracks' design matrices — as sufficient grounds to proceed with Candidate A first, consistent with the tie-break rule's preference for the less invasive fix. Task 3 implements `normalize_basis` and verifies Section 1's edge-vs-midpoint tolerance and the quartic-bow-removal regression before treating the fix as accepted. If Task 3's implementation reveals Candidate A does not clear Section 4's rejection evidence, Task 3 falls back to Candidate B under this same document's Section 3/4 terms rather than inventing a new mechanism.
