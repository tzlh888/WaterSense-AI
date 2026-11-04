# Execution notes and non-successful attempts

- Initial preflight halted before tests because README linked a final report
  that had not yet been written. The report was then created and link checks
  rerun. No tests were marked passed by this preflight.
- First complete test attempt: baseline main 88/88 passed; current main
  109/110 passed with one new evidence-ledger schema failure. The new POST_HOC
  status was outside the fixed vocabulary. It was changed to EXPLORATORY with
  an explicit post-hoc method/boundary; no test was relaxed. Both V4 suites
  retained their README archive failure. Complete first-attempt logs and
  named outcomes are retained in attempt_01.
- First network probes used Python's trust configuration and failed certificate
  verification. The fallback used native curl's system trust with TLS
  verification enabled. No insecure flag or certificate bypass was used.
- Final complete run: current main 110 passed; V4 seven passed/one historical
  failure; baseline main 88 passed, V4 seven passed/one identical historical
  failure. No skips or errors. See test_results.json for named outcomes/times.
- Saved-prediction diagnostic and Git/hash audit use no RNG, fitting or model
  prediction. Existing test suites exercise their small synthetic fitting
  fixtures; they do not tune scientific models or rescore 2025.
- Historical replay, V3/V4 model searches, new external inference, warning
  deployment and paper publication were not executed in this final sprint.
  Earlier historical replay and 2025 scoring remain in their prior records.
- The diagnostic execution JSON and audit command log are retained locally
  here with private workspace prefixes replaced by <REPO>. Raw ignored
  download bodies remain under work/final_release; provenance records
  retain URLs, retrieval times and hashes.
