# 《LLM辅助Linux内核缺陷修复》实验复现指南

本文档用于复现本项目的样本整理、三组 LLM 实验、轻量检查、人工评价统计、真实 Linux 源码适用性核验、单样本三路局部编译对照，以及 `bug_008` 的 kGymSuite 动态验证。

## 1. 复现范围

项目包含四层验证：

1. Prompt 实验：8 个真实 kBenchSyz 样本，Baseline、With Trace、Improved 三组，共 24 个模型输出。
2. 真实源码适用性核验：在每个样本的 `parentOfFixCommit` 上执行 patch apply、diff check 和 checkpatch。
3. 局部编译对照：分别对 `bug_008` parent 原始版本、developer patch 和 LLM improved patch 执行 `make defconfig` 和 `make fs/namespace.o`。
4. 动态对照：在 kGymSuite 中完整构建 `bug_008` parent 与 LLM improved 内核，并在 QEMU/KVM 中运行相同 syzkaller C reproducer。

动态验证只覆盖一个代表样本，不包含 24 个模型输出的全量动态验证，也不构成对 CrashFixer 的完整复现。

## 2. 当前验证环境

| 项目 | 当前环境 |
|---|---|
| Windows | Windows + PowerShell |
| 项目目录 | `D:\SQA\llm-linux-kernel-repair` |
| Python | 3.11 虚拟环境 `.venv` |
| LLM | DeepSeek V4 Pro |
| Linux 环境 | WSL2 Ubuntu 24.04 |
| WSL 存储位置 | `D:\SQA\wsl\Ubuntu` |
| Linux 源码源 | kernel.org 官方仓库 |
| 局部编译版本 | Linux 6.3-rc4 |
| 动态验证 | kGymSuite + Docker + QEMU/KVM + syzkaller |
| WSL 资源 | 12 GB 内存、6 vCPU、8 GB swap |

建议将数据、Linux 源码、虚拟环境和编译缓存放在 D 盘，避免占用系统盘。

## 3. 项目目录

```text
llm-linux-kernel-repair/
├── data/selected/             8 个正式样本
├── prompts/                   四类 Prompt 模板
├── src/                       实验、检查和统计脚本
├── outputs/baseline/          Baseline 输出
├── outputs/with_trace/        With Trace 输出
├── outputs/improved/          Semantic Guard 输出
├── results/                   评价、核验、图表和编译日志
├── docs/                      报告与说明文档
└── requirements.txt
```

## 4. Windows Python 环境

在 PowerShell 中执行：

```powershell
cd D:\SQA\llm-linux-kernel-repair

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\requirements.txt
```

检查环境：

```powershell
python --version
python -c "import requests, openpyxl; print('python environment ok')"
```

预期输出包含：

```text
Python 3.11.x
python environment ok
```

如果 PowerShell 禁止激活脚本，可直接使用：

```powershell
.\.venv\Scripts\python.exe .\src\run_all_groups.py --help
```

## 5. API 配置

### 5.1 临时配置

仅对当前 PowerShell 窗口生效：

```powershell
$env:DEEPSEEK_API_KEY="your_api_key"
$env:DEEPSEEK_THINKING="disabled"
```

### 5.2 持久配置

写入 Windows 当前用户环境变量：

```powershell
[Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "your_api_key", "User")
[Environment]::SetEnvironmentVariable("DEEPSEEK_THINKING", "disabled", "User")
```

设置后需要重新打开 PowerShell。检查变量是否存在时不要打印完整密钥：

```powershell
$key = [Environment]::GetEnvironmentVariable("DEEPSEEK_API_KEY", "User")
if ($key) { "API key configured, length=$($key.Length)" } else { "API key missing" }
```

安全要求：

- 不要把真实 API key 写入 `.env.example`、README、实验日志或 GitHub；
- 不要在截图、PPT和答辩演示中显示完整密钥；
- 如果密钥曾公开，应立即在服务商控制台撤销并重新生成。

## 6. kBenchSyz 数据准备

当前仓库已经包含整理后的 8 个样本，可直接跳到第 7 节。需要从原始数据重新导出时执行以下步骤。

下载数据到 D 盘：

```powershell
New-Item -ItemType Directory -Force D:\SQA\kbench_data_fresh | Out-Null
Invoke-WebRequest `
  -Uri "https://huggingface.co/datasets/chenxi-kalorona-huang/kbench/resolve/main/dataset-kb.json" `
  -OutFile "D:\SQA\kbench_data_fresh\dataset-kb.json"
```

导出固定的 8 个样本：

```powershell
cd D:\SQA\llm-linux-kernel-repair
.\.venv\Scripts\python.exe .\src\prepare_kbench_selected.py `
  --dataset D:\SQA\kbench_data_fresh\dataset-kb.json `
  --out-dir .\data\selected
```

检查：

```powershell
Get-ChildItem .\data\selected -Directory
Import-Csv .\data\selected_bugs.csv | Format-Table bug_id,bug_type,localization_file
```

预期存在 `bug_001` 至 `bug_008`。每个目录至少包含：

```text
crash_report.txt
source.c
developer_patch.diff
trace_summary.txt
metadata.json
```

注意：`source.c` 是由 developer patch context 重构的源码片段，不是完整 Linux 源文件。真实源码核验在第 11 节单独完成。

## 7. 低成本流程测试

在调用真实 API 前，先用 mock provider 测试完整流程：

```powershell
cd D:\SQA\llm-linux-kernel-repair
.\.venv\Scripts\python.exe .\src\run_all_groups.py `
  --provider mock `
  --limit 1 `
  --summary-out .\results\run_all_summary_mock_check.json
```

成功标准：

- 命令正常退出；
- `outputs/baseline/bug_001/`、`outputs/with_trace/bug_001/`、`outputs/improved/bug_001/` 中生成 JSON 文件；
- summary 文件记录 3 次运行。

Mock 输出仅用于检查流程，不计入正式实验结果。

## 8. 运行三组真实 LLM 实验

正式实验命令：

```powershell
cd D:\SQA\llm-linux-kernel-repair

$env:DEEPSEEK_API_KEY = [Environment]::GetEnvironmentVariable("DEEPSEEK_API_KEY", "User")
$env:DEEPSEEK_THINKING = "disabled"

.\.venv\Scripts\python.exe .\src\run_all_groups.py `
  --provider deepseek `
  --model deepseek-v4-pro `
  --temperature 0.2 `
  --summary-out .\results\run_all_summary_deepseek.json
```

实验规模：

```text
8 bugs × 3 groups × 3 LLM stages = 72 API calls
```

三组输入：

| 组别 | 输入 | Patch Prompt |
|---|---|---|
| Baseline | crash report + source | 普通 Patch Generation |
| With Trace | crash report + source + trace summary | 普通 Patch Generation |
| Improved | crash report + source + trace summary | Semantic Guard |

每个输出目录应包含：

```text
hypotheses.json
reflection.json
patch.json
check_result.json
run_metadata.json
```

注：`run_metadata.json` 由当前 `src/experiment_runner.py` 生成，用于记录 provider、模型、token usage、API 成本和重试次数；部分早期历史输出可能缺少该文件。

运行单个样本可使用：

```powershell
.\.venv\Scripts\python.exe .\src\run_improved.py `
  --bug-dir .\data\selected\bug_008 `
  --provider deepseek `
  --model deepseek-v4-pro
```

注意：重复运行会更新对应输出目录。正式复现实验前应备份需要保留的历史输出，并记录模型名、temperature 和运行日期。

## 9. Replace-based Edit 轻量检查

对已有输出重新执行检查：

```powershell
.\.venv\Scripts\python.exe .\src\recheck_outputs.py `
  --selected-dir .\data\selected `
  --outputs-dir .\outputs
```

汇总 24 个正式输出，排除 demo：

```powershell
.\.venv\Scripts\python.exe .\src\collect_check_results.py `
  --outputs-dir .\outputs `
  --selected-only `
  --exclude-demo `
  --out .\results\check_results_summary_deepseek.csv
```

检查项包括：

- `original` 是否能在源码片段中匹配；
- 是否只修改定位文件；
- 是否大段删除；
- 是否出现无依据提前 return；
- 是否注释或绕过核心逻辑；
- 是否存在 amputation risk；
- reason 是否存在。

当前正式结果基准：

| 指标 | 结果 |
|---|---:|
| 输出数 | 24 |
| JSON 解析失败 | 0 |
| original 匹配成功 | 18 |
| 疑似截肢式修复 | 0 |
| high risk | 0 |
| medium risk | 7 |

## 10. 人工评价与统计

生成 developer patch、模型 patch 和检查结果的对照材料：

```powershell
.\.venv\Scripts\python.exe .\src\export_review_pack.py
```

人工评价记录在：

```text
results/evaluation_real.csv
```

主要字段：

```text
bug_id
bug_type
group
root_cause_correct
patch_applicable
semantic_similarity
amputation_risk
final_label
comment
```

标签标准：

- plausible：与 developer patch 语义基本一致；
- helpful：根因或修复方向正确，但补丁不完全等价；
- incorrect：根因错误、补丁不可用、无补丁、破坏功能或属于截肢式修复。

生成统计和图表：

```powershell
.\.venv\Scripts\python.exe .\src\summarize_evaluation.py `
  --evaluation .\results\evaluation_real.csv

.\.venv\Scripts\python.exe .\src\summarize_extra_metrics.py
```

当前基准结果：

| 组别 | plausible | helpful | incorrect | plausible+helpful |
|---|---:|---:|---:|---:|
| Baseline | 1/8 | 1/8 | 6/8 | 2/8 (25.0%) |
| With Trace | 0/8 | 3/8 | 5/8 | 3/8 (37.5%) |
| Improved | 1/8 | 3/8 | 4/8 | 4/8 (50.0%) |

整体结果：plausible 2/24，helpful 7/24，incorrect 15/24，plausible+helpful 9/24。

人工评价不是 kernel build 或 reproducer 验证结果，不能表述为真实修复成功率。

## 11. 真实 Linux 源码适用性核验

### 11.1 前置条件

- WSL2 Ubuntu 可正常启动；
- WSL 中存在 `git`、`perl` 和 `python3`；
- 网络可访问 kernel.org；
- 建议将 WSL 虚拟磁盘或核验仓库存放在 D 盘。

检查：

```powershell
wsl -d Ubuntu -- bash -lc "git --version; perl --version | head -1; python3 --version"
```

### 11.2 导出 commit 信息

该脚本从原始 kBench JSON 中提取 `fix_commit` 和 `parentOfFixCommit`：

```powershell
cd D:\SQA\llm-linux-kernel-repair
.\.venv\Scripts\python.exe .\src\export_kernel_verify_cases.py
```

预期生成：

```text
results/kernel_verify_cases.json
```

### 11.3 执行核验

```powershell
wsl -d Ubuntu -- bash -lc "cd /mnt/d/SQA/llm-linux-kernel-repair && python3 src/kernel_verify_wsl.py --repo-dir /home/wisp/linux-kernel-verify/linux"
```

当前 WSL 已整体迁移到 D 盘，所以 `/home/wisp/...` 实际存储在 `D:\SQA\wsl\Ubuntu\ext4.vhdx` 内。

重新生成摘要：

```powershell
.\.venv\Scripts\python.exe .\src\summarize_kernel_verify.py
```

成功标准：

- 8 个 parent commit 均 checkout 成功；
- 8/8 developer patch 通过 `git apply --check`；
- 生成 `results/kernel_verify_summary.csv` 和 `.md`。

当前基准结果：

| 组别 | patch apply ok | diff check ok |
|---|---:|---:|
| Developer Patch | 8/8 | - |
| Baseline | 3/8 | 3/8 |
| With Trace | 2/8 | 2/8 |
| Improved | 5/8 | 5/8 |

## 12. bug_008 三路局部编译对照

### 12.1 验证对象

```text
bug_id: bug_008
parent commit: 197b6b60ae7bc51dd0814953c562833143b292aa
Linux version: 6.3-rc4
source file: fs/namespace.c
target: fs/namespace.o
```

### 12.2 当前工具链

项目使用无 sudo 的 micromamba 工具链：

```text
/home/wisp/micromamba-bin/bin/micromamba
/home/wisp/kernel-build-env
```

环境中包含 make、GCC、flex、bison、OpenSSL 和 elfutils/libelf。

真实 Linux 源码树：

```text
/home/wisp/linux-local-compile/linux
```

### 12.3 执行命令

```powershell
wsl -d Ubuntu -- bash -lc "cd /mnt/d/SQA/llm-linux-kernel-repair && python3 src/local_compile_compare_wsl.py"
```

脚本自动执行：

1. checkout `197b6b60ae7bc51dd0814953c562833143b292aa`；
2. 编译未应用补丁的 parent 原始版本；
3. 应用 `data/selected/bug_008/developer_patch.diff` 并编译；
4. 应用 `outputs/improved/bug_008/patch.json` 并编译；
5. 三个版本分别执行 `make defconfig` 和 `make fs/namespace.o`；
6. 保存源码 diff、编译日志、对象 SHA-256 和汇总表。

成功标准：三个 variant 的 `checkout_ok`、`defconfig_ok` 和 `local_compile_ok` 均为 true；developer 与 LLM 的 `patch_apply` 均为 passed。

当前结果：

| variant | patch apply | defconfig | local compile | SHA-256 前缀 |
|---|---|---|---|---|
| parent | 不适用 | pass | pass | `8abccf3ac28a...` |
| developer | pass | pass | pass | `bad2f34483c0...` |
| llm_improved | pass | pass | pass | `bad2f34483c0...` |

编译日志应包含：

```text
CC      fs/namespace.o
```

产物：

```text
results/local_compile_comparison/summary.json
results/local_compile_comparison/summary.csv
results/local_compile_comparison/summary.md
results/local_compile_comparison/parent/
results/local_compile_comparison/developer/
results/local_compile_comparison/llm_improved/
```

developer patch 与 LLM improved patch 的源码 diff 和目标文件 SHA-256 完全一致，parent 对象哈希不同。局部编译和对象一致性只能提供编译层证据，不能证明 crash 已经动态消失。

## 13. bug_008 kGymSuite 动态验证

### 13.1 前置环境

动态验证使用同级目录 `D:\SQA\third_party\kGymSuite`。需要 WSL2、Docker、`/dev/kvm` 和约 12 GB 可用内存。当前实验使用 1 个 kbuilder 与 1 个 kvmmanager worker，以降低本机内存压力。

```powershell
wsl -d Ubuntu -- bash -lc "test -e /dev/kvm && echo KVM_OK"
wsl -d Ubuntu -- bash -lc "cd /mnt/d/SQA/third_party/kGymSuite && DEPLOYMENT=local docker compose --project-directory . -f deployment/local/compose.yml up -d"
```

### 13.2 提交与判定

`src/run_kgym_bug008.py` 从动态验证数据集读取 parent commit、内核配置和 C reproducer，并提交 kbuilder 与 kvmmanager 两阶段任务。先运行 parent 确认目标 crash 可复现，再使用 parent kCache 提交 `llm_improved`。

| variant | job | 判定 |
|---|---|---|
| parent | `00000009` | 目标 KASAN crash 约 59 秒复现 |
| llm_improved 初始 | `0000000a` | 目标 crash 未复现，但有旧看门狗告警 |
| llm_improved 重复验证 | `00000016`–`00000018` | 3 次 × 6 分钟 clean pass |

developer patch 与 LLM improved patch 在 LF 规范化后内容相同，因此动态阶段省略重复 developer 任务。结果判定必须同时检查目标 crash 标题、特殊 crash、`imageAbility` 和原始 `syz-crush.log`。

重复验证使用 `src/run_kgym_bug008_repeated.py`，复用 `0000000a` 的 patched VM image，跳过内核重编译。固定 syzkaller 只把包含 `executing program` 或 `executed programs:` 的输出视为活性，因此脚本使用独立子进程每 10 秒输出协议心跳，并通过 `PR_SET_PDEATHSIG` 绑定主 reproducer 生命周期。正式运行不增加循环节流。

结果保存在：

```text
results/dynamic_validation/dynamic_validation_report.md
results/dynamic_validation/dynamic_validation_summary.json
results/dynamic_validation/parent_job_00000009/
results/dynamic_validation/llm_improved_job_0000000a/
results/dynamic_validation/repeated_dynamic_validation_report.md
results/dynamic_validation/repeated_dynamic_validation_summary.json
results/dynamic_validation/bug008_protocol_heartbeat_repeated_3x/
```

任务完成后仅停止服务，以保留镜像和编译缓存：

```powershell
wsl -d Ubuntu -- bash -lc "cd /mnt/d/SQA/third_party/kGymSuite && DEPLOYMENT=local docker compose --project-directory . -f deployment/local/compose.yml stop"
```

## 14. 重新生成 Excel 交付物

```powershell
.\.venv\Scripts\python.exe .\src\export_evaluation_xlsx.py `
  --out .\results\evaluation.xlsx
```

工作簿应包含：

```text
Overview
Samples
Manual Evaluation
Group Summary
Patch Checks
Kernel Verify
Compile Compare
Local Compile
```

## 15. 最终一致性检查

在提交前执行：

```powershell
cd D:\SQA\llm-linux-kernel-repair

(Get-ChildItem .\outputs\baseline -Directory | Where-Object Name -like "bug_0*").Count
(Get-ChildItem .\outputs\with_trace -Directory | Where-Object Name -like "bug_0*").Count
(Get-ChildItem .\outputs\improved -Directory | Where-Object Name -like "bug_0*").Count

Get-Content .\results\evaluation_summary.md
Get-Content .\results\kernel_verify_summary.md
Get-Content .\results\local_compile_comparison\summary.json
```

预期：

- 三个输出目录各有 8 个正式样本；
- `evaluation_real.csv` 有 24 条评价记录；
- kernel verify 有 32 条记录：8 条 developer + 24 条模型输出；
- local compile comparison 的三个 variant 均通过，developer 与 LLM 对象哈希一致。

## 16. 常见问题

### 16.1 关闭 PowerShell 后 API key 消失

`$env:DEEPSEEK_API_KEY=...` 只对当前终端有效。使用用户环境变量持久保存，并重新打开终端。

### 16.2 `_ssl` 导入失败

不要继续使用损坏的系统 Python。重新创建 Python 3.11 虚拟环境，并安装 `requirements.txt`。

### 16.3 DeepSeek 输出不是 JSON

- 保持 `DEEPSEEK_THINKING=disabled`；
- 使用较低 temperature，例如 0.2；
- 检查 `run_metadata.json` 和原始响应；
- 对失败样本单独重跑，不要修改评价表伪造结果。

### 16.4 GitHub 在 WSL 中连接失败

真实源码核验脚本默认使用 kernel.org 官方仓库，不依赖 GitHub。

### 16.5 developer patch 在 WSL 中无法 apply

kBench patch 可能使用 CRLF。核验脚本会先归一化为 LF，再执行 `git apply --check`。

### 16.6 `.git/index.lock` 存在

先确认没有 git 进程运行：

```powershell
wsl -d Ubuntu -- bash -lc "ps -eo pid,cmd | grep '[g]it' || true"
```

确认没有 git 进程后，再移除中断遗留的单个锁文件。

### 16.7 `gelf.h` 缺失

这是 objtool 缺少 libelf 开发头文件。当前工具链已经安装 elfutils，并在局部编译脚本中配置了 include/lib 路径。

### 16.8 WSL 占用 C 盘

WSL 的 `/home` 默认可能存储在 C 盘的 `ext4.vhdx`。本项目已将 Ubuntu 迁移到：

```text
D:\SQA\wsl\Ubuntu\ext4.vhdx
```

后续大文件应优先放在 D 盘。不要直接删除 `ext4.vhdx`，否则会破坏整个 Ubuntu 发行版。

## 17. 结果真实性边界

复现完成后可以证明：

- 使用了 8 个真实 kBenchSyz 样本；
- 获得了 24 个真实 LLM 输出；
- 完成了 CrashFixer-style 人工评价；
- 完成了真实 Linux parent commit 级源码适用性核验；
- `bug_008` 三路均通过 `fs/namespace.o` 局部编译，developer 与 LLM 对象哈希一致。
- `bug_008` parent 约 59 秒复现目标 KASAN crash；LLM improved 在 3 次 × 6 分钟中均 clean pass。

不能据此证明：

- 9/24 输出是真实修复成功；
- Semantic Guard 必然提升所有内核缺陷修复效果；
- 其余 7 个样本已经通过完整内核构建或动态验证；
- 3 次 × 6 分钟未复现可以证明补丁在所有调度和长期负载下正确。

报告中应使用“人工语义评价结果”“真实源码适用性”“局部编译通过”和“`bug_008` 重复动态验证 3/3 clean pass”等分层表述，不使用“总体真实修复成功率”描述当前结果。

## 18. 最小复现命令清单

已具备样本和输出时，只重新生成全部结果：

```powershell
cd D:\SQA\llm-linux-kernel-repair

.\.venv\Scripts\python.exe .\src\recheck_outputs.py --selected-dir .\data\selected --outputs-dir .\outputs
.\.venv\Scripts\python.exe .\src\collect_check_results.py --outputs-dir .\outputs --selected-only --exclude-demo --out .\results\check_results_summary_deepseek.csv
.\.venv\Scripts\python.exe .\src\summarize_evaluation.py --evaluation .\results\evaluation_real.csv
.\.venv\Scripts\python.exe .\src\summarize_extra_metrics.py
.\.venv\Scripts\python.exe .\src\summarize_kernel_verify.py
.\.venv\Scripts\python.exe .\src\export_evaluation_xlsx.py --out .\results\evaluation.xlsx
```

重新调用模型时，再执行第 8 节的 `run_all_groups.py`。
