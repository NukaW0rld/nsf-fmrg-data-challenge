---
phase: 01-target-extraction-contract
reviewed: 2026-07-20T00:47:33Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - src/targets.py
  - tests/test_targets.py
  - scripts/run_target_extraction.py
  - scripts/check_targets.py
  - tests/test_run_target_extraction.py
  - src/nsf_fmrg_data.py
findings:
  critical: 2
  warning: 2
  info: 0
  total: 4
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-20T00:47:33Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Narrative Findings (AI reviewer)

### Summary

The post-smoothing boundary revalidation and canonical raw/output containment that motivated plan 01-03 are now implemented, and all four bounded contract/safety commands pass in normal and optimized Python. The current persisted artifacts also pass the normal checker. Two blocker-class integrity defects nevertheless remain: the runner publishes each output directly into the live generation, so an interrupted run leaves a mixed set that the checker certifies; and the checker still implements all validation with optimization-removable `assert` statements. Two test/validator gaps also remain: invalid slots may contain infinities instead of the contractually required NaNs, and the no-per-track-tuning regression recognizes only a narrow subset of track-dependent syntax.

Focused temporary-repository probes reproduced the first three defects: an injected second-track failure left track 8 refreshed and tracks 10/14/21 stale while `check_targets.py` exited 0 with `ALL CHECKS PASSED`; `python -O scripts/check_targets.py` accepted four artifacts with crossed boundaries and negative widths; and the normal checker accepted infinities in every invalid numeric slot. No source file was modified during review.

## Critical Issues

### CR-01: Interrupted extraction publishes a mixed artifact generation that passes validation

**Severity:** BLOCKER
**File:** `/home/khoa2/nsf-fmrg-data-challenge/scripts/run_target_extraction.py:254-276`
**Related:** `/home/khoa2/nsf-fmrg-data-challenge/scripts/run_target_extraction.py:320-345`, `/home/khoa2/nsf-fmrg-data-challenge/scripts/check_targets.py:121-130`
**Issue:** `run_pipeline()` writes the live `extraction_params.json` first and then `run_track()` overwrites each live NPZ and QA image in sequence. If a later track or plot fails, earlier outputs belong to the attempted run while untouched outputs remain from the prior run. The final raw audit does not roll back or quarantine those processed outputs. `check_targets.py` has no generation ID, completion manifest, raw-input digest, code digest, or atomic publication marker, so it validates each remaining file independently and certifies the mixed set. A temporary probe started with a complete four-track generation, refreshed track 8, injected failure on track 10, and then observed checker exit 0 with `ALL CHECKS PASSED`. These files are downstream scientific ground truth, so silently combining generations is a correctness and provenance failure.

**Fix:** Write every JSON/NPZ/PNG into a new staging or generation directory. Include a completion manifest containing a run ID and the parameter/code/raw-input identities; validate all four staged tracks and complete the final raw audit; then atomically publish the complete generation by rename or pointer swap. Make the checker require the manifest and verify that every artifact belongs to that same completed run. On failure, leave the previous complete generation selected.

### CR-02: Optimized Python removes the checker and still reports success

**Severity:** BLOCKER
**File:** `/home/khoa2/nsf-fmrg-data-challenge/scripts/check_targets.py:25-81`
**Related:** `/home/khoa2/nsf-fmrg-data-challenge/scripts/check_targets.py:121-131`
**Issue:** Every artifact and provenance check is a language `assert`. Python removes those statements under `-O`, but the directly executable checker still loads the arrays, prints summaries, and unconditionally prints `ALL CHECKS PASSED`. A focused probe supplied four artifacts whose masks marked crossed boundaries and negative widths valid; `.venv/bin/python -O scripts/check_targets.py` exited 0 and printed success. The plan deliberately made the touched test suites optimization-safe, but the production artifact validator remains fail-open in the same supported interpreter mode.

**Fix:** Replace runtime assertions with an explicit check helper and add an optimized-mode malformed-artifact regression:

```python
def require(condition, message):
    if not bool(condition):
        raise ValueError(message)

require(np.all(y_upper_mm[valid_mask] > y_lower_mm[valid_mask]),
        f"Track {track_id}: crossed or degenerate boundaries survived.")
```

## Warnings

### WR-01: The normal checker accepts infinities in invalid slots

**Severity:** WARNING
**File:** `/home/khoa2/nsf-fmrg-data-challenge/scripts/check_targets.py:60-68`
**Issue:** Equality between `np.isfinite(array)` and `valid_mask` proves only that invalid slots are non-finite. Positive and negative infinity therefore pass all three mask checks, while the width identity and physical-bound checks inspect valid slots only. A normal-mode probe with one valid value and infinities in the other 399 width/upper/lower slots exited 0 with `ALL CHECKS PASSED`, despite D-07 requiring invalid numeric slots to contain NaN.

**Fix:** Explicitly require NaN in each invalid numeric slot:

```python
for key, values in (("w_mm", w_mm), ("y_upper_mm", y_upper_mm), ("y_lower_mm", y_lower_mm)):
    require(np.isnan(values[~valid_mask]).all(),
            f"Track {track_id}: {key} invalid slots must be NaN.")
```

### WR-02: The no-per-track-tuning test does not enforce its stated invariant

**Severity:** WARNING
**File:** `/home/khoa2/nsf-fmrg-data-challenge/tests/test_targets.py:131-137`
**Issue:** The regex rejects only `if track_id` and direct comparison/membership operators on the literal name `track_id`. Straightforward track-dependent parameterization such as `PARAMS_BY_TRACK[track_id]`, `get_params(track_id)`, `match track_id`, or a renamed local passes. The current extractor uses one shared parameterization, but this regression can remain green after a future violation of TARGET-02's central no-per-track-tuning rule.

**Fix:** Prefer a behavioral interface test showing that the pure extractor receives no track identity or track-derived parameters. If a structural guard remains useful, inspect the AST and allow `track_id` only in the I/O wrapper's filename lookup and returned metadata, rejecting subscripts, calls, matches, and aliases that influence extraction constants or functions.

---

_Reviewed: 2026-07-20T00:47:33Z_
_Reviewer: the agent (gsd-code-reviewer; generic-agent workaround)_
_Depth: standard_
