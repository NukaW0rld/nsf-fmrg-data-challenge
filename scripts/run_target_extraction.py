from pathlib import Path
import argparse
import hashlib
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


def resolve_repository_root(project_dir: Path, repository_anchor: Path = REPO_ROOT) -> Path:
    anchor = Path(repository_anchor).resolve(strict=True)
    candidate = Path(project_dir).resolve(strict=True)
    if candidate != anchor:
        raise ValueError(f"Project directory must resolve to the canonical repository root {anchor}, got {candidate}.")

    markers = (
        candidate / "src" / "targets.py",
        candidate / "scripts" / "run_target_extraction.py",
    )
    missing = [path.relative_to(candidate).as_posix() for path in markers if not path.is_file()]
    if missing:
        raise ValueError(f"Canonical repository markers are missing: {missing}.")
    resolve_raw_dir(candidate)
    return candidate


def resolve_raw_dir(project_root: Path) -> Path:
    root = Path(project_root).resolve(strict=True)
    raw_dir = (root / "data" / "raw").resolve(strict=True)
    if not raw_dir.is_dir():
        raise ValueError(f"Resolved raw path is not a directory: {raw_dir}.")
    if not raw_dir.is_relative_to(root) or raw_dir == root:
        raise ValueError(f"Resolved data/raw path escapes the canonical repository: {raw_dir}.")
    return raw_dir


def resolve_output_path(path: Path, project_root: Path, raw_dir: Path) -> Path:
    root = Path(project_root).resolve(strict=True)
    protected_raw = Path(raw_dir).resolve(strict=True)
    candidate = Path(path).resolve(strict=False)
    if not candidate.is_relative_to(root):
        raise ValueError(f"Output path escapes the canonical repository: {candidate}.")
    if candidate == protected_raw or candidate.is_relative_to(protected_raw):
        raise ValueError(f"Output path enters the protected raw tree: {candidate}.")
    return candidate


def snapshot_raw(raw_dir: Path) -> dict:
    supplied = Path(raw_dir)
    resolved_raw = supplied.resolve(strict=True)
    if not supplied.is_absolute() or supplied != resolved_raw or not resolved_raw.is_dir():
        raise ValueError(f"snapshot_raw requires the resolved raw directory, got {supplied}.")

    snapshot = {}
    for path in sorted(resolved_raw.rglob("*"), key=lambda item: item.relative_to(resolved_raw).as_posix()):
        resolved_path = path.resolve(strict=True)
        if not resolved_path.is_relative_to(resolved_raw):
            raise ValueError(f"Raw-tree symlink escapes the protected directory: {path} -> {resolved_path}.")
        if not path.is_file():
            continue

        before = path.stat()
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        after = path.stat()
        if (before.st_mtime_ns, before.st_size) != (after.st_mtime_ns, after.st_size):
            raise RuntimeError(f"Raw file changed while being snapshotted: {path}.")
        relative = path.relative_to(resolved_raw).as_posix()
        snapshot[relative] = (before.st_mtime_ns, before.st_size, digest.hexdigest())
    return snapshot


def raw_snapshot_diff(before: dict, after: dict) -> dict:
    before_paths = set(before)
    after_paths = set(after)
    return {
        "added": sorted(after_paths - before_paths),
        "removed": sorted(before_paths - after_paths),
        "changed": sorted(path for path in before_paths & after_paths if before[path] != after[path]),
    }


def shade_invalid_slots(ax, x_grid_mm, valid_mask):
    half_step = TARGET_GRID_STEP_MM / 2.0
    for x_mm in x_grid_mm[~valid_mask]:
        ax.axvspan(x_mm - half_step, x_mm + half_step, color="0.75", alpha=0.25, linewidth=0)


def save_residual_map(result, qa_dir: Path, project_root: Path, raw_dir: Path, track_id: int):
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
    try:
        output_path = resolve_output_path(
            qa_dir / f"track_{track_id}_residual_map.png",
            project_root,
            raw_dir,
        )
        fig.savefig(output_path, dpi=160)
    finally:
        plt.close(fig)


def save_overlay(result, qa_dir: Path, project_root: Path, raw_dir: Path, track_id: int):
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
    try:
        output_path = resolve_output_path(
            qa_dir / f"track_{track_id}_overlay.png",
            project_root,
            raw_dir,
        )
        fig.savefig(output_path, dpi=160)
    finally:
        plt.close(fig)


def save_width_curve(
    result,
    qa_dir: Path,
    project_root: Path,
    raw_dir: Path,
    track_id: int,
    median_width_mm: float,
    mean_width_mm: float,
):
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
    try:
        output_path = resolve_output_path(
            qa_dir / f"track_{track_id}_width.png",
            project_root,
            raw_dir,
        )
        fig.savefig(output_path, dpi=160)
    finally:
        plt.close(fig)


def run_track(
    project_root: Path,
    raw_dir: Path,
    targets_dir: Path,
    qa_dir: Path,
    track_id: int,
) -> dict:
    height_dir = raw_dir / "height_maps"
    result = extract_track_targets(height_dir, track_id)
    print(f'Track {track_id} source: {result["file"]}')

    target_path = resolve_output_path(
        targets_dir / f"track_{track_id}_targets.npz",
        project_root,
        raw_dir,
    )
    np.savez(
        target_path,
        x_grid_mm=result["x_grid_mm"].astype(np.float64),
        w_mm=result["w_mm"].astype(np.float64),
        y_upper_mm=result["y_upper_mm"].astype(np.float64),
        y_lower_mm=result["y_lower_mm"].astype(np.float64),
        valid_mask=result["valid_mask"].astype(bool),
    )

    valid_widths_mm = result["w_mm"][result["valid_mask"]]
    median_width_mm = float(np.median(valid_widths_mm))
    mean_width_mm = float(np.mean(valid_widths_mm))
    save_residual_map(result, qa_dir, project_root, raw_dir, track_id)
    save_overlay(result, qa_dir, project_root, raw_dir, track_id)
    save_width_curve(
        result,
        qa_dir,
        project_root,
        raw_dir,
        track_id,
        median_width_mm,
        mean_width_mm,
    )

    return {
        "track_id": track_id,
        "laser_power_w": TRACK_POWER_W[track_id],
        "valid_count": int(result["valid_mask"].sum()),
        "median_width_mm": median_width_mm,
        "mean_width_mm": mean_width_mm,
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


def run_pipeline(
    project_dir: Path,
    track_ids=TRACK_IDS,
    track_runner=run_track,
    repository_anchor: Path = REPO_ROOT,
):
    project_root = resolve_repository_root(project_dir, repository_anchor=repository_anchor)
    raw_dir = resolve_raw_dir(project_root)
    raw_before = snapshot_raw(raw_dir)
    active_error = None
    summaries = None

    try:
        targets_dir = resolve_output_path(
            project_root / "processed_data" / "targets",
            project_root,
            raw_dir,
        )
        targets_dir.mkdir(parents=True, exist_ok=True)
        targets_dir = resolve_output_path(targets_dir, project_root, raw_dir)

        qa_dir = resolve_output_path(targets_dir / "qa", project_root, raw_dir)
        qa_dir.mkdir(parents=True, exist_ok=True)
        qa_dir = resolve_output_path(qa_dir, project_root, raw_dir)

        params_path = resolve_output_path(
            targets_dir / "extraction_params.json",
            project_root,
            raw_dir,
        )
        with params_path.open("w", encoding="utf-8") as stream:
            json.dump(extraction_params(), stream, indent=2, sort_keys=True)
            stream.write("\n")

        summaries = [
            track_runner(project_root, raw_dir, targets_dir, qa_dir, track_id)
            for track_id in track_ids
        ]
    except BaseException as exc:
        active_error = exc
        raise
    finally:
        try:
            raw_after = snapshot_raw(raw_dir)
        except BaseException as audit_error:
            failure = RuntimeError("data/raw integrity audit failed closed: final snapshot unavailable.")
            if active_error is not None:
                failure.add_note(f"Pipeline error pending during audit: {active_error!r}")
            raise failure from audit_error

        difference = raw_snapshot_diff(raw_before, raw_after)
        if any(difference.values()):
            details = "; ".join(
                f"{category}={paths}"
                for category, paths in difference.items()
                if paths
            )
            failure = RuntimeError(f"data/raw integrity FAIL: {details}")
            if active_error is not None:
                raise failure from active_error
            raise failure
        print("data/raw/ integrity PASS: no files created, modified, or deleted.")

    print_results(summaries, track_ids=track_ids)
    return summaries


def main():
    parser = argparse.ArgumentParser(description="Extract local-width targets for all NSF FMRG tracks.")
    parser.add_argument("--project_dir", type=Path, default=Path("."), help="Repository/project root.")
    args = parser.parse_args()
    run_pipeline(args.project_dir)


if __name__ == "__main__":
    main()
