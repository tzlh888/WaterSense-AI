# Data attribution and release boundaries

Contains public sector information licensed under the
[Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).

Historical monitoring data: OpenDataNI / Northern Ireland Environment Agency,
[River Water Quality Monitoring 1990–2024 — All Parameters](https://www.data.gov.uk/dataset/15ec8080-ee1c-469b-858e-546d2fb57c27/riverwaterqualitymonitoring-1990to2024-allparameters13).
2025 data: DAERA / NIEA,
[DAERA/26-784 Annex A](https://www.daera-ni.gov.uk/publications/daera26-784-river-water-quality-monitoring-data-all-northern-ireland-2025),
published 26 October 2026.
England compatibility metadata/observations: Environment Agency,
[Water Quality Explorer](https://www.data.gov.uk/dataset/583e771f-1af6-4934-b8f0-28f1d1ddd48c/water-quality-explorer),
under the catalogue's OGL terms. There is no agency endorsement of this project.

The repository MIT licence covers project software and documentation; it does
not replace source-data terms or the rights in cited papers. New figures are
generated from project analysis rather than copied publisher illustrations.

DAERA's [Crown copyright policy](https://www.daera-ni.gov.uk/articles/crown-copyright-daera)
permits reuse with attribution, but excludes personal data, logos and certain
third-party/OSNI mapping rights. This branch adds no agency logos or OSNI map
artwork. It does not assume the licence grants rights to such excluded content.
Official public measurement/station identifiers in derived tables describe
environmental samples; they are not claims about individual people.

Full historical/2025 raw CSVs, reconstructed tables, local download bodies and
baseline worktrees remain ignored. Newly added station-context data contain
date, DO, saturation and temperature only, with no sampler/person identifiers.
Saved prediction rows and public API snapshots already in the branch are derived
public environmental evidence; hashes and provenance identify their sources.
No private API credentials or user home paths are intended for these artifacts.
Git identities and prior history are preserved, not certified as human authorship.

The final audit scans text for private paths and credential patterns and checks
local links. This is a bounded engineering check, not a certification that all
possible personal information has been eliminated. Before approving remote
publication, the owner should inspect the staged files, attribution and Git
identity and confirm willingness to publish the derived records.
