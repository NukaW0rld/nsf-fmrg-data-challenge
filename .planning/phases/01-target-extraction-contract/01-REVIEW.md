---
phase: 01-target-extraction-contract
reviewed: 2026-07-20T05:43:59Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - .gitignore
  - scripts/check_targets.py
  - scripts/run_target_extraction.py
  - src/nsf_fmrg_data.py
  - src/targets.py
  - tests/test_nsf_fmrg_data.py
  - tests/test_run_target_extraction.py
  - tests/test_targets.py
findings:
  critical: 3
  warning: 4
  info: 0
  total: 7
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-20T05:43:59Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Narrative Findings (AI reviewer)

### Summary

All eight scoped files were read in full. The three plain-Python test scripts pass in normal and optimized modes, and the current persisted-artifact checker exits successfully in both modes. Those checks do not cover several live failure paths in the new provenance and staged-publication code.

The highest-risk issues are that a numeric extraction parameter is absent from persisted provenance, output containment follows in-repository symlinks before destructive operations, and publication does not restore the previous live generation when its second rename fails. Four additional robustness gaps affect manifest trust, iterable handling, crash residue, and argument validation.

### Critical Issues

#### CR-01: Boundary-tracking behavior is omitted from extraction provenance

**File:** `src/targets.py:15-16,32-47`; `tests/test_targets.py:323-340`
**Issue:** `MAX_TRACKING_GAP_COLUMNS` controls when cross-column boundary history is discarded and therefore can change every persisted boundary and width. Unlike every other locked numeric extraction constant, it is absent from `extraction_params()`. The test explicitly locks the incomplete 12-value dictionary, so changing this constant would alter generated targets while leaving `extraction_params.json` and `manifest.json`'s parameter digest unchanged. The published artifacts would claim the same parameterization despite being numerically non-reproducible under that provenance.
**Fix:** Add `MAX_TRACKING_GAP_COLUMNS` to `extraction_params()`, update the expected provenance test, and regenerate the parameter file, manifest, and target artifacts. Add a regression that changing this constant changes the serialized parameter digest.

#### CR-02: Resolved output paths allow destructive operations on unrelated repository trees

**File:** `scripts/run_target_extraction.py:62-70,294-306`
**Issue:** `resolve_output_path()` resolves symlinks and accepts any resulting location inside the repository except `data/raw`. `publish_staging_dir()` then calls `shutil.rmtree()` and `Path.rename()` on those resolved locations. For example, if `processed_data/targets.previous` is a symlink to `src/`, `backup_dir` becomes the real `src/` path and line 301 recursively deletes source code. If `processed_data/targets` is a symlink to another in-repository directory, the resolved referent can be renamed away at line 303. The current test only covers a symlink into `data/raw`, so these data-loss paths pass unnoticed.
**Fix:** Treat output paths as a fixed lexical namespace under a non-symlinked `processed_data/` directory. Reject symlinks in every output ancestor and at `targets`, `targets.previous`, and staging destinations using `lstat()`/`is_symlink()` before mutation; do not return a referent path for later deletion. Restrict the publisher to the exact expected targets, backup, and staging names, and add temporary-repository regressions pointing both live and backup paths at harmless in-repository victim directories.

#### CR-03: A failed publish leaves the live target generation missing

**File:** `scripts/run_target_extraction.py:294-306,405-408`
**Issue:** Replacing an existing generation is a two-rename sequence: live targets are moved to `.previous`, then staging is moved to the live name. If the second rename fails (permissions, filesystem error, interruption), the previous valid generation is never restored and the pipeline exits with `processed_data/targets/` absent. Cleanup and rollback are not wrapped around the publication step. This contradicts the stated atomic-publication guarantee and turns a fully computed but failed update into loss of the live artifact set.
**Fix:** Implement publication as a transaction: after moving live to backup, wrap the staging rename in `try/except`; on failure, restore backup to the live name before re-raising, preserving the original error (and report a distinct fatal error if rollback also fails). Prefer an atomic directory-exchange primitive where supported. Add an injected second-rename-failure test that starts with a valid live generation and asserts its bytes remain available at the canonical path.

### Warnings

#### WR-01: The completion manifest does not bind any artifact bytes to its run

**File:** `scripts/run_target_extraction.py:353-368`; `scripts/check_targets.py:123-140`
**Issue:** The manifest records a run ID, track IDs, timestamp, and parameter hash, but no hashes for the four NPZ files or QA outputs. The checker only compares the parameter hash and track-ID set. Replacing one NPZ with a structurally valid artifact from another run therefore still passes `ALL CHECKS PASSED`, so the checker cannot establish the same-generation claim in its error messages.
**Fix:** Create the manifest after all track files are complete, include a deterministic filename-to-SHA256 map (at minimum for every NPZ and the parameter JSON), and have the checker require the exact artifact set and verify every digest.

#### WR-02: One-shot or empty `track_ids` inputs can publish an incomplete generation

**File:** `scripts/run_target_extraction.py:309-312,358-373,405-412`
**Issue:** `list(track_ids)` consumes a generator while writing the manifest, so the later extraction comprehension runs zero tracks and publishes only metadata. An explicitly empty sequence does the same. There is no non-empty, uniqueness, or supported-ID validation before the existing live directory is replaced.
**Fix:** Normalize once at function entry with `track_ids = tuple(track_ids)`, reject an empty tuple, duplicates, and IDs outside `TRACK_POWER_W`, then reuse that tuple for the manifest, extraction, and reporting. Add generator and empty-input regressions.

#### WR-03: Crash-recovery directories are not ignored

**File:** `.gitignore:6-10`; `scripts/run_target_extraction.py:294-306,329-336`
**Issue:** Only `/processed_data/targets/` is ignored. The publisher deliberately creates `/processed_data/.targets-staging-*` and `/processed_data/targets.previous`, either of which can remain after process termination or a publish failure. These potentially large generated data trees then appear as untracked files and can be committed accidentally.
**Fix:** Ignore `/processed_data/.targets-staging-*/` and `/processed_data/targets.previous/`. Keep runtime cleanup and recovery logic; ignore rules are only the repository-safety backstop.

#### WR-04: Invalid polynomial orders bypass validation on degenerate inputs

**File:** `src/nsf_fmrg_data.py:205-216`
**Issue:** `robust_plane_detrend()` returns its degenerate `(copy, None)` fallback before validating `order`. Consequently, `order=-1` or a non-integer silently succeeds when fewer than 100 sampled values are finite but raises `ValueError` for the same argument on non-degenerate data. Argument validity should not depend on input density.
**Fix:** Move the `order` type/range validation before the `valid.sum() < 100` return and add invalid-order tests for both degenerate and ordinary inputs.

---

_Reviewed: 2026-07-20T05:43:59Z_
_Reviewer: the agent (gsd-code-reviewer; generic-agent workaround)_
_Depth: standard_
