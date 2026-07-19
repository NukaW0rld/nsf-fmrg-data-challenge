<!-- GSD:project-start source:PROJECT.md -->

## Project

**NSF FMRG Data Challenge — Thermal-to-Geometry Prediction Pipeline**

A reproducible, end-to-end pipeline for the NSF Future Manufacturing Data Challenge. It converts raw thermal, SEM, and profilometry data into spatially aligned samples, derives a physically defensible local track-geometry target from the height maps, predicts that geometry and its uncertainty from thermal history (optionally fused with masked SEM context), validates generalization across held-out tracks, and produces the code and figures required for competition submission.

**Core Value:** A thermal-only baseline that runs end-to-end — raw data in, cross-track-validated local-width predictions with calibrated uncertainty out — must work before anything else matters. Given the 8-day runway to the deadline, a complete simple pipeline beats an incomplete ambitious one.

### Constraints

- **Timeline**: 8 days to submission deadline (today 2026-07-19, due 2026-07-27) — favors coarse phases and a working baseline before polish
- **Compute**: Local GPU available — model choices should fit that budget; no requirement for distributed/cloud-scale training
- **Data volume**: Only 4 track conditions exist — cross-track (leave-one-out) validation is required; random/neighboring-sample splits within a track are invalid due to spatial correlation
- **Data licensing**: Dataset is competition-restricted per `DATA_USE_LICENSE.md` — no external reuse or sharing
- **Methodology**: SEM input (if used) must mask the processed track region — target leakage is an explicit failure mode called out by organizers
- **Reproducibility**: Submission requires executable code — the pipeline must run end-to-end from raw data to figures/predictions, not just a describe-only report

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- Python 3.12/3.13 - all source (`src/nsf_fmrg_data.py`, `scripts/run_thermal_video_export.py`), notebooks compiled to `.pyc` for both 3.12 and 3.13 (`src/__pycache__/nsf_fmrg_data.cpython-312.pyc`, `.cpython-313.pyc`), indicating dev/testing across at least two Python versions.
- Jupyter Notebook (JSON) - `notebooks/01_starter_code_loading_and_visualization.ipynb`, `notebooks/02_starter_code_loading_and_visualization_standalone_colab.ipynb`
- Markdown - documentation and the companion research paper (`paper/research_paper.md`, `README.md`)

## Runtime

- CPython 3.12+ (no version pin file such as `.python-version` present; `requirements.txt` has no version pins either)
- pip, driven by `requirements.txt` (`python -m pip install -r requirements.txt` per README)
- Lockfile: missing (no `requirements-lock.txt`, `poetry.lock`, or `uv.lock` present)
- README recommends using `uv` to create/manage virtual environments, but no `pyproject.toml` or `uv.lock` exists in the repo — this is a suggestion, not an enforced tool.

## Frameworks

- None (no web framework, no CLI framework beyond stdlib `argparse`). This is a scientific data-processing/analysis repository, not an application.
- None detected. No `pytest`, `unittest`, or test directories/files found anywhere in the repo.
- None (no build system, no linter/formatter config, no CI config detected — no `.github/workflows/`, `tox.ini`, `Makefile`, etc.)

## Key Dependencies

- `numpy` - array/numeric handling for thermal frames, height maps, SEM tiles
- `scipy` - specifically `scipy.io.loadmat` for reading MATLAB `.mat` thermal files (`src/nsf_fmrg_data.py:5`)
- `pillow` (PIL) - `PIL.Image`, `PIL.ImageOps` for loading/grayscaling SEM `.png`/`.tif` tiles (`src/nsf_fmrg_data.py:6`, `140-141`)
- `pandas` - listed in `requirements.txt` but not imported in `src/nsf_fmrg_data.py`; likely used only within the notebooks
- `matplotlib` - visualization and video export (`scripts/run_thermal_video_export.py` uses `matplotlib.pyplot` and `matplotlib.animation`)
- `h5py` - imported lazily inside `_loadmat_any()` (`src/nsf_fmrg_data.py:39`) as a fallback when `scipy.io.loadmat` raises `NotImplementedError` (i.e., MATLAB v7.3/HDF5-format `.mat` files). Not listed in `requirements.txt` — a gap if any thermal `.mat` file is v7.3 format.
- `ffmpeg` (external binary, not a Python package) - required by `matplotlib.animation.FFMpegWriter` in `scripts/run_thermal_video_export.py:64` for MP4 video export. Must be installed on the system PATH separately.

## Configuration

- No environment variable usage detected anywhere in the codebase (no `os.environ`, `.env` files, or config files).
- All configuration is done via Python constants at module level, e.g. `COMMON_X_START_MM`, `COMMON_X_END_MM`, `THERMAL_FPS`, `SCAN_SPEED_MM_PER_S` in `src/nsf_fmrg_data.py:8-13`, and `THERMAL_CMAP`, `THERMAL_VMIN`, `THERMAL_VMAX`, `THERMAL_PIXEL_SIZE_MM` in `scripts/run_thermal_video_export.py:14-17`.
- `scripts/run_thermal_video_export.py` accepts CLI args via `argparse`: `--project_dir`, `--track_id`, `--fps` (`scripts/run_thermal_video_export.py:69-74`).
- No build config files present (no `setup.py`, `pyproject.toml`, `setup.cfg`).
- `src/` is used as an ad-hoc import path — not an installable package. `scripts/run_thermal_video_export.py` manually appends `REPO_ROOT / "src"` to `sys.path` (`scripts/run_thermal_video_export.py:7-10`) rather than importing an installed package.

## Platform Requirements

- Python 3.12+ (evidenced by compiled `.pyc` caches)
- Sufficient local disk space for large raw datasets (`data/raw/thermal/*.mat`, `data/raw/sem/`, `data/raw/height_maps/*.ASC`) downloaded separately from Zenodo (not committed to git; `.gitkeep` placeholders only)
- `ffmpeg` binary on PATH (only needed for `scripts/run_thermal_video_export.py`)
- Works in both a local system environment and Google Colab (README: `notebooks/02_starter_code_loading_and_visualization_standalone_colab.ipynb` is fully standalone and Colab-compatible)
- Not applicable — this repository is a data-challenge starter kit/toolkit, not a deployed application. There is no production runtime target.

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Project Type

## Naming Patterns

- Lowercase snake_case module/script names: `nsf_fmrg_data.py`, `run_thermal_video_export.py`
- Notebooks numbered with descriptive suffix: `01_starter_code_loading_and_visualization.ipynb`, `02_starter_code_loading_and_visualization_standalone_colab.ipynb` (`notebooks/`)
- snake_case, verb-first, descriptive of the transform performed: `find_track_file`, `extract_final_thermal_frames`, `robust_plane_detrend`, `parse_wyko_header` (`src/nsf_fmrg_data.py`)
- Private/internal helpers prefixed with a single underscore: `_loadmat_any` (`src/nsf_fmrg_data.py:34`)
- snake_case throughout: `thermal_dir`, `track_id`, `on_start`, `stop_idx`
- Physical-quantity variables encode units in the name: `COMMON_X_START_MM`, `THERMAL_MM_PER_FRAME`, `x_mm_center`, `pixel_size_mm`, `Z_mm` (`src/nsf_fmrg_data.py:8-13`)
- Matrix/array variables use domain math notation with capital letters where conventional: `Z_yx`, `Z_x_y`, `X_plot`, `Y_plot` (`src/nsf_fmrg_data.py:185-238`) — this deviates from PEP8 lowercase-variable convention deliberately to mirror linear-algebra notation; follow this pattern for new grid/matrix variables.
- SCREAMING_SNAKE_CASE, module-level, grouped at top of file with inline derivation: `THERMAL_FPS`, `SCAN_SPEED_MM_PER_S`, `THERMAL_MM_PER_FRAME`, `EXTRACTED_THERMAL_FRAMES` (`src/nsf_fmrg_data.py:8-13`)
- Script-level display/plot constants also SCREAMING_SNAKE_CASE at top of file: `THERMAL_CMAP`, `THERMAL_VMIN`, `THERMAL_VMAX`, `THERMAL_PIXEL_SIZE_MM` (`scripts/run_thermal_video_export.py:15-18`)
- No custom classes or type aliases defined anywhere in the codebase. All data structures are plain `dict`, `np.ndarray`, and built-in types.

## Code Style

- No formatter (Black/Ruff/autopep8) configured — no `pyproject.toml`, `.flake8`, or `setup.cfg` present.
- Style is hand-consistent: 4-space indentation, no trailing semicolons, single blank line between top-level functions in `src/nsf_fmrg_data.py`, double blank line in `scripts/run_thermal_video_export.py`.
- Line length generally kept under ~100 characters; dense one-line dict returns are used for multi-field results (`src/nsf_fmrg_data.py:124-130`, `199-202`).
- No linter config found (no `.eslintrc`-equivalent, no `ruff.toml`, no `.pylintrc`).
- No type hints in `src/nsf_fmrg_data.py`. `scripts/run_thermal_video_export.py` uses type hints selectively for its public function signature only: `def save_video(project_dir: Path, track_id: int, fps: int = 10) -> Path:` (`scripts/run_thermal_video_export.py:21`). Follow this convention: add type hints to script-level entry points/CLI functions, but library-internal numerical functions in `nsf_fmrg_data.py` remain untyped, consistent with existing style.

## Import Organization

- None (no bundler/module system). `scripts/run_thermal_video_export.py` manually appends `src/` to `sys.path` to import the sibling module without packaging:

## Error Handling

- Fail-fast with built-in exceptions and explicit messages rather than custom exception classes: `raise ValueError('No thermal-like array found in MAT file.')` (`src/nsf_fmrg_data.py:71`)
- Narrow `try/except` used only around a specific known failure mode (unsupported MAT file version), with a fallback code path rather than a bare re-raise: `_loadmat_any` catches `NotImplementedError` from `scipy.io.loadmat` and falls back to `h5py` (`src/nsf_fmrg_data.py:34-49`).
- Inner exception swallowing is scoped tightly and justified by best-effort array conversion: `except Exception: pass` inside the `h5py` visit callback (`src/nsf_fmrg_data.py:46-47`) — only used when skipping a single non-convertible dataset entry is safe, not as a general pattern.
- No input validation layer, no argument-checking decorators, no custom exception hierarchy. Functions assume well-formed scientific data files as arguments.

## Logging

- CLI feedback via `print()` only, at the end of the `main()` entry point: `print(f"Saved: {out_path}")` (`scripts/run_thermal_video_export.py:81`). Follow this pattern for new CLI scripts — do not introduce `logging` module without checking with maintainers first, since the existing scripts are print-based.

## Comments

- Sparse, single-line comments used only to explain non-obvious intent (e.g., a sys.path hack): `# Allow running from repo root without installing as a package.` (`scripts/run_thermal_video_export.py:7`)
- No comments inside `src/nsf_fmrg_data.py` function bodies — the code relies on descriptive naming instead of inline commentary. Physical/units context is carried by variable names (`_MM`, `_FPS`) rather than comments.
- None present anywhere in the codebase. No module, function, or class docstrings. New functions should follow existing style (no docstrings) unless the maintainers request otherwise; if introducing docstrings, prefer adding them consistently across the whole module rather than piecemeal.

## Function Design

## Module Design

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

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

- Single flat module (`src/nsf_fmrg_data.py`) exposing loader functions per data modality (thermal, SEM, height map).
- No classes, no framework, no persistent server/process — everything is a synchronous function call over local files.
- Physical-coordinate alignment (mm along the 20-100mm scan window) is the central cross-cutting concern threaded through all three loaders.
- Consumers (notebooks, `scripts/`) import functions directly; there is no plugin/DI system.

## Layers

- Purpose: Immutable multimodal experimental data, organized per track ID (8, 10, 14, 21)
- Location: `data/raw/thermal/`, `data/raw/sem/SEM_<id>/PlainImages/`, `data/raw/height_maps/`
- Contains: `.mat` thermal cubes, `.png`/`.tif` SEM tiles, Wyko `.ASC` height-map text files
- Depends on: nothing (external Zenodo download, not in repo)
- Used by: `src/nsf_fmrg_data.py` loader functions
- Purpose: Convert raw per-modality files into aligned, physically-coordinated NumPy arrays
- Location: `src/nsf_fmrg_data.py`
- Contains: file-finding, MAT/ASC parsing, unit conversion, coordinate alignment/cropping, detrending
- Depends on: `numpy`, `scipy.io.loadmat`, `h5py` (fallback for MAT v7.3), `PIL`
- Used by: `notebooks/01_*.ipynb`, `scripts/run_thermal_video_export.py`
- Purpose: Analysis, visualization, and batch export
- Location: `notebooks/`, `scripts/`
- Contains: plotting (matplotlib), figure/video generation, exploratory data checks
- Depends on: library layer (notebook 01, script) or is fully standalone (notebook 02)
- Used by: end users (competition participants, organizers)
- Purpose: Store rendered outputs from scripts/notebooks
- Location: `processed_data/videos/` (created at runtime by `scripts/run_thermal_video_export.py`)
- Depends on: library + consumer layers
- Used by: nothing downstream in-repo (terminal artifact for human review)

## Data Flow

### Thermal video export path (CLI)

### Multimodal alignment path (notebook/analysis)

- No persistent state or database. Each loader function is pure/stateless, taking file paths and returning in-memory NumPy arrays/dicts. State exists only within a single notebook cell's or script run's local variables.

## Key Abstractions

- Purpose: Identifies one physical experiment (laser power condition); values are 8, 10, 14, 21
- Examples: used as a parameter across all loader functions (`find_track_file`, `extract_final_thermal_frames`, `get_sem_tile_paths`, `load_wyko_asc`)
- Pattern: passed as `int` or numeric string, matched against filenames via regex in `find_track_file` (`src/nsf_fmrg_data.py:21-31`)
- Purpose: Common spatial reference (millimeters along the 20-100mm scan direction) that all three modalities must be aligned to since each sensor has its own file format/orientation
- Examples: `x_mm_center` in thermal result dict, `x_actual_mm` in height-map result dict
- Pattern: computed via modality-specific unit conversion + reorientation, then optionally cropped to `[COMMON_X_START_MM, COMMON_X_END_MM]` (`src/nsf_fmrg_data.py:8-9`)
- Purpose: Loader functions return a plain `dict` bundling the data array plus metadata (file path, header, coordinate arrays) rather than a custom class
- Examples: return values of `extract_final_thermal_frames` (`src/nsf_fmrg_data.py:124-130`), `load_wyko_asc` (`src/nsf_fmrg_data.py:199-202`)
- Pattern: consistent `dict` keys across loaders (`'file'`, coordinate arrays, primary data array) for simple destructuring in notebooks

## Entry Points

- Location: `scripts/run_thermal_video_export.py`
- Triggers: run via `python scripts/run_thermal_video_export.py --track_id <id>`
- Responsibilities: standalone CLI wrapper around `extract_final_thermal_frames`; adds `src/` to `sys.path` manually (no packaging/install step) and renders/exports a video
- Location: `notebooks/01_starter_code_loading_and_visualization.ipynb`
- Triggers: opened interactively in Jupyter/Colab
- Responsibilities: participant-facing demonstration of loading and aligning all three modalities using `src/nsf_fmrg_data.py`
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

### Silent broad exception handling in MAT parsing fallback

## Error Handling

- `find_track_file` returns `None` if no match is found rather than raising (caller must check) (`src/nsf_fmrg_data.py:21-31`).
- `_loadmat_any` catches `NotImplementedError` specifically to trigger the HDF5 fallback path for MAT v7.3 files (`src/nsf_fmrg_data.py:34-49`).

## Cross-Cutting Concerns

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
