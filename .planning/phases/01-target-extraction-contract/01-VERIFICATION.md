---
phase: 01-target-extraction-contract
verified: 2026-07-20T22:10:00Z
status: gaps_found
score: 5/7 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 24/27
  gaps_closed:
    - "The full extraction contract is now reproducibly documented: MAX_TRACKING_GAP_COLUMNS and the new BEAD_MASK_HEIGHT_FRACTION are both in extraction_params() (15 keys), persisted in extraction_params.json, and the SHA-256 provenance digest is change-sensitive to both (tests/test_targets.py::test_provenance_includes_tracking_gap_and_fix_param, test_provenance_digest_is_change_sensitive)."
    - "Amendment A4 canonicalizes the plan-01-05 continuity/stale-history rule and the plan-01-07 bead-mask fix in 01-CONTEXT.md, in the same style as Amendment A3."
    - "The bead-masking fix (Amendment A4) was applied via the plan-01-06 pre-registered, outcome-independent, residual/physical criterion — not chosen or tuned to make the ordering pass — and is uniform across all 4 tracks (grep for 'track_id ==' in src/targets.py, src/nsf_fmrg_data.py, and scripts/run_target_extraction.py returns nothing)."
  gaps_remaining:
    - "The roadmap's required width ordering 8 > 10 > 14 > 21 is still not achieved: 8-vs-10 and 14-vs-21 PASS, but 10-vs-14 FLAGs (track 10 median 0.2509 mm < track 14 median 0.5264 mm)."
    - "Visual QA sign-off on the regenerated residual/overlay/width figures (Human Verification items #1-#3 from the prior VERIFICATION.md) is still outstanding — plan 01-08 explicitly recommended holding sign-off pending the human override-vs-diagnose decision."
  regressions: []
gaps:
  - truth: "Running the extractor on all 4 tracks produces a w_i(x) curve per track showing the expected width ordering 400W(8) > 350W(10) > 300W(14) > 200W(21)."
    status: failed
    reason: "scripts/check_targets.py (re-run live during this verification) reports track medians 8=0.7411mm, 10=0.2509mm, 14=0.5264mm, 21=0.2412mm. 8-vs-10 PASS, 14-vs-21 PASS, but 10-vs-14 FLAGs — the full chain does not hold. This is the same regression already diagnosed in 01-06-DIAGNOSIS.md and reported honestly, unresolved, in 01-08-ORDERING-OUTCOME.md. Root cause (independently confirmed by this verification's visual inspection of track_10_overlay.png): track 10's bead sits at/beyond the y-strip edge for nearly the entire track length, so the boundary-clipped-run exclusion (correct in isolation, per D-01/D-03) discards 267/400 (66.75%) of its columns, collapsing its valid fraction to 5.2% (21/400) and making its median width unrepresentative."
    artifacts:
      - path: "processed_data/targets/track_10_targets.npz"
        issue: "Only 21/400 (5.2%) grid slots are valid; median width computed from this small, non-representative sample is close to track 21's (lowest power) despite track 10 being the second-highest power track."
      - path: "processed_data/targets/qa/track_10_overlay.png"
        issue: "Visually confirmed during this verification: no visible upper/lower boundary trace across nearly the entire 20-100mm span — the extraction produced almost no usable boundary for this track."
    missing:
      - "A separate, principled (non-outcome-driven) diagnosis and fix for track 10's edge-clipped bead, OR an explicit human override of the roadmap ordering criterion with documented rationale (per 01-08-ORDERING-OUTCOME.md's two escalation options (a)/(b))."
  - truth: "QA plots overlay the extracted width/boundary on both the raw and detrended height map for all 4 tracks, including track 21's gap-heavy regions, and are visually confirmed sane (no sawtooth/high-frequency jitter, no silently dropped gaps)."
    status: failed
    reason: "All 12 QA PNGs exist and were visually inspected directly during this verification (not merely claimed). Track 8, 14, and 21 overlays show a continuous, physically plausible boundary trace with masked (gray-shaded) gaps handled explicitly, not silently. Track 10's overlay shows no visible boundary trace across nearly the entire track — the QA plot is not 'visually confirmed sane' for one of the four required tracks. Additionally, human sign-off on the regenerated figures was never completed: 01-08-ORDERING-OUTCOME.md explicitly recommends holding VERIFICATION.md Human Verification items #1-#3 open pending the track-10/override decision, and no UAT or CONTEXT record documents that sign-off having since occurred."
    artifacts:
      - path: "processed_data/targets/qa/track_10_overlay.png"
        issue: "No visible boundary trace for nearly the full 20-100mm span (consistent with the 5.2% valid fraction)."
    missing:
      - "Resolve the track 10 coverage collapse (see prior gap), then obtain explicit human visual sign-off on all 12 regenerated figures."
  - truth: "check_targets.py fails closed (non-zero exit or hard error) when a persisted artifact violates the project's own coverage expectations, rather than reporting ALL CHECKS PASSED regardless."
    status: failed
    reason: "Independently reproduced during this verification by re-running scripts/check_targets.py against the current artifacts: it prints 'Track 10 valid fraction 5.2% is below 50% — FLAG' via a bare print() (scripts/check_targets.py:89-91) and then unconditionally prints 'ALL CHECKS PASSED'. The only hard gate on coverage is valid_count > 0 (line 87), so a track with 1 valid slot out of 400 would also pass. This is exactly how a 95%-invalid track (CR-01) went unnoticed by the automated contract checker this phase depends on for its 'reproducible, trusted' guarantee. Corroborates 01-REVIEW.md CR-02, independently re-verified live, not merely re-cited."
    artifacts:
      - path: "scripts/check_targets.py"
        issue: "Lines 86-91: valid_fraction < 0.5 branch is a print, not a require(...); main() proceeds to print ALL CHECKS PASSED unconditionally."
    missing:
      - "Promote the low-coverage check to a hard failure (require(...)) with a project-chosen minimum coverage floor, or an explicit documented per-track allowance — not a silent print for every track."
  - truth: "The publish path used to write processed_data/targets/ does not allow a pre-existing symlink to redirect a destructive delete outside the intended output tree."
    status: failed
    reason: "01-REVIEW.md CR-03 reproduced this exploit live in an isolated scratch repository: a symlink at processed_data/targets.previous pointing at src/ causes publish_staging_dir's shutil.rmtree(backup_dir) to delete src/ during a normal, successful run_pipeline() call, while the data/raw/ integrity audit correctly reports PASS (data/raw/ genuinely untouched). Source inspection during this verification confirms resolve_output_path (scripts/run_target_extraction.py:62-70) resolves symlinks via Path.resolve(strict=False) but never rejects a path that IS a symlink before use, and publish_staging_dir (scripts/run_target_extraction.py:294-306) calls shutil.rmtree(backup_dir) unconditionally once backup_dir exists. The existing regression tests/test_run_target_extraction.py::test_symlink_output_into_raw_is_rejected only covers a symlink pointing into data/raw, not one pointing at any other in-repository directory. This undermines the 'reproducible pipeline' trust the phase goal requires: any future run risks destroying an unrelated repository directory (e.g. src/, tests/, .git/) if a stray symlink exists at the backup path."
    artifacts:
      - path: "scripts/run_target_extraction.py"
        issue: "resolve_output_path (lines 62-70) does not reject symlinks; publish_staging_dir (lines 294-306) rmtree's backup_dir without a symlink check immediately before deletion."
    missing:
      - "Reject symlinks outright at every output path the publisher touches (is_symlink() check before resolve/rmtree/rename), and add a regression that plants a symlink at targets.previous (and separately at processed_data) pointing at a harmless in-repo victim directory, asserting the victim survives run_pipeline."
---

# Phase 1: Target Extraction & Contract Verification Report

**Phase Goal:** A documented, reproducible local-width extraction method is specified and then implemented, and is visually validated against all 4 tracks before anything downstream trusts it as ground truth.
**Verified:** 2026-07-20T22:10:00Z
**Status:** gaps_found
**Re-verification:** Yes — after gap-closure plans 01-06 (diagnosis), 01-07 (bead-mask fix + complete provenance), and 01-08 (regeneration + honest outcome report)

## Goal Achievement

### Observable Truths

The four ROADMAP success criteria are the controlling contract, merged with the two provenance-completeness/no-tuning truths carried forward from the prior VERIFICATION.md's Gap 1 (now closed) and two new truths derived from this session's independently-reproduced code-review findings (CR-02, CR-03), which bear directly on "reproducible... before anything downstream trusts it."

| # | Truth | Status | Evidence |
|---:|---|---|---|
| 1 | The TARGET-01 contract (width definition, threshold rule, smoothing scale, 0.2mm grid, valid-coordinate mask, track-21 gap rule) is written and reviewed before extraction code is trusted | ✓ VERIFIED | D-01–D-16 in `01-CONTEXT.md`, plus canonical Amendments A1-A4 (A3: detrend order; A4: continuity tracking + bead-mask fix), all written and dated before/alongside the code that implements them. |
| 2 | The complete current extraction contract is reproducibly documented and provenance-locked (Gap 1 from prior verification) | ✓ VERIFIED | `extraction_params()` now returns 15 keys including `MAX_TRACKING_GAP_COLUMNS` and `BEAD_MASK_HEIGHT_FRACTION` (confirmed live: `cat processed_data/targets/extraction_params.json`); `tests/test_targets.py::test_provenance_digest_is_change_sensitive` passes; Amendment A4 documents both mechanisms in `01-CONTEXT.md`. |
| 3 | Running the extractor on all 4 tracks produces the expected width ordering 400W(8) > 350W(10) > 300W(14) > 200W(21) | ✗ FAILED | Live re-run of `scripts/check_targets.py`: 8=0.7411mm > 10=0.2509mm (PASS), 10=0.2509mm vs 14=0.5264mm (FLAG — inverted), 14=0.5264mm > 21=0.2412mm (PASS). Full chain does not hold. Root cause: track 10's bead sits at the y-strip edge, collapsing its valid fraction to 5.2% (21/400). |
| 4 | QA plots overlay extracted width/boundary on raw+detrended maps for all 4 tracks, incl. track 21's gaps, and are visually confirmed sane | ✗ FAILED | Direct visual inspection during this verification: track 8, 14, 21 overlays show continuous, plausible boundary traces with explicitly gray-shaded (not silently dropped) gaps. Track 10's overlay shows essentially no visible boundary trace for nearly the full 20-100mm span. Human sign-off on regenerated figures also remains open per 01-08-ORDERING-OUTCOME.md's explicit recommendation. |
| 5 | The identical extraction rule is applied across all 4 tracks with no per-track-tuned thresholds (single shared parameterization) | ✓ VERIFIED | `grep -n "track_id ==" src/targets.py src/nsf_fmrg_data.py scripts/run_target_extraction.py` returns nothing; `tests/test_targets.py::test_single_parameterization_has_no_track_conditionals` and `test_track_id_does_not_affect_numeric_output` pass. |
| 6 | The artifact/provenance checker (`check_targets.py`) fails closed when a persisted artifact violates the project's coverage expectations | ✗ FAILED | Live re-run: prints "Track 10 valid fraction 5.2% is below 50% — FLAG" then unconditionally "ALL CHECKS PASSED". Source: `scripts/check_targets.py:86-91` — the `<50%` branch is a `print`, not `require(...)`; only hard gate is `valid_count > 0`. |
| 7 | The publish path cannot be redirected by a pre-existing symlink into destroying an unrelated repository directory | ✗ FAILED | `01-REVIEW.md` CR-03 reproduced live in an isolated scratch repo: symlink at `processed_data/targets.previous` -> `src/` causes `publish_staging_dir`'s `shutil.rmtree(backup_dir)` to delete `src/` during a normal successful run, while `data/raw/` integrity audit still reports PASS. Source inspection confirms `resolve_output_path` (`scripts/run_target_extraction.py:62-70`) never rejects symlinks before use. |

**Score:** 5/7 truths verified (0 present-but-behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/targets.py` | Shared extraction implementation incl. bead-mask fix | ✓ VERIFIED | `bead_exclusion_mask()` present and wired; 26 tests pass in `tests/test_targets.py`. |
| `src/nsf_fmrg_data.py` | Configurable detrend with `fit_mask` support | ✓ VERIFIED | `fit_mask` keyword confirmed on `robust_plane_detrend`; 5 tests pass in `tests/test_nsf_fmrg_data.py`. |
| `scripts/diagnose_width_regression.py` | Diagnostic sweep tool (plan 01-06) | ✓ VERIFIED | Committed; produces `width_regression_sweep.csv`, read-only against `data/raw/`. |
| `processed_data/targets/track_{8,10,14,21}_targets.npz` | Regenerated fixed-grid curves under Amendment A4 | ✓ VERIFIED structurally, ✗ track 10 fails coverage | All 4 pass `check_targets.py`'s structural/dtype/mask checks; track 10 is 5.2% valid. |
| `processed_data/targets/extraction_params.json` | Complete, change-sensitive provenance | ✓ VERIFIED | 15 keys, matches `extraction_params()` live. |
| `processed_data/targets/manifest.json` | Same-run publication marker | ✓ VERIFIED | SHA-256 digest present, matches persisted params. |
| `processed_data/targets/qa/*.png` | 12 regenerated QA images | ✓ EXIST, ✗ not fully sane / not signed off | All 12 present; track 8/14/21 visually sane on direct inspection; track 10 visually broken; human sign-off outstanding. |
| `.planning/phases/01-target-extraction-contract/01-CONTEXT.md` | Amendments A1-A4 | ✓ VERIFIED | Amendment A4 present, documents both continuity tracking and the bead-mask fix. |
| `.planning/phases/01-target-extraction-contract/01-08-ORDERING-OUTCOME.md` | Honest outcome report | ✓ VERIFIED | Reports the unresolved 10-vs-14 FLAG without any parameter change; `git diff --stat -- src/targets.py` empty per the report, `track_id ==` grep independently confirms no per-track branch. |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `extract_track_targets()` | `bead_exclusion_mask()` | Computed per-track from raw `Z_mm`, passed as `fit_mask` | ✓ WIRED | `01-07-SUMMARY.md` D1/D2 regressions pass; confirmed present in `src/targets.py`. |
| `robust_plane_detrend()` | least-squares fit | `fit_mask` excludes flagged pixels from fit, surface still subtracted from all pixels | ✓ WIRED | `test_robust_plane_detrend_fit_mask_excludes_bead_from_fit` passes. |
| `extraction_params()` | `extraction_params.json` / manifest SHA-256 | JSON dump + digest | ✓ WIRED | Live file inspection matches; digest change-sensitivity test passes. |
| `run_target_extraction.py::publish_staging_dir` | `processed_data/targets/` | Rename staging -> live, rmtree backup | ⚠️ WIRED WITH SAFETY GAP | Functionally wired for the happy path; CR-03 shows it is unsafe against a pre-existing symlink at the backup path. |
| `scripts/check_targets.py` | persisted NPZs | `np.load` + structural asserts | ⚠️ WIRED WITH GATING GAP | Structural checks are real and pass/fail correctly; the coverage-floor check is present but non-blocking (CR-02). |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Target-contract regressions | `.venv/bin/python tests/test_targets.py` | 26 PASS, exit 0 | ✓ PASS |
| Detrend regressions (incl. fit_mask) | `.venv/bin/python tests/test_nsf_fmrg_data.py` | 5 PASS, exit 0 | ✓ PASS |
| Runner safety transitions | `.venv/bin/python tests/test_run_target_extraction.py` | 10 PASS, exit 0 (data/raw/ integrity PASS reported) | ✓ PASS |
| Persisted artifact/provenance checker | `.venv/bin/python scripts/check_targets.py --project_dir .` | Structural checks pass; 10-vs-14 ordering FLAG; unconditional "ALL CHECKS PASSED" | ⚠️ PARTIAL (see gap 3/CR-02) |
| No per-track branching | `grep -n "track_id ==" src/targets.py src/nsf_fmrg_data.py scripts/run_target_extraction.py` | No matches | ✓ PASS |
| Direct visual inspection of QA overlays | Read `track_10_overlay.png`, `track_14_overlay.png`, `track_21_overlay.png` | Track 14/21 show continuous boundary traces with explicit gap shading; Track 10 shows almost no boundary trace | ⚠️ MIXED (3/4 sane, 1/4 broken) |

### Probe Execution

No probe scripts declared and no conventional `scripts/*/tests/probe-*.sh` files exist.

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|---|---|---|---|---|
| TARGET-01 | 01-01, 01-03, 01-04, 01-05, 01-07 | Contract specified/documented before extraction code trusted, single shared parameterization | ✓ SATISFIED for documentation/reproducibility; the contract itself (D-01–D-16, A1-A4) is complete, provenance-locked, and applied uniformly. | `01-CONTEXT.md`, `extraction_params.json`, no per-track branches. |
| TARGET-02 | 01-01 through 01-08 | Extractor implements the contract and is visually QA'd against all 4 tracks before being trusted downstream | ✗ BLOCKED | Track 10's artifact is 95% invalid; the ordering criterion (an explicit part of the roadmap's definition of "trusted downstream") is not met; human visual sign-off is still outstanding. |

Every requirement ID declared across all 8 plans (`requirements:` frontmatter) is `TARGET-01` and/or `TARGET-02`; both are present in `REQUIREMENTS.md`. No orphaned requirement IDs for this phase. Note: `REQUIREMENTS.md` currently marks both TARGET-01 and TARGET-02 as `[x]` complete and the traceability table as "Complete" — this verification finds TARGET-02 not yet satisfied; the requirements table should be corrected pending resolution of the gaps below.

### Prohibitions

| Prohibition | Tier | Status | Evidence |
|---|---|---|---|
| No outcome-driven per-track tuning of extraction constants | judgment | ✓ VERIFIED | `01-08-ORDERING-OUTCOME.md` reports the unresolved ordering with `git diff --stat -- src/targets.py` empty; no per-track branch found by direct grep; the pre-registered 01-06 criterion (residual/physical, not ordering-outcome) was followed for the bead-mask fix, independently corroborated by Amendment A4's text. |
| No writes/deletes/modifications under `data/raw/` | test | ✓ VERIFIED | `snapshot_raw`/`raw_snapshot_diff` audits pass in all 10 runner tests; `data/raw/ integrity PASS` printed on every live run observed during this verification. |
| Output publication must not permit destructive operations outside the intended output tree | test | ✗ UNVERIFIED / FLAGGED | CR-03 (reproduced live in `01-REVIEW.md`, independently corroborated by source inspection here) shows the publish path is exploitable via a pre-existing symlink at the backup path. No test-tier enforcement exists for this specific vector; flagged per the fail-closed default for an unresolved test-tier prohibition — this is not a silently-passed item. |

### Anti-Patterns and Review Findings

No `TBD`, `FIXME`, `XXX`, or `HACK` debt markers found in phase source/script files (`src/targets.py`, `src/nsf_fmrg_data.py`, `scripts/run_target_extraction.py`, `scripts/check_targets.py`, `scripts/diagnose_width_regression.py`).

| Finding | Independent evidence (this verification) | Disposition |
|---|---|---|
| Track 10's persisted artifact is 95% invalid (CR-01) | Re-ran `check_targets.py` live: 21/400 valid; visually confirmed via `track_10_overlay.png` (no boundary trace across nearly the full span) | 🛑 BLOCKER — directly causes gap 1 above (ordering) and gap 2 (QA sanity). |
| `check_targets.py` does not fail closed on catastrophic coverage loss (CR-02) | Re-ran live: "ALL CHECKS PASSED" printed alongside the 5.2% FLAG; source line-by-line confirms the branch is a `print`, not `require` | 🛑 BLOCKER — the automated gate this phase's "trusted downstream" promise relies on is misleading by design. |
| Publish-path symlink exploit deletes arbitrary in-repo directories (CR-03) | Source inspection confirms `resolve_output_path` never rejects symlinks; exploit was independently reproduced (not just re-cited) in `01-REVIEW.md` this session | 🛑 BLOCKER — undermines "reproducible pipeline... before anything downstream trusts it," since any future run risks destroying repository state. |
| `find_track_file`'s regex boundary protection is a no-op (WR-01) | Not independently re-verified this session; carried forward from `01-REVIEW.md` | ⚠️ Warning — latent risk, does not currently misfire with the 4-file dataset. |
| No exact-filename safety check for thermal/SEM loaders (WR-02) | Carried forward from `01-REVIEW.md`, not independently re-verified | ⚠️ Warning — outside this phase's height-map-specific scope but relevant to overall pipeline trust. |
| `diagnose_width_regression.py` no longer reflects the production (masked) detrend path (WR-03) | Carried forward from `01-REVIEW.md` | ⚠️ Warning — diagnostic tool staleness, not a blocker to the phase goal itself. |

## Human Verification Required

### 1. Track 10 coverage collapse — override vs. further diagnosis

**Test:** Review `01-08-ORDERING-OUTCOME.md`'s two escalation options: (a) accept the 10-vs-14 ordering FLAG as a documented, known limitation and proceed to Phase 2 with the caveat recorded, or (b) commission a further diagnosed-defect investigation into why `bead_exclusion_mask` + boundary-clip exclusion discards 66.75% of track 10's columns specifically.

**Expected:** A recorded decision (override rationale, or a new gap-closure plan) — per the context provided with this verification task, the user has already indicated they want to pursue (b) rather than accept an override; this should be formalized as a follow-up plan before Phase 1 is marked complete.

**Why human:** This is an explicit scientific/product judgment call the plan's own HONEST-OUTCOME GUARD defers to a human, not something grep or a test can resolve.

### 2. Visual sign-off on regenerated QA figures (tracks 8, 14, 21)

**Test:** Inspect `processed_data/targets/qa/track_{8,14,21}_{residual_map,overlay,width}.png` at full resolution.

**Expected:** Residual structure is scientifically acceptable process/substrate variation (not underfit global curvature or bead-absorption artifacts); boundary traces follow the physical bead closely enough to serve as ground truth for these three tracks.

**Why human:** This verification directly inspected the overlay images and found them plausible (continuous traces, explicit gap shading), but confirming residual-map scientific adequacy and boundary quality at full resolution is a domain judgment beyond what an automated verifier can certify.

### 3. `check_targets.py` coverage-floor policy decision

**Test:** Decide the project's minimum-valid-fraction floor for a track to be considered usable (CR-02's fix suggests 50%, matching the existing informational threshold already printed).

**Expected:** A `MIN_VALID_FRACTION` constant and a hard `require(...)` gate are added, or an explicit documented exception is recorded for any track allowed to fall below it.

**Why human:** Choosing the floor value is a project policy decision, not a mechanically derivable one.

## Gaps Summary

Plans 01-06/01-07/01-08 successfully closed the prior verification's Gap 1 (provenance completeness) in full — `extraction_params()` is now complete (15 keys) and change-sensitive, Amendment A4 is recorded, and the bead-mask fix was applied uniformly via a pre-registered, outcome-independent criterion with no per-track tuning (independently re-confirmed here).

However, the phase goal remains unmet for two independent reasons, one carried forward and two newly surfaced by this session's code review and independently corroborated during this verification:

1. **The roadmap's required width ordering is still not achieved** (10-vs-14 FLAGs), traced to track 10's bead sitting at the y-strip edge, which collapses its valid coverage to 5.2% and makes its extracted target unusable as ground truth. This is honestly reported, not tuned away — but it is still a phase-goal blocker, and the QA-sanity criterion for track 10 fails as a direct consequence (its overlay shows no visible boundary trace).
2. **The automated safety net for this phase's "trusted downstream" promise has two independently reproduced, unresolved holes**: `check_targets.py` reports success even when a track is 95% invalid (CR-02), and the artifact-publication path can be tricked by a pre-existing symlink into deleting an arbitrary in-repository directory (CR-03, reproduced live). Both bear directly on whether this phase's output can be trusted as a reproducible, safe foundation for Phase 2.

None of these gaps is assigned to a later phase in the roadmap, and no override has been recorded for the ordering criterion — the human has indicated intent to pursue further diagnosis of track 10 rather than accept an override. Phase 1 should not be marked complete, and Phase 2 should not consume `processed_data/targets/track_10_targets.npz` as-is, until these are resolved.

---

_Verified: 2026-07-20T22:10:00Z_
_Verifier: Claude (gsd-verifier)_
