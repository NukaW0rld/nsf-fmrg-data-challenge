---
phase: 01-target-extraction-contract
plan: 01
subsystem: scientific-data
tags: [profilometry, numpy, target-extraction, contract-testing]

requires: []
provides:
  - Locked D-01 through D-16 local-width extraction contract on a shared 0.2 mm grid
  - Synthetic invariant suite covering gap handling, half-max edges, masked smoothing, and fixed-grid output
  - Explicit human ratification of Amendments A1 and A2 before any official real-track extraction
affects: [01-02-target-extraction-run, dataset-alignment, target-provenance]

tech-stack:
  added: [numpy, scipy, matplotlib, pillow, pandas]
  patterns: [bin-first profile aggregation, masked windowed polynomial smoothing, fixed-grid validity masks]

key-files:
  created: [src/targets.py, tests/test_targets.py]
  modified: []

key-decisions:
  - "Ratified Amendment A1 as written: D-05/D-06 gap handling applies to each 0.2 mm binned median profile, not each native approximately 4 micrometer column."
  - "Ratified Amendment A2 as written: a half-max run touching either y boundary is invalid because the true bead edge lies outside the measured strip."
  - "Locked one shared extraction parameterization before the official four-track run, including a 0.005 mm separation floor, 10-pixel maximum gap, and 5-point order-2 masked smoother."

patterns-established:
  - "Contract constants live in one module-level block with no track-specific extraction branches."
  - "Invalid fixed-grid slots remain NaN through separate upper/lower-boundary smoothing."

requirements-completed: [TARGET-01, TARGET-02]

coverage:
  - id: D1
    description: "Executable D-01 through D-16 target-extraction contract with one shared parameterization"
    requirement: TARGET-01
    verification:
      - kind: unit
        ref: ".venv/bin/python tests/test_targets.py (12/12 PASS)"
        status: pass
      - kind: other
        ref: "Task 2 acceptance greps: 12 constants, 8 functions, zero track conditionals, zero scipy savgol/filter overrides"
        status: pass
    human_judgment: false
  - id: D2
    description: "Amendments A1 and A2 ratified before plan 01-02 performs the official real-track extraction"
    requirement: TARGET-01
    verification:
      - kind: manual_procedural
        ref: "Task 3 checkpoint response: approved"
        status: pass
    human_judgment: false
  - id: D3
    description: "Project scientific Python environment is ready for the four-track extraction runner"
    requirement: TARGET-02
    verification:
      - kind: integration
        ref: ".venv/bin/python import check for numpy, scipy, matplotlib, and pandas"
        status: pass
      - kind: other
        ref: "uv pip list --python .venv/bin/python confirms no pytest installation"
        status: pass
    human_judgment: false

duration: 16min
completed: 2026-07-19
status: complete
---

# Phase 1 Plan 1: Target Extraction Contract Summary

**A fixed-grid, bin-first half-max width extractor with masked boundary smoothing, 12 synthetic invariants, and user-ratified A1/A2 validity rules**

## Performance

- **Duration:** 16 min
- **Started:** 2026-07-19T23:16:36Z
- **Completed:** 2026-07-19T23:32:31Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Implemented the full D-01 through D-16 contract in `src/targets.py` with 12 locked constants, eight pure extraction functions, fixed 400-slot output, and no per-track tuning branches.
- Added and passed 12 synthetic contract-invariant tests covering exact gap/noise boundaries, clipped and degenerate edges, NaN-mask fidelity, cross-gap smoothing, and end-to-end fixed-grid extraction.
- Recorded the user's explicit `approved` response as ratification of A1 (bin-first D-05/D-06) and A2 (invalidate y-boundary-clipped runs) before plan 01-02 performs the official real-track computation.

## Task Commits

Task 1 created the ignored local environment and therefore required no repository commit. Task 2 followed the required RED/GREEN sequence:

1. **Task 1: Wave 0 project environment** - environment-only (`.venv/` ignored)
2. **Task 2 RED: Contract-invariant tests** - `b1937fe` (test)
3. **Task 2 GREEN: TARGET-01 extraction contract** - `6fc97e5` (feat)
4. **Task 3: A1/A2 pre-compute ratification** - explicit user approval recorded in this summary

## Files Created/Modified

- `src/targets.py` - Shared contract constants and pure binning, gap handling, edge extraction, smoothing, and track I/O functions.
- `tests/test_targets.py` - Plain-Python synthetic assertion runner with 12 named invariant tests.

## Decisions Made

- Amendment A1 approved as-is: aggregation first within each 0.2 mm output cell, then apply the D-05/D-06 y-profile gap rule. This preserves output-cell locality while avoiding the empirically all-invalid native-column interpretation.
- Amendment A2 approved as-is: invalidate a slot when its largest half-max run touches either edge of the measured y strip, because the true boundary and width are not observable.
- All thresholds remain locked before the official four-track extraction and will not be tuned to force the expected power ordering.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The virtual environment intentionally has no `pip` module; package verification used `uv pip list --python .venv/bin/python` and confirmed the approved scientific stack with no pytest installation.
- A read-only security check found restricted raw data was already committed historically in `831987c`, before this plan. Neither Task 2 commit touches `data/raw/`; history remediation remains outside this plan and should occur before any external repository sharing.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-02 is unblocked to run the official four-track extraction with the ratified, locked contract.
- The expected width ordering remains an investigation outcome, not a tuning target; any ordering flag must be documented without changing these constants.

## Self-Check: PASSED

- Confirmed `src/targets.py`, `tests/test_targets.py`, and this summary exist.
- Confirmed commits `b1937fe` and `6fc97e5` exist in RED-to-GREEN order.
- Re-ran the assertion script with 12/12 PASS results and validated the coverage metadata.

---
*Phase: 01-target-extraction-contract*
*Completed: 2026-07-19*
