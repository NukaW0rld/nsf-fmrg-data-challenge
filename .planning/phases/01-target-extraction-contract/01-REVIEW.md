---
phase: 01-target-extraction-contract
reviewed: 2026-07-19T23:48:38Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - src/targets.py
  - tests/test_targets.py
  - scripts/run_target_extraction.py
  - scripts/check_targets.py
  - .gitignore
findings:
  critical: 4
  warning: 2
  info: 0
  total: 6
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-19T23:48:38Z  
**Depth:** standard  
**Files Reviewed:** 5  
**Status:** issues_found

## Narrative Findings (AI reviewer)

### Summary

The extraction implementation follows most of the locked constants and its current synthetic and persisted-artifact checks pass. Those passing checks do not establish the scientific contract, however. Four blocker-class integrity failures remain: smoothing can turn valid positive widths into crossed boundaries without invalidating them; the raw-data guard is derived from an unvalidated CLI root and can therefore protect the wrong directory while writing inside the real raw tree; a failed run can leave a mixed-generation artifact set that later validation cannot detect; and both validation entry points can print success with their assertions disabled. Two additional verifier/test gaps allow malformed invalid slots and future per-track parameterization regressions to pass their stated checks.

The imported `load_wyko_asc`, `robust_plane_detrend`, and `largest_true_run` call boundaries were traced in `src/nsf_fmrg_data.py`. No source outside the five-file review scope was modified or counted in the frontmatter.

## Critical Issues

### CR-01: Boundary smoothing can create negative widths that remain marked valid

**Severity:** BLOCKER  
**File:** `/home/khoa2/nsf-fmrg-data-challenge/src/targets.py:158-165`  
**Issue:** `halfmax_edges()` rejects crossed raw boundaries, but `extract_targets_from_arrays()` separately smooths the two boundary curves and then defines validity only as `np.isfinite(w_mm)`. A quadratic Savitzky-Golay fit is not positivity-preserving, so initially positive widths can become zero or negative after smoothing. For example, applying the public smoother to an upper-minus-lower width sequence `[10.0, 0.1, 0.1, 0.1, 10.0]` produces `-1.59714286` at the center while it remains finite and therefore valid under line 163. This violates the locked rule that crossed or degenerate boundaries must be invalid and can persist physically impossible ground truth. The downstream checker may catch the artifact only after it has already been written, but the library contract itself is wrong.

**Fix:** Revalidate the smoothed boundaries before returning, remask every crossed/degenerate result to NaN, and apply the zero-valid hard error after that revalidation. Add a regression case with positive unsmoothed widths that exhibit polynomial overshoot.

```python
y_upper = nan_savgol(y_upper_raw)
y_lower = nan_savgol(y_lower_raw)
valid_mask = (
    np.isfinite(y_upper)
    & np.isfinite(y_lower)
    & (y_upper > y_lower)
)
y_upper = np.where(valid_mask, y_upper, np.nan)
y_lower = np.where(valid_mask, y_lower, np.nan)
w_mm = np.where(valid_mask, y_upper - y_lower, np.nan)
if not valid_mask.any():
    raise ValueError("Target extraction produced zero valid x-positions.")
```

### CR-02: The raw-data guard can protect the wrong tree while the runner writes into the real raw tree

**Severity:** BLOCKER  
**File:** `/home/khoa2/nsf-fmrg-data-challenge/scripts/run_target_extraction.py:198-216`  
**Issue:** Both the protected raw path and the output path are derived from an unchecked `--project_dir`. A concrete invocation such as `--project_dir data/raw` snapshots `<repo>/data/raw/data/raw` (normally nonexistent/empty) at line 204, then creates `<repo>/data/raw/processed_data/targets/extraction_params.json` at lines 205-209, directly violating the absolute raw-write prohibition. The first extraction then fails because the nested height-map path is wrong, and lines 212-216 never execute, so even the incorrectly scoped post-run check is skipped. Existing symlinks from `processed_data` or `processed_data/targets` into `data/raw` create the same write-before-detect problem. A post-hoc mtime/size comparison cannot prevent or recover raw corruption, and it does not run in a `finally` block.

**Fix:** Before any mkdir/open/save operation, validate that `project_dir` is the repository root (using required repository markers and the expected raw height-map directory), resolve the raw and output paths through symlinks, and reject any output path contained by the resolved raw tree. Keep an integrity snapshot/digest check in `finally` so failures are audited as well as successes. Pass already-validated resolved paths into all writing functions rather than reconstructing them from arbitrary CLI input.

```python
project_dir = args.project_dir.resolve(strict=True)
if not (project_dir / "src" / "targets.py").is_file():
    raise ValueError(f"Not a project root: {project_dir}")
raw_dir = (project_dir / "data" / "raw").resolve(strict=True)
targets_dir = (project_dir / "processed_data" / "targets").resolve(strict=False)
if targets_dir == raw_dir or targets_dir.is_relative_to(raw_dir):
    raise ValueError("Target output resolves inside data/raw.")
```

### CR-03: Failed runs leave scientifically incoherent mixed-generation artifacts

**Severity:** BLOCKER  
**File:** `/home/khoa2/nsf-fmrg-data-challenge/scripts/run_target_extraction.py:147-166`  
**Related:** `/home/khoa2/nsf-fmrg-data-challenge/scripts/run_target_extraction.py:204-216`, `/home/khoa2/nsf-fmrg-data-challenge/scripts/check_targets.py:121-130`  
**Issue:** The runner overwrites `extraction_params.json` first and then overwrites each track artifact and QA image directly in the live cache. If a later track, plot save, or raw-integrity check fails, earlier tracks are from the attempted run while later tracks may remain from a previous run. There is no generation ID, raw-input digest, parameter digest embedded in each artifact, completion manifest, or atomic publication boundary. `check_targets.py` validates each file independently and compares only the single current params JSON to current code, so a mixed set can still print `ALL CHECKS PASSED`. Because these files become downstream ground truth, this is a provenance and data-integrity failure rather than merely untidy failure cleanup.

**Fix:** Produce the complete four-track generation in a new staging/generation directory, include one manifest containing a run ID plus code/parameter and raw-input digests, validate the staged generation, perform the raw-integrity check, and only then atomically publish a pointer or rename to that generation. Make the checker require the completion manifest and verify every NPZ belongs to the same run. On failure, leave the prior complete generation selected and discard or clearly quarantine the incomplete staging directory.

### CR-04: Both validation entry points can report success with validation compiled out

**Severity:** BLOCKER  
**File:** `/home/khoa2/nsf-fmrg-data-challenge/scripts/check_targets.py:25-81`  
**Related:** `/home/khoa2/nsf-fmrg-data-challenge/scripts/check_targets.py:121-127`, `/home/khoa2/nsf-fmrg-data-challenge/tests/test_targets.py:17-190`, `/home/khoa2/nsf-fmrg-data-challenge/tests/test_targets.py:193-210`  
**Issue:** The artifact checker and nearly all contract tests use Python `assert` as runtime validation, but both are shipped as directly executable scripts. Python removes these statements under `python -O`. In that supported execution mode, malformed artifacts can bypass the dtype, grid, mask, physical-bound, and provenance checks while `check_targets.py` still reaches `ALL CHECKS PASSED`; most test functions likewise become no-ops while the manual runner prints `PASS`. These scripts are the mechanical evidence for a scientific ground-truth contract, so a success result must not depend on interpreter optimization flags.

**Fix:** Replace runtime `assert` statements with an explicit helper that raises `ValueError`/`AssertionError`, or run tests through a framework that rewrites and preserves assertions. Given the current no-pytest constraint, an explicit helper is sufficient:

```python
def require(condition, message):
    if not bool(condition):
        raise AssertionError(message)

require(target_path.exists(), f"Track {track_id}: missing artifact {target_path}.")
```

Add a subprocess regression check that invokes each entry point with `-O` against a deliberately invalid condition and verifies a nonzero exit.

## Warnings

### WR-01: The checker accepts infinities in slots that the contract requires to contain NaN

**Severity:** WARNING  
**File:** `/home/khoa2/nsf-fmrg-data-challenge/scripts/check_targets.py:60-68`  
**Issue:** Comparing `np.isfinite(array)` to `valid_mask` proves only that invalid slots are non-finite. Positive or negative infinity therefore satisfies all three mask checks when `valid_mask` is false, even though D-07 requires invalid widths to remain specifically `NaN`. The later identity and bound checks index valid slots only, so they do not reject those infinities. The checker can consequently certify a malformed persisted artifact.

**Fix:** Explicitly require NaN in every invalid slot for widths and both boundaries, in addition to the finite/mask equality checks.

```python
for key in ("w_mm", "y_upper_mm", "y_lower_mm"):
    require(np.isnan(artifact[key][~valid_mask]).all(),
            f"Track {track_id}: {key} invalid slots must be NaN.")
```

### WR-02: The no-per-track-tuning regression test does not enforce its stated invariant

**Severity:** WARNING  
**File:** `/home/khoa2/nsf-fmrg-data-challenge/tests/test_targets.py:123-129`  
**Issue:** The regex detects only an `if track_id` form or direct comparison/membership operators applied to the literal name `track_id`. Common per-track parameterization forms such as `params = PARAMS_BY_TRACK[track_id]`, `match track_id`, a renamed local variable, or a helper call keyed by the ID all pass. The current implementation is shared, but this test can remain green after a straightforward future regression that violates the phase's central single-parameterization prohibition.

**Fix:** Test behavior rather than a small syntax subset: isolate the pure extractor from track identity (as it currently is), verify that the I/O wrapper passes no track-derived extraction parameters, and use AST inspection if a structural guard is still desired. At minimum, reject subscript/call/match uses of `track_id` inside extraction logic and allow only filename resolution plus returned metadata.

---

_Reviewed: 2026-07-19T23:48:38Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_
