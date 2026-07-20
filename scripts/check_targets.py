from pathlib import Path
import argparse
import json
import sys

import numpy as np

# Allow running from repo root without installing as a package.
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from targets import extraction_params, target_grid

TRACK_POWER_W = {8: 400, 10: 350, 14: 300, 21: 200}
TRACK_IDS = tuple(TRACK_POWER_W)
EXPECTED_KEYS = {"x_grid_mm", "w_mm", "y_upper_mm", "y_lower_mm", "valid_mask"}
FLOAT_KEYS = ("x_grid_mm", "w_mm", "y_upper_mm", "y_lower_mm")
EXPECTED_SHAPE = (400,)
Y_STRIP_EXTENT_MM = 1.907


def require(condition, message):
    if not bool(condition):
        raise ValueError(message)


def check_track(targets_dir: Path, track_id: int) -> dict:
    target_path = targets_dir / f"track_{track_id}_targets.npz"
    require(target_path.exists(), f"Track {track_id}: missing artifact {target_path}.")

    with np.load(target_path) as artifact:
        require(set(artifact.files) == EXPECTED_KEYS, (
            f"Track {track_id}: expected keys {sorted(EXPECTED_KEYS)}, got {sorted(artifact.files)}."
        ))
        for key in FLOAT_KEYS:
            require(artifact[key].dtype == np.dtype(np.float64), (
                f"Track {track_id}: {key} must be float64, got {artifact[key].dtype}."
            ))
            require(artifact[key].shape == EXPECTED_SHAPE, (
                f"Track {track_id}: {key} must have shape {EXPECTED_SHAPE}, got {artifact[key].shape}."
            ))
        require(artifact["valid_mask"].dtype == np.dtype(bool), (
            f'Track {track_id}: valid_mask must be bool, got {artifact["valid_mask"].dtype}.'
        ))
        require(artifact["valid_mask"].shape == EXPECTED_SHAPE, (
            f'Track {track_id}: valid_mask must have shape {EXPECTED_SHAPE}, '
            f'got {artifact["valid_mask"].shape}.'
        ))

        x_grid_mm = artifact["x_grid_mm"]
        w_mm = artifact["w_mm"]
        y_upper_mm = artifact["y_upper_mm"]
        y_lower_mm = artifact["y_lower_mm"]
        valid_mask = artifact["valid_mask"]

        require(np.isclose(x_grid_mm[0], 20.1), (
            f"Track {track_id}: first grid slot must be 20.1 mm, got {x_grid_mm[0]}."
        ))
        require(np.allclose(np.diff(x_grid_mm), 0.2), f"Track {track_id}: grid step is not uniformly 0.2 mm.")
        require(np.allclose(x_grid_mm, target_grid()), (
            f"Track {track_id}: persisted grid differs from targets.target_grid()."
        ))
        require(np.array_equal(np.isfinite(w_mm), valid_mask), (
            f"Track {track_id}: finite width slots do not equal valid_mask."
        ))
        require(np.array_equal(np.isfinite(y_upper_mm), valid_mask), (
            f"Track {track_id}: finite upper-boundary slots do not equal valid_mask."
        ))
        require(np.array_equal(np.isfinite(y_lower_mm), valid_mask), (
            f"Track {track_id}: finite lower-boundary slots do not equal valid_mask."
        ))
        require(np.allclose(w_mm[valid_mask], y_upper_mm[valid_mask] - y_lower_mm[valid_mask]), (
            f"Track {track_id}: width does not equal upper minus lower boundary."
        ))
        require(np.all(y_upper_mm[valid_mask] > y_lower_mm[valid_mask]), (
            f"Track {track_id}: crossed or degenerate boundaries survived in valid slots."
        ))
        require(np.all(w_mm[valid_mask] > 0.0), f"Track {track_id}: valid widths must be positive.")
        require(np.all(w_mm[valid_mask] < Y_STRIP_EXTENT_MM), (
            f"Track {track_id}: valid width exceeds the {Y_STRIP_EXTENT_MM} mm y-strip extent."
        ))

        valid_count = int(valid_mask.sum())
        require(valid_count > 0, f"Track {track_id}: all-invalid artifacts are prohibited.")
        valid_fraction = valid_count / len(valid_mask)
        if valid_fraction < 0.5:
            print(f"Track {track_id} valid fraction {valid_fraction:.1%} is below 50% — FLAG")

        return {
            "track_id": track_id,
            "laser_power_w": TRACK_POWER_W[track_id],
            "valid_count": valid_count,
            "median_width_mm": float(np.median(w_mm[valid_mask])),
            "mean_width_mm": float(np.mean(w_mm[valid_mask])),
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


def main():
    parser = argparse.ArgumentParser(description="Assert persisted NSF FMRG target artifacts.")
    parser.add_argument("--project_dir", type=Path, default=Path("."), help="Repository/project root.")
    args = parser.parse_args()
    targets_dir = args.project_dir.resolve() / "processed_data" / "targets"

    params_path = targets_dir / "extraction_params.json"
    require(params_path.exists(), f"Missing extraction provenance {params_path}.")
    with params_path.open(encoding="utf-8") as stream:
        persisted_params = json.load(stream)
    require(persisted_params == extraction_params(), (
        "Persisted extraction_params.json does not match the locked code constants."
    ))

    summaries = [check_track(targets_dir, track_id) for track_id in TRACK_IDS]
    print_results(summaries)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
