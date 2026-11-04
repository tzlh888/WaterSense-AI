# Local freeze chronology: verified records and limits

This is a retrospective provenance audit, not preregistration. Machine-readable
evidence is in [freeze_chronology.json](freeze_chronology.json) and
[freeze_commit.txt](freeze_commit.txt); the original execution log remains in
[the prior audit](../evidence_breakthrough/ni2025_evaluation.log).

| Local record | UTC on 2026-11-03 | What it establishes |
|---|---|---|
| FREEZE.json recorded timestamp | 13:50:32.627954 | Locally asserted freeze time |
| Unsigned commit 2a55e5a author/committer | 13:50:57 | Protocol, adapter, cohort and freeze are in a Git commit |
| Prediction file local birth time | 13:50:59.449446 | Local file creation, not inference start |
| RESULTS.json local birth time | 13:50:59.869833 | Local result-file creation |
| Evaluation log local birth time | 13:51:00.026313 | Log creation; no UTC execution-start line |

The adapter, protocol, preprocessing and cohort blobs at
`2a55e5a7d4ff608f34695ef19bf9c1f8c9aa8d63` match their FREEZE.json hashes
and current files. Predictions and RESULTS.json are absent from that commit.
The next result-containing commit is
`00e4cd3ac5781b808b17045d92760a0f9128b5bf` (2026-11-04).
The freeze's git_head points to parent `18cf7d7`, captured before the
freeze commit; it is not a claim that the parent already contained that freeze.

The retained workflow records a commit followed by the evaluation command.
Git, reflog and file metadata are consistent with that sequence. **Their
timestamps are locally controlled, the commit is unsigned, and the execution
log has no independently timestamped start.** File creation follows inference,
so its two-second offset cannot prove inference started after the commit.
Neither these records nor an existing-output guard exclude an earlier
unrecorded run. Do not assert an independently verified first-ever execution.

Conclusion: locally frozen, acquired later-period evidence, with a documented
recorded run; not third-party preregistration, prospective collection or an
independently certified outcome-blind protocol. No timestamp or old log was
rewritten to strengthen this claim. Repeating the chronology script on another
checkout will yield different filesystem times; use this retained snapshot
for the original machine metadata.
