# Evaluation Summary

## Overall

- Total evaluated outputs: 24
- Plausible: 2/24 (8.3%)
- Helpful: 7/24 (29.2%)
- Incorrect: 15/24 (62.5%)
- Plausible + Helpful: 9/24 (37.5%)

## By Group

| group | total | plausible | helpful | incorrect | plausible+helpful |
|---|---:|---:|---:|---:|---:|
| baseline | 8 | 1 (12.5%) | 1 (12.5%) | 6 (75.0%) | 2 (25.0%) |
| with_trace | 8 | 0 (0.0%) | 3 (37.5%) | 5 (62.5%) | 3 (37.5%) |
| improved | 8 | 1 (12.5%) | 3 (37.5%) | 4 (50.0%) | 4 (50.0%) |

## By Bug Type

| bug_type | total | plausible | helpful | incorrect |
|---|---:|---:|---:|---:|
| memory leak | 6 | 0 | 0 | 6 |
| null_pointer | 9 | 2 | 0 | 7 |
| out_of_bounds | 9 | 0 | 7 | 2 |

## Interpretation

The calculation follows the CrashFixer-style manual analysis categories: plausible, helpful, and incorrect. These aggregate labels are based on manual semantic comparison against developer patches and lightweight replace-edit checks. A separate full-build and reproducer validation was completed only for the representative `bug_008 improved` case; it must not be treated as runtime validation of all 24 outputs.
