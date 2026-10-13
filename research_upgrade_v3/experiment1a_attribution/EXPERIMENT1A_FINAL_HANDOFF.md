# Experiment 1A Final Handoff

## 最终结论

现有 Experiment 1 的正式 `IMPROVEMENT SUPPORTED` 标签属于完整 selected procedure，不能直接等同于“权重本身已被 outer CV 独立证明”。但是，无需新增训练即可从冻结 inner grid 构建 640 个同架构、同超参数、同 fold 的 weight 1/8 配对；Low-DO MAE 与 Recall 在 640/640 个配对中均向有利方向变化。因此，加权的独立贡献获得了强而一致的**探索性支持**。

## Benefit–cost summary

- Outer OOF Low-DO MAE：3.3235 → 2.3613 mg/L。
- Recall：0.1293 → 0.3641；净增加 178 TP。
- Recall 净增益分布于 50 个低氧站点；没有站点出现净 TP 下降。
- Overall MAE：0.8797 → 0.9516 mg/L，恶化 8.17%。
- FP：26 → 219；新增 193 个，分布于 76 个站点。
- 新增 FP 中 83 个真实 DO `>=6`，不能解释为只在阈值附近发生。
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
