# Phase 1: Target Extraction & Contract - Pattern Map

**Mapped:** 2026-07-19
**Files analyzed:** 4 new files
**Analogs found:** 3 / 4

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/targets.py` | library module (pure extraction functions + constants) | batch/transform (array in → dict out) | `src/nsf_fmrg_data.py` | exact (role + data flow) |
| `scripts/run_target_extraction.py` | CLI batch script (run 4 tracks, persist `.npz` + QA figures) | batch, file I/O | `scripts/run_thermal_video_export.py` | exact (role + data flow) |
| `scripts/check_targets.py` | assertion/verification script over persisted artifacts | file I/O, request-response (assert + print) | `scripts/run_thermal_video_export.py` | role-match (CLI script pattern; no assertion script exists yet) |
| `processed_data/targets/` artifacts (`track_{id}_targets.npz`, `extraction_params.json`, `qa/*.png`) | data artifacts | file I/O output | `processed_data/videos/` output pattern in `scripts/run_thermal_video_export.py:25-28` | partial (directory-creation pattern only) |

Note: `src/nsf_fmrg_data.py` is **not modified** — D-13/D-16 lock `robust_plane_detrend()` as-is; new code imports it.

## Pattern Assignments

### `src/targets.py` (library module, array transform)

**Analog:** `src/nsf_fmrg_data.py` (the only library module; new module must mirror it exactly)

**Imports pattern** (`src/nsf_fmrg_data.py:1-6`) — stdlib first, then third-party, flat, no relative imports:
```python
from pathlib import Path
import re
import json
import numpy as np
from scipy.io import loadmat
from PIL import Image, ImageOps
```
For `targets.py`: `import numpy as np` plus `from nsf_fmrg_data import load_wyko_asc, robust_plane_detrend, largest_true_run, COMMON_X_START_MM, COMMON_X_END_MM` (flat sibling import works because consumers add `src/` to `sys.path` — see script pattern below).

**Module-level constants pattern** (`src/nsf_fmrg_data.py:8-13`) — SCREAMING_SNAKE_CASE, unit-suffixed, derived constants computed inline at module level:
```python
COMMON_X_START_MM = 20.0
COMMON_X_END_MM = 100.0
THERMAL_FPS = 50.0
SCAN_SPEED_MM_PER_S = 10.0
THERMAL_MM_PER_FRAME = SCAN_SPEED_MM_PER_S / THERMAL_FPS
EXTRACTED_THERMAL_FRAMES = int(round((COMMON_X_END_MM - COMMON_X_START_MM) / THERMAL_MM_PER_FRAME))
```
Apply for the contract constants block (RESEARCH Pattern 2): `TARGET_GRID_START_MM = 20.1`, `TARGET_GRID_STEP_MM = 0.2`, `TARGET_GRID_N = 400`, `BASELINE_PCT`, `PEAK_PCT`, `HALF_MAX_FRACTION`, `MIN_PEAK_BASELINE_SEPARATION_MM = 0.005`, `MAX_GAP_PIXELS = 10`, `SG_WINDOW_PTS = 5`, `SG_POLYORDER = 2`, `MIN_VALID_Y_POINTS`. Grid must match the thermal center formula at `src/nsf_fmrg_data.py:123`: `x_mm_center = COMMON_X_END_MM - ((stop_idx - indices) - 0.5) * THERMAL_MM_PER_FRAME` → centers 20.1…99.9.

**Function style** — snake_case verb-first, **no type hints, no docstrings**, single blank line between functions, sparse comments only for non-obvious intent (e.g. `robust_plane_detrend`, `extract_final_thermal_frames`).

**Core pattern: run-length detection** (`src/nsf_fmrg_data.py:88-97`) — reuse/adapt this for NaN-gap runs (D-05/D-06) and largest above-threshold run (half-max edges); the "Don't Hand-Roll" table in RESEARCH points here explicitly:
```python
def largest_true_run(mask):
    mask = np.asarray(mask, dtype=bool)
    if not mask.any():
        return None, None
    idx = np.flatnonzero(mask)
    breaks = np.where(np.diff(idx) > 1)[0]
    starts = np.r_[idx[0], idx[breaks + 1]]
    stops = np.r_[idx[breaks] + 1, idx[-1] + 1]
    j = int(np.argmax(stops - starts))
    return int(starts[j]), int(stops[j])
```

**Core pattern: robust percentile-based thresholding** (`src/nsf_fmrg_data.py:100-111`, `detect_laser_on_interval`) — model for the half-max threshold logic (compute stats, derive threshold, boolean mask, largest run):
```python
def detect_laser_on_interval(frames):
    score = thermal_frame_score(frames)
    ...
    range_thr = np.nanmin(score) + 0.20 * (np.nanmax(score) - np.nanmin(score))
    ...
    mask = score > threshold
    on_start, on_stop = largest_true_run(mask)
    return on_start, on_stop, score, threshold
```

**Core pattern: iterative robust lstsq with percentile trimming** (`src/nsf_fmrg_data.py:205-227`, `robust_plane_detrend`) — called unchanged with default `stride_x=40, stride_y=2` per D-13/D-16. Signature: `robust_plane_detrend(Z_mm, x_mm, y_mm, stride_x=40, stride_y=2)` → returns `(Z_detrended, coef)`; note its degenerate fallback returns `(Z_mm.copy(), None)` when `<100` valid samples (line 213-214) — caller should fail fast if `coef is None`.

**Dict-return pattern** (`src/nsf_fmrg_data.py:199-202`, `load_wyko_asc` return):
```python
return {
    'file': str(path), 'header': header, 'Z_mm': Z_yx,
    'x_actual_mm': x_actual, 'x_local_mm': x_local_sorted, 'y_mm': y_mm,
}
```
Extraction entry point returns the analogous bundle: `{'track_id', 'file', 'x_grid_mm', 'w_mm', 'y_upper_mm', 'y_lower_mm', 'valid_mask'}` (RESEARCH Pattern 3). Input consumed: `load_wyko_asc` result keys `'Z_mm'` (y,x float32 grid, NaN='Bad'), `'x_actual_mm'`, `'y_mm'`.

**Error handling pattern** (`src/nsf_fmrg_data.py:71`) — fail-fast built-in exceptions with explicit messages, no custom classes:
```python
raise ValueError('No thermal-like array found in MAT file.')
```

**Matrix naming** — math notation with capitals for grids: `Z_yx`, `Z_x_y` (`src/nsf_fmrg_data.py:185-186`); use e.g. `Zd` for detrended map, plain snake_case for 1-D arrays (`x_actual_mm`, `y_mm`, `prof`).

---

### `scripts/run_target_extraction.py` (CLI batch script, file I/O)

**Analog:** `scripts/run_thermal_video_export.py` (only existing script; copy its structure wholesale)

**Imports + sys.path pattern** (lines 1-13) — copy verbatim, adjusting the import line:
```python
from pathlib import Path
import argparse
import sys
import matplotlib.pyplot as plt
from matplotlib import animation

# Allow running from repo root without installing as a package.
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from nsf_fmrg_data import extract_final_thermal_frames
```
(New script imports from `targets` instead; keep the same comment.)

**Script-level display constants** (lines 15-18) — plot-only constants live at top of the script, not the library:
```python
THERMAL_CMAP = "jet"
THERMAL_VMIN = 1000.0
THERMAL_VMAX = 2500.0
THERMAL_PIXEL_SIZE_MM = 0.014
```

**Typed entry-point signature** (line 21) — type hints on script public functions ONLY (library stays untyped):
```python
def save_video(project_dir: Path, track_id: int, fps: int = 10) -> Path:
```
New script: e.g. `def run_track(project_dir: Path, track_id: int) -> Path:`.

**Output directory + path construction** (lines 22-28) — the pattern for `processed_data/targets/` and `qa/`:
```python
thermal_dir = project_dir / "data" / "raw" / "thermal"
result = extract_final_thermal_frames(thermal_dir, track_id)

out_dir = project_dir / "processed_data" / "videos"
out_dir.mkdir(parents=True, exist_ok=True)

out_path = out_dir / f"Track_{track_id}_thermal_20to100mm.mp4"
```

**Figure lifecycle** (lines 39-51, 68) — create fig, label with units-in-name axes, `plt.close(fig)` after save:
```python
fig, ax = plt.subplots(figsize=(5, 5))
im = ax.imshow(frames[0], cmap=THERMAL_CMAP, vmin=THERMAL_VMIN, vmax=THERMAL_VMAX, extent=extent)
title = ax.set_title(f"Track {track_id} | x ≈ {x_mm[0]:.1f} mm")
ax.set_xlabel("thermal local x (mm)")
ax.set_ylabel("thermal local y (mm)")
...
plt.close(fig)
```

**argparse + main pattern** (lines 73-85) — copy structure; `--project_dir` default `Path(".")`, `print()` feedback only (no `logging`):
```python
def main():
    parser = argparse.ArgumentParser(description="Export thermal videos for one NSF FMRG track.")
    parser.add_argument("--project_dir", type=Path, default=Path("."), help="Repository/project root.")
    parser.add_argument("--track_id", type=int, default=8, help="Track ID, e.g., 8, 10, 14, or 21.")
    ...
    out_path = save_video(args.project_dir.resolve(), args.track_id, args.fps)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
```
New script loops all 4 tracks (8, 10, 14, 21) by default, prints summary table and raw-data prohibition PASS/FAIL via `print()`.

**Style note:** this script uses double blank lines between top-level defs (vs single in the library) — match per-file convention.

---

### `scripts/check_targets.py` (assertion script)

**Analog:** `scripts/run_thermal_video_export.py` (role-match — no test/assert script exists; reuse the same skeleton)

Copy: sys.path block (lines 7-11), argparse `--project_dir` (lines 74-75), `print()` output (line 81), typed entry-point signature convention (line 21). Body loads `processed_data/targets/track_{id}_targets.npz` via `np.load` and uses plain `assert`/`raise ValueError('...')` fail-fast (library error style, `src/nsf_fmrg_data.py:71`) — no pytest (RESEARCH Validation Architecture: assertion scripts, not a test framework).

---

### `processed_data/targets/` artifacts

**Analog:** output-directory creation at `scripts/run_thermal_video_export.py:25-26` (`out_dir.mkdir(parents=True, exist_ok=True)`). Persist with `np.savez` (float64 — note `load_wyko_asc` allocates float32 at `src/nsf_fmrg_data.py:167`; cast up at persistence per RESEARCH anti-pattern). Write `extraction_params.json` via stdlib `json` (already imported in the library at `src/nsf_fmrg_data.py:3` — precedent for json use).

---

## Shared Patterns

### sys.path bootstrap (no packaging)
**Source:** `scripts/run_thermal_video_export.py:7-11`
**Apply to:** both new scripts (verbatim, including the comment).

### Fail-fast error handling
**Source:** `src/nsf_fmrg_data.py:71` (`raise ValueError('No thermal-like array found in MAT file.')`)
**Apply to:** all new files. Built-in exceptions, explicit messages, no custom exception classes, no broad try/except. Also assert exact filename resolution per RESEARCH threat table: after `find_track_file`, assert `Path(result['file']).name == f'Heightmap_{track_id}.ASC'`-style check (guards Pitfall 4 substring fallback at `src/nsf_fmrg_data.py:28`).

### Dict-return convention
**Source:** `src/nsf_fmrg_data.py:124-130` and `:199-202`
**Apply to:** every new library function returning multi-field results — plain dict with `'file'`, coordinate arrays, primary data array; keys unit-suffixed (`_mm`).

### Print-only CLI feedback
**Source:** `scripts/run_thermal_video_export.py:81` (`print(f"Saved: {out_path}")`)
**Apply to:** both scripts. No `logging` module.

### Constants convention
**Source:** `src/nsf_fmrg_data.py:8-13`
**Apply to:** `src/targets.py` (contract constants) and script-level plot constants. SCREAMING_SNAKE_CASE, unit suffix, grouped at file top, derived values computed inline, zero per-track branches (TARGET-02 inspection requirement).

### No docstrings, no library type hints
**Source:** entire codebase (CLAUDE.md conventions)
**Apply to:** `src/targets.py` untyped/undocstringed; scripts hint only public entry-point signatures.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| NaN-aware Savitzky-Golay smoother (function inside `src/targets.py`) | numerical utility | transform | No smoothing code exists in repo; `scipy.signal.savgol_filter` is NOT NaN-aware (RESEARCH Finding 2). Use the ~20-line windowed-polyfit implementation in RESEARCH §Code Examples (`nan_savgol`), styled per library conventions. |
| Raw-data prohibition check (function inside run script) | integrity check | file I/O | No precedent; use RESEARCH §Code Examples mtime/size snapshot pattern with `Path.rglob` + `stat()`, printed PASS/FAIL. |
| `extraction_params.json` provenance write | config output | file I/O | No config-file writes exist; stdlib `json.dump` of the constants dict, written once by the run script. |

## Metadata

**Analog search scope:** `src/`, `scripts/` (entire non-notebook codebase — 2 Python files total; notebooks excluded as non-canonical per CONTEXT)
**Files scanned:** 2 (both read in full)
**Pattern extraction date:** 2026-07-19
