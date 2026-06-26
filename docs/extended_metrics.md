# Extended Evaluation Metrics

The project records one row per `bug_id` and experiment group in
`results/extended_metrics.csv`.

## Metrics

- `localization_status`: whether a proposed edit targets the developer-fixed file. Outputs without edits are `not_proposed` and are excluded from localization accuracy. Because the current prompts disclose one localization file, this is an edit-target hit rate, not end-to-end fault-localization accuracy.
- `patch_apply_status`: whether the model patch applies to the real parent commit.
- `compile_status`: whether the applied patch passes the recorded compile target.
- `crash_elimination_status`: whether the patched kernel completes reproducer validation without the target crash.
- `developer_file_overlap`: Jaccard overlap between model-edited files and developer-fixed files.
- `developer_diff_similarity`: normalized lexical similarity between model and developer changed lines. It supplements, but does not replace, semantic review.
- `api_cost_usd`: token-based cost when usage and explicit per-million-token prices were recorded.
- `retry_count`: retries after the initial three-stage repair attempt.

`not_run` means no compile or dynamic experiment was executed. `unknown` means an older run did not record the metadata. These states must not be counted as failures.

## Generate

```powershell
python .\src\summarize_extended_metrics.py
```

For future API runs, provide the prices applicable at execution time with the
`--input-price-per-million` and `--output-price-per-million` arguments. Do not
reuse old prices without checking the provider's current pricing.

```powershell
python .\src\run_all_groups.py `
  --provider deepseek `
  --model deepseek-v4-pro
```

Each output directory will contain `run_metadata.json` with token usage, cost inputs, total cost, call count, and retry count. Cost remains `unknown` when prices are omitted.
