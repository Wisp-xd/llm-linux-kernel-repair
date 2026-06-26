# Extra Metrics Summary

## Root Cause Correctness

| group | yes | partial | no | yes+partial |
|---|---:|---:|---:|---:|
| baseline | 2 | 5 | 1 | 7 (87.5%) |
| with_trace | 3 | 4 | 1 | 7 (87.5%) |
| improved | 4 | 1 | 3 | 5 (62.5%) |

## Amputation Risk

| group | amputation_suspected |
|---|---:|
| baseline | 0 |
| with_trace | 0 |
| improved | 0 |

## CrashFixer-Style Useful Outputs

`plausible + helpful` is used as the lightweight useful-output measure, following the paper's manual-analysis categories while keeping this project's validation scope explicit.

| group | plausible+helpful | total | rate |
|---|---:|---:|---:|
| baseline | 2 | 8 | 25.0% |
| with_trace | 3 | 8 | 37.5% |
| improved | 4 | 8 | 50.0% |