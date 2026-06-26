# 结项报告增补：Memory Leak 失败案例

本项目的两个 memory leak 样本在三组实验中共得到 6 个输出，人工评价全部为 incorrect，真实源码 patch apply ok 为 0/6。这一结果是项目的重要负结果，而不是应被隐藏的异常值。

`bug_001` 的三组模型均生成 edit，但均无法应用到真实 parent 源码，说明 trace 和 Semantic Guard 没有解决源码 grounding 与 cleanup path 恢复问题。`bug_002` 的 Baseline 和 With Trace 没有生成 edit；Improved 虽生成补丁，却将“frontend 已获得、后续 I/O 失败时缺少 release”的资源泄漏误修为 attach 后 NULL check。

该子集表明，crash trace 更容易提供症状和分配位置，而不是完整的资源所有权图。局部 source excerpt 对边界检查和语句重排可能足够，但难以表达跨调用 acquire-transfer-release、部分初始化失败和 goto cleanup 链。Semantic Guard 能约束“如何修改”，却不能在上下文不足时自动推导“哪个对象应由谁在何时释放”。

因此，本项目的方法边界应表述为：当前流程对局部、可在 crash 附近解释的缺陷更有效；对 memory leak、跨路径 ownership 和复杂 cleanup 协议仍需要完整函数上下文、资源账本、控制流分析以及静态/动态反馈。

完整逐项分析见 `results/memory_leak_failure_analysis.md`，汇报页见 `docs/memory_leak_failure_slide.md`。
