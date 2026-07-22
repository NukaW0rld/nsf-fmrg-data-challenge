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
    DETREND_MAX_Y_DEGREE,
    DETREND_POLY_ORDER,
    TRACK_IDS,
    bead_exclusion_mask,
)
from nsf_fmrg_data import load_wyko_asc, robust_plane_detrend
from run_target_extraction import (
    raw_snapshot_diff,
    resolve_output_path,
    resolve_raw_dir,
    resolve_repository_root,
    snapshot_raw,
)

# Grid-geometry constants, not per-track tuning -- identical native y-grid
# and Y_STRIP_EXTENT_MM across all four tracks (matches the debug session's
# already-validated bands).
LOW_Y_BAND_MM = (0.0, 0.5)
BEAD_BAND_MM = (0.7, 1.3)
SAMPLE_X_MM = (30, 40, 50, 60, 70, 80, 90, 95, 99)
INTERIOR_X_MM = 60
FAR_EDGE_X_MM = 99


def shape_gap_at_x(plane, x_actual_mm, y_mm, x_target_mm):
    x_idx = int(np.argmin(np.abs(x_actual_mm - x_target_mm)))
    low_y_rows = (y_mm >= LOW_Y_BAND_MM[0]) & (y_mm <= LOW_Y_BAND_MM[1])
    bead_rows = (y_mm >= BEAD_BAND_MM[0]) & (y_mm <= BEAD_BAND_MM[1])
    low_y_value = float(np.nanmedian(plane[low_y_rows, x_idx]))
    bead_value = float(np.nanmedian(plane[bead_rows, x_idx]))
    return low_y_value - bead_value


def measure_track(height_dir, track_id):
    data = load_wyko_asc(height_dir, track_id)
    Z_mm = data['Z_mm']
    x_actual_mm = data['x_actual_mm']
    y_mm = data['y_mm']

    # The exact CURRENT production path (Amendment A5, no new parameter,
    # since none exists yet): observe only the currently-shipped fit.
    fit_mask = bead_exclusion_mask(Z_mm)
    Zd, coef = robust_plane_detrend(
        Z_mm, x_actual_mm, y_mm,
        order=DETREND_POLY_ORDER, fit_mask=fit_mask, max_y_degree=DETREND_MAX_Y_DEGREE,
    )
    plane = Z_mm - Zd

    row = {'track_id': track_id}
    for x_target_mm in SAMPLE_X_MM:
        row[f'shape_gap_x{x_target_mm}'] = shape_gap_at_x(plane, x_actual_mm, y_mm, x_target_mm)

    interior_gap = shape_gap_at_x(plane, x_actual_mm, y_mm, INTERIOR_X_MM)
    far_edge_gap = shape_gap_at_x(plane, x_actual_mm, y_mm, FAR_EDGE_X_MM)
    row['interior_gap'] = interior_gap
    row['far_edge_gap'] = far_edge_gap
    row['departure'] = abs(far_edge_gap - interior_gap)
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


def run_tail_collapse_diagnostic(project_dir: Path) -> Path:
    project_root = resolve_repository_root(project_dir)
    raw_dir = resolve_raw_dir(project_root)
    raw_before = snapshot_raw(raw_dir)

    height_dir = raw_dir / "height_maps"
    rows = [measure_track(height_dir, track_id) for track_id in TRACK_IDS]
    print_measurement_table(rows)

    # processed_data/diagnostics/ is a SIBLING of processed_data/targets/, not
    # a child of it: run_target_extraction.publish_staging_dir renames the
    # whole targets/ tree aside and rmtree's the backup on every extraction
    # run, so a CSV written under targets/ would be silently destroyed by
    # that publish.
    diagnostics_dir = resolve_output_path(
        project_root / "processed_data" / "diagnostics",
        project_root,
        raw_dir,
    )
    diagnostics_dir.mkdir(parents=True, exist_ok=True)

    csv_path = resolve_output_path(
        diagnostics_dir / "track10_tail_collapse_diagnosis.csv",
        project_root,
        raw_dir,
    )
    write_csv(csv_path, rows)

    raw_after = snapshot_raw(raw_dir)
    difference = raw_snapshot_diff(raw_before, raw_after)
    if any(difference.values()):
        raise RuntimeError(f"data/raw integrity FAIL: {difference}")
    print("data/raw/ integrity PASS: no files created, modified, or deleted.")
    print(f"Wrote tail-collapse diagnosis: {csv_path}")
    return csv_path


def main():
    parser = argparse.ArgumentParser(
        description="Measure the x-direction shape-gap evidence for track 10's x=70-100mm tail collapse.",
    )
    parser.add_argument("--project_dir", type=Path, default=Path("."), help="Repository/project root.")
    args = parser.parse_args()
    run_tail_collapse_diagnostic(args.project_dir)


if __name__ == "__main__":
    main()
