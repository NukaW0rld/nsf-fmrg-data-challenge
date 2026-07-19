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
| **Framework** | pytest (latest) |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| (filled by planner) | | | TARGET-01, TARGET-02 | — | N/A | unit | `uv run pytest tests/ -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `uv` environment created and `requirements.txt` deps installed (no venv exists yet; system Python lacks numpy)
- [ ] `pytest` installed — no test framework detected in repo
- [ ] `tests/` directory created with stubs for TARGET-01 contract invariants

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| QA overlay plots visually sane (no sawtooth jitter, no silently dropped gaps) | TARGET-02 | Visual confirmation of plots is inherently human | Open QA overlay PNGs for all 4 tracks (raw + detrended), inspect boundaries and track-21 gap regions |
| Width ordering 400W(8) > 350W(10) > 300W(14) > 200W(21) — investigation checkpoint | TARGET-02 | Research shows 8 vs 10 ordering empirically at risk; outcome needs human decision, not constant-tuning | Review per-track median width table emitted by extractor CLI; if ordering fails, escalate per plan checkpoint |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
