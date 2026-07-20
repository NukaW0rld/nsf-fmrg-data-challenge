---
phase: 01
slug: target-extraction-contract
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-07-19
---

# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| raw `.ASC` files → parser | irreplaceable, unversioned scientific input crosses into parsing/extraction code | competition-restricted height-map data |
| filename pattern → track identity | `find_track_file` substring fallback can silently resolve the wrong track's file | track identity (8/10/14/21) |
| `run_target_extraction.py` / `check_targets.py` → `data/raw/` | batch scripts iterate over irreplaceable raw files while writing outputs elsewhere | filesystem read/write |
| CLI `--project_dir` → canonical repository | caller-controlled filesystem identity must resolve to the runner's actual repository before any state change | filesystem path |
| canonical output candidate → resolved `data/raw` | existing directories/files can be symlinks; lexical path prefixes are not a safety boundary | filesystem path |
| pipeline exception → integrity audit | parse, extraction, plotting, or persistence failure must not bypass the post-run raw comparison | control flow |
| repository git history → GitHub remote | competition-restricted raw dataset must not leave the official Zenodo distribution point | competition-restricted dataset (pre-existing, out of Phase 1 scope) |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-01-01 | Tampering (accidental) | anything touching `data/raw/` | high | mitigate | Tests use synthetic arrays exclusively; `load_wyko_asc` opens raw files read-only (`open(path, 'r')`, `src/nsf_fmrg_data.py:171`); mechanical before/after snapshot enforcement in `run_target_extraction.py` (`snapshot_raw`/`raw_snapshot_diff`) | closed |
| T-01-02 | Spoofing (identity confusion) | `extract_track_targets` file resolution | medium | mitigate | Hard `ValueError` unless resolved basename exactly matches expected `Heightmap_{track_id}.ASC` (`src/targets.py:214-216`) | closed |
| T-01-03 | Information disclosure | git history vs. competition-restricted data | medium | accept | Phase 1 task commits stage only `src/targets.py`/`scripts/`/`tests/` — verified clean. However `git log --all -- data/raw` is **not** empty: commit `831987c` ("Started tracking data", pre-dates Phase 1) added the full raw dataset via Git LFS, merged to `origin/main`, and `origin` (`NukaW0rld/nsf-fmrg-data-challenge`) is a **public** GitHub repo. This contradicts `DATA_USE_LICENSE.md` ("do not create separate unofficial mirrors") and `CLAUDE.md`'s data-licensing constraint. Not introduced by Phase 1's code; user has been notified and elected to remediate the repository/history separately, outside this workflow. | accepted (open, non-blocking — below `block_on: high` threshold) |
| T-01-04 | Tampering (malformed input) | `.ASC` header parsing | low | mitigate | `ValueError` when header lacks `pixel_size_mm` instead of silently accepting a hardcoded fallback (`src/targets.py:217-218`) | closed |
| T-01-05 | Tampering (accidental) | `run_target_extraction.py` file I/O | high | mitigate | All writes confined via `resolve_output_path`; before/after `snapshot_raw` SHA-256/mtime/size comparison raises on any `data/raw/` delta | closed |
| T-01-06 | Spoofing (identity confusion) | per-track file resolution (runner) | medium | mitigate | Inherits T-01-02's hard-fail; runner prints each resolved source path (`run_target_extraction.py:254`) | closed |
| T-01-07 | Information disclosure | git vs. competition-restricted data (runner/checker) | medium | accept | Same underlying issue as T-01-03 — see that entry for full detail | accepted (open, non-blocking — below `block_on: high` threshold) |
| T-01-08 | Repudiation (untraceable ground truth) | persisted artifacts vs. parameters | low | mitigate | `extraction_params.json` provenance written every run; `check_targets.py` asserts equality against code constants and a manifest SHA-256 digest | closed |
| T-01-09 | Spoofing | `resolve_repository_root` | high | mitigate | Strict `resolve(strict=True)` of CLI candidate and script-derived anchor, equality check plus repository-marker check, before any write (`run_target_extraction.py:35-49`) | closed |
| T-01-10 | Tampering | `resolve_output_path` and all persistence destinations | high | mitigate | Resolves symlink components, requires canonical-root containment and raw-tree exclusion; revalidated after `mkdir` and immediately before every JSON/NPZ/PNG write; `check_targets.py` now performs the same root/raw validation (WR-05, commit `adb186d`) | closed |
| T-01-11 | Tampering | validation-to-write TOCTOU window | medium | mitigate | Path resolution repeated at each concrete destination; raw bytes/metadata reverified in `finally` via a second `snapshot_raw`; residual concurrent-swap risk explicitly documented as low-likelihood for this single-user local pipeline (`01-03-SUMMARY.md`) | closed |
| T-01-12 | Repudiation | `run_pipeline` exception handling | high | mitigate | Second snapshot/comparison lives in `finally`; clean-run exceptions preserved and chained behind integrity failures; an unavailable final audit snapshot is treated as failure; staged output only published atomically on a fully clean run (CR-02, commit `f8dcf01`) | closed |
| T-01-13 | Denial of service | SHA-256 snapshot over the full raw tree | low | accept | Hashing cost is bounded in fixture tests and is an intentional trade-off for protecting irreplaceable inputs; accepted in the originating plan | closed |
| T-01-14 | Tampering | optimized validation scripts | medium | mitigate | Bare `assert` in `check_targets.py` replaced with an always-raising `require()` helper; verified green under both normal and `python -O` execution (CR-01, commit `9ddf9f6`) | closed |
| T-01-SC | Tampering | pip installs (all 3 plans) | high | mitigate | No packages installed during Phase 1; `requirements.txt` unchanged since `8914567` (initial release); no new/[ASSUMED]/[SUS] packages introduced | closed |

*Status: open · closed · open — below {block_on} threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01 | T-01-03, T-01-07 | Competition-restricted raw dataset (`data/raw/**`, Git-LFS tracked) is present in this repository's git history (commit `831987c`, pre-dating Phase 1) and pushed to the public GitHub remote `NukaW0rld/nsf-fmrg-data-challenge`, contradicting `DATA_USE_LICENSE.md`'s "no unofficial mirrors" clause. Not introduced by any Phase 1 commit. Severity is `medium` per the originating plan's threat model and falls below the configured `security_block_on: high` gate, so it does not block Phase 1 advancement. User was notified directly during this audit and chose to remediate the repository (visibility / history / dataset-owner contact) separately, outside this workflow. | User (khoa2002piano@gmail.com) | 2026-07-19 |
| AR-02 | T-01-13 | SHA-256 hashing of the full `data/raw/` tree on every pipeline run is a bounded, intentional cost accepted at plan time to protect irreplaceable inputs; no external actor can trigger this locally-run pipeline, so DoS impact is self-inflicted at worst. | Plan 01-03 author (plan-time) | 2026-07-19 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-07-19 | 16 (15 unique + T-01-SC deduped across 3 plans) | 14 | 2 (accepted, non-blocking) | Claude (gsd-secure-phase, L1 grep-depth verification against implementation) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed (blocking threats; 2 non-blocking accepted risks remain open by design)
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-07-19
