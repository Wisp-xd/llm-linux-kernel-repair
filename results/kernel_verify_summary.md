# Kernel Source Verification Summary

This verification uses a sparse checkout of the real Linux kernel repository at each case's `parentOfFixCommit`.
It checks whether the developer patch can be applied with `git apply --check`, and whether model replace-based edits can be applied to the real source file followed by `git diff --check` and `scripts/checkpatch.pl`.

This is stronger than source-excerpt matching, but it is still not a full kernel build or reproducer validation.

## Summary By Group

| group | total | source checkout ok | patch apply ok | diff check ok | checkpatch errors | checkpatch warnings |
|---|---:|---:|---:|---:|---:|---:|
| developer | 8 | 8/8 (100.0%) | 8/8 (100.0%) |  | 0 | 0 |
| baseline | 8 | 8/8 (100.0%) | 3/8 (37.5%) | 3/8 (37.5%) | 0 | 0 |
| with_trace | 8 | 8/8 (100.0%) | 2/8 (25.0%) | 2/8 (25.0%) | 0 | 0 |
| improved | 8 | 8/8 (100.0%) | 5/8 (62.5%) | 5/8 (62.5%) | 0 | 2 |

## Model Patch Applicability By Case

| bug_id | baseline | with_trace | improved |
|---|---:|---:|---:|
| bug_001 | fail | fail | fail |
| bug_002 | no edit | no edit | fail |
| bug_003 | pass | pass | pass |
| bug_004 | no edit | fail | pass |
| bug_005 | pass | pass | pass |
| bug_006 | no edit | no edit | pass |
| bug_007 | no edit | no edit | fail |
| bug_008 | pass | no edit | pass |

## Interpretation

- All 8 developer patches are applicable on their real parent commits, confirming that the selected kBenchSyz cases are version-resolvable.
- Improved / Semantic Guard has the highest real-source replace-edit applicability: 5/8, compared with Baseline 3/8 and With Trace 2/8.
- Passing this check means the replace-based edit can be applied to the real source file and has no whitespace/conflict errors. It does not prove semantic correctness or successful kernel build.
