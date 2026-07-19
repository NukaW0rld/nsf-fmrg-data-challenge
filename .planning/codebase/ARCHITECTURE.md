<!-- refreshed: 2026-07-19 -->
# Architecture

**Analysis Date:** 2026-07-19

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                   Raw Multimodal Dataset                     │
│  `data/raw/thermal/*.mat`  `data/raw/sem/SEM_*/PlainImages/` │
│  `data/raw/height_maps/*.ASC`                                │
└───────────────────────────┬────────────────────────────────┘
                             │ loaders (per-modality functions)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              Data Access / Preprocessing Library             │
│                    `src/nsf_fmrg_data.py`                    │
│  - thermal: find_track_file, extract_final_thermal_frames    │
│  - SEM: get_sem_tile_paths, load_sem_tile                    │
│  - height map: parse_wyko_header, load_wyko_asc              │
│  - shared geometry helpers: robust_plane_detrend,             │
│    display_shear_grid                                        │
└───────┬───────────────────────────────┬─────────────────────┘
        │                                │
        ▼                                ▼
┌───────────────────────────┐  ┌───────────────────────────────┐
│   Notebooks (analysis /    │  │   CLI Scripts (batch export)  │
│   visualization)           │  │  `scripts/                    │
│  `notebooks/01_*.ipynb`    │  │   run_thermal_video_export.py`│
│  `notebooks/02_*.ipynb`    │  │                                │
└───────────────────────────┘  └────────────┬──────────────────┘
                                             │
                                             ▼
                                ┌───────────────────────────────┐
                                │  Generated Outputs             │
                                │  `processed_data/videos/*.mp4` │
                                └───────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Thermal loader | Locate `.mat` file per track, parse array (incl. HDF5 fallback), auto-orient to (frame, y, x) | `src/nsf_fmrg_data.py:21-81` |
| Laser-on detection | Score frames, detect largest contiguous "laser on" interval, extract last 400 frames (20-100mm window) | `src/nsf_fmrg_data.py:84-130` |
| SEM loader | List/sort SEM tile image paths per track, load a tile as grayscale array | `src/nsf_fmrg_data.py:133-141` |
| Height-map loader | Parse Wyko `.ASC` header/body, convert units, reorient to increasing 20-100mm physical coordinate, optional crop | `src/nsf_fmrg_data.py:144-202` |
| Geometry utilities | Robust (outlier-resistant) plane detrending; display-only shear correction for visualization | `src/nsf_fmrg_data.py:205-238` |
| Standalone organizer notebook | Data QA, figure generation, thermal extraction/export, does not depend on `src/` | `notebooks/02_starter_code_loading_and_visualization_standalone_colab.ipynb` |
| Participant starter notebook | Clean example of loading/aligning all three modalities using `src/nsf_fmrg_data.py` | `notebooks/01_starter_code_loading_and_visualization.ipynb` |
| Thermal video export CLI | Batch-render an MP4 animation of a track's extracted thermal frames | `scripts/run_thermal_video_export.py` |

## Pattern Overview

**Overall:** Data-science utility library + notebook/script consumers. Not a service/app — this is a research/competition-data-loading toolkit with a functional (not class-based), stateless module of pure loader/transform functions imported by exploratory notebooks and one CLI script.

**Key Characteristics:**
- Single flat module (`src/nsf_fmrg_data.py`) exposing loader functions per data modality (thermal, SEM, height map).
- No classes, no framework, no persistent server/process — everything is a synchronous function call over local files.
- Physical-coordinate alignment (mm along the 20-100mm scan window) is the central cross-cutting concern threaded through all three loaders.
- Consumers (notebooks, `scripts/`) import functions directly; there is no plugin/DI system.

## Layers

**Data layer (raw inputs):**
- Purpose: Immutable multimodal experimental data, organized per track ID (8, 10, 14, 21)
- Location: `data/raw/thermal/`, `data/raw/sem/SEM_<id>/PlainImages/`, `data/raw/height_maps/`
- Contains: `.mat` thermal cubes, `.png`/`.tif` SEM tiles, Wyko `.ASC` height-map text files
- Depends on: nothing (external Zenodo download, not in repo)
- Used by: `src/nsf_fmrg_data.py` loader functions

**Library layer (loading/preprocessing):**
- Purpose: Convert raw per-modality files into aligned, physically-coordinated NumPy arrays
- Location: `src/nsf_fmrg_data.py`
- Contains: file-finding, MAT/ASC parsing, unit conversion, coordinate alignment/cropping, detrending
- Depends on: `numpy`, `scipy.io.loadmat`, `h5py` (fallback for MAT v7.3), `PIL`
- Used by: `notebooks/01_*.ipynb`, `scripts/run_thermal_video_export.py`

**Consumer layer (notebooks/scripts):**
- Purpose: Analysis, visualization, and batch export
- Location: `notebooks/`, `scripts/`
- Contains: plotting (matplotlib), figure/video generation, exploratory data checks
- Depends on: library layer (notebook 01, script) or is fully standalone (notebook 02)
- Used by: end users (competition participants, organizers)

**Output layer (generated artifacts):**
- Purpose: Store rendered outputs from scripts/notebooks
- Location: `processed_data/videos/` (created at runtime by `scripts/run_thermal_video_export.py`)
- Depends on: library + consumer layers
- Used by: nothing downstream in-repo (terminal artifact for human review)

## Data Flow

### Thermal video export path (CLI)

1. Entry point parses `--project_dir`, `--track_id`, `--fps` (`scripts/run_thermal_video_export.py:73-85`)
2. `save_video()` resolves `data/raw/thermal` and calls `extract_final_thermal_frames()` (`scripts/run_thermal_video_export.py:21-23`)
3. `extract_final_thermal_frames()` finds the track's `.mat` file, loads it (with HDF5 fallback), auto-orients the array, detects the laser-on interval, and slices the last `EXTRACTED_THERMAL_FRAMES` frames corresponding to the 20-100mm window (`src/nsf_fmrg_data.py:114-130`)
4. Frames are rendered via `matplotlib.animation.FuncAnimation` and written to `processed_data/videos/Track_<id>_thermal_20to100mm.mp4` using `FFMpegWriter` (`scripts/run_thermal_video_export.py:39-70`)

### Multimodal alignment path (notebook/analysis)

1. Load thermal frames for a track (`extract_final_thermal_frames`), which returns frames plus `x_mm_center` array giving each frame's physical scan-direction coordinate
2. Load SEM tiles for the same track (`get_sem_tile_paths` + `load_sem_tile`); tiles are numbered such that the highest tile index is the physical 20mm end (per README, requires manual stitching/flipping by consumer — not implemented in `src/`)
3. Load the Wyko height map (`load_wyko_asc`), which reorients raw local coordinates to increasing 20-100mm physical coordinates and crops to the shared window
4. Optionally detrend height map with `robust_plane_detrend` before comparing/plotting against thermal or SEM data at matching `x` coordinates

**State Management:**
- No persistent state or database. Each loader function is pure/stateless, taking file paths and returning in-memory NumPy arrays/dicts. State exists only within a single notebook cell's or script run's local variables.

## Key Abstractions

**Track ID:**
- Purpose: Identifies one physical experiment (laser power condition); values are 8, 10, 14, 21
- Examples: used as a parameter across all loader functions (`find_track_file`, `extract_final_thermal_frames`, `get_sem_tile_paths`, `load_wyko_asc`)
- Pattern: passed as `int` or numeric string, matched against filenames via regex in `find_track_file` (`src/nsf_fmrg_data.py:21-31`)

**Physical coordinate (`x_mm` / `x_actual_mm`):**
- Purpose: Common spatial reference (millimeters along the 20-100mm scan direction) that all three modalities must be aligned to since each sensor has its own file format/orientation
- Examples: `x_mm_center` in thermal result dict, `x_actual_mm` in height-map result dict
- Pattern: computed via modality-specific unit conversion + reorientation, then optionally cropped to `[COMMON_X_START_MM, COMMON_X_END_MM]` (`src/nsf_fmrg_data.py:8-9`)

**Result dict:**
- Purpose: Loader functions return a plain `dict` bundling the data array plus metadata (file path, header, coordinate arrays) rather than a custom class
- Examples: return values of `extract_final_thermal_frames` (`src/nsf_fmrg_data.py:124-130`), `load_wyko_asc` (`src/nsf_fmrg_data.py:199-202`)
- Pattern: consistent `dict` keys across loaders (`'file'`, coordinate arrays, primary data array) for simple destructuring in notebooks

## Entry Points

**`scripts/run_thermal_video_export.py`:**
- Location: `scripts/run_thermal_video_export.py`
- Triggers: run via `python scripts/run_thermal_video_export.py --track_id <id>`
- Responsibilities: standalone CLI wrapper around `extract_final_thermal_frames`; adds `src/` to `sys.path` manually (no packaging/install step) and renders/exports a video

**`notebooks/01_starter_code_loading_and_visualization.ipynb`:**
- Location: `notebooks/01_starter_code_loading_and_visualization.ipynb`
- Triggers: opened interactively in Jupyter/Colab
- Responsibilities: participant-facing demonstration of loading and aligning all three modalities using `src/nsf_fmrg_data.py`

**`notebooks/02_starter_code_loading_and_visualization_standalone_colab.ipynb`:**
- Location: `notebooks/02_starter_code_loading_and_visualization_standalone_colab.ipynb`
- Triggers: opened interactively in Colab/Jupyter
- Responsibilities: organizer/post-processing notebook; self-contained (does not import `src/`), used for QA, figure generation, and thermal export

## Architectural Constraints

- **Threading:** Single-threaded, synchronous throughout. No async, no worker processes. `matplotlib.animation.FuncAnimation` runs on the main thread during video export.
- **Global state:** Module-level constants only (`COMMON_X_START_MM`, `COMMON_X_END_MM`, `THERMAL_FPS`, `SCAN_SPEED_MM_PER_S`, `THERMAL_MM_PER_FRAME`, `EXTRACTED_THERMAL_FRAMES` in `src/nsf_fmrg_data.py:8-13`; `THERMAL_CMAP`, `THERMAL_VMIN`, `THERMAL_VMAX`, `THERMAL_PIXEL_SIZE_MM` in `scripts/run_thermal_video_export.py:15-18`). No mutable singletons.
- **Circular imports:** None — single-module library with no internal package structure.
- **No packaging:** `src/` is not an installable package (no `setup.py`/`pyproject.toml`/`__init__.py`); consumers manipulate `sys.path` directly (`scripts/run_thermal_video_export.py:7-11`) or run notebooks from the repo root.
- **Large/external data not versioned:** Raw dataset files live under `data/raw/` but are fetched externally from Zenodo; the repo only ships `.gitkeep` placeholders and (per README) the SEM PNGs.

## Anti-Patterns

### Manual `sys.path` manipulation instead of packaging

**What happens:** `scripts/run_thermal_video_export.py` appends `src/` to `sys.path` at runtime to import `nsf_fmrg_data` (`scripts/run_thermal_video_export.py:7-11`).
**Why it's wrong:** Fragile relative-to-`__file__` path logic; breaks if the script is invoked from a different working directory structure or moved; no `pip install -e .` support.
**Do this instead:** Add a `pyproject.toml`/`setup.py` with `src/` as the package root and install the project in editable mode, or run scripts as `python -m scripts.run_thermal_video_export` from repo root with a proper package.

### Silent broad exception handling in MAT parsing fallback

**What happens:** `_loadmat_any`'s HDF5 fallback swallows all `Exception`s per-dataset with a bare `except Exception: pass` (`src/nsf_fmrg_data.py:44-47`).
**Why it's wrong:** Any per-array conversion failure is silently dropped, which could hide malformed thermal data without any warning to the caller.
**Do this instead:** Log or collect skipped keys and surface them (e.g., a warning) so data-quality issues in the raw `.mat` files are visible rather than silently missing.

## Error Handling

**Strategy:** Minimal explicit error handling; relies on Python's default exception propagation. A few functions raise explicit `ValueError` when expected data is absent (`find_thermal_array` in `src/nsf_fmrg_data.py:52-71` raises if no thermal-like array is found).

**Patterns:**
- `find_track_file` returns `None` if no match is found rather than raising (caller must check) (`src/nsf_fmrg_data.py:21-31`).
- `_loadmat_any` catches `NotImplementedError` specifically to trigger the HDF5 fallback path for MAT v7.3 files (`src/nsf_fmrg_data.py:34-49`).

## Cross-Cutting Concerns

**Logging:** None — no logging framework configured; scripts use `print()` for final output confirmation only (`scripts/run_thermal_video_export.py:81`).
**Validation:** Minimal; relies on array shape/dtype heuristics (e.g., `find_thermal_array` scores candidate arrays by shape/size) rather than schema validation.
**Authentication:** Not applicable — purely local file I/O, no network/auth concerns in `src/` or `scripts/`.

---

*Architecture analysis: 2026-07-19*
