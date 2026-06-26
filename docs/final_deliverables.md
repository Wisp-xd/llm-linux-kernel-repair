# 结项交付物索引

项目题目：《LLM辅助Linux内核缺陷修复》

## 1. 项目入口

| 内容 | 路径 | 说明 |
|---|---|---|
| 项目说明 | `README.md` | 项目目标、流程、运行方式和结项结果 |
| 结项报告 | `docs/final_report.md` | 可直接整理为课程结项报告 |
| PPT 提纲 | `docs/final_ppt_outline.md` | 可直接制作结项答辩 PPT |
| 典型案例 | `docs/final_case_studies.md` | 3 个代表性样本分析 |
| 实验复现指南 | `docs/reproduction_guide.md` | 环境、数据、API、三组实验、源码核验、编译和动态验证 |
| 答辩一页摘要 | `docs/final_defense_brief.md` | 核心数据、三分钟讲稿和答辩口径 |

## 2. 数据与样本

| 内容 | 路径 | 说明 |
|---|---|---|
| 样本清单 | `data/selected_bugs.csv` | 8 个真实 kBenchSyz 样本记录 |
| 样本目录 | `data/selected/bug_001` 至 `data/selected/bug_008` | crash report、source excerpt、developer patch、trace summary |
| 样本说明 | `docs/selected_cases.md` | 样本筛选依据和限制说明 |

## 3. Prompt 与脚本

| 内容 | 路径 | 说明 |
|---|---|---|
| Prompt 模板 | `prompts/` | Hypothesis、Reflection、Patch、Semantic Guard |
| 实验脚本 | `src/run_all_groups.py` | 批量运行三组实验 |
| 轻量检查 | `src/check_patch.py` | 检查 replace-based edit 风险 |
| 统计脚本 | `src/summarize_evaluation.py` | 生成 plausible/helpful/incorrect 统计 |
| 扩展指标脚本 | `src/summarize_extended_metrics.py` | 汇总定位命中、patch apply、编译、动态验证、开发者补丁相似度、API 成本和重试次数 |
| 真实源码核验 | `src/kernel_verify_wsl.py` | 在 WSL2 中执行 Linux parent commit 级 patch apply 核验 |
| 核验统计 | `src/summarize_kernel_verify.py` | 生成真实源码核验摘要 |
| 局部编译对照 | `src/local_compile_compare_wsl.py` | 对 parent、developer、LLM 三路执行 `fs/namespace.o` 编译验证 |
| kGymSuite 动态运行 | `src/run_kgym_bug008.py` | 提交 `bug_008` 完整构建与 reproducer 验证任务 |
| Excel 导出 | `src/export_evaluation_xlsx.py` | 生成评价工作簿 |

## 4. 模型输出

| 内容 | 路径 | 说明 |
|---|---|---|
| Baseline 输出 | `outputs/baseline/bug_001` 至 `bug_008` | crash report + source |
| With Trace 输出 | `outputs/with_trace/bug_001` 至 `bug_008` | crash report + source + trace summary |
| Improved 输出 | `outputs/improved/bug_001` 至 `bug_008` | 加入 Semantic Guard |

每个 bug 输出目录中包含：

- `hypotheses.json`
- `reflection.json`
- `patch.json`
- `check_result.json`
- `run_metadata.json`（当前脚本生成；部分早期历史输出可能缺少该文件）

## 5. 评价与结果

| 内容 | 路径 | 说明 |
|---|---|---|
| 人工评价原始表 | `results/evaluation_real.csv` | 24 个模型输出的人工标签 |
| 评价工作簿 | `results/evaluation.xlsx` | 总览、样本、评价、分组统计、检查结果 |
| 分组统计 | `results/evaluation_summary_by_group.csv` | 三组 plausible/helpful/incorrect 统计 |
| 扩展指标明细 | `results/extended_metrics.csv` | 24 个输出逐项可审计指标 |
| 扩展指标摘要 | `results/extended_metrics_summary.md` | 按实验组汇总新增指标及验证覆盖率 |
| 统计说明 | `results/evaluation_summary.md` | 可直接放入报告 |
| 额外指标 | `results/extra_metrics_summary.md` | 根因正确性、截肢风险、useful outputs |
| 当前结果总览 | `results/current_experiment_results.md` | 主实验、消融、失败案例和动态验证的统一摘要 |
| 当前结果 JSON | `results/current_experiment_results.json` | 结项核心指标的机器可读版本 |
| Semantic Guard 消融报告 | `results/semantic_guard_ablation.md` | 相同 trace 输入下普通 Prompt 与 Semantic Guard 的配对比较 |
| Semantic Guard 消融数据 | `results/semantic_guard_ablation.csv` | useful、源码适用性、no edit 和 warning 的量化变化 |
| Memory Leak 失败分析 | `results/memory_leak_failure_analysis.md` | 6 个 incorrect 输出的逐项原因和方法边界 |
| Memory Leak 失败数据 | `results/memory_leak_failure_analysis.csv` | 失败类型、人工标签和真实源码核验结果 |
| 轻量检查汇总 | `results/check_results_summary_deepseek.csv` | JSON、original 匹配、风险检查 |
| 真实源码核验表 | `results/kernel_verify_summary.csv` | parent commit 级 patch apply / diff check / checkpatch 结果 |
| 真实源码核验摘要 | `results/kernel_verify_summary.md` | 可直接放入报告的核验结论 |
| 局部编译增强项说明 | `docs/local_compile_verification.md` | 工具链、源码树、执行命令和问题处理记录 |
| 局部编译对照说明 | `docs/local_compile_comparison.md` | 三路控制变量、完整哈希、结果解释和结论边界 |
| 局部编译对照表 | `results/local_compile_comparison/summary.csv` | 三路编译结果与目标文件 SHA-256 |
| 局部编译对照摘要 | `results/local_compile_comparison/summary.md` | 可直接放入报告的三路对照结论 |
| 动态验证报告 | `results/dynamic_validation/dynamic_validation_report.md` | `bug_008` parent 与 improved 动态对照结论 |
| 动态验证摘要 | `results/dynamic_validation/dynamic_validation_summary.json` | job、构建耗时、目标 crash 和限制的机器可读记录 |
| 重复动态验证报告 | `results/dynamic_validation/repeated_dynamic_validation_report.md` | 3 次 × 6 分钟 clean pass 及看门狗修复说明 |
| 重复动态验证摘要 | `results/dynamic_validation/repeated_dynamic_validation_summary.json` | jobs `00000016`–`00000018` 的机器可读结果 |
| 动态验证原始证据 | `results/dynamic_validation/` | 任务上下文、syz-crush 日志、VM 日志和 KASAN report |
| 人工复核包 | `results/manual_review_pack.md` | developer patch 与模型 patch 对照 |
| 图表 | `results/figures/` | SVG 结果图 |
| CrashFixer 流程对照图 | `results/figures/crashfixer_project_flow_comparison.svg` | 论文完整流程与课程项目轻量流程对照 |
| 三组实验输入差异图 | `results/figures/experiment_group_input_comparison.svg` | Baseline、With Trace、Improved 控制变量说明 |
| 真实源码核验证据链图 | `results/figures/llm_to_kernel_evidence_chain.svg` | 从 LLM JSON 到人工语义评价的分层证据 |

## 6. 可汇报的核心结论

本项目共运行 8 个真实 kBenchSyz 样本、3 组实验、24 个 DeepSeek V4 Pro 输出。按照 CrashFixer-style 人工分类：

| 组别 | plausible | helpful | incorrect | plausible+helpful |
|---|---:|---:|---:|---:|
| Baseline | 1/8 | 1/8 | 6/8 | 2/8 (25.0%) |
| With Trace | 0/8 | 3/8 | 5/8 | 3/8 (37.5%) |
| Improved / Semantic Guard | 1/8 | 3/8 | 4/8 | 4/8 (50.0%) |

整体：

- plausible：2/24 (8.3%)
- helpful：7/24 (29.2%)
- incorrect：15/24 (62.5%)
- plausible + helpful：9/24 (37.5%)

真实源码适用性核验：

| 组别 | patch apply ok | diff check ok |
|---|---:|---:|
| Developer Patch | 8/8 (100.0%) | - |
| Baseline | 3/8 (37.5%) | 3/8 (37.5%) |
| With Trace | 2/8 (25.0%) | 2/8 (25.0%) |
| Improved / Semantic Guard | 5/8 (62.5%) | 5/8 (62.5%) |

局部编译对照：

| 版本 | `fs/namespace.o` | SHA-256 前缀 |
|---|---|---|
| parent 原始版本 | pass | `8abccf3ac28a...` |
| developer patch | pass | `bad2f34483c0...` |
| LLM improved patch | pass | `bad2f34483c0...` |

动态验证：

| 版本 | job | 目标 crash |
|---|---|---|
| parent | `00000009` | 约 59 秒复现，复现率 100% |
| LLM improved | `00000016`–`00000018` | 3 次 × 6 分钟未复现；3/3 clean pass |

Semantic Guard 消融：

| 指标 | With Trace | Improved | 变化 |
|---|---:|---:|---:|
| useful | 3/8 | 4/8 | +12.5 pp |
| patch apply ok | 2/8 | 5/8 | +37.5 pp |
| no edit | 4/8 | 0/8 | -50.0 pp |

失败边界：memory leak 子集 6/6 incorrect、0/6 patch apply ok。

## 7. 真实性边界

这些结果来自真实 kBenchSyz 样本、真实 DeepSeek V4 Pro API 调用、真实 Linux kernel parent commit 级 patch applicability 核验，以及 `bug_008` 的完整构建、QEMU/KVM 和 reproducer 动态对照。因此汇报时应使用如下表述：

> 本项目在 24 个模型输出上报告 CrashFixer-style 人工语义评价，并在 `bug_008` 上完成动态对照：parent 约 59 秒复现目标崩溃，LLM improved 在 3 次独立、每次 6 分钟的运行中均 clean pass。该单案例结果初步支持方案可行，但不等同于总体真实修复成功率。
