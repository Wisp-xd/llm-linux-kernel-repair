# 已筛选真实 kBenchSyz 样本

## 数据来源

本轮样本不是使用旧目录中的已有文件，而是重新从 Hugging Face 数据集下载：

```text
https://huggingface.co/datasets/chenxi-kalorona-huang/kbench/resolve/main/dataset-kb.json
```

下载后的本地文件：

```text
D:\SQA\kbench_data_fresh\dataset-kb.json
```

导出命令：

```powershell
python .\src\prepare_kbench_selected.py --dataset D:\SQA\kbench_data_fresh\dataset-kb.json --out-dir .\data\selected --selected-csv .\data\selected_bugs.csv
```

## 筛选原则

- 总数控制为 8 个。
- 优先 memory leak、out-of-bounds、null pointer 三类。
- 优先单文件修复。
- 优先 developer patch 较短。
- 避免复杂并发、锁、RCU、跨文件大规模修改。

## 样本列表

| bug_id | 类型 | 子系统 | 定位文件 | patch大小 | 说明 |
|---|---|---|---|---:|---|
| bug_001 | memory leak | netfilter | net/netfilter/nf_tables_api.c | 4 | memory leak in nft_chain_parse_hook |
| bug_002 | memory leak | usb, media | drivers/media/usb/dvb-usb/cinergyT2-core.c | 2 | memory leak in cinergyt2_fe_attach |
| bug_003 | out_of_bounds | fs | kernel/printk/printk.c | 2 | KASAN slab-out-of-bounds/write 类样本 |
| bug_004 | out_of_bounds | selinux | net/xfrm/xfrm_user.c | 3 | KASAN slab-out-of-bounds/read 类样本 |
| bug_005 | out_of_bounds | usb | drivers/usb/usbip/vhci_hcd.c | 2 | UBSAN shift-out-of-bounds 类样本 |
| bug_006 | null_pointer | mm, udf | mm/filemap.c | 2 | KASAN null-ptr-deref in filemap_fault |
| bug_007 | null_pointer | media | drivers/media/common/videobuf2/videobuf2-core.c | 3 | KASAN null-ptr-deref in __vb2_buf_mem_free |
| bug_008 | null_pointer | fs | fs/namespace.c | 2 | KASAN null-ptr-deref in sys_mount_setattr |

## 文件结构

每个样本均已导出为统一格式：

```text
data/selected/bug_xxx/
├── metadata.json
├── crash_report.txt
├── source.c
├── developer_patch.diff
├── trace_summary.txt
└── note.md
```

## 重要说明

当前 `source.c` 是从 developer patch 的上下文中重构出的源码片段，不是完整 Linux 源文件。这样做适合本项目的 Prompt 实验和中期汇报，因为本阶段不进行完整内核编译和 QEMU 动态验证。

后续如果需要更严格的实验，可以下载对应 kernel commit，并用 `localization_file` 替换为完整源文件。

