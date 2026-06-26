# 典型案例分析模板

## Bug 基本信息

- bug_id:
- bug_type:
- subsystem:
- localization_file:
- developer_patch_size:

## Crash Report 摘要

简要摘录 crash 类型、关键 stack trace、sanitizer 信息。

## Developer Patch 摘要

说明真实开发者补丁修改了哪里，修复逻辑是什么。

## Baseline 输出分析

- 根因是否正确：
- patch 是否可匹配：
- 是否存在截肢风险：
- 人工标签：

## With Trace 输出分析

- trace 是否帮助定位：
- 与 Baseline 相比有什么变化：
- 人工标签：

## Semantic Guard 输出分析

- 是否减少删除/绕过逻辑：
- 是否保留原功能分支：
- 人工标签：

## 小结

该案例说明了什么：

- trace 的作用：
- semantic guard 的作用：
- 当前方法的不足：

