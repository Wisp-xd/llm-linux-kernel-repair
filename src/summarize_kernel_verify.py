import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "results" / "kernel_verify_summary.csv"
OUTPUT = ROOT / "results" / "kernel_verify_summary.md"


def pct(n: int, d: int) -> str:
    return f"{n}/{d} ({n / d * 100:.1f}%)" if d else "0/0 (0.0%)"


def main() -> None:
    rows = list(csv.DictReader(INPUT.open("r", encoding="utf-8-sig")))
    groups = ["developer", "baseline", "with_trace", "improved"]

    lines = [
        "# Kernel Source Verification Summary",
        "",
        "This verification uses a sparse checkout of the real Linux kernel repository at each case's `parentOfFixCommit`.",
        "It checks whether the developer patch can be applied with `git apply --check`, and whether model replace-based edits can be applied to the real source file followed by `git diff --check` and `scripts/checkpatch.pl`.",
        "",
        "This is stronger than source-excerpt matching, but it is still not a full kernel build or reproducer validation.",
        "",
        "## Summary By Group",
        "",
        "| group | total | source checkout ok | patch apply ok | diff check ok | checkpatch errors | checkpatch warnings |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    for group in groups:
        rs = [r for r in rows if r["group"] == group]
        total = len(rs)
        checkout_ok = sum(r["checkout_ok"] == "True" for r in rs)
        if group == "developer":
            apply_ok = sum(r["developer_patch_check_ok"] == "True" for r in rs)
            diff_ok = ""
        else:
            apply_ok = sum(r["model_apply_ok"] == "True" for r in rs)
            diff_ok_count = sum(r["diff_check_ok"] == "True" for r in rs)
            diff_ok = pct(diff_ok_count, total)
        errors = sum(int(r["checkpatch_errors"] or 0) for r in rs)
        warnings = sum(int(r["checkpatch_warnings"] or 0) for r in rs)
        lines.append(
            f"| {group} | {total} | {pct(checkout_ok, total)} | {pct(apply_ok, total)} | {diff_ok} | {errors} | {warnings} |"
        )

    lines += [
        "",
        "## Model Patch Applicability By Case",
        "",
        "| bug_id | baseline | with_trace | improved |",
        "|---|---:|---:|---:|",
    ]
    bug_ids = sorted({r["bug_id"] for r in rows})
    for bug_id in bug_ids:
        cells = []
        for group in ["baseline", "with_trace", "improved"]:
            row = next(r for r in rows if r["bug_id"] == bug_id and r["group"] == group)
            if row["model_apply_ok"] == "True" and row["diff_check_ok"] == "True":
                cells.append("pass")
            elif row["notes"] == "no edits":
                cells.append("no edit")
            else:
                cells.append("fail")
        lines.append(f"| {bug_id} | {cells[0]} | {cells[1]} | {cells[2]} |")

    lines += [
        "",
        "## Interpretation",
        "",
        "- All 8 developer patches are applicable on their real parent commits, confirming that the selected kBenchSyz cases are version-resolvable.",
        "- Improved / Semantic Guard has the highest real-source replace-edit applicability: 5/8, compared with Baseline 3/8 and With Trace 2/8.",
        "- Passing this check means the replace-based edit can be applied to the real source file and has no whitespace/conflict errors. It does not prove semantic correctness or successful kernel build.",
    ]

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
