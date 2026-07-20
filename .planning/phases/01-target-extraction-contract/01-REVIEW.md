---
phase: 01-target-extraction-contract
reviewed: 2026-07-20T21:50:24Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - scripts/check_targets.py
  - scripts/diagnose_width_regression.py
  - scripts/run_target_extraction.py
  - src/nsf_fmrg_data.py
  - src/targets.py
  - tests/test_nsf_fmrg_data.py
  - tests/test_run_target_extraction.py
  - tests/test_targets.py
findings:
  critical: 3
  warning: 3
  info: 2
  total: 8
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-20T21:50:24Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

This review supersedes the earlier `01-REVIEW.md`/`01-REVIEW-FIX.md` pass (which covered plans 01-01..01-05) and evaluates the full current state of the target-extraction contract, including the 01-06/01-07/01-08 gap-closure sequence (width-ordering diagnosis + bead-masking detrend fix + artifact regeneration).

All three test suites (`tests/test_nsf_fmrg_data.py`, `tests/test_targets.py`, `tests/test_run_target_extraction.py`) were executed in a fresh venv against the real repository and **all 38 tests pass**. `git diff e88f8d2^..HEAD` for this gap-closure sequence is small and surgical: a new `fit_mask` parameter threaded through `robust_plane_detrend`, a new `bead_exclusion_mask()` in `targets.py`, and a new `scripts/diagnose_width_regression.py` diagnostic tool.

This review did not stop at "tests pass," per the adversarial mandate. Two independent lines of investigation surfaced real, reproduced problems the test suite does not catch:

1. **Real-data verification.** `scripts/check_targets.py` was re-run against the actual, currently-persisted `processed_data/targets/*.npz` artifacts (published `2026-07-20T21:34:24Z`, `extraction_params_sha256` matching the current locked constants including the new `BEAD_MASK_HEIGHT_FRACTION` fix) and the resulting QA figures were inspected. Track 10's artifact is 95% invalid and the width-ordering regression this phase exists to fix is still present for the 10-vs-14 pair (CR-01), and the checker that is supposed to gate this doesn't fail on it (CR-02).
2. **Reproduced exploit against `run_target_extraction.py`'s publish step.** The prior review's CR-02 ("resolved output paths allow destructive operations on unrelated repository trees") was independently re-tested against the current code in an isolated scratch repository and is **still exploitable**: a pre-existing symlink at `processed_data/targets.previous` pointing at `src/` causes a successful pipeline run to `shutil.rmtree()` the entire `src/` directory (CR-03, reproduced live below).

## Critical Issues

### CR-01: Track 10's persisted target artifact is 95% invalid and still violates the width-ordering contract this phase was built to fix

**File:** `processed_data/targets/track_10_targets.npz` (produced by `src/targets.py:246-314`, `scripts/run_target_extraction.py:245-291`)
**Issue:**
Running `scripts/check_targets.py` against the current, freshly-published artifacts (manifest `run_id=0a50e5c1...`, published `2026-07-20T21:34:24Z`) produces:

```
Track 10 valid fraction 5.2% is below 50% — FLAG

track  power_W  valid_bins  median_mm  mean_mm
    8      400         359     0.7411   0.6808
   10      350          21     0.2509   0.1493
   14      300         301     0.5264   0.4794
   21      200         324     0.2412   0.2834
Ordering 8 vs 10: 0.7411 mm > 0.2509 mm — PASS
Ordering 10 vs 14: 0.2509 mm > 0.5264 mm — FLAG
Ordering 14 vs 21: 0.5264 mm > 0.2412 mm — PASS
ALL CHECKS PASSED
```

Track 10 only produces 21 of 400 valid grid slots (5.25%). Its median width (0.2509 mm, computed from that 21-point sample) is nearly identical to Track 21's width (the *lowest*-power track, 200 W) even though Track 10 is the second-*highest*-power track (350 W). Excluding Track 10, the remaining three tracks (8: 0.74 mm @ 400 W, 14: 0.53 mm @ 300 W, 21: 0.24 mm @ 200 W) are cleanly monotonic in power — strongly indicating Track 10's number is an artifact of extraction failure, not real physics.

I instrumented the exact per-bin rejection reasons for Track 10 through the current locked pipeline (`bead_exclusion_mask` + `robust_plane_detrend(order=4, fit_mask=...)` + `extract_targets_from_arrays`):

```
{'no_columns': 0, 'gap_fail': 112, 'no_baseline_sep': 0, 'clipped_run_only': 267, 'ok': 21}
```

267 of 400 bins (66.75%) fail because the *only* above-half-max run in that bin's profile touches the y=0 or y=479 edge of the mapped strip, and `halfmax_edges` (`src/targets.py:141-147`) deliberately excludes boundary-clipped runs as "never a tracking candidate" (by design, per D-01/D-03). Visual confirmation: `processed_data/targets/qa/track_10_residual_map.png` shows the elevated (bead) residual concentrated along the y≈0–0.4 mm edge of the strip for nearly the full 20–100 mm track length, unlike Track 14's residual map (`track_14_residual_map.png` / `track_14_overlay.png`), which shows a clean bead band centered around y≈0.5–1.3 mm, well clear of both edges. Track 10's bead is not fully captured within the profilometer's y-scan window (or the strip is misaligned for this file), so the boundary-exclusion safeguard — correct in isolation — silently discards the vast majority of the track for this one file. All four `Heightmap_*.ASC` headers report the identical `y_size=480`, `pixel_size_mm=0.003982`, so this is not explained by a different strip height for Track 10.

This matters because `CLAUDE.md` is explicit that only 4 track conditions exist and cross-track leave-one-out validation is required; a target artifact that is 95% invalid for one of the four conditions means that condition is effectively unusable for training/validation, and the phase's own regenerated ordering diagnostic (the entire purpose of 01-06/07/08) is still flagged as failing.

**Fix:**
Do not treat this as "documented and never used to tune" (the `print_results` disclaimer at `src/targets.py:77` is appropriate for genuine physical ordering ambiguity, not for a track that is 95% unextracted). Before this phase is considered done:
1. Investigate why Track 10's bead sits at/beyond the y-strip edge for nearly the entire track length.
2. Either re-acquire/re-crop Track 10 with a wider y-window that fully contains the bead, or make a principled, documented decision (not derived from the resulting ordering, consistent with the project's own Amendment-A3/A4 precedent) about how edge-clipped tracks should be handled, and re-run the extraction.
3. Do not treat `processed_data/targets/track_10_targets.npz` as production-ready until it clears a real minimum-coverage bar (see CR-02).

### CR-02: `check_targets.py` treats catastrophic per-track coverage loss as a non-blocking print, so "ALL CHECKS PASSED" is emitted even when a track is 95% invalid

**File:** `scripts/check_targets.py:92-96`
**Issue:**
```python
valid_count = int(valid_mask.sum())
require(valid_count > 0, f"Track {track_id}: all-invalid artifacts are prohibited.")
valid_fraction = valid_count / len(valid_mask)
if valid_fraction < 0.5:
    print(f"Track {track_id} valid fraction {valid_fraction:.1%} is below 50% — FLAG")
```
The only coverage guard is `valid_count > 0`; a track with just 1 valid slot out of 400 would pass. The `< 50%` branch is a `print`, not a `require(...)` — it never raises and never prevents `main()` from reaching `print("ALL CHECKS PASSED")`. This is precisely how CR-01 (5.25% valid coverage) went unnoticed by the automated "contract" checker: the script that exists specifically to gate the target-extraction contract silently accepts a near-total extraction failure for one of the four track conditions and reports success.

**Fix:** Promote the low-coverage check to a hard failure (or at minimum a distinct, non-zero exit path) with a project-chosen minimum coverage threshold, e.g.:
```python
MIN_VALID_FRACTION = 0.5  # or whatever the team decides is the real floor

require(
    valid_fraction >= MIN_VALID_FRACTION,
    f"Track {track_id}: valid fraction {valid_fraction:.1%} is below the "
    f"{MIN_VALID_FRACTION:.0%} minimum-coverage floor — extraction likely failed.",
)
```
If some tracks are expected to have legitimately lower (but still usable) coverage, encode that as an explicit, per-track, documented allowance — not a silent print for every track.

### CR-03: `publish_staging_dir` follows a pre-existing symlink at the backup path and recursively deletes whatever it points at — reproduced, deletes `src/` in a live run

**File:** `scripts/run_target_extraction.py:62-70` (`resolve_output_path`), `294-306` (`publish_staging_dir`)
**Issue:** `resolve_output_path` only forbids two things: escaping `project_root`, and landing inside `data/raw`. It resolves symlinks (`Path(path).resolve(strict=False)`) but does not reject them when they point elsewhere inside the repository. `publish_staging_dir` computes `backup_dir = resolve_output_path(targets_dir.with_name(targets_dir.name + ".previous"), ...)` and then unconditionally does `shutil.rmtree(backup_dir)` if it exists.

If `processed_data/targets.previous` already exists as a symlink to any other in-repo directory (e.g. `src/`, `.git/`, `tests/`) — left over from a prior partial failure, created by another process, or planted maliciously — `resolve_output_path` happily resolves it to that real directory (since it isn't under `data/raw`), and `publish_staging_dir` deletes it. I reproduced this against the current code in an isolated scratch repository (not the real project repo):

```
Before publish: src exists? True VICTIM exists? True
data/raw/ integrity PASS: no files created, modified, or deleted.
run_pipeline completed without error
After publish: src exists? False VICTIM exists? False
src contents: GONE
```

`run_pipeline` reported the `data/raw/` integrity audit as PASS (correctly — `data/raw/` genuinely wasn't touched) and returned normally, while `src/` (standing in for any non-`data/raw` repository directory, e.g. `.git/`) was recursively deleted. The existing regression `tests/test_run_target_extraction.py::test_symlink_output_into_raw_is_rejected` only covers a symlink pointing *into* `data/raw`; it does not cover a symlink at `targets.previous` (or `processed_data` itself) pointing at any other in-repository directory, so this path has no test coverage.

**Fix:** Reject symlinks outright at every output path the publisher touches, rather than resolving through them:
```python
def resolve_output_path(path: Path, project_root: Path, raw_dir: Path) -> Path:
    root = Path(project_root).resolve(strict=True)
    protected_raw = Path(raw_dir).resolve(strict=True)
    candidate = Path(path)
    if candidate.is_symlink():
        raise ValueError(f"Output path must not be a symlink: {candidate}.")
    resolved = candidate.resolve(strict=False)
    if not resolved.is_relative_to(root):
        raise ValueError(f"Output path escapes the canonical repository: {resolved}.")
    if resolved == protected_raw or resolved.is_relative_to(protected_raw):
        raise ValueError(f"Output path enters the protected raw tree: {resolved}.")
    return resolved
```
and/or have `publish_staging_dir` `lstat()`/`is_symlink()`-check `backup_dir` and `targets_dir` immediately before `rmtree`/`rename` and refuse to operate on a symlink. Add a regression that plants a symlink at `targets.previous` (and separately at `processed_data`) pointing at a harmless in-repo victim directory and asserts the victim survives `run_pipeline`.

## Warnings

### WR-01: `find_track_file`'s fallback condition makes its anchored boundary-regex protection a no-op

**File:** `src/nsf_fmrg_data.py:28`
**Issue:**
```python
if re.search(rf'(^|[_\-\s]){track_id}($|[_\-\s\.])', name) or f'{track_id}' in name:
    matches.append(p)
```
The `or f'{track_id}' in name` clause is a strict superset of the regex match (any regex match is already a substring match), so the entire condition reduces to `f'{track_id}' in name`. The word-boundary-anchored regex — clearly written to prevent, e.g., track 10 accidentally matching a file containing "210" or a resolution/date string — provides no actual protection because of the `or`. With the current 4-file dataset this does not currently misfire (verified: `find_track_file` resolves each of the 4 tracks' thermal/height-map files correctly), but it is a latent correctness risk for any future file whose name happens to contain a track ID's digits anywhere — `find_track_file` would silently include it as a candidate and `natural_key`-sort could pick the wrong file with no error raised.
**Fix:** Drop the fallback (the regex is already correct), or intentionally document why a permissive fallback is desired:
```python
if re.search(rf'(^|[_\-\s]){track_id}($|[_\-\s\.])', name):
    matches.append(p)
```

### WR-02: The exact-filename safety check exists only for height maps, not for thermal or SEM loaders

**File:** `src/targets.py:288-290` vs. `src/nsf_fmrg_data.py:114-130`, `133-137`
**Issue:** `extract_track_targets` guards against `find_track_file` mis-selecting the wrong height map by asserting `Path(data['file']).name == f'Heightmap_{track_id}.ASC'` (raising `ValueError` otherwise). No equivalent verification exists in `extract_final_thermal_frames` (thermal `.mat` selection) or `get_sem_tile_paths` (SEM tile directory selection) — both rely solely on the fragile matching described in WR-01 with no post-hoc validation. If a future thermal/SEM filename collides under WR-01's loose matching, the wrong track's thermal cube or SEM tiles could be silently loaded and paired with the correct track's height-map targets, corrupting the thermal→geometry training pairing without any error.
**Fix:** Add the same kind of exact-name (or otherwise strict) verification to `extract_final_thermal_frames` and `get_sem_tile_paths` that `extract_track_targets` already applies to height maps, e.g. assert the resolved filename matches `Thermal_{track_id}.mat` and the SEM directory matches `SEM_{track_id}`.

### WR-03: `diagnose_width_regression.py` no longer reflects the production detrend path after the bead-mask fix landed

**File:** `scripts/diagnose_width_regression.py:101-122`
**Issue:** `run_sweep` calls `robust_plane_detrend(data['Z_mm'], data['x_actual_mm'], data['y_mm'], order=order)` with no `fit_mask` argument, i.e. it always exercises the pre-fix (unmasked) detrend path. That was correct when this script was written to diagnose the original regression (01-06), but since `src/targets.py:294-301`'s production path now always passes `fit_mask=bead_exclusion_mask(...)`, this diagnostic tool's sweep results no longer represent what the shipped pipeline actually does. A future engineer re-running this script to debug a new ordering anomaly (e.g. the Track 10 problem in CR-01) would be comparing against a stale, no-longer-applicable baseline with no indication in the script that it predates the bead-masking fix.
**Fix:** Either add a `fit_mask` dimension to the sweep (masked vs. unmasked, matching how `DETREND_ORDERS`/`CONTINUITY_OPTIONS` are already swept) or add a prominent comment noting this script intentionally diagnoses the *pre-fix* detrend behavior and is not representative of current production output.

## Info

### IN-01: Magic numbers without derivation comments

**File:** `scripts/check_targets.py:24`, `src/nsf_fmrg_data.py:68`
**Issue:** `Y_STRIP_EXTENT_MM = 1.907` (check_targets.py) is close to but not derived inline from `y_size * pixel_size_mm` (≈1.9114 mm for all four current height maps, verified directly from their headers) — a reader can't tell if 1.907 is a deliberate safety margin or a stale/rounded constant. Similarly, `score = arr.size * (10 if 400 in arr.shape else 1)` in `find_thermal_array` hardcodes `400` with no comment connecting it to `EXTRACTED_THERMAL_FRAMES` (also 400, computed independently from `TARGET_GRID_N`/scan geometry) — the coincidence that both equal 400 is easy to break silently if either constant is later changed independently.
**Fix:** Add a one-line comment deriving each constant, e.g. `# slightly below y_size * pixel_size_mm (1.9114 mm) to allow interpolation margin` and `# EXTRACTED_THERMAL_FRAMES is 400; bias toward arrays whose shape already matches it`.

### IN-02: Redundant duplicate call to `resolve_output_path` on an already-resolved path

**File:** `scripts/diagnose_width_regression.py:160-166`
**Issue:**
```python
diagnostics_dir = resolve_output_path(
    project_root / "processed_data" / "targets" / "diagnostics",
    project_root,
    raw_dir,
)
diagnostics_dir.mkdir(parents=True, exist_ok=True)
diagnostics_dir = resolve_output_path(diagnostics_dir, project_root, raw_dir)
```
`resolve_output_path` already returns a fully resolved, validated path; re-passing its own output back through itself is dead/no-op code that adds noise without changing behavior.
**Fix:** Drop the second call.

---

_Reviewed: 2026-07-20T21:50:24Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
