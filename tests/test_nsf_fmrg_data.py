from pathlib import Path
import sys
import tempfile

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


def synthetic_grid():
    x_mm = np.linspace(20.0, 100.0, 401)
    y_mm = np.linspace(0.0, 2.0, 241)
    x_grid, y_grid = np.meshgrid(x_mm, y_mm)
    return x_mm, y_mm, x_grid, y_grid


def test_default_order_removes_affine_surface():
    x_mm, y_mm, x_grid, y_grid = synthetic_grid()
    Z_mm = 0.003 * x_grid - 0.02 * y_grid + 0.7

    residual, coef = nsf_fmrg_data.robust_plane_detrend(Z_mm, x_mm, y_mm)

    require(coef is not None, "an affine surface must produce fitted coefficients")
    require(
        np.nanstd(residual) < 1e-12,
        "the default order=1 fit must remove a pure affine surface",
    )


def test_order_four_removes_quartic_bow():
    x_mm, y_mm, x_grid, y_grid = synthetic_grid()
    centered_x = (x_grid - 60.0) / 40.0
    quartic_bow = 0.08 * centered_x**4 - 0.03 * centered_x**2
    Z_mm = 0.003 * x_grid - 0.02 * y_grid + 0.7 + quartic_bow

    residual_order_one, _ = nsf_fmrg_data.robust_plane_detrend(
        Z_mm, x_mm, y_mm, order=1
    )
    residual_order_four, _ = nsf_fmrg_data.robust_plane_detrend(
        Z_mm, x_mm, y_mm, order=4
    )

    order_one_std = float(np.nanstd(residual_order_one))
    order_four_std = float(np.nanstd(residual_order_four))
    require(order_one_std > 1e-4, "order=1 must leave the quartic bow visible")
    require(
        order_four_std < order_one_std / 100.0,
        "order=4 must reduce quartic-bow residual magnitude by at least 100x",
    )


def test_degenerate_fallback_is_preserved_for_all_orders():
    x_mm = np.linspace(20.0, 21.0, 20)
    y_mm = np.linspace(0.0, 1.0, 20)
    Z_mm = np.arange(400, dtype=np.float64).reshape(20, 20)

    for order in (1, 4):
        residual, coef = nsf_fmrg_data.robust_plane_detrend(
            Z_mm, x_mm, y_mm, stride_x=1, stride_y=5, order=order
        )
        require(coef is None, f"order={order} must preserve the degenerate fallback")
        require(
            np.array_equal(residual, Z_mm),
            f"order={order} fallback must return an unchanged copy",
        )
        require(residual is not Z_mm, "the fallback must return a copy, not the input object")


def test_robust_plane_detrend_fit_mask_excludes_bead_from_fit():
    # Synthetic height map = smooth low-order background (identical to the
    # existing quartic-bow regression) + an elevated rectangular bead
    # corridor whose height itself varies smoothly along x (the along-track
    # direction), mirroring the 01-06-DIAGNOSIS mechanism: an unmasked
    # order-4 fit has enough x-degrees-of-freedom to partially absorb the
    # bead's own along-track profile into the "background."
    x_mm, y_mm, x_grid, y_grid = synthetic_grid()
    centered_x = (x_grid - 60.0) / 40.0
    background = 0.003 * x_grid - 0.02 * y_grid + 0.7 + (
        0.08 * centered_x**4 - 0.03 * centered_x**2
    )
    bead_amplitude_x = np.clip(0.15 * (1.0 - centered_x**2), 0.0, None)
    bead_rows = (y_grid >= 0.6) & (y_grid <= 1.4)
    Z_mm = background.copy()
    Z_mm[bead_rows] += bead_amplitude_x[bead_rows]

    fit_mask = np.ones(Z_mm.shape, dtype=bool)
    fit_mask[bead_rows] = False

    residual_unmasked, coef_unmasked = nsf_fmrg_data.robust_plane_detrend(
        Z_mm, x_mm, y_mm, order=4
    )
    residual_masked, coef_masked = nsf_fmrg_data.robust_plane_detrend(
        Z_mm, x_mm, y_mm, order=4, fit_mask=fit_mask
    )

    require(coef_unmasked is not None, "the unmasked order-4 fit must produce coefficients")
    require(coef_masked is not None, "the masked order-4 fit must produce coefficients")
    require(
        residual_masked.shape == Z_mm.shape and residual_unmasked.shape == Z_mm.shape,
        "fit_mask must not change the output shape or coverage",
    )

    center_x_idx = int(np.argmin(np.abs(x_mm - 60.0)))
    bead_row_idx = int(np.argmin(np.abs(y_mm - 1.0)))
    background_row_idx = int(np.argmin(np.abs(y_mm - 0.1)))
    true_bead_height = float(bead_amplitude_x[bead_row_idx, center_x_idx])

    unmasked_bead_height = float(
        residual_unmasked[bead_row_idx, center_x_idx]
        - residual_unmasked[background_row_idx, center_x_idx]
    )
    masked_bead_height = float(
        residual_masked[bead_row_idx, center_x_idx]
        - residual_masked[background_row_idx, center_x_idx]
    )

    require(
        masked_bead_height > 0.9 * true_bead_height,
        "the masked fit must recover the bead's true height at the corridor peak",
    )
    require(
        unmasked_bead_height < 0.5 * true_bead_height,
        "the unmasked order-4 fit must suppress the bead height by absorbing it into the background",
    )


def test_polynomial_basis_sizes_are_stable():
    x_mm, y_mm, x_grid, y_grid = synthetic_grid()
    Z_mm = 0.003 * x_grid - 0.02 * y_grid + 0.7

    _, coef_order_one = nsf_fmrg_data.robust_plane_detrend(
        Z_mm, x_mm, y_mm, order=1
    )
    _, coef_order_four = nsf_fmrg_data.robust_plane_detrend(
        Z_mm, x_mm, y_mm, order=4
    )

    require(len(coef_order_one) == 3, "order=1 must use the legacy 3-term basis")
    require(len(coef_order_four) == 15, "order=4 must use a 15-term total-degree basis")

    _, coef_order_four_capped = nsf_fmrg_data.robust_plane_detrend(
        Z_mm, x_mm, y_mm, order=4, max_y_degree=2
    )
    require(
        len(coef_order_four_capped) == 12,
        "order=4 with max_y_degree=2 must drop the three cross-track-degree-3/4 terms (12-term basis)",
    )


def test_detrend_edge_fix_preserves_default_behavior():
    # Amendment A5: the max_y_degree keyword must be off by default, so every
    # other caller (order=1 affine path, notebooks, diagnose_width_regression.py's
    # historical rows) is bit-for-bit unchanged.
    x_mm, y_mm, x_grid, y_grid = synthetic_grid()
    centered_x = (x_grid - 60.0) / 40.0
    Z_mm = 0.003 * x_grid - 0.02 * y_grid + 0.7 + (
        0.08 * centered_x**4 - 0.03 * centered_x**2
    )

    for order in (1, 4):
        residual_omitted, coef_omitted = nsf_fmrg_data.robust_plane_detrend(
            Z_mm, x_mm, y_mm, order=order
        )
        residual_explicit_none, coef_explicit_none = nsf_fmrg_data.robust_plane_detrend(
            Z_mm, x_mm, y_mm, order=order, max_y_degree=None
        )
        require(
            np.array_equal(residual_omitted, residual_explicit_none, equal_nan=True),
            f"order={order}: omitting max_y_degree must match max_y_degree=None bit-for-bit",
        )
        require(
            np.array_equal(coef_omitted, coef_explicit_none),
            f"order={order}: coefficients must match bit-for-bit between omitted and explicit-None max_y_degree",
        )

    _, coef_default = nsf_fmrg_data.robust_plane_detrend(Z_mm, x_mm, y_mm, order=4)
    require(
        len(coef_default) == 15,
        "the default (max_y_degree=None) must use the full 15-term order=4 basis, not a silently-capped one",
    )


def _track10_shaped_edge_scenario(shelf_amplitude_mm):
    # Track-10-shaped synthetic grid: long along-track extent, short
    # cross-track strip (480 samples matching the measured Wyko y_size), a
    # smooth low-order substrate warp, a bounded near-edge shelf feature
    # (the kind of genuine, localized substrate structure a degree-4-in-y
    # basis over a ~1.9mm strip can only represent by ringing/extrapolating,
    # producing a much larger edge departure than a lower-degree fit would),
    # and an interior bead well clear of both edges, masked from the fit
    # exactly as the production path masks it.
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


def _fitted_surface_edge_departures(Z_mm, x_mm, y_mm, fit_mask, max_y_degree):
    residual, coef = nsf_fmrg_data.robust_plane_detrend(
        Z_mm, x_mm, y_mm, order=4, fit_mask=fit_mask, max_y_degree=max_y_degree
    )
    require(coef is not None, "the scenario must produce a valid fit")
    fitted = Z_mm - residual
    profile = np.median(fitted, axis=1)
    mid = len(profile) // 2
    return abs(profile[0] - profile[mid]), abs(profile[-1] - profile[mid])


def test_detrend_does_not_diverge_at_strip_edge():
    # 01-11-CRITERION.md's tolerance: the fitted surface's edge value must
    # stay within 0.05 mm of its own interior midpoint.
    edge_tolerance_mm = 0.05
    Z_mm, x_mm, y_mm, fit_mask = _track10_shaped_edge_scenario(shelf_amplitude_mm=0.5)

    default_y0, default_yN = _fitted_surface_edge_departures(
        Z_mm, x_mm, y_mm, fit_mask, max_y_degree=None
    )
    require(
        default_y0 > edge_tolerance_mm,
        "an uncapped order=4-in-y masked detrend must manufacture an edge feature "
        "the synthetic substrate does not itself contain, exceeding the criterion's tolerance",
    )

    fixed_y0, fixed_yN = _fitted_surface_edge_departures(
        Z_mm, x_mm, y_mm, fit_mask, max_y_degree=targets.DETREND_MAX_Y_DEGREE
    )
    require(
        fixed_y0 <= edge_tolerance_mm,
        "the selected fix must bring the y=0 edge departure within the criterion's tolerance",
    )
    require(
        fixed_yN <= edge_tolerance_mm,
        "the selected fix must bring the y=N edge departure within the criterion's tolerance",
    )


def test_find_track_file_rejects_unanchored_substring_match():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / 'Heightmap_210.ASC').write_bytes(b"")
        result = nsf_fmrg_data.find_track_file(root, 10, ['.asc'])
        require(
            result is None,
            "a bare substring occurrence ('10' inside '210') must not qualify as a match",
        )


def test_find_track_file_still_resolves_real_dataset_names():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for track_id in (8, 10, 14, 21):
            (root / f'Heightmap_{track_id}.ASC').write_bytes(b"")
        for track_id in (8, 10, 14, 21):
            result = nsf_fmrg_data.find_track_file(root, track_id, ['.asc'])
            require(result is not None, f"track {track_id} must still resolve")
            require(
                result.name == f'Heightmap_{track_id}.ASC',
                f"track {track_id} resolved to {result.name}, expected Heightmap_{track_id}.ASC",
            )


def test_height_map_loader_raises_value_error_when_unresolved():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            nsf_fmrg_data.load_wyko_asc(tmp, 10)
        except ValueError:
            pass
        else:
            raise AssertionError("load_wyko_asc must raise ValueError when no file resolves")


def test_thermal_loader_rejects_unresolved_or_mismatched_filename():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            nsf_fmrg_data.extract_final_thermal_frames(tmp, 8)
        except ValueError:
            pass
        else:
            raise AssertionError(
                "extract_final_thermal_frames must raise ValueError on an empty directory"
            )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / 'Track_8_data.mat').write_bytes(b"")
        try:
            nsf_fmrg_data.extract_final_thermal_frames(root, 8)
        except ValueError:
            pass
        else:
            raise AssertionError(
                "extract_final_thermal_frames must raise ValueError on a mismatched basename"
            )


def test_sem_tile_paths_rejects_missing_or_symlinked_track_directory():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            nsf_fmrg_data.get_sem_tile_paths(tmp, 8)
        except ValueError:
            pass
        else:
            raise AssertionError(
                "get_sem_tile_paths must raise ValueError when SEM_{track_id} is absent"
            )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        real_plain_images = root / 'SEM_10' / 'PlainImages'
        real_plain_images.mkdir(parents=True)
        (real_plain_images / 'tile_0.png').write_bytes(b"")
        (root / 'SEM_8').symlink_to(root / 'SEM_10', target_is_directory=True)
        try:
            nsf_fmrg_data.get_sem_tile_paths(root, 8)
        except ValueError:
            pass
        else:
            raise AssertionError(
                "get_sem_tile_paths must raise ValueError for a symlinked track directory, "
                "not silently return another track's tiles"
            )


if __name__ == "__main__":
    tests = [
        test_default_order_removes_affine_surface,
        test_order_four_removes_quartic_bow,
        test_degenerate_fallback_is_preserved_for_all_orders,
        test_polynomial_basis_sizes_are_stable,
        test_robust_plane_detrend_fit_mask_excludes_bead_from_fit,
        test_detrend_edge_fix_preserves_default_behavior,
        test_detrend_does_not_diverge_at_strip_edge,
        test_find_track_file_rejects_unanchored_substring_match,
        test_find_track_file_still_resolves_real_dataset_names,
        test_height_map_loader_raises_value_error_when_unresolved,
        test_thermal_loader_rejects_unresolved_or_mismatched_filename,
        test_sem_tile_paths_rejects_missing_or_symlinked_track_directory,
    ]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
