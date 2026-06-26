# Memory Leak 失败案例：汇报页

## 负结果

| 子集 | plausible | helpful | incorrect | 源码 apply ok |
|---|---:|---:|---:|---:|
| 2 个 memory leak × 3 组 | 0/6 | 0/6 | 6/6 | 0/6 |

## 六个输出发生了什么

- `bug_001`：三组都生成 edit，但都无法应用到真实 parent 源码。
- `bug_002 Baseline/With Trace`：认为上下文不足，没有生成 edit。
- `bug_002 Improved`：把错误路径资源泄漏误修为 attach 后 NULL check，没有执行 frontend `release()`。

## 为什么失败

1. leak trace 指向未释放对象或分配栈，不一定暴露遗漏 cleanup 的分支。
2. source excerpt 缺少完整 acquire-transfer-release 控制流。
3. Semantic Guard 能限制补丁形式，但不能自动推导资源 ownership。
4. NULL 防护不能替代“资源已获得、后续步骤失败”时的 rollback。

## 方法边界

当前方案较适合局部边界检查和语句重排，不擅长跨调用 ownership、多阶段初始化和 cleanup 链。

## 改进方向

- 输入完整目标函数和 cleanup helper。
- 生成 resource ledger：acquire、owner、transfer、release、error exits。
- 使用 ownership-aware reflection 逐条检查错误返回路径。

> 该负结果与 `bug_008` 成功案例共同说明：Semantic Guard 可以改善局部修复，但不能替代完整控制流与资源所有权分析。
