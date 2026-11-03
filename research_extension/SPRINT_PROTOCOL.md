# Final scientific strengthening protocol

Exploratory protocol recorded before the sprint analyses. Existing concentration
and headline metrics were already inspected. This is not preregistration.

- Inputs: frozen V3/V4 development OOF predictions only. No fitting or threshold
  selection. Preserve all V1–V4 directories and the deployed estimator.
- Sampling control: tabulate all 672 stations, including zero-event stations.
  For minimum station sample counts 1, 10, 30, 100, retain observed station
  counts n_s and simulate K_s ~ Binomial(n_s, pooled event rate), independently,
  20,000 times. Compare observed event-share HHI with the null distribution;
  report null mean/95% reference range and add-one Monte Carlo tail fraction.
  This null is a sampling-intensity benchmark with independent, constant-rate
  observations. Temporal clustering, nonrandom monitoring, and changing case
  mix can violate it; a small tail fraction is not evidence of geographic risk.
- Uncertainty: 5,000 paired nonparametric bootstrap draws of 672 complete
  stations with replacement, seed 20261103. Aggregate sufficient statistics
  preserve every within-station row and pair all models on the same draw.
  Percentile 95% intervals are descriptive development uncertainty conditional
  on the fixed fitted OOF predictions, not retraining uncertainty. Missing
  denominators remain undefined and their counts are reported.
- Costs: fixed FN:FP ratios 1,2,5,10,25,50; all three model pairs. Report cost
  difference per 10,000 observations and bootstrap percentile intervals plus
  the fraction of replicates where the first model has lower cost. The latter
  is bootstrap stability, not a posterior probability or independent test.
- Time: the existing four bands; report n, station count, prevalence, target
  mean/SD/quantiles and overall/low-DO error. Continue the same-station sensitivity.
  These estimates concern contemporaneous OOF predictions, not forward validation.
- Reproduction: record HEAD, package versions, input hashes, commands, stdout,
  stderr, exit codes, every unittest outcome and historical file comparison.
  Raw data availability determines the evidence layer; skips are never passes.
