from pathlib import Path

import numpy as np

from nsf_fmrg_data import load_wyko_asc, robust_plane_detrend

TARGET_GRID_START_MM = 20.1
TARGET_GRID_STEP_MM = 0.2
TARGET_GRID_N = 400
BASELINE_PCT = 5.0
PEAK_PCT = 95.0
HALF_MAX_FRACTION = 0.5
MIN_PEAK_BASELINE_SEPARATION_MM = 0.005
MAX_GAP_PIXELS = 10
# Discard a boundary anchor after this many consecutive untracked columns.
MAX_TRACKING_GAP_COLUMNS = 10
SG_WINDOW_PTS = 5
SG_POLYORDER = 2
MIN_VALID_Y_POINTS = 50
MIN_COLUMNS_PER_BIN = 10
# Amendment A3: fixed a priori from the debug session's per-track R^2 evidence.
DETREND_POLY_ORDER = 4
# Amendment A4 (Gap 2 fix): baseline-relative fraction of each column's
# peak-baseline separation above which a pixel is excluded from the detrend
# surface fit. Fixed at the already-locked HALF_MAX_FRACTION value (D-01/D-03):
# a pixel this codebase already classifies as "bead" by the half-max width
# convention is, by that same definition, not background, so it must not be
# allowed to bias the fitted surface. Not chosen from the resulting ordering.
BEAD_MASK_HEIGHT_FRACTION = HALF_MAX_FRACTION
# Amendment A5: fixed a priori after 01-11-CRITERION.md's committed criterion
# established (by measurement, not by the resulting ordering) that Candidate
# A (basis conditioning) cannot change the least-squares fit at all -- column
# rescaling does not change a full-rank linear regression's fitted surface --
# and its own fallback provision selected Candidate B instead. 2 is the
# LARGEST cross-track degree cap that clears the criterion's 0.05 mm
# fitted-surface edge-vs-midpoint tolerance on all four tracks (01-11-
# DIAGNOSIS.md measurements): cap 3 leaves one track's edge departure at
# 0.0665 mm, still above tolerance, while cap 2 brings every track's largest
# edge departure to 0.0238 mm, comfortably under. Preserves the maximum
# cross-track fitting capacity that still satisfies the criterion.
DETREND_MAX_Y_DEGREE = 2
# Amendment A6: fixed a priori after 01-13-CRITERION.md's committed criterion
# established (by measurement, not by the resulting ordering) the x-direction
# shape-gap tolerance (fitted surface's own low-y-band-vs-bead-band value at
# the domain's far edge x~99mm, compared to its own interior-midpoint value
# at x~60mm, must not depart by more than SHAPE_GAP_EDGE_TOLERANCE_MM=0.012mm
# on all four tracks). Basis conditioning was already ruled out as a viable
# mechanism by 01-11-CRITERION.md (column rescaling cannot change a full-rank
# least-squares fit's fitted values), leaving cross-term x-exponent capping
# as the sole candidate. 2 is the LARGEST cap that clears the criterion on
# all four tracks (measured on processed_data/diagnostics/track10_tail_
# collapse_diagnosis.csv): cap 3 (a no-op vs uncapped, since max_y_degree=2
# already limits the highest surviving cross-term x-exponent to 3) leaves
# track 10's departure at 0.0212mm, still above tolerance, while cap 2
# brings it to 0.0118mm, comfortably under -- preserving the maximum
# cross-track fitting capacity that still satisfies the criterion.
DETREND_MAX_XY_DEGREE = 2
# Amendment A7: reuses the already-locked D-05/D-06 judgment that a short
# (<=10 native-pixel) below-criterion stretch should not be treated as a
# genuine break/separation, now applied to post-threshold run fragmentation
# (merge_adjacent_runs) instead of raw NaN gaps. Not chosen from the
# resulting fragmentation count or width ordering.
MAX_RUN_MERGE_GAP_PIXELS = MAX_GAP_PIXELS
# Amendment A7: reuses the already-locked D-01/D-03 half-max convention's own
# fraction -- a tracked candidate whose length falls below half of the
# largest same-column alternative is not a plausible competing feature under
# that same convention. Not chosen from the resulting fragmentation count or
# width ordering.
MIN_TRACKED_LENGTH_RATIO = HALF_MAX_FRACTION

TRACK_POWER_W = {8: 400, 10: 350, 14: 300, 21: 200}
TRACK_IDS = tuple(TRACK_POWER_W)


def target_grid():
    return TARGET_GRID_START_MM + TARGET_GRID_STEP_MM * np.arange(TARGET_GRID_N)


def extraction_params():
    return {
        'TARGET_GRID_START_MM': TARGET_GRID_START_MM,
        'TARGET_GRID_STEP_MM': TARGET_GRID_STEP_MM,
        'TARGET_GRID_N': TARGET_GRID_N,
        'BASELINE_PCT': BASELINE_PCT,
        'PEAK_PCT': PEAK_PCT,
        'HALF_MAX_FRACTION': HALF_MAX_FRACTION,
        'MIN_PEAK_BASELINE_SEPARATION_MM': MIN_PEAK_BASELINE_SEPARATION_MM,
        'MAX_GAP_PIXELS': MAX_GAP_PIXELS,
        'SG_WINDOW_PTS': SG_WINDOW_PTS,
        'SG_POLYORDER': SG_POLYORDER,
        'MIN_VALID_Y_POINTS': MIN_VALID_Y_POINTS,
        'MIN_COLUMNS_PER_BIN': MIN_COLUMNS_PER_BIN,
        'DETREND_POLY_ORDER': DETREND_POLY_ORDER,
        'MAX_TRACKING_GAP_COLUMNS': MAX_TRACKING_GAP_COLUMNS,
        'BEAD_MASK_HEIGHT_FRACTION': BEAD_MASK_HEIGHT_FRACTION,
        'DETREND_MAX_Y_DEGREE': DETREND_MAX_Y_DEGREE,
        'DETREND_MAX_XY_DEGREE': DETREND_MAX_XY_DEGREE,
        'MAX_RUN_MERGE_GAP_PIXELS': MAX_RUN_MERGE_GAP_PIXELS,
        'MIN_TRACKED_LENGTH_RATIO': MIN_TRACKED_LENGTH_RATIO,
    }


def print_results(summaries, track_ids=TRACK_IDS):
    print("\ntrack  power_W  valid_bins  median_mm  mean_mm")
    for summary in summaries:
        print(
            f'{summary["track_id"]:>5}  {summary["laser_power_w"]:>7}  '
            f'{summary["valid_count"]:>10}  {summary["median_width_mm"]:>9.4f}  '
            f'{summary["mean_width_mm"]:>7.4f}'
        )

    by_track = {summary["track_id"]: summary for summary in summaries}
    for higher_track, lower_track in zip(track_ids, track_ids[1:]):
        higher = by_track[higher_track]["median_width_mm"]
        lower = by_track[lower_track]["median_width_mm"]
        outcome = "PASS" if higher > lower else "FLAG"
        print(
            f"Ordering {higher_track} vs {lower_track}: "
            f"{higher:.4f} mm > {lower:.4f} mm — {outcome}"
        )
    print("Ordering FLAG outcomes are documented and never used to tune locked extraction constants.")


def bin_profile(Zd, x_actual_mm, x_center):
    half_step = TARGET_GRID_STEP_MM / 2.0
    columns = (x_actual_mm >= x_center - half_step) & (x_actual_mm < x_center + half_step)
    if columns.sum() < MIN_COLUMNS_PER_BIN:
        return None
    # Bin first because native-column gap checks invalidate nearly every raw column.
    return np.nanmedian(Zd[:, columns], axis=1)


def fill_small_gaps(prof):
    filled = np.asarray(prof, dtype=np.float64).copy()
    idx = np.flatnonzero(np.isnan(filled))
    if not len(idx):
        return filled, True

    breaks = np.where(np.diff(idx) > 1)[0]
    starts = np.r_[idx[0], idx[breaks + 1]]
    stops = np.r_[idx[breaks] + 1, idx[-1] + 1]
    if np.any(stops - starts > MAX_GAP_PIXELS):
        return filled, False

    for start, stop in zip(starts, stops):
        if start == 0 or stop == len(filled):
            continue
        positions = np.arange(start, stop)
        filled[start:stop] = np.interp(
            positions,
            [start - 1, stop],
            [filled[start - 1], filled[stop]],
        )
    return filled, True


def all_true_runs(mask):
    mask = np.asarray(mask, dtype=bool)
    if not mask.any():
        return []
    idx = np.flatnonzero(mask)
    breaks = np.where(np.diff(idx) > 1)[0]
    starts = np.r_[idx[0], idx[breaks + 1]]
    stops = np.r_[idx[breaks] + 1, idx[-1] + 1]
    return [(int(start), int(stop)) for start, stop in zip(starts, stops)]


def merge_adjacent_runs(runs, max_gap):
    # Combines adjacent above-threshold sub-runs separated by only a few
    # below-threshold samples into one candidate before clip-exclusion and
    # selection, so a noise-fragmented true bead is not split into several
    # competing tiny candidates. `runs` must already be sorted and
    # non-overlapping (as all_true_runs produces); does not mutate the input.
    if not runs:
        return []
    merged = [runs[0]]
    for start, stop in runs[1:]:
        last_start, last_stop = merged[-1]
        if start - last_stop <= max_gap:
            merged[-1] = (last_start, stop)
        else:
            merged.append((start, stop))
    return merged


def halfmax_edges(prof, y_mm, previous_center=None, previous_length_mm=None):
    prof = np.asarray(prof, dtype=np.float64)
    y_mm = np.asarray(y_mm, dtype=np.float64)
    finite = np.isfinite(prof)
    if finite.sum() < MIN_VALID_Y_POINTS:
        return None

    vals = prof[finite]
    base = np.percentile(vals, BASELINE_PCT)
    peak = np.percentile(vals, PEAK_PCT)
    if peak - base < MIN_PEAK_BASELINE_SEPARATION_MM:
        return None

    threshold = base + HALF_MAX_FRACTION * (peak - base)
    above = np.where(finite, prof > threshold, False)
    # Amendment A8 (Mechanism A fix): apply the D-01/D-03 clip-exclusion test
    # to each RAW run BEFORE merging, not after. This guarantees a merged
    # candidate can never touch a y-strip boundary -- its start/stop are
    # always drawn from already-interior surviving runs -- so no separate
    # post-merge clip filter is needed. Under the old merge-then-clip
    # ordering, a raw edge-touching run within MAX_RUN_MERGE_GAP_PIXELS of an
    # otherwise-valid interior run would fuse with it and the whole fused
    # span (including the legitimate interior run) was discarded as
    # edge-touching -- silently swallowing a legitimate candidate (see
    # .planning/debug/boundary-fragmentation-crop-edge-post-A7-visual-signoff.md,
    # Mechanism A).
    raw_runs = all_true_runs(above)
    non_edge_runs = [
        run for run in raw_runs
        if run[0] != 0 and run[1] != len(prof)
    ]
    candidates = merge_adjacent_runs(non_edge_runs, MAX_RUN_MERGE_GAP_PIXELS)
    if not candidates:
        return None
    if previous_center is None:
        start, stop = min(candidates, key=lambda run: (-(run[1] - run[0]), run[0]))
    else:
        # An implausibly-small candidate can never win purely on midpoint
        # proximity: only candidates at least MIN_TRACKED_LENGTH_RATIO of the
        # largest same-column candidate's length are eligible for selection.
        # This set is never empty -- the run achieving max_len always
        # satisfies the inequality.
        max_len = max(stop - start for start, stop in candidates)
        plausible = [
            run for run in candidates
            if (run[1] - run[0]) >= MIN_TRACKED_LENGTH_RATIO * max_len
        ]
        # Amendment A8 (Mechanism B fix): the same-column-relative filter
        # above is structurally moot when a column has exactly one
        # candidate -- it trivially satisfies its own ratio. Add a
        # history-based joint far-AND-small gate: a lone candidate is only
        # rejected when it is BOTH farther from previous_center than the
        # recently-tracked run's own physical width (previous_length_mm)
        # AND smaller than MIN_TRACKED_LENGTH_RATIO of that same width. This
        # introduces NO new named constant -- it reuses MIN_TRACKED_LENGTH_RATIO
        # for the "small" test and derives the "far" distance scale from the
        # just-computed previous_length_mm itself (a runtime-derived
        # quantity, not a new tunable number). A candidate close to
        # previous_center is never rejected on size alone (plausible
        # narrowing), and a candidate as large as recent history is never
        # rejected on distance alone (plausible drift/relocation).
        if previous_length_mm is not None:
            def _is_implausible_versus_history(run):
                start, stop = run
                length_mm = y_mm[stop - 1] - y_mm[start]
                is_small = length_mm < MIN_TRACKED_LENGTH_RATIO * previous_length_mm
                mid_y = y_mm[(start + stop - 1) // 2]
                is_far = abs(mid_y - previous_center) > previous_length_mm
                return is_small and is_far

            history_plausible = [
                run for run in plausible if not _is_implausible_versus_history(run)
            ]
            if not history_plausible:
                return None
            plausible = history_plausible
        start, stop = min(
            plausible,
            key=lambda run: (
                abs(y_mm[(run[0] + run[1] - 1) // 2] - previous_center),
                -(run[1] - run[0]),
                run[0],
            ),
        )

    if np.isfinite(prof[start - 1]):
        y0 = y_mm[start - 1]
        y1 = y_mm[start]
        z0 = prof[start - 1]
        z1 = prof[start]
        y_lower = y0 + (threshold - z0) * (y1 - y0) / (z1 - z0)
    else:
        y_lower = y_mm[start]

    if np.isfinite(prof[stop]):
        y0 = y_mm[stop - 1]
        y1 = y_mm[stop]
        z0 = prof[stop - 1]
        z1 = prof[stop]
        y_upper = y0 + (threshold - z0) * (y1 - y0) / (z1 - z0)
    else:
        y_upper = y_mm[stop - 1]

    if y_upper <= y_lower:
        return None
    return y_lower, y_upper


def nan_savgol(v):
    v = np.asarray(v, dtype=np.float64)
    out = np.full(len(v), np.nan, dtype=np.float64)
    half = SG_WINDOW_PTS // 2
    for i in range(len(v)):
        if not np.isfinite(v[i]):
            continue
        lo = max(0, i - half)
        hi = min(len(v), i + half + 1)
        window = v[lo:hi]
        offsets = np.arange(lo, hi) - i
        finite = np.isfinite(window)
        if finite.sum() < 3:
            out[i] = v[i]
            continue
        degree = min(SG_POLYORDER, finite.sum() - 2)
        coef = np.polyfit(offsets[finite], window[finite], degree)
        out[i] = np.polyval(coef, 0.0)
    return out


def finalize_smoothed_boundaries(y_lower_raw, y_upper_raw):
    y_lower = nan_savgol(y_lower_raw)
    y_upper = nan_savgol(y_upper_raw)
    valid_mask = np.isfinite(y_lower) & np.isfinite(y_upper) & (y_upper > y_lower)

    y_lower = y_lower.copy()
    y_upper = y_upper.copy()
    y_lower[~valid_mask] = np.nan
    y_upper[~valid_mask] = np.nan
    w_mm = y_upper - y_lower

    if valid_mask.sum() == 0:
        raise ValueError('Target extraction produced zero valid x-positions.')
    return y_lower, y_upper, w_mm, valid_mask


def bead_exclusion_mask(Z_mm):
    # One shared, per-column-relative rule (mirrors D-01/D-02's
    # BASELINE_PCT/PEAK_PCT convention): a pixel is excluded from the detrend
    # surface fit only if it sits above baseline + BEAD_MASK_HEIGHT_FRACTION *
    # (peak - baseline) for its own column, so tracks with very different
    # absolute bead heights are masked by the same fraction, not the same
    # absolute threshold. Columns without a valid baseline/peak separation are
    # left fully included (the detrend fit degrades no worse than unmasked).
    Z_mm = np.asarray(Z_mm, dtype=np.float64)
    mask = np.ones(Z_mm.shape, dtype=bool)
    for j in range(Z_mm.shape[1]):
        column = Z_mm[:, j]
        finite = np.isfinite(column)
        if finite.sum() < MIN_VALID_Y_POINTS:
            continue
        vals = column[finite]
        base = np.percentile(vals, BASELINE_PCT)
        peak = np.percentile(vals, PEAK_PCT)
        if peak - base < MIN_PEAK_BASELINE_SEPARATION_MM:
            continue
        threshold = base + BEAD_MASK_HEIGHT_FRACTION * (peak - base)
        above = finite & (column > threshold)
        mask[above, j] = False
    return mask


def extract_targets_from_arrays(Zd, x_actual_mm, y_mm):
    x_grid = target_grid()
    y_upper_raw = np.full(TARGET_GRID_N, np.nan, dtype=np.float64)
    y_lower_raw = np.full(TARGET_GRID_N, np.nan, dtype=np.float64)
    previous_center = None
    previous_length_mm = None
    invalid_run_columns = 0

    for i, x_center in enumerate(x_grid):
        if invalid_run_columns >= MAX_TRACKING_GAP_COLUMNS:
            previous_center = None
            previous_length_mm = None
        prof = bin_profile(Zd, x_actual_mm, x_center)
        if prof is None:
            invalid_run_columns += 1
            continue
        prof, ok = fill_small_gaps(prof)
        if not ok:
            invalid_run_columns += 1
            continue
        edges = halfmax_edges(
            prof, y_mm,
            previous_center=previous_center,
            previous_length_mm=previous_length_mm,
        )
        if edges is None:
            invalid_run_columns += 1
            continue
        y_lower_raw[i], y_upper_raw[i] = edges
        previous_center = 0.5 * (edges[0] + edges[1])
        previous_length_mm = edges[1] - edges[0]
        invalid_run_columns = 0

    y_lower, y_upper, w_mm, valid_mask = finalize_smoothed_boundaries(
        y_lower_raw,
        y_upper_raw,
    )

    return {
        'x_grid_mm': x_grid,
        'w_mm': w_mm,
        'y_upper_mm': y_upper,
        'y_lower_mm': y_lower,
        'valid_mask': valid_mask,
    }


def extract_track_targets(height_dir, track_id):
    data = load_wyko_asc(height_dir, track_id)
    expected_name = f'Heightmap_{track_id}.ASC'
    if Path(data['file']).name != expected_name:
        raise ValueError(f'Expected {expected_name}, resolved {Path(data["file"]).name}.')
    if 'pixel_size_mm' not in data['header']:
        raise ValueError(f'{expected_name} header is missing pixel_size_mm.')

    fit_mask = bead_exclusion_mask(data['Z_mm'])
    Zd, coef = robust_plane_detrend(
        data['Z_mm'],
        data['x_actual_mm'],
        data['y_mm'],
        order=DETREND_POLY_ORDER,
        fit_mask=fit_mask,
        max_y_degree=DETREND_MAX_Y_DEGREE,
        max_xy_degree=DETREND_MAX_XY_DEGREE,
    )
    if coef is None:
        raise ValueError(f'Plane detrending failed for {expected_name}.')

    result = extract_targets_from_arrays(Zd, data['x_actual_mm'], data['y_mm'])
    result.update({
        'track_id': track_id,
        'file': data['file'],
        'Z_mm': data['Z_mm'],
        'Zd_mm': Zd,
        'x_actual_mm': data['x_actual_mm'],
        'y_mm': data['y_mm'],
    })
    return result
