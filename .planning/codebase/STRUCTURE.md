# Codebase Structure

**Analysis Date:** 2026-07-19

## Directory Layout

```
nsf-fmrg-data-challenge/
├── README.md                    # Competition/challenge description, dataset docs, workflow guide
├── DATA_USE_LICENSE.md          # Data usage terms
├── CITATION.cff                 # Citation metadata
├── requirements.txt             # Python dependencies (flat, unpinned)
├── data/
│   └── raw/                     # Raw multimodal dataset (downloaded from Zenodo)
│       ├── thermal/             # Thermal `.mat` cubes per track (Thermal_<id>.mat)
│       ├── sem/                 # SEM tile images per track
│       │   └── SEM_<id>/PlainImages/   # Per-track PNG/TIFF tiles
│       └── height_maps/         # Wyko ASCII height-map files (Heightmap_<id>.ASC)
├── notebooks/
│   ├── 01_starter_code_loading_and_visualization.ipynb              # Participant starter (uses src/)
│   └── 02_starter_code_loading_and_visualization_standalone_colab.ipynb  # Organizer notebook (standalone)
├── src/
│   ├── nsf_fmrg_data.py         # Core data-loading/preprocessing library (thermal, SEM, height map)
│   └── __pycache__/             # Compiled bytecode (generated, not source)
├── scripts/
│   └── run_thermal_video_export.py   # CLI: export thermal frames to MP4 for one track
├── paper/
│   ├── research_paper.md        # Companion dataset paper content
│   └── figures/                 # PNG figures referenced by README/paper
├── processed_data/              # Generated outputs (created at runtime, e.g. videos/)
└── .planning/                   # GSD planning artifacts (not part of the data-science codebase)
```

## Directory Purposes

**`data/raw/`:**
- Purpose: Holds the raw, unmodified multimodal dataset as downloaded from Zenodo
- Contains: `.mat` thermal cubes, SEM `.png`/`.tif` tiles under `SEM_<track_id>/PlainImages/`, Wyko `.ASC` height-map text files
- Key files: none checked into git except `.gitkeep` placeholders (per README); actual data added locally by participants after download

**`notebooks/`:**
- Purpose: Interactive exploration, visualization, and reference workflows
- Contains: two Jupyter notebooks — one standalone (organizer), one dependent on `src/` (participant starter)
- Key files: `notebooks/01_starter_code_loading_and_visualization.ipynb`, `notebooks/02_starter_code_loading_and_visualization_standalone_colab.ipynb`

**`src/`:**
- Purpose: Reusable Python library code shared by notebooks and scripts
- Contains: a single flat module, `nsf_fmrg_data.py`, with no sub-packages
- Key files: `src/nsf_fmrg_data.py`

**`scripts/`:**
- Purpose: Standalone command-line entry points for batch/automated tasks (as opposed to interactive notebooks)
- Contains: one CLI script for exporting thermal videos
- Key files: `scripts/run_thermal_video_export.py`

**`paper/`:**
- Purpose: Companion dataset-paper content and figures referenced from README
- Contains: `research_paper.md`, `figures/*.png`
- Key files: `paper/research_paper.md`

**`processed_data/`:**
- Purpose: Destination for generated artifacts (videos, exported figures) — not committed source
- Generated: Yes (created at runtime by `scripts/run_thermal_video_export.py`, subfolder `videos/`)
- Committed: Only a `.gitkeep` placeholder per README; generated content itself is not committed

## Key File Locations

**Entry Points:**
- `scripts/run_thermal_video_export.py`: CLI for exporting a track's thermal frames as an MP4

**Configuration:**
- `requirements.txt`: flat list of Python dependencies (numpy, scipy, matplotlib, pillow, pandas) — no version pins
- No `.eslintrc`, `tsconfig`, `pyproject.toml`, or `setup.py` present — no packaging/lint config in this repo

**Core Logic:**
- `src/nsf_fmrg_data.py`: all data loading, alignment, and preprocessing logic (thermal, SEM, height map)

**Testing:**
- None present — no test directory, test framework config, or test files found in the repository

## Naming Conventions

**Files:**
- Python modules/scripts: `lower_snake_case.py` (e.g., `nsf_fmrg_data.py`, `run_thermal_video_export.py`)
- Notebooks: numbered prefix + descriptive snake_case + suffix for variant (e.g., `01_starter_code_loading_and_visualization.ipynb`, `02_..._standalone_colab.ipynb`)
- Raw data files: `<Modality>_<track_id>.<ext>` (e.g., `Thermal_8.mat`, `Heightmap_8.ASC`) and `SEM_<track_id>/PlainImages/Plain_SEM_<track_id>_<tile_number>.png`

**Directories:**
- Data modality directories under `data/raw/` are lowercase (`thermal/`, `sem/`, `height_maps/`), while per-track SEM subdirectories are uppercase-prefixed (`SEM_8/`, `SEM_10/`)
- Generated output directories are created under `processed_data/<artifact_type>/` (e.g., `processed_data/videos/`)

**Functions (in `src/nsf_fmrg_data.py`):**
- `lower_snake_case`, verb-first for actions (`find_track_file`, `load_wyko_asc`, `extract_final_thermal_frames`), noun-first only for pure computations (`thermal_frame_score`, `largest_true_run`)
- Private/internal helpers prefixed with underscore (`_loadmat_any`)

**Constants:**
- `UPPER_SNAKE_CASE` at module scope, grouped near top of file (e.g., `COMMON_X_START_MM`, `THERMAL_FPS`, `SCAN_SPEED_MM_PER_S`)

## Where to Add New Code

**New data-loading/preprocessing function (new modality or new derived quantity):**
- Add to `src/nsf_fmrg_data.py`, following the existing pattern: pure function taking file/dir paths (+ `track_id` where relevant), returning a `dict` with a `'file'` key plus data/coordinate arrays
- If the module grows significantly, consider splitting into `src/thermal.py`, `src/sem.py`, `src/height_map.py` submodules under a proper `src/nsf_fmrg_data/` package — not yet done

**New CLI script (e.g., batch export of another modality):**
- Add under `scripts/`, following `scripts/run_thermal_video_export.py`'s pattern: `argparse` CLI, manual `sys.path` insertion of `src/`, `main()` guarded by `if __name__ == "__main__":`

**New analysis notebook:**
- Add under `notebooks/` with a numeric prefix continuing from `01_`, `02_`; import shared logic from `src/nsf_fmrg_data.py` rather than duplicating loading code (mirror notebook `01`'s pattern, not notebook `02`'s standalone pattern, unless a fully self-contained Colab notebook is intended)

**Tests (none currently exist):**
- No test directory or framework is configured. If adding tests, create a `tests/` directory at repo root and choose a framework (e.g., pytest) — this would be a new addition, not an extension of existing conventions

**Generated outputs:**
- Write to `processed_data/<artifact_type>/`, creating the subdirectory at runtime (mirroring `scripts/run_thermal_video_export.py:25-26`)

## Special Directories

**`data/raw/`:**
- Purpose: External large dataset files (thermal `.mat`, SEM images, height-map `.ASC`), downloaded manually from Zenodo
- Generated: No (externally sourced), except `.gitkeep` placeholders
- Committed: `.gitkeep` files only per README instructions; actual data files are expected to be added locally and are large/not intended for git

**`src/__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes
- Committed: No (should be gitignored; contains `.pyc` files for Python 3.12/3.13)

**`processed_data/`:**
- Purpose: Runtime-generated analysis outputs (e.g., exported thermal videos)
- Generated: Yes
- Committed: Placeholder only (`.gitkeep`), not the generated content itself

**`.planning/`:**
- Purpose: GSD workflow planning artifacts (codebase maps, config) — not part of the application/library code
- Generated: Yes (by GSD tooling)
- Committed: Depends on project convention; not part of the data-science codebase itself

---

*Structure analysis: 2026-07-19*
