# 中期汇报材料

## 1. 项目题目

LLM辅助Linux内核缺陷修复

## 2. 研究背景

Linux 内核代码规模庞大，包含大量底层 C 代码、并发逻辑和硬件交互。Syzkaller 等 fuzzing 工具能够持续发现 Linux kernel crash，但 crash report 通常是机器生成的 stack trace、sanitizer 日志和寄存器信息，缺少自然语言 bug 描述。

近年来，大语言模型在代码理解和程序修复方面表现突出，但现有自动程序修复研究多集中于用户态小规模程序。Linux kernel crash 修复仍然困难。CrashFixer 提出了一种模拟内核开发者调试流程的 LLM agent，将修复拆分为根因假设生成和补丁生成两个阶段。

## 3. 项目定位

本项目不做完整 CrashFixer 复现，也不部署完整 kGymSuite。项目定位为：

> 基于 CrashFixer 思想的 Linux 内核缺陷修复轻量化 Prompt 实验与语义保护约束改进。

实验采用 kBenchSyz 数据中的 crash report、source code、developer patch 和人工整理 trace summary，完成 6-8 个 bug 的小规模可复现实验。

## 4. 已完成工作

### 4.1 完成方法设计

已确定三阶段流程：

```text
Hypothesis Generation
        ↓
Self-Reflection
        ↓
Patch Generation
```

并在 Patch Generation 阶段加入 Semantic Guard 作为轻量创新点。

### 4.2 完成项目仓库结构

当前仓库已经包含：

- `data/`：样本数据目录。
- `prompts/`：四类 Prompt 模板。
- `src/`：实验脚本。
- `outputs/`：三组实验输出目录。
- `results/`：评价表与图表目录。
- `docs/`：实验方案、工具分析和中期汇报材料。

### 4.3 完成 Prompt 模板

已完成：

- `hypothesis_generation.txt`
- `self_reflection.txt`
- `patch_generation.txt`
- `semantic_guard_patch.txt`

其中 Semantic Guard 要求模型不得通过删除、注释、绕过核心功能代码来消除 crash，并要求解释每个 edit 为什么不破坏原功能。

### 4.4 完成脚本框架

已实现：

- `load_bug.py`：读取样本。
- `build_prompt.py`：构造 Prompt。
- `call_llm.py`：调用模型，目前支持 mock 和 Gemini 接口。
- `run_baseline.py`：运行 A 组实验。
- `run_with_trace.py`：运行 B 组实验。
- `run_improved.py`：运行 C 组实验。
- `check_patch.py`：轻量检查 replace-based edit。
- `evaluate_results.py`：汇总评价结果。
- `visualize.py`：生成简单 SVG 图。

### 4.5 完成 demo 链路

目前提供了一个 toy demo case，用于验证实验链路：

```text
data/demo/bug_demo_001/
```

该 demo 不作为正式实验结果，仅用于中期展示“项目流程已经跑通”。

### 4.6 已重新下载并筛选真实 kBenchSyz 样本

已从 Hugging Face 重新下载 `dataset-kb.json` 到：

```text
D:\SQA\kbench_data_fresh\dataset-kb.json
```

并筛选导出 8 个真实样本到：

```text
data/selected/
```

样本类型分布：

- memory leak：2 个。
- out-of-bounds：3 个。
- null pointer：3 个。

详细样本表见 `docs/selected_cases.md`。

### 4.7 已接入 DeepSeek V4 Pro

项目脚本已支持 DeepSeek API：

```powershell
python .\src\run_all_groups.py --provider deepseek --model deepseek-v4-pro
```

由于 API key 属于敏感信息，项目不会把 key 写入仓库。运行前需要在 PowerShell 会话中设置 `DEEPSEEK_API_KEY`。

## 5. 实验设计

正式实验将设置三组：

| 实验组 | 输入 | Patch 阶段 | 目的 |
|---|---|---|---|
| A Baseline | crash report + source code | 普通 Patch Prompt | 复现 CrashFixer 核心流程 |
| B With Trace | crash report + source code + trace summary | 普通 Patch Prompt | 观察 trace 信息影响 |
| C Improved | crash report + source code + trace summary | Semantic Guard Prompt | 观察是否减少截肢式修复 |

## 6. 中期可展示内容

中期汇报可以重点展示：

1. 为什么 Linux kernel crash 修复难。
2. CrashFixer 的两阶段思想。
3. 本项目如何降阶为本科生可执行实验。
4. 三组实验设计。
5. Semantic Guard 创新点。
6. 当前仓库和脚本已经能跑通 demo。
7. 下一阶段将替换为真实 kBenchSyz 样本并完成评价。

## 7. 下一步计划

第1步：从 kBenchSyz 中筛选 6-8 个真实 bug。

第2步：为每个 bug 整理 `metadata.json`、`crash_report.txt`、`source.c`、`developer_patch.diff`、`trace_summary.txt`。

第3步：使用 Gemini API 运行 A/B/C 三组实验。

第4步：运行 `check_patch.py` 生成轻量检查结果。

第5步：对照 developer patch 进行 plausible/helpful/incorrect 人工评价。

第6步：生成结果图表和典型案例分析。

第7步：完成结题报告和最终 PPT。

## 8. 风险与应对

- kBenchSyz 数据复杂：先手动整理 6 个样本，不追求全量自动解析。
- 内核代码难懂：优先选择单文件、短补丁、明确 crash 类型。
- API 不稳定：保留 mock 模式和 raw output，失败样本可重试。
- Patch 无法真实编译：报告中明确采用轻量静态检查和人工语义评价。
- 评价主观：制定固定三分类标准，每条评价必须写 comment。
