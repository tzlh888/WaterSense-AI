# Main Merge Diff Audit

Date: 2026-10-13

## Compared revisions

- Base: `main` / `origin/main` at `3553b29ff104918b12da8c84d2c9a8c5ed032e18`
- Reviewed research branch before this link-resolution commit: `eb24304143f9250342106e27a7344d4b74884f7d`
- Relationship: the research branch is a direct three-commit descendant of the base; the remote base has no unknown update.

## Diff findings

- The previously reviewed branch diff contains 94 paths: 91 additions and 3 modifications, with no deletions.
- This Stage 4A change adds four governance records and modifies only the two historical documents listed in `LINK_EXCEPTION_REGISTRY.csv`.
- No model, raw data, historical metric, frozen protocol, experiment configuration, result table, figure, or provenance hash was modified by Stage 4A.
- No merge conflict was detected against `origin/main`.
- `RESEARCH_CONTRIBUTION_STATEMENT.md` is not tracked and is not part of the merge diff.
- No private absolute path, credential pattern, prohibited development-workspace path, or newly redistributed third-party binary was found in the public diff.
- The WaterSense README retains the development-only nested-CV interpretation and the documented costs: low-DO MAE `3.3235 → 2.3613 mg/L`, recall `0.1293 → 0.3641`, overall MAE `0.8797 → 0.9516 mg/L`, precision `0.7903 → 0.5576`, and false positives `26 → 219`.
- The remotely verified LFS model remains outside this documentation-only change. Its verified size is 175,556,503 bytes and SHA-256 is `7434cbd29bf6a1b2b624ef3283d073212a82ec72a839d7a050bb912b8506f44f`.
- Post-change verification passed all 88 repository tests and all 47 checked repository-relative Markdown links.

## Personal-claim review

The README contains no first-person sentence. It does state that AI-assisted implementation and the author's research direction are documented. This is not treated as proof that the owner independently wrote particular code or made every technical decision. The owner should confirm that wording before merge; the untracked contribution statement remains the authoritative unresolved human-review item.

## Assessment

The diff is technically suitable for a pull request after this local commit is pushed under separate authorization. Main merge remains conditional on owner review of personal-contribution wording and normal GitHub branch review.
