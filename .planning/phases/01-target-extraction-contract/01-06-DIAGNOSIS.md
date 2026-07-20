# Phase 1 Plan 06: Width-Ordering Regression Diagnosis

**Diagnosed:** 2026-07-20
**Diagnostic script:** `scripts/diagnose_width_regression.py`
**Sweep table:** `processed_data/targets/diagnostics/width_regression_sweep.csv`

## 1. The sweep table

Six uniform configurations (detrend order in {1, 2, 4} crossed with continuity
tracking on/off), the same order/continuity applied identically to all four
tracks, evaluated against real height-map data with no per-track values:

| detrend_order | continuity | median_width_8 | median_width_10 | median_width_14 | median_width_21 | ordering_verdict |
|---:|:---|---:|---:|---:|---:|:---|
| 1 | True  | 0.8015 | 0.6954 | 0.5520 | 0.1260 | PASS |
| 1 | False | 0.8127 | 0.7097 | 0.6369 | 0.5654 | PASS |
| 2 | True  | 0.6435 | 0.5645 | 0.4127 | 0.1657 | PASS |
| 2 | False | 0.6737 | 0.5772 | 0.5427 | 0.5309 | PASS |
| 4 | True  | 0.2357 | 0.2927 | 0.3607 | 0.1558 | FLAG |
| 4 | False | 0.5333 | 0.5379 | 0.5589 | 0.5635 | FLAG |

`data/raw/` was audited read-only before and after the sweep and reported
integrity PASS; `processed_data/targets/extraction_params.json`,
`manifest.json`, and all four published `track_*_targets.npz` files are
byte-identical (mtime- and hash-verified) before and after the run — this
diagnostic touched nothing that plan 01-05's published artifacts depend on.

For reference, the pre-01-04 (pre-quartic-detrend) baseline reported in
`01-VERIFICATION.md` was **0.8168 > 0.7410 > 0.6386 > 0.6095 mm** — an
ordering PASS. The `order=1, continuity=False` row above (0.8127, 0.7097,
0.6369, 0.5654) reproduces that baseline shape closely (continuity tracking
did not exist pre-01-05, so `order=1, continuity=False` is the closest
achievable analog to the pre-01-04 world within this sweep's two-axis
design).

## 2. Root-cause reading

**The regression is caused by `DETREND_POLY_ORDER = 4`, not by continuity
tracking.**

The verdict column flips from PASS to FLAG at exactly `detrend_order == 4`,
and it flips there under **both** continuity settings. Continuity tracking
alone (order 1 or 2, either continuity value) never breaks the ordering.
This isolates the order axis as the necessary condition for the regression:
holding continuity fixed and varying only order reproduces the FLAG; holding
order fixed at 4 and varying continuity never recovers a PASS.

Two effects are visible in the table, and only one of them is the cause of
the ordering failure:

- **Order-4 collapses and inverts tracks 8/10/14 relative to each other.**
  Moving from order 1 to order 4 (continuity=False) shrinks track 8 from
  0.8127 to 0.5333 mm (34% collapse), track 10 from 0.7097 to 0.5379 mm (24%
  collapse), and track 14 from 0.6369 to 0.5589 mm (12% collapse) — a
  systematically *unequal* collapse that inverts the original 8>10>14
  relationship into 8<10<14. This unequal, order-dependent shrinkage is
  exactly the signature predicted by Amendment A3's own risk profile: the
  quartic surface has enough degrees of freedom (15 total-degree-≤4
  coefficients) to partially fit the bead's own along-track (x-direction)
  elevated corridor as if it were background curvature, and it does so more
  aggressively for tracks with a larger/taller true bead (8 and 10, the
  highest-power tracks) than for tracks with a smaller bead (14, 21) —
  because a taller, more spatially extended bead gives the polynomial more
  systematic residual to absorb. The percentile-based half-max threshold
  then sees an artificially flattened peak-baseline separation and returns a
  narrower half-max width, disproportionately for the tracks whose beads the
  surface absorbed the most. This mechanism directly explains both the
  magnitude collapse (~3-4x smaller than the order-1 values) and the
  ordering inversion (8, 10, 14 collapse toward each other and cross) —
  it does not, however, explain track 21's separately large continuity-driven
  swing, since 21's order-4 continuity=False value (0.5635) is actually
  *higher* than its order-1 continuity=False value (0.5654) — a
  near-wash, not a collapse. Track 21's bead is smallest/least complete, so
  it has the least along-track corridor for the surface to absorb.

- **Continuity tracking has a large, order-independent effect isolated to
  track 21, but it never changes the PASS/FLAG verdict on its own.** At every
  order (1, 2, and 4), switching continuity from False to True cuts track
  21's median by roughly 3-4x (0.5654→0.1260 at order 1; 0.5309→0.1657 at
  order 2; 0.5635→0.1558 at order 4) while leaving tracks 8/10/14 comparatively
  unaffected (typically a 1-15% change, not 3-4x). This is consistent with
  track 21 being the gap-heaviest track (least-complete profilometry,
  200W/lowest power): continuity's nearest-candidate selection, once
  anchored on a narrow tracked segment, is more likely on this track to lock
  onto a persistently narrower candidate across its frequent short gaps
  instead of periodically re-selecting the largest available run. But this
  effect is present identically at order 1 (where the ordering still PASSes,
  because 0.1260 mm is still comfortably below track 14's 0.5520 mm) and at
  order 4 (where the ordering FLAGs for the unrelated 8-vs-10-vs-14 reason
  above). Continuity tracking is therefore a real, uniform (applies
  identically to all tracks, not per-track-tuned) mechanism that shrinks
  track 21's apparent width, but it is not the cause of the 8/10/14
  inversion, and removing it alone (order=4, continuity=False row) still
  FLAGs.

**Conclusion:** the order-4 detrend absorbing the bead's own elevated
corridor into the fitted background surface is the isolated cause of the
width-ordering regression. Continuity tracking is a separate, real,
uniformly-applied effect on track 21's absolute magnitude that is not
implicated in the ordering failure itself.

## 3. Pre-registered fix-selection criterion (outcome-independent)

In the same disciplined spirit as Amendment A3 (which fixed
`DETREND_POLY_ORDER=4` from measured pre-regeneration R² evidence, not from
the resulting width ordering) and D-14 (escalate to a fix only once the
mandatory residual QA check surfaces a concrete, diagnosed problem), the
following criterion is written down **before** plan 01-07 selects or applies
any fix, and it is **not** re-derived or adjusted after seeing 01-07's
resulting ordering:

> **The fix must be justified by residual structure and physical
> plausibility: the fitted detrend background surface must not follow the
> elevated bead corridor.** Concretely, a candidate fix is acceptable only if
> it can be shown, by direct inspection of the fitted surface / residual map
> relative to the known bead location, that the surface no longer partially
> reproduces the bead's own along-track height profile. A candidate fix is
> **not** acceptable merely because it happens to make `8 > 10 > 14 > 21`
> pass — outcome-shopping among sweep cells or fix variants is explicitly
> prohibited by this criterion, matching the plan's no-tuning prohibition.

**Endorsed leading remedy:** mask the bead region before fitting the
order-4 detrend surface, so a high-order polynomial cannot use bead pixels
as fitting data and therefore cannot absorb the bead's own cross-sectional
profile into the background. This is applied identically to all four
tracks (uniform mask-derivation rule, no per-track mask geometry). This
directly targets the mechanism identified in Section 2 without lowering the
surface's ability to remove genuine substrate/process curvature elsewhere in
the map.

**Fallback conditions**, in order, only if the bead-mask remedy is not
viable during 01-07 implementation:

1. If further investigation instead implicates continuity tracking as
   disproportionately harming the gap-heavy track 21 (Section 2's second
   effect, even though it did not itself break the ordering here), fix that
   mechanism uniformly — e.g., a track-independent change to gap-fallback or
   candidate-selection behavior — rather than special-casing track 21.
2. If investigation implicates the detrend **order** specifically (as this
   diagnostic's sweep does), a lower uniform order is acceptable **only**
   when justified by the residual/physical criterion above (e.g., a
   residual-map inspection showing a lower order still removes the
   originally diagnosed bow without absorbing the bead corridor) — **never**
   because a lower order happens to restore the width ordering. Per this
   diagnosis, the mask-based remedy is preferred over simply lowering the
   order, because a lower order was already shown in Amendment A3's own R²
   evidence to leave more of the originally-diagnosed global bow
   unaddressed for tracks 8 and 14 (order 2 explained 97.7%/96.3% of their
   pre-detrend bow, versus order 4's fuller correction); masking the bead
   preserves the order-4 fit's bow-removal capability while removing its
   bead-absorption failure mode.

## 4. Scope note: what this sweep does and does not establish

This {1, 2, 4} detrend-order x continuity sweep establishes the **cause** of
the regression — the isolated mechanism is the order-4 detrend absorbing the
elevated bead corridor into the fitted background surface (Section 2). The
chosen fix is **not** itself one of the six swept cells: bead-masking is not
a swept axis in this diagnostic, by design, because the sweep's purpose was
to isolate which of the two already-implemented, already-suspected
mechanisms (order, continuity) caused the regression, not to pre-evaluate
the fix. The bead-mask remedy named in Section 3 is a principled *response*
to this diagnosis; its efficacy is proven separately, by the synthetic
regression test `test_robust_plane_detrend_fit_mask_excludes_bead_from_fit`
added in plan 01-07, not by any row of `width_regression_sweep.csv`. No
reader or executor of plan 01-07 should expect sweep evidence for the mask
axis itself, or treat its absence from the sweep table as a gap.

Plan 01-07 will apply exactly **one** uniform, track-independent correction,
chosen by the Section 3 criterion. Plan 01-08 will report the resulting
`8 > 10 > 14 > 21` ordering outcome honestly, whatever it is, without further
tuning in response to that outcome.
