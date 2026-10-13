#!/usr/bin/env python3
"""Generate the saved-evidence-only WaterSense Experiment 1A audit."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.experiment1a_attribution import (  # noqa: E402
    classification_transitions,
    false_positive_range_analysis,
    false_positive_site_analysis,
    low_do_recall_site_analysis,
    matched_inner_weight_pairs,
    outer_error_decomposition,
    pair_outer_predictions,
    prediction_shift_quantiles,
    selected_config_attribution,
    summarize_inner_weight_pairs,
)
from src.phase2b0_readiness import sha256_file  # noqa: E402


EXPERIMENT1 = ROOT / "research_upgrade_v3/experiment1_weighted_regression"
OUTPUT = ROOT / "research_upgrade_v3/experiment1a_attribution"
EXPECTED_HEAD = "3553b29ff104918b12da8c84d2c9a8c5ed032e18"
EXPECTED_CONFIG_CANONICAL_SHA256 = (
    "39d12658f1d63a3a0cd98ee1edd625163c42f8a57f009203fd5e2f04aa660896"
)


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def _canonical_json_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _preflight() -> dict[str, Any]:
    if _git("branch", "--show-current") != "research-upgrade-v3":
        raise RuntimeError("Experiment 1A requires research-upgrade-v3")
    if _git("rev-parse", "HEAD") != EXPECTED_HEAD:
        raise RuntimeError("WaterSense baseline HEAD changed")
    manifest = json.loads(
        (EXPERIMENT1 / "EXPERIMENT1_RUN_MANIFEST.json").read_text(encoding="utf-8")
    )
    if manifest.get("status") != "complete":
        raise RuntimeError("Experiment 1 is not complete")
    if manifest.get("conclusion") != "IMPROVEMENT SUPPORTED":
        raise RuntimeError("Unexpected Experiment 1 conclusion")
    if manifest.get("legacy_benchmark_read") is not False:
        raise RuntimeError("Experiment 1 legacy-test boundary is not intact")
    if (
        manifest.get("experiment_config_canonical_sha256")
        != EXPECTED_CONFIG_CANONICAL_SHA256
    ):
        raise RuntimeError("Experiment 1 canonical config identity changed")
    for relative, expected in manifest["output_sha256"].items():
        path = EXPERIMENT1 / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise RuntimeError(f"Experiment 1 evidence hash mismatch: {relative}")
    config = json.loads((EXPERIMENT1 / "EXPERIMENT1_CONFIG.json").read_text())
    if _canonical_json_hash(config) != EXPECTED_CONFIG_CANONICAL_SHA256:
        raise RuntimeError("Experiment 1 config contents changed")
    return manifest


def _save_table(frame: pd.DataFrame, name: str, *, compressed: bool = False) -> Path:
    path = OUTPUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if compressed:
        frame.to_csv(
            path,
            index=False,
            compression={"method": "gzip", "mtime": 0},
            float_format="%.15g",
        )
    else:
        frame.to_csv(path, index=False, float_format="%.15g")
    return path


def _metric(
    summary: pd.DataFrame, family: str, metric: str, column: str
) -> float:
    row = summary.loc[
        summary["family"].eq(family) & summary["metric"].eq(metric), column
    ]
    if len(row) != 1:
        raise RuntimeError(f"Missing summary row: {family}/{metric}/{column}")
    return float(row.iloc[0])


def _render_reports(
    inner_summary: pd.DataFrame,
    selected_attribution: pd.DataFrame,
    error_by_range: pd.DataFrame,
    transitions: pd.DataFrame,
    recall_sites: pd.DataFrame,
    false_positive_sites: pd.DataFrame,
    false_positive_ranges: pd.DataFrame,
    shift_quantiles: pd.DataFrame,
    comparison: pd.DataFrame,
    uncertainty: pd.DataFrame,
    site_comparison: pd.DataFrame,
) -> None:
    comparison = comparison.set_index("variant")
    baseline = comparison.loc["baseline"]
    weighted = comparison.loc["weighted"]
    delta_ci = uncertainty.loc[
        uncertainty["comparison"].eq("delta_weighted_minus_baseline")
    ].set_index("metric")

    selected_means = selected_attribution.select_dtypes(include=[np.number]).mean()
    weight_low_mae = selected_means[
        "weight_delta_weight8_minus_weight1__pooled_low_do_mae_mg_l"
    ]
    architecture_low_mae = selected_means[
        "architecture_delta_hgb_weight1_minus_anchor__pooled_low_do_mae_mg_l"
    ]
    weight_recall = selected_means[
        "weight_delta_weight8_minus_weight1__pooled_low_do_recall"
    ]
    architecture_recall = selected_means[
        "architecture_delta_hgb_weight1_minus_anchor__pooled_low_do_recall"
    ]
    weight_overall = selected_means[
        "weight_delta_weight8_minus_weight1__pooled_overall_mae_mg_l"
    ]
    architecture_overall = selected_means[
        "architecture_delta_hgb_weight1_minus_anchor__pooled_overall_mae_mg_l"
    ]
    weight_precision = selected_means[
        "weight_delta_weight8_minus_weight1__pooled_low_do_precision"
    ]
    weight_false_positive = selected_means[
        "weight_delta_weight8_minus_weight1__pooled_false_positive_count"
    ]

    low_mae_all = int(
        _metric(
            inner_summary,
            "ALL",
            "low_do_mae_mg_l",
            "beneficial_pair_count",
        )
    )
    recall_all = int(
        _metric(
            inner_summary,
            "ALL",
            "low_do_recall",
            "beneficial_pair_count",
        )
    )
    all_pairs = int(
        _metric(inner_summary, "ALL", "low_do_recall", "matched_pair_count")
    )
    hgb_low_mae_mean = _metric(
        inner_summary,
        "HistGradientBoostingRegressor",
        "low_do_mae_mg_l",
        "mean_delta_weight8_minus_weight1",
    )
    hgb_recall_mean = _metric(
        inner_summary,
        "HistGradientBoostingRegressor",
        "low_do_recall",
        "mean_delta_weight8_minus_weight1",
    )

    improved_mae_sites = int(
        site_comparison.loc[
            site_comparison["low_do_rows"].gt(0),
            "delta_weighted_minus_baseline_low_do_mae_mg_l",
        ].lt(0).sum()
    )
    worsened_mae_sites = int(
        site_comparison.loc[
            site_comparison["low_do_rows"].gt(0),
            "delta_weighted_minus_baseline_low_do_mae_mg_l",
        ].gt(0).sum()
    )
    recall_positive_sites = int(recall_sites["true_positive_gain"].gt(0).sum())
    recall_zero_sites = int(recall_sites["true_positive_gain"].eq(0).sum())
    recall_negative_sites = int(recall_sites["true_positive_gain"].lt(0).sum())
    positive_gain_total = int(
        recall_sites.loc[
            recall_sites["true_positive_gain"].gt(0), "true_positive_gain"
        ].sum()
    )
    recall_top5_share = (
        recall_sites.nlargest(5, "true_positive_gain")["true_positive_gain"].sum()
        / positive_gain_total
    )
    recall_top10_share = (
        recall_sites.nlargest(10, "true_positive_gain")["true_positive_gain"].sum()
        / positive_gain_total
    )

    new_fp_count = int(false_positive_sites["new_false_positive_count"].sum())
    new_fp_sites = len(false_positive_sites)
    fp_top1_share = false_positive_sites.iloc[0]["new_false_positive_count"] / new_fp_count
    fp_top5_share = (
        false_positive_sites.head(5)["new_false_positive_count"].sum() / new_fp_count
    )
    fp_top10_share = (
        false_positive_sites.head(10)["new_false_positive_count"].sum() / new_fp_count
    )
    fp_at_least_6 = int(
        false_positive_ranges.loc[
            false_positive_ranges["actual_do_range_mg_l"].isin(["6-<8", ">=8"]),
            "new_false_positive_count",
        ].sum()
    )
    fp_at_least_8 = int(
        false_positive_ranges.loc[
            false_positive_ranges["actual_do_range_mg_l"].eq(">=8"),
            "new_false_positive_count",
        ].sum()
    )

    net_absolute_error_change = float(
        error_by_range["delta_total_absolute_error_mg_l"].sum()
    )
    low_absolute_error_change = float(
        error_by_range.loc[
            error_by_range["actual_do_range_mg_l"].isin(["<2", "2-<3", "3-<4"]),
            "delta_total_absolute_error_mg_l",
        ].sum()
    )
    high_absolute_error_change = float(
        error_by_range.loc[
            error_by_range["actual_do_range_mg_l"].isin(["6-<8", "8-<10", ">=10"]),
            "delta_total_absolute_error_mg_l",
        ].sum()
    )
    at_least_8_change = float(
        error_by_range.loc[
            error_by_range["actual_do_range_mg_l"].isin(["8-<10", ">=10"]),
            "delta_total_absolute_error_mg_l",
        ].sum()
    )
    shift_median = float(
        shift_quantiles.loc[shift_quantiles["quantile"].eq(0.5)].iloc[0, 1]
    )
    top_fp = false_positive_sites.head(10)[
        ["station_code", "new_false_positive_count", "actual_do_mean_mg_l"]
    ]
    top_recall = recall_sites.head(10)[
        [
            "station_code",
            "low_do_observation_count",
            "baseline_true_positive_count",
            "weighted_true_positive_count",
            "true_positive_gain",
        ]
    ]

    def table(frame: pd.DataFrame) -> str:
        columns = [str(column) for column in frame.columns]
        lines = [
            "| " + " | ".join(columns) + " |",
            "| " + " | ".join("---" for _ in columns) + " |",
        ]
        for values in frame.itertuples(index=False, name=None):
            rendered = [
                f"{value:.6f}" if isinstance(value, (float, np.floating)) else str(value)
                for value in values
            ]
            lines.append("| " + " | ".join(rendered) + " |")
        return "\n".join(lines)

    report = f"""# Experiment 1A Attribution Report

## Executive conclusion

Experiment 1 的 outer-CV `IMPROVEMENT SUPPORTED` 结论针对的是完整的 inner-selected procedure，而不是纯粹的权重因果效应，因为 baseline 是固定 Random Forest，selected procedure 是 weight 8 的 HistGradientBoostingRegressor，模型架构和非权重超参数同时变化。

不过，现有 2,560 条 inner-fold 结果已经包含严格匹配的 weight 1/8 对照，因此无需新训练。对完全相同架构、非权重超参数、inner train/validation stations 和预处理矩阵的 {all_pairs} 个配对，weight 8 的 Low-DO MAE 在 {low_mae_all}/{all_pairs} 个配对中降低，Recall 在 {recall_all}/{all_pairs} 个配对中提高。这构成一致的**探索性权重归因证据**，但不是未受选择影响的 outer-level 确认性估计。

## 1. Attribution audit

| 维度 | Baseline | Selected procedure | 是否相同 |
| --- | --- | --- | --- |
| 模型架构 | RandomForestRegressor | HistGradientBoostingRegressor | 否 |
| 非权重超参数 | 150 trees, leaf 2, max_features 0.8 | outer-specific HGB learning rate/leaves/leaf size/L2 | 否 |
| 样本权重 | 1 | 8 | 否 |
| 开发数据与 folds | 冻结的 119,690 行、672 站点、5×4 folds | 同左 | 是 |
| 特征 | 冻结 full 25 features | 同左 | 是 |
| 预处理 | 每个训练折拟合 median/missing indicators/scaling | 同一训练折拟合并复用于全部候选 | 是 |
| 选择流程 | 固定 anchor，不参与新选择 | inner CV 资格门槛和冻结排序 | 否 |

因此，outer OOF 的 Baseline→Weighted 总差异不能单独归因于 weighting。能够分离权重的证据来自已保存 inner grid 中的 matched weight 1/8 对照。

### 1.1 全冻结网格的 matched weight 对照

- 共有 32 个非权重配置 × 20 inner folds = {all_pairs} 个严格匹配对照。
- 所有 {all_pairs} 对照的 Low-DO MAE 和 Bias 都向有利方向变化；所有 {all_pairs} 对照的 Recall 都提高。
- HGB 子集 320 个配对的平均 weight 8 − weight 1 差异：Low-DO MAE {hgb_low_mae_mean:.4f} mg/L，Recall {hgb_recall_mean:+.4f}。
- 这些 folds 在不同 outer frameworks 中重用站点，不能被当作 {all_pairs} 个独立统计重复；这里只报告方向一致性和描述性效应，不计算伪独立 CI。

### 1.2 对五个最终 selected HGB 配置的描述性分解

在各 outer-training partition 的 pooled inner OOF 中，五个 selected HGB 配置的平均分解为：

| 指标 | HGB weight 1 − RF anchor（架构/超参数部分） | HGB weight 8 − HGB weight 1（权重部分） |
| --- | ---: | ---: |
| Overall MAE | {architecture_overall:+.4f} mg/L | {weight_overall:+.4f} mg/L |
| Low-DO MAE | {architecture_low_mae:+.4f} mg/L | {weight_low_mae:+.4f} mg/L |
| Low-DO Recall | {architecture_recall:+.4f} | {weight_recall:+.4f} |
| Low-DO Precision | not used for simple allocation | {weight_precision:+.4f} |
| False positives per pooled inner OOF | not used for simple allocation | {weight_false_positive:+.1f} |

该分解显示，在 selected configurations 的 inner evidence 中，低氧 MAE 与 Recall 的大部分增益和大部分新增误报都与权重从 1 提升到 8 同向；Overall MAE 代价则主要与 HGB 架构/超参数差异相关。但这仍是选择后的描述性分解，不能当作随机化因果估计。

## 2. Benefit–cost analysis

### 2.1 Low-DO MAE 稳定性

- 五个 outer folds 的 selected procedure 均降低 Low-DO MAE。
- Pooled delta 为 {weighted['low_do_mae_mg_l'] - baseline['low_do_mae_mg_l']:.4f} mg/L；paired site-bootstrap 95% CI [{delta_ci.loc['low_do_mae_mg_l','ci_95_lower']:.4f}, {delta_ci.loc['low_do_mae_mg_l','ci_95_upper']:.4f}]。
- 115 个低氧站点中 {improved_mae_sites} 个 MAE 改善，{worsened_mae_sites} 个恶化。

这支持“开发 CV 内改善稳定”，但不能保证新区域、新年份或新低氧事件中保持相同幅度。

### 2.2 Recall 的独立站点分布

- 净增加 178 个 true positives：179 个 baseline FN 被修正为 TP，同时 1 个 baseline TP 变为 FN。
- {recall_positive_sites}/115 个低氧站点有净 TP 增益，{recall_zero_sites} 个无净变化，{recall_negative_sites} 个净下降。
- 前 5 个站点占全部正向 TP 增益的 {recall_top5_share:.1%}，前 10 个占 {recall_top10_share:.1%}。改善跨多个站点，但并非均匀。

最大 TP 增益站点：

{table(top_recall)}

### 2.3 Overall MAE 恶化来源

总绝对误差增加 {net_absolute_error_change:.1f} mg/L。真实低氧 `<4` 的总绝对误差减少 {-low_absolute_error_change:.1f} mg/L，但真实 DO `>=6` 的总绝对误差增加 {high_absolute_error_change:.1f} mg/L，其中 `>=8` 增加 {at_least_8_change:.1f} mg/L。也就是说，整体 MAE 恶化主要来自大量正常/较高 DO 记录，而不是低氧记录本身。

完整 DO 分层分解在 `OUTER_ERROR_DECOMPOSITION.csv`。

### 2.4 False Positives 的集中程度

Weighted procedure 的 219 个 FP 中，26 个 baseline 已经是 FP，新增 FP 为 {new_fp_count} 个，分布于 {new_fp_sites} 个站点。最大单站占 {fp_top1_share:.1%}，前 5 站占 {fp_top5_share:.1%}，前 10 站占 {fp_top10_share:.1%}；不存在单一站点解释全部误报。

新增 FP 中 {fp_at_least_6}/{new_fp_count} 的真实 DO `>=6`，其中 {fp_at_least_8}/{new_fp_count} 的真实 DO `>=8`。误报并不只集中在 4 mg/L 阈值附近，这些远离阈值的误报是重要风险信号。

最大新增 FP 站点：

{table(top_fp)}

### 2.5 预测分布位移

全体预测的平均 weighted − baseline 位移为 -0.0595 mg/L，中位数为 {shift_median:.4f} mg/L，52.5% 的预测降低。低氧区位移更大：真实 DO `<2` 的平均位移约 -1.3924 mg/L。该变化不是简单的全局常数平移，但存在面向低值的系统性移动，并延伸到部分高 DO 记录。

### 2.6 Precision–Recall 权衡

Recall 从 {baseline['low_do_recall']:.4f} 提高到 {weighted['low_do_recall']:.4f}，FNR 从 {baseline['low_do_false_negative_rate']:.4f} 降至 {weighted['low_do_false_negative_rate']:.4f}；Precision 从 {baseline['low_do_precision']:.4f} 降到 {weighted['low_do_precision']:.4f}，FP 从 {int(baseline['false_positive_count'])} 增至 {int(weighted['false_positive_count'])}。研究上这表明 rare-regime sensitivity 可以提高；应用上是否值得取决于漏报与误报的相对成本，而当前没有冻结的业务成本函数或环境预警容忍阈值。

## 3. Scientific conclusion categories

### Confirmed within development CV

- 冻结的完整 inner-selected procedure 相比固定 RF baseline，在开发集 outer OOF 中改善 Low-DO MAE、Bias、Recall 和 F1。
- 同一流程同时恶化 Overall MAE/RMSE/R²、Precision、FP 和 FPR。
- 改善和代价都跨多个 outer folds/站点出现；配对站点 bootstrap 支持两类方向。
- 这些陈述只覆盖冻结开发站点总体及其 CV 过程。

### Exploratory evidence

- 在现有 inner grid 的 {all_pairs} 个同配置配对中，weight 8 对 Low-DO MAE/Bias/Recall 的方向一致，支持“权重具有独立贡献”。
- 对 selected HGB configurations 的描述性分解显示，权重贡献了大部分低氧收益及误报增加，而架构差异贡献了较大部分 Overall MAE 代价。
- 该分析在模型选择后提出并使用参与选择的 inner metrics，不能升级为新的独立确认。

### Unresolved

- 没有保存 selected HGB weight 1 在 outer validation 上的 matched predictions，因此无法获得不受 inner reuse 影响的 outer-level纯权重效应。
- 无法把 architecture、hyperparameters、weighting 和选择过程的交互完全加性分解。
- 没有应用成本函数判断 +193 FP 与 −178 FN 的净实用价值。
- 权重 8 位于冻结搜索边界；本轮禁止据此扩展到 16/32。
- 当前输入是同期化学变量，模型不是未来事件预报器。

### Requires independent external validation

- 新站点、新 basin、新年份和新的低氧事件上的 MAE、Recall、Precision 与误报模式。
- 环境变化、测量流程差异和未观测变量条件下的稳定性。
- 任何部署、预警可靠性、真实环境风险降低或业务成本优势声明。

## 4. Research decisions

### A. 加权本身的独立贡献是否得到支持？

**得到一致但探索性的支持，尚未得到独立确认。** 同配置 inner pair 的方向高度一致，且 selected-config 分解显示权重是低氧收益的主要来源；但 Experiment 1 的正式 outer 比较仍被架构和选择流程混杂。

### B. 当前模型是否更适合低氧识别研究？

**在开发 CV 的研究用途上是。** 它提供更高 Recall、更低 Low-DO MAE/Bias 和更高 F1，适合继续研究低氧敏感性机制；但 Precision、FP 和整体回归损害使其不能被称为更适合部署的模型。

### C. 哪些代价仍不可接受或没有标准？

Overall MAE 相对恶化 8.17%，Precision 下降 0.2327，FP 增加 193，且 43.0% 的新增 FP 真实 DO `>=6`。这些是否可接受没有应用容忍标准、误报成本、漏报成本或决策阈值，因此不能作应用性接受判断。

### D. 是否值得继续 Two-stage Model？

**科学上值得，但优先级不高于独立数据。** Two-stage 可直接研究分类敏感性与连续回归的分离，并可能显式控制 Precision–Recall；若继续，必须沿用已冻结协议并将使用同一开发 folds 的结果标为探索性。本轮不启动。

### E. 若停止 WaterSense 模型开发，是否已形成诚实且可解释的本科研究成果？

**是。** 研究已经包含可追溯数据身份、严格站点隔离、负面结果、预注册门槛、nested CV、站点 bootstrap、完整预测、可复算指标、混杂归因审计以及明确的非部署边界。继续堆叠模型并不是科学完整性的必要条件。

### F. 继续 WaterSense 与转向 AquaVision，哪项边际价值更高？

在没有新 WaterSense 外部数据的前提下，**转向 AquaVision 的地理身份恢复、原始工件恢复和新 High-containing components 数据门槛，边际研究价值更高**；不是立即训练 AquaVision。WaterSense 在同一开发集继续做模型变体的边际收益已下降。若能获得 WaterSense 2025+ 或外部区域的新低氧数据，则一次性独立验证仍是 WaterSense 最高价值的下一步，价值高于继续内部调模。

## Reproducibility and scope

- 本轮仅加载 Experiment 1 已保存 inner metrics、selection、outer predictions、uncertainty 和 site tables。
- 新训练模型数：0；新选择模型数：0；legacy test 读取次数：0。
- 没有修改 Experiment 1 结果、冻结规则或 AquaVision。
"""
    _write_text(OUTPUT / "EXPERIMENT1A_ATTRIBUTION_REPORT.md", report)

    handoff = f"""# Experiment 1A Final Handoff

## 最终结论

现有 Experiment 1 的正式 `IMPROVEMENT SUPPORTED` 标签属于完整 selected procedure，不能直接等同于“权重本身已被 outer CV 独立证明”。但是，无需新增训练即可从冻结 inner grid 构建 {all_pairs} 个同架构、同超参数、同 fold 的 weight 1/8 配对；Low-DO MAE 与 Recall 在 {all_pairs}/{all_pairs} 个配对中均向有利方向变化。因此，加权的独立贡献获得了强而一致的**探索性支持**。

## Benefit–cost summary

- Outer OOF Low-DO MAE：{baseline['low_do_mae_mg_l']:.4f} → {weighted['low_do_mae_mg_l']:.4f} mg/L。
- Recall：{baseline['low_do_recall']:.4f} → {weighted['low_do_recall']:.4f}；净增加 178 TP。
- Recall 净增益分布于 {recall_positive_sites} 个低氧站点；没有站点出现净 TP 下降。
- Overall MAE：{baseline['overall_mae_mg_l']:.4f} → {weighted['overall_mae_mg_l']:.4f} mg/L，恶化 8.17%。
- FP：{int(baseline['false_positive_count'])} → {int(weighted['false_positive_count'])}；新增 {new_fp_count} 个，分布于 {new_fp_sites} 个站点。
- 新增 FP 中 {fp_at_least_6} 个真实 DO `>=6`，不能解释为只在阈值附近发生。
- 总体误差恶化主要来自大量真实 DO `>=6` 的记录；低氧区域自身的绝对误差总量下降。

## Research decision

1. 加权本身：探索性支持，未获得独立 outer-level 确认。
2. 当前模型：更适合低氧识别研究，不足以宣称更适合部署。
3. 不明确的代价：Overall MAE、Precision、FP 及远离阈值的误报缺少应用容忍标准。
4. Two-stage：值得作为后续探索性机制实验，但独立数据优先，本轮未启动。
5. 本科研究完整性：如果现在停止模型开发，已经具备科学上诚实、技术上可解释、失败记录完整的研究成果。
6. 边际价值：没有新 WaterSense 外部数据时，AquaVision 的数据身份/High support 恢复高于继续 WaterSense 内部模型变体；若有 WaterSense 新外部数据，则优先做一次性独立验证。

## Execution statement

- 新训练模型：0。
- 新超参数搜索：0。
- Legacy test：未读取。
- AquaVision：未修改。
- Experiment 2 / Two-stage：未启动。
- Git commit / push：未执行。
"""
    _write_text(OUTPUT / "EXPERIMENT1A_FINAL_HANDOFF.md", handoff)


def _run_tests() -> dict[str, str]:
    command = [
        sys.executable,
        "-m",
        "unittest",
        "tests.test_experiment1a_attribution",
        "-v",
    ]
    completed = subprocess.run(
        command, cwd=ROOT, text=True, capture_output=True, check=False
    )
    output = "\n".join(
        part.strip() for part in (completed.stdout, completed.stderr) if part.strip()
    )
    if completed.returncode:
        raise RuntimeError(f"Experiment 1A tests failed:\n{output}")
    summary = next(
        (line for line in output.splitlines() if line.startswith("Ran ")),
        "tests passed",
    )
    return {
        "command": " ".join(command[1:]),
        "result": "passed",
        "summary": summary,
    }


def main() -> None:
    experiment1_manifest = _preflight()
    inner = pd.read_csv(EXPERIMENT1 / "INNER_CV_FOLD_RESULTS.csv.gz")
    selection = pd.read_csv(EXPERIMENT1 / "INNER_CV_SELECTION.csv")
    predictions = pd.read_csv(EXPERIMENT1 / "OUTER_CV_PREDICTIONS.csv.gz")
    comparison = pd.read_csv(EXPERIMENT1 / "BASELINE_VS_WEIGHTED.csv")
    uncertainty = pd.read_csv(EXPERIMENT1 / "SITE_CLUSTERED_UNCERTAINTY.csv")
    site_comparison = pd.read_csv(EXPERIMENT1 / "SITE_ERROR_COMPARISON.csv")

    paired = pair_outer_predictions(predictions)
    inner_pairs = matched_inner_weight_pairs(inner)
    inner_summary = summarize_inner_weight_pairs(inner_pairs)
    selected_attribution = selected_config_attribution(selection)
    error_by_range = outer_error_decomposition(paired)
    transitions = classification_transitions(paired)
    recall_sites = low_do_recall_site_analysis(paired)
    false_positive_sites = false_positive_site_analysis(paired)
    false_positive_ranges = false_positive_range_analysis(paired)
    shift_quantiles = prediction_shift_quantiles(paired)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    _save_table(inner_pairs, "INNER_WEIGHT_MATCHED_PAIRS.csv.gz", compressed=True)
    _save_table(inner_summary, "INNER_WEIGHT_ATTRIBUTION_SUMMARY.csv")
    _save_table(selected_attribution, "SELECTED_CONFIG_ATTRIBUTION.csv")
    _save_table(error_by_range, "OUTER_ERROR_DECOMPOSITION.csv")
    _save_table(transitions, "OUTER_CLASSIFICATION_TRANSITIONS.csv")
    _save_table(recall_sites, "LOW_DO_RECALL_SITE_DISTRIBUTION.csv")
    _save_table(false_positive_sites, "FALSE_POSITIVE_SITE_DISTRIBUTION.csv")
    _save_table(false_positive_ranges, "FALSE_POSITIVE_DO_RANGE.csv")
    _save_table(shift_quantiles, "PREDICTION_SHIFT_QUANTILES.csv")
    _render_reports(
        inner_summary,
        selected_attribution,
        error_by_range,
        transitions,
        recall_sites,
        false_positive_sites,
        false_positive_ranges,
        shift_quantiles,
        comparison,
        uncertainty,
        site_comparison,
    )
    tests = _run_tests()

    source_files = [
        ROOT / "src/experiment1a_attribution.py",
        ROOT / "scripts/run_experiment1a_attribution.py",
        ROOT / "tests/test_experiment1a_attribution.py",
    ]
    outputs = {
        str(path.relative_to(OUTPUT)): sha256_file(path)
        for path in sorted(OUTPUT.rglob("*"))
        if path.is_file() and path.name != "EXPERIMENT1A_RUN_MANIFEST.json"
    }
    manifest = {
        "status": "complete",
        "analysis_type": "post-hoc exploratory attribution using saved evidence",
        "models_trained": 0,
        "models_selected": 0,
        "legacy_benchmark_read": False,
        "aqua_vision_modified": False,
        "two_stage_started": False,
        "water_sense_head": EXPECTED_HEAD,
        "experiment1_config_canonical_sha256": EXPECTED_CONFIG_CANONICAL_SHA256,
        "experiment1_manifest_sha256": sha256_file(
            EXPERIMENT1 / "EXPERIMENT1_RUN_MANIFEST.json"
        ),
        "experiment1_verified_output_count": len(
            experiment1_manifest["output_sha256"]
        ),
        "matched_inner_weight_pair_count": len(inner_pairs),
        "matched_nonweight_configuration_count": int(
            inner_pairs.groupby(["family", "parameters_json"]).ngroups
        ),
        "paired_outer_observation_count": len(paired),
        "automated_tests": tests,
        "source_code_sha256": {
            str(path.relative_to(ROOT)): sha256_file(path) for path in source_files
        },
        "output_sha256": outputs,
        "git_branch": _git("branch", "--show-current"),
        "git_head": _git("rev-parse", "HEAD"),
        "git_status": _git("status", "--short", "--branch", "--untracked-files=all").splitlines(),
    }
    _write_json(OUTPUT / "EXPERIMENT1A_RUN_MANIFEST.json", manifest)


if __name__ == "__main__":
    main()
