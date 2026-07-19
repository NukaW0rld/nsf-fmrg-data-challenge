# Coding Conventions

**Analysis Date:** 2026-07-19

## Project Type

This is a scientific data-processing repository (NSF FMRG data challenge) built around a single Python module, `src/nsf_fmrg_data.py`, plus a CLI export script (`scripts/run_thermal_video_export.py`) and exploratory Jupyter notebooks (`notebooks/`). It is not a typical application codebase — no package structure, no `setup.py`/`pyproject.toml`, no test suite, no linter configuration.

## Naming Patterns

**Files:**
- Lowercase snake_case module/script names: `nsf_fmrg_data.py`, `run_thermal_video_export.py`
- Notebooks numbered with descriptive suffix: `01_starter_code_loading_and_visualization.ipynb`, `02_starter_code_loading_and_visualization_standalone_colab.ipynb` (`notebooks/`)

**Functions:**
- snake_case, verb-first, descriptive of the transform performed: `find_track_file`, `extract_final_thermal_frames`, `robust_plane_detrend`, `parse_wyko_header` (`src/nsf_fmrg_data.py`)
- Private/internal helpers prefixed with a single underscore: `_loadmat_any` (`src/nsf_fmrg_data.py:34`)

**Variables:**
- snake_case throughout: `thermal_dir`, `track_id`, `on_start`, `stop_idx`
- Physical-quantity variables encode units in the name: `COMMON_X_START_MM`, `THERMAL_MM_PER_FRAME`, `x_mm_center`, `pixel_size_mm`, `Z_mm` (`src/nsf_fmrg_data.py:8-13`)
- Matrix/array variables use domain math notation with capital letters where conventional: `Z_yx`, `Z_x_y`, `X_plot`, `Y_plot` (`src/nsf_fmrg_data.py:185-238`) — this deviates from PEP8 lowercase-variable convention deliberately to mirror linear-algebra notation; follow this pattern for new grid/matrix variables.

**Constants:**
- SCREAMING_SNAKE_CASE, module-level, grouped at top of file with inline derivation: `THERMAL_FPS`, `SCAN_SPEED_MM_PER_S`, `THERMAL_MM_PER_FRAME`, `EXTRACTED_THERMAL_FRAMES` (`src/nsf_fmrg_data.py:8-13`)
- Script-level display/plot constants also SCREAMING_SNAKE_CASE at top of file: `THERMAL_CMAP`, `THERMAL_VMIN`, `THERMAL_VMAX`, `THERMAL_PIXEL_SIZE_MM` (`scripts/run_thermal_video_export.py:15-18`)

**Types:**
- No custom classes or type aliases defined anywhere in the codebase. All data structures are plain `dict`, `np.ndarray`, and built-in types.

## Code Style

**Formatting:**
- No formatter (Black/Ruff/autopep8) configured — no `pyproject.toml`, `.flake8`, or `setup.cfg` present.
- Style is hand-consistent: 4-space indentation, no trailing semicolons, single blank line between top-level functions in `src/nsf_fmrg_data.py`, double blank line in `scripts/run_thermal_video_export.py`.
- Line length generally kept under ~100 characters; dense one-line dict returns are used for multi-field results (`src/nsf_fmrg_data.py:124-130`, `199-202`).

**Linting:**
- No linter config found (no `.eslintrc`-equivalent, no `ruff.toml`, no `.pylintrc`).
- No type hints in `src/nsf_fmrg_data.py`. `scripts/run_thermal_video_export.py` uses type hints selectively for its public function signature only: `def save_video(project_dir: Path, track_id: int, fps: int = 10) -> Path:` (`scripts/run_thermal_video_export.py:21`). Follow this convention: add type hints to script-level entry points/CLI functions, but library-internal numerical functions in `nsf_fmrg_data.py` remain untyped, consistent with existing style.

## Import Organization

**Order (as observed in both files):**
1. Standard library (`pathlib`, `re`, `json`, `argparse`, `sys`)
2. Third-party scientific stack (`numpy`, `scipy.io`, `PIL`, `matplotlib`)
3. Local/repo imports (`from nsf_fmrg_data import extract_final_thermal_frames`)

No `import json` is actually used in `src/nsf_fmrg_data.py` — imported but unused (see CONCERNS if generated).

**Path Aliases:**
- None (no bundler/module system). `scripts/run_thermal_video_export.py` manually appends `src/` to `sys.path` to import the sibling module without packaging:
```python
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))
```
(`scripts/run_thermal_video_export.py:7-11`) — replicate this pattern for any new script that needs to import from `src/`.

## Error Handling

**Patterns:**
- Fail-fast with built-in exceptions and explicit messages rather than custom exception classes: `raise ValueError('No thermal-like array found in MAT file.')` (`src/nsf_fmrg_data.py:71`)
- Narrow `try/except` used only around a specific known failure mode (unsupported MAT file version), with a fallback code path rather than a bare re-raise: `_loadmat_any` catches `NotImplementedError` from `scipy.io.loadmat` and falls back to `h5py` (`src/nsf_fmrg_data.py:34-49`).
- Inner exception swallowing is scoped tightly and justified by best-effort array conversion: `except Exception: pass` inside the `h5py` visit callback (`src/nsf_fmrg_data.py:46-47`) — only used when skipping a single non-convertible dataset entry is safe, not as a general pattern.
- No input validation layer, no argument-checking decorators, no custom exception hierarchy. Functions assume well-formed scientific data files as arguments.

## Logging

**Framework:** None. No `logging` module usage anywhere.

**Patterns:**
- CLI feedback via `print()` only, at the end of the `main()` entry point: `print(f"Saved: {out_path}")` (`scripts/run_thermal_video_export.py:81`). Follow this pattern for new CLI scripts — do not introduce `logging` module without checking with maintainers first, since the existing scripts are print-based.

## Comments

**When to Comment:**
- Sparse, single-line comments used only to explain non-obvious intent (e.g., a sys.path hack): `# Allow running from repo root without installing as a package.` (`scripts/run_thermal_video_export.py:7`)
- No comments inside `src/nsf_fmrg_data.py` function bodies — the code relies on descriptive naming instead of inline commentary. Physical/units context is carried by variable names (`_MM`, `_FPS`) rather than comments.

**Docstrings:**
- None present anywhere in the codebase. No module, function, or class docstrings. New functions should follow existing style (no docstrings) unless the maintainers request otherwise; if introducing docstrings, prefer adding them consistently across the whole module rather than piecemeal.

## Function Design

**Size:** Small to medium, single-responsibility, typically 5-30 lines. Each function performs one clearly named transformation step in a data pipeline (find file → load raw → extract signal → detrend → plot).

**Parameters:** Plain positional/keyword arguments with sensible defaults for tunable numeric thresholds, e.g. `robust_plane_detrend(Z_mm, x_mm, y_mm, stride_x=40, stride_y=2)` (`src/nsf_fmrg_data.py:205`), `thermal_frame_score(frames, top_percentile=99.5)` (`src/nsf_fmrg_data.py:84`). No `**kwargs`/`*args` usage.

**Return Values:** Mix of plain tuples for simple multi-value results (`largest_true_run` returns `(start, stop)`, `src/nsf_fmrg_data.py:88-97`) and dicts with named string keys for complex/composite results (`extract_final_thermal_frames`, `load_wyko_asc` — both return dicts bundling data + provenance/metadata, `src/nsf_fmrg_data.py:124-130`, `199-202`). Prefer dict returns when a function produces more than 2-3 heterogeneous outputs that downstream code accesses by name (e.g., in notebooks).

## Module Design

**Exports:** No `__all__`, no explicit public/private API boundary beyond the single-underscore convention for `_loadmat_any`. All top-level functions are implicitly public.

**Structure:** Single flat module (`src/nsf_fmrg_data.py`) containing all data-loading, signal-processing, and geometry-correction logic for three sensing modalities (thermal `.mat`, SEM images, Wyko `.asc` profilometry). No sub-packages. When adding a new modality or processing step, add a new top-level function to this module following the existing naming/section grouping (functions for the same modality are kept adjacent, e.g., all thermal functions together at lines 84-131, all SEM functions at 133-141, all Wyko functions at 144-227).

**Compiled artifacts:** `src/__pycache__/*.pyc` is present in the working tree — not covered by `.gitignore` currently for the `src/` cache directory specifically (verify `.gitignore` before committing new files under `src/`).

---

*Convention analysis: 2026-07-19*
</content>
