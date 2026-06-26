# 结项汇报 PPT 提纲

## 1. 题目页

LLM辅助Linux内核缺陷修复

关键词：Linux kernel crash、CrashFixer、kBenchSyz、DeepSeek V4 Pro、Semantic Guard

## 2. 背景

- Linux kernel crash 修复难。
- Syzkaller 能持续发现 crash，但报告缺少自然语言描述。
- LLM 可辅助根因分析和补丁生成。

## 3. 参考方法：CrashFixer

配图：`results/figures/crashfixer_project_flow_comparison.svg`

```text
Hypothesis Generation
→ Self-Reflection
→ Patch Generation
→ Build/Reproducer Validation
```

本项目保留前三步，降阶为本科可执行实验。

## 4. 项目定位

- 不完整复现 CrashFixer。
- 做真实 kBenchSyz 小样本 Prompt 实验。
- 对 8 个样本做真实源码适用性核验。
- 对 1 个代表样本做局部编译、完整 kernel build、QEMU/KVM 和 reproducer 动态验证。

## 5. 数据集与样本

- 数据：kBenchSyz / kBench
- 样本：8 个
- 类型：memory leak 2，out-of-bounds 3，null pointer 3

## 6. 实验分组

配图：`results/figures/experiment_group_input_comparison.svg`

| 组别 | 输入 | 目的 |
|---|---|---|
| Baseline | crash + source | 基线 |
| With Trace | crash + source + trace | 验证 trace |
| Improved | crash + source + trace + semantic guard | 减少截肢式修复 |

## 7. Prompt 流程

展示四类 Prompt：

- Hypothesis Generation
- Self-Reflection
- Patch Generation
- Semantic Guard Patch Generation

## 8. 工程实现

展示目录：

```text
data/
prompts/
src/
outputs/
results/
docs/
```

## 9. DeepSeek 实验运行

- 模型：DeepSeek V4 Pro
- 输出：24 组
- JSON 解析失败：0

## 10. 轻量检查结果

| 指标 | 数量 |
|---|---:|
| original 匹配成功 | 18 |
| 疑似截肢式修复 | 0 |
| high risk | 0 |

## 11. 真实源码适用性核验

配图：`results/figures/llm_to_kernel_evidence_chain.svg`

- 环境：WSL2 Ubuntu
- 仓库：kernel.org Linux sparse checkout
- 版本：每个样本的 `parentOfFixCommit`
- 检查：developer patch `git apply --check`，模型 patch `git diff --check` + `checkpatch.pl`

| 组别 | patch apply ok |
|---|---:|
| Developer Patch | 8/8 |
| Baseline | 3/8 |
| With Trace | 2/8 |
| Improved | 5/8 |

说明：该页是 8 个样本的源码级检查；完整构建与动态验证见后续 `bug_008` 案例。

## 12. 单样本三路局部编译对照

| 项目 | 内容 |
|---|---|
| 样本 | bug_008 |
| parent commit | `197b6b60ae7bc51dd0814953c562833143b292aa` |
| 文件 | `fs/namespace.c` |
| 目标 | `fs/namespace.o` |

| 版本 | 局部编译 | SHA-256 前缀 |
|---|---|---|
| parent 原始版本 | pass | `8abccf3ac28a...` |
| developer patch | pass | `bad2f34483c0...` |
| LLM improved patch | pass | `bad2f34483c0...` |

日志证据：

```text
CC      fs/namespace.o
```

说明：developer patch 与 LLM improved patch 的对象哈希一致；下一页继续验证运行时行为。

## 13. bug_008 完整构建与动态验证

实验控制：相同 parent commit、内核配置、userspace image、syzkaller checkout 和 C reproducer。

| 版本 | job | 完整构建 | 动态结果 |
|---|---|---|---|
| parent | `00000009` | pass | 约 59 秒复现目标 KASAN crash，复现率 100% |
| LLM improved | `00000016`–`00000018` | pass | 3 次 × 6 分钟均 clean pass，target/special crash 为 0 |

主结论：`bug_008` 获得初步动态修复证据。

看门狗修复：使用独立子进程输出 syzkaller 认可的 `executing program` 协议心跳；主 reproducer 保持无节流。

## 14. 人工评价口径

参考 CrashFixer：

- plausible
- helpful
- incorrect

说明：不是内核动态修复成功率。

## 15. 人工评价结果

| 组别 | plausible | helpful | incorrect | plausible+helpful |
|---|---:|---:|---:|---:|
| Baseline | 1 | 1 | 6 | 2 |
| With Trace | 0 | 3 | 5 | 3 |
| Improved | 1 | 3 | 4 | 4 |

## 16. Semantic Guard 消融实验

严格控制变量：With Trace 与 Improved 输入相同，仅 Patch Prompt 不同。

| 指标 | 普通 Prompt | Semantic Guard | 变化 |
|---|---:|---:|---:|
| useful | 3/8 | 4/8 | +12.5 pp |
| patch apply ok | 2/8 | 5/8 | +37.5 pp |
| no edit | 4/8 | 0/8 | -50.0 pp |
| checkpatch warnings | 0 | 2 | +2 |

解释：最小修改、保留正常路径、cleanup/lifetime 约束与 `bug_004`、`bug_006`、`bug_008` 的提升相关；更多尝试也会产生无效补丁和 warning。

## 17. 失败案例：Memory Leak

| 子集 | useful | incorrect | patch apply ok |
|---|---:|---:|---:|
| 2 个 bug × 3 组 | 0/6 | 6/6 | 0/6 |

- `bug_001`：三组 edit 均无法应用到真实源码。
- `bug_002`：两组 no edit；Improved 把 cleanup leak 误修为 NULL check。
- 方法边界：局部 source/trace 无法稳定恢复 acquire-transfer-release ownership。

## 18. 典型案例一：memory leak

bug_002：模型难以补全正确资源释放路径。

## 19. 典型案例二：out-of-bounds

bug_005：模型能生成边界检查，但错误路径不完全等价。

## 20. 典型案例三：null pointer

bug_008：Improved 与 developer patch 相同，并获得完整构建和动态对照支持。

## 21. 结论

- 框架可运行。
- DeepSeek 输出格式稳定。
- Trace 提升 helpful 数量。
- Semantic Guard 的 plausible+helpful 最高。
- Semantic Guard 的真实源码 patch apply ok 数量最高。
- bug_008 三路局部编译均通过，developer 与 LLM 对象哈希一致。
- bug_008 parent 可复现目标 crash，LLM improved 在 3 次 × 6 分钟中均 clean pass。
- 消融显示 Semantic Guard 主要减少 no edit、提升源码适用性，但存在 warning 和无效尝试代价。
- memory leak 0/6 useful 明确界定了 ownership/cleanup 场景的方法边界。
- 可以初步认为方案可行，但不能将单案例结果外推为总体真实修复成功率。

## 22. 局限性

- source excerpt 非完整源码。
- 完整构建与动态验证只覆盖 1 个代表样本。
- 重复动态验证仍只覆盖一个 bug 和一种 VM 配置。
- 样本规模小。

## 23. 未来工作

- 扩展 kGymSuite 动态验证到其余 plausible/helpful 补丁。
- 将重复动态验证扩展到更多案例和 VM 配置。
- 扩大样本规模。
- 多模型对比。
