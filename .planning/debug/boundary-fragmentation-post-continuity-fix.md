---
status: diagnosed
trigger: "G-01-5: Under Phase 01's target-extraction pipeline, boundary overlays remain fragmented and physically implausible after 01-05-PLAN.md's continuity-tracking fix (for G-01-2) and Amendment A5's bead-mask/quartic-detrend changes. Track 10 has 65 separate valid contiguous runs and collapses toward near-zero width after ~70mm; tracks 8/14/21 retain abrupt excursions; max adjacent-column boundary jumps are ~0.62-0.88mm across all four tracks (down from pre-fix 0.67-1.38mm, but not eliminated)."
created: 2026-07-21T00:00:00Z
updated: 2026-07-21T00:30:00Z
---

## Current Focus

hypothesis: CONFIRMED (revised from initial). MAX_TRACKING_GAP_COLUMNS resets are RARE (1-2 per track) and NOT the dominant mechanism. The actual residual defect is in halfmax_edges' tracked-selection rule itself: `min(candidates, key=(abs(mid - previous_center), -length, start))` has NO maximum-distance gate and NO length/plausibility weighting beyond an unreachable exact-tie tiebreak -- it unconditionally picks whichever candidate run is numerically nearest to previous_center, however far away or however tiny that candidate is, and however much larger a bead-plausible candidate is in the very same column. Because previous_center is then unconditionally overwritten with the newly-chosen (possibly wrong) run's own midpoint every single successful column, one spurious column (where noise fragments the true bead's above-threshold run into several small sub-runs, or the true run momentarily fails to clear threshold at all) can permanently corrupt the anchor and trigger a SELF-REINFORCING WRONG LOCK that persists across many subsequent columns -- a new failure mode the pre-fix independent-per-column algorithm did not have (each column used to be independent; now one bad column poisons the ones after it) -- until, by chance, no small near-anchor candidate exists in some later column and the true (wide) bead is recovered by default.
test: (1) Instrumented extract_targets_from_arrays with full candidate-list logging on all 4 real tracks (read-only, ad-hoc script, `.venv/bin/python` against real `data/raw/height_maps/*.ASC`). (2) Quantified, per track, how often the tracked-selection rule picks a candidate under 40% of the largest same-column candidate's length while a >=50-native-pixel (bead-plausible) candidate was available in the same column. (3) Traced a concrete multi-column wrong-lock episode step-by-step on Track 8 (x=24.9-26.5mm) and Track 10 (x=67.1-81.9mm).
expecting/found: Confirmed. Wrong-narrow-pick rate: Track 8 5.7% (21/369), Track 10 7.1% (18/253), Track 14 34.3% (106/309), Track 21 43.1% (151/350) of all tracked (previous_center-driven) selections. Track 8 example: true bead candidate (len 195-266, width ~0.8-1.0mm) tracked correctly x=24.1-24.7mm; at x=24.9mm the true-bead-region candidate vanishes from that one column's candidate list (only small candidates near a different y remain) -> nearest-to-history picks a len=23 candidate (width collapses 1.06mm->0.09mm) -> previous_center corrupted to ~0.59 -> for the next 8 columns (x=25.1-26.5mm, spanning ~1.4mm of track) the true wide bead candidate (still present in the SAME columns, e.g. len=277 at x=25.1) is repeatedly rejected as "too far" from the corrupted anchor in favor of tiny (len 1-24) candidates near the corrupted position -> only recovers at x=26.7mm when no small candidate remains nearby, forcing selection back onto the true bead. Track 10 shows the identical mechanism far more often (frequent big_gap dropouts + frequent above-threshold-run fragmentation in the x>70mm region), producing a near-continuous narrow-width lock from x~68mm to beyond x~82mm with only brief true-bead recoveries. Finalized (post-nan_savgol) max adjacent-column jumps reproduced directly: Track 8 0.322/0.622mm, Track 10 0.879/0.843mm, Track 14 0.770/0.665mm, Track 21 0.715/0.871mm (lower/upper) -- matching the reported ~0.62-0.88mm range. Finalized valid_mask contiguous-run counts reproduced exactly: Track 8=22, Track 10=65 (exact match to reported "65 separate valid runs"), Track 14=63, Track 21=34.
next_action: Report root cause (find_root_cause_only mode -- do not fix; investigation complete).

## Symptoms

expected: |
  Boundary overlays (upper/lower boundary traces overlaid on each track's height-map image, in processed_data/targets/qa/track_{id}_overlay.png) should be continuous and physically plausible: no unacceptable fragmentation into many disconnected valid runs, no abrupt cross-track-distance jumps between adjacent grid columns, and gaps should only appear where data is genuinely invalid (explicit masked/NaN regions), not from tracking losing the bead.
actual: |
  User's own quantitative re-analysis of the regenerated (post-01-05, post-Amendment-A5) QA figures:
  - Gap handling passes: invalid columns show explicit grey shading / NaN-broken traces, not silently bridged/interpolated, on all four tracks.
  - Boundary continuity does NOT pass: track 10 has 65 separate valid contiguous runs (i.e., its boundary trace is broken into 65 disconnected segments across the 400-column grid) and its width collapses toward near-zero after roughly x=70mm.
  - Tracks 8, 14, and 21 also retain abrupt excursions in their boundary traces.
  - Maximum adjacent-column boundary jumps are roughly 0.62-0.88mm across the four tracks (still large jumps, even after the continuity-tracking fix was supposed to suppress "blob flips" of 0.67-1.38mm that were measured before the fix).
  So the 01-05 continuity-tracking fix reduced but did NOT eliminate the fragmentation/jump problem it targeted (G-01-2's root cause: halfmax_edges' per-column independent largest-run selection with no continuity constraint, per .planning/debug/boundary-tracking-sawtooth.md).
errors: None reported — no exceptions; check_targets.py exits 0. This is a persistent scientific/robustness quality gap, not a crash.
reproduction: |
  Test 6 in .planning/phases/01-target-extraction-contract/01-UAT.md ("Visual sign-off on 12 regenerated QA figures").
  Inspect processed_data/targets/qa/track_{8,10,14,21}_overlay.png and track_{8,10,14,21}_width.png (already generated, read-only).
started: Discovered during final visual sign-off (UAT Test 6), after G-01-2's 01-05 continuity-tracking fix, Amendment A5's bead-mask/quartic-detrend changes (01-07/01-08), and the track-10-coverage fix (01-11) were all already applied and QA figures regenerated.

## Eliminated

- hypothesis: "MAX_TRACKING_GAP_COLUMNS=10 resets to the untracked largest-run fallback are the dominant residual mechanism (i.e., Track 10 keeps losing its anchor and re-falling into the pre-fix largest-run bug)."
  evidence: "Instrumented the real 4-track pipeline: actual reset events (invalid_run_columns reaching 10+, forcing previous_center=None) occur only 1-2 times per track (Track 8: 0, Track 10: 1 counted reset event logged at x=91.9mm plus 2 invalid-runs>=10 total, Track 14: 0, Track 21: 0). This is far too rare to explain 65 fragmented runs on Track 10 or the widespread jump statistics on all 4 tracks. The reset mechanism itself works as designed (rare, bounded) -- it is not the source of the residual defect."
  timestamp: 2026-07-21T00:10:00Z

## Evidence

- timestamp: 2026-07-21T00:05:00Z
  checked: "src/targets.py:137-193 (current halfmax_edges), read in full alongside 01-05-PLAN.md's described design and 01-05-SUMMARY.md's reported before/after jump table."
  found: |
    The tracked-selection branch is:
    `start, stop = min(candidates, key=lambda run: (abs(y_mm[mid] - previous_center), -(run[1]-run[0]), run[0]))`
    This is a pure nearest-neighbor rule over ALL non-clipped candidates in the column, with:
    (a) no maximum-distance gate -- it always returns *some* candidate, however far the nearest one is from previous_center, rather than ever concluding "no candidate is close enough to be trusted, invalidate this column";
    (b) length/plausibility only as an exact-float-tie tiebreak (`-(run[1]-run[0])`), which in practice almost never fires since two candidates' midpoint distances to a float previous_center essentially never tie exactly -- so a 1-native-pixel noise spike and a 300-pixel true bead run are treated as equally valid candidates, decided purely by which one's *midpoint* happens to be marginally closer to history.
    In `extract_targets_from_arrays` (src/targets.py:277-283), `previous_center` is unconditionally overwritten with `0.5*(edges[0]+edges[1])` on every successful (non-None) column, with no check that the new selection is itself plausible relative to recent history.
  implication: "The continuity mechanism has no rejection/gating criterion at all -- it is architecturally identical to 'always trust whatever locally-nearest candidate exists,' which is a materially weaker guarantee than 01-05-PLAN's own stated intent (its interfaces language and the original debug session's suggested fix direction both describe 'constrain...to stay near' / a bounded or DP/Viterbi-style tracker) and than what could prevent runaway lock-on."

- timestamp: 2026-07-21T00:15:00Z
  checked: "Real Track 8 data, columns x=24.1mm to x=26.9mm (grid indices 20-34), full per-column above-half-max candidate list logged via ad-hoc instrumentation of the actual extract_targets_from_arrays loop (ad-hoc script, not committed)."
  found: |
    x=24.1-24.7mm: true bead candidate present every column, length 195-266 (width ~0.78-1.06mm), correctly tracked, previous_center follows ~1.15-1.28.
    x=24.9mm (i=24): the true-bead-region candidate is ABSENT from this one column's candidate list (only small candidates near y=0.1-0.6 remain, largest len=32). previous_center=1.168 (stale from prior column). Nearest available is (mid=0.589, len=23) at distance 0.579mm -- selected anyway (no gate rejects it) -> width collapses from ~1.1mm to 0.091mm; previous_center corrupted to 0.590.
    x=25.1mm (i=25): candidate list DOES include the true bead again -- (mid=1.111, len=277) is present in this exact column -- but since previous_center is now the corrupted 0.590, the true bead (distance 0.521) loses to a nearby small candidate (mid=0.530, len=7, distance 0.060) -> width=0.030mm.
    This self-reinforcing wrong lock persists for 8 more columns (x=25.3 through 26.5mm, ~1.4mm of track), each choosing a tiny (len 1-24) candidate near the corrupted anchor while a true-bead-sized candidate (len 165-269) is present and rejected in most of the same columns purely on midpoint-distance grounds.
    Recovery only occurs at x=26.7mm (i=33), where the small candidates near the corrupted anchor happen to vanish from that column entirely, forcing selection back onto the only remaining plausible candidate (the true bead, len=256) by default -- not because the algorithm ever recognized the lock was wrong.
  implication: "Confirms the mechanism directly and concretely: one spurious per-column misdetection (true above-threshold run momentarily absent/fragmented) triggers a MULTI-COLUMN persistent wrong lock, not a single-column flip. This is qualitatively different from -- and in some stretches visually worse than -- the pre-01-05 bug, because errors now propagate forward via the unconditionally-updated anchor instead of being independent per column."

- timestamp: 2026-07-21T00:20:00Z
  checked: "Real Track 10 data, columns x=65.1mm to x=81.9mm (grid indices 225-309), same instrumentation."
  found: |
    Good tracking (width 0.35-0.60mm, near true bead length ~130-155 native px) through x=65.1-66.7mm.
    x=67.1mm (i=235): the true bead's above-threshold run has FRAGMENTED into 3 adjacent sub-runs within ~0.13mm of each other (mid=0.984 len=5, mid=1.031 len=18, mid=1.111 len=20) instead of one ~130-155-length run -- consistent with a local noise dip briefly pulling part of the bead's profile below the half-max threshold. Nearest-to-history selects the len=18 fragment (width 0.074mm, vs. the ~0.5mm true bead width that would result if the fragments were treated as one feature). previous_center is now anchored to a narrow fragment's own midpoint.
    x=68.1mm onward: candidates near the true bead's OLD y-location increasingly disappear from columns entirely, replaced by unrelated small candidates near y=0.4-0.6mm; because previous_center is already corrupted, these keep winning nearest-selection.
    From x~68mm through the rest of the inspected range (x=81.9mm), the tracker stays locked in a narrow (0.002-0.09mm wide) mode almost continuously, interrupted only by real invalid/big_gap columns (Track 10's dominant invalidity reason: 112/400 columns fail on the internal 10-native-pixel gap check, concentrated later in the track) and by brief true-bead recoveries at columns where the true wide candidate happens to be the ONLY candidate present (e.g., x=70.5mm, width jumps back to 0.523mm) before relapsing into the narrow lock at the very next column.
    Mean width of successfully-tracked ('ok') columns: 0.4268mm for x<70mm vs. 0.0712mm for x>=70mm -- a ~6x collapse, matching the reported "collapses toward near-zero after ~70mm."
  implication: "Track 10's severe fragmentation/collapse is the SAME mechanism as Track 8's, just triggered far more often: Track 10 has both a much higher genuine native-data-gap rate (112/400 big_gap, vs. 25-79 on the other 3 tracks) and, in the x>70mm region specifically, more frequent above-threshold-run fragmentation providing repeated trigger opportunities, with few forced-recovery columns to break the lock. This is why the same algorithmic gap manifests as visually catastrophic on Track 10 but as moderate (still real) excursions on 8/14/21."

- timestamp: 2026-07-21T00:25:00Z
  checked: "Quantified wrong-narrow-pick rate across all 4 real tracks: count of tracked (previous_center-driven) column selections where the chosen candidate's length is under 40% of the largest same-column candidate's length, restricted to columns where that largest candidate is itself bead-plausible (>=50 native pixels)."
  found: "Track 8: 21/369 tracked selections (5.7%); Track 10: 18/253 (7.1%); Track 14: 106/309 (34.3%); Track 21: 151/350 (43.1%). Concrete examples include cases where a length-1-native-pixel noise spike is chosen over a length-339-pixel true-bead-plausible candidate in the very same column (Track 21, x=28.7mm), purely because the 1-pixel spike's midpoint happened to be closer to a (possibly already slightly corrupted) previous_center."
  implication: "This is not a Track-10-specific or rare edge case: on 2 of the 4 tracks, over a third of all continuity-tracked selections choose a candidate that is dramatically narrower than an available same-column alternative. The magnitude varies by track (likely tied to how frequently that track's raw bead signal locally dips near/below the half-max threshold, i.e., signal-to-noise margin per RESEARCH.md Finding 4), but the underlying algorithmic gap -- selection by pure midpoint-proximity with no size/plausibility weighting or distance gate -- is present identically in all 4 tracks' shared, untuned code path."

- timestamp: 2026-07-21T00:30:00Z
  checked: "Reproduced the exact finalized (post-nan_savgol) jump and fragmentation statistics reported in UAT Test 6, using the current (post-01-05, post-Amendment-A5) code and real artifacts, via `T.extract_track_targets` end-to-end (no modification to src/targets.py)."
  found: "Finalized valid_mask contiguous-run counts: Track 8=22, Track 10=65, Track 14=63, Track 21=34 -- Track 10's count is an EXACT match to the reviewer's reported '65 separate valid runs.' Finalized max adjacent-column jumps (lower/upper): Track 8 0.322/0.622mm, Track 10 0.879/0.843mm, Track 14 0.770/0.665mm, Track 21 0.715/0.871mm -- matching the reviewer's reported '~0.62-0.88mm across the four tracks' range closely."
  implication: "The instrumented analysis and its root-cause narrative are grounded in the same artifacts the reviewer inspected, not a synthetic or hypothetical scenario -- the wrong-lock mechanism identified above is confirmed as the direct, reproducible source of exactly the numbers in the UAT gap report."

## Resolution

root_cause: |
  01-05-PLAN.md's continuity-tracking fix for G-01-2 replaced halfmax_edges' original
  "always pick the single largest above-half-max-threshold run, independently per column"
  rule with "pick whichever non-clipped candidate run's midpoint is numerically nearest to
  previous_center, when tracking history exists." This selection rule has two structural
  gaps that together explain the residual (G-01-5) fragmentation:

  1. No maximum-distance gate. The nearest-candidate rule always returns SOME candidate,
     however far away it is from previous_center -- there is no threshold beyond which a
     column is instead invalidated as "no plausible candidate nearby." Length/size is only
     consulted as an exact-float-tie tiebreak (`-(run[1]-run[0])` in the sort key), which in
     practice never fires because two real-valued midpoint distances essentially never tie
     exactly. A 1-native-pixel noise spike and a 300-native-pixel true bead run are therefore
     treated as equally legitimate candidates, decided purely by whichever midpoint is
     marginally closer to history -- confirmed directly: on Track 14, 34.3% of all
     continuity-tracked column selections, and on Track 21, 43.1%, chose a candidate under
     40% of the largest same-column candidate's length despite that larger, bead-plausible
     candidate being available in the identical column (Track 8: 5.7%, Track 10: 7.1%).

  2. Unconditional anchor update creates a NEW, self-reinforcing failure mode. Because
     `extract_targets_from_arrays` (src/targets.py:277-283) overwrites `previous_center`
     with the midpoint of whatever run was just selected -- correct or wrong -- with no
     plausibility check, a single spurious column (where the true bead's above-threshold
     run either fragments into several small sub-runs due to a local noise dip, per
     RESEARCH.md Finding 4's already-documented signal/noise-margin overlap, or briefly
     fails to clear threshold as one contiguous run at all) corrupts the anchor. Every
     subsequent column then keeps preferring nearby small/spurious candidates over the true
     (wider, but now more-distant-from-the-corrupted-anchor) bead candidate, even when that
     true candidate is present in the very same columns. This produces a MULTI-COLUMN
     persistent wrong lock -- directly traced on Track 8 (x=24.9-26.5mm, an 8-column/1.4mm
     episode) and, more severely and more often, on Track 10 (a near-continuous narrow lock
     from x~68mm through beyond x~82mm, interrupted only by real data gaps and occasional
     forced recoveries) -- rather than the bounded, single-column-independent flip the
     pre-fix algorithm exhibited. This is qualitatively different from, and can be locally
     more persistent than, the original G-01-2 defect: errors now propagate forward through
     state rather than resetting every column.

  Track 10's especially severe fragmentation (65 disconnected valid runs; mean tracked
  width collapsing from 0.4268mm before x=70mm to 0.0712mm after x=70mm, a ~6x drop) is the
  SAME mechanism as the other three tracks, triggered far more often: Track 10 independently
  has the highest genuine native-column-gap rate (112/400 columns fail the existing
  MAX_GAP_PIXELS check, concentrated later in the track, vs. 25-79 on tracks 8/14/21) AND,
  in the x>70mm region specifically, frequent above-threshold-run fragmentation, giving the
  wrong-lock mechanism many more trigger opportunities with comparatively few
  forced-recovery columns to break it. MAX_TRACKING_GAP_COLUMNS=10 resets (which discard a
  stale anchor entirely) were directly measured to be rare (0-1 per track) and are NOT the
  dominant residual mechanism -- that hypothesis was tested and eliminated.

  Reproduced directly against the real, current (post-01-05, post-Amendment-A5) artifacts:
  finalized valid_mask contiguous-run counts of 22/65/63/34 for tracks 8/10/14/21 (Track
  10's 65 is an exact match to the reviewer's report) and finalized max adjacent-column
  jumps of 0.32-0.88mm across the four tracks (matching the reviewer's reported
  ~0.62-0.88mm range) -- confirming this mechanism is the direct, reproducible source of
  the G-01-5 gap, not a hypothetical.
fix: []
verification: []
files_changed: []
