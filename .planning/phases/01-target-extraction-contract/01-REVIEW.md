---
phase: 01-target-extraction-contract
reviewed: 2026-07-23T00:00:00Z
depth: deep
files_reviewed: 29
files_reviewed_list:
  - processed_data/diagnostics/track10_coverage_diagnosis.csv
  - processed_data/diagnostics/track10_tail_collapse_diagnosis.csv
  - processed_data/targets/extraction_params.json
  - processed_data/targets/qa/track_10_overlay.png
  - processed_data/targets/qa/track_10_residual_map.png
  - processed_data/targets/qa/track_10_width.png
  - processed_data/targets/qa/track_14_overlay.png
  - processed_data/targets/qa/track_14_residual_map.png
  - processed_data/targets/qa/track_14_width.png
  - processed_data/targets/qa/track_21_overlay.png
  - processed_data/targets/qa/track_21_residual_map.png
  - processed_data/targets/qa/track_21_width.png
  - processed_data/targets/qa/track_8_overlay.png
  - processed_data/targets/qa/track_8_residual_map.png
  - processed_data/targets/qa/track_8_width.png
  - processed_data/targets/track_10_targets.npz
  - processed_data/targets/track_14_targets.npz
  - processed_data/targets/track_21_targets.npz
  - processed_data/targets/track_8_targets.npz
  - scripts/check_targets.py
  - scripts/diagnose_track10_coverage.py
  - scripts/diagnose_track10_tail_collapse.py
  - scripts/diagnose_width_regression.py
  - scripts/run_target_extraction.py
  - src/nsf_fmrg_data.py
  - src/targets.py
  - tests/test_nsf_fmrg_data.py
  - tests/test_run_target_extraction.py
  - tests/test_targets.py
findings:
  critical: 0
  warning: 7
  info: 8
  total: 15
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-23T00:00:00Z
**Depth:** deep
**Files Reviewed:** 29
**Status:** issues_found

## Summary

This is an independent deep-depth pass over the target-extraction contract deliverable (HEAD
`48d8254`). I read every file in scope in full, ran all three test suites and `scripts/check_targets.py`
against the real, checked-in `.venv` environment (all 63 tests pass: `test_nsf_fmrg_data.py` 13/13,
`test_targets.py` 38/38, `test_run_target_extraction.py` 10/10; `check_targets.py` reports `ALL
CHECKS PASSED` against the committed `processed_data/targets/*.npz` and correctly reproduces the
documented `10 vs 14` ordering `FLAG`), then traced call chains across module boundaries
(`robust_plane_detrend`, `halfmax_edges`, `extract_track_targets`/`extract_targets_from_arrays`,
`resolve_output_path`/`publish_staging_dir`) rather than reading each file in isolation, and
independently re-derived several numeric claims against the real `data/raw/height_maps/*.ASC` data
rather than trusting prior review prose.

This codebase has already been through many prior review-and-fix cycles (visible in `git log`:
multiple `docs(01): add code review report` / `add code review fix report` commits). Comparing the
current tree against the last deep-depth pass (`2730512`) shows `src/nsf_fmrg_data.py`,
`scripts/run_target_extraction.py`, `scripts/check_targets.py`, `scripts/diagnose_width_regression.py`,
and `scripts/diagnose_track10_tail_collapse.py` are **byte-identical** to that commit — only
`scripts/diagnose_track10_coverage.py` and `src/targets.py` changed since, via the Amendment A8
boundary-tracking fix (`fbc22af`/`a51c57b`) and its disclosure comment (`3f87937`). Concretely:

- The prior pass's **WR-02** (`diagnose_track10_coverage.py`'s `production_residual_profile`
  omitting `max_xy_degree`) is now **fixed** — verified: the current file imports
  `DETREND_MAX_XY_DEGREE` and passes it into `robust_plane_detrend` (`scripts/diagnose_track10_coverage.py:71`).
- The prior pass's **WR-01** (`classify_column` drifting out of sync with `targets.halfmax_edges`)
  has **drifted again** as a direct side effect of Amendment A8 (the fix reordered clip-exclusion
  before merging and added a history-based plausibility gate that `classify_column` does not
  mirror), but this new drift is now **honestly disclosed** in a code comment
  (`scripts/diagnose_track10_coverage.py:110-125`) that accurately states the committed
  `track10_coverage_diagnosis.csv` is stale and must not be read as live production behavior. I
  verified the comment's factual claims against `src/targets.py:186-291` and they are correct. This
  is accepted, disclosed debt and is not re-flagged below as a new finding.
- Everything else the prior deep pass found (**WR-03 through WR-09**, **IN-01 through IN-07**) is
  in files that have not changed since, and I independently re-verified each is **still open** on
  the current tree (re-running the exact numeric checks against the real data where applicable —
  see WR-05 and WR-06 below, whose tables I reproduced independently rather than copying). They are
  restated below with fresh verification, renumbered for this report.
- One item I specifically investigated and **ruled out as a false lead**: I hypothesized that
  `halfmax_edges`'s boundary-crossing linear interpolation (`src/targets.py:271-287`,
  `y_lower = y0 + (threshold - z0) * (y1 - y0) / (z1 - z0)`) could divide by zero if `z0 == z1`
  exactly (plausible in principle given the ASC data's 1e-6mm quantization). Tracing the mask logic
  shows this is structurally impossible: `start`/`stop` are defined by a strict `above = prof >
  threshold` crossing, so `z0 <= threshold < z1` (or the mirror at `stop`) always holds, which
  forces `z1 != z0` by construction. Confirmed with a targeted reproduction attempt (no warning or
  NaN produced). Not included as a finding.
- One **new** issue not covered by any prior pass, in code Amendment A8 added: **IN-08** below (a
  minor internal inconsistency in the new Mechanism B history gate's length estimate).

No hardcoded secrets, injection vectors, unsafe deserialization, or `eval`/`exec` usage were found
anywhere in scope. The symlink/path-escape/raw-integrity hardening in `run_target_extraction.py`
remains thorough and test-covered for its stated threat model. No Critical/Blocker-severity finding
is warranted in this pass.

## Warnings

### WR-01: `bin_profile`'s half-open binning window still silently drops the domain's exact trailing-edge sample

**File:** `src/targets.py:124-130`
**Issue:** `columns = (x_actual_mm >= x_center - half_step) & (x_actual_mm < x_center + half_step)`
is asymmetric (`>=` on the lower bound, strict `<` on the upper bound). `load_wyko_asc`'s native
`x_actual_mm` array reaches exactly `100.0` mm for every track (verified:
`load_wyko_asc('data/raw/height_maps', 8)['x_actual_mm'][-1] == 100.0`), and the target grid's last
bin is centered at `x_center = 99.9` with `half_step = 0.1`, so the upper bound is exactly `100.0`.
The strict `<` means the single native column at `x_actual_mm == 100.0` is structurally unreachable
by any bin — it is silently excluded from the last x-slot's median rather than included. Practical
impact is currently negligible (the last bin still has well over `MIN_COLUMNS_PER_BIN=10` native
columns), but it is a real, unintentional boundary asymmetry in a codebase that is otherwise
deliberate about half-open/inclusive conventions elsewhere (e.g. `above = prof > threshold` is
consistently strict).
**Fix:** Make the window symmetric, e.g. `x_actual_mm <= x_center + half_step`, and re-verify no
native column becomes double-counted between adjacent bins (the strict upper bound was presumably
chosen to prevent exactly this, so switching to inclusive requires either also making the lower
bound of the *next* bin strict, or accepting/documenting the edge-column double count).

### WR-02: `load_wyko_asc` never validates that the `RAW_DATA` body actually supplied `x_size * y_size` rows

**File:** `src/nsf_fmrg_data.py:186-204`
**Issue:** `z_mm_flat` is NaN-filled up front (`z_mm_flat.fill(np.nan)`), and the read loop only
ever breaks early via `if count >= n_expected: break`. There is no check that a truncated or
malformed `.ASC` file actually supplied at least `n_expected` data rows before the `for line in f`
loop exhausts the file naturally. A short/corrupted height-map file would silently produce a
mostly-NaN `Z_mm` array (reshaped with the declared `x_size`/`y_size` regardless of how many rows
were actually read) instead of failing closed — inconsistent with the guard three lines above it
(`if 'x_size' not in header or 'y_size' not in header: raise ValueError(...)`) and with this same
phase's stated goal of eliminating silent-wrong-output failure modes (Amendment-era guards on
`pixel_size_mm`, the laser-on interval, filename matching, etc.).
**Fix:**
```python
Z_x_y = z_mm_flat.reshape((x_size, y_size))
if count < n_expected:
    raise ValueError(
        f'{path} RAW_DATA body supplied {count} rows, expected {n_expected} '
        f'(x_size={x_size} * y_size={y_size}).'
    )
```

### WR-03: `extract_final_thermal_frames` does not validate the extracted segment actually has `EXTRACTED_THERMAL_FRAMES` (400) frames

**File:** `src/nsf_fmrg_data.py:118-141`, specifically line 131
**Issue:** `start_idx = max(0, stop_idx - EXTRACTED_THERMAL_FRAMES)` clamps to `0` without checking
`stop_idx >= EXTRACTED_THERMAL_FRAMES`. If a thermal `.mat` file's detected laser-on interval ends
before frame 400, `segment = frames[start_idx:stop_idx]` and `x_mm_center` are silently shorter than
400 samples instead of raising. Every consumer in this codebase assumes a fixed 400-element
correspondence with `targets.target_grid()` (`tests/test_targets.py::test_target_grid_matches_thermal_centers`
derives its expected grid directly from `nsf_fmrg_data.EXTRACTED_THERMAL_FRAMES`, and the module
comment at `src/nsf_fmrg_data.py:13-16` explicitly documents this constant as load-bearing for that
correspondence). Not exercised by this phase's shipped pipeline (target extraction only touches
height maps) so it has zero current blast radius, but it is exactly the class of silent-wrong-length
bug this phase's other guards were written to prevent, and no test exercises `on_stop <
EXTRACTED_THERMAL_FRAMES`.
**Fix:**
```python
stop_idx = int(on_stop)
if stop_idx < EXTRACTED_THERMAL_FRAMES:
    raise ValueError(
        f'Laser-on interval for track {track_id} ends at frame {stop_idx}, '
        f'fewer than the required {EXTRACTED_THERMAL_FRAMES} frames.'
    )
start_idx = stop_idx - EXTRACTED_THERMAL_FRAMES
```

### WR-04: `publish_staging_dir` has no rollback if the final `staging_dir.rename(targets_dir)` step fails

**File:** `scripts/run_target_extraction.py:309-329`
**Issue:** The publish sequence is: back up the old `targets_dir` to `targets_dir.previous`, then
`staging_dir.rename(targets_dir)`. There is no `try/except` around the second rename. If it raises
(e.g. cross-device rename, disk full, permission error) after the first rename has already
succeeded, `processed_data/targets` is left **absent entirely**, with the previous generation
stranded at `targets.previous` and no automatic restore — worse than either the pre- or
post-publish state. `tests/test_run_target_extraction.py` covers symlink-rejection paths and the
happy path but does not inject a failure at this specific window.
**Fix:**
```python
if targets_dir.is_symlink() or staging_dir.is_symlink():
    raise ValueError(f"Refusing to rename a symlinked path: {staging_dir} -> {targets_dir}.")
try:
    staging_dir.rename(targets_dir)
except BaseException:
    if backup_dir.exists() and not targets_dir.exists():
        backup_dir.rename(targets_dir)
    raise
```

### WR-05: `diagnose_track10_tail_collapse.py`'s "exact CURRENT production path" comment is stale, and its committed CSV reports the pre-Amendment-A6 (uncapped-in-x) numbers, not the shipped fit

**File:** `scripts/diagnose_track10_tail_collapse.py:57-63`
**Issue:** `measure_track`'s comment reads: `# The exact CURRENT production path (Amendment A5, no
new parameter, since none exists yet): observe only the currently-shipped fit.` This predates
Amendment A6, which added `DETREND_MAX_XY_DEGREE`/`max_xy_degree` to the real production call in
`targets.extract_track_targets` (`src/targets.py:412-421`). This script's own `robust_plane_detrend`
call (lines 60-63) still omits `max_xy_degree`, and `DETREND_MAX_XY_DEGREE` is not in its import
list (lines 17-22) — only `DETREND_MAX_Y_DEGREE` is imported. I independently re-derived the
`departure` metric with and without `max_xy_degree=DETREND_MAX_XY_DEGREE` against the real,
checked-in `data/raw/height_maps/*.ASC` files:

| track | as currently coded (no `max_xy_degree`) | actual production path (`max_xy_degree=2`) |
|---|---|---|
| 8  | 0.006038 | 0.003761 |
| 10 | 0.021200 | 0.011843 |
| 14 | 0.0000539 | 0.0001700 |
| 21 | 0.006166 | 0.005772 |

The committed `processed_data/diagnostics/track10_tail_collapse_diagnosis.csv` row for track 10
(`departure=0.021199873273603273`) matches the *stale* column exactly, not the real production value
(`0.011843`) — the number `src/targets.py:50-56`'s Amendment A6 comment cites as clearing the
0.012mm criterion tolerance. The checked-in diagnostic artifact for the exact metric that justified
a locked, load-bearing constant is one full amendment out of date, and its own inline comment
affirmatively (and now falsely) claims otherwise.
**Fix:** Import `DETREND_MAX_XY_DEGREE`, pass `max_xy_degree=DETREND_MAX_XY_DEGREE` in the
`robust_plane_detrend` call, correct the stale comment, and regenerate
`track10_tail_collapse_diagnosis.csv`. (Same category of drift as `diagnose_track10_coverage.py`'s
now-disclosed staleness — this sibling script has neither been fixed nor disclosed.)

### WR-06: `robust_plane_detrend`'s 3-round trim/refit loop discards its final trim decision

**File:** `src/nsf_fmrg_data.py:263-273`
**Issue:**
```python
keep = valid.copy()
coef = None
for _ in range(3):
    coef, *_ = np.linalg.lstsq(A[keep], z[keep], rcond=None)
    resid = z - A @ coef
    rv = resid[valid]
    lo, hi = np.nanpercentile(rv, [5, 95])
    keep_new = valid & (resid >= lo) & (resid <= hi)
    if keep_new.sum() < 100:
        break
    keep = keep_new
```
Each iteration fits with the *current* `keep`, then computes `keep_new` for the *next* iteration.
After the loop's third and final iteration, `keep` is updated to `keep_new`, but the loop ends —
`coef` is never refit against that final, most-trimmed `keep`. The function returns coefficients
from a fit that reflects only 2 of the 3 apparent trim cycles; the third trim's entire purpose
(informing a refit) is computed and then discarded. I independently reproduced this against the
real, checked-in height-map data by adding one explicit final refit and comparing the resulting
fitted plane to the shipped `order=4, max_y_degree=2, max_xy_degree=2` production configuration:

| track | max \|plane(with final refit) − plane(shipped)\| (mm) |
|---|---|
| 8  | 0.0017 |
| 10 | 0.0050 |
| 14 | 0.0029 |
| 21 | 0.0078 |

Track 21's discrepancy is ~65% of the 0.012mm `DETREND_MAX_XY_DEGREE` edge-shape-gap tolerance that
Amendment A6 locked via measurement (`src/targets.py:42-57`), and is not negligible next to the
margins those amendments were tuned against. This is a genuine off-by-one in the loop's control
flow, not a documented "stop one short" design choice.
**Fix:** Either perform an explicit final refit using the last `keep` after the loop, or reduce the
loop to `range(2)` so the effective iteration count matches what the code implies. Either way,
re-measure and re-lock the Amendment A4/A5/A6 tolerance margins against the corrected fit, since the
fix itself measurably moves the fitted surface by amounts comparable to those margins.

### WR-07: `diagnose_width_regression.py`'s sweep never applies the shipped `DETREND_MAX_Y_DEGREE`/`DETREND_MAX_XY_DEGREE` caps, so no row reproduces the real production configuration

**File:** `scripts/diagnose_width_regression.py:107-131`, specifically lines 116-119
**Issue:** `run_sweep` calls `robust_plane_detrend(data['Z_mm'], data['x_actual_mm'], data['y_mm'],
order=order, fit_mask=fit_mask)` for every `(order, bead_mask)` combination — neither `max_y_degree`
nor `max_xy_degree` is ever passed, and neither `DETREND_MAX_Y_DEGREE` nor `DETREND_MAX_XY_DEGREE`
is imported. This means no row of the checked-in `processed_data/diagnostics/width_regression_sweep.csv`
(currently untracked in git, unlike its two sibling diagnostic CSVs) corresponds to what
`targets.extract_track_targets` actually ships — including the row a reader would most naturally
mistake for "the production config" (`order=4, continuity=True, bead_mask=True`). Re-running
`scripts/check_targets.py` against the real, committed `processed_data/targets/*.npz` gives
`track_8=0.7653, track_10=0.3940, track_14=0.7122, track_21=0.6308` (this review's own re-run,
printed above); the uncapped `order=4` sweep row reports materially different medians for the same
tracks, since it omits the caps that were the actual Amendment A5/A6 fix for the width-ordering
regression this script's own module docstring says it diagnoses.
**Fix:** Add a dedicated "actual production" row/column that applies
`DETREND_MAX_Y_DEGREE`/`DETREND_MAX_XY_DEGREE` alongside `order=DETREND_POLY_ORDER`, or at minimum
add an explicit comment/CSV column stating every row is deliberately uncapped and therefore not
comparable to the shipped artifacts — then either commit `width_regression_sweep.csv` alongside its
siblings or add it to `.gitignore`.

## Info

### IN-01: Unused `import json` in `src/nsf_fmrg_data.py`

**File:** `src/nsf_fmrg_data.py:3`
**Issue:** `json` is imported at module scope and never referenced anywhere in the file (`grep -n
"json\." src/nsf_fmrg_data.py` finds nothing).
**Fix:** Remove the unused import.

### IN-02: The three `scripts/diagnose_*.py` files duplicate `write_csv`/table-printing helpers verbatim

**File:** `scripts/diagnose_track10_coverage.py:283-296`, `scripts/diagnose_track10_tail_collapse.py:78-91`, `scripts/diagnose_width_regression.py:150-161`
**Issue:** All three scripts define near-identical `print_measurement_table`/`write_csv` (or
`print_sweep_table`/`write_sweep_csv`) helpers, plus a verbatim-repeated "diagnostics/ is a SIBLING
of targets/, not a child" comment explaining the same publish-collision hazard.
**Fix:** Extract a shared `scripts/_diagnostic_io.py` helper module.

### IN-03: Redundant `.copy()` calls in `finalize_smoothed_boundaries`

**File:** `src/targets.py:315-323`
**Issue:** `y_lower = nan_savgol(y_lower_raw)` / `y_upper = nan_savgol(y_upper_raw)` already return
freshly allocated arrays (`nan_savgol` builds `out = np.full(len(v), np.nan, ...)` internally); the
subsequent `y_lower = y_lower.copy()` / `y_upper = y_upper.copy()` are dead copies of arrays nothing
else references.
**Fix:** Remove the redundant `.copy()` calls.

### IN-04: `Y_STRIP_EXTENT_MM` in `scripts/check_targets.py` is a hardcoded constant, not derived per-track from the header at check time

**File:** `scripts/check_targets.py:24-30`
**Issue:** The `1.907` mm bound is documented as derived from `y_size * pixel_size_mm = 480 *
0.003982 = 1.91136 mm for all four current Heightmap_*.ASC headers`, but is not re-derived from
each track's actual header at check time. If a future track's height map used a different
`pixel_size_mm` or `y_size`, this constant would silently become the wrong bound instead of failing
loudly or adapting.
**Fix (optional):** Derive per-track from `load_wyko_asc`'s header at check time, or load the four
raw headers here and cross-check them against the hardcoded constant instead of trusting it blind.

### IN-05: `scripts/check_targets.py` duplicates the target-grid start value as a bare literal alongside its own authoritative check

**File:** `scripts/check_targets.py:67-73`
**Issue:** `require(np.isclose(x_grid_mm[0], 20.1), ...)` hardcodes `20.1` even though the very next
check (`require(np.allclose(x_grid_mm, target_grid()), ...)`) already validates the persisted grid
against the authoritative `targets.target_grid()`/`TARGET_GRID_START_MM`. If
`TARGET_GRID_START_MM` were ever changed, this literal would drift out of sync with the constant it
is meant to be checking (the redundant `target_grid()` check would still catch a real mismatch, but
this specific, more readable error message would fire for the wrong stated reason).
**Fix (optional):** Replace the literal with `targets.TARGET_GRID_START_MM` (importable from
`src/targets.py`, already imported indirectly via `target_grid`).

### IN-06: Track 10 vs. Track 14 median width violates the expected power-monotonic ordering (documented, not a code defect)

**File:** `processed_data/targets/track_10_targets.npz`, `processed_data/targets/track_14_targets.npz`
**Issue:** Re-confirmed by re-running `scripts/check_targets.py` against the live, committed
artifacts in this review: Track 10 (350W) median width `0.3940mm` is less than Track 14 (300W)
`0.7122mm`, printed by the code's own ordering check as `FLAG`, and explicitly documented in
`targets.print_results` as never used to tune locked extraction constants.
**Fix:** None required for this phase; carry the caveat forward into downstream (Phase 2+)
documentation and modeling assumptions.

### IN-07: `resolve_raw_dir` is validated twice on every invocation

**File:** `scripts/run_target_extraction.py:35-59`
**Issue:** `resolve_repository_root` calls `resolve_raw_dir(candidate)` (line 48) purely for its
validating side effect and discards the result; every caller (`run_pipeline` at line 339,
`scripts/check_targets.py:120`, and all three `diagnose_*` scripts) then calls `resolve_raw_dir(project_root)`
again immediately afterward. Harmless (idempotent, cheap) but is duplicated validation work with no
comment explaining the intentional redundancy.
**Fix:** Either have `resolve_repository_root` return `(project_root, raw_dir)` so callers reuse the
already-validated `raw_dir`, or drop the internal call and document that raw-dir validation is the
caller's responsibility.

### IN-08 (new): Amendment A8's Mechanism B history gate estimates a candidate's `length_mm` one grid step shorter than how `previous_length_mm` itself is computed

**File:** `src/targets.py:248-254`
**Issue:** `_is_implausible_versus_history` computes `length_mm = y_mm[stop - 1] - y_mm[start]` for
a half-open candidate run `[start, stop)`, i.e. `(stop - start - 1) * dy`. But the caller
(`extract_targets_from_arrays`, `src/targets.py:386-387`) derives `previous_length_mm` from the
*actual returned edges* (`edges[1] - edges[0]`), which are linearly interpolated roughly half a
native pixel beyond both `start` and `stop`, approximating `(stop - start) * dy` — one grid step
longer than the estimate used inside the plausibility gate. With `dy` on the order of `0.004mm` and
observed `previous_length_mm` values ranging roughly `0.1`–`1.4mm` (per the checked-in QA width
plots), this is a small (~0.3%–4%) systematic underestimate of every candidate's length when
compared against `MIN_TRACKED_LENGTH_RATIO * previous_length_mm`, which could tip a genuinely
borderline candidate (one sitting right at the 0.5x ratio) from "plausible" to "implausible" purely
due to this internal inconsistency rather than a genuine size difference. Not exercised by name in
any of the Amendment A8 regression tests (`tests/test_targets.py`'s Mechanism B tests all use
candidates far from the 0.5x boundary).
**Fix:** Use the same span convention as the caller, e.g. `length_mm = y_mm[stop] - y_mm[start]` if
`stop < len(y_mm)` (guaranteed by the non-edge-run filter earlier in this same function), so the
gate's internal length estimate matches `previous_length_mm`'s own derivation.

---

_Reviewed: 2026-07-23T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
