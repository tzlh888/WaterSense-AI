# Research originality, negative results, and limitations

## What is original in the portfolio

The project does not claim a new machine-learning algorithm. Its originality is
in the research design and synthesis: it turns a routine regression problem into
an auditable study of reliability under station dependence, rare-event
imbalance, and competing error objectives.

The strongest contributions are:

- combining station, time, spatiotemporal, and basin separations while keeping
  their interpretations distinct;
- designing a frozen nested station-grouped low-DO experiment with explicit
  qualification and stopping rules;
- preserving row-level evidence that permits exact post-run metric and identity
  reconstruction;
- separating the complete selected-procedure effect from exploratory
  weighting-specific evidence;
- quantifying rare-event concentration across monitoring stations with HHI and
  an inverse effective representation count; and
- deriving transparent cost breakpoints instead of declaring one error profile
  universally superior.

These are meaningful undergraduate-level contributions because they show
scientific judgment: the work asks what the model score estimates, what the
data cannot identify, and what evidence is required next.

## Why the negative results matter

The study preserves several results that make the portfolio more credible:

1. The V3 selected procedure improves low-DO MAE and recall but worsens overall
   MAE, precision, and false alarms.
2. The fixed V4 classifier reaches high recall only with 9,517 false positives
   and 0.0684 precision.
3. Historical prediction intervals have near-nominal aggregate coverage but
   very poor low-DO coverage.
4. Rare events are concentrated, so row counts overstate the diversity of
   geographic support.
5. The official data checked in V4 were not independent of historical data, so
   external evaluation was correctly stopped.
6. A historical report omitted weight 2 from the written candidate list; an
   additive erratum corrects the documentation without rewriting the record.

These findings demonstrate that research quality is not the same as maximizing
one metric. A result that changes or rejects a tempting conclusion is still a
scientific result.

## Limitations that must remain visible

- There is no independent external confirmation.
- Data come from one regional monitoring programme.
- Temperature, flow, and catchment context are missing.
- Repeated observations and reused splits are statistically dependent.
- V3 does not isolate the full outer effect of weighting alone.
- V4 uses a different objective and reused development data.
- Time-slice analysis is descriptive, not a forecast evaluation.
- No application owner has supplied a defensible false-negative/false-positive
  cost ratio.
- The system is not validated for warnings, regulation, or deployment.
- The applicant’s exact independent contribution requires human confirmation.

## Defensible originality statement — draft pending owner confirmation

“The project’s originality lies in converting a dissolved-oxygen prediction
task into a reliability study. I focused on how station dependence, rare-event
concentration, and conflicting error objectives change the meaning of model
performance. I preserved negative outcomes and separated reproducible
development evidence from claims that require genuinely new data.”

Use this statement only after confirming that it accurately describes the
applicant’s own decisions and work.
