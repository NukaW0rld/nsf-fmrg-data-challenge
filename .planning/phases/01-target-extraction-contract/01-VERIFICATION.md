---
phase: 01-target-extraction-contract
verified: 2026-07-21T18:30:00Z
status: human_needed
score: 4/6 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 5/7
  gaps_closed:
    - "check_targets.py now fails closed on coverage violations via a hard MIN_VALID_FRACTION=0.5 require() gate (01-10) — confirmed live: exit 0 today only because all 4 tracks clear >=60.5% coverage; previously exit 0 was printed even at track 10's 5.2% coverage."
    - "Publish-path symlink exploit (CR-03) is closed: reject_symlink_path() rejects a symlinked candidate or in-repo symlinked ancestor before any resolve/rmtree/rename, and publish_staging_dir() re-checks is_symlink() immediately before every destructive op (01-10) — 4 dedicated regression tests pass (test_symlink_at_backup_path_is_rejected, test_symlink_at_processed_data_is_rejected, test_publish_refuses_symlinked_backup_immediately_before_rmtree, test_symlink_output_into_raw_is_rejected)."
    - "Track 10's catastrophic coverage collapse (21/400, 5.2%) is diagnosed as a detrend-fitting edge artifact and fixed via Amendment A5 (DETREND_MAX_Y_DEGREE=2, 01-11), restoring track 10 to 242/400 (60.5%) — a representative, non-degenerate sample, no longer failing check_targets.py's coverage gate."
  gaps_remaining:
    - "The 10-vs-14 width-ordering pair still FLAGs even after track 10's coverage fix (0.3713mm vs 0.4765mm, per 01-11-ORDERING-OUTCOME.md) — this is reclassified below from a code-level FAILED gap to a human override-vs-investigate decision, since two independent, honest diagnostic/fix cycles (01-06/07/08 and 01-11) have already been run against this exact defect class without forcing the outcome."
    - "Visual sign-off on all 12 regenerated QA figures has not occurred — 01-SIGNOFF-REQUEST.md exists, is actionable, and has 0 ticked checkboxes."
  regressions: []
behavior_unverified_items: []
human_verification:
  - test: "Decide the 10-vs-14 width-ordering FLAG: accept it as a documented, known limitation (human override, 01-SIGNOFF-REQUEST.md option (a)) or commission a further diagnosed-defect investigation (option (b))."
    expected: "A recorded decision. If (a): rationale recorded and carried as a caveat in ROADMAP.md/REQUIREMENTS.md before Phase 2 starts. If (b): a new gap-closure plan targeting the 10-vs-14 relationship specifically, without touching the now-resolved coverage fix."
    why_human: "This is an explicit scientific/product judgment call the phase's own HONEST-OUTCOME GUARD defers to a human — the constants (DETREND_POLY_ORDER, BEAD_MASK_HEIGHT_FRACTION, MAX_TRACKING_GAP_COLUMNS, DETREND_MAX_Y_DEGREE) were each fixed from residual/physical/numerical evidence before this outcome was inspected, and the project has explicitly committed to not tuning further in response to the ordering result. No grep or test can decide whether the residual gap is acceptable."
  - test: "Open all 12 regenerated QA figures under processed_data/targets/qa/ at full resolution (residual maps, boundary overlays, width curves for tracks 8/10/14/21) and answer the four questions in 01-SIGNOFF-REQUEST.md."
    expected: "Residual structure is scientifically acceptable process/substrate variation on all 4 tracks; boundary overlays are continuous and physically plausible with explicit (not silently bridged) gap shading, including track 10; track 10's terminal V-spike from prior UAT is confirmed gone; the four locked constants are confirmed fixed independently of the ordering outcome."
    why_human: "This verification's own visual inspection of track_10_overlay.png and track_10_width.png shows a real, continuous boundary trace across most of the 20-100mm span (a major improvement over the prior verification's near-total absence of trace), but the trace is visibly more jagged/spiky than tracks 8 and 21's, and the width curve degrades toward near-zero past x=70mm. Whether this level of noise is 'sane' (D-14 bow/curvature and sawtooth criteria) versus still-borderline is a domain judgment beyond what grep/structural checks can certify — exactly what 01-SIGNOFF-REQUEST.md asks a human to confirm."
---

# Phase 1: Target Extraction & Contract Verification Report

**Phase Goal:** A documented, reproducible local-width extraction method is specified and then implemented, and is visually validated against all 4 tracks before anything downstream trusts it as ground truth.
**Verified:** 2026-07-21T18:30:00Z
**Status:** human_needed
**Re-verification:** Yes — full re-verification after 4 gap-closure plans (01-09, 01-10, 01-11, 01-12) landed since the 2026-07-20T22:10:00Z VERIFICATION.md (previous status: gaps_found, 5/7)

## Goal Achievement

### Observable Truths

The four ROADMAP success criteria, merged with the two safety-net truths carried forward from the prior verification's CR-02/CR-03 findings (both bear directly on "reproducible... before anything downstream trusts it").

| # | Truth | Status | Evidence |
|---:|---|---|---|
| 1 | The TARGET-01 contract (width definition, threshold rule, smoothing scale, 0.2mm grid, valid-coordinate mask, track-21 gap rule) is written and reviewed before extraction code is trusted | ✓ VERIFIED | Unchanged since prior verification: D-01–D-16 in `01-CONTEXT.md`, plus Amendments A1-A5 (A5 added by 01-11), all written/dated before or alongside the code implementing them. |
| 2 | Running the extractor on all 4 tracks produces the expected width ordering 400W(8) > 350W(10) > 300W(14) > 200W(21) | ? UNCERTAIN (human) | Live re-run of `scripts/check_targets.py --project_dir .` today: 8=0.7528mm > 10=0.3713mm (PASS), 10=0.3713mm vs 14=0.4765mm (FLAG), 14=0.4765mm > 21=0.1998mm (PASS). Track 10's coverage collapse that made its prior median unrepresentative is fixed (60.5% valid, up from 5.2%), and the 10-vs-14 gap narrowed substantially (0.2509→0.3713 vs 0.4765mm), but the chain still does not fully hold. Two independent, pre-registered, outcome-independent fix cycles have already targeted this defect class (01-06/07/08, then 01-11); the project's own HONEST-OUTCOME GUARD explicitly declines to chase this further with code and instead escalates to a human override-vs-investigate decision via `01-SIGNOFF-REQUEST.md`. Reclassified from FAILED to UNCERTAIN accordingly — see Human Verification #1. |
| 3 | QA plots overlay extracted width/boundary on raw+detrended maps for all 4 tracks, incl. track 21's gaps, and are visually confirmed sane | ? UNCERTAIN (human) | All 12 QA PNGs regenerated 2026-07-21 and directly inspected during this verification. Track 8 and 21 show continuous, plausible boundary traces (as in the prior verification). Track 10's overlay now shows a real boundary trace across most of the 20-100mm span (a major change from the prior verification's near-total absence), but the trace is visibly noisier/more jagged than tracks 8/21, and its width curve degrades toward near-zero past x≈70mm. `01-SIGNOFF-REQUEST.md` was produced specifically to route this domain judgment to a human; 0/4 checkboxes ticked. Not FAILED (the artifact is no longer structurally broken) and not VERIFIED (visual sanity is an explicit human-only gate) — see Human Verification #2. |
| 4 | The identical extraction rule is applied across all 4 tracks with no per-track-tuned thresholds (single shared parameterization) | ✓ VERIFIED | `grep -n "track_id =="` over `src/targets.py`, `src/nsf_fmrg_data.py`, `scripts/run_target_extraction.py` returns nothing; `tests/test_targets.py::test_single_parameterization_has_no_track_conditionals`, `test_track_id_does_not_affect_numeric_output`, and (new) `test_edge_divergence_fix_is_track_independent` all pass. |
| 5 | `check_targets.py` fails closed (non-zero exit / hard error) when a persisted artifact violates the project's own coverage expectations | ✓ VERIFIED | Prior verification's CR-02 gap is closed: `scripts/check_targets.py:100-104` now `require(valid_fraction >= MIN_VALID_FRACTION, ...)` (0.5), a hard `ValueError`-raising gate, not a `print`. Source inspection + live run confirmed. |
| 6 | The publish path used to write `processed_data/targets/` cannot be redirected by a pre-existing symlink into a destructive delete outside the intended output tree | ✓ VERIFIED | Prior verification's CR-03 gap is closed: `reject_symlink_path()` (new in `scripts/run_target_extraction.py:62-73`) rejects a symlinked candidate or symlinked in-repo ancestor before any resolve; `publish_staging_dir()` (lines 309-329) re-checks `is_symlink()` immediately before every `rmtree`/`rename`. 4 dedicated regression tests pass, including the specific `targets.previous`-symlink scenario the prior review reproduced as a live exploit. |

**Score:** 4/6 truths verified (0 present-but-behavior-unverified; 2 routed to human judgment, not counted toward the verified score)

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/targets.py` | Shared extraction implementation incl. bead-mask fix | ✓ VERIFIED | `bead_exclusion_mask()` present and wired; `tests/test_targets.py` — 27/27 PASS. |
| `src/nsf_fmrg_data.py` | Configurable detrend with `fit_mask` + `max_y_degree` (Amendment A5) | ✓ VERIFIED | `robust_plane_detrend(..., fit_mask=..., max_y_degree=...)` confirmed; `tests/test_nsf_fmrg_data.py` — 12/12 PASS. |
| `scripts/run_target_extraction.py` | Symlink-safe publish pipeline | ✓ VERIFIED | `reject_symlink_path`, re-checked `is_symlink()` guards present at every destructive op; `tests/test_run_target_extraction.py` — 14/14 PASS. |
| `scripts/check_targets.py` | Hard coverage-floor gate + structural/provenance checks | ✓ VERIFIED | `MIN_VALID_FRACTION = 0.5` enforced via `require()`; live run exits 0 only because all 4 tracks now clear the floor. |
| `scripts/diagnose_track10_coverage.py` | Committed, re-runnable coverage diagnostic (01-11) | ✓ EXISTS, ⚠️ diverges from production (see WR-01 below) | Present and runnable; its `production_residual_profile()` omits `max_y_degree=DETREND_MAX_Y_DEGREE`, so it reports track 10 at 5.25% valid while the real pipeline produces 60.5% — a diagnostic-staleness warning, not a phase-goal blocker. |
| `scripts/diagnose_width_regression.py` | Diagnostic sweep tool (bead-mask axis added 01-09) | ✓ EXISTS, ⚠️ still diverges from production on `max_y_degree` (WR-02) | Bead-mask axis present and correct per WR-03 (prior review); `max_y_degree` axis still missing, so its "production-labeled" sweep row underreports track 10's width by ~48% relative to the live pipeline. |
| `processed_data/targets/track_{8,10,14,21}_targets.npz` | Regenerated fixed-grid curves under Amendment A5 | ✓ VERIFIED | All 4 pass `check_targets.py`'s full structural/dtype/mask/coverage checks; valid fractions 91.0% / 60.5% / 75.0% / 81.3%. |
| `processed_data/targets/extraction_params.json` / `manifest.json` | Complete, change-sensitive provenance | ✓ VERIFIED | 16 keys (added `DETREND_MAX_Y_DEGREE`); SHA-256 digest matches; `check_targets.py` cross-checks both live. |
| `processed_data/targets/qa/*.png` | 12 regenerated QA images | ✓ EXIST, visual sanity ? UNCERTAIN | All 12 present and dated 2026-07-21 (post-Amendment-A5 regeneration); see Truth #3. |
| `.planning/phases/01-target-extraction-contract/01-CONTEXT.md` | Amendments A1-A5 | ✓ VERIFIED | Amendment A5 present with the pre-registered criterion and evidence. |
| `.planning/phases/01-target-extraction-contract/01-11-ORDERING-OUTCOME.md` | Honest outcome report | ✓ VERIFIED | Reports the still-unresolved 10-vs-14 FLAG; `git diff --stat -- src/targets.py src/nsf_fmrg_data.py scripts/check_targets.py` empty for the reporting commit; no per-track branch. |
| `.planning/phases/01-target-extraction-contract/01-SIGNOFF-REQUEST.md` | Human sign-off handoff | ✓ VERIFIED | Exists, names all 12 figures with concrete acceptance questions, presents the override-vs-investigate choice without recommending one, 0/4 checkboxes ticked. |
| `.planning/REQUIREMENTS.md` | TARGET-02 status corrected | ✓ VERIFIED | Reads "Awaiting human visual sign-off on regenerated QA figures — see `01-SIGNOFF-REQUEST.md`" with a dated correction note, not falsely marked `Complete`. |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `extract_track_targets()` | `bead_exclusion_mask()` | Computed per-track from raw `Z_mm`, passed as `fit_mask` | ✓ WIRED | Unchanged, tests pass. |
| `robust_plane_detrend()` | least-squares fit | `fit_mask` excludes bead pixels; `max_y_degree` caps cross-track polynomial degree (Amendment A5) | ✓ WIRED | `test_robust_plane_detrend_fit_mask_excludes_bead_from_fit`, `test_detrend_does_not_diverge_at_strip_edge`, `test_polynomial_basis_sizes_are_stable` all pass. |
| `extraction_params()` | `extraction_params.json` / manifest SHA-256 | JSON dump + digest | ✓ WIRED | Live file inspection matches; digest change-sensitivity test passes. |
| `run_target_extraction.py::publish_staging_dir` | `processed_data/targets/` | Rename staging → live, rmtree backup, symlink-checked at every step | ✓ WIRED (safety gap closed) | Previously "WIRED WITH SAFETY GAP" (CR-03); now fully guarded — 4 dedicated symlink regression tests pass. |
| `scripts/check_targets.py` | persisted NPZs | `np.load` + structural asserts + hard coverage-floor gate | ✓ WIRED (gating gap closed) | Previously "WIRED WITH GATING GAP" (CR-02); coverage check is now a `require()`, confirmed to actually block (exercised indirectly: the pre-fix track 10 state would have failed this gate; today's regenerated state passes it honestly). |
| `find_track_file()` (thermal/height-map read path) | filesystem | `is_file()` match with no `is_symlink()` rejection | ⚠️ WIRED WITH LATENT GAP (WR-03, not a phase blocker) | Read-path symlink rejection exists for SEM tiles (`get_sem_tile_paths`) and the entire write path, but not for `find_track_file` itself — flagged by `01-REVIEW.md` as a real but currently non-misfiring gap given the 4-file real dataset. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Target-contract regressions | `.venv/bin/python tests/test_targets.py` | 27 PASS, 0 FAIL | ✓ PASS |
| Detrend + loader regressions | `.venv/bin/python tests/test_nsf_fmrg_data.py` | 12 PASS, 0 FAIL | ✓ PASS |
| Runner safety + symlink regressions | `.venv/bin/python tests/test_run_target_extraction.py` | 14 PASS, 0 FAIL (incl. `data/raw/` integrity PASS on every real-data run) | ✓ PASS |
| Persisted artifact/provenance/coverage checker | `.venv/bin/python scripts/check_targets.py --project_dir .` | Structural + provenance + coverage-floor checks all pass; ordering FLAG on 10-vs-14 printed as diagnostic, not gated; exit 0 | ✓ PASS (coverage gate now blocking; ordering FLAG intentionally non-blocking per design) |
| No per-track branching | `grep -n "track_id ==" src/targets.py src/nsf_fmrg_data.py scripts/run_target_extraction.py` | No matches | ✓ PASS |
| `data/raw/` untouched by any phase-1 code path | `git log --oneline -- data/raw` shows only the original data-tracking commit; runner's own audit prints `PASS` on every run | Unmodified since original commit; runner-internal audit consistently PASS | ✓ PASS (note: `data/raw/` itself IS committed to git via a prior, out-of-phase commit — a Phase 5 SUBMIT-01/02 concern per ROADMAP, not a Phase 1 must-have; flagged for awareness, not scored here) |

### Probe Execution

No probe scripts declared in any Phase 1 plan and no conventional `scripts/*/tests/probe-*.sh` files exist.

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|---|---|---|---|---|
| TARGET-01 | 01-01, 01-03, 01-04, 01-05, 01-07, 01-10, 01-11 | Contract specified/documented before extraction code trusted, single shared parameterization | ✓ SATISFIED | `01-CONTEXT.md` (D-01–D-16, A1-A5), `extraction_params.json` (16 keys), no per-track branches; `REQUIREMENTS.md` marks this `[x] Complete`, consistent with this verification. |
| TARGET-02 | 01-01 through 01-12 | Extractor implements the contract and is visually QA'd against all 4 tracks before being trusted downstream | ? NEEDS HUMAN | Coverage collapse (the structural blocker from the prior verification) is fixed; both remaining criteria (width-ordering acceptance, visual figure sign-off) are explicitly human-only decisions per `01-SIGNOFF-REQUEST.md`. `REQUIREMENTS.md` correctly reflects this as "Awaiting human visual sign-off," not `Complete` — consistent with this verification. |

Every requirement ID declared across all 12 plans (`requirements:` frontmatter) is `TARGET-01` and/or `TARGET-02`; both are present in `REQUIREMENTS.md`. No orphaned requirement IDs for this phase.

### Prohibitions

| Prohibition | Tier | Status | Evidence |
|---|---|---|---|
| No outcome-driven per-track tuning of extraction constants | judgment | ✓ VERIFIED | `01-11-ORDERING-OUTCOME.md` reports the still-unresolved ordering with `git diff --stat` empty for the reporting commit; `01-11-CRITERION.md` pre-registered the fix-selection tolerance and candidate mechanisms before any source change existed; Candidate A was rejected by a priori measurement (not by its effect on the ordering); no per-track branch found by direct grep. |
| No writes/deletes/modifications under `data/raw/` | test | ✓ VERIFIED | `snapshot_raw`/`raw_snapshot_diff` audits pass in all 14 runner tests; `data/raw/ integrity PASS` printed on every live run observed during this verification. |
| Output publication must not permit destructive operations outside the intended output tree | test | ✓ VERIFIED (was UNVERIFIED/FLAGGED in prior verification) | CR-03 is closed: `reject_symlink_path()` + per-step `is_symlink()` re-checks close the exploit `01-REVIEW.md` previously reproduced live; 4 dedicated regression tests pass, including the exact `targets.previous`-symlink scenario. |

### Anti-Patterns and Review Findings

No `TBD`, `FIXME`, `XXX`, `TODO`, `HACK`, or placeholder-language markers found in any phase source/script file (`src/targets.py`, `src/nsf_fmrg_data.py`, `scripts/run_target_extraction.py`, `scripts/check_targets.py`, `scripts/diagnose_width_regression.py`, `scripts/diagnose_track10_coverage.py`).

A fresh, independent code review (`01-REVIEW.md`, 2026-07-21T17:19:38Z) re-verified the three prior CRITICALs as genuinely fixed against real data and real pipeline execution (not just re-cited), and surfaced 6 new WARNINGs + 2 INFO items — none rise to blocker severity per the review's own classification, since none produce wrong targets in the shipped production pipeline:

| Finding | Severity | Disposition |
|---|---|---|
| WR-01: `diagnose_track10_coverage.py`'s "production" path omits `DETREND_MAX_Y_DEGREE`, reports 10x-worse numbers than real production | ⚠️ Warning | Diagnostic-tooling staleness; does not affect the shipped extraction pipeline. |
| WR-02: `diagnose_width_regression.py`'s sweep still never applies `DETREND_MAX_Y_DEGREE` | ⚠️ Warning | Same class as WR-01; diagnostic tool drift, not a production defect. |
| WR-03: `find_track_file` (thermal/height-map read path) has no symlink rejection, unlike every other data-touching path | ⚠️ Warning | Real latent gap, inconsistent with the codebase's own established threat model, but does not currently misfire against the 4-file real dataset. |
| WR-04: `load_wyko_asc` has no exact-filename guard of its own; silently defaults a missing `pixel_size_mm` header | ⚠️ Warning | Guard exists one layer up in `extract_track_targets`; gap only affects direct-caller diagnostic scripts. |
| WR-05: `robust_plane_detrend`'s `order`/`max_y_degree` validation runs after the degenerate-data early return | ⚠️ Warning | Production call sites always pass hardcoded, correct values; only affects programmatically-swept `order` values in diagnostics. |
| WR-06: `bin_profile`'s `np.nanmedian` over all-NaN slices emits an uncontrolled `RuntimeWarning` on every real run | ⚠️ Warning | Cosmetic/log-hygiene issue; behavior is otherwise correctly handled downstream. |
| IN-01/IN-02 | ℹ️ Info | Unused import; redundant no-op path-resolution call. |

None of these findings block the phase goal as scored above; they are legitimate follow-up items (naturally suited to a Phase 2 planning note or a small standalone cleanup) but do not gate Phase 1 completion.

## Human Verification Required

### 1. Width-ordering override vs. further investigation (10-vs-14 FLAG)

**Test:** Review `01-SIGNOFF-REQUEST.md`'s "Width-ordering override vs. further investigation" section. Choose exactly one: (a) accept the 10-vs-14 FLAG as a documented, known limitation (track 10's median width, from its now-representative 242/400 valid positions, remains below track 14's) and record the rationale, or (b) commission a new gap-closure plan to investigate the 10-vs-14 relationship further.

**Expected:** A recorded decision, captured via `/gsd-verify-work` run against this phase (not by editing `01-SIGNOFF-REQUEST.md` directly, per that document's own instructions).

**Why human:** This is an explicit scientific/product judgment call the phase's own HONEST-OUTCOME GUARD defers to a human. Two independent, pre-registered, outcome-independent diagnostic/fix cycles have already been run against this exact defect class (01-06→01-08, then 01-11); a third automated attempt without new evidence would risk becoming outcome-driven tuning, which the phase has explicitly and repeatedly refused to do.

### 2. Visual sign-off on all 12 regenerated QA figures

**Test:** Open each of `processed_data/targets/qa/track_{8,10,14,21}_{residual_map,overlay,width}.png` at full resolution and answer the three per-figure-class questions plus the constants-confirmation question in `01-SIGNOFF-REQUEST.md`.

**Expected:** Residual structure is scientifically acceptable process/substrate variation on all 4 tracks (no coherent track-wide bow, no manufactured edge feature); boundary overlays are continuous and physically plausible with explicit gray-shaded invalid regions, including track 10; crop-edge behavior is physically plausible and track 10's prior terminal V-spike is confirmed gone; the four locked constants are confirmed fixed independently of the ordering outcome.

**Why human:** This verification's own inspection of `track_10_overlay.png`/`track_10_width.png` confirms a real, continuous boundary trace now exists across most of the 20-100mm span (a major, independently-visible improvement over the prior verification's near-total absence of trace) — but the trace is visibly noisier than tracks 8/21, and the width curve trails toward near-zero past x≈70mm. Whether this residual noise level is within acceptable "no sawtooth/high-frequency jitter" bounds is a domain judgment call this verifier cannot certify programmatically; it is exactly the question `01-SIGNOFF-REQUEST.md` was built to route to a human.

## Gaps Summary

This re-verification finds that the four gap-closure plans (01-09 through 01-12) genuinely closed the two prior structural BLOCKERs (CR-02: `check_targets.py` no longer silently passes catastrophic coverage loss; CR-03: the publish path is no longer symlink-exploitable) and resolved the underlying defect that made track 10's target artifact structurally unusable (its valid coverage rose from 5.2% to 60.5% via a uniform, pre-registered, outcome-independent fix). All 53 regression tests pass; no debt markers or blocker-severity anti-patterns were found in phase source files; both requirement IDs (TARGET-01, TARGET-02) are accounted for with no orphans; `REQUIREMENTS.md`'s prior false "Complete" marking on TARGET-02 has been correctly walked back.

What remains is not a code defect but two linked human decisions, both routed through the same artifact (`01-SIGNOFF-REQUEST.md`) and the same action (`/gsd-verify-work` against Phase 1): (1) whether to accept the residual 10-vs-14 width-ordering FLAG as a documented limitation or commission further investigation, and (2) visual sign-off on the 12 regenerated QA figures, most notably track 10's now-present-but-still-somewhat-noisy boundary trace. Per this phase's own design (an explicit HONEST-OUTCOME GUARD that refuses to keep tuning code in response to an outcome it has already investigated twice), status is `human_needed` rather than `gaps_found` — there is no further mechanical gap-closure step available; the phase awaits a human decision, not more code.

---

_Verified: 2026-07-21T18:30:00Z_
_Verifier: Claude (gsd-verifier)_
