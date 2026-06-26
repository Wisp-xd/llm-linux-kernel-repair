# 典型案例分析

本节选取 3 个代表性样本，分别覆盖 memory leak、out-of-bounds 和 null pointer dereference。每个案例均对照 developer patch，比较 Baseline、With Trace 和 Improved/Semantic Guard 的输出。

## Case 1: bug_002 - memory leak in cinergyt2_fe_attach

### 基本信息

- 类型：memory leak
- 定位文件：`drivers/media/usb/dvb-usb/cinergyT2-core.c`
- developer patch 大小：2 行新增

### Developer Patch 修复逻辑

developer patch 在 `dvb_usb_generic_rw()` 返回错误时，检查 `adap->fe_adap[0].fe` 是否存在，并调用：

```c
adap->fe_adap[0].fe->ops.release(adap->fe_adap[0].fe);
```

核心语义是：前面已经创建或持有的 frontend 资源在错误路径上没有释放，因此需要补全资源释放逻辑。

### 模型输出对比

| 组别 | 结果 | 人工标签 | 原因 |
|---|---|---|---|
| Baseline | 未生成 edit | incorrect | 模型认为上下文不足，未给出补丁 |
| With Trace | 未生成 edit | incorrect | trace 未帮助模型定位 developer cleanup path |
| Improved | 增加 attach 后 NULL check | incorrect | 不是 developer patch 的资源释放路径，不能解决该 leak |

### 案例结论

memory leak 类 bug 对模型较难。模型容易把资源泄漏误解为空指针检查问题，而不是补全错误路径释放逻辑。Semantic Guard 虽然要求“优先释放资源”，但在该样本中仍未生成正确 release 逻辑。

## Case 2: bug_005 - UBSAN shift-out-of-bounds in vhci_hub_control

### 基本信息

- 类型：out_of_bounds / UBSAN
- 定位文件：`drivers/usb/usbip/vhci_hcd.c`
- developer patch 大小：2 行新增

### Developer Patch 修复逻辑

developer patch 在执行位移操作前增加：

```c
if (wValue >= 32)
    goto error;
```

核心语义是：`1 << wValue` 中 `wValue` 大于等于 32 时会触发 shift-out-of-bounds，因此必须在位移前拒绝非法输入。

### 模型输出对比

| 组别 | 结果 | 人工标签 | 原因 |
|---|---|---|---|
| Baseline | 将 `1` 改为 `1U` | incorrect | unsigned shift 仍不能解决 shift count >= 32 的问题 |
| With Trace | 增加 `wValue < 32` 条件 | helpful | 根因方向正确，但非法输入被静默跳过，不等同 developer 的 `goto error` |
| Improved | 增加 `wValue < 32` 条件并解释语义保护 | helpful | 保留合法路径，但仍未使用 developer 的错误路径 |

### 案例结论

out-of-bounds 类 bug 对模型相对友好。Trace 和 Semantic Guard 都能帮助模型生成接近正确方向的边界检查，但还需要人工审查错误路径是否与 developer patch 一致。

## Case 3: bug_008 - KASAN null-ptr-deref in sys_mount_setattr

### 基本信息

- 类型：null_pointer / use-after-free-like cleanup ordering
- 定位文件：`fs/namespace.c`
- developer patch 大小：2 行位置调整

### Developer Patch 修复逻辑

developer patch 将：

```c
namespace_unlock();
if (err)
    cleanup_group_ids(mnt, NULL);
```

调整为：

```c
if (err)
    cleanup_group_ids(mnt, NULL);
namespace_unlock();
```

核心语义是：在释放 namespace lock 之前完成 cleanup，避免 `mnt` 生命周期变化导致非法访问。

### 模型输出对比

| 组别 | 结果 | 人工标签 | 原因 |
|---|---|---|---|
| Baseline | 与 developer patch 相同的重排 | plausible | 修改位置和语义均与 developer patch 一致 |
| With Trace | 未生成 edit | incorrect | 模型认为上下文不足，错过了已给出的修复位置 |
| Improved | 与 developer patch 相同的重排 | plausible | 语义保护解释完整，保留原 cleanup 逻辑 |

### 三路局部编译对照

在真实 Linux 6.3-rc4 parent commit 上，分别编译 parent 原始版本、developer patch 和 LLM improved patch：

| 版本 | `fs/namespace.o` | SHA-256 前缀 |
|---|---|---|
| parent 原始版本 | pass | `8abccf3ac28a...` |
| developer patch | pass | `bad2f34483c0...` |
| LLM improved patch | pass | `bad2f34483c0...` |

parent 原始版本也能编译，因此编译成功本身不能证明 crash 被修复；但 developer patch 与 LLM improved patch 的源码 diff 和对象哈希均一致，为该案例中的补丁等价性提供了额外的编译层证据。

### 完整构建与动态验证

| 版本 | job | 完整构建 | syzkaller reproducer |
|---|---|---|---|
| parent | `00000009` | pass | 约 59 秒复现目标 KASAN crash，复现率 100% |
| LLM improved | `00000016`–`00000018` | pass | 3 次 × 6 分钟均 clean pass，无 target/special crash |

parent 组验证了 reproducer 的有效性；improved 组没有再次出现 `KASAN: null-ptr-deref Read in sys_mount_setattr`。通过独立子进程发送 syzkaller 认可的 `executing program` 心跳后，三次正式运行均由 syz-crush 正常停止，旧的 `no output from test machine` 告警不再出现。

### 案例结论

该样本说明，当 developer patch 是局部重排且上下文足够时，LLM 可以生成接近真实修复的补丁。Semantic Guard 在该案例中没有改变补丁形态，但提升了补丁解释质量；源码 diff、对象哈希、完整构建和动态对照共同表明 LLM patch 在该案例上与 developer patch 等价，并获得初步运行时支持。

## 综合观察

1. memory leak 样本最难，模型需要准确理解错误路径和资源释放函数。
2. out-of-bounds 样本较适合 Prompt 实验，模型通常能生成边界检查，但错误路径细节仍需人工审查。
3. null pointer / 生命周期类样本中，若修复为局部重排，模型有机会生成 plausible patch。
4. Semantic Guard 没有直接保证更高 plausible 数，但 improved 组的 useful output 数量最高。
5. 单案例动态验证表明，静态 plausible 结论可以进一步通过 parent 复现与 patched 对照建立运行时证据。
