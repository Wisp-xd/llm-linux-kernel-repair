# kGymSuite 工具架构理解

## 1. 本项目对 kGymSuite 的定位

kGymSuite 是 CrashFixer 用于大规模 Linux kernel crash 修复实验的平台。它负责内核构建、虚拟机运行、crash 复现、补丁预检查、任务调度和执行轨迹提取。

本课程项目不完整部署 kGymSuite，而是将其作为方法理解和报告分析对象。实际实验采用数据驱动 Prompt 流程，不依赖完整 Linux kernel build、QEMU reproducer 或 kDump 动态轨迹提取。

## 2. 核心模块

### kbuilder

负责 Linux kernel 构建。CrashFixer 论文中强调完整内核构建耗时较高，因此 kGymSuite 通过缓存和增量构建降低实验成本。

本项目中的对应降阶：

- 不执行真实内核构建。
- 用 `check_patch.py` 做 original 匹配、删除检测、提前 return 检测等轻量检查。

### kvmmanager

负责启动 QEMU/GCP 虚拟机，运行 crash reproducer，收集 crash 日志。

本项目中的对应降阶：

- 不启动虚拟机。
- 直接使用 kBenchSyz 中已有 crash report。

### kprebuilder

负责补丁快速预编译检查，用于过滤明显不可编译的补丁候选。

本项目中的对应降阶：

- 不做真实编译。
- 检查 replace-based edit 是否能匹配源码，并识别明显危险修改。

### kscheduler

负责调度构建、运行、检查等任务，支持大规模并发实验。

本项目中的对应降阶：

- 不做分布式调度。
- 用 Python 脚本逐个样本运行。

### kclient

提供客户端 API，连接任务调度、数据集和执行平台。

本项目中的对应降阶：

- 用 `load_bug.py` 和 `experiment_runner.py` 作为轻量客户端。

### kDump + crash-trace

用于从内核执行中提取最小执行轨迹，帮助 LLM 关注 crash 前后的相关函数。

本项目中的对应降阶：

- 不进行真实 kDump 轨迹提取。
- 从 crash report 的 stack trace 人工整理 `trace_summary.txt`。

## 3. 为什么中期不完整部署 kGymSuite

完整部署需要 Linux 服务器、Docker、QEMU、内核源码、复现脚本和较长调试时间。对于本科课程项目，中期目标应优先保证：

- 研究问题明确。
- 数据处理流程清楚。
- Prompt 实验链路可运行。
- 评价标准可执行。

因此，本项目采取“工具架构理解 + 小样本 Prompt 实验”的路线。

