---
phase: 01-target-extraction-contract
reviewed: 2026-07-21T17:19:38Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - scripts/check_targets.py
  - scripts/diagnose_track10_coverage.py
  - scripts/diagnose_width_regression.py
  - scripts/run_target_extraction.py
  - src/nsf_fmrg_data.py
  - src/targets.py
  - tests/test_nsf_fmrg_data.py
  - tests/test_run_target_extraction.py
  - tests/test_targets.py
findings:
  critical: 0
  warning: 6
  info: 2
  total: 8
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-21T17:19:38Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

This is a fresh, independent pass over the same nine files reviewed on 2026-07-20T21:50:24Z, plus `scripts/diagnose_track10_coverage.py` (new since that pass). It does not assume the four gap-closure plans (01-09..01-12) actually fixed what they claim; each of the prior review's three CRITICALs and three WARNINGs was independently re-verified against the real repository and real data, not just re-read.

**Verification method:** all three test suites were run in the project's `.venv` (38+12+10 = all tests pass), and — going beyond "tests pass" — the actual production pipeline was executed end-to-end against the real `data/raw/` dataset (`scripts/run_target_extraction.py --project_dir .` followed by `scripts/check_targets.py --project_dir .`), plus both diagnostic scripts, to observe real behavior rather than trust the diff.

**Prior CRITICALs — confirmed fixed:**
- **CR-01** (track 10 95% invalid coverage): re-running the real pipeline now yields track 10 = 242/400 valid (60.5%), not 21/400 (5.25%). The `DETREND_MAX_Y_DEGREE = 2` cross-track degree cap (Amendment A5) genuinely resolves the edge-manufactured-feature mechanism that was destroying track 10's coverage.
- **CR-02** (weak coverage gate): `scripts/check_targets.py` now hard-`require()`s `valid_fraction >= MIN_VALID_FRACTION` (0.5); a real run against the regenerated artifacts passes this gate honestly (all four tracks clear 0.5).
- **CR-03** (symlink-following `rmtree`): `reject_symlink_path()` plus per-step `is_symlink()` checks are now present at every stage of `publish_staging_dir`; `tests/test_run_target_extraction.py`'s four symlink-attack regression tests all pass, including the specific `targets.previous`-symlink and `processed_data`-symlink scenarios the prior review reproduced as live exploits.

**Prior WARNINGs — confirmed fixed:** WR-01 (`find_track_file`'s no-op regex fallback removed — verified via `test_find_track_file_rejects_unanchored_substring_match`), WR-02 (thermal loader now enforces `Thermal_{track_id}.mat` exact-name; SEM loader now rejects symlinked track dirs — verified via tests), WR-03 for `diagnose_width_regression.py` specifically (bead-mask axis added — but see new WARNING below, since the fix did not extend to the newer `DETREND_MAX_Y_DEGREE` parameter).

Despite the real, verified progress above, this pass surfaced **new problems introduced by, or left unaddressed by, the fix commits themselves** — mostly around the two diagnostic scripts silently diverging from the production path they exist to characterize, and validation/defense-in-depth gaps that are inconsistent with the rigor applied elsewhere in the same fix commits. None of these rise to the level of "the shipped pipeline produces wrong targets" — that specific risk (CR-01/02/03) is genuinely closed — but several are real, reproduced defects a future engineer would trip over.

## Warnings

### WR-01: `diagnose_track10_coverage.py`'s "production" path omits `DETREND_MAX_Y_DEGREE` and reports numbers 10x worse than what production actually produces

**File:** `scripts/diagnose_track10_coverage.py:60-64` (`production_residual_profile`)
**Issue:** This file was added in the same commit sequence (01-11) that introduced `DETREND_MAX_Y_DEGREE` as the fix for track 10's coverage collapse, yet its own `production_residual_profile()` — the function whose docstring-equivalent name claims to model "the current locked pipeline" — calls:
```python
Zd, coef = robust_plane_detrend(
    Z_mm, x_actual_mm, y_mm, order=DETREND_POLY_ORDER, fit_mask=fit_mask,
)
```
with no `max_y_degree=DETREND_MAX_Y_DEGREE`. `rejection_reason_histogram()` and `fitted_surface_edge_report()` both operate on this same under-parameterized `Zd`. I ran this diagnostic against the real dataset and it reports `rejection_ok=21` (5.25% valid) for track 10 — while the actual production run (`scripts/run_target_extraction.py` → `scripts/check_targets.py`, same real data, same day) reports 242/400 valid (60.5%). A future engineer re-running this "coverage diagnosis" tool to investigate a regression would see track 10 apparently still catastrophically broken and either waste time re-diagnosing an already-fixed problem, or lose confidence in a fix that is in fact working.
**Fix:**
```python
from targets import DETREND_MAX_Y_DEGREE, ...

def production_residual_profile(Z_mm, x_actual_mm, y_mm):
    fit_mask = bead_exclusion_mask(Z_mm)
    Zd, coef = robust_plane_detrend(
        Z_mm, x_actual_mm, y_mm, order=DETREND_POLY_ORDER,
        fit_mask=fit_mask, max_y_degree=DETREND_MAX_Y_DEGREE,
    )
```

### WR-02: `diagnose_width_regression.py`'s sweep still never applies `DETREND_MAX_Y_DEGREE`, so even its "production-labeled" row diverges from real output

**File:** `scripts/diagnose_width_regression.py:107-131` (`run_sweep`)
**Issue:** The prior review's WR-03 ("no longer reflects the production detrend path") was fixed for the *bead-mask* axis (a `BEAD_MASK_OPTIONS` sweep dimension was added, with a comment stating `bead_mask=True` rows "exercise the production detrend path"). But `robust_plane_detrend(...)` inside `run_sweep` is still called without `max_y_degree`, so the row the script's own comment labels as production-equivalent (`order=4, continuity=True, bead_mask=True`) is not actually production-equivalent post-Amendment-A5. Verified by execution: that row reports track 10 median width 0.2509 mm, while the real, current production output (via `check_targets.py` against freshly regenerated artifacts) is 0.3713 mm — a ~48% relative difference that would look like a regression to anyone comparing this sweep's "production" row against the live pipeline.
**Fix:** Add a `max_y_degree` sweep axis (or at minimum apply `DETREND_MAX_Y_DEGREE` unconditionally on `bead_mask=True` rows, mirroring how `bead_mask` gates `fit_mask`), and update the module comment (`BEAD_MASK_OPTIONS` docstring-comment at lines 39-42) accordingly — it currently claims `bead_mask=True` rows exercise "the production detrend path," which is no longer true.

### WR-03: Thermal and height-map loaders resolve through `find_track_file` with no symlink rejection, unlike every other data-touching path in this codebase

**File:** `src/nsf_fmrg_data.py:118-124` (`extract_final_thermal_frames`), `173-177` (`load_wyko_asc`)
**Issue:** `get_sem_tile_paths` explicitly rejects a symlinked `SEM_{track_id}`/`PlainImages` directory (`root.is_symlink() or root.parent.is_symlink()`), and the entire write path in `run_target_extraction.py` now has extensive, tested symlink defenses (`reject_symlink_path`, `snapshot_raw`'s escape check). But the two `find_track_file`-based read loaders have no equivalent: `find_track_file` uses `p.is_file()` (which follows symlinks) with no `p.is_symlink()` check, so a symlinked `Thermal_10.mat` or `Heightmap_10.ASC` under `data/raw/` pointing anywhere else on the filesystem would be silently matched, opened, and its target's bytes parsed as thermal/height data — with no error and no indication in the returned dict that the file was a symlink. Given how much deliberate effort the same fix commits invested in symlink defense elsewhere (CR-03, WR-02), this is a real gap in the read path that would be simple to close and is inconsistent with the codebase's own established threat model.
**Fix:** Reject symlinks in `find_track_file` itself:
```python
for p in root.rglob('*'):
    if p.is_file() and not p.is_symlink() and p.suffix.lower() in suffixes:
        ...
```

### WR-04: `load_wyko_asc` has no exact-filename guard of its own and silently defaults a missing `pixel_size_mm` header — both diagnostic scripts call it directly and get neither protection

**File:** `src/nsf_fmrg_data.py:173-180` (`load_wyko_asc`) vs. `src/targets.py:299-306` (`extract_track_targets`)
**Issue:** `extract_final_thermal_frames` enforces its exact-name check (`Thermal_{track_id}.mat`) *inside itself*, so every caller gets the protection automatically. `load_wyko_asc` has no equivalent internal check — the `Heightmap_{track_id}.ASC` exact-name assertion only exists in `targets.extract_track_targets`, one layer up. `scripts/diagnose_track10_coverage.py:measure_track` and `scripts/diagnose_width_regression.py:run_sweep` both call `load_wyko_asc(height_dir, track_id)` directly and never re-check the resolved filename, so if `find_track_file` ever resolves an unintended `.ASC`/`.txt` file for either diagnostic, there is no error — it silently analyzes the wrong file. The same function also does `pixel = float(header.get('pixel_size_mm', 0.003982))`, silently substituting a hardcoded default if the header field is absent, rather than raising; `extract_track_targets` only catches this *after* `load_wyko_asc` has already used the (possibly wrong) default to build every coordinate array in its result, and neither diagnostic script re-checks it at all.
**Fix:** Move the exact-filename assertion and the `pixel_size_mm`-presence check into `load_wyko_asc` itself (as `extract_final_thermal_frames` already does for `.mat` files), so every caller — production and diagnostic alike — gets the same guarantee without having to duplicate it.

### WR-05: `robust_plane_detrend`'s `order`/`max_y_degree` validation runs after the degenerate-data early return, so invalid parameter values are silently swallowed instead of raising

**File:** `src/nsf_fmrg_data.py:220-236`
**Issue:**
```python
if valid.sum() < 100:
    return Z_mm.copy(), None

if not isinstance(order, (int, np.integer)) or order < 0:
    raise ValueError('order must be a non-negative integer.')
if max_y_degree is not None and (not isinstance(max_y_degree, (int, np.integer)) or max_y_degree < 0):
    raise ValueError('max_y_degree must be a non-negative integer or None.')
```
The `order`/`max_y_degree` type/value checks are placed *after* the `valid.sum() < 100` early return. Reproduced directly:
```python
>>> robust_plane_detrend(Z_mm, x_mm, y_mm, stride_x=1, stride_y=5, order=-1)
(array unchanged, None)   # no ValueError raised
>>> robust_plane_detrend(Z_mm, x_mm, y_mm, stride_x=1, stride_y=5, order=4, max_y_degree=-5)
(array unchanged, None)   # no ValueError raised
```
Whenever the strided/masked sample count for a given call happens to fall below 100 (a real, data-dependent condition — this is exactly the "degenerate fallback" path that `tests/test_nsf_fmrg_data.py::test_degenerate_fallback_is_preserved_for_all_orders` exercises, just never with an invalid `order`), a caller passing a malformed `order` or `max_y_degree` gets a silent `None` coefficient instead of the explicit `ValueError` the function is supposed to guarantee. Current production call sites always pass a hardcoded, correct `order=4`/`max_y_degree=2`, so this does not affect the shipped pipeline today, but it is a genuine validation-ordering bug in a function that is called directly by two diagnostic scripts and notebooks with programmatically-constructed `order` values (`diagnose_width_regression.py`'s `DETREND_ORDERS = (1, 2, 4)` sweep).
**Fix:** Move the `order`/`max_y_degree` validation above the `valid.sum() < 100` check, so it runs unconditionally regardless of data shape:
```python
if not isinstance(order, (int, np.integer)) or order < 0:
    raise ValueError('order must be a non-negative integer.')
if max_y_degree is not None and (not isinstance(max_y_degree, (int, np.integer)) or max_y_degree < 0):
    raise ValueError('max_y_degree must be a non-negative integer or None.')

... # existing valid/fit_mask computation
if valid.sum() < 100:
    return Z_mm.copy(), None
```

### WR-06: `bin_profile`'s `np.nanmedian` over all-NaN slices emits an uncontrolled `RuntimeWarning` on every real pipeline run

**File:** `src/targets.py:93-99` (`bin_profile`)
**Issue:** `np.nanmedian(Zd[:, columns], axis=1)` computes a per-row median across the columns selected for one x-bin. When a given y-row is entirely `NaN` across all selected columns (which happens for real data — bad/masked profilometer pixels), NumPy raises `RuntimeWarning: All-NaN slice encountered` for that row and returns `NaN`, which is the intended, correctly-handled behavior downstream (`fill_small_gaps`/`halfmax_edges` treat `NaN` correctly). Verified: every real run of `scripts/run_target_extraction.py`, `scripts/check_targets.py`, and both diagnostic scripts prints this warning to stderr on the very first line of output. Nothing filters, catches, or documents it, so it looks identical to an actual error in CI logs / terminal output for a codebase whose other paths are otherwise scrupulous about fail-closed, explicit signaling (e.g. the raw-integrity audit, the symlink guards). A maintainer skimming a log for the fail-closed `RuntimeError`/`ValueError` messages this pipeline is designed to emit could easily mistake this warning for one of them, or conversely start ignoring warnings from this script generally.
**Fix:** Either explicitly suppress the specific, expected warning with a documented `with warnings.catch_warnings(): warnings.filterwarnings("ignore", r"All-NaN slice encountered")` around the `np.nanmedian` call, or precompute the all-NaN rows and pass them through directly rather than relying on NumPy's warning-then-NaN behavior.

## Info

### IN-01: `import json` in `src/nsf_fmrg_data.py` is unused

**File:** `src/nsf_fmrg_data.py:3`
**Issue:** `import json` is present at module scope but `json` is never referenced anywhere in the file (confirmed via AST analysis — no `Name` node resolves to `json`). Dead import.
**Fix:** Remove the unused import.

### IN-02: `diagnose_track10_coverage.py` reintroduces the exact redundant `resolve_output_path` pattern that was removed from `diagnose_width_regression.py`

**File:** `scripts/diagnose_track10_coverage.py:279-285`
**Issue:** The prior review's IN-02 flagged an identical pattern in `diagnose_width_regression.py` (re-passing an already-resolved, already-created directory back through `resolve_output_path`) as dead/no-op noise, and that specific instance was since removed from `diagnose_width_regression.py`. `diagnose_track10_coverage.py` — a new file added after that fix — has the same pattern:
```python
diagnostics_dir = resolve_output_path(
    project_root / "processed_data" / "diagnostics",
    project_root,
    raw_dir,
)
diagnostics_dir.mkdir(parents=True, exist_ok=True)
diagnostics_dir = resolve_output_path(diagnostics_dir, project_root, raw_dir)
```
Not a functional bug (the second call is a no-op given the first call already fully resolved and validated the path), but it is an inconsistency: the exact pattern this project already decided to clean up in one file was reintroduced, unreviewed, in its sibling.
**Fix:** Drop the second `resolve_output_path` call, matching `diagnose_width_regression.py`'s current form.

---

_Reviewed: 2026-07-21T17:19:38Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
