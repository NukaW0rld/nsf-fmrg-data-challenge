---
phase: 01-target-extraction-contract
plan: 10
subsystem: infra
tags: [pathlib, symlink-safety, toctou, data-integrity, target-extraction]

# Dependency graph
requires:
  - phase: 01-target-extraction-contract
    provides: run_target_extraction.py publish pipeline and check_targets.py contract checker (01-08 and earlier plans)
provides:
  - "reject_symlink_path() rejecting a symlinked candidate or any in-repo ancestor before resolve_output_path resolves anything"
  - "publish_staging_dir() re-checking is_symlink() immediately before every shutil.rmtree/rename"
  - "MIN_VALID_FRACTION = 0.5 as a hard, single, project-wide require() gate in check_targets.py"
affects: [01-11-track-10-coverage-fix]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Lexical (unresolved) symlink rejection performed before Path.resolve(), since resolve() follows symlinks and would defeat the check"
    - "Re-check is_symlink() immediately before every destructive filesystem op, not only at validation time, to narrow the accepted TOCTOU window"

key-files:
  created: []
  modified:
    - scripts/run_target_extraction.py
    - scripts/check_targets.py
    - tests/test_run_target_extraction.py

key-decisions:
  - "reject_symlink_path walks candidate.parents but stops exactly at the resolved project_root, so a symlink outside the repository in the caller's own path prefix is not treated as the pipeline's business."
  - "Updated the pre-existing test_symlink_output_into_raw_is_rejected assertion from checking for the substring \"raw\" to checking for \"symlink\", since the rejection now fires at the earlier symlink check (on the processed_data ancestor) rather than the later raw-containment check — the plan explicitly anticipated this mechanism shift."
  - "check_targets.py's coverage floor is a single MIN_VALID_FRACTION module constant with no per-track table; per decision U-02 it is intentionally left failing (track 10 at 5.2%) rather than weakened."

requirements-completed: [TARGET-01, TARGET-02]

coverage:
  - id: D1
    description: "resolve_output_path rejects a symlinked candidate or any symlinked in-repo ancestor before resolving/returning anything"
    requirement: "TARGET-02"
    verification:
      - kind: unit
        ref: "tests/test_run_target_extraction.py#test_symlink_at_processed_data_is_rejected"
        status: pass
      - kind: unit
        ref: "tests/test_run_target_extraction.py#test_symlink_output_into_raw_is_rejected"
        status: pass
    human_judgment: false
  - id: D2
    description: "publish_staging_dir re-checks backup_dir/targets_dir/staging_dir with is_symlink() immediately before every rmtree/rename"
    requirement: "TARGET-02"
    verification:
      - kind: unit
        ref: "tests/test_run_target_extraction.py#test_publish_refuses_symlinked_backup_immediately_before_rmtree"
        status: pass
      - kind: unit
        ref: "tests/test_run_target_extraction.py#test_symlink_at_backup_path_is_rejected"
        status: pass
    human_judgment: false
  - id: D3
    description: "check_targets.py enforces MIN_VALID_FRACTION = 0.5 via a blocking require(), no longer a non-blocking print"
    requirement: "TARGET-01"
    verification:
      - kind: unit
        ref: "scripts/check_targets.py --project_dir . (manual invocation, exits non-zero naming track 10 and the 50% floor)"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-07-21
status: complete
---

# Phase 01 Plan 10: Symlink-Safe Publish Path and Hard Coverage Floor Summary

**Closed CR-03 (symlink-redirected `rmtree`/`rename` in the target publisher) and CR-02 (non-blocking sub-50% coverage print) by adding a repo-root-bounded symlink guard ahead of every destructive publish operation and promoting `check_targets.py`'s coverage check to a hard `require()`.**

## Performance

- **Duration:** ~12 min
- **Completed:** 2026-07-21
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- `reject_symlink_path(path, project_root)` added to `scripts/run_target_extraction.py`: rejects a symlinked candidate outright, and walks `candidate.parents` up to (but not including) the resolved `project_root`, rejecting any symlinked ancestor in between. Uses `is_symlink()` (lstat, no dereference) so dangling symlinks are also caught. Called as the first statement of `resolve_output_path`.
- `publish_staging_dir` now re-checks `is_symlink()` on `backup_dir`, `targets_dir`, and `staging_dir` immediately before each of its four destructive operations (two `shutil.rmtree` calls, two `rename` calls), narrowing the TOCTOU window between validation and the destructive op.
- Three new regressions in `tests/test_run_target_extraction.py` prove a symlink planted at `processed_data/targets.previous` or at `processed_data` itself is rejected with a real in-repo victim directory and its sentinel file surviving `run_pipeline`/`publish_staging_dir`. Test count grew from 7 to 10.
- `scripts/check_targets.py` gained `MIN_VALID_FRACTION = 0.5` as a single project-wide module constant and now enforces it via `require(valid_fraction >= MIN_VALID_FRACTION, ...)`, replacing the previous non-blocking informational print. The message names the track, its actual fraction, and the floor.
- Verified as intended: `check_targets.py --project_dir .` now exits non-zero against the currently published artifacts because track 10 is 5.2% valid; it no longer prints `ALL CHECKS PASSED`. Tracks 8 (359/400), 14 (301/400), and 21 (324/400) still pass the floor unchanged.

## Task Commits

Each task was committed atomically:

1. **Task 1: CR-03 — reject symlinks at every output path the publisher touches** - `ccf73cf` (fix)
2. **Task 2: CR-02 — promote the coverage floor to a hard, project-wide require()** - `55a6497` (fix)

**Plan metadata:** (this commit, docs: complete plan)

## Files Created/Modified
- `scripts/run_target_extraction.py` - Added `reject_symlink_path`; `resolve_output_path` calls it first; `publish_staging_dir` re-checks `is_symlink()` before every `rmtree`/`rename`
- `scripts/check_targets.py` - Added `MIN_VALID_FRACTION = 0.5`; replaced the non-blocking sub-50% print with a hard `require()`
- `tests/test_run_target_extraction.py` - Added `test_symlink_at_backup_path_is_rejected`, `test_symlink_at_processed_data_is_rejected`, `test_publish_refuses_symlinked_backup_immediately_before_rmtree`; updated `test_symlink_output_into_raw_is_rejected`'s assertion to match the new, earlier rejection point

## Decisions Made
- The ancestor walk in `reject_symlink_path` stops exactly at the resolved `project_root` (not beyond it), so a symlink in the user's own path prefix outside the repository is out of scope for this check.
- `test_symlink_output_into_raw_is_rejected`'s exception-message assertion was changed from `"raw" in str(exc).lower()` to `"symlink" in str(exc).lower()`, because the rejection now fires at the new symlink check on the `processed_data` ancestor rather than the raw-containment check further downstream — anticipated explicitly in the plan's `<behavior>` section.
- No per-track allowance table or exemption mechanism was added to `check_targets.py`; the floor is a single constant per decision U-02, and the resulting non-zero exit against track 10's 5.2%-valid artifact is the accepted, intended outcome that sequences plan 01-11.

## Deviations from Plan

None - plan executed exactly as written. The one test-assertion edit (`test_symlink_output_into_raw_is_rejected`) was explicitly anticipated by the plan's own `<behavior>` block ("now at the symlink check rather than the raw-containment check") and is not an unplanned deviation.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both automated safety-net defects (CR-03, CR-02) identified in `01-REVIEW.md` are now closed with regression coverage.
- `check_targets.py` currently exits non-zero (track 10 at 5.2% valid) — this is the intended, accepted state per decision U-02. Plan 01-11 must resolve track 10's coverage collapse before Phase 1 can sign off; this plan intentionally does not touch `src/targets.py`, `src/nsf_fmrg_data.py`, or any extraction constant.
- `processed_data/` artifacts were not regenerated by this plan (`git status --porcelain processed_data` is empty) — that regeneration is plan 01-11's responsibility.

---
*Phase: 01-target-extraction-contract*
*Completed: 2026-07-21*

## Self-Check: PASSED

All claimed files found on disk; both task commits (ccf73cf, 55a6497) found in git history.
