---
phase: 1
slug: target-extraction-contract
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-19
updated: 2026-07-20
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | plain-Python assertion scripts (planner decision: REQUIREMENTS.md scopes out a test-suite framework; RESEARCH §Validation Architecture specifies runnable assertion scripts; avoids installing any package outside the audited requirements.txt. `tests/test_targets.py` and `tests/test_run_target_extraction.py` use `test_*` functions + bare asserts, pytest-compatible if ever needed) |
| **Config file** | none — Wave 0 creates `.venv` from requirements.txt only |
| **Quick run command** | `.venv/bin/python tests/test_targets.py` (14 checks) and `.venv/bin/python tests/test_run_target_extraction.py` (7 checks) |
| **Optimization-safe command** | `.venv/bin/python -O tests/test_targets.py` and `.venv/bin/python -O tests/test_run_target_extraction.py` — both suites are asserted to stay green with Python's `-O` flag since plan 01-03 added optimization-safe contract checks |
| **Full suite command** | `.venv/bin/python scripts/run_target_extraction.py --project_dir .` then `.venv/bin/python scripts/check_targets.py --project_dir .` |
| **Estimated runtime** | quick: <10s · full pipeline: ~5–10 min (pure-Python ASC loader) |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/python tests/test_targets.py` (once it exists; plan 01 task 1 uses the venv import smoke check)
- **After every plan wave:** Wave 1: `tests/test_targets.py` green · Wave 2: full pipeline + `check_targets.py` green · Wave 3 (plan 01-03): `tests/test_targets.py` + `tests/test_run_target_extraction.py` green under normal and `-O` Python
- **Before `/gsd-verify-work`:** invariant tests + runner-safety tests + `check_targets.py` green, plus human visual sign-off of the 12 QA figures (tracked in `01-UAT.md`)
- **Max feedback latency:** 60 seconds (invariant tests <10s; runner-safety tests <10s; artifact checks <10s; only the one-time full extraction run exceeds this)

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

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `uv` environment created and `requirements.txt` deps installed (no venv exists yet; system Python lacks numpy) — plan 01 task 1
- [x] `tests/test_targets.py` created: plain-Python contract-invariant assertion runner (planner decision: no pytest — see Test Infrastructure rationale) — plan 01 task 2
- [x] `processed_data/targets/` + `qa/` created at runtime by `scripts/run_target_extraction.py` — plan 02 task 1
- [x] `tests/test_run_target_extraction.py` created: bounded-temp-repo runner-safety assertion runner — plan 03 task 2

---

## Manual-Only Verifications

Width ordering (400W(8) > 350W(10) > 300W(14) > 200W(21)) and the constants-locked-before-ordering-inspection prohibition are now mechanically verified — see `01-VERIFICATION.md` Observable Truths #2 and Prohibitions. The four remaining judgment items are tracked as live UAT tests in `01-UAT.md` (status: `testing`, 4/4 pending) rather than duplicated here:

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Residual curvature on all four tracks (D-14) | TARGET-02 | "No scientifically significant bow/curvature" is a visual judgment; broad residual structure is visible in tracks 8, 10, 14 | `01-UAT.md` Test 1 — open `processed_data/targets/qa/track_{id}_residual_map.png` for all 4 tracks |
| Boundary overlay sanity and explicit gaps | TARGET-02 | Numeric mask/order checks cannot decide whether visible sharp excursions are physically real or extraction artifacts | `01-UAT.md` Test 2 — open `processed_data/targets/qa/track_{id}_overlay.png`, emphasizing track 10's 43.8% valid fraction and track 21's gaps |
| Crop-edge smoothing plausibility | TARGET-02 | Synthetic quadratic exactness (proven by test) does not establish real-curve scientific plausibility | `01-UAT.md` Test 3 — open `processed_data/targets/qa/track_{id}_width.png`, inspect shaded 20/100 mm crop-edge regions |
| A1/A2 re-affirmation and no-tuning intent | TARGET-01 | Git chronology and the unchanged parameter dictionary prove implementation and commit order, not the user's actual scientific ratification/intent | `01-UAT.md` Test 4 — reconfirm A1/A2 after reviewing the real QA; confirm constants were fixed before, not tuned after, ordering inspection |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-07-20 — all mechanical requirements (TARGET-01, TARGET-02) have automated coverage that runs green under normal and `-O` Python. Remaining sign-off is scientific/visual judgment, tracked separately as live UAT tests in `01-UAT.md` (not a Nyquist gap).

---

## Validation Audit 2026-07-20

| Metric | Count |
|--------|-------|
| Gaps found | 1 (documentation drift: Per-Task Map and Test Infrastructure omitted plan 01-03's two tasks and `tests/test_run_target_extraction.py`) |
| Resolved | 1 (Per-Task Map, Test Infrastructure, Wave 0 Requirements, and Manual-Only reconciled against current SUMMARY/VERIFICATION/UAT artifacts; no missing automated coverage found — all commands re-run and confirmed green) |
| Escalated | 0 |
