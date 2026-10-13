# Experiment 1A Attribution Report

## Executive conclusion

Experiment 1 的 outer-CV `IMPROVEMENT SUPPORTED` 结论针对的是完整的 inner-selected procedure，而不是纯粹的权重因果效应，因为 baseline 是固定 Random Forest，selected procedure 是 weight 8 的 HistGradientBoostingRegressor，模型架构和非权重超参数同时变化。

不过，现有 2,560 条 inner-fold 结果已经包含严格匹配的 weight 1/8 对照，因此无需新训练。对完全相同架构、非权重超参数、inner train/validation stations 和预处理矩阵的 640 个配对，weight 8 的 Low-DO MAE 在 640/640 个配对中降低，Recall 在 640/640 个配对中提高。这构成一致的**探索性权重归因证据**，但不是未受选择影响的 outer-level 确认性估计。

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

- 共有 32 个非权重配置 × 20 inner folds = 640 个严格匹配对照。
- 所有 640 对照的 Low-DO MAE 和 Bias 都向有利方向变化；所有 640 对照的 Recall 都提高。
- HGB 子集 320 个配对的平均 weight 8 − weight 1 差异：Low-DO MAE -1.0720 mg/L，Recall +0.2049。
- 这些 folds 在不同 outer frameworks 中重用站点，不能被当作 640 个独立统计重复；这里只报告方向一致性和描述性效应，不计算伪独立 CI。

### 1.2 对五个最终 selected HGB 配置的描述性分解

在各 outer-training partition 的 pooled inner OOF 中，五个 selected HGB 配置的平均分解为：

| 指标 | HGB weight 1 − RF anchor（架构/超参数部分） | HGB weight 8 − HGB weight 1（权重部分） |
| --- | ---: | ---: |
| Overall MAE | +0.0477 mg/L | +0.0118 mg/L |
| Low-DO MAE | -0.0784 mg/L | -0.8879 mg/L |
| Low-DO Recall | +0.0387 | +0.2101 |
| Low-DO Precision | not used for simple allocation | -0.1644 |
| False positives per pooled inner OOF | not used for simple allocation | +148.0 |

该分解显示，在 selected configurations 的 inner evidence 中，低氧 MAE 与 Recall 的大部分增益和大部分新增误报都与权重从 1 提升到 8 同向；Overall MAE 代价则主要与 HGB 架构/超参数差异相关。但这仍是选择后的描述性分解，不能当作随机化因果估计。

## 2. Benefit–cost analysis

### 2.1 Low-DO MAE 稳定性

- 五个 outer folds 的 selected procedure 均降低 Low-DO MAE。
- Pooled delta 为 -0.9622 mg/L；paired site-bootstrap 95% CI [-1.0895, -0.8527]。
- 115 个低氧站点中 102 个 MAE 改善，13 个恶化。

这支持“开发 CV 内改善稳定”，但不能保证新区域、新年份或新低氧事件中保持相同幅度。

### 2.2 Recall 的独立站点分布

- 净增加 178 个 true positives：179 个 baseline FN 被修正为 TP，同时 1 个 baseline TP 变为 FN。
- 50/115 个低氧站点有净 TP 增益，65 个无净变化，0 个净下降。
- 前 5 个站点占全部正向 TP 增益的 37.6%，前 10 个占 56.7%。改善跨多个站点，但并非均匀。

最大 TP 增益站点：

| station_code | low_do_observation_count | baseline_true_positive_count | weighted_true_positive_count | true_positive_gain |
| --- | --- | --- | --- | --- |
| UKGBNIF10910 | 65 | 20 | 41 | 21 |
| UKGBNIF10337 | 46 | 21 | 36 | 15 |
| UKGBNIF10338 | 37 | 19 | 31 | 12 |
| UKGBNIF10545 | 21 | 1 | 11 | 10 |
| UKGBNIF10541 | 11 | 0 | 9 | 9 |
| UKGBNIF10523 | 37 | 0 | 7 | 7 |
| UKGBNIF10524 | 12 | 0 | 7 | 7 |
| UKGBNIF10626 | 23 | 1 | 8 | 7 |
| UKGBNIF10936 | 57 | 0 | 7 | 7 |
| UKGBNIF10339 | 27 | 7 | 13 | 6 |

### 2.3 Overall MAE 恶化来源

总绝对误差增加 8602.1 mg/L。真实低氧 `<4` 的总绝对误差减少 729.3 mg/L，但真实 DO `>=6` 的总绝对误差增加 9673.5 mg/L，其中 `>=8` 增加 8398.2 mg/L。也就是说，整体 MAE 恶化主要来自大量正常/较高 DO 记录，而不是低氧记录本身。

完整 DO 分层分解在 `OUTER_ERROR_DECOMPOSITION.csv`。

### 2.4 False Positives 的集中程度

Weighted procedure 的 219 个 FP 中，26 个 baseline 已经是 FP，新增 FP 为 193 个，分布于 76 个站点。最大单站占 7.8%，前 5 站占 26.4%，前 10 站占 42.5%；不存在单一站点解释全部误报。

新增 FP 中 83/193 的真实 DO `>=6`，其中 40/193 的真实 DO `>=8`。误报并不只集中在 4 mg/L 阈值附近，这些远离阈值的误报是重要风险信号。

最大新增 FP 站点：

| station_code | new_false_positive_count | actual_do_mean_mg_l |
| --- | --- | --- |
| UKGBNIF10339 | 15 | 5.633333 |
| UKGBNIF10006 | 9 | 7.200000 |
| UKGBNIF10541 | 9 | 7.611111 |
| UKGBNIF10545 | 9 | 13.155556 |
| UKGBNIF10626 | 9 | 4.633333 |
| UKGBNIF10619 | 8 | 5.462500 |
| UKGBNIF10522 | 6 | 13.833333 |
| UKGBNIF10910 | 6 | 5.566667 |
| UKGBNIF11306 | 6 | 5.516667 |
| UKGBNIF10005 | 5 | 6.240000 |

### 2.5 预测分布位移

全体预测的平均 weighted − baseline 位移为 -0.0595 mg/L，中位数为 -0.0219 mg/L，52.5% 的预测降低。低氧区位移更大：真实 DO `<2` 的平均位移约 -1.3924 mg/L。该变化不是简单的全局常数平移，但存在面向低值的系统性移动，并延伸到部分高 DO 记录。

### 2.6 Precision–Recall 权衡

Recall 从 0.1293 提高到 0.3641，FNR 从 0.8707 降至 0.6359；Precision 从 0.7903 降到 0.5576，FP 从 26 增至 219。研究上这表明 rare-regime sensitivity 可以提高；应用上是否值得取决于漏报与误报的相对成本，而当前没有冻结的业务成本函数或环境预警容忍阈值。

## 3. Scientific conclusion categories

### Confirmed within development CV

- 冻结的完整 inner-selected procedure 相比固定 RF baseline，在开发集 outer OOF 中改善 Low-DO MAE、Bias、Recall 和 F1。
- 同一流程同时恶化 Overall MAE/RMSE/R²、Precision、FP 和 FPR。
- 改善和代价都跨多个 outer folds/站点出现；配对站点 bootstrap 支持两类方向。
- 这些陈述只覆盖冻结开发站点总体及其 CV 过程。

### Exploratory evidence

- 在现有 inner grid 的 640 个同配置配对中，weight 8 对 Low-DO MAE/Bias/Recall 的方向一致，支持“权重具有独立贡献”。
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
