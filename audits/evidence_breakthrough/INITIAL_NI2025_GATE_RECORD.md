# Initial gate failure and pre-performance resolution

The first `python3 scripts/validate_ni2025.py freeze` attempt returned
`ValueError: Duplicate full sample identity` before a FREEZE file existed and
before any prediction. Metadata inspection found two nonidentical source rows
at station 10546, 03/03/2025, 09:00, depth 0. Sampler metadata differed.

The protocol was amended before performance access to exclude both members,
not pick or average a record. The subsequent freeze records 2 excluded conflict
rows and 3,490 eligible targets. Both excluded rows had missing DO; this does
not conceal a selected performance exclusion.

This record is transcribed from the initial tool execution and metadata audit,
not represented as an independently timestamped registration or human signature.
Commit `2a55e5a` preserves the actual final freeze before prediction.
