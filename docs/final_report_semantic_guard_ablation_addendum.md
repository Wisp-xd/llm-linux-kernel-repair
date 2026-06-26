# 结项报告增补：Semantic Guard 消融实验

## 实验设计

为单独分析 Semantic Guard 的作用，选择 With Trace 作为普通 Patch Prompt 对照组，Improved 作为实验组。两组使用相同的 8 个样本、crash report、source excerpt、trace summary、Hypothesis Generation 和 Self-Reflection；唯一设计差异是 Patch Generation 阶段是否加入语义保护约束。

## 量化结果

| 指标 | With Trace | Improved | 变化 |
|---|---:|---:|---:|
| plausible + helpful | 3/8 (37.5%) | 4/8 (50.0%) | +12.5 pp |
| incorrect | 5/8 (62.5%) | 4/8 (50.0%) | -12.5 pp |
| 真实源码 patch apply ok | 2/8 (25.0%) | 5/8 (62.5%) | +37.5 pp |
| 未生成 edit | 4/8 (50.0%) | 0/8 (0.0%) | -50.0 pp |
| checkpatch warnings | 0 | 2 | +2 |

## 结果解释

源码适用性的净提升来自 `bug_004`、`bug_006` 和 `bug_008`。其中 `bug_008` 仅调整 cleanup 与 unlock 顺序，符合最小局部修改、保留正常路径和关注对象生命周期的约束，并最终与 developer patch 相同。

禁止删除、注释和绕过核心功能的约束没有产生可单独测量的提升，因为普通 Prompt 组同样没有疑似截肢式修复，存在 floor effect。Semantic Guard 更明确的作用是减少拒绝生成：no edit 从 4/8 降至 0/8。

该变化也有代价。`bug_002` 和 `bug_007` 从 no edit 变为不可应用补丁，checkpatch warning 增加 2 个。这表明语义约束能促进模型尝试局部修复，但不能替代缺失的资源关系、控制流和并发上下文。

## 可汇报结论

在相同 trace 输入下，Semantic Guard 与更高的补丁产出率、人工 useful 比例和真实源码适用率相关。最可能贡献改善的是最小修改、保留正常路径和 cleanup/lifetime 检查约束；但由于样本仅 8 个且每种配置只运行一次，该结果是阶段性相关性观察，不是确定因果证明。

详细逐样本分析见 `results/semantic_guard_ablation.md`，汇报页见 `docs/semantic_guard_ablation_slide.md`。
