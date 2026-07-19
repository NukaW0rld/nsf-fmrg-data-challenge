# Codebase Concerns

**Analysis Date:** 2026-07-19

## Overview

This repository is a small data-loading/starter-code toolkit for the NSF Future Manufacturing Data Challenge (multimodal DED laser track dataset: thermal `.mat` videos, SEM images, Bruker/Wyko `.asc` height maps). It is not a production application — it is exploratory/scientific starter code (`src/nsf_fmrg_data.py`, `scripts/run_thermal_video_export.py`, two Jupyter notebooks). Concerns below reflect the risks appropriate to that context: data-parsing fragility, missing dependency declarations, and lack of automated testing, rather than typical web-app security/scaling issues.

## Tech Debt

**No test suite:**
- Issue: There are no unit tests anywhere in the repo for the core parsing/processing logic in `src/nsf_fmrg_data.py`.
- Files: `src/nsf_fmrg_data.py`, `scripts/run_thermal_video_export.py`
- Impact: Any change to MAT-file array detection, Wyko `.asc` parsing, or thermal on/off detection cannot be verified except by manually re-running notebooks against the sample dataset.
- Fix approach: Add `pytest` with small synthetic fixtures (fake `.mat` dict, fake `.asc` text) covering `find_thermal_array`, `parse_wyko_header`, `load_wyko_asc`, and `detect_laser_on_interval`.

**Undeclared dependencies in `requirements.txt`:**
- Issue: `requirements.txt` lists only `numpy, scipy, matplotlib, pillow, pandas`. `src/nsf_fmrg_data.py:39` conditionally imports `h5py` (used for MATLAB v7.3/HDF5-format `.mat` files), and `scripts/run_thermal_video_export.py` uses `matplotlib.animation.FFMpegWriter`, which requires an external `ffmpeg` binary. Neither is declared.
- Files: `requirements.txt`, `src/nsf_fmrg_data.py:39`, `scripts/run_thermal_video_export.py:66`
- Impact: `pip install -r requirements.txt` followed by running the video export script or loading newer-format `.mat` thermal files will fail with `ImportError`/`FileNotFoundError` on a clean environment.
- Fix approach: Add `h5py` to `requirements.txt`; document the `ffmpeg` system dependency in README or add a `pandas`/`jupyter` note if notebooks require it (also not declared).

**`jupyter`/notebook runtime not declared:**
- Issue: Two `.ipynb` notebooks exist (`notebooks/01_starter_code_loading_and_visualization.ipynb`, `notebooks/02_..._standalone_colab.ipynb`) but no `jupyter`/`notebook`/`ipykernel` dependency is listed in `requirements.txt`.
- Files: `requirements.txt`, `notebooks/`
- Impact: Local (non-Colab) users following the README must separately discover and install Jupyter tooling.
- Fix approach: Add a note or optional extras group for local notebook execution.

**Heuristic/magic-number-driven data parsing:**
- Issue: Core extraction logic in `src/nsf_fmrg_data.py` relies on heuristics and hard-coded constants rather than explicit schema validation: `find_thermal_array` (`src/nsf_fmrg_data.py:52-81`) guesses which array in a `.mat` file is the thermal stack by scoring shape/size (`400 in arr.shape` gets a 10x bonus at line 68), and `detect_laser_on_interval` (`src/nsf_fmrg_data.py:100-111`) uses fixed multipliers (`0.20`, `8.0`, `1.4826`) to threshold laser-on frames.
- Files: `src/nsf_fmrg_data.py:52-81`, `src/nsf_fmrg_data.py:100-111`
- Impact: Silently wrong array selection or laser-interval detection for tracks whose `.mat` layout or thermal signal profile differs from the 4 sample tracks (8, 10, 14, 21) used to write the heuristics. There is no validation/assertion step that surfaces a wrong guess to the user.
- Fix approach: Add sanity-check assertions/logging (e.g., warn if the winning array's score margin over runner-up is small) and document the assumptions inline.

**Default pixel size silently substituted on parse failure:**
- Issue: `load_wyko_asc` (`src/nsf_fmrg_data.py:165`) falls back to a hard-coded default `pixel_size_mm=0.003982` if `parse_wyko_header` fails to find a `PIXEL_SIZE` line, with no warning emitted.
- Files: `src/nsf_fmrg_data.py:165`
- Impact: A malformed or differently-formatted `.asc` header would silently produce height maps with an incorrect physical scale, without any error or log message.
- Fix approach: Log a warning (or raise) when `pixel_size_mm` is missing from the header and the default is used.

## Known Bugs

**No explicit "file not found" handling in `find_track_file`:**
- Symptoms: `find_track_file` (`src/nsf_fmrg_data.py:21-31`) returns `None` when no match is found rather than raising. Callers (`extract_final_thermal_frames` line 115, `load_wyko_asc` line 161) pass this directly into `_loadmat_any(path)` / `open(path, ...)` without a None-check.
- Files: `src/nsf_fmrg_data.py:115`, `src/nsf_fmrg_data.py:161`
- Trigger: Calling `extract_final_thermal_frames(thermal_dir, track_id)` or `load_wyko_asc(height_dir, track_id)` with a `track_id` that has no matching file in the given directory.
- Workaround: None currently; results in a confusing low-level `TypeError` (e.g. `path.suffix` on `NoneType` inside `loadmat`/`open`) instead of a clear "track not found" error.

**`get_sem_tile_paths` has no missing-directory guard:**
- Symptoms: `get_sem_tile_paths` (`src/nsf_fmrg_data.py:133-137`) directly calls `root.iterdir()` on `Path(sem_dir) / f'SEM_{track_id}' / 'PlainImages'` without checking existence.
- Files: `src/nsf_fmrg_data.py:133-137`
- Trigger: Passing a `track_id` whose SEM subdirectory doesn't exist (e.g., any ID other than 8, 10, 14, 21) raises an unhandled `FileNotFoundError` from `iterdir()`.
- Workaround: None; caller must pre-validate track IDs against known dataset tracks.

## Security Considerations

**Low overall risk — offline scientific/data-analysis tool.**
- Risk: The codebase does no network I/O, has no auth/credentials, and does not appear to execute user-supplied code beyond standard file parsing. `scipy.io.loadmat` and `h5py.File` used in `_loadmat_any` (`src/nsf_fmrg_data.py:34-49`) parse binary MAT files; malicious/malformed `.mat` files could in principle trigger crashes via these third-party libraries, but this is an inherent risk of the file formats, not a bug introduced here.
- Files: `src/nsf_fmrg_data.py:34-49`
- Current mitigation: None needed given trusted-dataset usage context (competition-provided files via git-lfs, `data/raw/**`).
- Recommendations: No action needed unless this code is repurposed to accept untrusted uploads.

## Performance Bottlenecks

**Row-by-row parsing of large `.asc` height-map files:**
- Problem: `load_wyko_asc` (`src/nsf_fmrg_data.py:171-184`) parses the Wyko `.asc` file line-by-line in pure Python (`for line in f: ... parts = line.strip().split()`), writing one float at a time into a pre-allocated array.
- Files: `src/nsf_fmrg_data.py:171-184`
- Cause: No use of vectorized parsing (e.g., `numpy.loadtxt`/`genfromtxt` or pandas `read_csv`) despite pandas already being a declared dependency (`requirements.txt`).
- Improvement path: Replace the manual per-line loop with a vectorized read (e.g., `pandas.read_csv` with `skiprows` computed from the `RAW_DATA` marker) for large height maps, especially if the dataset scales beyond the 4 sample tracks.

**Full-resolution decimated but still O(n) plane fit per call:**
- Problem: `robust_plane_detrend` (`src/nsf_fmrg_data.py:205-227`) iterates up to 3 times performing `np.linalg.lstsq` over a strided subsample; this is reasonable but strides (`stride_x=40, stride_y=2`) are hard-coded and not adapted to input array size, so very large or very small height maps get a fixed, possibly suboptimal, sample density.
- Files: `src/nsf_fmrg_data.py:205-227`
- Cause: Fixed default stride parameters.
- Improvement path: Not urgent at current dataset scale (4 tracks); consider scaling strides to array shape if the dataset grows.

## Fragile Areas

**`find_thermal_array` shape-based heuristic (`src/nsf_fmrg_data.py:52-81`):**
- Files: `src/nsf_fmrg_data.py:52-81`
- Why fragile: Determines which variable in a `.mat` file is the "thermal" array purely from ndim/dtype/shape scoring; any MAT file with multiple 3D numeric arrays of similar size, or a differently-shaped thermal array (not containing `400` in its shape), could select the wrong array without error.
- Safe modification: Add assertions on final `arr_t.shape` (e.g., expected 400x400 frame size from `data/dataset_readme.txt`) before returning, and unit-test with synthetic multi-array `.mat` dicts.
- Test coverage: None (no tests exist).

**`.asc` header parsing (`parse_wyko_header`, `src/nsf_fmrg_data.py:144-157`):**
- Files: `src/nsf_fmrg_data.py:144-157`
- Why fragile: Parses header fields by exact lowercase string match on tokens (`'x'`, `'size'`, `'pixel_size'`) and breaks at the literal `RAW_DATA` marker; any variation in Bruker/Wyko export format (extra whitespace patterns already handled via `.split()`, but different key names would silently fail) is not caught.
- Safe modification: Validate that `x_size`/`y_size` keys were actually found before use in `load_wyko_asc` (currently accessed via `header['x_size']` at line 163, which will raise `KeyError` with a low-level, non-descriptive message if missing).
- Test coverage: None.

**`detect_laser_on_interval` threshold heuristic (`src/nsf_fmrg_data.py:100-111`):**
- Files: `src/nsf_fmrg_data.py:100-111`
- Why fragile: Combines a percentile-range threshold and a MAD-based threshold with fixed multipliers tuned (implicitly) against the 4 sample tracks; no fallback or sanity check if `largest_true_run` returns `(None, None)` — this is passed directly into `stop_idx = int(on_stop)` in `extract_final_thermal_frames` (`src/nsf_fmrg_data.py:119`), which will raise `TypeError: int() argument must be ... not 'NoneType'` with no context if no laser-on interval is detected.
- Safe modification: Add explicit error handling/messaging when `on_stop is None`.
- Test coverage: None.

## Scaling Limits

**Not applicable at current scope.** The dataset is fixed at 4 tracks (8, 10, 14, 21) via git-lfs (`data/raw/height_maps`, `data/raw/sem`, `data/raw/thermal`, tracked per `.gitattributes`). The toolkit is designed for local/Colab exploratory use, not for processing arbitrary-scale data pipelines.

## Dependencies at Risk

**None identified.** Declared dependencies (`numpy`, `scipy`, `matplotlib`, `pillow`, `pandas`) are all mainstream, actively maintained scientific Python packages. See "Tech Debt" above for *undeclared* dependencies (`h5py`, `ffmpeg`, Jupyter tooling), which is the primary dependency-related risk.

## Missing Critical Features

**No CLI/notebook entry point validates track IDs against the dataset:**
- Problem: Nothing in `src/nsf_fmrg_data.py` or `scripts/run_thermal_video_export.py` enumerates valid track IDs; the only way a user learns valid IDs (8, 10, 14, 21) is by reading `--track_id` help text in `scripts/run_thermal_video_export.py:76` or inspecting `data/raw/`.
- Blocks: Fast, clear failure feedback for users experimenting with the starter code on IDs outside the sample set.

## Test Coverage Gaps

**Entire `src/nsf_fmrg_data.py` module untested:**
- What's not tested: `find_track_file`, `_loadmat_any`, `find_thermal_array`, `thermal_frame_score`, `largest_true_run`, `detect_laser_on_interval`, `extract_final_thermal_frames`, `get_sem_tile_paths`, `load_sem_tile`, `parse_wyko_header`, `load_wyko_asc`, `robust_plane_detrend`, `display_shear_grid`.
- Files: `src/nsf_fmrg_data.py`
- Risk: Any refactor (e.g., updating the MAT-array heuristic or `.asc` parsing) can silently break downstream notebook analysis with no automated signal.
- Priority: Medium — appropriate for a starter-code/competition repo, but worth adding lightweight tests if the module is extended or reused across more tracks.

**`scripts/run_thermal_video_export.py` untested:**
- What's not tested: `save_video()` end-to-end behavior (relies on `ffmpeg` availability, which is itself undeclared as a dependency).
- Files: `scripts/run_thermal_video_export.py`
- Risk: Silent failures if `ffmpeg` is missing (`FFMpegWriter` raises at `ani.save()`, line 67) are only caught at runtime, not via any pre-flight check.
- Priority: Low — script is a convenience/demo utility, not core logic.

---

*Concerns audit: 2026-07-19*
