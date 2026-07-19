from pathlib import Path
import re
import sys

import numpy as np

# Allow running from repo root without installing as a package.
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

import nsf_fmrg_data
import targets


def test_target_grid_matches_thermal_centers():
    grid = targets.target_grid()
    stop_idx = nsf_fmrg_data.EXTRACTED_THERMAL_FRAMES
    indices = np.arange(stop_idx)
    thermal_centers = nsf_fmrg_data.COMMON_X_END_MM - (
        (stop_idx - indices) - 0.5
    ) * nsf_fmrg_data.THERMAL_MM_PER_FRAME

    assert grid.shape == (400,)
    assert np.isclose(grid[0], 20.1)
    assert np.isclose(grid[-1], 99.9)
    assert np.allclose(np.diff(grid), 0.2)
    assert np.allclose(grid, np.sort(thermal_centers))


def test_gap_rule_exact_boundary_and_no_extrapolation():
    base = np.linspace(0.0, 1.0, 480)

    interior_ten = base.copy()
    interior_ten[200:210] = np.nan
    filled, ok = targets.fill_small_gaps(interior_ten)
    assert ok
    assert np.isfinite(filled).all()

    interior_eleven = base.copy()
    interior_eleven[200:211] = np.nan
    _, ok = targets.fill_small_gaps(interior_eleven)
    assert not ok

    leading_eight = base.copy()
    leading_eight[:8] = np.nan
    filled, ok = targets.fill_small_gaps(leading_eight)
    assert ok
    assert np.isnan(filled[:8]).all()
    assert np.isfinite(filled[8:]).all()

    leading_eleven = base.copy()
    leading_eleven[:11] = np.nan
    _, ok = targets.fill_small_gaps(leading_eleven)
    assert not ok


def test_halfmax_edges_for_rectangular_bump():
    y_mm = np.arange(480, dtype=np.float64) * 0.004
    prof = np.zeros(480, dtype=np.float64)
    prof[160:320] = 0.02
    edges = targets.halfmax_edges(prof, y_mm)

    assert edges is not None
    y_lower, y_upper = edges
    expected_lower = 0.5 * (y_mm[159] + y_mm[160])
    expected_upper = 0.5 * (y_mm[319] + y_mm[320])
    assert abs(y_lower - expected_lower) <= np.diff(y_mm).max()
    assert abs(y_upper - expected_upper) <= np.diff(y_mm).max()
    assert y_upper > y_lower


def test_noise_floor_exact_boundary_is_valid():
    y_mm = np.arange(480, dtype=np.float64) * 0.004
    prof = np.zeros(480, dtype=np.float64)
    prof[160:320] = targets.MIN_PEAK_BASELINE_SEPARATION_MM

    assert targets.halfmax_edges(prof, y_mm) is not None
    assert targets.halfmax_edges(0.8 * prof, y_mm) is None


def test_boundary_clipped_runs_are_invalid():
    y_mm = np.arange(480, dtype=np.float64) * 0.004
    leading = np.zeros(480, dtype=np.float64)
    trailing = np.zeros(480, dtype=np.float64)
    leading[:120] = 0.02
    trailing[-120:] = 0.02

    assert targets.halfmax_edges(leading, y_mm) is None
    assert targets.halfmax_edges(trailing, y_mm) is None


def test_nan_savgol_preserves_mask():
    values = np.linspace(-1.0, 1.0, 21) ** 2
    values[[2, 8, 9, 17]] = np.nan
    smoothed = targets.nan_savgol(values)

    assert np.array_equal(np.isfinite(smoothed), np.isfinite(values))


def test_nan_savgol_preserves_quadratic_at_crop_edges():
    x = np.arange(21, dtype=np.float64)
    values = 0.3 * x**2 - 2.0 * x + 5.0
    smoothed = targets.nan_savgol(values)

    assert np.allclose(smoothed, values, atol=1e-10)
    assert np.allclose(smoothed[[0, 1, -2, -1]], values[[0, 1, -2, -1]], atol=1e-10)


def test_nan_savgol_blends_across_masked_gaps():
    x = np.arange(11, dtype=np.float64)
    expected = 0.25 * x**2 + 1.5 * x - 3.0
    values = expected.copy()
    values[[4, 6]] = np.nan
    smoothed = targets.nan_savgol(values)

    assert np.isclose(smoothed[5], expected[5], atol=1e-10)
    assert np.isclose(smoothed[3], expected[3], atol=1e-10)
    assert np.isclose(smoothed[7], expected[7], atol=1e-10)


def test_single_parameterization_has_no_track_conditionals():
    source = (SRC_DIR / "targets.py").read_text()
    track_conditional = re.compile(
        r"\bif\s+track_id\b|\btrack_id\s*(?:==|!=|<=|>=|<|>|\bin\b)"
    )

    assert track_conditional.search(source) is None


def test_extraction_params_provenance():
    expected = {
        "TARGET_GRID_START_MM": 20.1,
        "TARGET_GRID_STEP_MM": 0.2,
        "TARGET_GRID_N": 400,
        "BASELINE_PCT": 5.0,
        "PEAK_PCT": 95.0,
        "HALF_MAX_FRACTION": 0.5,
        "MIN_PEAK_BASELINE_SEPARATION_MM": 0.005,
        "MAX_GAP_PIXELS": 10,
        "SG_WINDOW_PTS": 5,
        "SG_POLYORDER": 2,
        "MIN_VALID_Y_POINTS": 50,
        "MIN_COLUMNS_PER_BIN": 10,
    }

    assert targets.extraction_params() == expected


def test_all_invalid_track_raises_value_error():
    x_actual_mm = np.arange(20.0, 20.4, 0.004)
    y_mm = np.arange(480, dtype=np.float64) * 0.004
    Zd = np.zeros((len(y_mm), len(x_actual_mm)), dtype=np.float64)

    try:
        targets.extract_targets_from_arrays(Zd, x_actual_mm, y_mm)
    except ValueError as exc:
        assert "zero valid" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError for an all-invalid target track")


def test_synthetic_end_to_end_fixed_grid_and_width():
    x_actual_mm = 20.0 + 0.004 * np.arange(2000, dtype=np.float64)
    y_mm = 0.004 * np.arange(480, dtype=np.float64)
    Zd = np.zeros((len(y_mm), len(x_actual_mm)), dtype=np.float64)
    ridge = (y_mm >= 0.65) & (y_mm <= 1.25)
    Zd[ridge, :] = 0.02

    result = targets.extract_targets_from_arrays(Zd, x_actual_mm, y_mm)
    grid = result["x_grid_mm"]
    coverage = (grid >= 20.1) & (grid < 28.0)

    assert set(result) == {
        "x_grid_mm",
        "w_mm",
        "y_upper_mm",
        "y_lower_mm",
        "valid_mask",
    }
    assert all(np.asarray(value).shape == (400,) for value in result.values())
    assert np.array_equal(result["valid_mask"], coverage)
    assert np.allclose(result["w_mm"][coverage], 0.6, atol=0.05)
    assert np.array_equal(np.isfinite(result["w_mm"]), result["valid_mask"])
    assert np.allclose(
        result["w_mm"][coverage],
        result["y_upper_mm"][coverage] - result["y_lower_mm"][coverage],
    )
    assert np.isnan(result["w_mm"][~coverage]).all()


if __name__ == "__main__":
    tests = [
        test_target_grid_matches_thermal_centers,
        test_gap_rule_exact_boundary_and_no_extrapolation,
        test_halfmax_edges_for_rectangular_bump,
        test_noise_floor_exact_boundary_is_valid,
        test_boundary_clipped_runs_are_invalid,
        test_nan_savgol_preserves_mask,
        test_nan_savgol_preserves_quadratic_at_crop_edges,
        test_nan_savgol_blends_across_masked_gaps,
        test_single_parameterization_has_no_track_conditionals,
        test_extraction_params_provenance,
        test_all_invalid_track_raises_value_error,
        test_synthetic_end_to_end_fixed_grid_and_width,
    ]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
