# 当前实验结果总览

更新时间：2026-06-20

## 1. 总体实验

| 项目 | 结果 |
|---|---|
| 数据集 | 8 个真实 kBenchSyz 样本 |
| 实验组 | Baseline、With Trace、Improved/Semantic Guard |
| 模型输出 | 24 |
| JSON 解析成功 | 24/24 |
| plausible | 2/24 (8.3%) |
| helpful | 7/24 (29.2%) |
| incorrect | 15/24 (62.5%) |
| plausible + helpful | 9/24 (37.5%) |

按组比较：

| 组别 | plausible | helpful | incorrect | plausible+helpful |
|---|---:|---:|---:|---:|
| Baseline | 1/8 | 1/8 | 6/8 | 2/8 (25.0%) |
| With Trace | 0/8 | 3/8 | 5/8 | 3/8 (37.5%) |
| Improved | 1/8 | 3/8 | 4/8 | 4/8 (50.0%) |

## 2. 真实源码适用性

| 组别 | patch apply ok | diff check ok |
|---|---:|---:|
| Developer | 8/8 (100.0%) | - |
| Baseline | 3/8 (37.5%) | 3/8 (37.5%) |
| With Trace | 2/8 (25.0%) | 2/8 (25.0%) |
| Improved | 5/8 (62.5%) | 5/8 (62.5%) |

## 3. Semantic Guard 消融

严格对照 With Trace 与 Improved：两组均包含 crash、source 和 trace，仅 Patch Prompt 不同。

| 指标 | 普通 Patch Prompt | Semantic Guard | 变化 |
|---|---:|---:|---:|
| plausible + helpful | 3/8 | 4/8 | +12.5 pp |
| patch apply ok | 2/8 | 5/8 | +37.5 pp |
| no edit | 4/8 | 0/8 | -50.0 pp |
| checkpatch warnings | 0 | 2 | +2 |

解释：最小局部修改、保留正常路径、关注 cleanup/lifetime 与 `bug_004`、`bug_006`、`bug_008` 的改善相关。代价是更多修复尝试也产生无效补丁和格式警告。该结果是小样本相关性观察，不是确定因果证明。

## 4. Memory Leak 失败边界

| 子集 | plausible | helpful | incorrect | patch apply ok |
|---|---:|---:|---:|---:|
| 2 个 memory leak × 3 组 | 0/6 | 0/6 | 6/6 | 0/6 |

- `bug_001` 三组均生成 edit，但真实源码应用全部失败。
- `bug_002` 的 Baseline/With Trace 没有生成 edit。
- `bug_002 Improved` 把错误路径资源泄漏误修为 NULL check，没有补全 frontend `release()`。

方法边界：当前局部 source excerpt 和 crash trace 难以恢复跨路径 acquire-transfer-release ownership；Semantic Guard 可以约束补丁形态，但不能替代完整控制流和资源生命周期分析。

## 5. bug_008 编译与动态验证

| 验证层 | 结果 |
|---|---|
| developer 与 LLM source diff | 相同 |
| `fs/namespace.o` SHA-256 | developer 与 LLM 完全相同 |
| 完整内核构建 | parent 与 LLM improved 均通过 |
| parent 动态结果 | job `00000009`，约 59 秒复现目标 KASAN crash，复现率 100% |
| LLM improved 重复结果 | jobs `00000016`–`00000018`，3 次 × 6 分钟均 clean pass |
| patched target crash | 0/3 |
| patched special crash | 0/3 |
| patched imageAbility | 3/3 `normal` |

旧的 `no output from test machine` 告警已解决。固定 syzkaller 只认可包含 `executing program` 或 `executed programs:` 的活性输出；最终使用独立子进程每 10 秒发送协议心跳，正式验证保持原 reproducer 主循环无节流。

## 6. 当前结论

1. Improved/Semantic Guard 在小样本中取得最高人工 useful 比例和真实源码适用率。
2. 消融结果表明它最明显的作用是减少 no edit 并促进局部可应用修改，但会增加无效尝试和少量 checkpatch warning。
3. Memory leak 的 0/6 useful 明确揭示当前方法对资源 ownership 和复杂 cleanup 路径的不足。
4. `bug_008` 已形成“语义评价、源码适用、对象编译、完整构建、3 次重复动态验证”的证据链，可以初步认为补丁可行。
5. 动态结论仍只覆盖一个 bug 和一种 VM 配置，不能外推为总体真实修复成功率。
