# Extended Evaluation Metrics

`not_run` means that the experiment was not executed; `unknown` means that historical metadata was not recorded. Neither is counted as failure.

| group | localization accuracy | patch apply rate | compile pass | crash elimination | mean diff similarity | API cost | retries |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 4/4 (100.0%) | 3/8 (37.5%) | 0/0 | 0/0 | 0.1848 | unknown | unknown |
| with_trace | 4/4 (100.0%) | 2/8 (25.0%) | 0/0 | 0/0 | 0.0998 | unknown | unknown |
| improved | 8/8 (100.0%) | 5/8 (62.5%) | 1/1 | 1/1 | 0.4078 | unknown | unknown |

## Coverage

- Outputs: 24
- Patch apply evaluated: 24/24
- Compile evaluated: 1/24
- Dynamic crash elimination evaluated: 1/24
- API cost recorded: 0/24
- Retry count recorded: 0/24

Localization accuracy uses only outputs that proposed at least one edit file. Because the prompt discloses one localization file, it is an edit-target hit rate rather than end-to-end fault-localization accuracy. Developer similarity is a reproducible lexical diff metric and does not replace semantic review.