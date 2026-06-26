# bug_008 三次重复动态验证报告

## 目标

对 LLM improved patched kernel 连续执行 3 次独立验证，每次不少于 5 分钟，并消除原始 `no output from test machine` 特殊告警。

## 看门狗问题与修复

固定 syzkaller commit 的 `MonitorExecution` 不会把任意 stdout 当作活性。它只在输出包含以下标记时刷新执行时间：

```text
executing program
executed programs:
```

最初的 `KGYM_HEARTBEAT` 虽出现在 VM 日志中，但不被监控器认可，因此仍触发 `no output from test machine`。最终方案使用独立子进程每 10 秒输出：

```text
executing program: KGYM_HEARTBEAT_INDEPENDENT ...
```

子进程通过 `PR_SET_PDEATHSIG` 与主 reproducer 生命周期绑定。正式实验不增加循环节流，原 reproducer 主循环速度保持不变；唯一行为性增量是监控协议心跳。

## 配置

| 项目 | 配置 |
|---|---|
| patched kernel | 复用 job `0000000a` 的 VM image 和 vmlinux |
| syz-crush 窗口 | 每轮 6 分钟 |
| 重复次数 | 3 |
| VM | QEMU，2 vCPU，2048 MB |
| instance / proc | 1 / 2 |
| 心跳 | 独立进程，每 10 秒，包含 `executing program` 标记 |
| 主循环节流 | 0 ms，保持原始压力 |

## 正式结果

| 轮次 | job | syz-crush 结果 | target crash | special crash | imageAbility | 结论 |
|---|---|---|---:|---:|---|---|
| 1 | `00000016` | `running long enough, stopping` | 0 | 0 | `normal` | clean pass |
| 2 | `00000017` | `running long enough, stopping` | 0 | 0 | `normal` | clean pass |
| 3 | `00000018` | `running long enough, stopping` | 0 | 0 | `normal` | clean pass |

汇总：

```text
clean pass: 3/3
target crash: 0/3
special crash: 0/3
worker exception: 0/3
configured validation time: 6 min x 3 = 18 min
```

## 结论

与 parent job `00000009` 约 59 秒复现目标 KASAN crash、复现率 100% 相比，patched kernel 在 3 次独立、每次 6 分钟的运行中均未复现目标 crash，并且旧的静默看门狗告警已完全消除。该结果显著降低了单次运行偶然性的影响，为 `bug_008` 补丁可行性提供了更强的动态证据。

结论仍限于单个 bug、单一 VM 配置和总计 18 分钟验证，不构成长期稳定性或全体模型输出真实修复率的证明。

## 证据

正式结果目录：

```text
results/dynamic_validation/bug008_protocol_heartbeat_repeated_3x/
```

每轮包含 `context.json`、`summary.json`、`reproducer.c`、`syz-crush.log` 和 job id。机器可读汇总为 `results/dynamic_validation/repeated_dynamic_validation_summary.json`。

诊断过程中产生的 bounded-exit、未识别心跳、paced heartbeat 等尝试均保留，但不计入正式 3 次结果。
