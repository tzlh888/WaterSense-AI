# Reference and source-link check

All nine manuscript references retain primary-source links. HTTP transport
results are in [source_and_link_probes.json](source_and_link_probes.json);
[reference_metadata.json](reference_metadata.json) retains a separate Crossref
registry query. HTTP 403/429 are recorded as access/rate limits, not evidence
that the underlying paper is absent.

| Reference | Bibliographic check |
|---|---|
| Roberts et al., Ecography 40, 913–929 | Crossref title/authors/volume/pages match; [publisher page](https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.02881) also verified through web retrieval |
| Breiman, Random Forests, Machine Learning 45, 5–32 | DOI resolves with HTTP 200 to publisher; Crossref request rate-limited (429) |
| Pedregosa et al., JMLR 12, 2825–2830 | [Official JMLR page](https://www.jmlr.org/papers/v12/pedregosa11a.html) returns 200 |
| Saito and Rehmsmeier, PLOS ONE e0118432 | Crossref title/authors/volume match; DOI publisher response 200 |
| Lei et al., JASA 113, 1094–1111 | Crossref title, five authors, volume/pages match; publisher HTTP 403 |
| OpenDataNI historical source | Official catalogue HTTP 200; byte-exact source recovery is documented separately |
| Field and Welsh, JRSS B 69(3), 369–390 | [Publisher search record](https://rss.onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-9868.2007.00593.x) matches title, authors and pages; direct DOI blocked and Crossref rate-limited |
| Diggle, Menezes and Su, JRSS C 59(2), 191–232 | [Publisher search record](https://rss.onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-9876.2009.00701.x) matches title, year and pages; direct DOI blocked and Crossref rate-limited |
| DAERA/26-784 (26 October 2026) | Official release and Annex A HTTP 200; re-downloaded CSV byte-identical |

The methodological citations support validation, bootstrap and monitoring
assumptions; none is cited as direct evidence for WaterSense's numerical
results. Those numbers come from committed predictions and audit outputs.
No paywall bypass, fabricated citation or new claimed external validation
was used.
