# Semantic Guard 消融实验

## 1. 对照设计

本消融比较 `With Trace` 与 `Improved`，而不是直接比较 Baseline 与 Improved。两组均输入 crash report、source excerpt 和 trace summary，并共享 Hypothesis Generation 与 Self-Reflection 流程；唯一设计差异是 Patch Generation 阶段是否加入 Semantic Guard。这样可以避免把 trace 信息的影响误算为 Semantic Guard 的效果。

## 2. 被消融的约束

Semantic Guard 主要强调：

1. 保留合法输入和正常执行路径的原有行为。
2. 优先采用局部、最小修改，不扩大修改范围。
3. 不通过删除、注释或绕过核心逻辑来消除崩溃。
4. 显式关注资源释放、错误路径和对象生命周期，避免只做表面防护。
5. 说明补丁如何阻止目标 crash，以及仍然存在的限制。

## 3. 聚合结果

| 指标 | 普通 Patch Prompt（With Trace） | Semantic Guard（Improved） | 变化 |
|---|---:|---:|---:|
| plausible | 0/8 (0.0%) | 1/8 (12.5%) | +1，+12.5 pp |
| helpful | 3/8 (37.5%) | 3/8 (37.5%) | 不变 |
| plausible + helpful | 3/8 (37.5%) | 4/8 (50.0%) | +1，+12.5 pp |
| incorrect | 5/8 (62.5%) | 4/8 (50.0%) | -1，-12.5 pp |
| 真实源码 patch apply ok | 2/8 (25.0%) | 5/8 (62.5%) | +3，+37.5 pp |
| `git diff --check` ok | 2/8 (25.0%) | 5/8 (62.5%) | +3，+37.5 pp |
| 未生成 edit | 4/8 (50.0%) | 0/8 (0.0%) | -4，-50.0 pp |
| checkpatch warnings | 0 | 2 | +2 |

`pp` 表示百分点。Semantic Guard 组更少拒绝生成补丁，真实源码适用率提高 37.5 个百分点，人工 useful 比例提高 12.5 个百分点。与此同时，更多补丁尝试也带来了 2 个 checkpatch warning，说明“更愿意修改”不等于“所有修改质量都更高”。

## 4. 逐样本配对结果

| bug | With Trace | Improved | 消融观察 |
|---|---|---|---|
| `bug_001` | fail | fail | 未解决复杂 memory leak 根因 |
| `bug_002` | no edit | fail | 从拒绝生成变为尝试修复，但补丁仍不可用 |
| `bug_003` | pass | pass | 两种 Prompt 均生成可应用补丁 |
| `bug_004` | fail | pass | Improved 的局部防护能落到真实源码 |
| `bug_005` | pass | pass | 均定位位移边界，但错误路径语义仍仅为 helpful |
| `bug_006` | no edit | pass | Improved 从无补丁提升为可应用补丁 |
| `bug_007` | no edit | fail | 尝试修改，但有限上下文下仍失败 |
| `bug_008` | no edit | pass | Improved 生成与 developer 相同的 cleanup ordering 修复 |

真实源码适用性的净提升来自 `bug_004`、`bug_006` 和 `bug_008`。`bug_002`、`bug_007` 则说明，当 source excerpt 缺少完整资源关系或并发上下文时，语义约束不能替代程序分析。

## 5. 为什么可能有效

### 5.1 保留正常路径与最小修改

`bug_008` 只调整 `cleanup_group_ids()` 与 `namespace_unlock()` 的顺序，不删除功能、不新增旁路，最终与 developer patch 相同。这符合“保留行为、最小修改”的约束，也是本项目完成动态验证的 improved 案例。

### 5.2 强调 cleanup 与生命周期

`bug_008` 的根因不是简单缺少 NULL check，而是 cleanup 发生在 namespace unlock 之后，带来 `mnt` 生命周期风险。对 cleanup/error path 的强调有助于选择顺序修复，而不是添加表面空指针防护。

### 5.3 禁止删除、注释和绕过

24 个正式输出中没有发现疑似截肢式修复，说明该风险得到控制。但普通 Prompt 组同样没有出现此类问题，存在 floor effect，因此不能声称这一约束单独带来了可测提升。

### 5.4 要求具体局部 edit

With Trace 有 4/8 未生成 edit，而 Improved 为 0/8。这提高了可评估补丁覆盖率，并贡献了 3 个真实源码适用样本；代价是 `bug_002`、`bug_007` 从 no edit 变为 fail，说明强制尝试也会产生无效补丁。

## 6. 结论边界

本消融支持阶段性结论：在相同 trace 输入下，Semantic Guard 与更高的补丁产出率、真实源码适用率和人工 useful 比例相关，最明显的收益是减少 no edit 并促进局部可应用修改。

这不是确定因果证明：每个样本每种 Prompt 仅运行一次，样本量为 8，未控制模型随机性；动态验证也只覆盖 `bug_008 improved`。更严格的后续实验应固定采样参数、每组重复至少 3 次，并分别移除“最小修改”“禁止绕过”“cleanup/lifetime 检查”等单条约束。
