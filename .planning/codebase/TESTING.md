# Testing Patterns

**Analysis Date:** 2026-07-19

## Test Framework

**Runner:**
- None configured. No `pytest`, `unittest`, `nose`, or any test runner appears in `requirements.txt` (which lists only `numpy`, `scipy`, `matplotlib`, `pillow`, `pandas`).
- No `pytest.ini`, `tox.ini`, `pyproject.toml`, `setup.cfg`, or `conftest.py` exists anywhere in the repository.

**Assertion Library:**
- Not applicable — no tests exist.

**Run Commands:**
```bash
# No test command exists in this repository.
# There is no CI workflow (.github/workflows) or Makefile target for testing.
```

## Test File Organization

**Location:**
- No test files exist. A repository-wide search for `*test*` (case-insensitive) returns zero matches outside of `.git`.

**Naming:**
- Not applicable.

**Structure:**
- Not applicable.

## Test Structure

Not applicable — no test suite exists to derive patterns from.

## Mocking

Not applicable — no mocking framework or usage found.

## Fixtures and Factories

**Test Data:**
- None. The repository instead ships small real/example data samples referenced from `notebooks/01_starter_code_loading_and_visualization.ipynb` and `notebooks/02_starter_code_loading_and_visualization_standalone_colab.ipynb`, which serve as informal, manual "smoke tests" of the loading/visualization functions in `src/nsf_fmrg_data.py` — run interactively rather than via an automated test runner. Actual experimental data lives under `data/` (tracked via Git LFS per `.gitattributes`) and is not fixture data in the pytest sense.

**Location:**
- `data/` (raw datasets, out of scope for automated tests), `notebooks/` (manual verification via notebook execution).

## Coverage

**Requirements:** None enforced. No coverage tool (`coverage.py`, `pytest-cov`) referenced anywhere.

**View Coverage:**
```bash
# Not applicable — no coverage tooling configured.
```

## Test Types

**Unit Tests:** None exist. Candidate functions that would benefit most from unit tests (pure, deterministic, easily testable with synthetic arrays) include:
- `natural_key`, `largest_true_run`, `thermal_frame_score`, `detect_laser_on_interval`, `find_thermal_array`, `robust_plane_detrend`, `display_shear_grid` — all in `src/nsf_fmrg_data.py`, all operate on plain NumPy arrays with no file I/O, making them straightforward to test with synthetic inputs.

**Integration Tests:** None exist. Functions that touch the filesystem or require real experimental data (`find_track_file`, `extract_final_thermal_frames`, `get_sem_tile_paths`, `load_sem_tile`, `parse_wyko_header`, `load_wyko_asc`) would need integration-style tests with sample fixture files (e.g., a small `.mat`/`.asc`/`.tif` fixture) rather than unit tests.

**E2E Tests:** Not used. `scripts/run_thermal_video_export.py` is exercised manually via CLI invocation, not via an automated end-to-end test.

## Verification Approach Actually Used

In the absence of automated tests, the project's de facto verification method is:
1. Running the Jupyter notebooks in `notebooks/` against real sample data and visually inspecting plots/outputs.
2. Running `scripts/run_thermal_video_export.py` as a CLI script and inspecting the resulting `.mp4` output manually.

## Recommendations for Adding Tests

If introducing a test suite for this codebase:
- Add `pytest` to `requirements.txt` (or a new `requirements-dev.txt`) as the runner has no existing convention to conflict with.
- Start with unit tests for the pure-array functions listed above under "Unit Tests," using small synthetic NumPy arrays (no need for real experimental data).
- Place tests in a new top-level `tests/` directory mirroring `src/`, e.g. `tests/test_nsf_fmrg_data.py`, since no existing test directory convention exists to follow.
- For file-parsing functions (`parse_wyko_header`, `load_wyko_asc`, `find_track_file`), create minimal synthetic fixture files under `tests/fixtures/` rather than relying on the real (Git-LFS-tracked) dataset in `data/`.

---

*Testing analysis: 2026-07-19*
</content>
