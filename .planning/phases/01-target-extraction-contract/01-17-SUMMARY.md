---
phase: 01-target-extraction-contract
plan: 17
subsystem: docs/human-sign-off
tags: [gap-closure, sign-off-regeneration, amendment-a8, target-extraction]
dependency-graph:
  requires: ["01-16"]
  provides: ["01-SIGNOFF-REQUEST.md (Amendment A8, live)"]
  affects: ["01-18"]
tech-stack:
  added: []
  patterns: ["live-derive-then-write (no transcription from plan text)"]
key-files:
  created:
    - .planning/phases/01-target-extraction-contract/01-17-SUMMARY.md
  modified:
    - .planning/phases/01-target-extraction-contract/01-SIGNOFF-REQUEST.md
decisions:
  - "Re-derived every number in 01-SIGNOFF-REQUEST.md from a live check_targets.py run and a live manifest.json read in this execution, never transcribed from this plan or from 01-16-ORDERING-OUTCOME.md's quoted blocks."
  - "Stated plainly that the 10-vs-14 gap widened to 0.3182mm (from 0.2404mm) and that extraction_params_sha256 is unchanged across A7->A8 because Amendment A8 introduced no new named constant -- run_id, not the digest, identifies the current generation."
  - "Preserved the existing human-recorded width-ordering override (2026-07-22, option (a), SELECTED) verbatim; added one new unticked reaffirmation item rather than re-asking or re-ticking the original decision."
metrics:
  duration: "~12 min"
  completed: 2026-07-23
status: complete
---

# Phase 1 Plan 17: Regenerate 01-SIGNOFF-REQUEST.md against live Amendment A8 artifacts Summary

Regenerated `.planning/phases/01-target-extraction-contract/01-SIGNOFF-REQUEST.md` end-to-end against the artifact generation Amendment A8 actually produced (plan 01-16), replacing every stale Amendment-A7 number, identifier, and narrative claim with values re-derived live in this execution from `scripts/check_targets.py` and `processed_data/targets/manifest.json` -- closing the single blocking gap `01-VERIFICATION.md` recorded for Phase 1 and making a fresh `/gsd-verify-work 1` visual sign-off round possible and unambiguous.

## What Was Built

**Task 1 -- live re-derivation of `## Current state`:** Ran `.venv/bin/python scripts/check_targets.py --project_dir .` once (exit 0, `ALL CHECKS PASSED`) and read `processed_data/targets/manifest.json` live in this execution. Rewrote the document's header (requested date, requester line naming plan 01-17 as the gap-closure regeneration of the plan 01-15 original) and the entire `## Current state` section:
- Live artifact identity: `run_id b3f79f207cc1431fa238bb153c04419b`, published `2026-07-23T02:43:48.290492+00:00`, `extraction_params_sha256 773a25a388dae2954495e4b6f67b2a8c1c7664de01bbb56c005a8bc0e3051c08` -- the only 32-hex and 64-hex tokens anywhere in the document, each byte-identical to the manifest.
- A sentence disclosing that the sha256 is unchanged from the prior (Amendment A7) generation's digest because Amendment A8 introduced no new named constant, so a matching digest is not evidence of currency -- `run_id` is the field that identifies the generation.
- The live checker's stdout reproduced verbatim as its own fenced block, every non-empty line (results header, all four per-track rows, all three ordering verdicts, the FLAG-outcomes sentence, `ALL CHECKS PASSED`) present as its own full line in the document.
- The coverage table rebuilt from live valid-bin counts (368/232/309/338 for tracks 8/10/14/21) with each track's count and fraction co-located on its own row (92.00% / 58.00% / 77.25% / 84.50%), and an honest statement that track 10's margin *improved* from the prior generation's razor-thin 50.50% to a materially more comfortable 58.00% -- reported at its live, better value rather than kept pessimistic for continuity.
- Plain-language bullets stating the live 10-vs-14 gap (0.3182mm, widened from 0.2404mm, never described as narrowing), the mixed (not uniform) fragmentation/jump-statistic outcome from `01-16-ORDERING-OUTCOME.md`, and Mechanism C's undiminished residual far-edge jitter.

**Task 2 -- Contract table, figure questions, and decision set:** Added two `## Contract in effect` rows for Amendment A8's clip-before-merge reordering and history-based joint far-AND-small gate, each explicitly stating it introduces no new named constant, alongside the seven previously-locked constants (table now spans Amendments A3 through A8). Rewrote the `## Figures to inspect` intro and all three subsections' per-track observations against `01-16-ORDERING-OUTCOME.md`'s measured fragmentation, jump-statistic, and crop-edge findings, framing the reviewer's task as judging residual jitter acceptability rather than confirming A8 fixed it. In `## Decisions requested`: kept the four visual/constants items (retargeted to close `01-VERIFICATION.md`'s Human Verification item 1, the visual-sign-off round), preserved the existing ticked width-ordering override record verbatim (original 2026-07-22 date, `SELECTED`, option (a) rationale text unchanged) while refreshing only its "Current position" numbers and adding one sentence noting the magnitude moved, and added one new unticked reaffirmation item (closing Human Verification item 2) asking the reviewer to confirm -- not re-decide -- the acceptance at the widened magnitude. Updated `## How to record the outcome` and `## Closing note` to name plan 01-17 and cover Amendments A3 through A8.

## Deviations from Plan

None -- plan executed exactly as written. The plan's own assumption 10 ("live artifacts outrank this plan's text") did not need to be invoked: the live `check_targets.py` output and `manifest.json` values matched exactly what `01-16-ORDERING-OUTCOME.md` and `01-VERIFICATION.md` had already reported for the Amendment A8 generation (run_id `b3f79f207cc1431fa238bb153c04419b`; 368/232/309/338 valid bins; medians 0.7653/0.3940/0.7122/0.6308mm; 0.3182mm 10-vs-14 gap). No disagreement between this execution's live run and the plan's narrative was found or needed reconciling.

## Auth Gates

None encountered.

## Known Stubs

None. This plan produces no code and touches no data path; the regenerated document's only content is text and table rows derived from live command output and a live JSON read.

## Verification

- `.venv/bin/python scripts/check_targets.py --project_dir .` was run live during Task 1: exit 0, `ALL CHECKS PASSED`; every non-empty stdout line confirmed present verbatim as its own line in `01-SIGNOFF-REQUEST.md` via the `grep -qxF` loop specified in the plan's `<verify>`.
- `grep -oE '\b[0-9a-f]{32}\b' 01-SIGNOFF-REQUEST.md | sort -u` produces exactly `b3f79f207cc1431fa238bb153c04419b`, matching `manifest.json`'s live `run_id`.
- `grep -oE '\b[0-9a-f]{64}\b' 01-SIGNOFF-REQUEST.md | sort -u` produces exactly `773a25a388dae2954495e4b6f67b2a8c1c7664de01bbb56c005a8bc0e3051c08`, matching `manifest.json`'s live `extraction_params_sha256`.
- Coverage rows co-located per track (track 8/10/14/21 -> 368/92.00%, 232/58.00%, 309/77.25%, 338/84.50%) via the plan's awk-driven verify loop.
- Live 10-vs-14 gap `0.3182` present in the document; `widened` present; a digest/`unchanged` line present.
- `Amendment A8` present; `grep -c -F 'Amendment A7 on top of' 01-SIGNOFF-REQUEST.md` returns 0.
- `01-SIGNOFF-REQUEST.md` contains `merge_adjacent_runs`, `previous_center`, `previous_length_mm`, and all seven locked constant names; Contract-in-effect table has 9 data rows.
- Every `.png` under `processed_data/targets/qa/` is referenced by path (12 present); `grep -cE '^- \[ \] \*\*'` returns exactly 5; `grep -cE '^- \[x\] \*\*'` returns exactly 1; the single ticked line names the width-ordering override; `2026-07-22` still present.
- `.planning/REQUIREMENTS.md` unchanged and still shows `- [ ] **TARGET-02**`.
- `git status --porcelain --untracked-files=no src tests scripts processed_data data/raw` empty for both tasks and at plan close -- no source, test, script, artifact, or raw-data file was touched.

## Self-Check: PASSED

- FOUND: `.planning/phases/01-target-extraction-contract/01-SIGNOFF-REQUEST.md`
- FOUND: `.planning/phases/01-target-extraction-contract/01-17-SUMMARY.md`
- FOUND: commit `e546f4b` (Task 1)
- FOUND: commit `d3c460e` (Task 2)

## Next Steps

- A fresh `/gsd-verify-work 1` round against the regenerated document and the current 12 QA PNGs is the only remaining step to close TARGET-02 and Phase 1's blocking gap -- not an executor task by design.
- Plan 01-18 (already staged) handles the remaining non-visual gap-closure items: COVERAGE.md reasoned no-external-API declaration, `scripts/diagnose_track10_coverage.py`'s in-file historical-baseline disclaimer, and annotating (not flipping) `01-UAT.md`'s G-01-6 status.
