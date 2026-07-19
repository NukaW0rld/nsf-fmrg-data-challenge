# External Integrations

**Analysis Date:** 2026-07-19

## APIs & External Services

**Data Hosting:**
- Zenodo - raw multimodal dataset (thermal `.mat`, SEM `.png`/`.tif`, Bruker/Wyko `.ASC` height maps) is hosted externally on Zenodo because files are too large for GitHub (`README.md:9-11`). Dataset DOI: `10.5281/zenodo.21285367`. No programmatic API client in code — download is a manual, out-of-band step performed by the participant, then extracted into `data/raw/` following the documented layout (`README.md:117-141`).
  - No SDK/client library used; access is via manual download from the Zenodo web UI/DOI link.

**Competition Submission Portal:**
- Qualtrics - final submissions (report PDF, code, slide deck as a zip) are submitted through a Qualtrics form link (`README.md:29`, `README.md:298-300`). Not integrated into code; purely a manual, human-driven submission workflow.

**Community/Support:**
- Discord - competition organizers post clarifications in a competition Discord channel (`README.md:149`). No bot/API integration; referenced only as documentation provenance ("Organizer clarification (Discord, July 17, 2026)").

## Data Storage

**Databases:**
- None. No SQL/NoSQL database, ORM, or DB client of any kind is used in this repository.

**File Storage:**
- Local filesystem only. All data is read from and written to local paths under `data/raw/` (thermal `.mat` via `scipy.io.loadmat`/`h5py`, SEM images via `PIL.Image`, height maps via manual ASCII parsing) and `processed_data/` (output videos from `scripts/run_thermal_video_export.py`). No cloud storage buckets (S3, GCS, Azure Blob) are referenced in code.

**Caching:**
- None (aside from standard Python `__pycache__/*.pyc` bytecode caching, which is not application-level caching).

## Authentication & Identity

**Auth Provider:**
- None. No authentication, authorization, API keys, or credentials are used anywhere in the codebase. This is a local data-processing toolkit with no network-facing services.

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry, error-tracking SDKs, or similar).

**Logs:**
- None structured. The only runtime output is a `print()` statement in `scripts/run_thermal_video_export.py:78` reporting the saved video path. No logging framework (`logging` module) is used.

## CI/CD & Deployment

**Hosting:**
- Not applicable. This is a data/code repository for a research competition, not a deployed service. Notebooks are designed to run either locally or in Google Colab (`README.md:395`).

**CI Pipeline:**
- None. No `.github/workflows/`, `.gitlab-ci.yml`, or other CI configuration found in the repository.

## Environment Configuration

**Required env vars:**
- None. No environment variables are read anywhere in the code.

**Secrets location:**
- Not applicable — no secrets, credentials, or API keys are used by this codebase.

## Webhooks & Callbacks

**Incoming:**
- None.

**Outgoing:**
- None.

## Data Sources (domain-specific, not software integrations)

These are physical instruments whose output files are consumed by the code, not software/API integrations:
- Stratonics ThermaViz melt-pool sensor - source of thermal `.mat` files (`data/dataset_readme.txt:6`)
- Zeiss EVO MA10 SEM system - source of SEM images in `data/raw/sem/SEM_<track_id>/PlainImages/` (`data/dataset_readme.txt:7`)
- Bruker ContourGT-K white-light 3D optical profilometer - source of Wyko `.ASC` height-map files parsed in `src/nsf_fmrg_data.py:144-202` (`data/dataset_readme.txt:8`)

---

*Integration audit: 2026-07-19*
