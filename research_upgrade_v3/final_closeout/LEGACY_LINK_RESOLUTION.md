# Legacy Link Resolution

Date: 2026-10-13

## Scope

This audit examined the two unresolved repository-relative links identified after the `research-upgrade-v3` branch was published. Both occurred in historical portfolio documents that remain publicly readable and both pointed to `docs/application_materials.md`, a path that does not exist in the current tree or any reachable Git revision.

## Resolution

| Source | Classification | Previous target | Resolution |
|---|---|---|---|
| `reports/interview_preparation.md` | ACTIVE | `../docs/application_materials.md` | Replaced with `../research_upgrade_v3/final_closeout/TECHNICAL_INTERVIEW_QA.md`, the existing final interview document for the low-DO study. **Status as of 2026-11-05: source file moved out of the public repository (no longer public). This resolution applied only before the move.** |
| `reports/portfolio_web_copy.md` | ACTIVE | `../docs/application_materials.md` | Replaced with `../research_upgrade_v3/final_closeout/ONE_PAGE_RESEARCH_SUMMARY.md`, the existing current publication summary. **Status as of 2026-11-05: source file moved out of the public repository (no longer public). This resolution applied only before the move.** |

No document was invented or reconstructed. The surrounding descriptions were narrowed so they accurately describe the replacement targets. No model, data, experiment configuration, frozen result, research output, or source hash was changed.

## Result

The two active links now resolve within the repository. WaterSense has no documented legacy-link exception from this audit.

## Update 2026-11-05: source files moved out of the public repository

Seven first-person application, interview-preparation, demonstration and portfolio drafts were removed from the public working tree with `git rm`:

- `reports/application_description.md`
- `reports/psl_project_description.md`
- `reports/project_reflection.md`
- `reports/interview_preparation.md`
- `reports/demo_script.md`
- `reports/cv_description.md`
- `reports/portfolio_web_copy.md`

Two of them, `reports/interview_preparation.md` and `reports/portfolio_web_copy.md`, are the sources in the 2026-10-13 resolution table above. Their repaired links no longer exist in the public tree because the files themselves are no longer public; the October resolution applied only before this move.

A repository-wide search found no other link, script, test or manifest that referenced the seven files, apart from the two records in this directory that are annotated above and in `LINK_EXCEPTION_REGISTRY.csv`. `MAIN_MERGE_DIFF_AUDIT.md` refers to this resolution record and its registry as a historical audit and is left unchanged. No model, data, experiment configuration, frozen result, research output or source hash was changed.

This change does not rewrite Git history. Earlier commits, branches and pull requests that predate this change still contain the removed files.
