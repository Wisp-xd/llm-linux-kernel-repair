# Selected Cases

正式实验阶段从 kBenchSyz 中筛选 6-8 个 bug，每个 bug 建议整理为：

```text
bug_001/
├── metadata.json
├── crash_report.txt
├── source.c
├── developer_patch.diff
├── trace_summary.txt
└── note.md
```

筛选优先级：

1. 单文件修复。
2. developer patch 较短。
3. crash report 和 stack trace 清晰。
4. memory leak、UBSAN out-of-bounds、null pointer dereference 各 2 个左右。
5. 避免复杂并发、锁、RCU、跨文件大规模修改。

