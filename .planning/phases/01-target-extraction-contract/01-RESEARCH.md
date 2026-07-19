# Phase 1: Target Extraction & Contract - Research

**Researched:** 2026-07-19
**Domain:** Profilometry height-map processing — local track-width extraction (Wyko/Bruker `.ASC` → `w_i(x)` on a 0.2mm grid)
**Confidence:** HIGH (all load-bearing claims verified by running code against the actual 4 raw height-map files in this session)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Edge-detection method (how y_upper/y_lower are found per x-column)
- **D-01:** Use a relative half-max threshold: for each x-column's (already-detrended) y-profile `Z(y)`, estimate a local baseline and peak height, then set each edge where `Z` crosses `baseline + 0.5*(peak - baseline)`. Never a fixed absolute height value — track heights vary too much across the 4 laser powers (per PITFALLS.md Pitfall 6).
- **D-02:** Baseline = 5th percentile, peak = 95th percentile of that column's `Z(y)` values (per-column percentile split, not a track-wide baseline or a parametric peak/shoulder fit).
- **D-03:** Half-max fraction locked at 0.5 (50%) with the 5th/95th percentile baseline/peak — the classic half-max/FWHM-style convention.
- **D-04:** Add a minimum peak-baseline separation validity check: if `(peak - baseline)` for a column falls below a fixed minimum (tied to the profilometer's noise floor), that x position is marked invalid rather than reporting a spurious noise-driven edge. This check feeds directly into the valid-coordinate mask.

#### Track 21 gap-handling rule (applies identically to all tracks, triggers mostly on 21)
- **D-05:** Small gaps (≤10 consecutive NaN/'bad' pixels within a column) are linearly interpolated along `y` only, within that single x-column — never 2D/cross-column interpolation, to avoid smearing real x-direction (scan-direction) structure across columns.
- **D-06:** If a gap in a column exceeds 10 consecutive NaNs (in the region relevant to edge detection), that entire x-column is marked invalid via the valid-coordinate mask rather than guessed/interpolated.
- **D-07:** Output `w_i(x)` stays on a fixed shared 0.2mm x-grid with the **same length/positions across all 4 tracks**. Invalid x positions keep their grid slot with `width = NaN` and a `False` entry in the boolean valid-coordinate mask — never a ragged/dropped-position array. This directly matters for Phase 2's alignment step, which will consume this same grid.

#### Smoothing scale & method
- **D-08:** Use a Savitzky-Golay filter (NaN-aware), not a plain moving average and not "grid-binning only" — SG preserves local peaks/slopes better, which matters directly for the organizer's "preservation of spatial variation" evaluation criterion.
- **D-09:** Window ≈1mm of scan distance (≈5 points at the 0.2mm grid spacing), polynomial order 2-3.
- **D-10:** Smoothing is applied to `y_upper(x)` and `y_lower(x)` **separately**, and `w(x)` is derived from the smoothed boundaries afterward — not smoothing the raw width curve directly. This also keeps boundary curves available if boundary-function output (TARGET-03/v2 stretch) is pursued later.
- **D-11:** The SG fit skips invalid/masked x positions rather than interpolating through them first — a position already invalidated by D-04/D-06 stays NaN in the smoothed output too. No fabricated values for excluded positions (matches TARGET-02's "no silently dropped gaps" success criterion, interpreted as "no silently fabricated data" for excluded positions).
- **D-12:** Edge effects at the 20mm/100mm crop boundaries (Pitfall 7): use SG's edge/interp boundary mode (shrinking window near the crop edges rather than assuming out-of-crop data exists) — no exclusion of boundary positions from output, but the QA plots must make this edge behavior visually inspectable/documented rather than silent.

#### Detrending approach
- **D-13:** Keep `robust_plane_detrend()` from `src/nsf_fmrg_data.py` as-is (existing, working infrastructure) — do not upgrade to a higher-order polynomial surface preemptively.
- **D-14:** Add a mandatory QA step: visually inspect post-detrend residual maps for all 4 tracks, confirming no obvious remaining bow/curvature (Pitfall 6's concern) before the target extractor is trusted. If curvature is visible in this check, escalate to a fix at that point — don't pre-solve an unconfirmed problem.
- **D-15:** Detrending happens once per full (cropped) track, before edge detection runs — not per-column or per-local-window. Keeps detrending and edge-detection as separate, independently testable steps.
- **D-16:** Keep `robust_plane_detrend()`'s existing default stride (`stride_x=40, stride_y=2`) unchanged. Don't symmetrize preemptively; revisit only if the D-14 residual-curvature QA check surfaces an actual problem.

### Claude's Discretion
- Exact noise-floor value used for the D-04 minimum peak-baseline separation threshold (should be grounded in the profilometer's stated vertical resolution/noise characteristics, determined during implementation/research).
- Precise scipy `savgol_filter` boundary-mode parameter choice satisfying D-12 (e.g. `mode='interp'` vs `'nearest'`) — pick during implementation, verify visually per D-12.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope (implementation decisions for the locked TARGET-01/TARGET-02 requirements). No new capabilities were proposed during discussion.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TARGET-01 | Local-width target contract specified/documented before extraction code: width definition, threshold rule, smoothing scale, 0.2mm output grid, valid-coordinate mask, explicit Track 21 gap rule; one rule for all 4 tracks | Contract = CONTEXT.md D-01–D-16 (per SPEC). **Empirical finding below requires one interpretive amendment**: the gap/edge rules must operate on the 0.2mm-binned median profile, not per native ~4µm column (§Critical Empirical Findings, Finding 1) — otherwise 0% of columns survive on *every* track. Grid recommendation: match thermal frame centers 20.1–99.9mm, 400 slots (§Architecture Patterns). Noise-floor value grounded in measured substrate statistics (§Finding 4). |
| TARGET-02 | Extractor implements the contract, persists per-track artifacts under `processed_data/targets/`, visual QA on all 4 tracks incl. track 21 gaps, width ordering 8>10>14>21, one shared parameterization | Verified pipeline shape: `load_wyko_asc` → `robust_plane_detrend` → bin-to-0.2mm → gap rule → half-max edges → validity mask → NaN-aware SG → persist `.npz` → QA plots. Probe run on all 4 real tracks produced 288–374 valid bins/track and plausible widths (0.6–0.9mm median). **Width-ordering gate is at risk between tracks 8 and 10** (§Finding 3) — plan must handle this outcome honestly (prohibition forbids tuning constants to force ordering). |
</phase_requirements>

## Summary

This phase is pure local scientific data processing: parse four ~265MB Wyko ASCII height maps, detrend, extract a half-max width per 0.2mm position, mask invalid positions, smooth boundaries, persist, and QA-plot. The stack is already in `requirements.txt` (numpy/scipy/matplotlib); no new dependencies are needed. The existing `load_wyko_asc()` and `robust_plane_detrend()` are sound and should be reused unchanged per D-13.

I ran the locked contract rules against the actual raw data in this session (all 4 tracks, full resolution). Three findings materially change how the planner must structure this phase: **(1)** at native ~4µm column resolution, 37–56% of all pixels are "Bad" and effectively **100% of native x-columns on every track** violate the D-06 ≤10-consecutive-NaN rule — the contract only works if "column" means the 0.2mm-binned median cross-section profile (which yields 288–374 valid bins of 400 per track); **(2)** `scipy.signal.savgol_filter` is **not** NaN-aware (verified on scipy 1.18.0: 1 input NaN → 5 output NaNs), so D-08/D-11 require a small hand-rolled windowed-polyfit smoother — there is no standard library function for masked SG; **(3)** the roadmap's width-ordering success gate 400W(8) > 350W(10) is **empirically at risk** — my probe measured track 10 *wider* than track 8 (median 0.838 vs 0.790mm, mean 0.940 vs 0.859mm), partly driven by 117/288 track-10 bins whose half-max region touches the y-window boundary. Track 10, not track 21, is the biggest extraction-quality risk.

**Primary recommendation:** Build `src/targets.py` as a bin-first pipeline (aggregate ~50 native columns per 0.2mm slot via `nanmedian`, then apply gap rule + half-max edges + NaN-aware SG on the binned profile), persist one `.npz` per track, and structure QA so the ordering-gate outcome is *investigated and documented* rather than assumed — with an explicit checkpoint if 8/10 ordering fails.

## Critical Empirical Findings (verified this session against raw data)

All numbers below come from running the locked D-01–D-16 rules (faithfully reimplemented) against the four real `.ASC` files at full resolution. `[VERIFIED: direct execution on data/raw/height_maps/*.ASC]`

### Finding 1 — The per-native-column gap rule invalidates ~100% of columns on ALL tracks; bin-first rescues it

| Track | Bad-pixel fraction (cropped, detrended) | Native columns with NaN run >10 | Valid 0.2mm bins (binned-profile rule) |
|-------|------|------|------|
| 8 (400W) | 36.9% | **99.97%** | 374/400 |
| 10 (350W) | 51.6% | **100.00%** | 288/400 |
| 14 (300W) | 51.1% | **100.00%** | 314/400 |
| 21 (200W) | 55.6% | **99.99%** | 360/400 |

- "Bad" pixels are pervasive on every track, not a track-21 quirk. Median max-NaN-run per native column is 38–57 pixels (0.15–0.23mm) — far above the 10-pixel limit. Applying D-05/D-06 literally per native column triggers the SPEC's all-invalid hard error **on all four tracks**.
- NaNs concentrate **off-track**: bad fraction by y-band is 0.64–0.81 in the outer substrate bands vs 0.04–0.13 in the central on-track bands (track 21 central: 0.13–0.28 — its "less complete coverage" is on-track, consistent with the README warning). The rough unpolished substrate defeats white-light interferometry; the bead itself measures well. This is the *inverse* of what the contract discussion implicitly assumed.
- **Fix that preserves the contract's spirit:** aggregate first. Each 0.2mm output slot spans ~50 native columns (pixel size 0.003982mm). Taking `np.nanmedian` across the bin's columns at each y produces a nearly complete profile (median NaN fraction 0.2–3.7% per binned profile), and then D-05 (interpolate runs ≤10) / D-06 (invalidate runs >10) applied to the **binned profile** give the valid-bin counts above. This is aggregation within the output resolution cell, not cross-column interpolation — no information moves further along x than the 0.2mm slot the output already represents. It must still be confirmed as a contract interpretation (see Open Questions #1) because D-05's wording says "within that single x-column."

### Finding 2 — `scipy.signal.savgol_filter` is NOT NaN-aware; a small custom smoother is required

`[VERIFIED: executed on scipy 1.18.0]` One NaN in the input produces `window_length` NaNs in the output (tested: 1 NaN in, 5 NaNs out with `window_length=5, mode='interp'`). There is no scipy option for masked/NaN-skipping SG. D-08 ("NaN-aware SG") + D-11 ("skip invalid positions, don't interpolate through them first") therefore require a hand-rolled equivalent: for each output position, gather the ≤5-point window, drop NaN entries, least-squares-fit a degree-2 polynomial to the valid points, evaluate at the center (this *is* Savitzky-Golay generalized to missing samples — SG is exactly windowed polynomial least squares). ~20 lines of numpy; see Code Examples. Near the 20/100mm crop edges the window truncates naturally (shrinking one-sided window), satisfying D-12 without `savgol_filter`'s `mode=` parameter at all — resolving the second discretion item: **the discretion question "which scipy `mode`" dissolves, because scipy's function cannot be used directly**. Constraint verified: scipy raises `ValueError: polyorder must be less than window_length` — with a 5-point window, polyorder must be ≤4; recommend polyorder 2 (a cubic on 5 points with missing samples is under-determined too often).

### Finding 3 — The width-ordering gate (8 > 10 > 14 > 21) is empirically at risk

Probe widths using the locked rules (bin-first, p5/p95 baseline/peak, 0.5 fraction, largest contiguous above-threshold run):

| Track | Median width (mm) | Mean (mm) | 10%-trimmed mean (mm) | Bins where half-max run touches y-boundary |
|-------|------|------|------|------|
| 8 (400W) | 0.790 | 0.859 | 0.830 | 26 |
| 10 (350W) | **0.838** | **0.940** | **0.939** | **117 / 288** |
| 14 (300W) | 0.593 | 0.677 | 0.644 | 13 |
| 21 (200W) | 0.585 | 0.623 | 0.594 | 39 |

- Track 10 measures *wider* than track 8 on every summary statistic in this probe — the expected ordering fails at the 8/10 pair, and 14/21 are nearly tied (0.593 vs 0.585 median).
- A likely contributor: the measured y-window is only **1.907mm** wide (480 px), and 41% of track 10's valid bins have their above-threshold region clipped at the y-boundary — the extractor is latching onto broad elevated regions that extend beyond the measured strip. Track 10 also has the worst mid-band coverage. A boundary-clip validity rule (mark bins invalid when the half-max run touches the first/last y-pixel) would likely change these numbers substantially — but per the SPEC prohibition, constants/rules **must not be tuned to force the ordering**. The plan must therefore (a) include the clip rule *a priori* as a physically-motivated validity criterion (the true edge is unmeasurable when it lies outside the strip), decided before looking at its effect on ordering, and (b) treat the ordering check as an *investigation with documented outcome*, including a human checkpoint if it still fails, rather than an assumed-pass gate.
- Bead heights are small: peak-baseline separation (p95−p5 of the binned profile) has median 11.8–18.5µm per track. These are shallow melt tracks, not tall powder beads — width extraction operates on a ~10–20µm-tall feature over a substrate whose own p95−p5 in off-track bands is 9.6–20.1µm (median). Signal and background magnitudes overlap; the extraction works because the bead is *localized* in y, not because it towers over the noise.

### Finding 4 — Grounding for the D-04 noise floor (Claude's discretion item 1)

- Instrument spec: Bruker ContourGT-K white-light interferometer, vertical resolution <1nm (PSI) / ~3nm Ra (VSI) — instrument noise is negligible here. `[ASSUMED — Bruker marketing specs from training knowledge; not load-bearing]` The *effective* noise floor is substrate roughness + detrend residual, which I measured directly:
  - Per-binned-profile substrate (bottom-30% of values) std: **1.8–2.1µm** across tracks. `[VERIFIED: direct execution]`
  - Null statistic (the exact D-04 quantity — p95−p5 — computed on off-track-only y-bands per bin): median 9.6–20.1µm, p99 21–35µm. `[VERIFIED: direct execution]`
- **Implication:** a threshold that rejects the off-track null distribution (e.g. ≥25µm) would also reject most *real* on-track profiles (on-track separations median 11.8–18.5µm, track 21 p5 = 5.4µm). D-04's check can only be a **degenerate-profile floor**, not a strong signal/noise discriminator.
- **Recommendation:** `MIN_PEAK_BASELINE_SEPARATION_MM = 0.005` (5µm ≈ 2.5× the 2µm binned-profile substrate std; also ≈1.5× the 3.29σ p95−p5 of pure ~1µm-σ noise). At 5µm, ~5% of track 21's otherwise-valid bins fall below (its p5 separation is 5.35µm); at 8µm it would cut ≥5% of track 21 and start biting track 14. Set it at 5µm, document the grounding, and do not revisit after seeing QA output (prohibition). The real validity work is done by the gap rule, crossed-boundary rule, and (recommended) clip rule.

### Finding 5 — Per-track x-coverage differs; the fixed grid handles it

Cropped x-coverage start: track 10 = 20.00mm, track 8 = 20.26mm, track 21 = 20.73mm, track 14 = **21.46mm** (all end at 100.00mm). `[VERIFIED: direct execution]` With the fixed shared grid (D-07), tracks 8/14/21 will have leading grid slots permanently invalid (no data exists there) — this is expected behavior, not a bug; QA plots should annotate it so it isn't mistaken for extraction failure. All 4 `.ASC` headers parse cleanly (`X Size`, `Y Size`, `Pixel_size 0.003982` present in every file) — Pitfall 10's silent pixel-size fallback does **not** trigger on current files. `[VERIFIED: header inspection of all 4 files]`

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| ASC parsing, detrending | Library (`src/nsf_fmrg_data.py`) | — | Already exists; reuse per D-13/CONTEXT |
| Width extraction, gap handling, smoothing, mask | Library (new `src/targets.py`) | — | Pure functions over arrays, importable by Phase 2 |
| Batch run over 4 tracks + persistence + QA figures | Script (`scripts/run_target_extraction.py`) | — | Matches existing `scripts/run_thermal_video_export.py` CLI pattern |
| Persisted artifacts | `processed_data/targets/` | — | SPEC-mandated location; consumed by Phase 2 |
| Raw-data write-prohibition check | Script (pre/post checksum) | — | SPEC acceptance criterion, mechanically verifiable |

(Single-machine, single-process scientific pipeline — no client/server/DB tiers exist.)

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | 2.5.1 | arrays, percentiles, polyfit, NaN handling, `.npz` persistence | already a project dep; verified installs & runs on this machine |
| scipy | 1.18.0 | (only if needed) `savgol_filter` reference; `scipy.io` already used elsewhere | already a project dep — note savgol cannot be used directly (Finding 2) |
| matplotlib | 3.11.1 | QA overlay plots, residual maps | already a project dep |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pandas | 3.0.3 | fast `.ASC` body parsing (`read_csv` with `na_values=['Bad']`) | optional speedup: parses a 268MB file in ~15s vs the pure-Python line loop; already a project dep. Fine to keep `load_wyko_asc` per CONTEXT — it is canonical — but QA iteration is faster with an in-memory cache of the loaded/detrended arrays |

All versions above were installed from PyPI and executed successfully in this session on this machine. `[VERIFIED: PyPI install + execution]`

**Installation:**
```bash
uv venv .venv && uv pip install -p .venv/bin/python -r requirements.txt
```

**No new packages are introduced by this phase.** Persistence should use `np.savez` (`.npz`) — zero new deps, float64 arrays, loads with one call in Phase 2.

## Package Legitimacy Audit

No *new* packages are recommended — every library above is already listed in the project's `requirements.txt` and is a top-100 PyPI package with 10+ year history. All five installed cleanly from PyPI in this session (numpy 2.5.1, scipy 1.18.0, pandas 3.0.3, matplotlib 3.11.1, pillow 12.3.0).

| Package | Registry | Age | Source Repo | Verdict | Disposition |
|---------|----------|-----|-------------|---------|-------------|
| numpy | PyPI | 15+ yrs | github.com/numpy/numpy | OK | Approved (existing dep) |
| scipy | PyPI | 15+ yrs | github.com/scipy/scipy | OK | Approved (existing dep) |
| matplotlib | PyPI | 15+ yrs | github.com/matplotlib/matplotlib | OK | Approved (existing dep) |
| pandas | PyPI | 15+ yrs | github.com/pandas-dev/pandas | OK | Approved (existing dep) |
| pillow | PyPI | 10+ yrs | github.com/python-pillow/Pillow | OK | Approved (existing dep, unused this phase) |

**Packages removed due to SLOP verdict:** none · **Flagged SUS:** none

## Architecture Patterns

### System Architecture Diagram

```
data/raw/height_maps/Heightmap_{id}.ASC   (READ-ONLY — prohibition-checked)
        │
        ▼
load_wyko_asc()  [existing, src/nsf_fmrg_data.py:160-202]
  → Z_mm (480 × ~20k, float32, NaN='Bad'), x_actual_mm (20–100mm), y_mm (0–1.907mm)
        │
        ▼
robust_plane_detrend()  [existing, :205-227, D-13/D-15/D-16 unchanged]
  → Zd  ──────────────────────────────► QA: residual map figure ×4 tracks (D-14)
        │
        ▼
bin_to_grid()  [NEW]  x_grid = 20.1 + 0.2·k, k=0..399 (matches thermal centers)
  per slot: nanmedian across the slot's ~50 native columns → binned profile (480,)
        │
        ▼
gap_rule()  [NEW, D-05/D-06 on binned profile]
  interior NaN runs ≤ MAX_GAP_PIXELS(10) → linear interp along y
  any run > 10 (incl. leading/trailing) → slot invalid
        │
        ▼
halfmax_edges()  [NEW, D-01..D-04]
  base=p5, peak=p95, thr=base+0.5·(peak−base)
  validity: (peak−base) ≥ MIN_SEP · y_upper>y_lower · run not clipped at y-boundary
  → y_upper_raw(x), y_lower_raw(x), valid_mask(x)
        │
        ▼
nan_savgol()  [NEW, D-08..D-12 — hand-rolled windowed polyfit, Finding 2]
  smooth y_upper, y_lower separately over valid slots; invalid slots stay NaN
        │
        ▼
w(x) = y_upper_s(x) − y_lower_s(x)
        │
        ├──► processed_data/targets/track_{id}_targets.npz  (float64)
        │      keys: x_grid_mm, w_mm, y_upper_mm, y_lower_mm, valid_mask (+ params provenance)
        └──► processed_data/targets/qa/track_{id}_*.png
               overlay on raw + detrended maps, incl. track-21 gap regions
```

### Recommended Project Structure
```
src/
├── nsf_fmrg_data.py          # existing — unchanged
└── targets.py                # NEW: constants + pure extraction functions, dict-return convention
scripts/
└── run_target_extraction.py  # NEW: CLI (argparse --project_dir), runs all 4 tracks, writes npz + QA pngs,
                              #      prints summary table, runs raw-data checksum prohibition check
processed_data/
└── targets/
    ├── track_8_targets.npz … track_21_targets.npz
    ├── extraction_params.json          # single shared parameterization, written once
    └── qa/                             # residual maps, overlays, width curves
```

### Pattern 1: Shared 0.2mm grid = thermal frame centers
**What:** Fix `x_grid = 20.1 + 0.2*np.arange(400)` (centers 20.1 … 99.9mm).
**When to use:** This exactly matches `extract_final_thermal_frames`'s `x_mm_center` formula (`100 − (n−0.5)·0.2` → 20.1…99.9, 400 frames) `[VERIFIED: src/nsf_fmrg_data.py:123]`. Phase 2 then pairs thermal frame *k* with target slot *k* by construction — no interpolation needed downstream. Bin edges: `[xc−0.1, xc+0.1)`.

### Pattern 2: One module-level parameterization, persisted as provenance
**What:** All contract constants as SCREAMING_SNAKE_CASE module constants in `src/targets.py`, e.g.:
```python
TARGET_GRID_START_MM = 20.1
TARGET_GRID_STEP_MM = 0.2
TARGET_GRID_N = 400
BASELINE_PCT, PEAK_PCT = 5.0, 95.0
HALF_MAX_FRACTION = 0.5
MIN_PEAK_BASELINE_SEPARATION_MM = 0.005
MAX_GAP_PIXELS = 10
SG_WINDOW_PTS = 5          # ≈1mm at 0.2mm spacing
SG_POLYORDER = 2
MIN_VALID_Y_POINTS = 50    # minimum finite samples for percentile estimation
```
**Why:** TARGET-02 acceptance requires code inspection to confirm one shared parameterization — a single constants block with zero per-track branches makes that inspection trivial. Writing the same dict to `extraction_params.json` gives the artifact provenance.

### Pattern 3: Dict-return convention (existing codebase style)
Extraction entry point returns `{'track_id', 'x_grid_mm', 'w_mm', 'y_upper_mm', 'y_lower_mm', 'valid_mask', 'file'}` — mirrors `load_wyko_asc` / `extract_final_thermal_frames` returns. No classes, no type hints in library code, no docstrings (per codebase convention in CLAUDE.md).

### Anti-Patterns to Avoid
- **Per-native-column extraction:** invalidates ~100% of columns (Finding 1). Bin first.
- **`scipy.signal.savgol_filter` on masked data:** silently NaN-poisons 5 slots per gap (Finding 2).
- **Tuning any constant after viewing width ordering/QA output:** explicit SPEC prohibition; constants are locked from measured substrate statistics *before* the ordering is inspected.
- **Interpolating leading/trailing NaN runs in a profile:** linear interpolation is undefined without both anchors; count boundary runs toward the >10 invalidation rule instead of extrapolating.
- **`float32` persistence:** SPEC mandates float64. Note the SPEC's rationale ("matching `load_wyko_asc()`'s existing output precision") is factually off — the loader allocates `np.float32` (`src/nsf_fmrg_data.py:167`); cast up at persistence time. Precision impact is negligible (float32 eps at ~1mm ≈ 0.06nm), but the SPEC constraint stands.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ASC parsing / crop / reorientation | new parser | `load_wyko_asc()` | canonical per CONTEXT; verified working on all 4 files |
| Plane detrending | new fit | `robust_plane_detrend()` | locked D-13 |
| Percentiles, NaN stats, linear interp | custom loops | `np.percentile`, `np.interp`, `np.isfinite` | numpy default percentile method is `linear`, matching the SPEC precision edge `[VERIFIED]` |
| Run-length detection of NaN gaps | new logic | adapt `largest_true_run()` pattern (`src/nsf_fmrg_data.py:88-97`) | identical problem already solved in-repo |
| Persistence format | HDF5/parquet/custom | `np.savez` | zero deps, float64, one-call load |

**Justified exception — NaN-aware Savitzky-Golay:** no standard library provides masked SG (verified: scipy has no option; the handful of PyPI packages claiming it are obscure/low-download and would fail a legitimacy gate). Hand-roll the ~20-line windowed-polyfit version (Code Examples). SG *is* windowed polynomial least squares, so fitting only the valid points in each window is the mathematically correct generalization, and it satisfies D-11 (skip invalid slots) and D-12 (window truncates at crop edges) by construction.

## Common Pitfalls

### Pitfall 1: All-invalid hard error fires on every track if the gap rule is applied per native column
**What goes wrong:** SPEC's empty-track hard error triggers for all 4 tracks; phase cannot proceed.
**Why:** 37–56% Bad pixels; median max-NaN-run 38–57 px per native column (Finding 1).
**How to avoid:** Bin-first pipeline; apply D-05/D-06 to the 0.2mm binned median profile.
**Warning signs:** valid-bin count of 0, or valid fraction below ~70% on tracks 8/21.

### Pitfall 2: Track 10 (not 21) produces the worst extraction quality
**What goes wrong:** Planner focuses QA scrutiny on track 21 (per roadmap framing) while track 10 has the fewest valid bins (288/400), the worst mid-band coverage, 41% boundary-clipped half-max runs, and breaks the expected width ordering.
**How to avoid:** QA plots and the ordering investigation must treat track 10 as a first-class suspect; include the y-boundary-clip validity rule from the start (decided a priori, documented as such).
**Warning signs:** track 10 widths near the 1.9mm y-window extent; bimodal width distribution on track 10.

### Pitfall 3: Silent NaN poisoning in smoothing
**What goes wrong:** using `scipy.signal.savgol_filter` (or any convolution) spreads each masked slot into its neighbors — up to 5× more NaN slots than the mask, violating D-07's fixed-grid completeness expectations for Phase 2.
**How to avoid:** NaN-aware windowed polyfit; assert `isfinite(smoothed) == valid_mask` after smoothing (positions valid in → finite out, invalid in → NaN out).

### Pitfall 4: Leading/trailing gaps and missing x-coverage misread as bugs
**What goes wrong:** track 14 has no data below x=21.46mm; leading grid slots are invalid forever. Leading/trailing NaN runs within a profile can't be linearly interpolated.
**How to avoid:** Treat boundary runs as invalidating when >10 px (or unfillable otherwise); annotate per-track coverage start in QA figures (Finding 5).

### Pitfall 5: Outcome-contaminated constants
**What goes wrong:** adjusting `MIN_SEP`, `MAX_GAP_PIXELS`, or adding the clip rule *after* seeing that ordering fails — violates the SPEC prohibition and undermines the contract's defensibility for the competition report.
**How to avoid:** the plan should commit all constants + validity rules (including the clip rule) in an early task, with grounding written down (this document), *before* the task that computes per-track width summaries.

## Code Examples

Patterns below were executed against the real data in this session (adapted from the verified probe).

### NaN-aware Savitzky-Golay (windowed polyfit)
```python
# Source: hand-rolled; SG == windowed poly least squares. Verified pattern this session.
def nan_savgol(v, window=5, polyorder=2, min_pts=3):
    n = len(v)
    out = np.full(n, np.nan)
    half = window // 2
    for i in range(n):
        if not np.isfinite(v[i]):
            continue                      # D-11: invalid slots stay NaN
        lo, hi = max(0, i - half), min(n, i + half + 1)   # D-12: truncates at edges
        w = v[lo:hi]
        t = np.arange(lo, hi) - i
        m = np.isfinite(w)
        if m.sum() < min_pts:
            out[i] = v[i]                 # too few neighbors: pass through unsmoothed
            continue
        coef = np.polyfit(t[m], w[m], min(polyorder, m.sum() - 1))
        out[i] = np.polyval(coef, 0.0)
    return out
```

### Binning + gap rule + half-max edges (verified core)
```python
# Source: probe executed on all 4 tracks this session
def extract_bin_profile(Zd, x, xc, step=0.2):
    m = (x >= xc - step / 2) & (x < xc + step / 2)
    if m.sum() < 10:
        return None                       # no native columns → slot invalid
    return np.nanmedian(Zd[:, m], axis=1) # (480,) binned median cross-section

# gap rule (on binned profile): reuse largest_true_run-style run detection;
# interior runs <=10 -> np.interp along y; any run >10 -> slot invalid

def halfmax_edges(prof, y_mm):
    v = np.isfinite(prof)
    base = np.percentile(prof[v], 5.0)
    peak = np.percentile(prof[v], 95.0)
    if peak - base < MIN_PEAK_BASELINE_SEPARATION_MM:
        return None                       # D-04 degenerate-profile floor
    thr = base + 0.5 * (peak - base)
    above = np.where(np.isfinite(prof), prof > thr, False)
    # largest contiguous run above threshold -> (start, stop)
    # validity: run must NOT touch y[0]/y[-1] (clip rule), and stop > start
```

### Raw-data prohibition check (SPEC acceptance)
```python
# Before pipeline: record {path: (st_mtime_ns, st_size)} for data/raw/**
# After pipeline: recompute and assert equality; print PASS/FAIL.
```

## State of the Art

Nothing fast-moving here — FWHM/half-max width extraction on line-scan profiles is decades-old metrology practice; the modern nuance is exactly what the contract already locks (relative thresholds, robust percentile baselines, masked-data smoothing). numpy 2.x note: default percentile `method='linear'` matches the SPEC's precision-edge assumption `[VERIFIED: numpy 2.5.1]`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Bruker ContourGT-K instrument vertical resolution is nm-scale (spec sheet from training knowledge) | Finding 4 | Low — recommendation rests on *measured* substrate stats (2µm std), not the instrument spec |
| A2 | Bin-median aggregation satisfies the *intent* of D-05's "never cross-column interpolation" | Finding 1 | High if user disagrees — but the alternative (literal per-column rule) provably yields zero output; needs explicit confirmation (Open Question 1) |
| A3 | Track-10 boundary-clipped runs reflect real off-strip elevation (not a detrend artifact) | Finding 3 | Medium — D-14 residual-map QA will show if residual bow explains it; investigation task should check |

## Open Questions

1. **Contract amendment: "column" → "0.2mm-binned profile" (D-05/D-06).**
   - What we know: literal per-native-column application yields ~0% valid columns on all 4 tracks; binned application yields 72–94% valid slots.
   - What's unclear: whether the user considers bin-median aggregation consistent with D-05's "never 2D/cross-column interpolation" wording.
   - Recommendation: planner adopts bin-first (aggregation ≠ interpolation; nothing crosses the 0.2mm output cell) and flags it for explicit user confirmation at the first checkpoint. The evidence table in Finding 1 should be shown.

2. **The width-ordering success criterion may fail between tracks 8 and 10.**
   - What we know: probe measures 10 > 8 on median/mean/trimmed-mean; 41% of track-10 bins are y-boundary-clipped, which the probe did *not* exclude.
   - What's unclear: whether the a-priori clip rule restores 8 > 10, or the physical ordering genuinely differs at these powers for *width* (organizer's "bigger melt pool" tip is about the thermal signature, not guaranteed post-solidification width monotonicity).
   - Recommendation: plan an explicit investigation + human checkpoint task: compute ordering with the locked rules; if 8/10 ordering fails, do **not** touch constants — document the finding, present QA evidence to the user, and decide (with the user) whether the roadmap gate is amended. This is a phase-gate risk the planner must schedule for, not a reason to change the extraction.

3. **Y-boundary clip rule (new validity criterion, not in D-01–D-16).**
   - What we know: half-max runs touching the 1.907mm y-window edge mean the true boundary is outside the measured strip (width unknowable); affects 26/117/13/39 bins on tracks 8/10/14/21.
   - Recommendation: include it as an a-priori validity rule alongside D-04's crossed-boundary rule; get user sign-off in the same confirmation as Question 1, *before* any ordering numbers are shown.

4. **Bin aggregation minimums.** How many native columns (of ~50) and finite y-samples must a slot have? Recommendation: slot invalid if <10 native columns in bin or <50 finite samples in the binned profile (both matched the probe). Planner discretion; document as constants.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | everything | ✓ | 3.12.3 (system) | — |
| numpy/scipy/matplotlib/pandas | extraction + QA | ✗ (not installed in system Python) | — | **Wave 0: create venv** — verified `uv` installs all of them fine |
| uv | env creation | ✓ | /snap/bin/uv | `python3 -m venv` + pip |
| Raw height maps (4 × `.ASC`) | extraction | ✓ | all 4 present, headers parse | — (blocking if absent) |
| ffmpeg | — | not needed this phase | — | — |
| Disk for outputs | persistence | ✓ | `.npz` outputs are ~tens of KB | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** scientific packages — resolved by a Wave 0 environment-setup task (`uv venv` + `uv pip install -r requirements.txt`); all five packages verified installing and importing on this machine this session.

**Runtime note:** full-resolution load+detrend+extract of one track took ~40s in the probe (pandas parse ~15s of that; the repo's pure-Python `load_wyko_asc` loop will be slower, roughly 1–2min/track). A whole-pipeline run over 4 tracks is minutes, not hours — no caching architecture needed beyond the persisted outputs, but QA iteration will be pleasanter if the script caches loaded/detrended arrays in memory across the per-track loop.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | none exists; REQUIREMENTS.md explicitly excludes a "comprehensive test suite" from scope — use runnable assertion scripts instead of pytest |
| Config file | none — see Wave 0 |
| Quick run command | `.venv/bin/python scripts/check_targets.py` (asserts on persisted `.npz`, <10s) |
| Full suite command | `.venv/bin/python scripts/run_target_extraction.py --project_dir .` (full 4-track pipeline, ~5–10min) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TARGET-01 | Contract constants exist, single shared parameterization, no per-track branches | inspection + assert | `check_targets.py`: assert `extraction_params.json` written once and matches `src/targets.py` constants; grep for `track_id ==` branches in `src/targets.py` returns nothing | ❌ Wave 0 |
| TARGET-02a | 4 artifacts, correct keys/shapes/dtype/grid | assert | `check_targets.py`: each `.npz` has 5 keys, shape (400,), float64, `x_grid_mm[0]==20.1`, step 0.2, identical grid across tracks; `w = y_upper − y_lower` where valid; `isfinite(w) == valid_mask` | ❌ Wave 0 |
| TARGET-02b | width ordering 8>10>14>21 | assert (reported, not gating — see Open Q2) | `check_targets.py` prints per-track median/mean over valid slots + PASS/FLAG per pair | ❌ Wave 0 |
| TARGET-02c | QA plots sane | manual-only | human review of `processed_data/targets/qa/*.png` — justification: SPEC locked visual sign-off as the acceptance mode | — |
| TARGET-02 prohibition | no writes under `data/raw/` | assert | mtime/size snapshot before/after inside `run_target_extraction.py`, printed PASS/FAIL | ❌ Wave 0 |
| D-14 | residual maps show no bow | manual-only | human review of residual-map figures — justification: "obvious curvature" is a visual judgment per CONTEXT | — |

### Sampling Rate
- **Per task commit:** `.venv/bin/python scripts/check_targets.py` (once artifacts exist; earlier tasks: `python -c "import targets"` smoke import)
- **Per wave merge:** full extraction run on all 4 tracks
- **Phase gate:** full run + `check_targets.py` green + human visual sign-off of QA figures before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] Environment: `uv venv .venv && uv pip install -r requirements.txt` (no venv exists on this machine)
- [ ] `scripts/check_targets.py` — covers TARGET-01/TARGET-02 mechanical assertions above
- [ ] `processed_data/targets/` + `qa/` directories created by the run script (not committed as empty dirs)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | local single-user scientific pipeline; no auth surface |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | fail-fast on malformed `.ASC` (existing style: raise `ValueError` with message if header keys missing — do **not** silently accept the hardcoded pixel-size fallback; log loudly per PITFALLS Pitfall 10) |
| V6 Cryptography | no | none needed; mtime/size comparison suffices for the raw-data integrity check (threat model is accidental self-modification, not adversarial tampering) |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Accidental write/corruption of irreplaceable `data/raw/` | Tampering (accidental) | open raw files read-only; outputs restricted to `processed_data/targets/`; before/after snapshot assertion (SPEC-mandated) |
| Competition-restricted data leaking into git | Information disclosure | outputs are derived floats (fine to commit if desired), but never `git add` anything under `data/raw/`; `git log --all -- data/raw` stays empty (PITFALLS Pitfall 13) |
| Wrong-track file resolution via `find_track_file` substring fallback | Spoofing (identity confusion) | log resolved path per track; assert exactly the expected `Heightmap_{id}.ASC` filename (PITFALLS Pitfall 4 — a 5-line assert) |

## Project Constraints (from CLAUDE.md)

- Follow existing conventions: snake_case verb-first function names, SCREAMING_SNAKE_CASE unit-suffixed constants (`_MM`), matrix vars in math notation (`Z_yx`), **no type hints in library code** (hints only on script entry-point signatures), **no docstrings**, sparse comments only for non-obvious intent.
- CLI feedback via `print()` only — do not introduce `logging`.
- `src/` is not a package: new script uses the existing `sys.path.append(REPO_ROOT / "src")` pattern (`scripts/run_thermal_video_export.py:7-10`).
- Fail-fast with built-in exceptions and explicit messages; no custom exception classes.
- Dict-return convention for loader/extractor results.
- GSD workflow enforcement: all edits flow through planned phase execution.

## Sources

### Primary (HIGH confidence)
- Direct execution against `data/raw/height_maps/Heightmap_{8,10,14,21}.ASC` (full resolution, all 4 tracks) — NaN statistics, gap-run distributions, binned-profile validity counts, width summaries, null separations, substrate noise, per-track x-coverage
- Direct execution of scipy 1.18.0 (`savgol_filter` NaN behavior, polyorder constraint) and numpy 2.5.1 (percentile default method) on this machine
- `src/nsf_fmrg_data.py` — loader/detrend code inspection (incl. float32 allocation at :167, thermal center formula at :123)
- `README.md` §Task/alignment/evaluation, §Bruker/Wyko height maps, ground-truth clarification — organizer-authoritative
- `.planning/phases/01-target-extraction-contract/01-CONTEXT.md`, `01-SPEC.md`, `.planning/REQUIREMENTS.md`, `.planning/research/PITFALLS.md`

### Secondary (MEDIUM confidence)
- PyPI registry (via successful `uv pip install` of all five packages)

### Tertiary (LOW confidence)
- Bruker ContourGT-K vertical-resolution spec (training knowledge, tagged `[ASSUMED]`, not load-bearing)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all existing deps, installed and executed this session
- Architecture: HIGH — pipeline shape executed end-to-end (probe) on real data; grid formula verified against thermal extraction code
- Pitfalls: HIGH for Findings 1–5 (empirically measured); MEDIUM for the interpretation of *why* track 10 misbehaves (residual-map QA will confirm)
- Noise-floor recommendation: MEDIUM-HIGH — grounded in measured substrate statistics, but a judgment call between 5µm and 8µm with a documented track-21 sensitivity

**Research date:** 2026-07-19
**Valid until:** end of competition (2026-07-27) — data is frozen; findings do not go stale
