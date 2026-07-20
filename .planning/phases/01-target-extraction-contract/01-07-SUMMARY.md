---
phase: 01-target-extraction-contract
plan: 07
subsystem: data-processing
tags: [profilometry, detrending, provenance, bead-masking, numpy, tdd]

requires:
  - phase: 01-target-extraction-contract
    provides: quartic-order detrending (Amendment A3), boundary continuity tracking (plan 01-05), and the pre-registered residual/physical fix-selection criterion (01-06-DIAGNOSIS.md)
provides:
  - A fit_mask keyword on robust_plane_detrend() that excludes flagged pixels from the least-squares fit while still subtracting the fitted surface from every pixel
  - targets.bead_exclusion_mask(): one shared, per-column baseline/peak-relative rule excluding elevated bead-corridor pixels from the detrend fit
  - extract_track_targets() wired to compute and apply the bead mask identically for all four tracks
  - A complete, change-sensitive extraction_params() (15 keys: MAX_TRACKING_GAP_COLUMNS and BEAD_MASK_HEIGHT_FRACTION added)
  - Amendment A4 in 01-CONTEXT.md canonicalizing the continuity/stale-history rule and the Gap-2 bead-mask fix
affects: [target-extraction, dataset-alignment, model-training, submission-qa]

tech-stack:
  added: []
  patterns: [least-squares fit-mask exclusion with full-resolution surface subtraction, baseline/peak-relative per-column masking rule reusing D-01/D-02's percentile convention, change-sensitive provenance digest]

key-files:
  created: []
  modified: [src/nsf_fmrg_data.py, src/targets.py, tests/test_nsf_fmrg_data.py, tests/test_targets.py, .planning/phases/01-target-extraction-contract/01-CONTEXT.md]

key-decisions:
  - "Implemented the endorsed leading remedy from 01-06-DIAGNOSIS.md Section 3: mask the bead region before fitting the order-4 detrend surface, rather than either fallback (continuity-mechanism fix or a lower shared order)."
  - "Fixed BEAD_MASK_HEIGHT_FRACTION at the already-locked HALF_MAX_FRACTION (0.5): a pixel this contract already classifies as bead by the D-01/D-03 half-max convention is, by that same definition, not background."
  - "extraction_params() gains exactly two new keys (MAX_TRACKING_GAP_COLUMNS, BEAD_MASK_HEIGHT_FRACTION), reaching 15 total; no redundant/fabricated constant was added."
  - "Canonicalized both the plan-01-05 continuity/stale-history rule and this plan's Gap-2 fix as a single Amendment A4, matching Amendment A3's style, superseding nothing in A3."

patterns-established:
  - "Detrend fit-masking: a full-resolution boolean mask ANDs into the strided least-squares valid set (and its iterative percentile trimming) while the fitted surface is still subtracted from every pixel, unmasked or masked."
  - "Provenance completeness discipline: every behavior-changing constant a fix introduces or depends on must be added to extraction_params() and covered by an explicit change-sensitivity regression in the same plan that introduces it."

requirements-completed: [TARGET-01, TARGET-02]

coverage:
  - id: D1
    description: "robust_plane_detrend() accepts a fit_mask keyword that excludes flagged pixels from the fit while still subtracting the fitted surface from all pixels; default None preserves existing behavior."
    requirement: TARGET-01
    verification:
      - kind: unit
        ref: "tests/test_nsf_fmrg_data.py#test_robust_plane_detrend_fit_mask_excludes_bead_from_fit"
        status: pass
      - kind: unit
        ref: "tests/test_nsf_fmrg_data.py#test_default_order_removes_affine_surface (regression: default fit_mask=None unaffected)"
        status: pass
    human_judgment: false
  - id: D2
    description: "The masking rule is track-independent: one BEAD_MASK_HEIGHT_FRACTION excludes bead corridors of differing absolute height, and no per-track branch exists in src/targets.py."
    requirement: TARGET-02
    verification:
      - kind: unit
        ref: "tests/test_targets.py#test_bead_mask_rule_is_track_independent"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_single_parameterization_has_no_track_conditionals"
        status: pass
    human_judgment: false
  - id: D3
    description: "extraction_params() is complete (15 keys including MAX_TRACKING_GAP_COLUMNS and BEAD_MASK_HEIGHT_FRACTION) and its SHA-256 provenance digest is change-sensitive to both."
    requirement: TARGET-01
    verification:
      - kind: unit
        ref: "tests/test_targets.py#test_extraction_params_provenance"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_provenance_includes_tracking_gap_and_fix_param"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py#test_provenance_digest_is_change_sensitive"
        status: pass
    human_judgment: false
  - id: D4
    description: "Amendment A4 canonicalizes the continuity/stale-history rule and the Gap-2 bead-mask fix in 01-CONTEXT.md, reaffirming the no-outcome-driven-per-track-tuning prohibition."
    requirement: TARGET-01
    verification:
      - kind: manual_procedural
        ref: ".planning/phases/01-target-extraction-contract/01-CONTEXT.md Amendment A4 section"
        status: pass
    human_judgment: true
    rationale: "Confirming Amendment A4 faithfully documents the prior plan's implemented mechanism and this plan's fix without silently reframing either requires editorial/scientific judgment, not just a passing command."

duration: 10min
completed: 2026-07-20
status: complete
---

# Phase 01 Plan 07: Bead-Mask Detrend Fix and Complete Provenance Summary

**One uniform, track-independent bead-region mask now excludes elevated bead pixels from the order-4 detrend surface fit (chosen by 01-06's pre-registered residual/physical criterion), and extraction_params() is now complete and change-sensitive to both MAX_TRACKING_GAP_COLUMNS and the new BEAD_MASK_HEIGHT_FRACTION.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-07-20T21:24:00Z (approx.)
- **Completed:** 2026-07-20T21:34:00Z (approx.)
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Added a `fit_mask` keyword to `robust_plane_detrend()` (`src/nsf_fmrg_data.py`): flagged pixels are ANDed out of the strided least-squares valid set and its iterative percentile-trim loop, while the fitted surface is still subtracted from the full-resolution map. Default `None` preserves every existing caller (affine `order=1` path, notebooks) exactly.
- Added `bead_exclusion_mask(Z_mm)` (`src/targets.py`): one shared, per-column baseline/peak-relative rule mirroring D-01/D-02's `BASELINE_PCT`/`PEAK_PCT` convention — a pixel is excluded only if it exceeds `baseline + BEAD_MASK_HEIGHT_FRACTION * (peak - baseline)` for its own column, so the same fraction works across tracks of differing absolute bead height.
- Fixed `BEAD_MASK_HEIGHT_FRACTION = HALF_MAX_FRACTION` (0.5), grounded directly in the already-locked D-01/D-03 half-max width convention, not in the resulting ordering.
- Wired `extract_track_targets()` to compute `bead_exclusion_mask(data['Z_mm'])` and pass it as `fit_mask` into the shared `DETREND_POLY_ORDER=4` detrend call, identically for all four tracks. `grep` confirms no per-track numeric branch exists in `src/targets.py`.
- Proved the fix mechanism with a named synthetic regression (`test_robust_plane_detrend_fit_mask_excludes_bead_from_fit`): an unmasked order-4 fit on a quartic-bow background plus an along-track bead corridor suppresses/inverts the bead's true height (ratio ≈ -0.10), while the masked fit recovers it almost exactly (ratio ≈ 1.00).
- Proved the rule is track-independent (`test_bead_mask_rule_is_track_independent`): the same `BEAD_MASK_HEIGHT_FRACTION` fully excludes bead corridors at both a low (0.02 mm) and a high (0.2 mm) absolute bead height, and leaves all background pixels included in both cases.
- Completed `extraction_params()` provenance: added `MAX_TRACKING_GAP_COLUMNS` (introduced in plan 01-05, previously missing) and `BEAD_MASK_HEIGHT_FRACTION` (15 keys total), and proved the SHA-256 digest changes when either constant is mutated (`test_provenance_digest_is_change_sensitive`).
- Canonicalized the plan-01-05 continuity/stale-history tracking rule and this plan's Gap-2 fix as Amendment A4 in `01-CONTEXT.md`, matching Amendment A3's style and reaffirming the no-outcome-driven-per-track-tuning prohibition.

## Task Commits

Each task was committed atomically (Task 1 and Task 2's GREEN implementations were combined into one commit — see Deviations):

1. **Task 1 RED + Task 2 RED: add failing/target-state regressions** - `6d7cf25` (test)
2. **Task 1 GREEN + Task 2 GREEN: implement bead-mask fix and complete provenance** - `a83a4d9` (feat)
3. **Task 3: record Amendment A4** - `2f5f800` (docs)

## Files Created/Modified

- `src/nsf_fmrg_data.py` - `robust_plane_detrend()` gains a `fit_mask` keyword; strided mask ANDs into the fit's `valid` set, fitted surface still subtracted from the full-resolution array.
- `src/targets.py` - New `BEAD_MASK_HEIGHT_FRACTION` constant and `bead_exclusion_mask()` helper; `extract_track_targets()` wired to compute and pass the mask; `extraction_params()` gains `MAX_TRACKING_GAP_COLUMNS` and `BEAD_MASK_HEIGHT_FRACTION`.
- `tests/test_nsf_fmrg_data.py` - `test_robust_plane_detrend_fit_mask_excludes_bead_from_fit`.
- `tests/test_targets.py` - `test_bead_mask_rule_is_track_independent`, updated `test_extraction_params_provenance` (15-key expected dict, corrected wording), `test_provenance_includes_tracking_gap_and_fix_param`, `test_provenance_digest_is_change_sensitive`.
- `.planning/phases/01-target-extraction-contract/01-CONTEXT.md` - Amendment A4 appended after Amendment A3.

## Decisions Made

- Implemented the bead-mask remedy exactly as endorsed by 01-06-DIAGNOSIS.md Section 3 rather than either fallback (continuity-mechanism fix or a lower shared detrend order); no sweep evidence was sought for the mask axis, per the diagnosis's explicit scope note.
- Grounded `BEAD_MASK_HEIGHT_FRACTION` in the already-locked `HALF_MAX_FRACTION` (0.5) rather than deriving a new arbitrary value, since it is the most direct, non-arbitrary choice consistent with the width-extraction contract's own definition of "bead."
- Did not add a redundant new constant beyond what the fix actually depends on — `extraction_params()` grew by exactly 2 keys (13 → 15), matching the plan's must-have.
- Chose to combine Task 1's and Task 2's GREEN implementations into a single commit: the RED test commit already included the updated `test_extraction_params_provenance` (15-key expectation) alongside Task 1's synthetic regressions, so Task 1's own `<verify>` block (`.venv/bin/python tests/test_targets.py` must pass in full) could only pass once Task 2's `extraction_params()` keys also existed. Splitting them would have produced an intermediate commit that fails its own task's stated verification.

## Deviations from Plan

**1. [Process, not Rule 1-4] Task 1 and Task 2 GREEN implementations share one commit**
- **Found during:** Preparing to commit Task 1
- **Issue:** The plan describes Task 1 and Task 2 as separate atomic commits, but Task 1's `<verify>` block requires the full `tests/test_targets.py` suite to pass, and that suite (committed as one RED unit, matching how the two tasks' tests were authored together) already includes Task 2's updated `test_extraction_params_provenance` expecting the final 15-key dict. Committing Task 1's source changes alone would leave that test failing, violating the "commit only after verification passes" rule.
- **Resolution:** Committed Task 1's and Task 2's source implementation together as a single `feat` commit (`a83a4d9`), immediately after the combined `test` commit (`6d7cf25`). No functional content differs from what the plan specifies; only the commit granularity for these two closely-coupled tasks was adjusted. Task 3 (Amendment A4) remains its own separate commit as planned.
- **Files affected:** `src/nsf_fmrg_data.py`, `src/targets.py` (commit `a83a4d9`).
- **Verification:** Full test suite (`tests/test_nsf_fmrg_data.py`, `tests/test_targets.py`, `tests/test_run_target_extraction.py`) passes normally and under `python -O` after both commits.

No other deviations — the fix mechanism, its parameter, and Amendment A4's content follow the plan and the 01-06 pre-registered criterion exactly.

## Issues Encountered

- Initial synthetic bead regression used a narrow bead corridor (10% of the y-range) and showed only modest (~12%) suppression under the unmasked order-4 fit — not a convincing demonstration of the diagnosed mechanism. Widened the bead corridor to 40% of the y-range and increased its along-track amplitude variation, which reproduced the diagnosed effect clearly (unmasked fit inverts the bead height to roughly -10% of true; masked fit recovers ~100% of true). This tuning affected only the synthetic test fixture's parameters, not the production `BEAD_MASK_HEIGHT_FRACTION` or any other locked contract constant.

## Known Stubs

None. All new code paths (`fit_mask`, `bead_exclusion_mask`) are fully wired into the production `extract_track_targets()` path, not placeholder scaffolding.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-08 can now regenerate the four-track artifacts (`processed_data/targets/*.npz`, `extraction_params.json`, `manifest.json`, QA figures) using this plan's uniform, provenance-complete extraction path and report the resulting `8 > 10 > 14 > 21` ordering as an honest outcome, per 01-06-DIAGNOSIS.md's explicit scope note.
- `extraction_params()` is now the complete, machine-readable, change-sensitive current contract (15 keys); plan 01-08's regenerated `extraction_params.json` and manifest digest will reflect both `MAX_TRACKING_GAP_COLUMNS` and `BEAD_MASK_HEIGHT_FRACTION`, closing the Gap 1 provenance finding from `01-VERIFICATION.md`.
- The bead-mask fix's efficacy is proven only by the synthetic regression in this plan, per 01-06-DIAGNOSIS.md Section 4's explicit scope note — plan 01-08's real-data regeneration is the first place the fix's effect on the actual 8/10/14/21 ordering becomes observable, and that outcome must be reported honestly without further tuning.

## Self-Check: PASSED

- `src/nsf_fmrg_data.py`, `src/targets.py`, `tests/test_nsf_fmrg_data.py`, `tests/test_targets.py`, `.planning/phases/01-target-extraction-contract/01-CONTEXT.md` all exist and contain the described changes.
- Commits `6d7cf25`, `a83a4d9`, `2f5f800` exist in `git log`.
- `.venv/bin/python tests/test_nsf_fmrg_data.py` reports 5/5 PASS; `.venv/bin/python tests/test_targets.py` reports 26/26 PASS; both also pass under `python -O`.
- `.venv/bin/python tests/test_run_target_extraction.py` (unmodified by this plan) still reports 7/7 PASS.
- `extraction_params()` contains `MAX_TRACKING_GAP_COLUMNS` and `BEAD_MASK_HEIGHT_FRACTION`; mutating either changes the SHA-256 provenance digest (verified both via the plan's inline verify command and the new named regression).
- `grep` finds no `track_id ==` numeric branch in `src/targets.py`.
- `01-CONTEXT.md` contains an "Amendment A4" heading documenting `MAX_TRACKING_GAP_COLUMNS`, continuity/stale-history behavior, and the bead-mask fix.

---
*Phase: 01-target-extraction-contract*
*Completed: 2026-07-20*
