---
phase: 01-target-extraction-contract
plan: 15
subsystem: docs / phase-1 sign-off gate
tags: [gap-closure, documentation, sign-off, target-extraction]
dependency-graph:
  requires: ["01-13", "01-14"]
  provides: ["01-SIGNOFF-REQUEST.md (Amendment-A7-accurate)", "REQUIREMENTS.md TARGET-02 checkbox/traceability agreement"]
  affects: ["Phase 1 human sign-off round (/gsd-verify-work 1)", "REQUIREMENTS.md", "ROADMAP.md phase-1 status"]
tech-stack:
  added: []
  patterns: ["Live re-derivation of every quoted number from a fresh check_targets.py run + manifest.json read, never transcribed from planning text"]
key-files:
  created:
    - .planning/phases/01-target-extraction-contract/01-15-SUMMARY.md
  modified:
    - .planning/phases/01-target-extraction-contract/01-SIGNOFF-REQUEST.md
    - .planning/REQUIREMENTS.md
decisions:
  - "Re-derived every figure in 01-SIGNOFF-REQUEST.md from a live check_targets.py run and manifest.json read during this execution; every value matched the plan's stated figures exactly, so no live-vs-plan disagreement was recorded."
  - "Regenerated 01-SIGNOFF-REQUEST.md's 'Current state' to carry the razor-thin 50.50% track-10 coverage margin, the doubled 0.2404mm 10-vs-14 gap, and the MIXED fragmentation outcome, replacing every Amendment-A5-era figure."
  - "Expanded 'Contract in effect' from 4 to 7 rows, adding DETREND_MAX_XY_DEGREE (A6), MAX_RUN_MERGE_GAP_PIXELS and MIN_TRACKED_LENGTH_RATIO (A7)."
  - "Each of the 5 decision checkboxes now names which of 01-VERIFICATION.md's two open human_verification items it closes; all remain unticked."
  - "Flipped REQUIREMENTS.md's TARGET-02 checkbox from [x] to [ ] to agree with its own traceability row; TARGET-01 left untouched."
metrics:
  duration: "~6 min"
  completed: 2026-07-22
status: complete
---

# Phase 01 Plan 15: Regenerate stale 01-SIGNOFF-REQUEST.md against live Amendment-A7 run — Summary

Regenerated the standing human sign-off document against the live, checked-in Amendment-A7 artifact generation (every number re-derived from a fresh `check_targets.py` run and `manifest.json` read performed in this execution, not transcribed from planning text) and reconciled `REQUIREMENTS.md`'s TARGET-02 checkbox with its own traceability row — no source, test, constant, or pipeline artifact was touched.

## What Was Built

**Task 1 — Re-derived live A7 numbers into "## Current state":**
Ran `.venv/bin/python scripts/check_targets.py --project_dir .` live (exit 0, `ALL CHECKS PASSED`) and read `processed_data/targets/manifest.json` live. Rewrote the document's header (requested 2026-07-22, plan 01-15) and the entire "## Current state" section: the Amendment-A7 contract description, `run_id` `99a4e8472f0a4164938363af0725f31b` and `extraction_params_sha256` `773a25a388dae2954495e4b6f67b2a8c1c7664de01bbb56c005a8bc0e3051c08`, the verbatim checker output (361/202/301/308 valid bins; medians 0.7401/0.3770/0.6174/0.3825 mm), the coverage table (90.25%/50.50%/75.25%/77.00%), the razor-thin 50.50%-margin paragraph, and five rewritten plain-language bullets stating the doubled 0.2404mm gap (from 0.1052mm), the non-closed track-10 coverage narrative, and the MIXED fragmentation outcome (worsened contiguous-run counts on tracks 8/10/21, mixed jump-statistic direction).

**Task 2 — Refreshed contract table, figure questions, and decision set for A7:**
Expanded "## Contract in effect" from 4 to 7 rows, adding `DETREND_MAX_XY_DEGREE` (Amendment A6), `MAX_RUN_MERGE_GAP_PIXELS`, and `MIN_TRACKED_LENGTH_RATIO` (both Amendment A7, both reused from already-locked constants per `01-CONTEXT.md`). Rewrote the "## Figures to inspect" intro to state up front that gap handling is correct but fragmentation/jump metrics did not uniformly improve, and refreshed all three figure subsections' questions with the A6/A7-specific observations from `01-14-ORDERING-OUTCOME.md`. Rewrote "## Decisions requested" so each of the 5 unticked checkboxes names which of `01-VERIFICATION.md`'s two open `human_verification` items it closes, with the fifth checkbox surfacing the 0.2404mm gap and both outcome reports' shared option-(a) recommendation immediately next to each other while selecting neither option. Updated "## How to record the outcome" to name `/gsd-verify-work 1` explicitly, and "## Closing note" to list all seven locked constants.

**Task 3 — Reconciled REQUIREMENTS.md's TARGET-02 checkbox:**
Flipped `- [x] **TARGET-02**` to `- [ ] **TARGET-02**` (line ~13) via scoped `Edit` calls (no whole-file rewrite), so the checkbox agrees with its own Traceability row, which already correctly read "Awaiting human visual sign-off on regenerated QA figures". Added a dated 2026-07-22 correction line beneath the Traceability table, citing `01-VERIFICATION.md`'s Anti-Patterns finding as the basis, without deleting or modifying the pre-existing 2026-07-21 correction note. `TARGET-01`'s checkbox and traceability row (`[x]` / `Complete`) were left untouched. Coverage counts (12 v1 requirements, 12/12 mapped, 0 unmapped) unchanged.

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written; every live-derived number matched the figures the plan's text stated in advance (no live-vs-plan disagreement to record per assumption 7).

### Notable non-blocking observation (not a deviation caused by this plan)

A pre-existing untracked file, `processed_data/diagnostics/width_regression_sweep.csv`, was already present in the working tree before this plan's execution began (confirmed via `git log` showing no commit touches it, and its file timestamp of 2026-07-21 12:15, predating every task in this plan). It is diagnostic output from `scripts/diagnose_width_regression.py`, unrelated to the extraction pipeline or to any file this plan modifies. `git diff --stat -- src tests scripts processed_data data/raw` is empty (no tracked file under those paths changed), confirming this plan touched no source, test, script, or published artifact. This file is left as-is — untouched, not committed, not deleted — since disposing of it is out of this plan's scope (its only authorized writes are `01-SIGNOFF-REQUEST.md` and `REQUIREMENTS.md`).

## Verification

- `.venv/bin/python scripts/check_targets.py --project_dir .` was run three separate times during this execution (once per task boundary) and exited 0 printing `ALL CHECKS PASSED` every time — identical output each run, confirming no extraction constant or artifact was touched.
- `01-SIGNOFF-REQUEST.md` contains `361`, `202`, `301`, `308`; `90.25%`, `50.50%`, `75.25%`, `77.00%`; `99a4e8472f0a4164938363af0725f31b`; `773a25a388dae2954495e4b6f67b2a8c1c7664de01bbb56c005a8bc0e3051c08`; `0.2404` and `doubled`; `0.1052`; `razor-thin`; `MIXED`. Every Amendment-A5-era literal (`0.3713`, `0.4765`, `0.7528`, `0.1998`, `0.7370`, `0.3234`, `0.4246`, `0.2579`, `60.5%`, `91.0%`, `81.3%`, `75.0%`) is absent — verified by `grep -c -F` returning 0.
- `01-SIGNOFF-REQUEST.md` contains all 7 constant names and `/gsd-verify-work 1`. `grep -c -F 'processed_data/targets/qa/track_'` returns 12. `grep -c -F '[x]'` returns 0. `grep -cE '^- \[ \] \*\*'` returns exactly 5.
- `.planning/REQUIREMENTS.md` shows `- [ ] **TARGET-02**` and `- [x] **TARGET-01**`; the TARGET-02 traceability row still reads "awaiting human visual sign-off" and references `01-SIGNOFF-REQUEST.md`; the TARGET-01 row still reads `Complete`; both the 2026-07-21 and new 2026-07-22 correction notes are present; coverage still reports `12/12`.
- `git diff --stat -- src tests scripts processed_data data/raw` is empty across all three task commits — no source, test, script, or published artifact was modified by this plan.

## Known Stubs

None.

## Threat Flags

None — this round introduced no new network endpoint, auth path, file access pattern, or schema change. All writes are within `.planning/`, matching the threat model's stated scope.

## Self-Check: PASSED

- FOUND: `.planning/phases/01-target-extraction-contract/01-SIGNOFF-REQUEST.md`
- FOUND: `.planning/REQUIREMENTS.md`
- FOUND: `.planning/phases/01-target-extraction-contract/01-15-SUMMARY.md`
- FOUND commit `0934ef1` (Task 1: re-derive live A7 numbers)
- FOUND commit `511bbd0` (Task 2: refresh contract/figures/decisions)
- FOUND commit `7651ccf` (Task 3: reconcile REQUIREMENTS.md)
