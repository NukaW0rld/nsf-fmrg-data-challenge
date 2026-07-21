---
phase: 1
slug: target-extraction-contract
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-19
updated: 2026-07-21
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | plain-Python assertion scripts (planner decision: REQUIREMENTS.md scopes out a test-suite framework; RESEARCH §Validation Architecture specifies runnable assertion scripts; avoids installing any package outside the audited requirements.txt. `tests/test_targets.py`, `tests/test_nsf_fmrg_data.py`, and `tests/test_run_target_extraction.py` use `test_*` functions + bare asserts, pytest-compatible if ever needed) |
| **Config file** | none — Wave 0 creates `.venv` from requirements.txt only |
| **Quick run command** | `.venv/bin/python tests/test_targets.py` (27 checks), `.venv/bin/python tests/test_nsf_fmrg_data.py` (12 checks), and `.venv/bin/python tests/test_run_target_extraction.py` (14 checks) — 53 total, all green as of 2026-07-21 |
| **Optimization-safe command** | `.venv/bin/python -O` variant of all three suites above — asserted to stay green with Python's `-O` flag since plan 01-03 added optimization-safe contract checks; extended coverage through plan 01-11 |
| **Full suite command** | `.venv/bin/python scripts/run_target_extraction.py --project_dir .` then `.venv/bin/python scripts/check_targets.py --project_dir .` |
| **Diagnostic tooling (non-gating)** | `scripts/diagnose_width_regression.py --project_dir .` (detrend-order × continuity × bead-mask sweep, plans 01-06/01-09) and `scripts/diagnose_track10_coverage.py` (per-bin rejection histogram, plan 01-11) — read-only against `data/raw/`, used for evidence gathering, not part of the pass/fail gate |
| **Estimated runtime** | quick: <10s · full pipeline: ~5–10 min (pure-Python ASC loader) |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/python tests/test_targets.py` (once it exists; plan 01 task 1 uses the venv import smoke check)
- **After every plan wave:** Wave 1: `tests/test_targets.py` green · Wave 2: full pipeline + `check_targets.py` green · Wave 3 (plan 01-03): `tests/test_targets.py` + `tests/test_run_target_extraction.py` green under normal and `-O` Python · Waves 4-11 (plans 01-04 through 01-12): each wave's touched suite(s) plus `check_targets.py` green under normal and `-O` Python; `tests/test_nsf_fmrg_data.py` added at wave 4 and grown through wave 9
- **Before `/gsd-verify-work`:** invariant tests + loader tests + runner-safety tests + `check_targets.py` green, plus human visual sign-off of the 12 QA figures and the 10-vs-14 width-ordering override decision (tracked as Tests 1-6 in `01-UAT.md`)
- **Max feedback latency:** 60 seconds (invariant tests <10s; loader tests <10s; runner-safety tests <10s; artifact checks <10s; only the one-time full extraction run and the non-gating diagnostic sweeps exceed this)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-T1 | 01 | 1 | TARGET-01 | T-01-SC | only audited requirements.txt packages installed | smoke | `.venv/bin/python -c "import numpy, scipy, matplotlib, pandas"` | ✅ | ✅ green |
| 01-01-T2 | 01 | 1 | TARGET-01, TARGET-02 | T-01-02, T-01-04 | filename + header hard-fail asserts | unit (synthetic) | `.venv/bin/python tests/test_targets.py` | ✅ | ✅ green (14/14 PASS) |
| 01-01-T3 | 01 | 1 | TARGET-01 | — | A1/A2 pre-compute ratification | manual_procedural | user `approved` response recorded in `01-01-SUMMARY.md` | ✅ | ✅ resolved |
| 01-02-T1 | 02 | 2 | TARGET-02 | T-01-05 | data/raw snapshot integrity PASS | integration (real data) | `.venv/bin/python scripts/run_target_extraction.py --project_dir .` + artifact-existence one-liner | ✅ | ✅ green |
| 01-02-T2 | 02 | 2 | TARGET-02 | T-01-08 | params provenance equals code constants | assert (artifacts) | `.venv/bin/python scripts/check_targets.py --project_dir .` | ✅ | ✅ green (ALL CHECKS PASSED) |
| 01-03-T1 | 03 | 3 | TARGET-01 | — | crossed/degenerate boundaries invalidated after final smoothing; zero-valid track hard-fails | unit (synthetic) | `.venv/bin/python tests/test_targets.py` and `.venv/bin/python -O tests/test_targets.py` | ✅ | ✅ green (14/14 PASS, both modes) |
| 01-03-T2 | 03 | 3 | TARGET-02 | — | canonical-root/symlink containment; SHA-256-backed raw audit runs from `finally` on success and failure | integration (bounded temp repo) | `.venv/bin/python tests/test_run_target_extraction.py` and `.venv/bin/python -O tests/test_run_target_extraction.py` | ✅ | ✅ green (7/7 PASS, both modes) |
| 01-04-D1 | 04 | 4 | TARGET-01 | — | `robust_plane_detrend` supports affine (order=1) and quartic (order=4) surface fits | unit | `.venv/bin/python tests/test_nsf_fmrg_data.py` | ✅ | ✅ green |
| 01-04-D2 | 04 | 4 | TARGET-02 | — | shared `DETREND_POLY_ORDER=4` (Amendment A3) applied identically, persisted in provenance | unit + integration | `.venv/bin/python tests/test_targets.py` and `scripts/check_targets.py --project_dir .` | ✅ | ✅ green |
| 01-04-D3 | 04 | 4 | TARGET-02 | — | regenerated residual maps remove global bow, retain localized structure honestly | manual_procedural | visual QA — `01-UAT.md` Test 1 | ✅ | see Manual-Only |
| 01-05-D1 | 05 | 5 | TARGET-01 | — | continuity tracking follows nearest non-clipped candidate, resets after long gaps | unit | `.venv/bin/python tests/test_targets.py` (6 continuity regressions) | ✅ | ✅ green |
| 01-05-D2 | 05 | 5 | TARGET-01 | — | 3-point `nan_savgol` windows damp with ≥1 residual degree of freedom | unit | `.venv/bin/python tests/test_targets.py` | ✅ | ✅ green |
| 01-05-D3 | 05 | 5 | TARGET-02 | — | regenerated 4-track artifacts show reduced boundary-jump frequency | integration + manual_procedural | `scripts/check_targets.py --project_dir .` + visual QA — `01-UAT.md` Test 2/3 | ✅ | see Manual-Only |
| 01-06-D1 | 06 | 6 | TARGET-02 | — | detrend-order × continuity sweep diagnostic reuses shared helpers, read-only | integration | `.venv/bin/python scripts/diagnose_width_regression.py --project_dir .` | ✅ | ✅ green |
| 01-06-D2 | 06 | 6 | TARGET-02 | — | sweep isolates `DETREND_POLY_ORDER=4` as the necessary condition for the ordering regression | integration (artifact) | `processed_data/diagnostics/width_regression_sweep.csv` (4 PASS at order 1/2, 2 FLAG at order 4) | ✅ | ✅ green |
| 01-06-D3 | 06 | 6 | TARGET-02 | — | pre-registered, outcome-independent fix-selection criterion committed before any fix | manual_procedural | `01-06-DIAGNOSIS.md` §3 | ✅ | see Manual-Only |
| 01-07-D1 | 07 | 7 | TARGET-01 | — | `robust_plane_detrend(fit_mask=...)` excludes flagged pixels from the fit only; default unaffected | unit | `.venv/bin/python tests/test_nsf_fmrg_data.py` | ✅ | ✅ green |
| 01-07-D2 | 07 | 7 | TARGET-02 | WR-03 | bead-mask rule (Amendment A4) is track-independent; no per-track branch | unit | `.venv/bin/python tests/test_targets.py` | ✅ | ✅ green |
| 01-07-D3 | 07 | 7 | TARGET-01 | T-01-08 | `extraction_params()` complete (15 keys), SHA-256 digest change-sensitive to both new params | unit | `.venv/bin/python tests/test_targets.py` | ✅ | ✅ green |
| 01-07-D4 | 07 | 7 | TARGET-01 | — | Amendment A4 canonicalized in `01-CONTEXT.md` | manual_procedural | doc review — `01-CONTEXT.md` Amendment A4 | ✅ | see Manual-Only |
| 01-08-D1 | 08 | 8 | TARGET-01 | — | atomic regeneration of 4 NPZs + provenance + 12 QA PNGs carrying Amendment A4 | integration | `.venv/bin/python scripts/run_target_extraction.py --project_dir .` | ✅ | ✅ green |
| 01-08-D2 | 08 | 8 | TARGET-01 | — | persisted params/manifest/structural contract hold, normal + `-O` | integration | `scripts/check_targets.py --project_dir .` (normal + `-O`) | ✅ | ✅ green |
| 01-08-D3 | 08 | 8 | TARGET-01 | T-01-05 | `data/raw/` integrity audit: zero files created/modified/deleted | other | `git status --porcelain -- data/raw` (empty) + runner's own snapshot audit | ✅ | ✅ green |
| 01-08-D4 | 08 | 8 | TARGET-02 | — | 8>10>14>21 ordering re-checked, honestly reported as NOT restored, no constant tuned | manual_procedural | `01-08-ORDERING-OUTCOME.md` | ✅ | see Manual-Only |
| 01-09-D1 | 09 | 9 | TARGET-02 | WR-03 | width-regression sweep exercises production detrend path via bead-mask axis | unit + other | inline assertion + `py_compile scripts/diagnose_width_regression.py` | ✅ | ✅ green |
| 01-09-D2 | 09 | 9 | TARGET-02 | — | diagnostic evidence written outside the publish-destroyed tree (`processed_data/diagnostics/`) | other | grep + inline relative-path check | ✅ | ✅ green |
| 01-09-D3 | 09 | 9 | TARGET-02 | WR-01 | `find_track_file` requires a delimiter-anchored track-id token, not bare substring | unit + other | `.venv/bin/python tests/test_nsf_fmrg_data.py` + real-dataset one-liner | ✅ | ✅ green |
| 01-09-D4 | 09 | 9 | TARGET-02 | WR-02 | all modality loaders raise `ValueError` on unresolved/mis-resolved source | unit | `.venv/bin/python tests/test_nsf_fmrg_data.py` | ✅ | ✅ green |
| 01-09-D5 | 09 | 9 | TARGET-02 | — | no constant changed, no per-track branch, `data/raw/` untouched | other + unit | grep + `git status --porcelain data/raw` + full suites green | ✅ | ✅ green |
| 01-10-D1 | 10 | 9 | TARGET-02 | CR-03 | `resolve_output_path` rejects a symlinked candidate or symlinked in-repo ancestor | unit | `.venv/bin/python tests/test_run_target_extraction.py` | ✅ | ✅ green |
| 01-10-D2 | 10 | 9 | TARGET-02 | CR-03 | `publish_staging_dir` re-checks `is_symlink()` immediately before every `rmtree`/`rename` | unit | `.venv/bin/python tests/test_run_target_extraction.py` | ✅ | ✅ green |
| 01-10-D3 | 10 | 9 | TARGET-01 | CR-02 | `check_targets.py` enforces `MIN_VALID_FRACTION=0.5` via blocking `require()`, not a print | other | `scripts/check_targets.py --project_dir .` (exits non-zero on violation) | ✅ | ✅ green |
| 01-11-D1 | 11 | 10 | TARGET-01 | — | track 10 coverage collapse characterized by committed, re-runnable diagnostic | unit | `scripts/diagnose_track10_coverage.py` against real data | ✅ | ✅ green |
| 01-11-D2 | 11 | 10 | TARGET-01 | — | outcome-independent fix-selection criterion committed strictly before any source change | unit (git evidence) | `git log`/`git diff` ordering check | ✅ | ✅ green |
| 01-11-D3 | 11 | 10 | TARGET-02 | — | Amendment A5 (`DETREND_MAX_Y_DEGREE`) applied uniformly, provenance-locked (16 keys) | unit | `.venv/bin/python tests/test_targets.py` and `tests/test_nsf_fmrg_data.py` | ✅ | ✅ green |
| 01-11-D4 | 11 | 10 | TARGET-02 | — | all 4 tracks regenerated; track 10 clears 50% floor (242/400, 60.5%); ordering reported honestly | integration + manual_procedural | `scripts/check_targets.py --project_dir .` + `01-11-ORDERING-OUTCOME.md` | ✅ | see Manual-Only |
| 01-12-D1 | 12 | 11 | TARGET-02 | T-01-30 | `REQUIREMENTS.md` TARGET-02 row corrected from false `Complete` to honest awaiting-sign-off | other | grep against `.planning/REQUIREMENTS.md` | ✅ | ✅ green |
| 01-12-D2 | 12 | 11 | TARGET-02 | — | `01-SIGNOFF-REQUEST.md` handoff produced naming all 12 figures, 0 pre-ticked checkboxes | manual_procedural | grep counts + doc review | ✅ | see Manual-Only |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `uv` environment created and `requirements.txt` deps installed (no venv exists yet; system Python lacks numpy) — plan 01 task 1
- [x] `tests/test_targets.py` created: plain-Python contract-invariant assertion runner (planner decision: no pytest — see Test Infrastructure rationale) — plan 01 task 2
- [x] `processed_data/targets/` + `qa/` created at runtime by `scripts/run_target_extraction.py` — plan 02 task 1
- [x] `tests/test_run_target_extraction.py` created: bounded-temp-repo runner-safety assertion runner — plan 03 task 2

---

## Manual-Only Verifications

`01-UAT.md` has grown from 4 to 6 tests since the prior audit. Tests 1-3 originally reported `issue` (gaps G-01-1/G-01-2/G-01-3); each has since had a root-cause fix land in a dedicated plan (residual bow → Amendment A3 quartic detrend, plan 01-04; boundary sawtooth → continuity tracking + degenerate-window smoothing, plan 01-05; track 10 crop-edge V-spike and coverage collapse → bead-mask fix + Amendment A5, plans 01-07/01-11) and been re-verified live in `01-VERIFICATION.md`. Test 4 passed. Tests 5 and 6 are the two items still open and are exactly the two `human_verification` entries in `01-VERIFICATION.md`:

| Behavior | Requirement | Why Manual | Test Instructions | Current Status |
|----------|-------------|------------|-------------------|-----------------|
| Residual curvature on all four tracks (D-14) | TARGET-02 | "No scientifically significant bow/curvature" is a visual judgment | `01-UAT.md` Test 1 — `processed_data/targets/qa/track_{id}_residual_map.png` | resolved: root cause fixed by Amendment A3 (plan 01-04), re-verified |
| Boundary overlay sanity and explicit gaps | TARGET-02 | Numeric mask/order checks cannot decide whether sharp excursions are physically real or extraction artifacts | `01-UAT.md` Test 2 — `processed_data/targets/qa/track_{id}_overlay.png` | resolved: continuity tracking + smoothing fix (plan 01-05), re-verified |
| Crop-edge smoothing plausibility | TARGET-02 | Synthetic quadratic exactness (proven by test) does not establish real-curve scientific plausibility | `01-UAT.md` Test 3 — `processed_data/targets/qa/track_{id}_width.png` | resolved: track 10 V-spike confirmed gone (plans 01-07/01-11), re-verified |
| A1/A2 re-affirmation and no-tuning intent | TARGET-01 | Git chronology proves commit order, not the user's actual scientific ratification/intent | `01-UAT.md` Test 4 | passed |
| Width-ordering override vs. further investigation (10-vs-14 FLAG) | TARGET-02 | Explicit scientific/product judgment call; two independent, pre-registered, outcome-independent fix cycles (01-06→08, then 01-11) already ran against this defect class — the phase's HONEST-OUTCOME GUARD declines further automated tuning | `01-UAT.md` Test 5 / `01-SIGNOFF-REQUEST.md` — accept as documented limitation (option a) or commission further investigation (option b) | **pending** — decide via `/gsd-verify-work 1` |
| Visual sign-off on 12 regenerated QA figures | TARGET-02 | Whether track 10's now-present but visibly noisier boundary trace is within acceptable sawtooth/jitter bounds is a domain judgment, not a mechanical check | `01-UAT.md` Test 6 / `01-SIGNOFF-REQUEST.md` — open all 12 `processed_data/targets/qa/*.png` and answer the 4 questions | **pending** — decide via `/gsd-verify-work 1` |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-07-20, re-confirmed 2026-07-21 across all 12 plans — all mechanical requirements (TARGET-01, TARGET-02) have automated coverage that runs green under normal and `-O` Python. Remaining sign-off is scientific/visual judgment, tracked separately as live UAT tests in `01-UAT.md` (not a Nyquist gap).

---

## Validation Audit 2026-07-20

| Metric | Count |
|--------|-------|
| Gaps found | 1 (documentation drift: Per-Task Map and Test Infrastructure omitted plan 01-03's two tasks and `tests/test_run_target_extraction.py`) |
| Resolved | 1 (Per-Task Map, Test Infrastructure, Wave 0 Requirements, and Manual-Only reconciled against current SUMMARY/VERIFICATION/UAT artifacts; no missing automated coverage found — all commands re-run and confirmed green) |
| Escalated | 0 |

## Validation Audit 2026-07-21

| Metric | Count |
|--------|-------|
| Gaps found | 1 (documentation drift: Per-Task Map, Test Infrastructure, and Manual-Only had not been updated since 2026-07-20 and were missing all 9 tasks/waves from plans 01-04 through 01-12 — 9 gap-closure/hardening plans landed in the interim) |
| Resolved | 1 (Per-Task Map extended with 26 new rows sourced from each plan's `coverage:` frontmatter in its SUMMARY.md, cross-referenced against `01-VERIFICATION.md`'s live re-run; Test Infrastructure updated to include `tests/test_nsf_fmrg_data.py` and both diagnostic scripts; Manual-Only reconciled against `01-UAT.md`'s current 6-test state. All three test suites re-run live during this audit: `tests/test_targets.py` 27/27 PASS, `tests/test_nsf_fmrg_data.py` 12/12 PASS, `tests/test_run_target_extraction.py` 14/14 PASS (53/53 total); `scripts/check_targets.py --project_dir .` → ALL CHECKS PASSED. No requirement lacks automated coverage — every non-green item is a pre-existing, correctly-routed human-judgment gate (Tests 5-6 in `01-UAT.md`), not a Nyquist gap.) |
| Escalated | 0 |
