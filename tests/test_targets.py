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


def test_merge_adjacent_runs_bridges_short_below_threshold_gaps():
    max_gap = targets.MAX_RUN_MERGE_GAP_PIXELS

    exact_gap = [(0, 10), (10 + max_gap, 20 + max_gap)]
    merged = targets.merge_adjacent_runs(exact_gap, max_gap)
    require(merged == [(0, 20 + max_gap)], "a gap exactly at the merge limit must merge into one run")

    too_far = [(0, 10), (11 + max_gap, 20 + max_gap)]
    merged_too_far = targets.merge_adjacent_runs(too_far, max_gap)
    require(merged_too_far == too_far, "a gap one pixel beyond the merge limit must not merge")

    # Three runs each separated by small gaps -- mirrors Track 10's x~67.1mm
    # 3-way fragmentation into sub-runs of length 5/18/20 -- must all merge
    # into a single run spanning the full extent.
    fragmented = [(100, 105), (110, 128), (133, 153)]
    merged_fragmented = targets.merge_adjacent_runs(fragmented, max_gap)
    require(merged_fragmented == [(100, 153)], "three closely-spaced fragments must merge into one full-extent run")
    require(fragmented == [(100, 105), (110, 128), (133, 153)], "merge_adjacent_runs must not mutate the input list")


def test_merge_adjacent_runs_does_not_bridge_large_gaps():
    max_gap = targets.MAX_RUN_MERGE_GAP_PIXELS
    separated = [(0, 100), (100 + max_gap + 50, 200 + max_gap + 50)]
    merged = targets.merge_adjacent_runs(separated, max_gap)
    require(
        merged == separated,
        "two substantial runs separated by a gap larger than the merge limit must remain distinct",
    )


def test_halfmax_edges_rejects_implausibly_narrow_tracked_candidate():
    y_mm = np.arange(480, dtype=np.float64) * 0.004
    prof = np.zeros(480, dtype=np.float64)
    prof[90:140] = 0.02   # large, plausible candidate: len 50
    prof[200:205] = 0.02  # tiny candidate: len 5, far below 0.5 * 50 = 25
    previous_center = 0.5 * (y_mm[199] + y_mm[205])  # numerically nearer to the tiny candidate

    edges = targets.halfmax_edges(prof, y_mm, previous_center=previous_center)

    require(edges is not None, "a column with a plausible large candidate must still produce edges")
    require(
        np.isclose(np.mean(edges), 0.5 * (y_mm[89] + y_mm[140])),
        "the plausibility gate must select the large candidate over the nearer tiny one",
    )


def test_halfmax_edges_recovers_leading_edge_swallowed_interior_run():
    # Mechanism A (G-01-6, Amendment A8): mirrors track 10's chronic
    # y-index-0 leading edge. A raw run touching the LEADING boundary
    # (start == 0) sits within MAX_RUN_MERGE_GAP_PIXELS of an otherwise-valid
    # interior run. Under the old merge-then-clip ordering both were fused
    # and the whole fused span (including the legitimate interior run) was
    # discarded as edge-touching. Under the clip-before-merge fix, the
    # edge-touching raw run is filtered out before merging is ever
    # attempted, so the interior run must survive.
    y_mm = np.arange(480, dtype=np.float64) * 0.004
    prof = np.zeros(480, dtype=np.float64)
    prof[:10] = 0.02  # touches the leading boundary (start == 0)
    prof[15:400] = 0.02  # interior run, gap of 5 <= MAX_RUN_MERGE_GAP_PIXELS

    edges = targets.halfmax_edges(prof, y_mm, previous_center=None)
    require(edges is not None, "the surviving interior run must produce valid edges")
    y_lower, y_upper = edges
    expected_lower = 0.5 * (y_mm[14] + y_mm[15])
    expected_upper = 0.5 * (y_mm[399] + y_mm[400])
    require(np.isclose(y_lower, expected_lower), "lower edge must match the interior run's start")
    require(np.isclose(y_upper, expected_upper), "upper edge must match the interior run's stop")


def test_halfmax_edges_recovers_trailing_edge_swallowed_interior_run():
    # Mechanism A (G-01-6, Amendment A8): mirrors track 21's chronic
    # y-index-479 trailing edge, and replaces
    # test_merged_run_touching_boundary_remains_excluded (01-14/Amendment
    # A7) -- this EXACT fixture's correct outcome REVERSES under this fix:
    # under the old merge-then-clip ordering this asserted `edges is None`
    # (the interior run was swallowed by the trailing-edge-touching run);
    # under the clip-before-merge fix (this plan, 01-16,
    # .planning/debug/boundary-fragmentation-crop-edge-post-A7-visual-signoff.md
    # Mechanism A) the interior run is filtered from the boundary-touching
    # run BEFORE merging, so it must now survive and produce valid edges.
    y_mm = np.arange(480, dtype=np.float64) * 0.004
    prof = np.zeros(480, dtype=np.float64)
    prof[100:150] = 0.02  # interior run
    prof[155:480] = 0.02  # touches the trailing boundary, gap of 5 <= MAX_RUN_MERGE_GAP_PIXELS

    edges = targets.halfmax_edges(prof, y_mm, previous_center=None)
    require(edges is not None, "the surviving interior run must produce valid edges, not None")
    y_lower, y_upper = edges
    expected_lower = 0.5 * (y_mm[99] + y_mm[100])
    expected_upper = 0.5 * (y_mm[149] + y_mm[150])
    require(np.isclose(y_lower, expected_lower), "lower edge must match the interior run's start")
    require(np.isclose(y_upper, expected_upper), "upper edge must match the interior run's stop")


def _established_tracked_history(run_start=100, run_stop=300):
    # Establishes previous_center/previous_length_mm from a REAL
    # halfmax_edges call (not hand-derived numbers), per this plan's
    # <behavior> instruction for Tests 4-6.
    y_mm = np.arange(480, dtype=np.float64) * 0.004
    established = np.zeros(480, dtype=np.float64)
    established[run_start:run_stop] = 0.02
    established_edges = targets.halfmax_edges(established, y_mm, previous_center=None)
    previous_center = 0.5 * (established_edges[0] + established_edges[1])
    previous_length_mm = established_edges[1] - established_edges[0]
    return y_mm, previous_center, previous_length_mm


def test_halfmax_edges_rejects_lone_candidate_far_and_small_versus_tracked_history():
    # Mechanism B (G-01-6, Amendment A8): a single tiny candidate, both far
    # from previous_center (farther than previous_length_mm) and small
    # (below MIN_TRACKED_LENGTH_RATIO * previous_length_mm), with no
    # same-column competitor. The same-column MIN_TRACKED_LENGTH_RATIO gate
    # is structurally moot here (it trivially satisfies its own ratio) --
    # the new history-based joint far-AND-small gate must reject it.
    y_mm, previous_center, previous_length_mm = _established_tracked_history()
    prof = np.zeros(480, dtype=np.float64)
    prof[440:470] = 0.02  # small (len 30, 0.116mm << 0.4mm) and far (~1.02mm >> 0.8mm) from previous_center (~0.798mm)

    edges = targets.halfmax_edges(
        prof, y_mm, previous_center=previous_center, previous_length_mm=previous_length_mm,
    )
    require(edges is None, "a lone candidate both far and small versus tracked history must be rejected")


def test_halfmax_edges_accepts_lone_candidate_small_but_close_to_tracked_history():
    # Mechanism B: a single tiny candidate positioned CLOSE to
    # previous_center (within previous_length_mm) -- still small, but NOT
    # far. This proves the gate is a joint AND, not a size-only veto: a
    # plausible narrowing of the tracked bead must never be rejected.
    y_mm, previous_center, previous_length_mm = _established_tracked_history()
    prof = np.zeros(480, dtype=np.float64)
    prof[245:275] = 0.02  # small (len 30, 0.116mm << 0.4mm) but close (~0.24mm << 0.8mm) to previous_center (~0.798mm)

    edges = targets.halfmax_edges(
        prof, y_mm, previous_center=previous_center, previous_length_mm=previous_length_mm,
    )
    require(edges is not None, "a small-but-close lone candidate must not be rejected on size alone")


def test_halfmax_edges_accepts_lone_candidate_far_but_large_versus_tracked_history():
    # Mechanism B: a single candidate at least MIN_TRACKED_LENGTH_RATIO *
    # previous_length_mm in length, but farther than previous_length_mm from
    # previous_center. This proves distance alone never rejects a large
    # candidate (plausible drift/relocation).
    y_mm, previous_center, previous_length_mm = _established_tracked_history()
    prof = np.zeros(480, dtype=np.float64)
    prof[355:465] = 0.02  # large (len 110) but far from previous_center (~0.798mm)

    edges = targets.halfmax_edges(
        prof, y_mm, previous_center=previous_center, previous_length_mm=previous_length_mm,
    )
    require(edges is not None, "a far-but-large lone candidate must not be rejected on distance alone")


def test_extract_targets_from_arrays_recovers_from_track8_style_propagating_wrong_lock():
    # Mirrors the diagnosed Track 8 x=24.1-26.9mm episode
    # (.planning/debug/boundary-fragmentation-post-continuity-fix.md): a true
    # bead tracked correctly for several columns, then ONE column where only a
    # tiny fragment remains (the trigger), then several subsequent columns
    # where the true bead is present again alongside a tiny candidate near the
    # now-corrupted anchor (the propagation window).
    y_mm = 0.004 * np.arange(480, dtype=np.float64)
    true_bead = np.zeros(480, dtype=np.float64)
    true_bead[150:350] = 0.02  # len 200
    tiny_decoy = np.zeros(480, dtype=np.float64)
    tiny_decoy[10:40] = 0.02  # len 30, far below 0.5 * 200 = 100
    combined = true_bead.copy()
    combined[10:40] = 0.02

    profiles = {0: true_bead, 1: true_bead, 2: true_bead, 3: tiny_decoy}
    for index in range(4, 12):
        profiles[index] = combined
    profiles[12] = true_bead
    Zd, x_actual_mm, y_mm = _binned_synthetic_profiles(profiles)

    # WITHOUT the plausibility gate (documents the pre-fix behavior directly,
    # mirroring how 01-05's Test 5 first proved the old bug reproduces):
    # disabling the gate must reproduce the multi-column wrong lock.
    original_ratio = targets.MIN_TRACKED_LENGTH_RATIO
    try:
        targets.MIN_TRACKED_LENGTH_RATIO = 0.0
        unfixed = targets.extract_targets_from_arrays(Zd, x_actual_mm, y_mm)
        for index in range(4, 12):
            center = np.mean([unfixed["y_lower_mm"][index], unfixed["y_upper_mm"][index]])
            require(center < 0.5, f"pre-fix behavior must reproduce the wrong lock at column {index}")
    finally:
        targets.MIN_TRACKED_LENGTH_RATIO = original_ratio

    # WITH the gate (current, fixed behavior): tracking must recover onto the
    # true bead at the very next column where it is present, not stay locked.
    fixed = targets.extract_targets_from_arrays(Zd, x_actual_mm, y_mm)
    for index in range(4, 13):
        center = np.mean([fixed["y_lower_mm"][index], fixed["y_upper_mm"][index]])
        require(center > 0.5, f"the plausibility gate must stay on the true bead through column {index}")


def test_extract_targets_from_arrays_merges_track10_style_fragmented_bead():
    # Mirrors Track 10's x~67.1mm 3-way fragmentation: a true bead's
    # above-threshold run splits into 3 adjacent sub-runs (len 5/18/20)
    # separated by small below-threshold gaps.
    y_mm = 0.004 * np.arange(480, dtype=np.float64)
    fragmented = np.zeros(480, dtype=np.float64)
    fragmented[100:105] = 0.02
    fragmented[110:128] = 0.02
    fragmented[133:153] = 0.02
    profiles = {index: fragmented.copy() for index in range(8)}
    Zd, x_actual_mm, y_mm = _binned_synthetic_profiles(profiles)

    result = targets.extract_targets_from_arrays(Zd, x_actual_mm, y_mm)
    require(np.all(result["valid_mask"][:8]), "the merged bead must remain trackable across every column")
    expected_width = (153 - 100) * 0.004
    for index in range(8):
        require(
            abs(result["w_mm"][index] - expected_width) < 0.05,
            f"column {index} must report the merged bead's full width, not a narrow sub-fragment",
        )


def test_extract_targets_from_arrays_rejects_track8_style_single_candidate_trigger_column():
    # Mirrors Track 8's x=24.1/24.5/24.7/25.5mm single-candidate-column
    # episode (Mechanism B, G-01-6, Amendment A8) -- NOT covered by
    # test_extract_targets_from_arrays_recovers_from_track8_style_propagating_wrong_lock,
    # whose synthetic decoy always co-occurs with the true bead from the
    # recovery column onward rather than ever standing entirely alone. Here,
    # a true bead is tracked correctly for several columns, then ONE column
    # has ONLY a tiny far candidate (no competitor at all in that column),
    # then the true bead resumes. The trigger column must now be correctly
    # invalidated rather than wrongly locked onto the tiny candidate, and
    # the resumed columns must immediately recover onto the true bead.
    y_mm = 0.004 * np.arange(480, dtype=np.float64)
    true_bead = np.zeros(480, dtype=np.float64)
    true_bead[150:350] = 0.02  # len 200
    tiny_far_alone = np.zeros(480, dtype=np.float64)
    tiny_far_alone[10:20] = 0.02  # len 10, far from the true bead's center (~0.998mm)

    profiles = {
        0: true_bead, 1: true_bead, 2: true_bead, 3: true_bead,
        4: tiny_far_alone,
        5: true_bead, 6: true_bead,
    }
    Zd, x_actual_mm, y_mm = _binned_synthetic_profiles(profiles)

    result = targets.extract_targets_from_arrays(Zd, x_actual_mm, y_mm)
    require(not result["valid_mask"][4], "the single-candidate trigger column must be invalidated, not locked")
    for index in (5, 6):
        center = np.mean([result["y_lower_mm"][index], result["y_upper_mm"][index]])
        require(center > 0.5, f"column {index} must immediately recover onto the true bead")


def test_bead_mask_rule_is_track_independent():
    y_mm = np.arange(480, dtype=np.float64) * 0.004
    x_actual_mm = 20.0 + 0.004 * np.arange(50, dtype=np.float64)
    bead_rows = (y_mm >= 0.6) & (y_mm <= 0.8)

    def synthetic_track(bead_height):
        Z = np.zeros((len(y_mm), len(x_actual_mm)), dtype=np.float64)
        Z[bead_rows, :] = bead_height
        return Z

    low_track = synthetic_track(0.02)
    high_track = synthetic_track(0.2)

    low_mask = targets.bead_exclusion_mask(low_track)
    high_mask = targets.bead_exclusion_mask(high_track)

    require(low_mask.shape == low_track.shape, "the fit mask must match the input map shape")
    require(not low_mask[bead_rows, :].any(), "the low-height bead corridor must be excluded")
    require(not high_mask[bead_rows, :].any(), "the high-height bead corridor must be excluded")
    require(low_mask[~bead_rows, :].all(), "low-track background must remain included")
    require(high_mask[~bead_rows, :].all(), "high-track background must remain included")


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


def _edge_divergence_scenario(shelf_amplitude_mm):
    # Mirrors tests/test_nsf_fmrg_data.py's track-10-shaped scenario, but
    # exercised through the production targets.DETREND_POLY_ORDER /
    # targets.DETREND_MAX_Y_DEGREE constants, to prove the SAME committed
    # constant (not a per-track-tuned value) clears the criterion at two
    # substrate magnitudes ~44x apart -- roughly track 10's measured raw span
    # (~0.88mm) versus tracks 8/14/21's measured raw spans (~0.01-0.02mm),
    # per 01-11-DIAGNOSIS.md. The interior bead is masked explicitly (rather
    # than through targets.bead_exclusion_mask) so the deliberately-planted
    # near-edge shelf feature stays in the fit data at every amplitude --
    # bead_exclusion_mask's per-column percentile rule would otherwise also
    # exclude the tall-amplitude shelf itself, hiding the very divergence
    # this test exists to exercise.
    x_mm = np.linspace(20.0, 100.0, 2000)
    y_mm = np.linspace(0.0, 1.911, 480)
    x_grid, y_grid = np.meshgrid(x_mm, y_mm)

    centered_x = (x_grid - 60.0) / 40.0
    centered_y = (y_grid - 0.9555) / 0.9555
    substrate = 0.02 * centered_x - 0.01 * centered_y + 0.05

    shelf_frac = 0.06
    edge_band = y_mm < shelf_frac * y_mm[-1]
    shelf = np.zeros_like(y_grid)
    shelf[edge_band] = shelf_amplitude_mm * (1.0 - y_grid[edge_band] / (shelf_frac * y_mm[-1]))
    Z_mm = substrate + shelf

    bead_rows = (y_grid >= 0.8) & (y_grid <= 1.1)
    Z_mm = Z_mm.copy()
    Z_mm[bead_rows] += 0.2
    fit_mask = np.ones(Z_mm.shape, dtype=bool)
    fit_mask[bead_rows] = False
    return Z_mm, x_mm, y_mm, fit_mask


def test_edge_divergence_fix_is_track_independent():
    edge_tolerance_mm = 0.05
    # ~44x span ratio, matching 01-11-DIAGNOSIS.md's measured raw-span ratio
    # between track 10 (~0.88mm) and tracks 8/14/21 (~0.01-0.02mm).
    big_amplitude_mm = 0.5
    small_amplitude_mm = big_amplitude_mm / 44.0

    for label, amplitude_mm in (("big", big_amplitude_mm), ("small", small_amplitude_mm)):
        Z_mm, x_mm, y_mm, fit_mask = _edge_divergence_scenario(amplitude_mm)

        residual_fixed, coef_fixed = nsf_fmrg_data.robust_plane_detrend(
            Z_mm, x_mm, y_mm,
            order=targets.DETREND_POLY_ORDER,
            fit_mask=fit_mask,
            max_y_degree=targets.DETREND_MAX_Y_DEGREE,
        )
        require(coef_fixed is not None, f"{label}: the fixed fit must succeed")
        fitted_fixed = Z_mm - residual_fixed
        profile_fixed = np.median(fitted_fixed, axis=1)
        mid = len(profile_fixed) // 2
        require(
            abs(profile_fixed[0] - profile_fixed[mid]) <= edge_tolerance_mm,
            f"{label}: the shared DETREND_MAX_Y_DEGREE constant must clear the y=0 tolerance",
        )
        require(
            abs(profile_fixed[-1] - profile_fixed[mid]) <= edge_tolerance_mm,
            f"{label}: the shared DETREND_MAX_Y_DEGREE constant must clear the y=N tolerance",
        )

    # The fix is only load-bearing at the large (track-10-like) magnitude:
    # the small (track-8/14/21-like) magnitude already clears the tolerance
    # even with today's uncapped order=4-in-y fit, proving DETREND_MAX_Y_DEGREE
    # is a relative, structural correction rather than a value tuned to one
    # track's absolute scale.
    Z_big, x_mm, y_mm, fit_mask_big = _edge_divergence_scenario(big_amplitude_mm)
    residual_uncapped, coef_uncapped = nsf_fmrg_data.robust_plane_detrend(
        Z_big, x_mm, y_mm, order=targets.DETREND_POLY_ORDER, fit_mask=fit_mask_big,
    )
    require(coef_uncapped is not None, "the uncapped big-amplitude fit must succeed")
    fitted_uncapped = Z_big - residual_uncapped
    profile_uncapped = np.median(fitted_uncapped, axis=1)
    mid = len(profile_uncapped) // 2
    require(
        abs(profile_uncapped[0] - profile_uncapped[mid]) > edge_tolerance_mm,
        "the uncapped fit must still manufacture an edge feature at the large magnitude, "
        "confirming the fix (not the scenario) is what clears the tolerance there",
    )


def _xy_interaction_cap_scenario(scale):
    # Mirrors tests/test_nsf_fmrg_data.py's _track10_shaped_tail_collapse_scenario,
    # but exercised through the production targets.DETREND_POLY_ORDER /
    # targets.DETREND_MAX_Y_DEGREE / targets.DETREND_MAX_XY_DEGREE constants,
    # to prove the SAME committed constant (not a per-track-tuned value)
    # clears 01-13-CRITERION.md's tolerance at two substrate magnitudes 40x
    # apart -- the baseline (scale=1.0: bow=40x, shelf=0.6mm) is roughly
    # track-10-like per 01-13-CRITERION.md/the debug session's evidence;
    # scale=1/40 is roughly the other three tracks' much smaller magnitude.
    x_mm = np.linspace(20.0, 100.0, 2000)
    y_mm = np.linspace(0.0, 1.911, 480)
    x_grid, y_grid = np.meshgrid(x_mm, y_mm)

    centered_x = (x_grid - 60.0) / 40.0
    centered_y = (y_grid - 0.9555) / 0.9555
    bow_scale = 40.0 * scale
    shelf_amplitude_mm = 0.6 * scale
    quartic_bow = bow_scale * (0.08 * centered_x**4 - 0.03 * centered_x**2)
    substrate = 0.02 * centered_x - 0.01 * centered_y + 0.05 + quartic_bow

    shelf_frac = 0.06
    edge_band = y_mm < shelf_frac * y_mm[-1]
    shelf = np.zeros_like(y_grid)
    shelf[edge_band] = shelf_amplitude_mm * (1.0 - y_grid[edge_band] / (shelf_frac * y_mm[-1]))
    Z_mm = substrate + shelf

    bead_rows = (y_grid >= 0.8) & (y_grid <= 1.1)
    Z_mm = Z_mm.copy()
    Z_mm[bead_rows] += 0.2
    fit_mask = np.ones(Z_mm.shape, dtype=bool)
    fit_mask[bead_rows] = False
    return Z_mm, x_mm, y_mm, fit_mask


def _xy_interaction_shape_gap_departure(Z_mm, x_mm, y_mm, fit_mask, max_xy_degree):
    residual, coef = nsf_fmrg_data.robust_plane_detrend(
        Z_mm, x_mm, y_mm,
        order=targets.DETREND_POLY_ORDER,
        fit_mask=fit_mask,
        max_y_degree=targets.DETREND_MAX_Y_DEGREE,
        max_xy_degree=max_xy_degree,
    )
    require(coef is not None, "the scenario must produce a valid fit")
    plane = Z_mm - residual
    low_y_rows = (y_mm >= 0.0) & (y_mm <= 0.5)
    bead_rows = (y_mm >= 0.7) & (y_mm <= 1.3)
    interior_idx = int(np.argmin(np.abs(x_mm - 60.0)))
    far_edge_idx = int(np.argmin(np.abs(x_mm - 99.0)))

    def shape_gap(idx):
        return (
            float(np.nanmedian(plane[low_y_rows, idx]))
            - float(np.nanmedian(plane[bead_rows, idx]))
        )

    return abs(shape_gap(far_edge_idx) - shape_gap(interior_idx))


def test_xy_interaction_cap_is_track_independent():
    edge_tolerance_mm = 0.012
    big_scale = 1.0
    small_scale = big_scale / 40.0

    for label, scale in (("big", big_scale), ("small", small_scale)):
        Z_mm, x_mm, y_mm, fit_mask = _xy_interaction_cap_scenario(scale)
        departure = _xy_interaction_shape_gap_departure(
            Z_mm, x_mm, y_mm, fit_mask, max_xy_degree=targets.DETREND_MAX_XY_DEGREE
        )
        require(
            departure <= edge_tolerance_mm,
            f"{label}: the shared DETREND_MAX_XY_DEGREE constant must clear the far-edge "
            "shape-gap tolerance",
        )

    # The fix is only load-bearing at the large (track-10-like) magnitude:
    # confirm the uncapped fit still manufactures an edge-of-domain artifact
    # there, proving the fix (not the scenario) is what clears the tolerance.
    Z_big, x_mm, y_mm, fit_mask_big = _xy_interaction_cap_scenario(big_scale)
    uncapped_departure = _xy_interaction_shape_gap_departure(
        Z_big, x_mm, y_mm, fit_mask_big, max_xy_degree=None
    )
    require(
        uncapped_departure > edge_tolerance_mm,
        "the uncapped-in-x fit must still manufacture a shape-gap departure at the large "
        "magnitude, confirming the fix (not the scenario) is what clears the tolerance there",
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
        "MAX_TRACKING_GAP_COLUMNS": 10,
        "BEAD_MASK_HEIGHT_FRACTION": 0.5,
        "DETREND_MAX_Y_DEGREE": 2,
        "DETREND_MAX_XY_DEGREE": 2,
        "MAX_RUN_MERGE_GAP_PIXELS": 10,
        "MIN_TRACKED_LENGTH_RATIO": 0.5,
    }

    require(targets.extraction_params() == expected, "the exact 19-value extraction parameterization changed")


def test_provenance_includes_tracking_gap_and_fix_param():
    params = targets.extraction_params()

    require("MAX_TRACKING_GAP_COLUMNS" in params, "provenance must include the tracking-gap timeout")
    require(
        params["MAX_TRACKING_GAP_COLUMNS"] == targets.MAX_TRACKING_GAP_COLUMNS,
        "tracking-gap provenance value must match the module constant",
    )
    require("BEAD_MASK_HEIGHT_FRACTION" in params, "provenance must include the Gap-2 bead-mask fix parameter")
    require(
        params["BEAD_MASK_HEIGHT_FRACTION"] == targets.BEAD_MASK_HEIGHT_FRACTION,
        "bead-mask fraction provenance value must match the module constant",
    )


def test_provenance_digest_is_change_sensitive():
    import hashlib
    import json

    def digest():
        return hashlib.sha256(
            json.dumps(targets.extraction_params(), sort_keys=True).encode("utf-8")
        ).hexdigest()

    baseline = digest()

    original_gap = targets.MAX_TRACKING_GAP_COLUMNS
    try:
        targets.MAX_TRACKING_GAP_COLUMNS = 999
        require(digest() != baseline, "mutating MAX_TRACKING_GAP_COLUMNS must change the provenance digest")
    finally:
        targets.MAX_TRACKING_GAP_COLUMNS = original_gap
    require(digest() == baseline, "restoring MAX_TRACKING_GAP_COLUMNS must restore the baseline digest")

    original_fraction = targets.BEAD_MASK_HEIGHT_FRACTION
    try:
        targets.BEAD_MASK_HEIGHT_FRACTION = 0.999
        require(digest() != baseline, "mutating BEAD_MASK_HEIGHT_FRACTION must change the provenance digest")
    finally:
        targets.BEAD_MASK_HEIGHT_FRACTION = original_fraction
    require(digest() == baseline, "restoring BEAD_MASK_HEIGHT_FRACTION must restore the baseline digest")

    original_max_y_degree = targets.DETREND_MAX_Y_DEGREE
    try:
        targets.DETREND_MAX_Y_DEGREE = 999
        require(digest() != baseline, "mutating DETREND_MAX_Y_DEGREE must change the provenance digest")
    finally:
        targets.DETREND_MAX_Y_DEGREE = original_max_y_degree
    require(digest() == baseline, "restoring DETREND_MAX_Y_DEGREE must restore the baseline digest")

    original_max_xy_degree = targets.DETREND_MAX_XY_DEGREE
    try:
        targets.DETREND_MAX_XY_DEGREE = 999
        require(digest() != baseline, "mutating DETREND_MAX_XY_DEGREE must change the provenance digest")
    finally:
        targets.DETREND_MAX_XY_DEGREE = original_max_xy_degree
    require(digest() == baseline, "restoring DETREND_MAX_XY_DEGREE must restore the baseline digest")

    original_merge_gap = targets.MAX_RUN_MERGE_GAP_PIXELS
    try:
        targets.MAX_RUN_MERGE_GAP_PIXELS = 999
        require(digest() != baseline, "mutating MAX_RUN_MERGE_GAP_PIXELS must change the provenance digest")
    finally:
        targets.MAX_RUN_MERGE_GAP_PIXELS = original_merge_gap
    require(digest() == baseline, "restoring MAX_RUN_MERGE_GAP_PIXELS must restore the baseline digest")

    original_ratio = targets.MIN_TRACKED_LENGTH_RATIO
    try:
        targets.MIN_TRACKED_LENGTH_RATIO = 0.999
        require(digest() != baseline, "mutating MIN_TRACKED_LENGTH_RATIO must change the provenance digest")
    finally:
        targets.MIN_TRACKED_LENGTH_RATIO = original_ratio
    require(digest() == baseline, "restoring MIN_TRACKED_LENGTH_RATIO must restore the baseline digest")


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
        test_merge_adjacent_runs_bridges_short_below_threshold_gaps,
        test_merge_adjacent_runs_does_not_bridge_large_gaps,
        test_halfmax_edges_rejects_implausibly_narrow_tracked_candidate,
        test_halfmax_edges_recovers_leading_edge_swallowed_interior_run,
        test_halfmax_edges_recovers_trailing_edge_swallowed_interior_run,
        test_halfmax_edges_rejects_lone_candidate_far_and_small_versus_tracked_history,
        test_halfmax_edges_accepts_lone_candidate_small_but_close_to_tracked_history,
        test_halfmax_edges_accepts_lone_candidate_far_but_large_versus_tracked_history,
        test_extract_targets_from_arrays_recovers_from_track8_style_propagating_wrong_lock,
        test_extract_targets_from_arrays_merges_track10_style_fragmented_bead,
        test_extract_targets_from_arrays_rejects_track8_style_single_candidate_trigger_column,
        test_bead_mask_rule_is_track_independent,
        test_extract_targets_from_arrays_boundary_tracking_survives_decoy_blob,
        test_halfmax_edges_resets_stale_history_after_long_invalid_gap,
        test_nan_savgol_preserves_mask,
        test_nan_savgol_preserves_quadratic_at_crop_edges,
        test_nan_savgol_blends_across_masked_gaps,
        test_nan_savgol_no_longer_exact_interpolates_three_point_window,
        test_nan_savgol_track10_crop_edge_regression,
        test_single_parameterization_has_no_track_conditionals,
        test_track_id_does_not_affect_numeric_output,
        test_edge_divergence_fix_is_track_independent,
        test_xy_interaction_cap_is_track_independent,
        test_extraction_params_provenance,
        test_provenance_includes_tracking_gap_and_fix_param,
        test_provenance_digest_is_change_sensitive,
        test_post_smoothing_crossing_is_invalidated,
        test_post_smoothing_zero_valid_raises_value_error,
        test_all_invalid_track_raises_value_error,
        test_synthetic_end_to_end_fixed_grid_and_width,
    ]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
