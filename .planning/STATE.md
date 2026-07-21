---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Completed 01-12-PLAN.md
last_updated: "2026-07-21T17:07:38.983Z"
last_activity: 2026-07-21
progress:
  total_phases: 5
  completed_phases: 0
  total_plans: 12
  completed_plans: 12
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-19)

**Core value:** A thermal-only baseline that runs end-to-end — raw data in, cross-track-validated local-width predictions with calibrated uncertainty out — must work before anything else matters.
**Current focus:** Phase 01 — target-extraction-contract

## Current Position

Phase: 01 (target-extraction-contract) — HUMAN VERIFICATION NEEDED
Plan: 12 of 12 (all plans executed; phase not yet verified complete)
Status: Awaiting human sign-off — run /gsd-verify-work 1 (see 01-SIGNOFF-REQUEST.md, 01-UAT.md tests 5-6)
Last activity: 2026-07-21

Progress: [██████████] 100%

## Performance Metrics

**Velocity:**

- Total plans completed: 0
- Average duration: - min
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01-target-extraction-contract P01 | 16 min | 3 tasks | 2 files |
| Phase 01-target-extraction-contract P02 | 5 min | 2 tasks | 20 files |
| Phase 01-target-extraction-contract P03 | 7 min | 2 tasks | 4 files |
| Phase 01-target-extraction-contract P04 | 4 min | 2 tasks | 5 files |
| Phase 01-target-extraction-contract P05 | 6 min | 2 tasks | 2 files |
| Phase 01 P06 | 7 min | 2 tasks | 2 files |
| Phase 01 P07 | 10 min | 3 tasks | 5 files |
| Phase 01 P08 | 8min | 2 tasks | 1 files |
| Phase 01 P09 | 8min | 3 tasks | 3 files |
| Phase 01 P10 | 12min | 2 tasks | 3 files |
| Phase 01-target-extraction-contract P11 | 45min | 4 tasks | 11 files |
| Phase 01 P12 | 2min | 2 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Thermal-only baseline sequenced strictly before SEM fusion; horizontal-layer phase order (target → alignment → harness → model → packaging), each phase gating the next.
- [Roadmap]: v2 scope (interpretability, robustness ablation, conformal calibration, SEM fusion, boundary target) explicitly deferred out of the initial 5-phase roadmap — see ROADMAP.md Stretch section.
- [Phase 01-target-extraction-contract]: Ratified A1: apply D-05/D-06 to each 0.2 mm binned median profile. — The literal native-column interpretation invalidates essentially every column; within-slot aggregation preserves locality.
- [Phase 01-target-extraction-contract]: Ratified A2: invalidate half-max runs touching either y boundary. — A clipped run leaves the true bead edge and width outside the measured strip.
- [Phase 01-target-extraction-contract]: Locked the shared extraction constants before the official four-track run. — Prevents outcome-contaminated tuning against the expected width ordering.
- [Phase 01-target-extraction-contract]: Official median-width ordering passed for all three pairs; track 10 retains a separate 43.8% valid-fraction QA flag. — Ordering is diagnostic under locked constants; low coverage remains visible for human QA.
- [Phase 01-target-extraction-contract]: Generated target artifacts remain local and reproducible under processed_data/targets/. — Committed runner and checker recreate and validate outputs without adding runtime data to source history.
- [Phase 01-target-extraction-contract]: Revalidate strict upper/lower ordering after separate smoothing and remask invalid slots before width derivation. — The published smoothed boundaries, not only their raw inputs, must satisfy the target contract.
- [Phase 01-target-extraction-contract]: Anchor extraction to the script-derived repository and resolve every concrete output against the canonical root and raw tree. — Caller-controlled roots and existing symlinks cannot be trusted as filesystem safety boundaries.
- [Phase 01-target-extraction-contract]: Preserve clean pipeline exceptions, but let raw deltas or audit unavailability take precedence with causal chaining. — Raw-data integrity evidence must fail closed on every validated pipeline exit.
- [Phase 01-target-extraction-contract]: Accept the residual local TOCTOU window with repeated path resolution and a final digest audit. — The single-user scientific runner does not justify a new filesystem abstraction or dependency.
- [Phase 01-target-extraction-contract]: Amendment A3 fixes DETREND_POLY_ORDER=4 a priori from diagnosed per-track R² evidence and applies it identically to all tracks.
- [Phase 01-target-extraction-contract]: The affine-compatible order=1 default, three-pass percentile trimming, and existing sampling stride remain unchanged for other callers.
- [Phase 01-target-extraction-contract]: Post-fix width-ordering FLAGS are reported without changing any locked extraction constant.
- [Phase 01-target-extraction-contract]: Continuity tracking selects the nearest non-clipped candidate while fresh, then falls back to largest-run selection after ten invalid columns. — Resolves multi-blob ambiguity without per-track tuning and prevents stale anchors from capturing long-gap resumptions.
- [Phase 01-target-extraction-contract]: Three-point smoothing windows use degree finite_count minus two. — Retains at least one residual degree of freedom so sparse windows genuinely damp noise.
- [Phase 01-target-extraction-contract]: The width-ordering regression is caused by DETREND_POLY_ORDER=4, not continuity tracking — verdict flips PASS to FLAG exactly at order=4 under both continuity settings.
- [Phase 01-target-extraction-contract]: Continuity tracking has a real, uniform, order-independent effect that shrinks track 21's magnitude 3-4x, but never by itself flips the ordering verdict.
- [Phase 01-target-extraction-contract]: Pre-registered the fix-selection criterion (residual structure / physical plausibility — the detrend background must not follow the bead) before any fix is chosen or applied, naming bead-masking as the endorsed remedy.
- [Phase 01-target-extraction-contract]: Implemented the plan-06 endorsed bead-region masking of the detrend surface fit (BEAD_MASK_HEIGHT_FRACTION fixed at the already-locked HALF_MAX_FRACTION), completed extraction_params() provenance (MAX_TRACKING_GAP_COLUMNS, BEAD_MASK_HEIGHT_FRACTION, 15 keys), and canonicalized both as Amendment A4.
- [Phase ?]: The 8>10>14>21 width ordering is NOT restored under Amendment A4's corrected extraction (10-vs-14 FLAGs); no extraction parameter was changed, and the outcome is escalated for a separate human-override decision rather than tuned.
- [Phase ?]: Track 10's valid-bin fraction collapsed to 5.2% (21/400) under the bead-mask fix, down from ~43.8% previously — reported as material context for the human decision, not diagnosed/fixed in this plan.
- [Phase ?]: Restructured the width-regression sweep's detrend cache to iterate (order, bead_mask) so it exercises the production bead-masked fit_mask path, not just the historical unmasked baseline.
- [Phase ?]: Relocated the sweep's evidence CSV to processed_data/diagnostics/ (sibling of targets/), outside the tree publish_staging_dir renames and rmtree's.
- [Phase ?]: Removed find_track_file's permissive substring fallback entirely; the delimiter-anchored regex is now the sole candidate filter (WR-01).
- [Phase ?]: Extended the exact-basename fail-fast guard from the height-map loader to the thermal and SEM loaders, including lexical symlink rejection for SEM directories (WR-02).
- [Phase ?]: [Phase 01-target-extraction-contract]: Closed CR-03 by adding reject_symlink_path() (repo-root-bounded ancestor walk) called first in resolve_output_path, plus is_symlink() re-checks immediately before every rmtree/rename in publish_staging_dir.
- [Phase ?]: [Phase 01-target-extraction-contract]: Closed CR-02 by promoting check_targets.py's coverage check to require(valid_fraction >= MIN_VALID_FRACTION = 0.5) — a single project-wide floor with no per-track exemption; check_targets.py now intentionally exits non-zero on track 10's 5.2% valid fraction until plan 01-11 resolves it.
- [Phase ?]: [Phase 01-target-extraction-contract]: Diagnosed track 10's coverage collapse (5.2% valid) as a detrend-fitting artifact — raw argmax is interior, not physically truncated — using a committed re-runnable diagnostic that observes no fix outcome.
- [Phase ?]: [Phase 01-target-extraction-contract]: Pre-registered a 0.05mm fitted-surface edge tolerance and two candidate mechanisms in 01-11-CRITERION.md before any extraction-source change; Candidate A (basis conditioning) was rejected by a priori measurement (mathematically a no-op for a full-rank fit), and the criterion's own fallback selected Candidate B.
- [Phase ?]: [Phase 01-target-extraction-contract]: Implemented Amendment A5 (DETREND_MAX_Y_DEGREE=2), restoring track 10 to 242/400 (60.5%) valid bins and clearing the MIN_VALID_FRACTION floor; the 10-vs-14 width-ordering FLAG remains unresolved and is left for plan 01-12's human sign-off.
- [Phase ?]: [Phase 01-target-extraction-contract]: Corrected REQUIREMENTS.md's TARGET-02 status from a false Complete to an honest awaiting-human-sign-off state, citing 01-VERIFICATION.md and 01-11-ORDERING-OUTCOME.md.
- [Phase ?]: [Phase 01-target-extraction-contract]: Produced 01-SIGNOFF-REQUEST.md naming all 12 regenerated QA figures with per-figure acceptance questions and zero pre-ticked decision checkboxes; sign-off must be recorded via /gsd-verify-work, not self-certified by any plan.

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 1]: No organizer-provided width extractor exists — TARGET-01 contract must be locked and visually validated against all 4 tracks (incl. track 21's incomplete profilometry) before Phase 2 begins.
- [Phase 2]: Track 21's laser on/off thermal-detection heuristic is flagged (research/PITFALLS.md, Pitfall 9) as a plausible, unconfirmed misalignment risk — requires explicit numeric/visual cross-check during Phase 2, since track 21 is also the primary held-out evaluation track.
- [Phase 3]: The LOTO harness must be validated leak-free with a dummy predictor before Phase 4 model training starts — this is a hard, non-negotiable gate per research/ARCHITECTURE.md.
- Restricted raw data is already present in historical commit 831987c; remediate repository history before any external sharing.
- [Phase 1]: 8>10>14>21 width ordering still not restored (10-vs-14 FLAG, 0.3713mm vs 0.4765mm) after Amendment A5 regeneration — track 10's coverage-collapse defect (option b of 01-08-ORDERING-OUTCOME.md's escalation) is now diagnosed and fixed by plan 01-11 (21/400 → 242/400 valid), so Phase 1 verification sign-off is blocked solely on the remaining human decision to override the ordering criterion (option a), per 01-11-ORDERING-OUTCOME.md.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| v2 scope | INSIGHT-01, INSIGHT-02, ROBUST-01, CALIB-01, ABL-01, FUSION-01, FUSION-02, TARGET-03 | Deferred — pursued only if time remains after v1 phases 1-5 complete | Roadmap creation, 2026-07-19 |

## Session Continuity

Last session: 2026-07-21T17:07:38.974Z
Stopped at: Completed 01-12-PLAN.md
Resume file: None
