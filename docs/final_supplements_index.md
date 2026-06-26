# 结项补充实验索引

统一最新结果：`results/current_experiment_results.md`。

## Semantic Guard 消融实验

| 内容 | 路径 |
|---|---|
| 完整消融报告 | `results/semantic_guard_ablation.md` |
| 消融数据 | `results/semantic_guard_ablation.csv` |
| 结项报告增补 | `docs/final_report_semantic_guard_ablation_addendum.md` |
| PPT 汇报页 | `docs/semantic_guard_ablation_slide.md` |

核心结论：相同 trace 输入下，Semantic Guard 将 useful 从 3/8 提升到 4/8、真实源码适用从 2/8 提升到 5/8，但新增 2 个 checkpatch warning。

## Memory Leak 失败案例

| 内容 | 路径 |
|---|---|
| 六项失败分析 | `results/memory_leak_failure_analysis.md` |
| 失败分类数据 | `results/memory_leak_failure_analysis.csv` |
| 结项报告增补 | `docs/final_report_memory_leak_failure_addendum.md` |
| PPT 汇报页 | `docs/memory_leak_failure_slide.md` |

核心结论：两个 memory leak 样本的 6 个输出全部 incorrect，真实源码适用为 0/6。当前方法能约束补丁形式，但无法仅凭局部源码和 crash trace 稳定恢复跨路径资源 ownership。
