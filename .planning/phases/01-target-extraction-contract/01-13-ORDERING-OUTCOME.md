# Phase 1 Plan 13 Task 3: Regeneration and Ordering-Outcome Report

**Recorded:** 2026-07-21
**Source run:** `.venv/bin/python scripts/run_target_extraction.py --project_dir .` (single, atomic, staged-and-published run; `run_id=8e8c4faa9c7341e49f4778dcc8ad408f`, published `2026-07-22T03:18:14.428306+00:00`), re-checked by `.venv/bin/python scripts/check_targets.py --project_dir .`. Run exactly once for this task, per this plan's own re-run discipline (a second invocation is permissible only to recover from an infrastructure failure, disclosed as such) -- no infrastructure failure occurred, so a single run is reported.
**Extraction contract in effect:** Amendment A6 on top of A3/A4/A5 -- `DETREND_POLY_ORDER=4`, `fit_mask=bead_exclusion_mask(...)`, `BEAD_MASK_HEIGHT_FRACTION=HALF_MAX_FRACTION=0.5`, `MAX_TRACKING_GAP_COLUMNS=10`, `max_y_degree=DETREND_MAX_Y_DEGREE=2`, and (new in this plan) `max_xy_degree=DETREND_MAX_XY_DEGREE=2` on the shared `robust_plane_detrend` call -- applied identically to all four tracks with no per-track branch. This is the mechanism `01-13-CRITERION.md` pre-registered and selected: the largest shared cross-term x-exponent cap that cleared its `0.012 mm` x-direction shape-gap tolerance on all four tracks' real data, while `test_order_four_removes_quartic_bow` and `test_detrend_does_not_diverge_at_strip_edge` both stayed green.

## Regenerated results (verbatim from `run_target_extraction.py` / `check_targets.py`)

```
Track 8 source: /home/khoa2/nsf-fmrg-data-challenge/data/raw/height_maps/Heightmap_8.ASC
Track 10 source: /home/khoa2/nsf-fmrg-data-challenge/data/raw/height_maps/Heightmap_10.ASC
Track 14 source: /home/khoa2/nsf-fmrg-data-challenge/data/raw/height_maps/Heightmap_14.ASC
Track 21 source: /home/khoa2/nsf-fmrg-data-challenge/data/raw/height_maps/Heightmap_21.ASC
data/raw/ integrity PASS: no files created, modified, or deleted.

track  power_W  valid_bins  median_mm  mean_mm
    8      400         362     0.7455   0.7267
   10      350         243     0.2589   0.2699
   14      300         297     0.4865   0.4246
   21      200         316     0.2193   0.2708
Ordering 8 vs 10: 0.7455 mm > 0.2589 mm — PASS
Ordering 10 vs 14: 0.2589 mm > 0.4865 mm — FLAG
Ordering 14 vs 21: 0.4865 mm > 0.2193 mm — PASS
Ordering FLAG outcomes are documented and never used to tune locked extraction constants.
```

(A benign `RuntimeWarning: All-NaN slice encountered` is printed by `numpy` from `targets.bin_profile`'s `np.nanmedian` call on x-bins with zero valid detrended samples in some column; this is pre-existing, non-fatal warning behavior unrelated to this plan's change, not a new defect introduced here.)

`check_targets.py --project_dir .` full output and exit code, captured verbatim:

```
$ .venv/bin/python scripts/check_targets.py --project_dir .
exit=0

track  power_W  valid_bins  median_mm  mean_mm
    8      400         362     0.7455   0.7267
   10      350         243     0.2589   0.2699
   14      300         297     0.4865   0.4246
   21      200         316     0.2193   0.2708
Ordering 8 vs 10: 0.7455 mm > 0.2589 mm — PASS
Ordering 10 vs 14: 0.2589 mm > 0.4865 mm — FLAG
Ordering 14 vs 21: 0.4865 mm > 0.2193 mm — PASS
Ordering FLAG outcomes are documented and never used to tune locked extraction constants.
ALL CHECKS PASSED
```

## Coverage: the MIN_VALID_FRACTION floor is still cleared by all four tracks

| track | power (W) | valid bins | valid fraction | vs 50% floor |
|---|---:|---:|---:|---|
| 8 | 400 | 362 | 90.5% | PASS |
| 10 | 350 | 243 | 60.75% | PASS |
| 14 | 300 | 297 | 74.25% | PASS |
| 21 | 200 | 316 | 79.0% | PASS |

Track 10's valid-bin count under Amendment A6 (243/400, 60.75%) does **not** regress below Amendment A5's established 242/400 (60.5%) -- it is materially unchanged (+1 bin), comfortably clearing the `MIN_VALID_FRACTION = 0.5` floor exactly as it did before this plan. `check_targets.py` exits **0** and prints `ALL CHECKS PASSED`. Tracks 8, 14, and 21 show small, track-uniform shifts in valid-bin count relative to their Amendment-A5 figures (364→362, 300→297, 325→316) consistent with a shared basis change affecting every track's fit slightly, not a track-specific adjustment. No track lost the coverage floor.

## Verdict: 8 > 10 > 14 > 21 is still NOT restored

The 8-vs-10 and 14-vs-21 adjacent pairs pass. The 10-vs-14 pair still FLAGs, and the reported numbers moved in the opposite direction from what a naive reading of the tail-collapse diagnosis might have predicted: track 10's regenerated median (`0.2589 mm`) is *lower* than its Amendment-A5 value (`0.3713 mm`), while track 14's median (`0.4865 mm`) is essentially unchanged from Amendment A5 (`0.4765 mm`). The gap between track 10 and track 14 widened under Amendment A6, not narrowed.

This is reported exactly as measured, with no reinterpretation to make it look better or worse than it is. The pre-registered criterion (`01-13-CRITERION.md`) is a property of the fitted surface's own x-direction shape-gap departure at a sampled set of x positions -- it is not, and was never claimed to be, a guarantee that clearing it would also flip the resulting median-width ordering. Capping the cross-term x-exponent changes what the shared detrend surface can represent everywhere across all four tracks simultaneously; the `01-13-CRITERION.md` tolerance test confirms the fitted surface's edge-vs-midpoint shape-gap no longer diverges as measured at 9 sampled x positions, but the full-resolution boundary-detection pipeline (`halfmax_edges`, continuity tracking, per-column relative thresholding) responds to the complete corrected surface at every one of the 400 grid columns, not just the 9 sampled diagnostic positions -- and evidently still yields a materially narrower track 10 in aggregate than track 14 under the corrected contract.

**No extraction parameter was changed to try to force this outcome.** `git diff --stat -- src/targets.py src/nsf_fmrg_data.py` is empty for this task's own commit -- confirmed before and after writing this file. `DETREND_MAX_XY_DEGREE`, `DETREND_MAX_Y_DEGREE`, `DETREND_POLY_ORDER`, `BEAD_MASK_HEIGHT_FRACTION`, `MAX_TRACKING_GAP_COLUMNS`, `MIN_VALID_FRACTION`, and every other locked constant remain exactly as canonicalized by Amendments A3/A4/A5/A6. `grep -n "track_id ==" src/targets.py src/nsf_fmrg_data.py scripts/run_target_extraction.py` returns nothing -- no per-track branch exists. The extractor was run exactly once for this task; it was not re-run with a different `DETREND_MAX_XY_DEGREE` value to see whether a different cap would flip the 10-vs-14 verdict, which is precisely the outcome-shopping `01-13-CRITERION.md` prohibits.

## Decision point per the phase's authorized bounded cycle

Per `01-UAT.md` Test 5 / gap `G-01-4`'s exact language, the user authorized "exactly one further bounded, diagnosis-only investigation" for this defect class, with the explicit instruction that "if independent raw-data evidence confirms genuine narrowing or inadequate observability, accept option (a) immediately and proceed. Do not authorize another open-ended tuning cycle." `.planning/debug/track10-14-ordering-tail-collapse.md` conducted that one authorized investigation and confirmed (option b) that the tail collapse is an extraction artifact, not physical narrowing; this plan (01-13) was the one further bounded, criterion-driven fix cycle it licensed.

That cycle is now complete: a falsifiable, outcome-independent criterion was pre-registered before any source change (`01-13-CRITERION.md`), the sole viable candidate mechanism (`DETREND_MAX_XY_DEGREE`) was implemented and selected purely on that criterion's own measured evidence, and the resulting regeneration is reported above exactly as measured. The 10-vs-14 FLAG persists -- indeed the gap widened rather than narrowed under the corrected contract.

**This was the phase's LAST authorized bounded, diagnosis-and-criterion-driven cycle for this defect class.** No further open-ended tuning cycle is authorized. Per the phase's explicit mandate (`must_haves`, this plan's non-recoverable-condition Section 5 of `01-13-CRITERION.md`), this report **recommends accepting the 10-vs-14 FLAG as a documented, investigated, known limitation (option a)** for the next human verification round to ratify. This recommendation is made honestly on the measured evidence, not to avoid further work: two independent diagnosis cycles (`01-06→08`, then `.planning/debug/track10-14-ordering-tail-collapse.md`) and two independent criterion-driven fix cycles (`01-11`, then this plan) have now targeted this defect class, each correctly identifying and closing a real, distinct detrend-fitting artifact (the y-edge Runge effect in `01-11`, the x-edge Runge effect in this plan) without ever forcing the width-ordering outcome -- and the ordering still does not hold. Continuing to search for another mechanism without a new, independently-diagnosed root cause would constitute exactly the open-ended tuning the user's mandate prohibits.

## What this task did NOT do

- Did not change `DETREND_MAX_XY_DEGREE`, `DETREND_MAX_Y_DEGREE`, `BEAD_MASK_HEIGHT_FRACTION`, `DETREND_POLY_ORDER`, `MAX_TRACKING_GAP_COLUMNS`, `MIN_VALID_FRACTION`, or any other locked constant in response to the observed 10-vs-14 outcome.
- Did not relax the boundary-clipped-run exclusion in `halfmax_edges`.
- Did not add a per-track branch or conditional to force track 10's median up or track 14's median down.
- Ran `run_target_extraction.py` exactly once for this task -- no comparison run against a different constant value was performed.
- Did not silently mark Phase 1 complete despite the still-unresolved 10-vs-14 ordering criterion.
- Did not propose or imply a further open-ended tuning cycle; this report's recommendation is to accept the FLAG as a documented, investigated, known limitation (option a) for human ratification.
