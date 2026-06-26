# DeepSeek V4 Pro 运行说明

## 1. 密钥设置

不要把 API key 写进代码、README 或命令截图中。建议写入用户级环境变量：

```powershell
[Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "your_key", "User")
[Environment]::SetEnvironmentVariable("DEEPSEEK_THINKING", "disabled", "User")
```

说明：

- `DEEPSEEK_THINKING="disabled"` 是为了让 JSON 输出更稳定。
- 如果要尝试更强推理，可改成 `enabled`，但 JSON 解析失败风险会增加。

## 2. 单个样本运行

```powershell
cd D:\SQA\llm-linux-kernel-repair
.\.venv\Scripts\Activate.ps1
python .\src\run_baseline.py --bug-dir .\data\selected\bug_001 --provider deepseek --model deepseek-v4-pro
python .\src\run_with_trace.py --bug-dir .\data\selected\bug_001 --provider deepseek --model deepseek-v4-pro
python .\src\run_improved.py --bug-dir .\data\selected\bug_001 --provider deepseek --model deepseek-v4-pro
```

## 3. 8 个样本三组批量运行

```powershell
.\.venv\Scripts\Activate.ps1
python .\src\run_all_groups.py --provider deepseek --model deepseek-v4-pro
```

输出位置：

```text
outputs/baseline/bug_xxx/
outputs/with_trace/bug_xxx/
outputs/improved/bug_xxx/
```

每个目录包含：

```text
prompt_hypothesis.txt
hypotheses.raw.txt
hypotheses.json
prompt_reflection.txt
reflection.raw.txt
reflection.json
prompt_patch.txt
patch.raw.txt
patch.json
check_result.json
```

## 4. 中期汇报建议

如果 API 额度或网络不稳定，中期可以展示：

- 已重新下载真实 kBenchSyz 数据。
- 已筛选 8 个真实样本。
- 已完成 DeepSeek API 接入。
- 已完成 mock 模式流程验证。
- 下一步用 DeepSeek V4 Pro 生成正式 A/B/C 三组结果。

## 5. Python 环境说明

本项目已创建 `.venv`，其 Python SSL 正常。推荐使用：

```powershell
.\.venv\Scripts\Activate.ps1
python -c "import ssl; print(ssl.OPENSSL_VERSION)"
```

如果直接使用 `D:\aconada\python.exe`，可能出现 `_ssl` 缺失问题。
