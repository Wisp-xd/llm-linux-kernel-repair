# DeepSeek V4 Pro 中期实验运行摘要

## 运行状态

- 模型：DeepSeek V4 Pro (`deepseek-v4-pro`)
- 样本：8 个真实 kBenchSyz 样本
- 实验组：baseline、with_trace、improved
- 真实样本输出数：24
- JSON 解析失败数：0
- original 匹配成功数：18
- 截肢式修复疑似数：0
- medium 风险数：7
- high 风险数：0

## 分组轻量检查统计

| group | count | original_matched | amputation_suspected | medium_risk | high_risk |
|---|---:|---:|---:|---:|---:|
| baseline | 8 | 7 | 0 | 1 | 0 |
| improved | 8 | 5 | 0 | 4 | 0 |
| with_trace | 8 | 6 | 0 | 2 | 0 |

## 说明

- 当前检查是轻量静态检查，不代表内核编译通过或 crash 动态修复成功。
- `source.c` 是从 developer patch 上下文重构的源码片段，因此 original 不匹配可能来自模型生成了完整函数上下文、缩进差异，或 source excerpt 不完整。
- 下一步需要人工对照 developer patch 填写 `results/evaluation_real_template.csv`，给出 plausible/helpful/incorrect 标签。
