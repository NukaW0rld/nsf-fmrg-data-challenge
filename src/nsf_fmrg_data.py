from pathlib import Path
import re
import json
import numpy as np
from scipy.io import loadmat
from PIL import Image, ImageOps

COMMON_X_START_MM = 20.0
COMMON_X_END_MM = 100.0
THERMAL_FPS = 50.0
SCAN_SPEED_MM_PER_S = 10.0
THERMAL_MM_PER_FRAME = SCAN_SPEED_MM_PER_S / THERMAL_FPS
# find_thermal_array's candidate-scoring heuristic below biases toward arrays
# whose shape already contains this same frame count (400); a future change
# to the scan-geometry constants above that shifts this value also shifts
# that heuristic's intent.
EXTRACTED_THERMAL_FRAMES = int(round((COMMON_X_END_MM - COMMON_X_START_MM) / THERMAL_MM_PER_FRAME))


def natural_key(s):
    s = str(s)
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]


def find_track_file(root, track_id, suffixes):
    root = Path(root)
    suffixes = {s.lower() for s in suffixes}
    matches = []
    for p in root.rglob('*'):
        if p.is_file() and p.suffix.lower() in suffixes:
            name = p.name.lower()
            if re.search(rf'(^|[_\-\s]){track_id}($|[_\-\s\.])', name):
                matches.append(p)
    matches = sorted(matches, key=natural_key)
    return matches[0] if matches else None


def _loadmat_any(path):
    try:
        data = loadmat(path)
        return {k: v for k, v in data.items() if not k.startswith('__')}
    except NotImplementedError:
        import h5py
        out = {}
        with h5py.File(path, 'r') as f:
            def visit(name, obj):
                if hasattr(obj, 'shape'):
                    try:
                        out[name] = np.array(obj)
                    except Exception:
                        pass
            f.visititems(visit)
        return out


def find_thermal_array(mat_dict):
    candidates = []
    for k, v in mat_dict.items():
        arr = np.asarray(v)
        arr = np.squeeze(arr)
        if arr.ndim not in (3, 4):
            continue
        if not np.issubdtype(arr.dtype, np.number):
            continue
        if arr.ndim == 4:
            small_dims = [i for i, d in enumerate(arr.shape) if d in (1, 3, 4)]
            if small_dims:
                arr = np.take(arr, indices=0, axis=small_dims[-1])
                arr = np.squeeze(arr)
        if arr.ndim != 3:
            continue
        score = arr.size * (10 if 400 in arr.shape else 1)
        candidates.append((score, k, arr))
    if not candidates:
        raise ValueError('No thermal-like array found in MAT file.')
    candidates.sort(key=lambda x: x[0], reverse=True)
    key, arr = candidates[0][1], candidates[0][2]
    shape = arr.shape
    if shape[0] == shape[1] and shape[2] != shape[0]:
        arr_t = np.moveaxis(arr, 2, 0)
    elif shape[1] == shape[2]:
        arr_t = arr
    else:
        arr_t = np.moveaxis(arr, int(np.argmax(shape)), 0)
    return np.asarray(arr_t, dtype=np.float32), key


def thermal_frame_score(frames, top_percentile=99.5):
    return np.array([np.nanpercentile(fr, top_percentile) for fr in frames], dtype=np.float64)


def largest_true_run(mask):
    mask = np.asarray(mask, dtype=bool)
    if not mask.any():
        return None, None
    idx = np.flatnonzero(mask)
    breaks = np.where(np.diff(idx) > 1)[0]
    starts = np.r_[idx[0], idx[breaks + 1]]
    stops = np.r_[idx[breaks] + 1, idx[-1] + 1]
    j = int(np.argmax(stops - starts))
    return int(starts[j]), int(stops[j])


def detect_laser_on_interval(frames):
    score = thermal_frame_score(frames)
    n = len(score)
    pre = score[:max(5, n // 10)]
    med = np.nanmedian(pre)
    mad = 1.4826 * np.nanmedian(np.abs(pre - med))
    range_thr = np.nanmin(score) + 0.20 * (np.nanmax(score) - np.nanmin(score))
    mad_thr = med + 8.0 * max(mad, 1e-12)
    threshold = max(range_thr, mad_thr)
    mask = score > threshold
    on_start, on_stop = largest_true_run(mask)
    return on_start, on_stop, score, threshold


def extract_final_thermal_frames(thermal_dir, track_id):
    path = find_track_file(thermal_dir, track_id, ['.mat'])
    if not path:
        raise ValueError(f'No thermal file found for track {track_id} under {thermal_dir}.')
    expected_name = f'Thermal_{track_id}.mat'
    if Path(path).name != expected_name:
        raise ValueError(f'Expected {expected_name}, resolved {Path(path).name}.')
    mat = _loadmat_any(path)
    frames, key = find_thermal_array(mat)
    on_start, on_stop, score, threshold = detect_laser_on_interval(frames)
    stop_idx = int(on_stop)
    start_idx = max(0, stop_idx - EXTRACTED_THERMAL_FRAMES)
    segment = frames[start_idx:stop_idx]
    indices = np.arange(start_idx, stop_idx)
    x_mm_center = COMMON_X_END_MM - ((stop_idx - indices) - 0.5) * THERMAL_MM_PER_FRAME
    return {
        'file': str(path), 'variable': key, 'raw_frames': frames,
        'frames': segment, 'x_mm_center': x_mm_center,
        'on_start': int(on_start), 'on_stop': int(on_stop),
        'start_idx': int(start_idx), 'stop_idx': int(stop_idx),
        'score': score, 'threshold': float(threshold),
    }


def get_sem_tile_paths(sem_dir, track_id):
    root = Path(sem_dir) / f'SEM_{track_id}' / 'PlainImages'
    if not root.is_dir():
        raise ValueError(f'Expected SEM directory {root} for track {track_id}.')
    if root.is_symlink() or root.parent.is_symlink():
        raise ValueError(f'SEM path must not be a symlink: {root}.')
    suffixes = {'.tif', '.tiff', '.png', '.jpg', '.jpeg'}
    files = [p for p in root.iterdir() if p.is_file() and p.suffix.lower() in suffixes]
    return sorted(files, key=natural_key)


def load_sem_tile(path):
    return np.asarray(ImageOps.grayscale(Image.open(path)))


def parse_wyko_header(path):
    header = {}
    with open(path, 'r', errors='replace') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 3 and parts[0].lower() == 'x' and parts[1].lower() == 'size':
                header['x_size'] = int(float(parts[2]))
            elif len(parts) >= 3 and parts[0].lower() == 'y' and parts[1].lower() == 'size':
                header['y_size'] = int(float(parts[2]))
            elif parts and parts[0].lower() == 'pixel_size':
                header['pixel_size_mm'] = float(parts[-1])
            if parts and parts[0].upper() == 'RAW_DATA':
                break
    return header


def load_wyko_asc(height_dir, track_id, crop_to_common=True):
    path = find_track_file(height_dir, track_id, ['.asc', '.txt'])
    if not path:
        raise ValueError(f'No height-map file found for track {track_id} under {height_dir}.')
    header = parse_wyko_header(path)
    if 'x_size' not in header or 'y_size' not in header:
        raise ValueError(f'{path} header is missing X Size/Y Size fields.')
    x_size = int(header['x_size'])
    y_size = int(header['y_size'])
    pixel = float(header.get('pixel_size_mm', 0.003982))
    n_expected = x_size * y_size
    z_mm_flat = np.empty(n_expected, dtype=np.float32)
    z_mm_flat.fill(np.nan)
    count = 0
    in_raw = False
    with open(path, 'r', errors='replace') as f:
        for line in f:
            parts = line.strip().split()
            if not in_raw:
                if parts and parts[0].upper() == 'RAW_DATA':
                    in_raw = True
                continue
            if len(parts) < 3:
                continue
            z_tok = parts[2]
            z_mm_flat[count] = np.nan if z_tok.lower() == 'bad' else float(z_tok) * 1e-6
            count += 1
            if count >= n_expected:
                break
    Z_x_y = z_mm_flat.reshape((x_size, y_size))
    Z_yx = Z_x_y.T
    x_local = np.arange(x_size, dtype=np.float64) * pixel
    y_mm = np.arange(y_size, dtype=np.float64) * pixel
    x_actual_raw = 100.0 - x_local
    sort_idx = np.argsort(x_actual_raw)
    x_actual = x_actual_raw[sort_idx]
    x_local_sorted = x_local[sort_idx]
    Z_yx = Z_yx[:, sort_idx]
    if crop_to_common:
        mask = (x_actual >= COMMON_X_START_MM) & (x_actual <= COMMON_X_END_MM)
        x_actual = x_actual[mask]
        x_local_sorted = x_local_sorted[mask]
        Z_yx = Z_yx[:, mask]
    return {
        'file': str(path), 'header': header, 'Z_mm': Z_yx,
        'x_actual_mm': x_actual, 'x_local_mm': x_local_sorted, 'y_mm': y_mm,
    }


def robust_plane_detrend(Z_mm, x_mm, y_mm, stride_x=40, stride_y=2, order=1, fit_mask=None, max_y_degree=None):
    Zs = Z_mm[::stride_y, ::stride_x]
    xs = x_mm[::stride_x]
    ys = y_mm[::stride_y]
    Xs, Ys = np.meshgrid(xs, ys)
    z = Zs.ravel()
    valid = np.isfinite(z)
    if fit_mask is not None:
        fit_mask_strided = np.asarray(fit_mask, dtype=bool)[::stride_y, ::stride_x]
        valid = valid & fit_mask_strided.ravel()
    if not isinstance(order, (int, np.integer)) or order < 0:
        raise ValueError('order must be a non-negative integer.')
    if max_y_degree is not None and (not isinstance(max_y_degree, (int, np.integer)) or max_y_degree < 0):
        raise ValueError('max_y_degree must be a non-negative integer or None.')
    if valid.sum() < 100:
        return Z_mm.copy(), None

    exponents = [
        (i, degree - i)
        for degree in range(order + 1)
        for i in range(degree + 1)
    ]
    if max_y_degree is not None:
        exponents = [(i, j) for i, j in exponents if j <= max_y_degree]
    x_center = 0.5 * (x_mm[0] + x_mm[-1])
    y_center = 0.5 * (y_mm[0] + y_mm[-1])
    Xs_centered = Xs - x_center
    Ys_centered = Ys - y_center
    A = np.column_stack([
        Xs_centered.ravel() ** i * Ys_centered.ravel() ** j
        for i, j in exponents
    ])

    keep = valid.copy()
    coef = None
    for _ in range(3):
        coef, *_ = np.linalg.lstsq(A[keep], z[keep], rcond=None)
        resid = z - A @ coef
        rv = resid[valid]
        lo, hi = np.nanpercentile(rv, [5, 95])
        keep_new = valid & (resid >= lo) & (resid <= hi)
        if keep_new.sum() < 100:
            break
        keep = keep_new
    x_full = x_mm[None, :] - x_center
    y_full = y_mm[:, None] - y_center
    plane = sum(
        coefficient * x_full**i * y_full**j
        for coefficient, (i, j) in zip(coef, exponents)
    )
    return Z_mm - plane, coef


def display_shear_grid(x_mm, y_mm, slope_eff, strength=1.0, reference_x=None):
    x_mm = np.asarray(x_mm)
    y_mm = np.asarray(y_mm)
    if reference_x is None:
        reference_x = 0.5 * (float(x_mm[0]) + float(x_mm[-1]))
    correction = strength * slope_eff * (x_mm - reference_x)
    Y_plot = y_mm[:, None] - correction[None, :]
    X_plot = np.tile(x_mm[None, :], (len(y_mm), 1))
    return X_plot, Y_plot, correction
