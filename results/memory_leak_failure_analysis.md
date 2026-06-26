# Memory Leak 失败案例分析

## 1. 分析范围

正式样本中有 2 个 memory leak：

- `bug_001`：`net/netfilter/nf_tables_api.c`
- `bug_002`：`drivers/media/usb/dvb-usb/cinergyT2-core.c`

每个样本分别运行 Baseline、With Trace、Improved/Semantic Guard，共 6 个输出。人工评价结果为：

```text
plausible: 0/6
helpful: 0/6
incorrect: 6/6
```

真实源码核验中，这 6 个输出没有一个 patch apply ok：`bug_001` 三组均为 fail；`bug_002` 的 Baseline 与 With Trace 为 no edit，Improved 为 fail。

## 2. 六个输出逐项分析

| 样本 | 组别 | 输出/核验表现 | incorrect 的直接原因 | 失败类型 |
|---|---|---|---|---|
| `bug_001` | Baseline | 生成 edit；真实源码 apply fail | 修改无法落到真实 parent 源码，不能建立与 developer cleanup 逻辑的等价性 | 源码 grounding 失败 |
| `bug_001` | With Trace | 生成 edit；真实源码 apply fail | trace 没有解决补丁上下文与真实源码不匹配，仍不可执行 | trace 对 ownership 信息不足 |
| `bug_001` | Improved | 生成 edit；真实源码 apply fail | Semantic Guard 约束了补丁形式，但没有补足资源所有权和完整错误路径 | 语义保护不等于资源分析 |
| `bug_002` | Baseline | no edit | 模型认为上下文不足并拒绝修复，没有补全错误路径的资源释放 | 拒绝生成 |
| `bug_002` | With Trace | no edit | trace 仍未提供 frontend 资源由谁持有、应在哪个失败分支释放的信息 | trace 无法恢复 ownership |
| `bug_002` | Improved | 生成 edit；真实源码 apply fail | 增加 attach 后的 NULL check，而 developer patch 是在 `dvb_usb_generic_rw()` 失败时调用 frontend `release()`；防护对象和错误路径均不一致 | 将 leak 误修为 NULL 防护 |

说明：对于 `bug_001`，当前证据能够确定三个补丁均无法应用到真实 parent 源码，因而不能作为可执行修复；在无法重新读取原始输出的情况下，本报告不进一步虚构具体函数级错误。

## 3. 典型失败：bug_002

### Developer Patch 的正确语义

`cinergyt2_fe_attach()` 已经创建或持有 frontend 资源。当后续 `dvb_usb_generic_rw()` 返回错误时，函数直接离开会遗失该资源，因此 developer patch 在错误路径中执行：

```c
adap->fe_adap[0].fe->ops.release(adap->fe_adap[0].fe);
```

修复重点不是“frontend 是否为 NULL”，而是“资源成功获得后，后续步骤失败时必须回滚释放”。

### 为什么三个 Prompt 都失败

1. Baseline 只看到 crash/source excerpt，无法可靠恢复 acquire-use-release 关系，最终拒绝生成。
2. With Trace 增加了调用栈信息，但调用栈描述 leak 被检测的位置，不一定显示遗漏释放的控制流分支，因此仍拒绝生成。
3. Semantic Guard 虽强调资源释放和保留行为，但模型把问题转化成 attach 后 NULL check。该检查可能提高空指针安全性，却没有处理“已成功获得资源、随后 I/O 失败”的泄漏路径。

该案例展示了一个关键区别：

```text
allocation/attach 失败 -> NULL check
allocation/attach 成功 + later operation 失败 -> rollback/release
```

模型识别了资源相关代码，却没有识别资源状态转换发生在哪条路径上。

## 4. 共性失败机制

### 4.1 Crash trace 更接近症状，不等于资源所有权图

Memory leak 报告通常能指出最终未释放的对象或分配栈，但未必包含遗漏 cleanup 的返回分支。Trace 可以帮助定位对象来源，却不能直接回答：

- 谁拥有该资源？
- ownership 在哪个调用后转移？
- 哪些错误返回必须执行 rollback？
- 是否已有统一 cleanup label？

这解释了 With Trace 在 memory leak 上仍为 0/2 useful。

### 4.2 Source excerpt 缺少完整控制流

本项目的 `source.c` 由 developer patch context 重构，不是完整 Linux 源文件。对于边界检查或局部顺序错误，片段可能足够；对于 memory leak，正确修复通常依赖函数前后多个资源获取步骤、goto label 和调用者/被调用者约定，片段信息明显不足。

### 4.3 Semantic Guard 只能限制“怎么改”，不能自动推导“该释放什么”

Semantic Guard 能阻止删除、注释和绕过核心逻辑，并鼓励最小修改和资源清理。但如果模型没有正确恢复 ownership，它仍可能：

- 对错误对象增加 NULL check；
- 在错误时机释放资源；
- 漏掉 ownership 已转移的情况；
- 生成形式保守但语义无效的补丁。

### 4.4 拒绝生成与错误生成是两种不同风险

6 个输出中至少有 2 个 no edit，另外 4 个没有通过真实源码应用。前者安全但无帮助，后者更危险，因为补丁表面完整却不可执行或语义错误。评价框架应分别报告 no edit、unappliable 和 semantic mismatch，而不只汇总为 incorrect。

## 5. 方法边界

该失败组说明当前方法更适合以下问题：

- 局部边界条件；
- 明确的 NULL 检查；
- 小范围语句顺序调整；
- crash 点附近即可解释的缺陷。

当前方法不擅长：

- 跨多个调用的资源所有权；
- 多阶段初始化和部分失败回滚；
- 依赖完整 goto cleanup 链的修复；
- 并发释放和引用计数协议。

因此，Improved 组总体 useful 率和源码适用率提高，并不意味着它对所有 bug 类型都有效。memory leak 子集 0/6 useful 是一个明确的负结果，应与 `bug_008` 成功案例同时汇报。

## 6. 针对性改进

1. 输入完整目标函数及直接调用的 cleanup helper，而不只输入 patch context。
2. 在 Prompt 中显式生成资源账本：resource、acquire、owner、transfer、release、error exits。
3. 先枚举每个 return/goto 路径，再判断资源是否平衡。
4. 增加 ownership-specific reflection，要求区分 NULL 防护和 rollback cleanup。
5. 将 `git apply --check`、编译和静态资源分析结果反馈给模型进行第二轮修正。
6. 对 memory leak 单独设计 Prompt，不与 out-of-bounds/null pointer 共用完全相同的修复模板。

## 7. 可汇报结论

> Memory leak 的 6 个输出全部 incorrect，说明当前 Prompt 流程能约束补丁形态，但无法仅凭局部源码和 crash trace稳定恢复跨路径资源所有权。Trace 没有带来 useful 提升，Semantic Guard 也把其中一个 leak 误修为 NULL 防护。该负结果界定了方法的适用范围，并表明后续需要完整控制流、资源账本和 ownership-aware 验证。
