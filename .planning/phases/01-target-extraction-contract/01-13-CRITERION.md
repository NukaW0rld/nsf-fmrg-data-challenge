# Phase 1 Plan 13 Task 1: Pre-Registered Fix-Selection Criterion (x-direction shape-gap)

**Registered:** 2026-07-21, before any change exists in `src/targets.py` or `src/nsf_fmrg_data.py` for this plan. At the moment this document is committed, `git status --porcelain src/targets.py src/nsf_fmrg_data.py` and `git diff HEAD --stat -- src/targets.py src/nsf_fmrg_data.py` are both empty.

This mirrors `01-11-CRITERION.md`'s discipline exactly: written down before the fix is implemented, and not re-derived or adjusted after seeing Task 3's resulting width ordering. `.planning/debug/track10-14-ordering-tail-collapse.md` already confirmed (goal `find_root_cause_only`, no fix applied) that the 10-vs-14 tail collapse is an extraction artifact -- the fitted detrend surface's own y-shape prediction error grows systematically toward the domain's far edge (x=100mm) specifically on track 10. This criterion pre-registers the fix-selection test for the mechanism that targets that x-direction growth.

## 1. The criterion

**The fitted background surface's own y-shape dependence on x must not depart, at the domain's far edge (x~99mm), from its own value at the domain's interior midpoint (x~60mm) by more than a named numeric tolerance, on all four tracks, under one shared constant.**

Concretely, measured as `shape_gap(x) = median(plane[low_y_rows, x_col]) - median(plane[bead_rows, x_col])` (`scripts/diagnose_track10_tail_collapse.py`, Task 1), where `plane = Z_mm - Zd` is the fitted surface itself (isolated from residual noise) under the exact current production detrend call (`order=DETREND_POLY_ORDER`, `fit_mask=bead_exclusion_mask(...)`, `max_y_degree=DETREND_MAX_Y_DEGREE`), `low_y_rows` is `y in [0.0, 0.5]` mm, and `bead_rows` is `y in [0.7, 1.3]` mm:

> `departure = abs(shape_gap(x~99) - shape_gap(x~60))` must not exceed **`SHAPE_GAP_EDGE_TOLERANCE_MM = 0.012 mm`**, on every one of the four tracks, under one shared `DETREND_MAX_XY_DEGREE` value.

`0.012 mm` was chosen from this task's own measured departures (`processed_data/diagnostics/track10_tail_collapse_diagnosis.csv`), not from any candidate fix's outcome. Under today's (uncapped-in-x) contract, the three healthy tracks show: track 8 = `0.006038 mm`, track 14 = `0.0000539 mm`, track 21 = `0.006166 mm` -- the healthy population's largest observed departure is `0.006166 mm`. Track 10 shows `0.021200 mm`, roughly `3.4x` the healthiest tracks' largest departure. This margin is markedly narrower than `01-11-CRITERION.md`'s analogous y-edge population (which separated by one to two orders of magnitude) -- confirming this metric's natural scale genuinely differs and `0.05 mm` must NOT be reused verbatim here. `0.012 mm` sits with a comfortable margin on both sides of the two populations Task 1 measured: it is `~1.95x` above the healthy population's largest departure (`0.006166 mm`), and track 10's measured departure (`0.021200 mm`) exceeds it by `~1.77x` -- a proportionally balanced gap given the narrower natural scale of this x-direction metric, not a threshold reverse-engineered from a single track's number.

## 2. Rejection clause -- no outcome-shopping

A candidate is **NOT** acceptable merely because it restores `8 > 10 > 14 > 21`, merely because it raises any track's valid fraction, or merely because a QA plot looks better. Outcome-shopping among candidate variants -- implementing one, running the extractor, checking whether the ordering happens to pass, and keeping it only if it does -- is explicitly prohibited by this criterion, matching Amendment A3/A4/A5's precedent and `01-11-CRITERION.md`'s own rejection clause.

The boundary-clipped-run exclusion in `halfmax_edges` (D-01/D-03) is correct and is **not** an admissible candidate to relax, weaken, or bypass. `.planning/debug/track10-14-ordering-tail-collapse.md`'s full sequential reproduction already established that `halfmax_edges` and continuity tracking behave exactly as designed on the corrupted per-column input the shared detrend basis manufactures -- so the fix targets the CAUSE (the basis's x-direction fitting-error growth), never the symptom (the exclusion that correctly discards the resulting edge-touching artifact).

## 3. The candidate mechanism

There is exactly one candidate here, not a manufactured choice among several: `01-11-CRITERION.md` already established, by measurement, that "basis conditioning" (rescaling centered coordinates before building the monomial design matrix) cannot change a full-rank least-squares fit's fitted values for ANY axis -- column rescaling only changes the conditioning of solving for the coefficients, not what surface those coefficients describe. That mechanism is not re-considered here for the same reason it was rejected there.

**Capping the x-exponent of cross/interaction monomial terms (`max_xy_degree`).** In `robust_plane_detrend`'s basis, `exponents = [(i, j) for degree in range(order+1) for i in range(degree+1)]`, optionally filtered by the existing `max_y_degree` cap (`j <= max_y_degree`). The surviving cross terms after `max_y_degree=2` are `(1,1), (2,1), (3,1), (1,2), (2,2)` -- their x-exponents (`i` = 1, 2, 3, 1, 2) are NOT bounded by `max_y_degree`, which only bounds `j`. A term like `(3,1)` lets the y-linear-slope coefficient vary as a cubic in x, which can diverge disproportionately near the domain's far edge for a track whose fit must reproduce an unusually large x-magnitude drift (track 10's raw along-track drift is ~40-85x larger than the other three tracks', per the debug session's evidence).

The candidate: further filter `exponents` to drop any `(i, j)` where `j >= 1` and `i > max_xy_degree`. Terms with `j == 0` (pure along-track) are left fully intact at every x-degree up to `DETREND_POLY_ORDER`, so Amendment A3's quartic bow-removal capacity is structurally unaffected. Terms with `i == 0` (pure cross-track) are governed only by the existing `DETREND_MAX_Y_DEGREE` cap, unaffected by this new cap.

**Constant of record:** `DETREND_MAX_XY_DEGREE` (int). **Keyword:** `max_xy_degree` on `robust_plane_detrend`, defaulting to `None` (today's behavior, i.e. bit-for-bit identical to omitting it).

## 4. Evidence that would REJECT the candidate

- No shared `DETREND_MAX_XY_DEGREE` value clears Section 1's `0.012 mm` tolerance on all four tracks simultaneously.
- OR the chosen value regresses `test_order_four_removes_quartic_bow`'s >=100x residual-magnitude-reduction assertion (Amendment A3's own along-track bow-removal regression).
- OR it regresses `test_detrend_does_not_diverge_at_strip_edge` (Amendment A5's own y-edge fix, which must stay green with the new cap applied on top).
- OR it requires a per-track value to clear the tolerance (violating TARGET-02's single shared parameterization).

## 5. The non-recoverable branch

The "is it physical" non-recoverable branch does **not** apply here: `.planning/debug/track10-14-ordering-tail-collapse.md` already confirmed, on four independent, mutually consistent measurements (flat raw within-column bead contrast across the full x-range; a detrended-residual low-y-vs-mid-y gap growing ~4-5x specifically in x>70mm on track 10 only; the fitted plane's own low-y-vs-mid-y value crossing zero and growing monotonically with x; and full sequential reproduction of the boundary-tracking algorithm showing the true-bead candidate vanishing from the per-column candidate set itself), that this is a detrend-fitting artifact (option b), not genuine physical narrowing. That question is closed.

This plan's OWN non-recoverable condition is defined instead: if Task 2 cannot find any `DETREND_MAX_XY_DEGREE` value satisfying Section 1 under Section 4's constraints, Task 2 applies **no fix** -- no new constant, no behavior change, no Amendment A6 -- and Task 3 reports the unresolved outcome. Per `01-UAT.md` Test 5's exact language ("the user authorized exactly one further bounded... no further open-ended tuning cycle is authorized"), this is the phase's **LAST** authorized bounded, criterion-driven cycle for this defect class. If the criterion cannot be cleared, Task 3 must recommend accepting the 10-vs-14 FLAG as a documented, investigated, known limitation (option a) rather than proposing a further cycle.

## 6. The tie-break/selection rule (fixed now)

Candidate values of `DETREND_MAX_XY_DEGREE` form an ordered scale: smaller values remove more cross-term fitting capacity from the shared basis. Mirroring Amendment A5's own reasoning for `DETREND_MAX_Y_DEGREE=2`, prefer the **LARGEST** value of `DETREND_MAX_XY_DEGREE` that clears Section 1's criterion under Section 4's constraints -- this preserves the maximum cross-track fitting capacity the criterion permits, rather than being the smallest cap that happens to work. This rule is fixed here, before implementation, and is not to be revisited by comparing resulting widths, valid fractions, or ordering.
