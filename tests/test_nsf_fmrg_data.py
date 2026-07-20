from pathlib import Path
import sys

import numpy as np

# Allow running from repo root without installing as a package.
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

import nsf_fmrg_data


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


if __name__ == "__main__":
    tests = [
        test_default_order_removes_affine_surface,
        test_order_four_removes_quartic_bow,
        test_degenerate_fallback_is_preserved_for_all_orders,
        test_polynomial_basis_sizes_are_stable,
    ]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
