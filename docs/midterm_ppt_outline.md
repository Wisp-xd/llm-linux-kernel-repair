# 中期汇报 PPT 提纲

## 第1页：题目页

题目：LLM辅助Linux内核缺陷修复

关键词：Linux kernel crash、CrashFixer、kBenchSyz、Prompt、Semantic Guard

## 第2页：研究背景

- Linux 内核规模巨大，缺陷修复难。
- Syzkaller 持续发现 kernel crash。
- crash report 缺少自然语言描述，主要是 stack trace 和 sanitizer 日志。
- LLM 为程序理解和补丁生成提供新机会。

## 第3页：参考论文 CrashFixer

展示 CrashFixer 核心思想：

```text
crash report + source code + execution trace
        ↓
Hypothesis Generation
        ↓
Patch Generation
        ↓
Build + Reproducer Validation
```

强调：本项目借鉴前两个核心阶段，不完整复现完整系统。

## 第4页：本科项目降阶方案

完整 CrashFixer/kGymSuite 过重：

- 内核编译成本高。
- QEMU/reproducer 环境复杂。
- kDump 轨迹提取实现成本高。

本项目采用：

```text
kBenchSyz 小样本
+ Prompt 实验
+ replace-based edit
+ 轻量检查
+ 人工评价
```

## 第5页：总体流程

```text
样本筛选
  ↓
数据规范化
  ↓
Hypothesis Generation
  ↓
Self-Reflection
  ↓
Patch Generation
  ↓
Patch 检查
  ↓
人工评价
  ↓
结果展示
```

## 第6页：实验分组

| 组别 | 输入 | 目的 |
|---|---|---|
| A Baseline | crash report + source | 基线 |
| B With Trace | crash report + source + trace | 验证 trace 价值 |
| C Improved | crash report + source + trace + semantic guard | 减少截肢式修复 |

## 第7页：Semantic Guard 创新点

约束内容：

- 不得删除、注释、绕过核心功能代码。
- 不得无依据提前 return。
- memory leak 优先补资源释放。
- out-of-bounds 优先补边界检查。
- null pointer 优先补空指针检查。
- 每个 edit 说明为什么不破坏原功能。

## 第8页：当前实现

仓库结构：

```text
data/
prompts/
src/
outputs/
results/
docs/
```

已完成脚本：

- load_bug
- build_prompt
- call_llm
- run_baseline
- run_with_trace
- run_improved
- check_patch
- evaluate_results
- visualize

## 第9页：Demo 运行结果

展示 demo 输出目录：

```text
outputs/baseline/bug_demo_001/
outputs/with_trace/bug_demo_001/
outputs/improved/bug_demo_001/
```

展示关键文件：

- `hypotheses.json`
- `reflection.json`
- `patch.json`
- `check_result.json`

说明：demo 仅用于验证流程，不作为正式实验结论。

## 第9页补充：真实样本筛选进展

已重新下载 kBench 数据：

```text
D:\SQA\kbench_data_fresh\dataset-kb.json
```

已筛选 8 个样本：

- memory leak：2 个。
- out-of-bounds：3 个。
- null pointer：3 个。

展示文件：

```text
data/selected_bugs.csv
docs/selected_cases.md
```

## 第10页：评价方法

三分类：

- plausible：与 developer patch 语义基本一致。
- helpful：根因正确但补丁不完全等价。
- incorrect：根因错误、不可用或截肢式修复。

辅助检查：

- original 是否匹配源码。
- 是否大段删除。
- 是否提前 return。
- 是否注释核心逻辑。

## 第11页：下一阶段计划

1. 筛选 6-8 个 kBenchSyz 样本。
2. 整理统一样本目录。
3. 调用 Gemini API 跑三组实验。
4. 进行人工评价。
5. 生成结果图。
6. 完成典型案例分析。

## 第12页：风险与应对

- 数据复杂：手动小样本整理。
- 内核难懂：选短补丁、典型缺陷。
- API 不稳定：保存 raw output，支持重试。
- 无法完整验证：明确采用轻量检查 + 人工评价。
- 与完整 CrashFixer 有差距：定位为轻量复现实验。
