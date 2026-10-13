# Legacy Link Resolution

Date: 2026-10-13

## Scope

This audit examined the two unresolved repository-relative links identified after the `research-upgrade-v3` branch was published. Both occurred in historical portfolio documents that remain publicly readable and both pointed to `docs/application_materials.md`, a path that does not exist in the current tree or any reachable Git revision.

## Resolution

| Source | Classification | Previous target | Resolution |
|---|---|---|---|
| `reports/interview_preparation.md` | ACTIVE | `../docs/application_materials.md` | Replaced with `../research_upgrade_v3/final_closeout/TECHNICAL_INTERVIEW_QA.md`, the existing final interview document for the low-DO study. |
| `reports/portfolio_web_copy.md` | ACTIVE | `../docs/application_materials.md` | Replaced with `../research_upgrade_v3/final_closeout/ONE_PAGE_RESEARCH_SUMMARY.md`, the existing current publication summary. |

No document was invented or reconstructed. The surrounding descriptions were narrowed so they accurately describe the replacement targets. No model, data, experiment configuration, frozen result, research output, or source hash was changed.

## Result

The two active links now resolve within the repository. WaterSense has no documented legacy-link exception from this audit.
