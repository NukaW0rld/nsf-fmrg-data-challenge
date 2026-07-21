from pathlib import Path
import argparse
import csv
import sys

import numpy as np

# Allow running from repo root without installing as a package.
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from targets import (
    BASELINE_PCT,
    DETREND_POLY_ORDER,
    HALF_MAX_FRACTION,
    MAX_TRACKING_GAP_COLUMNS,
    MIN_PEAK_BASELINE_SEPARATION_MM,
    MIN_VALID_Y_POINTS,
    PEAK_PCT,
    TRACK_IDS,
    all_true_runs,
    bead_exclusion_mask,
    bin_profile,
    fill_small_gaps,
    target_grid,
)
from nsf_fmrg_data import load_wyko_asc, robust_plane_detrend
from run_target_extraction import (
    raw_snapshot_diff,
    resolve_output_path,
    resolve_raw_dir,
    resolve_repository_root,
    snapshot_raw,
)

EDGE_FRACTION = 0.05


def raw_row_median_profile(Z_mm):
    profile = np.nanmedian(Z_mm, axis=1)
    n = len(profile)
    argmax_idx = int(np.nanargmax(profile))
    edge_band = max(1, int(round(EDGE_FRACTION * n)))
    near_edge = argmax_idx < edge_band or argmax_idx >= n - edge_band
    return {
        'raw_min_mm': float(np.nanmin(profile)),
        'raw_max_mm': float(np.nanmax(profile)),
        'raw_span_mm': float(np.nanmax(profile) - np.nanmin(profile)),
        'raw_argmax_y_index': argmax_idx,
        'raw_argmax_near_edge': bool(near_edge),
        'raw_finite_fraction': float(np.isfinite(Z_mm).mean()),
    }


def production_residual_profile(Z_mm, x_actual_mm, y_mm):
    fit_mask = bead_exclusion_mask(Z_mm)
    Zd, coef = robust_plane_detrend(
        Z_mm, x_actual_mm, y_mm, order=DETREND_POLY_ORDER, fit_mask=fit_mask,
    )
    profile = np.nanmedian(Zd, axis=1)
    n = len(profile)
    peak_idx = int(np.nanargmax(profile))
    finite = np.isfinite(profile)
    vals = profile[finite]
    base = np.percentile(vals, BASELINE_PCT)
    peak = np.percentile(vals, PEAK_PCT)
    threshold = base + HALF_MAX_FRACTION * (peak - base)
    above = np.where(finite, profile > threshold, False)
    runs = all_true_runs(above)
    containing = [run for run in runs if run[0] <= peak_idx < run[1]]
    if containing:
        start, stop = containing[0]
    else:
        start, stop = peak_idx, peak_idx + 1
    return Zd, {
        'residual_peak_mm': float(profile[peak_idx]),
        'residual_peak_y_index': peak_idx,
        'residual_run_extent_points': int(stop - start),
        'residual_run_touches_y0': bool(start == 0),
        'residual_run_touches_yN': bool(stop == n),
    }


def fitted_surface_edge_report(Z_mm, Zd):
    fitted = Z_mm - Zd
    profile = np.nanmedian(fitted, axis=1)
    n = len(profile)
    mid = n // 2
    return {
        'fitted_surface_y0_mm': float(profile[0]),
        'fitted_surface_ymid_mm': float(profile[mid]),
        'fitted_surface_yN_mm': float(profile[-1]),
        'fitted_surface_span_mm': float(np.nanmax(profile) - np.nanmin(profile)),
    }


def classify_column(prof, y_mm, previous_center):
    # Mirrors targets.halfmax_edges' rejection branches so this diagnostic can
    # attribute a reason to each bin; must be kept in step with that function.
    prof = np.asarray(prof, dtype=np.float64)
    y_mm = np.asarray(y_mm, dtype=np.float64)
    finite = np.isfinite(prof)
    if finite.sum() < MIN_VALID_Y_POINTS:
        return 'no_baseline_sep', None

    vals = prof[finite]
    base = np.percentile(vals, BASELINE_PCT)
    peak = np.percentile(vals, PEAK_PCT)
    if peak - base < MIN_PEAK_BASELINE_SEPARATION_MM:
        return 'no_baseline_sep', None

    threshold = base + HALF_MAX_FRACTION * (peak - base)
    above = np.where(finite, prof > threshold, False)
    candidates = [
        (start, stop)
        for start, stop in all_true_runs(above)
        if start != 0 and stop != len(prof)
    ]
    if not candidates:
        return 'clipped_run_only', None
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
        return 'crossed', None
    return 'ok', (y_lower, y_upper)


def rejection_reason_histogram(Zd, x_actual_mm, y_mm):
    x_grid = target_grid()
    histogram = {
        'no_columns': 0, 'gap_fail': 0, 'no_baseline_sep': 0,
        'clipped_run_only': 0, 'crossed': 0, 'ok': 0,
    }
    previous_center = None
    invalid_run_columns = 0

    for x_center in x_grid:
        if invalid_run_columns >= MAX_TRACKING_GAP_COLUMNS:
            previous_center = None
        prof = bin_profile(Zd, x_actual_mm, x_center)
        if prof is None:
            histogram['no_columns'] += 1
            invalid_run_columns += 1
            continue
        prof, ok = fill_small_gaps(prof)
        if not ok:
            histogram['gap_fail'] += 1
            invalid_run_columns += 1
            continue
        reason, edges = classify_column(prof, y_mm, previous_center)
        histogram[reason] += 1
        if reason != 'ok':
            invalid_run_columns += 1
            continue
        previous_center = 0.5 * (edges[0] + edges[1])
        invalid_run_columns = 0

    return histogram


def design_matrix_condition(x_actual_mm, y_mm, order, stride_x=40, stride_y=2):
    xs = x_actual_mm[::stride_x]
    ys = y_mm[::stride_y]
    Xs, Ys = np.meshgrid(xs, ys)
    exponents = [
        (i, degree - i)
        for degree in range(order + 1)
        for i in range(degree + 1)
    ]
    x_center = 0.5 * (x_actual_mm[0] + x_actual_mm[-1])
    y_center = 0.5 * (y_mm[0] + y_mm[-1])
    Xs_centered = Xs - x_center
    Ys_centered = Ys - y_center

    def build(x_scaled, y_scaled):
        return np.column_stack([
            x_scaled.ravel() ** i * y_scaled.ravel() ** j
            for i, j in exponents
        ])

    A_raw = build(Xs_centered, Ys_centered)
    norms_raw = np.linalg.norm(A_raw, axis=0)
    norms_raw_nonzero = norms_raw[norms_raw > 0]

    x_half_span = 0.5 * (x_actual_mm[-1] - x_actual_mm[0])
    y_half_span = 0.5 * (y_mm[-1] - y_mm[0])
    A_scaled = build(Xs_centered / x_half_span, Ys_centered / y_half_span)
    norms_scaled = np.linalg.norm(A_scaled, axis=0)
    norms_scaled_nonzero = norms_scaled[norms_scaled > 0]

    return {
        'design_cond_unscaled': float(np.linalg.cond(A_raw)),
        'design_norm_ratio_unscaled': float(norms_raw_nonzero.max() / norms_raw_nonzero.min()),
        'design_cond_scaled': float(np.linalg.cond(A_scaled)),
        'design_norm_ratio_scaled': float(norms_scaled_nonzero.max() / norms_scaled_nonzero.min()),
    }


def measure_track(height_dir, track_id):
    data = load_wyko_asc(height_dir, track_id)
    Z_mm = data['Z_mm']
    x_actual_mm = data['x_actual_mm']
    y_mm = data['y_mm']

    row = {'track_id': track_id}
    row.update(raw_row_median_profile(Z_mm))
    Zd, residual_measures = production_residual_profile(Z_mm, x_actual_mm, y_mm)
    row.update(residual_measures)
    row.update(fitted_surface_edge_report(Z_mm, Zd))
    histogram = rejection_reason_histogram(Zd, x_actual_mm, y_mm)
    for reason, count in histogram.items():
        row[f'rejection_{reason}'] = count
    row.update(design_matrix_condition(x_actual_mm, y_mm, DETREND_POLY_ORDER))
    return row


def print_measurement_table(rows):
    fieldnames = list(rows[0].keys())
    print('\n' + ','.join(fieldnames))
    for row in rows:
        print(','.join(str(row[name]) for name in fieldnames))


def write_csv(csv_path, rows):
    fieldnames = list(rows[0].keys())
    with csv_path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def run_coverage_diagnostic(project_dir: Path) -> Path:
    project_root = resolve_repository_root(project_dir)
    raw_dir = resolve_raw_dir(project_root)
    raw_before = snapshot_raw(raw_dir)

    height_dir = raw_dir / "height_maps"
    rows = [measure_track(height_dir, track_id) for track_id in TRACK_IDS]
    print_measurement_table(rows)

    # processed_data/diagnostics/ is a SIBLING of processed_data/targets/, not a
    # child of it: run_target_extraction.publish_staging_dir renames the whole
    # targets/ tree aside and rmtree's the backup on every extraction run, so a
    # CSV written under targets/ would be silently destroyed by that publish.
    diagnostics_dir = resolve_output_path(
        project_root / "processed_data" / "diagnostics",
        project_root,
        raw_dir,
    )
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    diagnostics_dir = resolve_output_path(diagnostics_dir, project_root, raw_dir)

    csv_path = resolve_output_path(
        diagnostics_dir / "track10_coverage_diagnosis.csv",
        project_root,
        raw_dir,
    )
    write_csv(csv_path, rows)

    raw_after = snapshot_raw(raw_dir)
    difference = raw_snapshot_diff(raw_before, raw_after)
    if any(difference.values()):
        raise RuntimeError(f"data/raw integrity FAIL: {difference}")
    print("data/raw/ integrity PASS: no files created, modified, or deleted.")
    print(f"Wrote coverage diagnosis: {csv_path}")
    return csv_path


def main():
    parser = argparse.ArgumentParser(
        description="Characterize track 10's coverage collapse under the production extraction path.",
    )
    parser.add_argument("--project_dir", type=Path, default=Path("."), help="Repository/project root.")
    args = parser.parse_args()
    run_coverage_diagnostic(args.project_dir)


if __name__ == "__main__":
    main()
