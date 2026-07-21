# Phase 1 Plan 11 Task 4: Regeneration and Ordering-Outcome Report

**Recorded:** 2026-07-21
**Source run:** `.venv/bin/python scripts/run_target_extraction.py --project_dir .` (staged, atomically published; currently-published `run_id=3b94d6de79534d66ab86ef3cb678183e`), re-checked by `.venv/bin/python scripts/check_targets.py --project_dir .`. A first run (`run_id=07b0fb71caf041d289b822002dc7b054`) produced byte-identical `check_targets.py` output before this task's `<verify>` block re-ran the extractor as part of re-confirming this task's own checks — see "What this task did NOT do" for the disclosure this plan requires for any second invocation.
**Extraction contract in effect:** Amendment A5 on top of A3/A4 — `DETREND_POLY_ORDER=4`, `fit_mask=bead_exclusion_mask(...)`, `BEAD_MASK_HEIGHT_FRACTION=HALF_MAX_FRACTION=0.5`, `MAX_TRACKING_GAP_COLUMNS=10`, and (new in this plan) `max_y_degree=DETREND_MAX_Y_DEGREE=2` on the shared `robust_plane_detrend` call — applied identically to all four tracks with no per-track branch. This is the mechanism `01-11-CRITERION.md` selected via its own pre-registered fallback provision after Candidate A (basis conditioning) was measured, a priori, to be mathematically incapable of changing the fit.

## Regenerated results (verbatim from `run_target_extraction.py` / `check_targets.py`)

```
Track 8 source: /home/khoa2/nsf-fmrg-data-challenge/data/raw/height_maps/Heightmap_8.ASC
Track 10 source: /home/khoa2/nsf-fmrg-data-challenge/data/raw/height_maps/Heightmap_10.ASC
Track 14 source: /home/khoa2/nsf-fmrg-data-challenge/data/raw/height_maps/Heightmap_14.ASC
Track 21 source: /home/khoa2/nsf-fmrg-data-challenge/data/raw/height_maps/Heightmap_21.ASC
data/raw/ integrity PASS: no files created, modified, or deleted.

track  power_W  valid_bins  median_mm  mean_mm
    8      400         364     0.7528   0.7370
   10      350         242     0.3713   0.3234
   14      300         300     0.4765   0.4246
   21      200         325     0.1998   0.2579
Ordering 8 vs 10: 0.7528 mm > 0.3713 mm — PASS
Ordering 10 vs 14: 0.3713 mm > 0.4765 mm — FLAG
Ordering 14 vs 21: 0.4765 mm > 0.1998 mm — PASS
Ordering FLAG outcomes are documented and never used to tune locked extraction constants.
```

`check_targets.py --project_dir .` full output and exit code, captured verbatim:

```
$ .venv/bin/python scripts/check_targets.py --project_dir .
exit=0

track  power_W  valid_bins  median_mm  mean_mm
    8      400         364     0.7528   0.7370
   10      350         242     0.3713   0.3234
   14      300         300     0.4765   0.4246
   21      200         325     0.1998   0.2579
Ordering 8 vs 10: 0.7528 mm > 0.3713 mm — PASS
Ordering 10 vs 14: 0.3713 mm > 0.4765 mm — FLAG
Ordering 14 vs 21: 0.4765 mm > 0.1998 mm — PASS
Ordering FLAG outcomes are documented and never used to tune locked extraction constants.
ALL CHECKS PASSED
```

## Coverage: the MIN_VALID_FRACTION floor is now cleared by all four tracks

| track | power (W) | valid bins | valid fraction | vs 50% floor |
|---|---:|---:|---:|---|
| 8 | 400 | 364 | 91.0% | PASS |
| 10 | 350 | 242 | 60.5% | PASS |
| 14 | 300 | 300 | 75.0% | PASS |
| 21 | 200 | 325 | 81.3% | PASS |

Track 10's valid-bin count rose from **21/400 (5.2%)** — the state plan 01-10 correctly gated non-zero on — to **242/400 (60.5%)**, comfortably clearing the `MIN_VALID_FRACTION = 0.5` floor. `check_targets.py` exits **0** and prints `ALL CHECKS PASSED`, where it previously exited non-zero on the same coverage gate. This is the root blocker this plan (`must_haves`, `01-11-DIAGNOSIS.md`, `01-11-CRITERION.md`) exists to resolve, and it is resolved: all four track conditions now produce a usable, non-degenerate target artifact under one shared parameterization, restoring the fourth condition (track 10, 350W) to leave-one-track-out cross-validation eligibility.

Tracks 8, 14, and 21 also gained valid bins under Amendment A5 relative to their Amendment-A4 counts (359→364, 301→300 [−1], 324→325) — small, track-uniform shifts consistent with a shared basis change affecting every track's fit slightly, not a track-specific adjustment. No track lost meaningful coverage.

## Verdict: 8 > 10 > 14 > 21 is still NOT restored

The 8-vs-10 and 14-vs-21 adjacent pairs pass. The 10-vs-14 pair still FLAGs: track 10's regenerated median width (0.3713 mm) remains *lower* than track 14's (0.4765 mm), so the full chain `8 > 10 > 14 > 21` does not hold under the corrected, Amendment-A5 extraction. This is the same 10-vs-14 pair flagged in `01-08-ORDERING-OUTCOME.md` under Amendment A4 (0.2509 mm vs 0.5264 mm) — the gap has narrowed substantially (track 10's median more than doubled, from 0.2509 to 0.3713 mm; track 14's median dropped from 0.5264 to 0.4765 mm) but has not crossed.

**No extraction parameter was changed to try to force this outcome.** `git diff --stat -- src/targets.py src/nsf_fmrg_data.py scripts/check_targets.py` is empty for this task's commit — confirmed before and after writing this file. `DETREND_MAX_Y_DEGREE`, `BEAD_MASK_HEIGHT_FRACTION`, `DETREND_POLY_ORDER`, `MAX_TRACKING_GAP_COLUMNS`, and every other locked constant remain exactly as canonicalized by Amendments A3/A4/A5. `grep -n "track_id ==" src/targets.py src/nsf_fmrg_data.py scripts/run_target_extraction.py` returns nothing — no per-track branch exists.

Per this plan's HONEST-OUTCOME GUARD, this outcome is reported and not chased: `DETREND_MAX_Y_DEGREE` was not lowered further, the halfmax boundary-clip exclusion was not relaxed, and the extractor was not re-run with a different constant to see whether a different value would flip the 10-vs-14 verdict. This plan's mandate (per its `must_haves`) was specifically to characterize and resolve track 10's *valid-fraction collapse*, not to force the width-ordering pair to pass — those are separate, independently-scoped concerns, and `01-11-CRITERION.md` explicitly prohibited selecting the fix by its effect on the ordering.

## Relationship to the plan 01-08 escalation

`01-08-ORDERING-OUTCOME.md` escalated two things to a human decision: (a) whether to override the roadmap ordering criterion, or (b) diagnose track 10's valid-fraction collapse as a new defect. This plan (01-11) resolved (b) — track 10's coverage collapse is diagnosed and fixed, on evidence, without tuning to the ordering. The 10-vs-14 ordering FLAG is a separate, still-open question. Track 10's regenerated median is no longer built from a thin, unrepresentative 21-position sample (as `01-08-ORDERING-OUTCOME.md` noted was a weakness of the pre-fix number); it is now built from 242 positions, a materially more representative statistic — but that more representative number is still `0.3713 mm < 0.4765 mm` against track 14. Choice (a) — a human decision on the ordering criterion itself — remains the open item for plan 01-12's human sign-off handoff.

## What this task did NOT do

- Did not change `DETREND_MAX_Y_DEGREE`, `BEAD_MASK_HEIGHT_FRACTION`, `DETREND_POLY_ORDER`, `MAX_TRACKING_GAP_COLUMNS`, `MIN_VALID_FRACTION`, or any other locked constant in response to the observed 10-vs-14 outcome.
- Did not relax the boundary-clipped-run exclusion in `halfmax_edges`.
- Did not add a per-track branch or conditional to force track 10's median up or track 14's median down.
- Ran `run_target_extraction.py` twice for this task: once to produce the results reported above (`run_id=07b0fb71caf041d289b822002dc7b054`), and once more as part of re-executing this task's own `<verify>` automated command block (`run_id=3b94d6de79534d66ab86ef3cb678183e`). Disclosed here per this task's own re-run rule. This was not a re-run to compare or select between outcomes: both runs' `check_targets.py` output is byte-identical (diffed and confirmed empty), and no constant was changed between them — the extractor is deterministic given an unchanged contract and unchanged raw data, so the second run is a verification recovery/confirmation run, not outcome-shopping.
- Did not silently mark Phase 1 complete despite the still-unresolved 10-vs-14 ordering criterion.
- Did not treat the resolved coverage floor as resolving the separate ordering question — both are reported honestly and independently.
