#!/usr/bin/env python3
"""Reproduce sampling controls and paired cluster uncertainty from frozen OOF rows."""
import json
import platform
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_portfolio_analysis import load_and_verify
from src.portfolio_analysis import PERIOD_EDGES, PERIOD_LABELS, sha256_file

OUT = ROOT / 'research_extension/sprint'
SEED = 20261103
MODELS = ['baseline', 'weighted', 'classifier']


def sampling_null(n, k, draws=20000, seed=SEED):
    n, k = np.asarray(n), np.asarray(k)
    if (n <= 0).any() or (k < 0).any() or (k > n).any() or k.sum() == 0:
        raise ValueError('Invalid station counts or no events')
    simulated = np.random.default_rng(seed).binomial(n, k.sum() / n.sum(), size=(draws, len(n)))
    totals = simulated.sum(axis=1)
    valid = totals > 0
    hhi = (simulated[valid].astype(float) ** 2).sum(axis=1) / totals[valid] ** 2
    observed = float(np.square(k / k.sum()).sum())
    return hhi, dict(observed_hhi=observed, null_mean=float(hhi.mean()),
        null_lower=float(np.quantile(hhi, .025)), null_upper=float(np.quantile(hhi, .975)),
        mc_upper_tail=float((1 + (hhi >= observed).sum()) / (len(hhi) + 1)),
        valid_draws=int(valid.sum()), excluded_zero_event_draws=int((~valid).sum()))


def station_stats(frame):
    a = frame.actual_do_mg_l.to_numpy()
    low = a < 4
    pred = frame.predicted_low_do.to_numpy().astype(bool)
    data = pd.DataFrame({'station': frame.station_code, 'n': 1, 'low': low.astype(int),
        'tp': (low & pred).astype(int), 'fp': (~low & pred).astype(int),
        'fn': (low & ~pred).astype(int)})
    if 'predicted_do_mg_l' in frame:
        error = np.abs(frame.predicted_do_mg_l.to_numpy() - a)
        data['ae'] = error
        data['low_ae'] = error * low
    return data.groupby('station').sum().sort_index()


def bootstrap_weights(stations, draws=5000, seed=SEED):
    return np.random.default_rng(seed).multinomial(stations, np.full(stations, 1/stations), size=draws)


def interval(values):
    values = np.asarray(values)
    valid = np.isfinite(values)
    q = np.quantile(values[valid], [.025, .975]) if valid.any() else [np.nan, np.nan]
    return {'lower_95': float(q[0]), 'upper_95': float(q[1]),
            'valid_replicates': int(valid.sum()), 'undefined_replicates': int((~valid).sum())}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    reg, clf, hashes = load_and_verify()
    clf = clf.rename(columns={'dissolved_oxygen_mg_l': 'actual_do_mg_l'})
    frames = {m: reg[reg.variant.eq(m)].copy() for m in MODELS[:2]}
    frames['classifier'] = clf
    for model, frame in frames.items():
        actual = frame.actual_do_mg_l < 4
        if not np.array_equal(actual.astype(int), frame.actual_low_do.astype(int)):
            raise ValueError(f'{model}: actual low-DO label mismatch')
        predicted = (frame.predicted_low_do_probability >= .5) if model == 'classifier' else (frame.predicted_do_mg_l < 4)
        if not np.array_equal(predicted.astype(int), frame.predicted_low_do.astype(int)):
            raise ValueError(f'{model}: frozen decision label mismatch')
        if not frame.groupby('station_code').outer_fold.nunique().eq(1).all():
            raise ValueError(f'{model}: station crosses outer validation folds')
    stats = {m: station_stats(f) for m, f in frames.items()}
    base = stats['baseline']
    for data in stats.values():
        pd.testing.assert_series_equal(data.n, base.n)
        pd.testing.assert_series_equal(data.low, base.low)
    station = base[['n', 'low']].rename(columns={'n': 'observations', 'low': 'low_do_events'})
    station['low_do_rate'] = station.low_do_events / station.observations
    station['sampling_share'] = station.observations / station.observations.sum()
    station['event_share'] = station.low_do_events / station.low_do_events.sum()
    station['event_to_sampling_share'] = station.event_share / station.sampling_share
    station.to_csv(OUT / 'station_sampling_rates.csv')
    null_rows = []
    first_null = None
    for minimum in [1, 10, 30, 100]:
        subset = station[station.observations >= minimum]
        null, result = sampling_null(subset.observations, subset.low_do_events)
        null_rows.append({'minimum_observations': minimum, 'stations': len(subset),
            'observations': int(subset.observations.sum()), 'events': int(subset.low_do_events.sum()),
            'sampling_hhi': float(np.square(subset.observations / subset.observations.sum()).sum()), **result})
        if minimum == 1:
            first_null = null
    null_table = pd.DataFrame(null_rows)
    null_table.to_csv(OUT / 'sampling_null_sensitivity.csv', index=False)
    pd.DataFrame({'hhi': first_null}).to_csv(OUT / 'null_hhi_replicates.csv.gz', index=False, compression={'method':'gzip','mtime':0})

    weights = bootstrap_weights(len(base))
    totals = {m: weights @ data.to_numpy(dtype=float) for m, data in stats.items()}
    draws, point, metrics_rows = {}, {}, []
    for model, data in stats.items():
        cols = list(data.columns)
        values = {c: totals[model][:, i] for i, c in enumerate(cols)}
        observed = data.sum()
        with np.errstate(divide='ignore', invalid='ignore'):
            draws[model] = {'recall': values['tp']/values['low'],
                'precision': values['tp']/(values['tp']+values['fp'])}
            point[model] = {'recall': observed.tp/observed.low,
                'precision': observed.tp/(observed.tp+observed.fp)}
            if model != 'classifier':
                draws[model].update(mae=values['ae']/values['n'], low_do_mae=values['low_ae']/values['low'])
                point[model].update(mae=observed.ae/observed.n, low_do_mae=observed.low_ae/observed.low)
        for metric, samples in draws[model].items():
            metrics_rows.append({'model': model, 'metric': metric, 'estimate': point[model][metric], **interval(samples)})
    for metric in draws['baseline']:
        metrics_rows.append({'model': 'weighted_minus_baseline', 'metric': metric,
            'estimate': point['weighted'][metric]-point['baseline'][metric],
            **interval(draws['weighted'][metric]-draws['baseline'][metric])})
    metrics = pd.DataFrame(metrics_rows)
    metrics.to_csv(OUT / 'cluster_bootstrap_metrics.csv', index=False)
    cost_rows, cost_replicates = [], []
    for ratio in [1, 2, 5, 10, 25, 50]:
        costs, observed_costs = {}, {}
        for model, data in stats.items():
            ix = list(data.columns)
            costs[model] = 10000*(ratio*totals[model][:,ix.index('fn')]+totals[model][:,ix.index('fp')])/totals[model][:,ix.index('n')]
            observed_costs[model] = 10000*(ratio*data.fn.sum()+data.fp.sum())/data.n.sum()
        for first, second in [('weighted','baseline'), ('classifier','baseline'), ('classifier','weighted')]:
            delta = costs[first]-costs[second]
            cost_rows.append({'first': first, 'second': second, 'fn_fp_ratio': ratio,
                'delta_per_10000': observed_costs[first]-observed_costs[second], **interval(delta),
                'bootstrap_fraction_first_lower_cost': float((delta < 0).mean())})
            cost_replicates.append(pd.DataFrame({'first': first,'second':second,'ratio':ratio,'replicate':np.arange(len(delta)), 'delta_per_10000':delta}))
    costs = pd.DataFrame(cost_rows)
    costs.to_csv(OUT / 'cluster_cost_differences.csv', index=False)
    pd.concat(cost_replicates).to_csv(OUT / 'cost_bootstrap_replicates.csv.gz', index=False, compression={'method':'gzip','mtime':0})
    temporal = []
    for model in MODELS[:2]:
        frame = frames[model].copy()
        frame['period'] = pd.cut(pd.to_datetime(frame.sample_date), PERIOD_EDGES, labels=PERIOD_LABELS)
        for period, group in frame.groupby('period', observed=True):
            a = group.actual_do_mg_l
            ae = (group.predicted_do_mg_l-a).abs()
            temporal.append({'model':model,'period':str(period),'observations':len(group),
                'stations':group.station_code.nunique(),'low_do_events':int((a<4).sum()),
                'low_do_prevalence':float((a<4).mean()),'target_mean':a.mean(),'target_sd':a.std(),
                'target_q05':a.quantile(.05),'target_median':a.median(),'target_q95':a.quantile(.95),
                'mae':ae.mean(),'low_do_mae':ae[a<4].mean()})
    temporal = pd.DataFrame(temporal)
    temporal.to_csv(OUT / 'temporal_composition.csv', index=False)

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, axes = plt.subplots(1,2,figsize=(11,4.3))
    axes[0].scatter(station.sampling_share*100,station.event_share*100,s=12,alpha=.6)
    lim=max(station.sampling_share.max(),station.event_share.max())*100
    axes[0].plot([0,lim],[0,lim], '--',color='gray')
    axes[0].set(xlabel='Share of all observations (%)',ylabel='Share of low-DO events (%)',title='Sampling intensity and event concentration')
    axes[1].hist(first_null,bins=50,color='#0B7285')
    axes[1].axvline(null_rows[0]['observed_hhi'],color='#C92A2A',label='Observed HHI')
    axes[1].set(xlabel='Event-share HHI',ylabel='Null simulations',title='Common-rate independent-observation benchmark')
    axes[1].legend()
    fig.tight_layout(); fig.savefig(OUT/'sampling_control.png',dpi=180); plt.close(fig)
    fig, axes=plt.subplots(1,3,figsize=(12,4),sharey=True)
    for ax,(pair,group) in zip(axes,costs.groupby(['first','second'],sort=False)):
        ax.errorbar(group.fn_fp_ratio,group.delta_per_10000,
            yerr=[group.delta_per_10000-group.lower_95,group.upper_95-group.delta_per_10000],fmt='o-',capsize=3)
        ax.axhline(0,color='gray',ls='--'); ax.set_xscale('log')
        ax.set(title=f'{pair[0]} minus {pair[1]}',xlabel='FN / FP cost ratio')
    axes[0].set_ylabel('Cost difference per 10,000 rows (95% cluster interval)')
    fig.tight_layout(); fig.savefig(OUT/'cluster_cost_uncertainty.png',dpi=180); plt.close(fig)
    fig, axes=plt.subplots(1,3,figsize=(12,4))
    t=temporal[temporal.model.eq('baseline')]
    axes[0].bar(t.period,t.observations,color='#0B7285')
    axes[0].set_ylabel('Observations')
    axes[1].plot(t.period,t.low_do_prevalence*100,'o-',color='#C92A2A')
    axes[1].set_ylabel('Measured DO < 4 mg/L (%)')
    axes[2].plot(t.period,t.target_median,'o-',label='Median')
    axes[2].fill_between(np.arange(4),t.target_q05,t.target_q95,alpha=.2,label='5th–95th percentile')
    axes[2].set_ylabel('Measured DO (mg/L)'); axes[2].legend(fontsize=8)
    for ax in axes:
        ax.tick_params(axis='x',rotation=35)
    fig.suptitle('Changing temporal composition: descriptive development data')
    fig.tight_layout(); fig.savefig(OUT/'temporal_composition.png',dpi=180); plt.close(fig)
    summary = {'seed':SEED,'bootstrap_draws':len(weights),'null_draws':20000,'input_hashes':hashes,
        'sampling_control':null_rows,'metrics':metrics.to_dict('records'),'costs':costs.to_dict('records')}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'status':'PASS','stations':len(base),'sampling_control':null_rows},indent=2))


if __name__ == '__main__':
    main()
