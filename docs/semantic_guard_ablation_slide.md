# Semantic Guard 消融实验：汇报页

## 控制变量

- 对照组：With Trace + 普通 Patch Prompt
- 实验组：With Trace + Semantic Guard Patch Prompt
- 相同项：8 个 bug、crash、source、trace、模型流程
- 唯一设计差异：补丁阶段的语义保护约束

## 核心结果

| 指标 | 普通 Prompt | Semantic Guard | 变化 |
|---|---:|---:|---:|
| plausible + helpful | 3/8 | 4/8 | +12.5 pp |
| patch apply ok | 2/8 | 5/8 | +37.5 pp |
| no edit | 4/8 | 0/8 | -50.0 pp |
| checkpatch warnings | 0 | 2 | +2 |

## 为什么可能有效

1. **最小局部修改**：减少大范围改写，`bug_008` 仅重排 cleanup 与 unlock。
2. **保留正常路径**：禁止通过删除、注释或旁路消除 crash。
3. **关注 cleanup/lifetime**：帮助识别资源释放顺序，而不只增加 NULL check。
4. **要求具体 edit**：no edit 从 4/8 降至 0/8，提高可评估补丁覆盖率。

## 代价与边界

- `bug_002`、`bug_007` 从 no edit 变为不可应用补丁。
- checkpatch warning 增加 2 个。
- 每种 Prompt 每个样本只运行一次，结论是改善趋势，不是确定因果证明。

## 汇报结论

> 在相同 trace 输入下，Semantic Guard 与更高的补丁产出率、人工 useful 比例和真实源码适用率相关。主要收益来自最小修改、保留正常路径以及 cleanup/lifetime 约束，但更多修复尝试也会带来无效补丁和格式告警。
