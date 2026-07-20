---
phase: 01-target-extraction-contract
plan: 03
subsystem: scientific-data
tags: [profilometry, numpy, filesystem-safety, sha256, tdd]

requires:
  - phase: 01-target-extraction-contract
    provides: Locked target-extraction contract, four-track runner, persisted artifacts, and verifier gap report from plans 01-01 and 01-02
provides:
  - Strict post-smoothing boundary-order revalidation with NaN/False remasking
  - Canonical repository, raw-tree, and output-path containment for target extraction
  - Digest-backed raw integrity auditing from finally on successful and failed runs
  - Optimization-safe bounded contract and runner-safety evidence
affects: [dataset-alignment, phase-01-verification, target-provenance, raw-data-safety]

tech-stack:
  added: []
  patterns: [post-transform invariant revalidation, canonical-path containment, finally-path integrity audit, red-green TDD]

key-files:
  created:
    - tests/test_run_target_extraction.py
  modified:
    - src/targets.py
    - tests/test_targets.py
    - scripts/run_target_extraction.py

key-decisions:
  - "Revalidate finite strict upper/lower ordering only after both boundaries have been smoothed separately, then derive width from the remasked arrays."
  - "Trust only a project directory resolving exactly to the script-derived repository anchor; resolve every concrete output against the canonical root and real raw tree."
  - "Let an original pipeline exception propagate unchanged after a clean audit, but give raw mutation or audit unavailability precedence and preserve causal chaining."
  - "Accept the small local TOCTOU window as a documented residual risk while mitigating it with repeated path resolution and a final digest audit."

patterns-established:
  - "Post-smoothing validity: finite upper and lower values plus strict upper > lower define the only publishable slots."
  - "Raw integrity: stable relative path maps to mtime_ns, size, and SHA-256 and is compared from finally on every validated pipeline exit."

requirements-completed: [TARGET-01, TARGET-02]

coverage:
  - id: D1
    description: "Separately smoothed boundaries cannot publish crossed or degenerate slots, and zero valid post-remask output raises a hard error"
    requirement: TARGET-01
    verification:
      - kind: unit
        ref: ".venv/bin/python tests/test_targets.py (14 PASS lines)"
        status: pass
      - kind: unit
        ref: ".venv/bin/python -O tests/test_targets.py (14 PASS lines)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Canonical-root and symlink containment plus success/failure raw audits fail closed in bounded temporary repositories"
    requirement: TARGET-02
    verification:
      - kind: integration
        ref: ".venv/bin/python tests/test_run_target_extraction.py (7 PASS lines)"
        status: pass
      - kind: integration
        ref: ".venv/bin/python -O tests/test_run_target_extraction.py (7 PASS lines)"
        status: pass
    human_judgment: false
  - id: D3
    description: "The complete four-track extraction preserves the real raw tree and retains valid artifacts under the locked shared parameterization"
    requirement: TARGET-02
    verification:
      - kind: integration
        ref: ".venv/bin/python scripts/run_target_extraction.py --project_dir . (data/raw integrity PASS; four tracks complete; three ordering PASS lines)"
        status: pass
      - kind: integration
        ref: ".venv/bin/python scripts/check_targets.py --project_dir . (ALL CHECKS PASSED)"
        status: pass
    human_judgment: false

duration: 7min
completed: 2026-07-19
status: complete
---

# Phase 1 Plan 3: Target Extraction Safety Gap Closure Summary

**Strict post-smoothing target validity and canonical, digest-audited raw-data containment now close both Phase 1 verifier blockers in normal and optimized Python**

## Performance

- **Duration:** 7 min
- **Started:** 2026-07-20T00:30:21Z
- **Completed:** 2026-07-20T00:37:13Z
- **Tasks:** 2 TDD tasks
- **Files created/modified:** 4

## Accomplishments

- Added one post-smoothing finalizer that remasks every non-finite, crossed, or degenerate boundary slot to NaN/False before deriving width and applying the zero-valid hard error.
- Anchored the CLI to the actual script repository and rejected alternate roots, repository escapes, and existing symlink paths entering the resolved raw tree before writes.
- Replaced metadata-only raw snapshots with deterministic `(mtime_ns, size, SHA-256)` evidence and guaranteed the second comparison from `finally` on success and failure.
- Proved root rejection, symlink traversal, add/remove/change classification, clean success/failure, mutation precedence, and audit unavailability under both normal and optimized Python.
- Completed the full four-track rerun with the locked constants, a final raw-integrity PASS, and all three expected width-ordering checks passing.

## Task Commits

Each TDD task used separate RED and GREEN commits:

1. **Task 1 RED: Post-smoothing boundary regressions and optimization-safe contract checks** - `206b279` (test)
2. **Task 1 GREEN: Strict post-smoothing boundary finalization** - `c4c13ac` (feat)
3. **Task 2 RED: Canonical-path and raw-integrity runner regressions** - `f1e85b4` (test)
4. **Task 2 GREEN: Fail-closed extraction runner and finally audit** - `8771323` (feat)

## Files Created/Modified

- `src/targets.py` - Centralizes separate smoothing, strict order revalidation, invalid-slot remasking, width derivation, and zero-valid failure.
- `tests/test_targets.py` - Adds the smoothing-overshoot and post-revalidation empty regressions and keeps all 14 checks active under `python -O`.
- `scripts/run_target_extraction.py` - Adds canonical root/raw/output resolution, SHA-256 snapshots and diffs, checked JSON/NPZ/PNG writes, and finally-path integrity handling.
- `tests/test_run_target_extraction.py` - Uses bounded temporary repositories to exercise seven safety behaviors without writing under the real raw tree.

## Regression Outcomes

- The positive raw separation `[1.0, 0.1, 0.1, 0.1, 1.0]` still independently reproduces a non-positive smoothed center, but finalization now returns NaN upper/lower/width with `valid_mask=False` at that slot.
- A boundary pair with no strict post-smoothing separation raises `ValueError` containing `zero valid` only after final revalidation.
- The existing exact 10/11 gap, exact 0.005 mm separation, masked-gap blending, percentile, crop-edge, shared-grid, float64, and exact 12-constant checks remain green.

## Runner Safety Outcomes

- Passing the real `data/raw` directory as `--project_dir` exits nonzero with a canonical-root mismatch before any nested output appears.
- A temporary `processed_data` symlink into the resolved raw tree is rejected before parameter or track output is written, with an identical before/after snapshot.
- Snapshot diffs deterministically classify added, removed, and same-size content-changed files; the changed case remains detectable after restoring the original mtime because SHA-256 differs.
- Successful and injected-failure runs both execute a second snapshot from `finally`; clean injected failure preserves the original sentinel exception object.
- Raw mutation takes precedence over an active pipeline failure, names the changed path, and chains the original failure; an unavailable final snapshot raises a fail-closed audit error.

## Full Four-Track Verification

| Track | Power (W) | Valid slots | Median width (mm) | Mean width (mm) |
|------:|----------:|------------:|------------------:|----------------:|
| 8 | 400 | 348/400 | 0.8168 | 0.8441 |
| 10 | 350 | 175/400 | 0.7410 | 0.7914 |
| 14 | 300 | 299/400 | 0.6386 | 0.6696 |
| 21 | 200 | 311/400 | 0.6095 | 0.6236 |

The rerun printed `data/raw/ integrity PASS: no files created, modified, or deleted.` and all three median-order comparisons passed. The separate checker then printed `ALL CHECKS PASSED`. Track 10 retains the already documented 43.8% valid-fraction QA flag; no constant or validity rule changed in response.

## Decisions Made

- Kept D-10 separate boundary smoothing unchanged and placed the strict order backstop after it, so invalidity reflects the actual published smoothed values.
- Used script-anchor equality plus repository markers as the root trust boundary; no CLI option can substitute a different repository anchor.
- Used repeated canonical resolution immediately around output directory creation and concrete JSON/NPZ/PNG writes, followed by whole-raw-tree digest comparison.
- Preserved clean pipeline exceptions unchanged; only raw deltas or audit failure override them because safety evidence must fail closed.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The injected one-track runner exposed that ordering output still iterated the global four-track list. `print_results` now receives the same injected `track_ids` sequence as `run_pipeline`, which keeps bounded verification and production execution consistent.
- The full run emits the existing expected `All-NaN slice encountered` warning for gap-heavy off-track bins; the explicit gap and validity rules handle those slots and all checks pass.
- Track 10 remains below the 50% valid-fraction QA threshold. This is an existing scientific QA concern, not a safety or contract failure.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Residual Risk

A malicious concurrent local process could swap a validated directory or file symlink between the final path resolution and the write. For this single-user scientific runner, repeated resolution plus the final raw digest audit is the accepted mitigation; no new filesystem abstraction or dependency was introduced.

## Next Phase Readiness

- Both mechanical gaps from `01-VERIFICATION.md` are closed with bounded normal/optimized evidence and a successful real-data transition.
- Phase 1 is mechanically ready for end-of-phase verification; the previously identified visual QA judgments for residual curvature and boundary sanity remain part of that review.

## Self-Check: PASSED

- Confirmed all four key files exist and compile.
- Confirmed commits `206b279`, `c4c13ac`, `f1e85b4`, and `8771323` exist in history.
- Re-ran all four bounded normal/optimized test commands successfully.
- Re-ran the full four-track extraction and artifact checker successfully with raw-integrity PASS.
- Confirmed `git status --porcelain data/raw/` is empty and no generated target artifact is staged for commit.
- Confirmed no known stub or unplanned threat surface was introduced; the planned local TOCTOU residual is documented above.

---
*Phase: 01-target-extraction-contract*
*Completed: 2026-07-19*
