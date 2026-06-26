# 网上优秀案例学习总结

## 1. 学习目标

本项目需要对 LLM 生成的 Linux kernel crash 修复结果进行人工评价。为了避免评价标准过于主观，本次参考了以下公开案例来源：

- CrashFixer 论文及其 kBenchSyz 示例。
- kGym / kBench 论文中对 Linux kernel crash resolution benchmark 的说明。
- syzbot fixed bugs 页面中已由开发者修复的真实样本。
- Linux kernel commit / mailing list 中可见的短补丁案例。

学习目标不是照抄网上结果，而是提炼出适合本项目的人工评价规则：什么样的 patch 可以算 plausible，什么样只能算 helpful，什么样应判 incorrect。

## 2. 关键参考来源

### 2.1 CrashFixer

CrashFixer 的核心经验是：不要让模型直接从 crash report 生成 patch，而是先生成根因假设，再基于假设生成补丁。论文还指出，部分模型补丁虽然可能让 crash 消失，但会通过删除、绕过或大幅改写功能代码形成 amputation-style repair。

对本项目的启发：

- 人工评价不能只看 crash 是否可能消失。
- 必须判断补丁是否保留原有功能语义。
- `plausible / helpful / incorrect` 三分类适合本科项目复用。

### 2.2 kGym / kBench

kGym 论文说明 kBench 样本包含 crash stack trace、reproducer、developer-written fix 等信息，非常适合作为 Linux kernel crash 修复基准。论文也强调，即使给模型定位文件，Linux kernel crash 修复仍然很难。

对本项目的启发：

- 小样本实验是合理的，重点是流程完整和评价可信。
- 不能把轻量静态检查等同于真实修复成功。
- developer patch 是人工评价的重要参照答案。

### 2.3 syzbot fixed bugs

syzbot fixed bugs 页面提供了真实 crash 标题、reproducer 状态、子系统、fix commit 等信息。典型页面中可以看到例如：

- `memory leak in nft_chain_parse_hook`
- `UBSAN: shift-out-of-bounds in vhci_hub_control`
- `memory leak in nf_tables_parse_netdev_hooks`

对本项目的启发：

- 优先选择 fixed bugs，因为它们有开发者补丁可对照。
- 优先选择 `C repro`、单文件、短补丁样本。
- 避免锁、RCU、并发、跨文件大改样本。

## 3. 典型优秀案例模式

### 3.1 Memory Leak 类

代表案例：

- `memory leak in cinergyt2_fe_attach`
- `memory leak in nft_chain_parse_hook`
- `memory leak in nf_tables_parse_netdev_hooks`

优秀 developer patch 的共同模式：

1. 找到资源分配点，例如 `kmalloc`、`kzalloc`、`attach`、hook list allocation。
2. 找到错误路径或失败路径。
3. 在失败路径补充正确释放逻辑。
4. 不删除正常功能路径。
5. 使用领域内正确释放函数，而不是随意 `kfree`。

人工评价要点：

| 评价点 | plausible | helpful | incorrect |
|---|---|---|---|
| 根因 | 找到具体泄漏资源和路径 | 找到泄漏方向但资源不精确 | 把 leak 误判为 null deref 或 OOB |
| 补丁 | 在正确错误路径释放资源 | 释放位置接近但函数/顺序有疑问 | 直接 return 或跳过分配逻辑 |
| 语义 | 正常路径不变 | 正常路径基本保留 | 删除核心功能或破坏引用计数 |

本项目对应样本：

- `bug_001`: `memory leak in nft_chain_parse_hook`
- `bug_002`: `memory leak in cinergyt2_fe_attach`

建议作为中期案例：

- `bug_002` 更适合展示，因为 media/DVB frontend attach 类型相对直观，developer patch 较短。

### 3.2 Out-of-Bounds / UBSAN 类

代表案例：

- `UBSAN: shift-out-of-bounds in vhci_hub_control`
- `KASAN: slab-out-of-bounds Read`
- `KASAN: vmalloc-out-of-bounds Write`

优秀 developer patch 的共同模式：

1. 不删除触发 crash 的功能逻辑。
2. 在使用数组下标、长度、位移量之前增加检查。
3. 对 shift-out-of-bounds，重点检查 shift size 是否超出类型宽度。
4. 对 buffer OOB，重点检查 `len`、`index`、`offset`、`count`。
5. 正常输入路径保持原行为。

人工评价要点：

| 评价点 | plausible | helpful | incorrect |
|---|---|---|---|
| 根因 | 明确指出越界变量或 shift 参数 | 方向是边界检查但变量不精确 | 误判为内存泄漏或空指针 |
| 补丁 | 增加必要边界检查且保留正常路径 | 检查条件可能不完整 | 删除访问逻辑或直接跳过功能 |
| 语义 | 只拒绝非法输入 | 有保守拒绝风险 | 大面积禁用功能 |

本项目对应样本：

- `bug_003`: out-of-bounds
- `bug_004`: out-of-bounds
- `bug_005`: `UBSAN: shift-out-of-bounds in vhci_hub_control`

建议作为中期案例：

- `bug_005` 最适合展示，因为 UBSAN shift-out-of-bounds 的修复目标很清楚：保护 shift size。

### 3.3 Null Pointer Dereference 类

代表案例：

- `KASAN: null-ptr-deref Read in filemap_fault`
- `KASAN: null-ptr-deref Read in __vb2_buf_mem_free`
- `KASAN: null-ptr-deref Read in sys_mount_setattr`

优秀 developer patch 的共同模式：

1. 找到真正可能为 NULL 的对象。
2. 在第一次解引用之前检查。
3. 如果对象为 NULL，进入已有错误处理路径。
4. 不用过宽的提前 return 掩盖真实问题。
5. 不改变对象非空时的原有逻辑。

人工评价要点：

| 评价点 | plausible | helpful | incorrect |
|---|---|---|---|
| 根因 | 找到正确 NULL 对象 | 找到空指针方向但对象不完全对 | 误判为 OOB 或 leak |
| 补丁 | 在解引用前加精确检查 | 加了检查但返回值/错误路径有疑问 | 无依据提前 return，绕过核心逻辑 |
| 语义 | 非 NULL 路径保持不变 | 可能过于保守 | 破坏正常调用流程 |

本项目对应样本：

- `bug_006`: `KASAN: null-ptr-deref Read in filemap_fault`
- `bug_007`: `KASAN: null-ptr-deref Read in __vb2_buf_mem_free`
- `bug_008`: `KASAN: null-ptr-deref Read in sys_mount_setattr`

建议作为中期案例：

- `bug_006` 适合展示，因为 null-ptr-deref 类型清楚，人工判断路径较直接。

## 4. 对本项目人工评价的改进

学习这些案例后，人工评价不应只看 `check_result.json`，而应采用四步：

1. 看 crash report：确认 crash 类型和关键函数。
2. 看 developer patch：总结真实修复逻辑。
3. 看模型 hypothesis：判断根因方向是否正确。
4. 看模型 patch：判断是否接近 developer patch，是否保留功能语义。

建议对每个 patch 写一句评价理由：

```text
Root cause direction is correct, but the generated edit does not match the developer cleanup path.
```

或：

```text
The patch adds a bounds check before the shift operation and keeps the normal path unchanged, so it is plausible.
```

## 5. 推荐中期展示案例

中期不用展示 24 条全部人工评价，建议展示 3 个代表案例：

| 案例 | 类型 | 推荐原因 |
|---|---|---|
| bug_002 | memory leak | 资源释放逻辑清晰，适合解释 leak 修复 |
| bug_005 | out_of_bounds | shift-out-of-bounds 修复判断直观 |
| bug_006 | null_pointer | 空指针 dereference 类型清楚 |

展示方式：

```text
Crash Report 摘要
Developer Patch 修复逻辑
Baseline 输出
With Trace 输出
Semantic Guard 输出
人工评价标签
```

## 6. 最终可沉淀的评价规则

### Plausible

满足：

- 根因与 developer patch 一致。
- 修改位置相同或语义等价。
- patch 可应用或只存在轻微格式差异。
- 无截肢式修复。

### Helpful

满足：

- 根因方向基本正确。
- 能帮助人工定位问题。
- patch 不完全等价，或存在错误路径、返回值、释放函数选择等小问题。

### Incorrect

满足任一：

- 根因错误。
- patch 不可应用且不是简单格式问题。
- 删除、注释、绕过核心功能。
- 对 memory leak 使用错误释放函数。
- 对 OOB 直接禁用功能路径。
- 对 null pointer 无依据提前 return。

## 7. 对当前实验结果的解释建议

当前 DeepSeek V4 Pro 已生成 24 个真实样本输出，轻量检查显示：

- JSON 解析失败数为 0。
- 没有明显截肢式修复。
- improved 组没有出现 high risk，但 original 匹配率不高。

因此，中期报告应写：

> 当前结果说明实验链路已经可运行，模型输出格式较稳定，Semantic Guard 在轻量检查下未产生明显截肢式修复。但由于当前 source.c 为 patch context excerpt，且尚未完成人工语义评价，不能直接得出 Semantic Guard 提升补丁质量的结论。

下一步：

- 对 `bug_002`、`bug_005`、`bug_006` 先完成 9 条人工评价。
- 再扩展到 24 条完整人工评价。
- 生成 plausible / helpful / incorrect 分布图。

