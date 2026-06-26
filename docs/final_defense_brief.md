# 结项答辩一页摘要

## 一句话定位

本项目参考 CrashFixer，将 Linux 内核崩溃修复拆分为根因假设、自反思筛选、补丁生成和语义保护，并通过从人工评价到动态复现的分层证据验证 LLM 补丁。

## 核心产出

| 层级 | 范围 | 结果 |
|---|---|---|
| LLM 实验 | 8 个 kBenchSyz bug，3 组，24 个输出 | JSON 解析成功 24/24 |
| 人工语义评价 | 24 个输出 | plausible 2，helpful 7，incorrect 15 |
| 分组对比 | 每组 8 个输出 | plausible+helpful：Baseline 25%，With Trace 37.5%，Improved 50% |
| 真实源码适用性 | 8 个 bug | patch apply：Baseline 3/8，With Trace 2/8，Improved 5/8 |
| 局部编译 | `bug_008` 三路对照 | 全部通过；developer 与 LLM 对象哈希一致 |
| 动态验证 | `bug_008` parent / improved | parent 约 59 秒复现；improved 3 次 × 6 分钟均 clean pass |
| Semantic Guard 消融 | With Trace / Improved | useful 3/8→4/8；patch apply 2/8→5/8；no edit 4/8→0/8 |
| 失败案例 | 2 个 memory leak × 3 组 | 6/6 incorrect，0/6 patch apply ok |

## 最重要结论

1. Semantic Guard 组在本小样本实验中获得最高的人工有用率和真实源码适用率。
2. `bug_008` 建立了完整证据链：补丁语义与 developer 一致、真实源码可应用、局部编译产物一致、完整内核可构建、动态测试未复现目标崩溃。
3. 因此可以初步认为方案可行，但不能宣称 24 个输出具有 37.5% 的真实修复成功率。
4. Memory leak 的 0/6 useful 表明方法对跨路径 ownership 和复杂 cleanup 链仍不适用。

## 三分钟讲稿

本项目研究大语言模型能否辅助修复 Linux 内核崩溃。我们参考 CrashFixer，把流程拆成根因假设生成、自反思和补丁生成，并增加 Semantic Guard，要求模型避免删除、注释或绕过核心功能。

实验使用 8 个真实 kBenchSyz 样本，设置 Baseline、With Trace 和 Improved 三组，共获得 24 个 DeepSeek V4 Pro 输出。所有输出均可解析。人工评价中，Improved 组 plausible 加 helpful 为 4/8，高于 Baseline 的 2/8；在真实 Linux parent commit 上，Improved 补丁可应用 5/8，同样是三组最高。

为了避免只停留在人工判断，我们选择 `bug_008` 做深入验证。LLM improved 补丁与开发者补丁相同，局部编译对象哈希一致；随后在本地 kGymSuite 中完整编译内核并运行 syzkaller reproducer。原始内核约 59 秒复现 KASAN 空指针崩溃，补丁内核在 3 次独立、每次 6 分钟的运行中均 clean pass。

因此，本项目的结论是：Semantic Guard 在当前小样本中表现出提升补丁可用性的趋势，并且至少一个代表案例获得了重复动态支持。局限是动态验证仍只有一个案例和一种 VM 配置，后续需要扩大样本。

消融实验进一步说明，在相同 trace 输入下，Semantic Guard 将真实源码适用率从 2/8 提升到 5/8，主要通过减少 no edit、鼓励最小局部修改实现；但 memory leak 的 6 个输出全部 incorrect，说明它不能替代资源 ownership 和完整控制流分析。

## 答辩口径

可以说：

- “Improved 组的人工有用率为 50%，真实源码适用率为 62.5%。”
- “`bug_008` 重复动态验证 3/3 clean pass，目标崩溃和 special crash 均未出现。”
- “项目形成了从 Prompt、静态检查、真实源码、编译到动态复现的闭环。”

不要说：

- “LLM 的真实修复成功率是 37.5% 或 50%。”
- “所有 8 个 bug 都通过了内核编译和动态验证。”
- “补丁已经被证明完全正确。”

## 常见问答

**为什么只动态验证一个样本？**

完整内核构建和 VM 验证资源成本较高，因此先选择同时满足 plausible、真实源码可应用且能与 developer 对照的代表案例建立端到端证据。

**原来的 patched run 告警如何解决？**

固定 syzkaller 只把包含 `executing program` 或 `executed programs:` 的输出视为执行活性。最终使用独立子进程发送协议心跳，并保持主 reproducer 无节流；3 次正式运行均无告警。

**Semantic Guard 是否确定有效？**

不能下确定因果结论。当前结果是 8 个样本上的趋势，需要更多样本、重复实验和模型对照。
