# 实验方案

## 1. 项目目标

本项目围绕《LLM辅助Linux内核缺陷修复》展开，目标不是完整复现 CrashFixer，也不是构建大规模 Linux 内核自动修复平台，而是完成一个本科课程项目级别的小规模实验：

- 输入：kBenchSyz 中筛选出的 Linux kernel crash 样本。
- 输出：根因假设、反思选择结果、replace-based edit 补丁、轻量检查结果和人工评价。
- 方法：参考 CrashFixer 的 Hypothesis Generation + Self-Reflection + Patch Generation。
- 改进：在 Patch Generation 阶段加入 Semantic Guard，减少截肢式修复。

## 2. 实验样本

计划选择 6-8 个 kBenchSyz bug：

| 缺陷类型 | 数量 | 选择理由 |
|---|---:|---|
| memory leak | 2 | 资源释放路径相对容易人工判断 |
| UBSAN out-of-bounds | 2 | crash 类型明确，适合边界检查分析 |
| null pointer dereference | 2 | stack trace 和源码位置通常较清晰 |
| 备用样本 | 0-2 | 用于替换过难或信息不足的样本 |

筛选标准：

- 优先单文件修复。
- developer patch 较短。
- crash report 清楚。
- 避免复杂并发、锁、RCU、跨文件大规模修改。

## 3. 实验分组

### A组：Baseline

输入：

```text
crash report + source code
```

流程：

```text
Hypothesis Generation -> Self-Reflection -> Patch Generation
```

目的：复现 CrashFixer 的核心 Prompt 流程。

### B组：With Trace

输入：

```text
crash report + source code + trace summary
```

流程同 A 组。

目的：观察 trace summary 是否提升根因分析质量。

### C组：Improved / Semantic Guard

输入：

```text
crash report + source code + trace summary
```

流程：

```text
Hypothesis Generation -> Self-Reflection -> Semantic-Guard Patch Generation
```

目的：观察语义保护约束是否减少截肢式修复。

## 4. 输出文件

每个 bug 每个实验组保存：

```text
prompt_hypothesis.txt
hypotheses.raw.txt
hypotheses.json
prompt_reflection.txt
reflection.raw.txt
reflection.json
prompt_patch.txt
patch.raw.txt
patch.json
check_result.json
```

## 5. 轻量检查

由于本项目不完整部署 kGymSuite，不进行完整内核编译和 QEMU 动态复现，因此采用轻量检查：

- original 片段是否能在 source file 中匹配。
- replaced 是否为空或过短。
- 是否大段删除代码。
- 是否存在提前 return 或 goto 绕过逻辑。
- 是否注释掉核心功能代码。
- 是否修改定位文件之外的内容。
- 是否给出 reason 和 semantic preservation reason。

## 6. 人工评价

最终人工评价采用三分类：

- plausible：与 developer patch 语义基本一致。
- helpful：根因方向正确，但补丁不完全等价。
- incorrect：根因错误、补丁不可用、破坏功能或存在截肢式修复。

评价表字段：

```text
bug_id, bug_type, group, root_cause_correct, patch_applicable,
semantic_similarity, amputation_risk, final_label, comment
```

## 7. 当前中期完成情况

已完成：

- 项目目录结构。
- Prompt 模板。
- Python 实验脚本框架。
- mock 模式流程演示。
- 轻量 patch 检查。
- 中期汇报文档。

下一阶段：

- 筛选真实 kBenchSyz 样本。
- 调用真实 LLM API。
- 完成三组实验结果。
- 人工评价并生成图表。

