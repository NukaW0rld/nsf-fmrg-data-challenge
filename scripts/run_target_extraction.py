from pathlib import Path
import argparse
import json
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

# Allow running from repo root without installing as a package.
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from targets import extract_track_targets, extraction_params

TRACK_POWER_W = {8: 400, 10: 350, 14: 300, 21: 200}
TRACK_IDS = tuple(TRACK_POWER_W)
TARGET_GRID_STEP_MM = 0.2
EDGE_QA_WIDTH_MM = 0.5


def snapshot_raw(project_dir: Path) -> dict:
    raw_dir = project_dir / "data" / "raw"
    return {
        path.relative_to(project_dir): (path.stat().st_mtime_ns, path.stat().st_size)
        for path in raw_dir.rglob("*")
        if path.is_file()
    }


def shade_invalid_slots(ax, x_grid_mm, valid_mask):
    half_step = TARGET_GRID_STEP_MM / 2.0
    for x_mm in x_grid_mm[~valid_mask]:
        ax.axvspan(x_mm - half_step, x_mm + half_step, color="0.75", alpha=0.25, linewidth=0)


def save_residual_map(result, qa_dir: Path, track_id: int):
    Zd_mm = result["Zd_mm"]
    finite = np.isfinite(Zd_mm)
    if not finite.any():
        raise ValueError(f"Track {track_id} detrended map has no finite values for QA.")
    color_limit_mm = float(np.percentile(np.abs(Zd_mm[finite]), 99.0))
    if color_limit_mm == 0.0:
        color_limit_mm = float(np.finfo(np.float64).eps)

    fig, ax = plt.subplots(figsize=(12, 4))
    image = ax.imshow(
        Zd_mm,
        extent=[
            result["x_actual_mm"][0],
            result["x_actual_mm"][-1],
            result["y_mm"][0],
            result["y_mm"][-1],
        ],
        origin="lower",
        aspect="auto",
        cmap="coolwarm",
        vmin=-color_limit_mm,
        vmax=color_limit_mm,
    )
    ax.set_title(f"Track {track_id} post-detrend residual (D-14 bow/curvature check)")
    ax.set_xlabel("track position x (mm)")
    ax.set_ylabel("cross-track position y (mm)")
    colorbar = fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02)
    colorbar.set_label("detrended height (mm)")
    fig.tight_layout()
    fig.savefig(qa_dir / f"track_{track_id}_residual_map.png", dpi=160)
    plt.close(fig)


def save_overlay(result, qa_dir: Path, track_id: int):
    x_grid_mm = result["x_grid_mm"]
    valid_mask = result["valid_mask"]
    extent = [
        result["x_actual_mm"][0],
        result["x_actual_mm"][-1],
        result["y_mm"][0],
        result["y_mm"][-1],
    ]
    panels = (
        (result["Z_mm"], "raw height map", "viridis", "height (mm)"),
        (result["Zd_mm"], "detrended height map", "coolwarm", "detrended height (mm)"),
    )

    fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
    for ax, (Z_mm, title, cmap, colorbar_label) in zip(axes, panels):
        image = ax.imshow(Z_mm, extent=extent, origin="lower", aspect="auto", cmap=cmap)
        ax.plot(x_grid_mm, result["y_upper_mm"], color="white", linewidth=1.0, label="upper boundary")
        ax.plot(x_grid_mm, result["y_lower_mm"], color="black", linewidth=1.0, label="lower boundary")
        shade_invalid_slots(ax, x_grid_mm, valid_mask)
        ax.axvline(result["x_actual_mm"][0], color="gold", linestyle="--", linewidth=1.2)
        ax.text(
            result["x_actual_mm"][0] + 0.3,
            0.98,
            f'native coverage starts at {result["x_actual_mm"][0]:.2f} mm',
            transform=ax.get_xaxis_transform(),
            va="top",
            color="gold",
            fontsize=8,
        )
        ax.set_title(f"Track {track_id} {title}")
        ax.set_ylabel("cross-track position y (mm)")
        ax.legend(loc="lower right")
        colorbar = fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02)
        colorbar.set_label(colorbar_label)
    axes[-1].set_xlabel("track position x (mm)")
    fig.tight_layout()
    fig.savefig(qa_dir / f"track_{track_id}_overlay.png", dpi=160)
    plt.close(fig)


def save_width_curve(result, qa_dir: Path, track_id: int, median_width_mm: float, mean_width_mm: float):
    x_grid_mm = result["x_grid_mm"]
    valid_count = int(result["valid_mask"].sum())

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(x_grid_mm, result["w_mm"], color="tab:blue", linewidth=1.2)
    ax.axvspan(x_grid_mm[0], x_grid_mm[0] + EDGE_QA_WIDTH_MM, color="tab:orange", alpha=0.2)
    ax.axvspan(x_grid_mm[-1] - EDGE_QA_WIDTH_MM, x_grid_mm[-1], color="tab:orange", alpha=0.2)
    ax.text(
        0.01,
        0.97,
        f"median={median_width_mm:.4f} mm\nmean={mean_width_mm:.4f} mm\nvalid={valid_count}/400",
        transform=ax.transAxes,
        va="top",
        bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "0.7"},
    )
    ax.set_title(f"Track {track_id} extracted local width (D-12 crop-edge QA)")
    ax.set_xlabel("track position x (mm)")
    ax.set_ylabel("width (mm)")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(qa_dir / f"track_{track_id}_width.png", dpi=160)
    plt.close(fig)


def run_track(project_dir: Path, track_id: int) -> dict:
    height_dir = project_dir / "data" / "raw" / "height_maps"
    result = extract_track_targets(height_dir, track_id)
    print(f'Track {track_id} source: {result["file"]}')

    targets_dir = project_dir / "processed_data" / "targets"
    qa_dir = targets_dir / "qa"
    targets_dir.mkdir(parents=True, exist_ok=True)
    qa_dir.mkdir(parents=True, exist_ok=True)

    np.savez(
        targets_dir / f"track_{track_id}_targets.npz",
        x_grid_mm=result["x_grid_mm"].astype(np.float64),
        w_mm=result["w_mm"].astype(np.float64),
        y_upper_mm=result["y_upper_mm"].astype(np.float64),
        y_lower_mm=result["y_lower_mm"].astype(np.float64),
        valid_mask=result["valid_mask"].astype(bool),
    )

    valid_widths_mm = result["w_mm"][result["valid_mask"]]
    median_width_mm = float(np.median(valid_widths_mm))
    mean_width_mm = float(np.mean(valid_widths_mm))
    save_residual_map(result, qa_dir, track_id)
    save_overlay(result, qa_dir, track_id)
    save_width_curve(result, qa_dir, track_id, median_width_mm, mean_width_mm)

    return {
        "track_id": track_id,
        "laser_power_w": TRACK_POWER_W[track_id],
        "valid_count": int(result["valid_mask"].sum()),
        "median_width_mm": median_width_mm,
        "mean_width_mm": mean_width_mm,
    }


def print_results(summaries):
    print("\ntrack  power_W  valid_bins  median_mm  mean_mm")
    for summary in summaries:
        print(
            f'{summary["track_id"]:>5}  {summary["laser_power_w"]:>7}  '
            f'{summary["valid_count"]:>10}  {summary["median_width_mm"]:>9.4f}  '
            f'{summary["mean_width_mm"]:>7.4f}'
        )

    by_track = {summary["track_id"]: summary for summary in summaries}
    for higher_track, lower_track in zip(TRACK_IDS, TRACK_IDS[1:]):
        higher = by_track[higher_track]["median_width_mm"]
        lower = by_track[lower_track]["median_width_mm"]
        outcome = "PASS" if higher > lower else "FLAG"
        print(
            f"Ordering {higher_track} vs {lower_track}: "
            f"{higher:.4f} mm > {lower:.4f} mm — {outcome}"
        )
    print("Ordering FLAG outcomes are documented and never used to tune locked extraction constants.")


def main():
    parser = argparse.ArgumentParser(description="Extract local-width targets for all NSF FMRG tracks.")
    parser.add_argument("--project_dir", type=Path, default=Path("."), help="Repository/project root.")
    args = parser.parse_args()
    project_dir = args.project_dir.resolve()

    raw_before = snapshot_raw(project_dir)
    targets_dir = project_dir / "processed_data" / "targets"
    targets_dir.mkdir(parents=True, exist_ok=True)
    with (targets_dir / "extraction_params.json").open("w", encoding="utf-8") as stream:
        json.dump(extraction_params(), stream, indent=2, sort_keys=True)
        stream.write("\n")

    summaries = [run_track(project_dir, track_id) for track_id in TRACK_IDS]
    raw_after = snapshot_raw(project_dir)
    if raw_before != raw_after:
        changed = sorted(set(raw_before) | set(raw_after))
        changed = [path for path in changed if raw_before.get(path) != raw_after.get(path)]
        raise ValueError(f"data/raw/ integrity FAIL; changed paths: {changed}")
    print("data/raw/ integrity PASS: no files created, modified, or deleted.")
    print_results(summaries)


if __name__ == "__main__":
    main()
