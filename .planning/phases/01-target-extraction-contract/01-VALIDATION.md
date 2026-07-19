---
phase: 1
slug: target-extraction-contract
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-19
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | plain-Python assertion scripts (planner decision: REQUIREMENTS.md scopes out a test-suite framework; RESEARCH §Validation Architecture specifies runnable assertion scripts; avoids installing any package outside the audited requirements.txt. `tests/test_targets.py` uses `test_*` functions + bare asserts, pytest-compatible if ever needed) |
| **Config file** | none — Wave 0 creates `.venv` from requirements.txt only |
| **Quick run command** | `.venv/bin/python tests/test_targets.py` |
| **Full suite command** | `.venv/bin/python scripts/run_target_extraction.py --project_dir .` then `.venv/bin/python scripts/check_targets.py --project_dir .` |
| **Estimated runtime** | quick: <10s · full pipeline: ~5–10 min (pure-Python ASC loader) |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/python tests/test_targets.py` (once it exists; plan 01 task 1 uses the venv import smoke check)
- **After every plan wave:** Wave 1: `tests/test_targets.py` green · Wave 2: full pipeline + `check_targets.py` green
- **Before `/gsd-verify-work`:** invariant tests + `check_targets.py` green, plus human visual sign-off of the 12 QA figures
- **Max feedback latency:** 60 seconds (invariant tests <10s; artifact checks <10s; only the one-time full extraction run exceeds this)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-T1 | 01 | 1 | TARGET-01 | T-01-SC | only audited requirements.txt packages installed | smoke | `.venv/bin/python -c "import numpy, scipy, matplotlib, pandas"` | ❌ W0 | ⬜ pending |
| 01-01-T2 | 01 | 1 | TARGET-01, TARGET-02 | T-01-02, T-01-04 | filename + header hard-fail asserts | unit (synthetic) | `.venv/bin/python tests/test_targets.py` | ❌ W0 | ⬜ pending |
| 01-02-T1 | 02 | 2 | TARGET-02 | T-01-05 | data/raw snapshot integrity PASS | integration (real data) | `.venv/bin/python scripts/run_target_extraction.py --project_dir .` + artifact-existence one-liner | ❌ W0 | ⬜ pending |
| 01-02-T2 | 02 | 2 | TARGET-02 | T-01-08 | params provenance equals code constants | assert (artifacts) | `.venv/bin/python scripts/check_targets.py --project_dir .` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `uv` environment created and `requirements.txt` deps installed (no venv exists yet; system Python lacks numpy) — plan 01 task 1
- [ ] `tests/test_targets.py` created: plain-Python contract-invariant assertion runner (planner decision: no pytest — see Test Infrastructure rationale) — plan 01 task 2
- [ ] `processed_data/targets/` + `qa/` created at runtime by `scripts/run_target_extraction.py` — plan 02 task 1

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| QA overlay plots visually sane (no sawtooth jitter, no silently dropped gaps) | TARGET-02 | Visual confirmation of plots is inherently human | Open QA overlay PNGs for all 4 tracks (raw + detrended), inspect boundaries and track-21 gap regions |
| Width ordering 400W(8) > 350W(10) > 300W(14) > 200W(21) — investigation checkpoint | TARGET-02 | Research shows 8 vs 10 ordering empirically at risk; outcome needs human decision, not constant-tuning | Review per-track median width table emitted by extractor CLI; if ordering fails, escalate per plan checkpoint |
| Post-detrend residual maps show no obvious bow/curvature (D-14) | TARGET-02 | "Obvious curvature" is a visual judgment per CONTEXT | Open `processed_data/targets/qa/track_{id}_residual_map.png` for all 4 tracks |
| Contract amendments A1 (bin-first D-05/D-06) and A2 (y-boundary clip rule) confirmed by user | TARGET-01 | A1/A2 are a-priori contract interpretations adopted from RESEARCH Findings 1/3 (literal per-column rule provably yields zero output); user must ratify at phase verification | Review evidence tables in 01-RESEARCH.md Finding 1 and Open Questions 1/3; confirm or amend the contract wording |
| Constants set before/independent of ordering inspection (prohibition P1) | TARGET-01 | Judgment review, not mechanically testable per SPEC | Confirm plan 01 commit locking constants predates plan 02's first width output; confirm `git diff -- src/targets.py` empty after plan 02 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
