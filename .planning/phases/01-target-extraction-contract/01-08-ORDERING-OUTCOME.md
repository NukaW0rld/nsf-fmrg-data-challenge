# Phase 1 Plan 08: Width-Ordering Outcome Report

**Recorded:** 2026-07-20
**Source run:** `.venv/bin/python scripts/run_target_extraction.py --project_dir .` (staged, atomically published), re-checked by `.venv/bin/python scripts/check_targets.py --project_dir .`
**Extraction contract in effect:** Amendment A4 (`DETREND_POLY_ORDER=4`, `fit_mask=bead_exclusion_mask(...)`, `BEAD_MASK_HEIGHT_FRACTION=HALF_MAX_FRACTION=0.5`, `MAX_TRACKING_GAP_COLUMNS=10`) — plan 01-07's uniform bead-mask detrend fix, applied identically to all four tracks with no per-track branch.

## Regenerated results (verbatim from `print_results` / `check_targets.py`)

```
track  power_W  valid_bins  median_mm  mean_mm
    8      400         359     0.7411   0.6808
   10      350          21     0.2509   0.1493
   14      300         301     0.5264   0.4794
   21      200         324     0.2412   0.2834

Track 10 valid fraction 5.2% is below 50% — FLAG

Ordering 8 vs 10: 0.7411 mm > 0.2509 mm — PASS
Ordering 10 vs 14: 0.2509 mm > 0.5264 mm — FLAG
Ordering 14 vs 21: 0.5264 mm > 0.2412 mm — PASS
```

## Verdict: 8 > 10 > 14 > 21 is NOT restored

The 8-vs-10 and 14-vs-21 adjacent pairs pass. The 10-vs-14 pair FLAGs: track 10's regenerated median width (0.2509 mm) is *lower* than track 14's (0.5264 mm), so the full chain `8 > 10 > 14 > 21` does not hold under the corrected, provenance-complete Amendment A4 extraction. This is the same 10-vs-14 pair that was already flagged in `01-VERIFICATION.md`'s Gap 2 finding prior to this plan; plan 01-07's bead-mask fix did not resolve it.

**No extraction parameter was changed to try to force this outcome.** `git diff --stat -- src/targets.py` is empty for this task — confirmed before and after writing this file. `BEAD_MASK_HEIGHT_FRACTION`, `DETREND_POLY_ORDER`, `MAX_TRACKING_GAP_COLUMNS`, and every other locked constant remain exactly as canonicalized by Amendment A3/A4. No per-track branch or conditional exists in `src/targets.py` (confirmed by `grep -n "track_id ==" src/targets.py` returning nothing, as it did in plan 01-07).

## Material context for the human decision: track 10's valid-fraction collapse

Track 10's valid-bin count dropped to **21/400 (5.2%)** under the Amendment A4 extraction — down sharply from the ~43.8% valid fraction (~175/400) recorded for track 10 under the pre-bead-mask contract (see STATE.md decision: "Official median-width ordering passed for all three pairs; track 10 retains a separate 43.8% valid-fraction QA flag."). Track 10's median width is therefore now computed from only 21 grid positions rather than ~175, a roughly 8x reduction in sample size for that track's summary statistic. This is reported as observed fact, not diagnosed further in this plan — 01-06-DIAGNOSIS.md Section 4 explicitly scoped plan 01-08 to report the real-data outcome, not to re-diagnose or re-fix.

This collapse is plausibly connected to the 10-vs-14 ordering flip: with only 21 valid positions surviving bead-mask + continuity-tracking + gap-handling on track 10, the resulting median is far more sensitive to which specific x-positions survived than track 8/14/21's larger valid populations (301-359 positions), making it a weaker, less representative summary statistic for track 10 specifically.

## Escalation: separate human-override decision required (per the plan's HONEST-OUTCOME GUARD)

Per this plan's non-negotiable instruction, the ordering is reported as an outcome, not tuned to pass. Because `8 > 10 > 14 > 21` is not fully restored, execution of Phase 1's remaining verification is **halted here** pending a separate human decision between:

**(a) Human override of the roadmap ordering criterion** — accept the 10-vs-14 FLAG as a documented, known limitation of the current contract (e.g., because track 10's profilometry coverage is inherently too sparse under the locked D-01..D-16 + Amendment A3/A4 rules to produce a reliable median-width comparison against track 14), and proceed to Phase 2 with this caveat recorded in ROADMAP.md / REQUIREMENTS.md traceability.

**(b) A new diagnosed defect for a follow-up plan** — investigate why track 10's valid fraction collapsed from ~43.8% to 5.2% under the bead-mask fix specifically (e.g., whether `bead_exclusion_mask` over-excludes track 10's columns because its lower-amplitude bead separates less cleanly from background noise than the other three tracks, causing `MIN_PEAK_BASELINE_SEPARATION_MM` or `MIN_VALID_Y_POINTS` to reject far more columns than before), following the same pre-registered, outcome-independent diagnosis discipline as 01-06-DIAGNOSIS.md — i.e., any future fix must be justified by residual/physical evidence, not chosen because it happens to restore the ordering.

**Recommendation: halt Phase 1 human verification sign-off (VERIFICATION.md Human Verification items #1-#3) until this decision is made.** The 12 regenerated QA figures (`processed_data/targets/qa/*.png`) and this outcome report give the human reviewer everything needed to make that call; this plan does not make it on their behalf.

## What this plan did NOT do

- Did not change `BEAD_MASK_HEIGHT_FRACTION`, `DETREND_POLY_ORDER`, `MAX_TRACKING_GAP_COLUMNS`, or any other locked constant.
- Did not add a per-track branch or conditional to force track 10's median up or track 14's median down.
- Did not re-tune, re-sweep, or re-select a different fix mechanism in response to this outcome.
- Did not silently mark Phase 1 complete despite the unresolved ordering criterion.
