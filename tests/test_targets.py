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


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def test_target_grid_matches_thermal_centers():
    grid = targets.target_grid()
    stop_idx = nsf_fmrg_data.EXTRACTED_THERMAL_FRAMES
    indices = np.arange(stop_idx)
    thermal_centers = nsf_fmrg_data.COMMON_X_END_MM - (
        (stop_idx - indices) - 0.5
    ) * nsf_fmrg_data.THERMAL_MM_PER_FRAME

    require(grid.shape == (400,), "target grid must contain 400 slots")
    require(np.isclose(grid[0], 20.1), "target grid must start at 20.1 mm")
    require(np.isclose(grid[-1], 99.9), "target grid must end at 99.9 mm")
    require(np.allclose(np.diff(grid), 0.2), "target grid spacing must be 0.2 mm")
    require(np.allclose(grid, np.sort(thermal_centers)), "target grid must match thermal centers")


def test_gap_rule_exact_boundary_and_no_extrapolation():
    base = np.linspace(0.0, 1.0, 480)

    interior_ten = base.copy()
    interior_ten[200:210] = np.nan
    filled, ok = targets.fill_small_gaps(interior_ten)
    require(ok, "an interior gap of exactly ten pixels must be accepted")
    require(np.isfinite(filled).all(), "an accepted interior gap must be filled")

    interior_eleven = base.copy()
    interior_eleven[200:211] = np.nan
    _, ok = targets.fill_small_gaps(interior_eleven)
    require(not ok, "an interior gap of eleven pixels must be rejected")

    leading_eight = base.copy()
    leading_eight[:8] = np.nan
    filled, ok = targets.fill_small_gaps(leading_eight)
    require(ok, "a leading gap within the limit must preserve the profile")
    require(np.isnan(filled[:8]).all(), "leading gaps must not be extrapolated")
    require(np.isfinite(filled[8:]).all(), "finite values after a leading gap must be preserved")

    leading_eleven = base.copy()
    leading_eleven[:11] = np.nan
    _, ok = targets.fill_small_gaps(leading_eleven)
    require(not ok, "a leading gap of eleven pixels must be rejected")


def test_halfmax_edges_for_rectangular_bump():
    y_mm = np.arange(480, dtype=np.float64) * 0.004
    prof = np.zeros(480, dtype=np.float64)
    prof[160:320] = 0.02
    edges = targets.halfmax_edges(prof, y_mm)

    require(edges is not None, "a rectangular bump must produce two edges")
    y_lower, y_upper = edges
    expected_lower = 0.5 * (y_mm[159] + y_mm[160])
    expected_upper = 0.5 * (y_mm[319] + y_mm[320])
    require(abs(y_lower - expected_lower) <= np.diff(y_mm).max(), "lower edge must be interpolated within one sample")
    require(abs(y_upper - expected_upper) <= np.diff(y_mm).max(), "upper edge must be interpolated within one sample")
    require(y_upper > y_lower, "upper edge must be strictly above lower edge")


def test_noise_floor_exact_boundary_is_valid():
    y_mm = np.arange(480, dtype=np.float64) * 0.004
    prof = np.zeros(480, dtype=np.float64)
    prof[160:320] = targets.MIN_PEAK_BASELINE_SEPARATION_MM

    require(targets.halfmax_edges(prof, y_mm) is not None, "exact noise-floor separation must be valid")
    require(targets.halfmax_edges(0.8 * prof, y_mm) is None, "sub-threshold separation must be invalid")


def test_boundary_clipped_runs_are_invalid():
    y_mm = np.arange(480, dtype=np.float64) * 0.004
    leading = np.zeros(480, dtype=np.float64)
    trailing = np.zeros(480, dtype=np.float64)
    leading[:120] = 0.02
    trailing[-120:] = 0.02

    require(targets.halfmax_edges(leading, y_mm) is None, "leading clipped runs must be invalid")
    require(targets.halfmax_edges(trailing, y_mm) is None, "trailing clipped runs must be invalid")


def test_all_true_runs_finds_every_contiguous_block():
    mask = np.zeros(24, dtype=bool)
    mask[1:4] = True
    mask[7:13] = True
    mask[18:20] = True

    runs = targets.all_true_runs(mask)
    require(runs == [(1, 4), (7, 13), (18, 20)], "all contiguous runs must be returned in order")
    require(
        max(runs, key=lambda run: run[1] - run[0]) == nsf_fmrg_data.largest_true_run(mask),
        "the longest enumerated run must match largest_true_run",
    )


def _two_blob_profile():
    y_mm = np.arange(480, dtype=np.float64) * 0.004
    prof = np.zeros(480, dtype=np.float64)
    prof[90:140] = 0.02
    prof[250:330] = 0.02
    return prof, y_mm


def test_halfmax_edges_prefers_largest_run_without_previous_center():
    prof, y_mm = _two_blob_profile()
    edges = targets.halfmax_edges(prof, y_mm, previous_center=None)

    require(edges is not None, "a two-blob profile must produce tracked edges")
    require(np.isclose(np.mean(edges), 0.5 * (y_mm[249] + y_mm[330])), "untracked selection must use the larger run")


def test_halfmax_edges_tracks_nearest_run_to_previous_center():
    prof, y_mm = _two_blob_profile()
    previous_center = 0.5 * (y_mm[89] + y_mm[140])
    edges = targets.halfmax_edges(prof, y_mm, previous_center=previous_center)

    require(edges is not None, "a tracked two-blob profile must produce edges")
    require(np.isclose(np.mean(edges), previous_center), "tracking history must select the nearer smaller run")


def test_halfmax_edges_excludes_clipped_runs_from_tracking_candidates():
    y_mm = np.arange(480, dtype=np.float64) * 0.004
    prof = np.zeros(480, dtype=np.float64)
    prof[:80] = 0.02
    prof[240:300] = 0.02
    edges = targets.halfmax_edges(prof, y_mm, previous_center=y_mm[20])

    require(edges is not None, "an unclipped alternative must remain selectable")
    require(np.mean(edges) > y_mm[200], "tracking must never select the nearer boundary-clipped run")


def _binned_synthetic_profiles(profile_by_bin):
    bin_count = max(profile_by_bin) + 1
    x_actual_mm = 20.0 + 0.004 * np.arange(50 * bin_count, dtype=np.float64)
    y_mm = 0.004 * np.arange(480, dtype=np.float64)
    Zd = np.zeros((len(y_mm), len(x_actual_mm)), dtype=np.float64)
    for bin_index, profile in profile_by_bin.items():
        Zd[:, 50 * bin_index:50 * (bin_index + 1)] = profile[:, None]
    return Zd, x_actual_mm, y_mm


def test_extract_targets_from_arrays_boundary_tracking_survives_decoy_blob():
    y_mm = 0.004 * np.arange(480, dtype=np.float64)
    bead = np.zeros(480, dtype=np.float64)
    bead[100:170] = 0.02
    competing = bead.copy()
    competing[270:360] = 0.02
    profiles = {index: bead.copy() for index in range(7)}
    profiles[3] = competing
    Zd, x_actual_mm, y_mm = _binned_synthetic_profiles(profiles)

    untracked = targets.halfmax_edges(competing, y_mm, previous_center=None)
    require(untracked is not None and np.mean(untracked) > 1.0, "test decoy must reproduce the old largest-run selection")

    result = targets.extract_targets_from_arrays(Zd, x_actual_mm, y_mm)
    neighbor_center = np.nanmean([
        np.mean([result["y_lower_mm"][2], result["y_upper_mm"][2]]),
        np.mean([result["y_lower_mm"][4], result["y_upper_mm"][4]]),
    ])
    tracked_center = np.mean([result["y_lower_mm"][3], result["y_upper_mm"][3]])
    require(abs(tracked_center - neighbor_center) < 0.05, "the full pipeline must stay on the continuous bead through a decoy bin")


def test_halfmax_edges_resets_stale_history_after_long_invalid_gap():
    y_mm = 0.004 * np.arange(480, dtype=np.float64)
    anchor = np.zeros(480, dtype=np.float64)
    anchor[80:140] = 0.02
    resumed = np.zeros(480, dtype=np.float64)
    resumed[290:380] = 0.02
    resumed_with_decoy = resumed.copy()
    resumed_with_decoy[85:135] = 0.02
    gap_profile = np.zeros(480, dtype=np.float64)

    base_profiles = {0: anchor}
    base_profiles.update({index: gap_profile for index in range(1, targets.MAX_TRACKING_GAP_COLUMNS + 1)})
    base_profiles[targets.MAX_TRACKING_GAP_COLUMNS + 1] = resumed
    Zd, x_actual_mm, y_mm = _binned_synthetic_profiles(base_profiles)
    no_decoy = targets.extract_targets_from_arrays(Zd, x_actual_mm, y_mm)
    resume_index = targets.MAX_TRACKING_GAP_COLUMNS + 1
    require(
        np.mean([no_decoy["y_lower_mm"][resume_index], no_decoy["y_upper_mm"][resume_index]]) > 1.0,
        "the drifted bead must remain detectable after a long gap",
    )

    stale_center = 0.5 * (y_mm[79] + y_mm[140])
    stale_edges = targets.halfmax_edges(resumed_with_decoy, y_mm, previous_center=stale_center)
    require(stale_edges is not None and np.mean(stale_edges) < 1.0, "a stale anchor alone must prefer the planted decoy")

    base_profiles[resume_index] = resumed_with_decoy
    Zd, x_actual_mm, y_mm = _binned_synthetic_profiles(base_profiles)
    tracked = targets.extract_targets_from_arrays(Zd, x_actual_mm, y_mm)
    resumed_center = np.mean([tracked["y_lower_mm"][resume_index], tracked["y_upper_mm"][resume_index]])
    require(resumed_center > 1.0, "stale history must reset so the largest drifted bead wins after the long gap")


def test_nan_savgol_preserves_mask():
    values = np.linspace(-1.0, 1.0, 21) ** 2
    values[[2, 8, 9, 17]] = np.nan
    smoothed = targets.nan_savgol(values)

    require(np.array_equal(np.isfinite(smoothed), np.isfinite(values)), "smoothing must preserve the finite mask")


def test_nan_savgol_preserves_quadratic_at_crop_edges():
    x = np.arange(21, dtype=np.float64)
    values = 0.3 * x**2 - 2.0 * x + 5.0
    smoothed = targets.nan_savgol(values)

    require(np.allclose(smoothed[1:-1], values[1:-1], atol=1e-10), "quadratic data with four-point support must survive smoothing")
    left_reference = np.polyval(np.polyfit([0, 1, 2], values[:3], 1), 0.0)
    right_reference = np.polyval(np.polyfit([-2, -1, 0], values[-3:], 1), 0.0)
    require(
        np.allclose(smoothed[[0, -1]], [left_reference, right_reference], atol=1e-10),
        "G-01-3 crop-edge fits must match the independent degree-one reference",
    )
    require(not np.isclose(left_reference, values[0]), "the left three-point fit must genuinely damp the quadratic edge")
    require(not np.isclose(right_reference, values[-1]), "the right three-point fit must genuinely damp the quadratic edge")


def test_nan_savgol_blends_across_masked_gaps():
    x = np.arange(11, dtype=np.float64)
    expected = 0.25 * x**2 + 1.5 * x - 3.0
    values = expected.copy()
    values[[4, 6]] = np.nan
    smoothed = targets.nan_savgol(values)

    center_reference = np.polyval(np.polyfit([-2, 0, 2], values[[3, 5, 7]], 1), 0.0)
    require(np.isclose(smoothed[5], center_reference, atol=1e-10), "three-point gap fit must match the degree-one reference")
    require(not np.isclose(center_reference, expected[5]), "three-point gap support must genuinely damp the quadratic center")
    require(np.isclose(smoothed[3], expected[3], atol=1e-10), "left fit may blend across a masked neighbor")
    require(np.isclose(smoothed[7], expected[7], atol=1e-10), "right fit may blend across a masked neighbor")


def test_nan_savgol_no_longer_exact_interpolates_three_point_window():
    values = np.array([np.nan, 0.0, 10.0, 0.0, np.nan])
    smoothed = targets.nan_savgol(values)

    require(np.isfinite(smoothed[2]), "the three-point center fit must remain finite")
    require(not np.isclose(smoothed[2], values[2]), "three-point support must damp rather than exactly interpolate noise")


def test_nan_savgol_track10_crop_edge_regression():
    values = np.array([1.0, 1.1, 0.9, 1.0, np.nan, np.nan, np.nan, 0.0, 10.0, 0.0])
    smoothed = targets.nan_savgol(values)

    require(np.isfinite(smoothed[-3:]).all(), "the final Track-10-shaped run must remain finite")
    require(
        not np.array_equal(smoothed[-3:], values[-3:]),
        "the final three-point run after a three-column gap must not pass through bit-identically",
    )
    require(np.all(np.abs(smoothed[-3:] - values[-3:]) > 1e-6), "all three terminal points must receive real damping")


def test_single_parameterization_has_no_track_conditionals():
    source = (SRC_DIR / "targets.py").read_text()
    track_conditional = re.compile(
        r"\bif\s+track_id\b|\btrack_id\s*(?:==|!=|<=|>=|<|>|\bin\b)"
    )

    require(track_conditional.search(source) is None, "target extraction must not branch on track id")


def test_track_id_does_not_affect_numeric_output():
    # Behavioral guard for TARGET-02: even parameterizations that dodge the
    # regex above (e.g. PARAMS_BY_TRACK[track_id], match statements) must
    # still fail this, since it drives identical input data through
    # extract_track_targets under two different track ids and requires
    # bit-identical numeric output.
    x_actual_mm = 20.0 + 0.004 * np.arange(2000, dtype=np.float64)
    y_mm = 0.004 * np.arange(480, dtype=np.float64)
    Z_mm = np.zeros((len(y_mm), len(x_actual_mm)), dtype=np.float64)
    ridge = (y_mm >= 0.65) & (y_mm <= 1.25)
    Z_mm[ridge, :] = 0.02

    def fake_loader(height_dir, track_id):
        return {
            "file": f"Heightmap_{track_id}.ASC",
            "header": {"pixel_size_mm": 0.004},
            "Z_mm": Z_mm.copy(),
            "x_actual_mm": x_actual_mm.copy(),
            "y_mm": y_mm.copy(),
        }

    original_loader = targets.load_wyko_asc
    targets.load_wyko_asc = fake_loader
    try:
        result_a = targets.extract_track_targets(Path("unused"), 8)
        result_b = targets.extract_track_targets(Path("unused"), 21)
    finally:
        targets.load_wyko_asc = original_loader

    require(result_a["track_id"] != result_b["track_id"], "test sanity: track ids must actually differ")
    numeric_keys = (
        "x_grid_mm", "w_mm", "y_upper_mm", "y_lower_mm", "valid_mask",
        "Z_mm", "Zd_mm", "x_actual_mm", "y_mm",
    )
    for key in numeric_keys:
        a = np.asarray(result_a[key])
        b = np.asarray(result_b[key])
        require(
            np.array_equal(a, b, equal_nan=True),
            f"{key} must be identical across track ids for identical input data",
        )


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
        "DETREND_POLY_ORDER": 4,
    }

    require(targets.extraction_params() == expected, "the exact 12-value extraction parameterization changed")


def test_post_smoothing_crossing_is_invalidated():
    y_lower_raw = np.zeros(5, dtype=np.float64)
    y_upper_raw = np.array([1.0, 0.1, 0.1, 0.1, 1.0], dtype=np.float64)

    require(np.all(y_upper_raw > y_lower_raw), "the reproducer must begin with positive raw separation")
    independently_smoothed = targets.nan_savgol(y_upper_raw) - targets.nan_savgol(y_lower_raw)
    require(independently_smoothed[2] <= 0.0, "the current smoother must cross at the center")

    y_lower, y_upper, width, valid_mask = targets.finalize_smoothed_boundaries(
        y_lower_raw,
        y_upper_raw,
    )
    require(not valid_mask[2], "a post-smoothing crossing must be invalid")
    require(np.isnan(y_lower[2]), "an invalid lower boundary must be NaN")
    require(np.isnan(y_upper[2]), "an invalid upper boundary must be NaN")
    require(np.isnan(width[2]), "an invalid width must be NaN")
    require(np.all(np.isfinite(y_lower[valid_mask])), "valid lower boundaries must be finite")
    require(np.all(np.isfinite(y_upper[valid_mask])), "valid upper boundaries must be finite")
    require(np.all(y_upper[valid_mask] > y_lower[valid_mask]), "valid boundaries must remain strictly ordered")


def test_post_smoothing_zero_valid_raises_value_error():
    y_lower_raw = np.zeros(5, dtype=np.float64)
    y_upper_raw = np.zeros(5, dtype=np.float64)

    try:
        targets.finalize_smoothed_boundaries(y_lower_raw, y_upper_raw)
    except ValueError as exc:
        require("zero valid" in str(exc).lower(), "zero-valid error must identify the condition")
    else:
        raise AssertionError("Expected ValueError after post-smoothing revalidation removes every slot")


def test_all_invalid_track_raises_value_error():
    x_actual_mm = np.arange(20.0, 20.4, 0.004)
    y_mm = np.arange(480, dtype=np.float64) * 0.004
    Zd = np.zeros((len(y_mm), len(x_actual_mm)), dtype=np.float64)

    try:
        targets.extract_targets_from_arrays(Zd, x_actual_mm, y_mm)
    except ValueError as exc:
        require("zero valid" in str(exc).lower(), "all-invalid extraction must identify the zero-valid condition")
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

    require(set(result) == {
        "x_grid_mm",
        "w_mm",
        "y_upper_mm",
        "y_lower_mm",
        "valid_mask",
    }, "extraction result keys changed")
    require(all(np.asarray(value).shape == (400,) for value in result.values()), "every result array must retain the shared grid")
    require(np.array_equal(result["valid_mask"], coverage), "valid mask must match synthetic x coverage")
    require(np.allclose(result["w_mm"][coverage], 0.6, atol=0.05), "synthetic width must remain near 0.6 mm")
    require(np.array_equal(np.isfinite(result["w_mm"]), result["valid_mask"]), "width finiteness must equal the mask")
    require(
        np.allclose(
            result["w_mm"][coverage],
            result["y_upper_mm"][coverage] - result["y_lower_mm"][coverage],
        ),
        "valid widths must equal upper minus lower",
    )
    require(np.isnan(result["w_mm"][~coverage]).all(), "invalid widths must be NaN")


if __name__ == "__main__":
    tests = [
        test_target_grid_matches_thermal_centers,
        test_gap_rule_exact_boundary_and_no_extrapolation,
        test_halfmax_edges_for_rectangular_bump,
        test_noise_floor_exact_boundary_is_valid,
        test_boundary_clipped_runs_are_invalid,
        test_all_true_runs_finds_every_contiguous_block,
        test_halfmax_edges_prefers_largest_run_without_previous_center,
        test_halfmax_edges_tracks_nearest_run_to_previous_center,
        test_halfmax_edges_excludes_clipped_runs_from_tracking_candidates,
        test_extract_targets_from_arrays_boundary_tracking_survives_decoy_blob,
        test_halfmax_edges_resets_stale_history_after_long_invalid_gap,
        test_nan_savgol_preserves_mask,
        test_nan_savgol_preserves_quadratic_at_crop_edges,
        test_nan_savgol_blends_across_masked_gaps,
        test_nan_savgol_no_longer_exact_interpolates_three_point_window,
        test_nan_savgol_track10_crop_edge_regression,
        test_single_parameterization_has_no_track_conditionals,
        test_track_id_does_not_affect_numeric_output,
        test_extraction_params_provenance,
        test_post_smoothing_crossing_is_invalidated,
        test_post_smoothing_zero_valid_raises_value_error,
        test_all_invalid_track_raises_value_error,
        test_synthetic_end_to_end_fixed_grid_and_width,
    ]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
