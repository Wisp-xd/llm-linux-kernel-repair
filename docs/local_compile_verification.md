# 局部编译验证增强项

> 本文记录最初的 LLM Improved 单路编译环境搭建与问题处理。最终实验采用 parent、developer patch、LLM improved patch 三路对照，结果见 `docs/local_compile_comparison.md` 和 `results/local_compile_comparison/summary.md`。

## 目标

在真实 Linux kernel `parentOfFixCommit` 上，对一个代表性样本执行局部编译验证：

- 样本：`bug_008`
- 类型：null pointer / cleanup ordering
- 文件：`fs/namespace.c`
- 实验组：`improved`
- commit：`197b6b60ae7bc51dd0814953c562833143b292aa`
- 编译目标：`fs/namespace.o`

该增强项的目标不是完整 syzkaller reproducer 验证，而是确认模型补丁在真实源码版本上不仅能 apply，还能进入 Linux kernel build system 并完成目标文件编译。

## 已完成准备

1. 已在 WSL2 Ubuntu 中下载 micromamba。
2. 已创建无 sudo 的用户态编译工具链：

```text
/home/wisp/kernel-build-env
```

其中包含：

- `make 4.4.1`
- `x86_64-conda-linux-gnu-gcc 15.2.0`
- `flex 2.6.4`
- `bison 3.8.2`

3. 已创建真实 Linux 源码 checkout：

```text
/home/wisp/linux-local-compile/linux
```

当前已 checkout 到：

```text
197b6b60ae7bc51dd0814953c562833143b292aa
Linux 6.3-rc4
```

4. 已新增可复现脚本：

```text
src/local_compile_verify_wsl.py
```

## 验证结果

局部编译验证已完成：

```text
patch_apply_ok: true
defconfig_ok: true
local_compile_ok: true
```

关键证据位于：

```text
results/local_compile/summary.json
results/local_compile/summary.md
results/local_compile/04_model_patch.diff
results/local_compile/05_defconfig.log
results/local_compile/06_local_compile.log
```

`06_local_compile.log` 的末尾包含：

```text
CC      fs/namespace.o
```

这说明 `bug_008 improved` 模型补丁已经在真实 Linux 6.3-rc4 parent commit 上通过 `fs/namespace.o` 局部编译检查。

## 执行命令

在普通 PowerShell 中运行：

```powershell
cd D:\SQA\llm-linux-kernel-repair
wsl -d Ubuntu -- bash -lc "cd /mnt/d/SQA/llm-linux-kernel-repair && python3 src/local_compile_verify_wsl.py"
```

## 实现过程中遇到的问题

1. WSL 默认文件系统最初位于 C 盘，Linux 源码和工具链导致 C 盘空间不足。后续已将 Ubuntu WSL 虚拟磁盘迁移到：

```text
D:\SQA\wsl\Ubuntu\ext4.vhdx
```

2. WSL 曾出现服务启动异常：

```text
Wsl/Service/CreateInstance/E_FAIL
Wsl/Service/CreateInstance/HCS_E_CONNECTION_TIMEOUT
```

迁移到 D 盘并恢复 WSL 后，脚本可以继续执行。

3. 第一次局部编译失败于 `objtool`，原因是缺少 `gelf.h`，即 libelf/elfutils 开发头文件。通过 micromamba 安装 `elfutils`，并在脚本中加入：

```text
HOSTCFLAGS=-I/home/wisp/kernel-build-env/include
HOSTLDFLAGS=-L/home/wisp/kernel-build-env/lib -Wl,-rpath,/home/wisp/kernel-build-env/lib
```

后编译通过。

## 生成文件

```text
results/local_compile/summary.json
results/local_compile/summary.md
results/local_compile/01_checkout.log
results/local_compile/02_reset.log
results/local_compile/03_clean.log
results/local_compile/04_model_patch.diff
results/local_compile/05_defconfig.log
results/local_compile/06_local_compile.log
```

## 汇报表述建议

> 在真实 Linux 6.3-rc4 parent commit 上，本文进一步选择 bug_008 improved patch 进行局部编译验证。模型 replace-based edit 应用于 `fs/namespace.c` 后，目标文件 `fs/namespace.o` 通过 Linux kernel build system 编译，说明该补丁至少具备真实源码级和编译级可用性。
