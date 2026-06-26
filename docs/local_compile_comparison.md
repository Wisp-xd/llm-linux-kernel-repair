# bug_008 三路局部编译对照

## 1. 验证目的

本实验在同一个真实 Linux parent commit 上，对以下三个版本进行局部编译：

1. parent 原始有缺陷版本；
2. 应用 developer patch 的版本；
3. 应用 LLM Improved / Semantic Guard patch 的版本。

目标是建立比单独编译 LLM patch 更完整的对照链，并检查 developer patch 与 LLM patch 是否产生一致的目标文件。

## 2. 控制变量

| 项目 | 值 |
|---|---|
| bug_id | `bug_008` |
| parent commit | `197b6b60ae7bc51dd0814953c562833143b292aa` |
| Linux version | Linux 6.3-rc4 |
| 定位文件 | `fs/namespace.c` |
| 编译目标 | `fs/namespace.o` |
| 架构 | x86 |
| 配置 | `make defconfig` |
| 编译器 | `x86_64-conda-linux-gnu-gcc 15.2.0` |

三个版本使用相同的源码基线、工具链、配置过程和编译目标，仅补丁状态不同。

## 3. 补丁关系

Developer patch 将 `cleanup_group_ids()` 移动到 `namespace_unlock()` 之前，避免解锁后对象生命周期变化导致非法访问。

LLM Improved patch 生成了相同的操作顺序调整。保存的 `git diff` 文件 SHA-256 一致，说明两个补丁对 `fs/namespace.c` 产生了相同文本修改。

```text
developer diff SHA-256: aaada1c354dc08037e59c17567ccd8bb908ce5e4d845a5f0da06f07ddc75832b
LLM diff SHA-256:       aaada1c354dc08037e59c17567ccd8bb908ce5e4d845a5f0da06f07ddc75832b
```

## 4. 编译结果

| 版本 | patch apply | defconfig | `fs/namespace.o` | 对象 SHA-256 |
|---|---|---|---|---|
| parent 原始版本 | 不适用 | pass | pass | `8abccf3ac28a18122e7f2431f08ee6f31cba1b5599633e70955d7d030bb40971` |
| developer patch | pass | pass | pass | `bad2f34483c009a1e25afb78a79e7002194738ea8355e140512c77205ba5edc8` |
| LLM improved patch | pass | pass | pass | `bad2f34483c009a1e25afb78a79e7002194738ea8355e140512c77205ba5edc8` |

三份编译日志均以以下目标编译记录结束：

```text
CC      fs/namespace.o
```

## 5. 结果解释

1. parent 原始版本也能编译通过，因此“能否编译”不能单独用于判断 crash 是否修复。
2. parent 与修复后版本的对象哈希不同，说明补丁确实改变了编译产物。
3. developer patch 与 LLM improved patch 的对象哈希完全一致。
4. 结合两者源码 diff 相同，可以认为 LLM patch 在该编译目标上与 developer patch 具有编译产物等价性。

## 6. 结论边界

该对照能够证明：

- 三个版本均能进入真实 Linux build system；
- developer patch 和 LLM patch 均可应用并完成目标文件编译；
- developer patch 与 LLM patch 产生相同的 `fs/namespace.o`。

该对照不能证明：

- parent 原始版本没有 crash；
- LLM patch 已通过完整 kernel build；
- LLM patch 已通过 syzkaller reproducer；
- 所有 Semantic Guard 输出都与 developer patch 等价。

## 7. 产物

```text
src/local_compile_compare_wsl.py
results/local_compile_comparison/summary.json
results/local_compile_comparison/summary.csv
results/local_compile_comparison/summary.md
results/local_compile_comparison/parent/
results/local_compile_comparison/developer/
results/local_compile_comparison/llm_improved/
```

其中每个 variant 目录包含 checkout、reset、source diff、defconfig 和 local compile 日志。
