# bug_008 动态验证报告

## 实验目标

验证 `bug_008` 的原始 Linux 内核能否复现目标崩溃，以及应用 LLM improved 补丁后目标崩溃是否仍会出现。

目标崩溃：

```text
KASAN: null-ptr-deref Read in sys_mount_setattr
```

## 控制变量

- Linux parent commit：`197b6b60ae7bc51dd0814953c562833143b292aa`
- syzkaller checkout：`fbf0499acc828df26995835e51d83c3a0117e716`
- 验证平台：本地 kGymSuite、Docker、QEMU/KVM
- VM：1 个实例，2 个进程，2 GB 内存
- reproducer：相同 syzkaller C reproducer
- 初始验证窗口：5 分钟
- 重复验证窗口：3 次，每次 6 分钟

## 实验结果

| 指标 | parent | LLM improved |
|---|---|---|
| job id | `00000009` | `0000000a` |
| 完整内核构建 | pass | pass |
| 构建耗时 | 4318.1 秒 | 4123.2 秒 |
| 目标崩溃 | 复现 | 未复现 |
| 动态表现 | 约 59 秒触发，复现率 100% | 完整 5 分钟内无目标 KASAN 报告 |
| imageAbility | `normal` | `warning` |
| 其他结果 | 无 | `no output from test machine` 特殊看门狗告警 |

初始 `0000000a` 的 target crash 判定为未复现，但存在特殊看门狗告警。随后修正心跳协议并复用同一个 patched kernel image，完成正式重复验证：

| 轮次 | job | 窗口 | target crash | special crash | imageAbility |
|---|---|---|---:|---:|---|
| 1 | `00000016` | 6 分钟 | 0 | 0 | `normal` |
| 2 | `00000017` | 6 分钟 | 0 | 0 | `normal` |
| 3 | `00000018` | 6 分钟 | 0 | 0 | `normal` |

## 结论

parent 组成功复现目标崩溃，证明 reproducer 和验证环境有效。LLM improved patched kernel 在 3 次独立、每次 6 分钟的正式运行中均未复现目标 crash，且 3 次均无 special crash、无 worker exception、`imageAbility=normal`。因此可以初步认为该补丁在 `bug_008` 上可行，证据强于原先的单次告警结果。

原始告警的根因是 pinned syzkaller 只把包含 `executing program` 或 `executed programs:` 的输出视为执行活性，普通心跳文本不会刷新 watchdog。最终复现器使用独立子进程输出协议标记，并保持原始主循环无节流运行，成功获得 `3/3 clean pass`。

该结论仍有明确边界：动态验证只覆盖一个 bug、一种 VM 配置和总计 18 分钟，不能外推为总体真实修复成功率或长期稳定性证明。

## 证据索引

| 内容 | 路径 |
|---|---|
| 机器可读摘要 | `results/dynamic_validation/dynamic_validation_summary.json` |
| parent 任务上下文 | `results/dynamic_validation/parent_job_00000009_context.json` |
| parent syz-crush 日志 | `results/dynamic_validation/parent_job_00000009/syz-crush.log` |
| parent KASAN report | `results/dynamic_validation/parent_job_00000009/0/report0` |
| improved 任务上下文 | `results/dynamic_validation/llm_improved_job_0000000a_context.json` |
| improved syz-crush 日志 | `results/dynamic_validation/llm_improved_job_0000000a/syz-crush.log` |
| 三次重复验证报告 | `results/dynamic_validation/repeated_dynamic_validation_report.md` |
| 三次重复验证摘要 | `results/dynamic_validation/repeated_dynamic_validation_summary.json` |
| 三次原始证据 | `results/dynamic_validation/bug008_protocol_heartbeat_repeated_3x/` |
| 实验检查点 | `results/dynamic_validation/checkpoint_20260618.json` |
