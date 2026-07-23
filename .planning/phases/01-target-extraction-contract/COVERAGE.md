# API Coverage — Phase 01 (target-extraction-contract)

## Why a declaration, not a matrix

The deterministic api-coverage detector matched the verb `integrates` against the noun `api` on a
sentence in `01-15-PLAN.md`'s own assumptions ("This phase integrates no external API, SDK, or
service…") — a self-referential false positive, not a real integration surface. Per the capability
contract, fabricating a coverage matrix for a surface that does not exist would be worse than the
absent file, so this phase declares its no-external-API status directly instead.

No external API integration: this phase reads local Wyko .ASC height maps and writes only local artifacts under processed_data/targets/, with no network call, SDK, or external service anywhere in the extraction pipeline.
