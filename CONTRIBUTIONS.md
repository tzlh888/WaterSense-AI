# Contributions

Author: Tang Zeluohe

This file answers the eight contribution questions listed in research_upgrade_v3/final_closeout/RESEARCH_CONTRIBUTION_STATEMENT.md. It covers this repository (WaterSense AI) only.
Labels: [self-report] = no contemporaneous record exists; [repository] = a repository file exists, but it does not show whose idea it was.
Last updated 2026-11-23. Drafted with AI help (see AI_DISCLOSURE.md); the facts come from the author's own answers.

## Role
The idea came from a team discussion at the SDG OpenHack hackathon in December 2025 (participation certificate; no award). The hackathon team members did not take part in developing this repository. [self-report]
After the hackathon the author kept exploring the idea alone and led this repository alone: no other person contributed code, data, decisions or interpretation to it. [self-report]
The author did not write the core model code and does not claim to have originated any specific method.

## The eight items
1. Files personally written or materially revised: none claimed. The author described requirements in natural language and AI tools generated most of the code, tests and documentation. The author did not read all code line by line and made some edits but cannot recall which. [self-report]
2. Who first proposed the low-DO question, the 4 mg/L definition, the weighting hypothesis, the nested station-grouped design, the qualification constraints and the stopping rule: the general idea came from the SDG OpenHack team discussion; the specific elements were developed in discussion with AI tools. The station-grouped evaluation was proposed during these AI-assisted discussions; the author did not identify the leakage problem independently. For the other elements the author cannot say who proposed each first and claims no originality. The qualification thresholds (10% overall-MAE guard, 0.30 precision floor) are human-set values with an undocumented origin. [self-report]
3. Steps personally performed (data acquisition, cleaning, debugging, running experiments, reviewing results): the code and most experiments were generated and run by AI tools. The author ran the test suites in the terminal and opened the raw data and output files to check them. [self-report]
4. Raw records and plots inspected, failure cases independently checked: the author opened the raw data and output files and reviewed the AI-written result summaries and figures. Specific failure cases were not independently checked: the 17 missed low-DO observations in the 2025 test and the 94 mg/L source value were not checked by the author. [self-report]
5. Anyone else who supplied code, data, decisions or interpretation to this repository: no. The original idea came from the SDG OpenHack team discussion; team members did not take part in developing the repository. [self-report]
6. Role of AI tools: Codex (desktop app) generated most of the code, tests, experiment runs, figures and documentation; ChatGPT (web) supported research discussion, experiment design and result analysis; Claude helped review and draft the disclosure files in November 2026. "Senior ML Research Engineer" in research_upgrade_v3/RESEARCH_DECISION_LOG.md is a role the author assigned to the AI in its instructions, not a person. [self-report]
7. AI outputs personally validated before being kept: the code and most experiments were generated and run by AI tools. The author ran the test suites in the terminal and opened the raw data and output files to check them. No claim is made that the author independently reproduced the results. [self-report]
8. Timeline and earlier work: the idea came from the SDG OpenHack hackathon in December 2025; after it the author kept exploring the direction alone, and that exploration is not part of this repository. Building this repository started at the end of September 2026: the oldest project files on the author's disk date from 2026-09-30 and the first public commit is dated 2026-10-02 (file dates can change when files are copied). [self-report]

## Level of involvement by component (self-assessed, not independently verified)
L2 = AI-generated; the author understands the general idea but has not verified the implementation or the content line by line.
L3 = AI-generated; the author cannot explain the implementation.

| Component | Level |
|---|---|
| Data cleaning | L2 |
| Station-grouped outer cross-validation | L2 |
| V3 weighting and inner selection code | L3 |
| Clustered bootstrap | L2 |
| Station-concentration (HHI) analysis | L2 |
| 2025 evaluation and freeze | L2 |
| Streamlit application | L2 |
| Manuscript text | L2 |

## What the author could explain from memory (self-report; Q&A of 2026-11-06, checked against the repository afterwards)
- why station grouping is used instead of random row splits;
- why a threshold must not be both chosen and evaluated on the same predictions;
- why the 2025 precision of 1.00 is not reliable evidence (three positive predictions at one station; recall 3/20);
- why the bootstrap resamples whole stations and what "paired" means;
- the V3 selection procedure (four inner folds, 128 candidate configurations, an eligibility gate followed by a lexicographic ranking); this was answered after the topic had already come up in the discussion.
The same Q&A found inaccuracies, for example the fold splitter was misnamed; those details are not claimed.
