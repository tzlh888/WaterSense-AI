# WaterSense portfolio extension — analysis protocol

**Status:** fixed for the formal repository analysis on 2026-11-03. This is an
exploratory protocol written after feasibility inspection of the saved column
schemas and headline values. It is **not** a preregistration and it does not
create a new validation population.

## Evidence boundary

The analysis may read only the frozen V3 outer out-of-fold regression
predictions and the frozen V4 outer out-of-fold classifier predictions. It may
not refit a model, tune a threshold, alter fold membership, inspect a protected
legacy holdout as if it were fresh, or overwrite V1–V4 artifacts. All results
remain development-only.

## Questions and fixed methods

1. **Can headline results be reconstructed?** Recompute membership, fold,
   regression, and confusion-matrix quantities from row-level predictions and
   fail on hash or identity mismatch.
2. **How concentrated are low-DO events across stations?** Count measured
   `DO < 4 mg/L` events by station and report top-1/top-5/top-10/top-20 shares,
   the Herfindahl concentration index, its inverse effective-station count,
   and the number of stations with one event. These are descriptive, not
   population estimates.
3. **How does error vary over time?** Use fixed calendar bands 1990–1999,
   2000–2009, 2010–2019, and 2020–2024. Report pooled row-weighted MAE and a
   balanced-station sensitivity analysis: station-macro MAE among stations
   represented in all four bands. Because models were fit with observations
   from all eras outside each held-out station, this is **not** prospective
   temporal validation or forecasting.
4. **When do error-cost preferences change?** For the V3 baseline, V3 selected
   procedure, and V4 classifier, define hypothetical cost
   `r × FN + FP`, where `r = C_FN / C_FP`. Derive pairwise break-even ratios
   algebraically from saved confusion counts and display a fixed scenario grid
   `1, 2, 5, 10, 25, 50`. Costs are hypothetical and not ecological,
   regulatory, or financial estimates.

## Outputs

The formal run writes CSV tables and an analysis report under
`research_extension/`, three figures under `figures/`, and a machine-readable
verification summary under `audits/`. Any failed invariant makes the command
exit nonzero.

## Limitations fixed before reporting

- Repeated observations within station are dependent.
- The station concentration summary does not measure geographic independence.
- Time-band comparisons mix changing measurement practice and unobserved
  covariates; the balanced-station check reduces but does not eliminate this.
- The V4 classifier uses a different objective and cannot be called an upgrade
  over V3.
- No analysis here is independent external confirmation or deployment evidence.
