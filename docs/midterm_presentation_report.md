# 《LLM辅助Linux内核缺陷修复》中期汇报

## 一、项目基本信息

课题名称：LLM辅助Linux内核缺陷修复

研究方向：软件工程、程序分析、大模型应用、自动程序修复

项目定位：

本项目不是完整复现 CrashFixer 系统，也不是构建大规模 Linux 内核自动修复平台，而是在 CrashFixer、kGym/kBench、syzbot 等已有研究和数据基础上，完成一个本科课程项目级别的小规模、可复现、可展示的 Prompt 实验。

当前项目目标是：

```text
kBenchSyz 真实样本
    ↓
Crash report + source excerpt + trace summary
    ↓
Hypothesis Generation
    ↓
Self-Reflection
    ↓
Patch Generation
    ↓
Semantic Guard 改进
    ↓
replace-based edit 轻量检查
    ↓
人工语义评价
```

目前项目已完成到“真实样本实验运行与轻量检查”阶段，下一步进入人工评价与结果分析阶段。

## 二、研究背景与参考方法

Linux 内核代码规模庞大，包含大量底层 C 代码、并发逻辑、驱动代码和硬件交互逻辑。Syzkaller 等 fuzzing 工具可以持续发现 Linux kernel crash，但 crash report 通常只有 stack trace、sanitizer 日志和 reproducer，缺少自然语言 bug 描述。

CrashFixer 提出了一种面向 Linux kernel crash 的 LLM 修复流程，其核心思想是模拟内核开发者调试过程：

1. 先根据 crash report、源码和执行轨迹生成根因假设。
2. 再基于根因假设生成候选补丁。
3. 最后通过编译和 reproducer 验证补丁。

本项目借鉴 CrashFixer 的核心思想，但进行本科课程项目级别降阶：

- 不部署完整 kGymSuite。
- 不进行完整 Linux 内核编译。
- 不启动 QEMU 复现 crash。
- 不进行 kDump 动态轨迹提取。
- 采用小规模真实样本 + Prompt 实验 + 轻量静态检查 + 人工评价。

## 三、已完成工作

### 3.1 项目仓库结构

当前项目已建立完整目录结构：

```text
llm-linux-kernel-repair/
├── data/
│   ├── raw/
│   ├── selected/
│   └── demo/
├── prompts/
├── src/
├── outputs/
│   ├── baseline/
│   ├── with_trace/
│   └── improved/
├── results/
└── docs/
```

主要目录说明：

| 目录 | 内容 |
|---|---|
| `data/selected` | 真实 kBenchSyz 样本 |
| `prompts` | Prompt 模板 |
| `src` | 实验运行脚本 |
| `outputs` | 模型输出 |
| `results` | 汇总结果和评价表 |
| `docs` | 实验方案、案例学习、中期汇报材料 |

### 3.2 Prompt 模板

已完成四类 Prompt：

| Prompt | 作用 |
|---|---|
| `hypothesis_generation.txt` | 生成多个根因假设 |
| `self_reflection.txt` | 对多个假设进行比较和筛选 |
| `patch_generation.txt` | 生成普通 replace-based edit 补丁 |
| `semantic_guard_patch.txt` | 加入语义保护约束的补丁生成 |

其中 Semantic Guard 约束包括：

- 不得删除、注释、绕过核心功能代码。
- 不得无依据提前 return。
- memory leak 优先补全资源释放逻辑。
- out-of-bounds 优先增加边界检查并保留正常路径。
- null pointer dereference 优先增加必要空指针检查。
- 每个 edit 必须说明为什么不会破坏原功能。

### 3.3 Python 实验脚本

已实现主要脚本：

| 脚本 | 作用 |
|---|---|
| `prepare_kbench_selected.py` | 从 kBench 数据中导出真实样本 |
| `load_bug.py` | 读取单个 bug 样本 |
| `build_prompt.py` | 构造 Prompt |
| `call_llm.py` | 调用模型 API |
| `run_baseline.py` | 运行 Baseline 组 |
| `run_with_trace.py` | 运行 With Trace 组 |
| `run_improved.py` | 运行 Semantic Guard 组 |
| `run_all_groups.py` | 批量运行三组实验 |
| `check_patch.py` | replace-based edit 轻量检查 |
| `recheck_outputs.py` | 对已有输出重新检查 |
| `collect_check_results.py` | 汇总检查结果 |

### 3.4 Python 环境

原本系统中的 `D:\aconada\python.exe` 存在 `_ssl` 缺失问题，导致无法直接进行 HTTPS API 调用。

目前已使用本机可用 Python 创建项目虚拟环境：

```text
D:\SQA\llm-linux-kernel-repair\.venv
```

该环境 SSL 正常：

```text
OpenSSL 3.0.9 30 May 2023
```

后续运行实验建议使用：

```powershell
cd D:\SQA\llm-linux-kernel-repair
.\.venv\Scripts\Activate.ps1
```

## 四、真实数据准备

### 4.1 数据来源

本项目已重新从网上下载 kBench 数据：

```text
https://huggingface.co/datasets/chenxi-kalorona-huang/kbench/resolve/main/dataset-kb.json
```

下载后的本地文件：

```text
D:\SQA\kbench_data_fresh\dataset-kb.json
```

### 4.2 样本筛选原则

筛选原则：

- 总数控制在 6-8 个。
- 优先 memory leak、out-of-bounds、null pointer dereference。
- 优先单文件修复。
- 优先 developer patch 较短。
- 避免复杂并发、锁、RCU、跨文件大规模修改。

### 4.3 当前样本

目前已筛选 8 个真实 kBenchSyz 样本：

| bug_id | 类型 | 子系统 | 定位文件 |
|---|---|---|---|
| bug_001 | memory leak | netfilter | `net/netfilter/nf_tables_api.c` |
| bug_002 | memory leak | usb, media | `drivers/media/usb/dvb-usb/cinergyT2-core.c` |
| bug_003 | out_of_bounds | fs | `kernel/printk/printk.c` |
| bug_004 | out_of_bounds | selinux | `net/xfrm/xfrm_user.c` |
| bug_005 | out_of_bounds | usb | `drivers/usb/usbip/vhci_hcd.c` |
| bug_006 | null_pointer | mm, udf | `mm/filemap.c` |
| bug_007 | null_pointer | media | `drivers/media/common/videobuf2/videobuf2-core.c` |
| bug_008 | null_pointer | fs | `fs/namespace.c` |

类型分布：

| 类型 | 数量 |
|---|---:|
| memory leak | 2 |
| out-of-bounds / UBSAN | 3 |
| null pointer dereference | 3 |

说明：

当前 `source.c` 是从 developer patch 上下文中重构的源码片段，不是完整 Linux 源文件。这样可以支撑 Prompt 实验和中期展示，但不能等同于完整内核源码验证。

## 五、实验设计

### 5.1 三组实验

本项目设置三组实验：

| 组别 | 输入 | Patch 阶段 | 目的 |
|---|---|---|---|
| Baseline | crash report + source | 普通 Patch Prompt | 复现基础流程 |
| With Trace | crash report + source + trace summary | 普通 Patch Prompt | 观察 trace 信息作用 |
| Improved | crash report + source + trace summary | Semantic Guard Patch Prompt | 观察是否减少截肢式修复 |

### 5.2 模型

当前使用模型：

```text
DeepSeek V4 Pro
模型名：deepseek-v4-pro
```

DeepSeek API 已接入项目脚本，并完成真实调用。

### 5.3 输出格式

模型补丁要求使用 replace-based edit JSON：

```json
{
  "edits": [
    {
      "file": "...",
      "original": "...",
      "replaced": "...",
      "reason": "..."
    }
  ],
  "expected_effect": "...",
  "limitations": "..."
}
```

Semantic Guard 组额外要求：

```json
{
  "semantic_preservation_reason": "...",
  "amputation_risk": "low"
}
```

## 六、当前实验结果

### 6.1 模型运行情况

已完成：

```text
8 个真实样本 × 3 组实验 = 24 组真实模型输出
```

所有输出均已保存至：

```text
outputs/baseline/
outputs/with_trace/
outputs/improved/
```

### 6.2 JSON 格式结果

| 指标 | 数量 |
|---|---:|
| 真实模型输出 | 24 |
| JSON 解析失败 | 0 |

说明：

DeepSeek V4 Pro 在当前 Prompt 约束下输出格式较稳定，24 组结果均可解析为 JSON。

### 6.3 轻量 patch 检查结果

检查内容包括：

- `original` 是否能匹配源码片段。
- 是否修改定位文件之外内容。
- `replaced` 是否为空或过短。
- 是否存在大段删除。
- 是否存在提前 return/goto 风险。
- 是否疑似注释或绕过核心功能。
- 是否存在截肢式修复风险。

整体结果：

| 指标 | 数量 |
|---|---:|
| 真实模型输出 | 24 |
| original 匹配成功 | 18 |
| 疑似截肢式修复 | 0 |
| high risk | 0 |
| medium risk | 7 |

分组结果：

| 组别 | 数量 | original 匹配成功 | 疑似截肢 | medium risk | high risk |
|---|---:|---:|---:|---:|---:|
| Baseline | 8 | 7 | 0 | 1 | 0 |
| With Trace | 8 | 6 | 0 | 2 | 0 |
| Improved | 8 | 5 | 0 | 4 | 0 |

### 6.4 当前结果解释

从轻量检查结果可以看出：

1. 模型输出格式稳定，所有 patch 均能解析为 JSON。
2. 大部分 replace-based edit 可以匹配到当前源码片段。
3. 当前未发现明显截肢式修复。
4. Improved 组没有 high risk，但 original 匹配率低于 Baseline，说明 Semantic Guard 是否提升补丁质量还不能直接下结论。
5. 当前结果只能作为轻量静态检查结果，不等同于内核编译通过或 crash 修复成功。

## 七、网上优秀案例学习

本项目已学习 CrashFixer、kGym/kBench 和 syzbot fixed bugs 中的典型案例，并整理为：

```text
docs/online_case_study_summary.md
```

总结出的三类人工评价规则：

### 7.1 Memory Leak

优秀修复应：

- 找到资源分配点。
- 在错误路径补充释放逻辑。
- 使用正确释放函数。
- 不删除正常功能路径。

### 7.2 Out-of-Bounds / UBSAN

优秀修复应：

- 在数组下标、长度、位移量使用前增加检查。
- 只拒绝非法输入。
- 保留合法输入正常路径。

### 7.3 Null Pointer Dereference

优秀修复应：

- 找到真正可能为 NULL 的对象。
- 在首次解引用之前检查。
- 进入已有错误处理路径。
- 不无依据提前 return。

## 八、当前阶段性结论

当前阶段可以得出以下结论：

1. 本项目已经完成真实 kBenchSyz 样本的筛选和标准化整理。
2. CrashFixer 风格的 Hypothesis Generation、Self-Reflection、Patch Generation 流程已经实现。
3. DeepSeek V4 Pro 已经成功接入，并完成 24 组真实模型输出。
4. replace-based edit 格式在当前 Prompt 下较稳定，JSON 解析失败数为 0。
5. 当前轻量检查未发现明显截肢式修复。
6. 由于尚未进行完整人工语义评价和内核动态验证，目前不能宣称模型已经成功修复 Linux 内核 bug。

当前最稳妥的结论是：

> 项目已经从方案设计推进到真实样本实验运行阶段，完成了 DeepSeek V4 Pro 在 8 个 kBenchSyz 样本上的三组 Prompt 实验，并获得可解析、可检查、可进一步人工评价的模型补丁输出。

## 九、目前存在的问题

### 9.1 源码上下文仍不完整

当前 `source.c` 是 patch context excerpt，不是完整 Linux 源码文件。这会影响模型理解，也会影响 `original` 匹配率。

后续可改进：

- 下载对应 Linux kernel commit。
- 根据 `localization_file` 提取完整文件。
- 用完整源码重新运行 Prompt。

### 9.2 尚未完成 plausible/helpful/incorrect 人工评价

当前只完成轻量静态检查，还没有逐条对照 developer patch 打标签。

后续需要填写：

```text
results/evaluation_real_template.csv
```

### 9.3 不能进行真实内核验证

项目当前未接入 kGymSuite，不进行完整 build 和 QEMU reproducer 验证。

汇报中需要明确：

> 本项目采用轻量静态检查 + 人工语义评价，不宣称真实修复成功率。

## 十、下一阶段计划

### 第1步：完成典型样本人工评价

优先评价 3 个典型样本：

| 样本 | 类型 | 原因 |
|---|---|---|
| bug_002 | memory leak | 资源释放路径清楚 |
| bug_005 | out_of_bounds | shift 越界修复直观 |
| bug_006 | null pointer | 空指针 dereference 类型明确 |

每个样本评价三组输出，共 9 条。

### 第2步：扩展到 24 条完整评价

对全部 8 个样本 × 3 组输出进行人工评价，标注：

- plausible
- helpful
- incorrect

### 第3步：生成结果图表

计划生成：

- 三组 patch 质量分布图。
- plausible/helpful/incorrect 分布图。
- trace 对根因判断影响图。
- Semantic Guard 对截肢风险影响图。

### 第4步：完成典型案例分析

每类缺陷选一个案例：

- memory leak
- out-of-bounds
- null pointer

分析 Baseline、With Trace、Improved 三组输出差异。

### 第5步：完善结题报告和 PPT

结题报告将包括：

- 背景与相关工作。
- 数据集和样本筛选。
- Prompt 流程设计。
- DeepSeek 实验结果。
- 人工评价结果。
- 典型案例分析。
- 局限性和未来工作。

## 十一、中期汇报可展示材料

当前可展示材料包括：

| 材料 | 路径 |
|---|---|
| 项目 README | `README.md` |
| 样本表 | `data/selected_bugs.csv` |
| 样本说明 | `docs/selected_cases.md` |
| 网上优秀案例总结 | `docs/online_case_study_summary.md` |
| DeepSeek 运行摘要 | `results/deepseek_midterm_summary.md` |
| 轻量检查汇总 | `results/check_results_summary_deepseek.csv` |
| 中期 PPT 提纲 | `docs/midterm_ppt_outline.md` |
| 本中期汇报文档 | `docs/midterm_presentation_report.md` |

## 十二、中期汇报推荐表述

可以在 PPT 结论页使用以下表述：

> 当前阶段已完成 8 个真实 kBenchSyz 样本的筛选，并使用 DeepSeek V4 Pro 跑通 Baseline、With Trace 和 Semantic Guard 三组实验，共获得 24 组模型输出。所有输出均可解析为 JSON，并完成 replace-based edit 轻量检查。初步结果显示，模型输出格式稳定，未发现明显截肢式修复。但由于尚未完成完整人工语义评价，也未进行内核编译和动态验证，因此当前不宣称修复成功率。下一阶段将对照 developer patch 完成 plausible/helpful/incorrect 人工评价，并生成最终对比图表。

