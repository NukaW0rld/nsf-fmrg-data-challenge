---
phase: 01-target-extraction-contract
plan: 09
subsystem: data-processing
tags: [detrend, provenance, file-resolution, security-hardening, numpy]

requires:
  - phase: 01-target-extraction-contract
    provides: Amendment A4's bead-mask detrend fix (bead_exclusion_mask) and complete extraction_params() provenance (plan 01-07); the diagnostic sweep tool itself (plan 01-06)
provides:
  - "scripts/diagnose_width_regression.py sweeps a bead-mask axis (BEAD_MASK_OPTIONS) that calls targets.bead_exclusion_mask and passes it as fit_mask, so it exercises the same production detrend path src/targets.py ships (WR-03 closed)"
  - "The sweep's evidence CSV writes to processed_data/diagnostics/, a sibling of processed_data/targets/ that publish_staging_dir cannot rename-and-rmtree, and outside the /processed_data/targets/ .gitignore entry"
  - "find_track_file's anchored delimiter regex is the sole candidate filter — the permissive bare-substring fallback is removed (WR-01 closed)"
  - "extract_final_thermal_frames and get_sem_tile_paths fail fast (ValueError) on an unresolved or mis-resolved track source, matching the existing height-map guard (WR-02 closed)"
affects: [target-extraction, phase-2-thermal-alignment, diagnostic-tooling]

tech-stack:
  added: []
  patterns: [production-faithful diagnostic sweeps (mirror the shipped fit_mask call shape), exact-basename fail-fast guards on every modality loader, diagnostic evidence written outside any tree a publish step destroys]

key-files:
  created: []
  modified:
    - scripts/diagnose_width_regression.py
    - src/nsf_fmrg_data.py
    - tests/test_nsf_fmrg_data.py

key-decisions:
  - "Restructured the sweep's detrend cache to iterate (order, bead_mask) and load each track's height map once per pair, keeping the existing CONTINUITY_OPTIONS loop nested inside — row count becomes 3 orders x 2 bead_mask x 2 continuity = 12."
  - "Relocated the sweep's output directory from processed_data/targets/diagnostics/ to processed_data/diagnostics/ (a sibling of targets/, not a child) so run_target_extraction.py's publish_staging_dir rename-and-rmtree cycle can never destroy the recorded evidence."
  - "Removed find_track_file's `or f'{track_id}' in name` fallback entirely rather than tightening the regex further — the anchored regex alone was already correct; the fallback was pure dead-weight risk."
  - "Mirrored src/targets.py's existing exact-name-guard shape (ValueError with 'Expected X, resolved Y' wording) for the new thermal-loader guard, rather than inventing a new error convention."
  - "get_sem_tile_paths checks is_symlink() on both the resolved PlainImages directory and its SEM_{track_id} parent, lexically, before any iterdir() call — a symlinked directory is rejected rather than read."

patterns-established:
  - "Diagnostic tooling must call the exact same production function signature (including fit_mask/masking arguments) that the pipeline it diagnoses uses, with unmasked/historical variants explicitly labeled as such in code comments."
  - "Every filesystem modality loader (thermal, SEM, height-map) now shares one guard shape: raise ValueError on no-match, raise ValueError on a resolved-but-mismatched exact basename, before any parsing is attempted."

requirements-completed: [TARGET-02]

coverage:
  - id: D1
    description: "scripts/diagnose_width_regression.py sweeps a bead-mask axis (BEAD_MASK_OPTIONS = (True, False)) that calls targets.bead_exclusion_mask and passes it as fit_mask into robust_plane_detrend, so the sweep exercises the production detrend path instead of the pre-Amendment-A4 unmasked baseline."
    requirement: TARGET-02
    verification:
      - kind: unit
        ref: "inline assertion: build_row(4, True, True, {...}) contains bead_mask=True; BEAD_MASK_OPTIONS == {True, False}; bead_exclusion_mask imported into the sweep module -> prints SWEEP MASK AXIS OK"
        status: pass
      - kind: other
        ref: ".venv/bin/python -m py_compile scripts/diagnose_width_regression.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "The sweep's evidence CSV is written to processed_data/diagnostics/, a sibling of processed_data/targets/, so publish_staging_dir's rename-and-rmtree cycle cannot destroy it, and it falls outside the /processed_data/targets/ .gitignore entry."
    requirement: TARGET-02
    verification:
      - kind: other
        ref: "grep -n processed_data scripts/diagnose_width_regression.py shows processed_data/diagnostics with no targets component"
        status: pass
      - kind: other
        ref: "inline check: Path('processed_data/diagnostics').resolve().is_relative_to(Path('processed_data/targets').resolve()) is False -> DIAGNOSTICS OUTSIDE PUBLISHED TREE"
        status: pass
    human_judgment: false
  - id: D3
    description: "find_track_file qualifies a candidate only when the track id appears as a delimiter-anchored token; a bare substring occurrence (e.g. '10' inside '210') no longer qualifies it, and all four real tracks (8, 10, 14, 21) still resolve correctly."
    requirement: TARGET-02
    verification:
      - kind: unit
        ref: "tests/test_nsf_fmrg_data.py::test_find_track_file_rejects_unanchored_substring_match"
        status: pass
      - kind: unit
        ref: "tests/test_nsf_fmrg_data.py::test_find_track_file_still_resolves_real_dataset_names"
        status: pass
      - kind: other
        ref: "real-dataset one-liner over data/raw/height_maps for tracks 8,10,14,21 -> Heightmap_{id}.ASC each"
        status: pass
    human_judgment: false
  - id: D4
    description: "load_wyko_asc, extract_final_thermal_frames, and get_sem_tile_paths all raise ValueError (not TypeError/FileNotFoundError) on an unresolved or mis-resolved track source, matching the height-map guard extract_track_targets already applies."
    requirement: TARGET-02
    verification:
      - kind: unit
        ref: "tests/test_nsf_fmrg_data.py::test_height_map_loader_raises_value_error_when_unresolved"
        status: pass
      - kind: unit
        ref: "tests/test_nsf_fmrg_data.py::test_thermal_loader_rejects_unresolved_or_mismatched_filename"
        status: pass
      - kind: unit
        ref: "tests/test_nsf_fmrg_data.py::test_sem_tile_paths_rejects_missing_or_symlinked_track_directory"
        status: pass
      - kind: other
        ref: "real-dataset one-liner: get_sem_tile_paths('data/raw/sem', 8) -> 13 tiles resolved"
        status: pass
    human_judgment: false
  - id: D5
    description: "No extraction constant changed, no per-track branch introduced, no gate weakened, and data/raw/ untouched by this plan."
    requirement: TARGET-02
    verification:
      - kind: other
        ref: "grep -n 'track_id ==' src/targets.py src/nsf_fmrg_data.py scripts/run_target_extraction.py -> no matches"
        status: pass
      - kind: other
        ref: "git status --porcelain data/raw -> empty"
        status: pass
      - kind: unit
        ref: "tests/test_targets.py (26/26 PASS), tests/test_run_target_extraction.py (7/7 PASS) unchanged and green"
        status: pass
    human_judgment: false

duration: 8min
completed: 2026-07-21
status: complete
---

# Phase 01 Plan 09: WR-01/WR-02/WR-03 Gap-Closure Summary

**Made the width-regression diagnostic sweep exercise the production bead-masked detrend path (not the pre-Amendment-A4 unmasked baseline), relocated its evidence CSV outside the tree the extraction publish step destroys, tightened `find_track_file` to the anchored regex alone, and gave the thermal and SEM loaders the same exact-basename fail-fast guard the height-map loader already had.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-07-21T16:15:00Z (approx.)
- **Completed:** 2026-07-21T16:22:30Z (approx.)
- **Tasks:** 3
- **Files modified:** 3 (`scripts/diagnose_width_regression.py`, `src/nsf_fmrg_data.py`, `tests/test_nsf_fmrg_data.py`)

## Accomplishments

- **WR-03 closed:** `scripts/diagnose_width_regression.py` now sweeps `BEAD_MASK_OPTIONS = (True, False)` alongside the existing `DETREND_ORDERS` and `CONTINUITY_OPTIONS` axes, calling `bead_exclusion_mask(data['Z_mm'])` and passing it as `fit_mask` into `robust_plane_detrend` — the exact call shape `extract_track_targets` uses in production. `build_row`, `print_sweep_table`, and `write_sweep_csv` all carry the new `bead_mask` column. The sweep's output directory moved from `processed_data/targets/diagnostics/` to `processed_data/diagnostics/` (a sibling of `targets/`), so `publish_staging_dir`'s rename-and-rmtree cycle can no longer silently destroy the recorded evidence, and the CSV now falls outside the `/processed_data/targets/` `.gitignore` entry. The redundant second `resolve_output_path` call (IN-02) was also removed.
- **WR-01 closed:** `find_track_file`'s permissive `or f'{track_id}' in name` substring fallback is removed; the delimiter-anchored regex is now the sole candidate filter. A directory containing only `Heightmap_210.ASC` no longer resolves for track 10. All four real tracks (8, 10, 14, 21) still resolve to their own `Heightmap_{id}.ASC` files, confirmed against the real dataset. `load_wyko_asc` now raises `ValueError` (not a downstream `TypeError`) when no file resolves.
- **WR-02 closed:** `extract_final_thermal_frames` raises `ValueError` when `find_track_file` resolves nothing, and again when the resolved basename is not exactly `Thermal_{track_id}.mat` — mirroring the existing height-map guard's wording and shape. `get_sem_tile_paths` raises `ValueError` when `SEM_{track_id}/PlainImages` is missing, and again when either that directory or its `SEM_{track_id}` parent is a symlink (checked lexically, before any `iterdir`), so a cross-track directory swap cannot silently pair the wrong track's tiles. Both loaders still resolve correctly against the real dataset (13 tiles for track 8's SEM directory).
- Added five new regressions to `tests/test_nsf_fmrg_data.py`, growing it from 5 to 10 registered tests, all passing under both `.venv/bin/python` and `.venv/bin/python -O`.
- Confirmed zero collateral regressions: `tests/test_targets.py` (26/26 PASS) and `tests/test_run_target_extraction.py` (7/7 PASS) unchanged and green; `grep -n "track_id =="` across `src/targets.py`, `src/nsf_fmrg_data.py`, `scripts/run_target_extraction.py` returns no matches (no per-track branching introduced); `git status --porcelain data/raw` empty throughout.

## Task Commits

Each task was committed atomically:

1. **Task 1: WR-03 — give the width-regression sweep a bead-mask axis so it exercises the production detrend path** - `064adad` (fix)
2. **Task 2: WR-01 — make find_track_file's anchored boundary regex actually load-bearing** - `b5c5b94` (fix)
3. **Task 3: WR-02 — extend the exact-resolution guard to the thermal and SEM loaders** - `68ed584` (fix)

**Plan metadata:** (this commit, docs: complete plan)

## Files Created/Modified

- `scripts/diagnose_width_regression.py` - Added `BEAD_MASK_OPTIONS`, imported `bead_exclusion_mask`, restructured `run_sweep`'s detrend cache to iterate `(order, bead_mask)`, added the `bead_mask` field/column to `build_row`/`print_sweep_table`/`write_sweep_csv`, removed the duplicate `resolve_output_path` call, and relocated the diagnostics output directory to `processed_data/diagnostics/`.
- `src/nsf_fmrg_data.py` - Removed `find_track_file`'s substring fallback; added `ValueError` guards to `load_wyko_asc` (no-match), `extract_final_thermal_frames` (no-match and mismatched basename), and `get_sem_tile_paths` (missing directory and symlink rejection).
- `tests/test_nsf_fmrg_data.py` - Added `test_find_track_file_rejects_unanchored_substring_match`, `test_find_track_file_still_resolves_real_dataset_names`, `test_height_map_loader_raises_value_error_when_unresolved`, `test_thermal_loader_rejects_unresolved_or_mismatched_filename`, `test_sem_tile_paths_rejects_missing_or_symlinked_track_directory`; all appended to the `__main__` runner list.

## Decisions Made

- Kept `robust_plane_detrend`'s existing `coef is None` degenerate handling unchanged inside the restructured sweep loop — no behavior change to the detrend function itself, only to how the sweep script calls it.
- Did not run the full sweep (`run_diagnostic`) as part of this plan; it reads all four real height maps at every configuration and takes several minutes. Verification exercised the new row/CSV schema directly via `build_row` and static assertions, per the plan's explicit instruction.
- Checked `is_symlink()` on the lexical path (not the resolved path) for the SEM directory guard, so a redirected directory is rejected before any read is attempted, per the plan's threat model (T-01-17).

## Deviations from Plan

None - plan executed exactly as written. All three tasks' `<action>` blocks were implemented as specified; every `<verify>` and `<acceptance_criteria>` command passed on the first attempt with no auto-fixes required.

## Issues Encountered

None.

## Known Stubs

None. All changes are complete, tested guard/regression logic — no placeholder or unwired code introduced.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- WR-01, WR-02, and WR-03 (the three code-review warnings blocking plan 01-11's track-10 diagnosis) are closed. Plan 01-11 can now diagnose track 10's valid-fraction collapse against a sweep tool that reflects the production bead-masked detrend path, and against loaders that fail fast on any mis-resolved track source.
- Phase 2 (which consumes `extract_final_thermal_frames` and `get_sem_tile_paths` directly) now inherits the same fail-fast guarantee the height-map loader already had — a silently mis-paired thermal cube or SEM tile set can no longer reach downstream alignment code undetected.
- The Phase 1 blocker recorded in STATE.md (8>10>14>21 ordering not restored, 10-vs-14 FLAG) remains open and unaffected by this plan; it is explicitly out of scope here and is the subject of the still-pending human-override-vs-diagnose decision and plan 01-11's track-10 diagnosis.

## Self-Check: PASSED

- `scripts/diagnose_width_regression.py`, `src/nsf_fmrg_data.py`, `tests/test_nsf_fmrg_data.py` all exist with the described changes.
- Commits `064adad`, `b5c5b94`, `68ed584` exist in `git log`.
- `tests/test_nsf_fmrg_data.py` reports 10/10 PASS under both `.venv/bin/python` and `.venv/bin/python -O`.
- `tests/test_targets.py` (26/26) and `tests/test_run_target_extraction.py` (7/7) remain green.
- `git status --porcelain data/raw` is empty.

---
*Phase: 01-target-extraction-contract*
*Completed: 2026-07-21*
