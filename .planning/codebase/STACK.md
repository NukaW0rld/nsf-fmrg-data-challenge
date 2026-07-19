# Technology Stack

**Analysis Date:** 2026-07-19

## Languages

**Primary:**
- Python 3.12/3.13 - all source (`src/nsf_fmrg_data.py`, `scripts/run_thermal_video_export.py`), notebooks compiled to `.pyc` for both 3.12 and 3.13 (`src/__pycache__/nsf_fmrg_data.cpython-312.pyc`, `.cpython-313.pyc`), indicating dev/testing across at least two Python versions.

**Secondary:**
- Jupyter Notebook (JSON) - `notebooks/01_starter_code_loading_and_visualization.ipynb`, `notebooks/02_starter_code_loading_and_visualization_standalone_colab.ipynb`
- Markdown - documentation and the companion research paper (`paper/research_paper.md`, `README.md`)

## Runtime

**Environment:**
- CPython 3.12+ (no version pin file such as `.python-version` present; `requirements.txt` has no version pins either)

**Package Manager:**
- pip, driven by `requirements.txt` (`python -m pip install -r requirements.txt` per README)
- Lockfile: missing (no `requirements-lock.txt`, `poetry.lock`, or `uv.lock` present)
- README recommends using `uv` to create/manage virtual environments, but no `pyproject.toml` or `uv.lock` exists in the repo — this is a suggestion, not an enforced tool.

## Frameworks

**Core:**
- None (no web framework, no CLI framework beyond stdlib `argparse`). This is a scientific data-processing/analysis repository, not an application.

**Testing:**
- None detected. No `pytest`, `unittest`, or test directories/files found anywhere in the repo.

**Build/Dev:**
- None (no build system, no linter/formatter config, no CI config detected — no `.github/workflows/`, `tox.ini`, `Makefile`, etc.)

## Key Dependencies

Declared in `requirements.txt` (unpinned):

**Critical:**
- `numpy` - array/numeric handling for thermal frames, height maps, SEM tiles
- `scipy` - specifically `scipy.io.loadmat` for reading MATLAB `.mat` thermal files (`src/nsf_fmrg_data.py:5`)
- `pillow` (PIL) - `PIL.Image`, `PIL.ImageOps` for loading/grayscaling SEM `.png`/`.tif` tiles (`src/nsf_fmrg_data.py:6`, `140-141`)
- `pandas` - listed in `requirements.txt` but not imported in `src/nsf_fmrg_data.py`; likely used only within the notebooks

**Infrastructure:**
- `matplotlib` - visualization and video export (`scripts/run_thermal_video_export.py` uses `matplotlib.pyplot` and `matplotlib.animation`)

**Not declared but required at runtime (transitive/optional):**
- `h5py` - imported lazily inside `_loadmat_any()` (`src/nsf_fmrg_data.py:39`) as a fallback when `scipy.io.loadmat` raises `NotImplementedError` (i.e., MATLAB v7.3/HDF5-format `.mat` files). Not listed in `requirements.txt` — a gap if any thermal `.mat` file is v7.3 format.
- `ffmpeg` (external binary, not a Python package) - required by `matplotlib.animation.FFMpegWriter` in `scripts/run_thermal_video_export.py:64` for MP4 video export. Must be installed on the system PATH separately.

## Configuration

**Environment:**
- No environment variable usage detected anywhere in the codebase (no `os.environ`, `.env` files, or config files).
- All configuration is done via Python constants at module level, e.g. `COMMON_X_START_MM`, `COMMON_X_END_MM`, `THERMAL_FPS`, `SCAN_SPEED_MM_PER_S` in `src/nsf_fmrg_data.py:8-13`, and `THERMAL_CMAP`, `THERMAL_VMIN`, `THERMAL_VMAX`, `THERMAL_PIXEL_SIZE_MM` in `scripts/run_thermal_video_export.py:14-17`.
- `scripts/run_thermal_video_export.py` accepts CLI args via `argparse`: `--project_dir`, `--track_id`, `--fps` (`scripts/run_thermal_video_export.py:69-74`).

**Build:**
- No build config files present (no `setup.py`, `pyproject.toml`, `setup.cfg`).
- `src/` is used as an ad-hoc import path — not an installable package. `scripts/run_thermal_video_export.py` manually appends `REPO_ROOT / "src"` to `sys.path` (`scripts/run_thermal_video_export.py:7-10`) rather than importing an installed package.

## Platform Requirements

**Development:**
- Python 3.12+ (evidenced by compiled `.pyc` caches)
- Sufficient local disk space for large raw datasets (`data/raw/thermal/*.mat`, `data/raw/sem/`, `data/raw/height_maps/*.ASC`) downloaded separately from Zenodo (not committed to git; `.gitkeep` placeholders only)
- `ffmpeg` binary on PATH (only needed for `scripts/run_thermal_video_export.py`)
- Works in both a local system environment and Google Colab (README: `notebooks/02_starter_code_loading_and_visualization_standalone_colab.ipynb` is fully standalone and Colab-compatible)

**Production:**
- Not applicable — this repository is a data-challenge starter kit/toolkit, not a deployed application. There is no production runtime target.

---

*Stack analysis: 2026-07-19*
