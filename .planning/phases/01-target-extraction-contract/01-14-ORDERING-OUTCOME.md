# Phase 1 Plan 14 Task 2: Regeneration, Fragmentation/Jump-Statistic Report, and Ordering Outcome

**Recorded:** 2026-07-22
**Source run:** `.venv/bin/python scripts/run_target_extraction.py --project_dir .` (single, atomic, staged-and-published run; `run_id=99a4e8472f0a4164938363af0725f31b`, published `2026-07-22T03:30:49.258468+00:00`), re-checked by `.venv/bin/python scripts/check_targets.py --project_dir .`. Run exactly once for this task — no infrastructure failure occurred, so a single run is reported, and the extractor was not re-run to compare outcomes.
**Extraction contract in effect:** Amendment A7 on top of A3/A4/A5/A6 — `DETREND_POLY_ORDER=4`, `fit_mask=bead_exclusion_mask(...)`, `BEAD_MASK_HEIGHT_FRACTION=HALF_MAX_FRACTION=0.5`, `MAX_TRACKING_GAP_COLUMNS=10`, `max_y_degree=DETREND_MAX_Y_DEGREE=2`, `max_xy_degree=DETREND_MAX_XY_DEGREE=2` on the shared `robust_plane_detrend` call, and (new in this plan) `halfmax_edges` merges adjacent above-half-max sub-runs separated by at most `MAX_RUN_MERGE_GAP_PIXELS=10` samples before candidate enumeration, and gates tracked selection to candidates whose length is at least `MIN_TRACKED_LENGTH_RATIO=0.5` of the largest same-column candidate — applied identically to all four tracks with no per-track branch.

## Regenerated results (verbatim from `run_target_extraction.py`)

```
/home/khoa2/nsf-fmrg-data-challenge/src/targets.py:130: RuntimeWarning: All-NaN slice encountered
  return np.nanmedian(Zd[:, columns], axis=1)
Track 8 source: /home/khoa2/nsf-fmrg-data-challenge/data/raw/height_maps/Heightmap_8.ASC
Track 10 source: /home/khoa2/nsf-fmrg-data-challenge/data/raw/height_maps/Heightmap_10.ASC
Track 14 source: /home/khoa2/nsf-fmrg-data-challenge/data/raw/height_maps/Heightmap_14.ASC
Track 21 source: /home/khoa2/nsf-fmrg-data-challenge/data/raw/height_maps/Heightmap_21.ASC
data/raw/ integrity PASS: no files created, modified, or deleted.

track  power_W  valid_bins  median_mm  mean_mm
    8      400         361     0.7401   0.7414
   10      350         202     0.3770   0.3744
   14      300         301     0.6174   0.6529
   21      200         308     0.3825   0.4130
Ordering 8 vs 10: 0.7401 mm > 0.3770 mm — PASS
Ordering 10 vs 14: 0.3770 mm > 0.6174 mm — FLAG
Ordering 14 vs 21: 0.6174 mm > 0.3825 mm — PASS
Ordering FLAG outcomes are documented and never used to tune locked extraction constants.
```

(The `RuntimeWarning: All-NaN slice encountered` from `targets.bin_profile`'s `np.nanmedian` call is pre-existing, benign, non-fatal warning behavior on x-bins with zero valid detrended samples in some column — unrelated to this plan's change, already noted in `01-13-ORDERING-OUTCOME.md`.)

`check_targets.py --project_dir .` full output and exit code, captured verbatim:

```
$ .venv/bin/python scripts/check_targets.py --project_dir .
exit=0

track  power_W  valid_bins  median_mm  mean_mm
    8      400         361     0.7401   0.7414
   10      350         202     0.3770   0.3744
   14      300         301     0.6174   0.6529
   21      200         308     0.3825   0.4130
Ordering 8 vs 10: 0.7401 mm > 0.3770 mm — PASS
Ordering 10 vs 14: 0.3770 mm > 0.6174 mm — FLAG
Ordering 14 vs 21: 0.6174 mm > 0.3825 mm — PASS
Ordering FLAG outcomes are documented and never used to tune locked extraction constants.
ALL CHECKS PASSED
```

## Coverage: every track's valid-bin count and fraction against the 50% floor

| track | power (W) | valid bins | valid fraction | vs 50% `MIN_VALID_FRACTION` floor |
|---|---:|---:|---:|---|
| 8 | 400 | 361 | 90.25% | PASS |
| 10 | 350 | 202 | 50.50% | PASS (razor-thin margin — see below) |
| 14 | 300 | 301 | 75.25% | PASS |
| 21 | 200 | 308 | 77.00% | PASS |

**Track 10's coverage dropped materially and now sits within 0.5 percentage points of the floor.** Under Amendment A6 (`01-13-ORDERING-OUTCOME.md`), track 10 had 243/400 valid bins (60.75%). Under this plan's merge+plausibility-gate fix, it has 202/400 (50.50%) — a drop of 41 bins / ~10.25 percentage points. `check_targets.py` still exits 0 and prints `ALL CHECKS PASSED` because 50.50% >= 50.0%, so this is **not** reported as a floor breach requiring separate diagnosis per this task's own instruction (the floor was not crossed). It is reported prominently here as material context: the plausibility gate now rejects some candidates that the pre-fix nearest-midpoint rule would have accepted as "valid" (however implausible), and for track 10 specifically this converts what were previously narrow-but-selected columns into genuinely invalidated columns (no plausible candidate exists in that column at all) rather than into wider, correct selections in every case. This is an expected, not silently-hidden, consequence of tightening the selection criterion: the gate can only ever narrow the accepted candidate set relative to the pre-fix rule, and where no candidate in a column clears the plausibility floor, that column is more likely to end up excluded via the existing zero-candidate/no-selection path than it was before. No extraction constant was adjusted in response to this drop.

Tracks 8, 14, and 21 also changed relative to their Amendment-A6 counts (362→361, 297→301, 316→308) — small, track-uniform shifts consistent with a shared selection-rule change affecting every track, not a track-specific adjustment.

## Fragmentation-count and jump-statistic before/after comparison

Measured with the same methodology the diagnosis used (`.planning/debug/boundary-fragmentation-post-continuity-fix.md`): number of separate contiguous valid (`valid_mask`) runs in the finalized `w_mm`/boundary arrays, and the max adjacent-column jump in `y_lower_mm`/`y_upper_mm` restricted to index pairs where both columns are valid.

| Track | Metric | Pre-fix (diagnosed, Amendment A5) | Post-fix (this plan, Amendment A7) | Change |
|---|---|---:|---:|---|
| 8  | Contiguous valid runs | 22 | 25 | **worse** (+3) |
| 8  | Max adjacent jump, lower (mm) | 0.322 | 0.532 | **worse** |
| 8  | Max adjacent jump, upper (mm) | 0.622 | 0.912 | **worse** |
| 10 | Contiguous valid runs | 65 | 67 | **worse** (+2) |
| 10 | Max adjacent jump, lower (mm) | 0.879 | 0.743 | improved |
| 10 | Max adjacent jump, upper (mm) | 0.843 | 0.482 | improved |
| 14 | Contiguous valid runs | 63 | 61 | improved (−2) |
| 14 | Max adjacent jump, lower (mm) | 0.770 | 0.821 | **worse** |
| 14 | Max adjacent jump, upper (mm) | 0.665 | 0.624 | improved |
| 21 | Contiguous valid runs | 34 | 43 | **worse** (+9) |
| 21 | Max adjacent jump, lower (mm) | 0.715 | 0.775 | **worse** |
| 21 | Max adjacent jump, upper (mm) | 0.871 | 0.922 | **worse** |

**The fragmentation and jump-statistic improvement is NOT measurable on all four tracks — reported exactly as measured, with no reinterpretation.** Contiguous-run counts got worse on tracks 8, 10, and 21, and only marginally improved on track 14. Max adjacent-column jumps improved on track 10 (both boundaries) and on track 14's upper boundary, but got worse everywhere else, including on track 8 where both boundaries' jumps roughly doubled.

**Important caveat on this comparison's baseline:** the pre-fix numbers (22/65/63/34; the four jump-pairs) were measured in `.planning/debug/boundary-fragmentation-post-continuity-fix.md` **under Amendment A5**, immediately after plan 01-11 and before plan 01-13's Amendment A6 (`DETREND_MAX_XY_DEGREE=2`) was applied. This plan's task instructions directed comparison against those exact diagnosed numbers, and that comparison is reported above honestly and unmodified. However, Amendment A6 itself already changed every track's detrended surface and valid-bin count materially (e.g. track 10 went from 242 valid bins under A5 to 243 under A6, track 14 from 300 to 297, track 21 from 325 to 316 — see `01-13-ORDERING-OUTCOME.md`), so part of the above before/after delta reflects Amendment A6's prior, already-accepted effect, not solely this plan's merge/plausibility-gate change in isolation. This plan did not re-run against an A6-only baseline to isolate its own marginal effect, since doing so was not part of this task's instructed comparison and the constants involved are already locked; the comparison above is reported exactly as the plan specified, with this caveat disclosed rather than silently omitted.

**Root-cause interpretation of the worsened fragmentation counts:** the plausibility gate is, by construction, strictly more conservative than the pre-fix nearest-midpoint rule — it can only ever reduce the set of candidates eligible for tracked selection, never expand it. Where the pre-fix rule would previously have accepted *some* candidate (however implausibly narrow) and kept a column inside a contiguous valid run, the gate can now leave a column with zero plausible tracked candidates, which is reported through the exact same `edges is None` / `invalid_run_columns` path as any other invalid column — turning what were previously (wrong, narrow) valid selections into genuine invalidations. This directly increases the *number* of contiguous run breaks even though it eliminates the specific self-reinforcing wrong-lock mechanism the diagnosis traced (verified directly by this plan's `test_extract_targets_from_arrays_recovers_from_track8_style_propagating_wrong_lock` and `test_extract_targets_from_arrays_merges_track10_style_fragmented_bead` regressions, both of which reproduce the diagnosed Track 8 and Track 10 episodes and confirm the fix eliminates them in isolation). In other words: the fix demonstrably closes the two specific, root-caused mechanisms the diagnosis identified (verified via targeted synthetic regressions), but the *aggregate* fragmentation-count and jump-statistic metrics on the real 4-track data do not uniformly improve, because the real tracks contain many more sources of per-column candidate absence/implausibility than the two synthetic episodes this plan's tests targeted, and a stricter (more conservative) gate mechanically produces more, not fewer, contiguous-run breaks whenever it correctly declines an implausible candidate rather than silently accepting it. This is reported as the honest, measured outcome, not chased or reinterpreted to look more favorable.

## Verdict: 8 > 10 > 14 > 21 is still NOT restored, and the underlying numbers changed substantially

The 8-vs-10 and 14-vs-21 adjacent pairs pass. The 10-vs-14 pair still FLAGs. The 10-vs-14 verdict **did not change** from plan 01-13's report (both FLAG), but the underlying median widths moved substantially for every track under this plan's fix — most notably track 14 (`0.4865mm` under A6 → `0.6174mm` now, +0.131mm) and track 21 (`0.2193mm` → `0.3825mm`, +0.163mm), with track 10 also increasing (`0.2589mm` → `0.3770mm`, +0.118mm) and track 8 essentially unchanged (`0.7455mm` → `0.7401mm`). The 10-vs-14 gap widened in absolute terms (0.2276mm under A6 vs 0.2404mm now).

This directional shift is consistent with the diagnosis's own measured wrong-narrow-pick rates: tracks 14 and 21 had the highest rates (34.3% and 43.1% of tracked selections, respectively, versus 5.7%/7.1% on tracks 8/10), so removing the wrong-narrow-pick mechanism was expected to raise their median widths the most — which is exactly what was observed. Track 10's median also rose, but track 14's rose by a comparable or larger absolute amount, so the 10-vs-14 ordering does not flip. Neither outcome (whether the ordering flipped or not) is a pass/fail condition for this plan, per this plan's own frontmatter and `<action>` instructions — this plan's fix targets boundary-tracking robustness (the diagnosed self-reinforcing wrong-lock mechanism), not the width ordering.

**No extraction parameter was changed to try to force this outcome.** `git diff --stat -- src/targets.py` is empty for this task's own commit — confirmed before and after writing this file. `MAX_RUN_MERGE_GAP_PIXELS`, `MIN_TRACKED_LENGTH_RATIO`, `DETREND_MAX_XY_DEGREE`, `DETREND_MAX_Y_DEGREE`, `DETREND_POLY_ORDER`, `BEAD_MASK_HEIGHT_FRACTION`, `MAX_TRACKING_GAP_COLUMNS`, `MIN_VALID_FRACTION`, and every other locked constant remain exactly as canonicalized by Amendments A3-A7. `grep -n "track_id ==" src/targets.py` returns nothing — no per-track branch exists. The extractor was run exactly once for this task; it was not re-run with different constant values to see whether a different value would flip the 10-vs-14 verdict or improve the fragmentation/jump statistics, which is precisely the outcome-shopping this plan's HONEST-OUTCOME GUARD prohibits.

## Human verification round context

This plan (01-14) closed the two specific, root-caused mechanisms the diagnosis (`.planning/debug/boundary-fragmentation-post-continuity-fix.md`) identified: (1) noise-fragmented true beads being split into competing tiny candidates, and (2) implausibly-small candidates winning tracked selection purely on midpoint proximity, corrupting the tracking anchor and propagating a multi-column wrong lock. Both are directly regression-tested against the exact diagnosed Track 8 and Track 10 episodes and confirmed fixed in isolation. However, on the real 4-track data, the aggregate fragmentation-count and jump-statistic metrics did not uniformly improve — they got worse on several tracks, for the structural reason explained above (a stricter gate produces more contiguous-run breaks, not fewer, whenever it correctly declines an implausible candidate). This honest, mixed outcome — along with the persisting (and here, substantially reshaped) 10-vs-14 ordering FLAG and track 10's now razor-thin coverage margin (50.50% vs the 50% floor) — is presented for the next human verification round (`/gsd-verify-work 1`) to evaluate, rather than characterized here as an unambiguous success.

## What this task did NOT do

- Did not change `MAX_RUN_MERGE_GAP_PIXELS`, `MIN_TRACKED_LENGTH_RATIO`, `DETREND_MAX_XY_DEGREE`, `DETREND_MAX_Y_DEGREE`, `BEAD_MASK_HEIGHT_FRACTION`, `DETREND_POLY_ORDER`, `MAX_TRACKING_GAP_COLUMNS`, `MIN_VALID_FRACTION`, or any other locked constant in response to the observed fragmentation, jump-statistic, coverage, or ordering outcomes.
- Did not relax the D-01/D-03 boundary-clipped-run exclusion in `halfmax_edges`.
- Did not add a per-track branch or conditional to force any track's median, fragmentation count, or coverage in a particular direction.
- Ran `run_target_extraction.py` exactly once for this task — no comparison run against a different constant value was performed.
- Did not silently mark Phase 1 complete despite the persisting 10-vs-14 ordering FLAG and the razor-thin track-10 coverage margin.
- Did not reinterpret or minimize the worsened fragmentation/jump-statistic numbers on tracks 8, 10, and 21 to make the outcome look more favorable than measured.
