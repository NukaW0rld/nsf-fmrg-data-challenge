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
    MAX_TRACKING_GAP_COLUMNS,
    TRACK_IDS,
    TRACK_POWER_W,
    bin_profile,
    fill_small_gaps,
    finalize_smoothed_boundaries,
    halfmax_edges,
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

DETREND_ORDERS = (1, 2, 4)
CONTINUITY_OPTIONS = (True, False)


def extract_swept(Zd, x_actual_mm, y_mm, continuity):
    x_grid = target_grid()
    n = len(x_grid)
    y_upper_raw = np.full(n, np.nan, dtype=np.float64)
    y_lower_raw = np.full(n, np.nan, dtype=np.float64)
    previous_center = None
    invalid_run_columns = 0

    for i, x_center in enumerate(x_grid):
        if continuity and invalid_run_columns >= MAX_TRACKING_GAP_COLUMNS:
            previous_center = None
        query_center = previous_center if continuity else None

        prof = bin_profile(Zd, x_actual_mm, x_center)
        if prof is None:
            invalid_run_columns += 1
            continue
        prof, ok = fill_small_gaps(prof)
        if not ok:
            invalid_run_columns += 1
            continue
        edges = halfmax_edges(prof, y_mm, previous_center=query_center)
        if edges is None:
            invalid_run_columns += 1
            continue

        y_lower_raw[i], y_upper_raw[i] = edges
        if continuity:
            previous_center = 0.5 * (edges[0] + edges[1])
        invalid_run_columns = 0

    y_lower, y_upper, w_mm, valid_mask = finalize_smoothed_boundaries(y_lower_raw, y_upper_raw)
    return {'x_grid_mm': x_grid, 'w_mm': w_mm, 'valid_mask': valid_mask}


def track_median_width_mm(Zd, x_actual_mm, y_mm, continuity):
    try:
        result = extract_swept(Zd, x_actual_mm, y_mm, continuity)
    except ValueError:
        return None
    valid_widths = result['w_mm'][result['valid_mask']]
    if valid_widths.size == 0:
        return None
    return float(np.median(valid_widths))


def ordering_verdict(medians):
    values = [medians[track_id] for track_id in TRACK_IDS]
    if any(value is None for value in values):
        return 'FLAG'
    return 'PASS' if all(a > b for a, b in zip(values, values[1:])) else 'FLAG'


def build_row(order, continuity, medians):
    row = {'detrend_order': order, 'continuity': continuity}
    for track_id in TRACK_IDS:
        row[f'median_width_{track_id}'] = medians[track_id]
    row['ordering_verdict'] = ordering_verdict(medians)
    return row


def run_sweep(raw_dir):
    height_dir = raw_dir / "height_maps"
    rows = []
    for order in DETREND_ORDERS:
        detrended = {}
        for track_id in TRACK_IDS:
            data = load_wyko_asc(height_dir, track_id)
            Zd, coef = robust_plane_detrend(
                data['Z_mm'], data['x_actual_mm'], data['y_mm'], order=order,
            )
            detrended[track_id] = (Zd, data['x_actual_mm'], data['y_mm'], coef)

        for continuity in CONTINUITY_OPTIONS:
            medians = {}
            for track_id in TRACK_IDS:
                Zd, x_actual_mm, y_mm, coef = detrended[track_id]
                if coef is None:
                    medians[track_id] = None
                    continue
                medians[track_id] = track_median_width_mm(Zd, x_actual_mm, y_mm, continuity)
            rows.append(build_row(order, continuity, medians))
    return rows


def print_sweep_table(rows):
    header = "order  continuity  " + "  ".join(
        f"track_{tid}(w={TRACK_POWER_W[tid]}W)" for tid in TRACK_IDS
    ) + "  verdict"
    print(f"\n{header}")
    for row in rows:
        values = "  ".join(
            "None" if row[f'median_width_{tid}'] is None else f"{row[f'median_width_{tid}']:.4f}"
            for tid in TRACK_IDS
        )
        print(f"{row['detrend_order']:>5}  {str(row['continuity']):>10}  {values}  {row['ordering_verdict']}")


def write_sweep_csv(csv_path, rows):
    fieldnames = ['detrend_order', 'continuity'] + [f'median_width_{tid}' for tid in TRACK_IDS] + ['ordering_verdict']
    with csv_path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            formatted = dict(row)
            for tid in TRACK_IDS:
                key = f'median_width_{tid}'
                value = formatted[key]
                formatted[key] = '' if value is None else f'{value:.6f}'
            writer.writerow(formatted)


def run_diagnostic(project_dir: Path) -> Path:
    project_root = resolve_repository_root(project_dir)
    raw_dir = resolve_raw_dir(project_root)
    raw_before = snapshot_raw(raw_dir)

    rows = run_sweep(raw_dir)
    print_sweep_table(rows)

    diagnostics_dir = resolve_output_path(
        project_root / "processed_data" / "targets" / "diagnostics",
        project_root,
        raw_dir,
    )
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    diagnostics_dir = resolve_output_path(diagnostics_dir, project_root, raw_dir)

    csv_path = resolve_output_path(
        diagnostics_dir / "width_regression_sweep.csv",
        project_root,
        raw_dir,
    )
    write_sweep_csv(csv_path, rows)

    raw_after = snapshot_raw(raw_dir)
    difference = raw_snapshot_diff(raw_before, raw_after)
    if any(difference.values()):
        raise RuntimeError(f"data/raw integrity FAIL: {difference}")
    print("data/raw/ integrity PASS: no files created, modified, or deleted.")
    print(f"Wrote sweep table: {csv_path}")
    return csv_path


def main():
    parser = argparse.ArgumentParser(
        description="Diagnose the Phase 1 width-ordering regression via a uniform detrend-order x continuity sweep.",
    )
    parser.add_argument("--project_dir", type=Path, default=Path("."), help="Repository/project root.")
    args = parser.parse_args()
    run_diagnostic(args.project_dir)


if __name__ == "__main__":
    main()
