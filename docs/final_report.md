# 《LLM辅助Linux内核缺陷修复》结项报告

## 摘要

本项目面向 Linux kernel crash / bug fixing 场景，参考 CrashFixer 的两阶段修复思想，构建了一个本科课程项目级别的轻量化 LLM 修复实验框架。项目使用 kBenchSyz 真实样本，设计 Hypothesis Generation、Self-Reflection、Patch Generation 和 Semantic Guard Patch Generation 四类 Prompt，调用 DeepSeek V4 Pro 生成 replace-based edit 补丁，并通过轻量静态检查和人工语义评价分析补丁质量。

本项目共筛选 8 个真实 kBenchSyz 样本，覆盖 memory leak、out-of-bounds 和 null pointer dereference 三类缺陷，并设置 Baseline、With Trace、Improved 三组实验，共得到 24 组模型输出。所有输出均成功解析为 JSON。按照 CrashFixer 论文人工分析中的 plausible / helpful / incorrect 三分类口径，本项目得到：plausible 2/24，helpful 7/24，incorrect 15/24；其中 Improved 组 plausible+helpful 为 4/8，高于 Baseline 的 2/8。

除总体静态与人工评价外，本项目进一步选择 `bug_008` 作为代表案例，在本地 kGymSuite 中完成完整 Linux 内核构建、QEMU/KVM 启动和 syzkaller C reproducer 对照验证：parent 内核约 59 秒复现目标 KASAN 崩溃，LLM improved patched kernel 在 3 次独立、每次 6 分钟的运行中均 clean pass。该结果为补丁可行性提供重复动态证据，但由于只覆盖一个案例和一种 VM 配置，本文不将其外推为总体真实修复成功率。

## 1. 引言

Linux 内核是现代操作系统基础设施的重要组成部分，代码规模庞大，涉及驱动、文件系统、网络协议栈、内存管理和并发控制等复杂模块。Syzkaller 等 fuzzing 工具能够持续发现内核 crash，但 crash report 通常只有 stack trace、sanitizer 日志和 reproducer，缺少自然语言 bug 描述。

大语言模型在代码理解和生成任务上表现突出，但 Linux kernel 自动修复仍然困难。CrashFixer 提出以根因假设生成和补丁生成两阶段流程模拟内核开发者调试过程，为本项目提供了重要参考。

## 2. 项目目标与范围

本项目目标不是完整复现 CrashFixer，也不是构建真实大规模 Linux 内核自动修复平台，而是完成一个可复现、可展示、可评价的小规模课程实验。

输入：

- kBenchSyz 真实 bug 样本。
- crash report。
- source excerpt。
- developer patch。
- trace summary。

输出：

- root-cause hypotheses。
- self-reflection 选择结果。
- replace-based edit 补丁。
- 轻量检查结果。
- 真实 Linux 源码 parent commit 级 patch applicability 核验结果。
- 代表案例的完整内核构建与 reproducer 动态验证结果。
- plausible / helpful / incorrect 人工评价。
- 结果表格、图表和案例分析。

## 3. 参考方法

本项目与 CrashFixer 的流程对照图见 `results/figures/crashfixer_project_flow_comparison.svg`。

CrashFixer 的核心流程包括：

```text
crash report + source code + execution trace
        ↓
Hypothesis Generation
        ↓
Self-Reflection
        ↓
Patch Generation
        ↓
Build / Reproducer Validation
```

本项目在 8 个样本上保留前三个适合本科项目落地的部分并加入 Semantic Guard；在代表案例上补充 Build / Reproducer Validation：

```text
Hypothesis Generation
        ↓
Self-Reflection
        ↓
Patch Generation / Semantic Guard Patch Generation
        ↓
replace-based edit check
        ↓
manual evaluation
        ↓
bug_008: full build + QEMU/KVM + reproducer validation
```

## 4. 数据集与样本

数据来源：

```text
https://huggingface.co/datasets/chenxi-kalorona-huang/kbench/resolve/main/dataset-kb.json
```

本项目从中筛选 8 个样本：

| bug_id | 类型 | 定位文件 |
|---|---|---|
| bug_001 | memory leak | `net/netfilter/nf_tables_api.c` |
| bug_002 | memory leak | `drivers/media/usb/dvb-usb/cinergyT2-core.c` |
| bug_003 | out_of_bounds | `kernel/printk/printk.c` |
| bug_004 | out_of_bounds | `net/xfrm/xfrm_user.c` |
| bug_005 | out_of_bounds | `drivers/usb/usbip/vhci_hcd.c` |
| bug_006 | null_pointer | `mm/filemap.c` |
| bug_007 | null_pointer | `drivers/media/common/videobuf2/videobuf2-core.c` |
| bug_008 | null_pointer | `fs/namespace.c` |

当前 `source.c` 是从 developer patch context 中重构的源码片段，而不是完整 Linux 源文件。这一选择降低了工程复杂度，但也限制了 original 匹配率和补丁语义判断的完整性。

## 5. 实验设计

### 5.1 实验组

三组输入和 Patch 阶段差异见 `results/figures/experiment_group_input_comparison.svg`。

| 组别 | 输入 | Patch 阶段 |
|---|---|---|
| Baseline | crash report + source | 普通 Patch Prompt |
| With Trace | crash report + source + trace summary | 普通 Patch Prompt |
| Improved | crash report + source + trace summary | Semantic Guard Patch Prompt |

### 5.2 模型

本项目使用 DeepSeek V4 Pro：

```text
deepseek-v4-pro
```

### 5.3 补丁格式

所有补丁均要求为 replace-based edit JSON，而不是完整 git diff。

### 5.4 轻量检查

检查项包括：

- JSON 是否可解析。
- `original` 是否匹配源码片段。
- 是否修改定位文件之外内容。
- 是否大段删除。
- 是否提前 return/goto。
- 是否疑似注释或绕过核心功能。
- 是否疑似截肢式修复。

### 5.5 真实源码适用性核验

在 WSL2 Ubuntu 环境中，本项目进一步配置了真实 Linux kernel sparse checkout。核验流程如下：

1. 从 kBench 原始数据读取每个样本的 `parentOfFixCommit` 和 `fixCommits`。
2. 使用官方 kernel.org Linux 仓库进行稀疏 checkout，仅拉取样本定位文件和 `scripts/checkpatch.pl`。
3. 在每个样本的 `parentOfFixCommit` 上执行 developer patch 的 `git apply --check`。
4. 将模型输出的 replace-based edit 应用于真实源码文件。
5. 对模型补丁执行 `git diff --check` 和 `scripts/checkpatch.pl`。

该核验能判断补丁是否可以落到真实 Linux 源码版本上，但仍不等价于完整编译和 reproducer 验证。

## 6. 评价方法

参考 CrashFixer 论文中的人工分析分类，本项目使用三类标签：

| 标签 | 含义 |
|---|---|
| plausible | 与 developer patch 语义基本一致 |
| helpful | 根因或修复方向正确，但补丁不完全等价 |
| incorrect | 根因错误、补丁不可用、无补丁或破坏功能 |

上述 24 个输出的评价标签主要来自人工语义比较，不能等价于总体真实修复成功率。动态验证仅覆盖其中的代表案例 `bug_008 improved`。

## 7. 实验结果

### 7.1 轻量检查结果

| 指标 | 数量 |
|---|---:|
| 真实模型输出 | 24 |
| JSON 解析失败 | 0 |
| original 匹配成功 | 18 |
| 疑似截肢式修复 | 0 |
| high risk | 0 |
| medium risk | 7 |

### 7.2 人工评价结果

整体结果：

| 标签 | 数量 | 比例 |
|---|---:|---:|
| plausible | 2/24 | 8.3% |
| helpful | 7/24 | 29.2% |
| incorrect | 15/24 | 62.5% |
| plausible + helpful | 9/24 | 37.5% |

按实验组：

| 组别 | plausible | helpful | incorrect | plausible+helpful |
|---|---:|---:|---:|---:|
| Baseline | 1/8 | 1/8 | 6/8 | 2/8 |
| With Trace | 0/8 | 3/8 | 5/8 | 3/8 |
| Improved | 1/8 | 3/8 | 4/8 | 4/8 |

按比例：

| 组别 | plausible | helpful | incorrect | plausible+helpful |
|---|---:|---:|---:|---:|
| Baseline | 12.5% | 12.5% | 75.0% | 25.0% |
| With Trace | 0.0% | 37.5% | 62.5% | 37.5% |
| Improved | 12.5% | 37.5% | 50.0% | 50.0% |

### 7.3 Semantic Guard 消融实验

为了单独分析 Semantic Guard 的作用，本项目将 With Trace 设为普通 Patch Prompt 对照组，将 Improved 设为实验组。两组使用相同 crash report、source excerpt、trace summary、Hypothesis Generation 和 Self-Reflection，唯一设计差异是 Patch Generation 阶段是否加入语义保护约束。

| 指标 | With Trace | Improved | 变化 |
|---|---:|---:|---:|
| plausible + helpful | 3/8 (37.5%) | 4/8 (50.0%) | +12.5 pp |
| incorrect | 5/8 (62.5%) | 4/8 (50.0%) | -12.5 pp |
| 真实源码 patch apply ok | 2/8 (25.0%) | 5/8 (62.5%) | +37.5 pp |
| 未生成 edit | 4/8 (50.0%) | 0/8 (0.0%) | -50.0 pp |
| checkpatch warnings | 0 | 2 | +2 |

逐样本配对显示，真实源码适用性的净提升来自 `bug_004`、`bug_006` 和 `bug_008`。其中 `bug_008` 符合最小局部修改、保留正常路径和关注 cleanup/lifetime 的约束，并与 developer patch 相同。Semantic Guard 最明显的作用是减少 no edit 并促进具体修复尝试，但 `bug_002`、`bug_007` 也由 no edit 变为不可应用补丁，说明更多尝试不等于全部更正确。

禁止删除、注释和绕过核心逻辑没有产生可单独测量的提升，因为普通 Prompt 组同样没有疑似截肢式修复，存在 floor effect。由于每个配置只运行一次，该消融是小样本相关性观察，不是确定因果证明。完整分析见 `results/semantic_guard_ablation.md`。

### 7.4 Memory Leak 失败案例分析

两个 memory leak 样本在三组实验中产生 6 个输出，结果全部为 incorrect，真实源码 patch apply ok 为 0/6。

| 子集 | plausible | helpful | incorrect | patch apply ok |
|---|---:|---:|---:|---:|
| 2 个 memory leak × 3 组 | 0/6 | 0/6 | 6/6 | 0/6 |

`bug_001` 三组均生成 edit，但均无法应用到真实 parent 源码。`bug_002` 的 Baseline 和 With Trace 没有生成 edit；Improved 虽生成补丁，却把“frontend 已获得、后续 I/O 失败时缺少 release”的泄漏误修为 attach 后 NULL check。

该负结果说明 crash trace 更容易提供症状和分配位置，而不是完整资源所有权图；局部 source excerpt 也难以表达跨调用 acquire-transfer-release、部分初始化失败和 goto cleanup 链。Semantic Guard 能约束如何修改，却不能在上下文不足时自动推导哪个对象应由谁在何时释放。完整分析见 `results/memory_leak_failure_analysis.md`。

### 7.5 真实 Linux 源码适用性核验

从 LLM 输出到真实源码核验的分层证据链见 `results/figures/llm_to_kernel_evidence_chain.svg`。

本项目在 WSL2 Ubuntu 中使用真实 Linux kernel sparse checkout，对 8 个样本的 `parentOfFixCommit` 执行补丁适用性检查。结果如下：

| 组别 | patch apply ok | diff check ok | checkpatch 结果 |
|---|---:|---:|---:|
| Developer Patch | 8/8 (100.0%) | - | - |
| Baseline | 3/8 (37.5%) | 3/8 (37.5%) | 0 errors, 0 warnings |
| With Trace | 2/8 (25.0%) | 2/8 (25.0%) | 0 errors, 0 warnings |
| Improved | 5/8 (62.5%) | 5/8 (62.5%) | 0 errors, 2 warnings |

其中 developer patch 8/8 均可在真实 parent commit 上应用，说明样本版本可解析。模型输出方面，Improved/Semantic Guard 组有 5/8 个 replace-based edit 能直接应用到真实源码并通过 `git diff --check`，高于 Baseline 的 3/8 和 With Trace 的 2/8。

需要注意：该结果只能说明补丁具备真实源码适用性和基本格式合法性，不能证明补丁语义正确，也不能替代完整内核编译或 syzkaller reproducer 验证。

### 7.6 单样本局部编译对照验证

为了进一步增强工程验证，本项目选择人工评价为 plausible 且真实源码适用性通过的 `bug_008 improved` 输出进行三路局部编译对照。原始有缺陷版本、developer patch 和 LLM improved patch 均使用相同 parent commit、工具链、`defconfig` 流程和编译目标。

| 项目 | 内容 |
|---|---|
| bug_id | `bug_008` |
| group | `improved` |
| parent commit | `197b6b60ae7bc51dd0814953c562833143b292aa` |
| Linux version | `Linux 6.3-rc4` |
| source file | `fs/namespace.c` |
| compile target | `fs/namespace.o` |

对照结果：

| 版本 | patch apply | `make defconfig` | `make fs/namespace.o` | 目标文件 SHA-256 前缀 |
|---|---|---|---|---|
| parent 原始版本 | 不适用 | pass | pass | `8abccf3ac28a...` |
| developer patch | pass | pass | pass | `bad2f34483c0...` |
| LLM improved patch | pass | pass | pass | `bad2f34483c0...` |

编译日志中出现：

```text
CC      fs/namespace.o
```

三种版本均能完成目标文件编译，说明“可编译”本身不能证明 crash 已被修复。进一步比较发现，developer patch 与 LLM improved patch 的源码 diff 相同，编译生成的 `fs/namespace.o` SHA-256 也完全一致，而 parent 原始版本的对象哈希不同。这为该案例中 LLM 补丁与 developer patch 的编译产物等价性提供了额外证据。

该结果在动态验证之前建立了编译层证据。完整哈希与三路日志保存在 `results/local_compile_comparison/`。

### 7.7 bug_008 完整构建与动态复现验证

本项目在 WSL2 本地部署 kGymSuite，以相同 parent commit、内核配置、userspace image、syzkaller checkout 和 C reproducer 对 parent 与 LLM improved patch 进行对照。开发者补丁与 LLM improved 补丁在换行规范化后内容相同，因此未重复消耗一次完整构建进行 developer 动态组。

| 项目 | parent 原始版本 | LLM improved patch |
|---|---|---|
| kGymSuite job | `00000009` | 初始 `0000000a`；正式重复 `00000016`–`00000018` |
| 完整内核构建 | pass | pass |
| 构建耗时 | 4318.1 秒 | 4123.2 秒 |
| 验证窗口 | 最多 5 分钟 | 3 次 × 6 分钟 |
| 目标崩溃 | 约 59 秒触发 | 未触发 |
| 目标 crash | `KASAN: null-ptr-deref Read in sys_mount_setattr` | 无 |
| syzkaller 结果 | 复现率 100%，`imageAbility=normal` | 3/3 clean pass，target/special crash 均为 0，`imageAbility=normal` |

parent 组证明输入样本和 reproducer 在当前环境中有效。补丁组在 3 次独立、每次 6 分钟的正式窗口内均未出现目标 KASAN 报告，为该补丁的可行性提供了更强的重复动态证据。

初始 `0000000a` 的静默告警来自 pinned syzkaller 只认可包含 `executing program` 或 `executed programs:` 的活性输出。最终复现器使用独立子进程每 10 秒输出协议心跳，并保持主 reproducer 无节流运行。正式三轮均由 syz-crush 记录为 `running long enough, stopping`，无 target crash、无 special crash、无 worker exception。完整报告见 `results/dynamic_validation/repeated_dynamic_validation_report.md`。

### 7.8 结果解释

1. DeepSeek V4 Pro 在当前 Prompt 下 JSON 输出稳定。
2. Trace 信息提升了 helpful 数量，但没有提升 plausible 数量。
3. Semantic Guard 组的 plausible+helpful 数最高，为 4/8。
4. 在真实源码适用性核验中，Semantic Guard 组 patch apply ok 数量最高，为 5/8。
5. 消融比较中，Semantic Guard 将 no edit 从 4/8 降到 0/8、源码适用从 2/8 提升到 5/8，但新增 2 个 checkpatch warning。
6. memory leak 类样本最难，6 个输出均 incorrect 且 0/6 可应用，暴露 ownership/cleanup 分析不足。
7. `bug_008` 三路局部编译均通过，且 developer patch 与 LLM improved patch 的目标文件哈希一致。
8. `bug_008` parent 动态复现目标 crash，而 improved 在 3 次 × 6 分钟中均 clean pass，初步支持补丁可行并降低单次偶然性。
9. Semantic Guard 没有产生明显截肢式修复，但也不能证明它一定提升真实修复正确性。
10. out-of-bounds 类样本更容易生成 helpful 输出。

## 8. 典型案例

详见：

```text
docs/final_case_studies.md
```

代表案例：

- bug_002：memory leak，模型未能补全正确资源释放路径。
- bug_005：UBSAN shift-out-of-bounds，模型能生成边界检查但错误路径不完全等价。
- bug_008：null pointer / cleanup ordering，Baseline 和 Improved 均生成 plausible patch。

## 9. 局限性

1. 当前源码是 patch context excerpt，不是完整 Linux 源文件。
2. 完整内核构建和 syzkaller 动态验证只覆盖 `bug_008`，其余 7 个样本仍停留在源码适用性与人工评价层。
3. patched 动态验证虽已达到 3 次 × 6 分钟 clean pass，但仍只覆盖单一 VM 配置和一个 bug。
4. 样本规模只有 8 个，不能代表大规模统计结论。
5. 人工评价存在主观性，但已按 developer patch 进行逐条说明。

## 10. 结论

本项目完成了一个基于 CrashFixer 思想的 Linux kernel crash 修复轻量实验框架，在 8 个真实 kBenchSyz 样本上运行 DeepSeek V4 Pro，获得 24 组模型输出，并完成轻量检查、真实源码适用性核验、单样本三路局部编译对照、完整内核构建、动态复现验证和人工语义评价。

按照 CrashFixer 风格的 plausible/helpful/incorrect 分类，最终得到：

```text
plausible: 2/24
helpful: 7/24
incorrect: 15/24
plausible + helpful: 9/24
```

按组看，Improved/Semantic Guard 的 plausible+helpful 比例最高，为 50.0%，真实源码 patch apply ok 为 5/8。严格消融显示，它相较普通 Trace Prompt 将 useful 提升 12.5 个百分点、源码适用提升 37.5 个百分点，主要收益是减少 no edit 并促进最小局部修改；但新增 warning 和失败尝试说明收益并非无代价。memory leak 子集 6/6 incorrect 则明确揭示方法无法仅凭局部上下文恢复复杂资源 ownership。

在 `bug_008` 中，developer 与 LLM improved 的源码 diff 和对象哈希一致，parent 约 59 秒复现目标 crash，而 improved 在 3 次独立、每次 6 分钟的运行中均 clean pass。这形成了“语义评价、消融解释、源码适用、局部编译、完整构建、重复动态复现”的分层证据链，初步说明方案可行。由于样本规模小且动态验证仅覆盖一个案例，结论仍是阶段性观察，而不是总体修复成功率或确定性因果证明。

## 11. 交付物

| 内容 | 路径 |
|---|---|
| 项目说明 | `README.md` |
| 真实样本 | `data/selected/` |
| Prompt 模板 | `prompts/` |
| 实验脚本 | `src/` |
| 模型输出 | `outputs/` |
| 轻量检查结果 | `results/check_results_summary_deepseek.csv` |
| 真实源码核验结果 | `results/kernel_verify_summary.csv` |
| 真实源码核验摘要 | `results/kernel_verify_summary.md` |
| 局部编译对照结果 | `results/local_compile_comparison/summary.md` |
| 局部编译对照原始表 | `results/local_compile_comparison/summary.csv` |
| 动态验证报告 | `results/dynamic_validation/dynamic_validation_report.md` |
| 动态验证原始证据 | `results/dynamic_validation/` |
| 人工评价表 | `results/evaluation_real.csv` |
| 评价工作簿 | `results/evaluation.xlsx` |
| 评价统计 | `results/evaluation_summary.md` |
| 当前结果总览 | `results/current_experiment_results.md` |
| Semantic Guard 消融 | `results/semantic_guard_ablation.md` |
| Memory Leak 失败分析 | `results/memory_leak_failure_analysis.md` |
| 图表 | `results/figures/` |
| CrashFixer 流程对照图 | `results/figures/crashfixer_project_flow_comparison.svg` |
| 三组实验输入差异图 | `results/figures/experiment_group_input_comparison.svg` |
| 真实源码核验证据链图 | `results/figures/llm_to_kernel_evidence_chain.svg` |
| 典型案例 | `docs/final_case_studies.md` |
| 实验复现指南 | `docs/reproduction_guide.md` |
| 交付索引 | `docs/final_deliverables.md` |
| 答辩一页摘要 | `docs/final_defense_brief.md` |
