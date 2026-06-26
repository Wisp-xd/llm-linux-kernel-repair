# 代码流程说明

## 1. 总体调用链

```text
run_all_groups.py / run_baseline.py / run_with_trace.py / run_improved.py
    -> experiment_runner.run_group()
        -> load_bug.load_bug()
        -> build_prompt.render_template()
        -> call_llm.call_llm()                 # 根因假设
        -> call_llm.extract_json()
        -> build_prompt.render_template()
        -> call_llm.call_llm()                 # 自反思
        -> experiment_runner.select_hypothesis()
        -> build_prompt.render_template()
        -> call_llm.call_llm()                 # 候选补丁
        -> check_patch.check_patch()
        -> outputs/<group>/<bug_id>/
```

## 2. 输入数据

`src/load_bug.py` 从一个缺陷目录读取：

| 文件 | 作用 |
|---|---|
| `metadata.json` | 缺陷编号、类型和定位文件等元数据 |
| `crash_report.txt` | 崩溃报告与调用栈 |
| `source.c` | 与缺陷相关的源码上下文 |
| `trace_summary.txt` | 可选的执行轨迹摘要 |
| `developer_patch.diff` | 用于离线比较的开发者补丁 |

公开仓库中的 `data/demo/bug_demo_001/` 是最小演示样本，不代表正式实验结果。

## 3. 三阶段生成

`src/experiment_runner.py` 是主编排模块。

1. 根因假设：使用 `prompts/hypothesis_generation.txt` 生成多个候选根因。
2. 自反思：使用 `prompts/self_reflection.txt` 比较候选证据并选出一个假设。
3. 补丁生成：Baseline 和 With Trace 使用 `patch_generation.txt`；Improved 使用 `semantic_guard_patch.txt`。

所有阶段均保留 Prompt、原始响应和解析后的 JSON，便于追溯。

## 4. 分组差异

`run_group()` 根据 `group` 控制输入和补丁模板：

```text
baseline   = crash report + source
with_trace = crash report + source + trace summary
improved   = crash report + source + trace summary + semantic guard
```

三组共享相同的样本、模型参数和生成阶段，便于进行控制变量比较。

## 5. 模型调用

`src/call_llm.py` 提供统一入口：

- `mock`：本地固定响应，用于流程测试。
- `deepseek`：DeepSeek Chat Completions API。
- `openai`：OpenAI Responses API。
- `gemini`：Gemini GenerateContent API。

API Key 只从环境变量读取。每次调用记录 provider、模型、耗时和可获得的 token usage；运行级汇总写入 `run_metadata.json`。

## 6. 候选补丁检查

`src/check_patch.py` 对 replace-based edit 执行轻量检查，包括：

- 输出结构是否完整；
- `original` 是否能在源码上下文中匹配；
- 修改路径是否与定位文件一致；
- 是否存在删除主体逻辑、注释代码或可疑提前返回；
- Semantic Guard 解释字段是否完整。

该步骤不是编译或动态验证，只用于快速筛除明显不可用的候选补丁。

## 7. 评价与验证脚本

| 模块 | 职责 |
|---|---|
| `evaluate_results.py` | 汇总人工标签与基础评价指标 |
| `summarize_extended_metrics.py` | 汇总补丁应用、成本、重试等扩展指标 |
| `kernel_verify_wsl.py` | 在 WSL Linux 源码树中验证补丁可应用性 |
| `local_compile_verify_wsl.py` | 执行目标对象的局部编译验证 |
| `run_kgym_bug008.py` | 调用本地 kGymSuite 进行代表性动态验证 |
| `visualize.py` | 将评价结果转换为图表 |

这些脚本产生的日志、结果表和图表均位于本地忽略目录，不上传 GitHub。

## 8. 推荐执行顺序

```text
1. 准备缺陷目录
2. 运行三组生成实验
3. 执行轻量检查与人工评价
4. 汇总扩展指标
5. 对可应用候选执行真实源码验证
6. 对代表性补丁执行局部编译
7. 在隔离虚拟机中执行动态复现与回归测试
```

真实内核补丁执行前应固定源码提交、编译配置、reproducer 和超时时间，并完整保留日志。
