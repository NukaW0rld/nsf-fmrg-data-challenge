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


def halfmax_edges(prof, y_mm, previous_center=None):
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
    # A run clipped by the measured strip has an unknowable true edge and is
    # never a tracking candidate, even when it is closest to prior history.
    candidates = [
        (start, stop)
        for start, stop in all_true_runs(above)
        if start != 0 and stop != len(prof)
    ]
    if not candidates:
        return None
    if previous_center is None:
        start, stop = min(candidates, key=lambda run: (-(run[1] - run[0]), run[0]))
    else:
        start, stop = min(
            candidates,
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
        degree = min(SG_POLYORDER, finite.sum() - 1)
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


def extract_targets_from_arrays(Zd, x_actual_mm, y_mm):
    x_grid = target_grid()
    y_upper_raw = np.full(TARGET_GRID_N, np.nan, dtype=np.float64)
    y_lower_raw = np.full(TARGET_GRID_N, np.nan, dtype=np.float64)
    previous_center = None
    invalid_run_columns = 0

    for i, x_center in enumerate(x_grid):
        if invalid_run_columns >= MAX_TRACKING_GAP_COLUMNS:
            previous_center = None
        prof = bin_profile(Zd, x_actual_mm, x_center)
        if prof is None:
            invalid_run_columns += 1
            continue
        prof, ok = fill_small_gaps(prof)
        if not ok:
            invalid_run_columns += 1
            continue
        edges = halfmax_edges(prof, y_mm, previous_center=previous_center)
        if edges is None:
            invalid_run_columns += 1
            continue
        y_lower_raw[i], y_upper_raw[i] = edges
        previous_center = 0.5 * (edges[0] + edges[1])
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

    Zd, coef = robust_plane_detrend(
        data['Z_mm'],
        data['x_actual_mm'],
        data['y_mm'],
        order=DETREND_POLY_ORDER,
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
