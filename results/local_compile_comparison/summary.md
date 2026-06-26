# bug_008 Local Compile Comparison

All three variants use the same Linux 6.3-rc4 parent commit, toolchain, defconfig procedure, and `fs/namespace.o` target.

| variant | patch apply | defconfig | local compile | object SHA-256 |
|---|---|---|---|---|
| parent | not_applicable | pass | pass | `8abccf3ac28a18122e7f2431f08ee6f31cba1b5599633e70955d7d030bb40971` |
| developer | passed | pass | pass | `bad2f34483c009a1e25afb78a79e7002194738ea8355e140512c77205ba5edc8` |
| llm_improved | passed | pass | pass | `bad2f34483c009a1e25afb78a79e7002194738ea8355e140512c77205ba5edc8` |

Developer and LLM improved source diff hashes identical: **yes**.
Developer and LLM improved object hashes identical: **yes**.

Interpretation: compilation success establishes build-level feasibility for this target. An identical object hash provides additional evidence that the LLM patch is compilation-equivalent to the developer patch for this case. Runtime evidence is reported separately in `results/dynamic_validation/dynamic_validation_report.md`.
