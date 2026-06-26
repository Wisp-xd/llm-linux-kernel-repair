from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


def pct(num: int, den: int) -> str:
    return f"{(num / den * 100):.1f}%" if den else "0.0%"


def write_simple_svg(path: Path, title: str, groups: list[str], values: list[int], color: str) -> None:
    width = 720
    height = 360
    left = 70
    bottom = 60
    top = 60
    max_v = max(values + [1])
    bar_w = 80
    gap = 80
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width/2}" y="30" text-anchor="middle" font-size="20" font-family="Arial">{title}</text>',
        f'<line x1="{left}" y1="{height-bottom}" x2="{width-40}" y2="{height-bottom}" stroke="#333"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#333"/>',
    ]
    for i, (group, val) in enumerate(zip(groups, values)):
        x = left + 70 + i * (bar_w + gap)
        h = int((height - top - bottom - 20) * val / max_v)
        y = height - bottom - h
        parts.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}" fill="{color}"/>')
        parts.append(f'<text x="{x+bar_w/2}" y="{y-8}" text-anchor="middle" font-size="13" font-family="Arial">{val}</text>')
        parts.append(f'<text x="{x+bar_w/2}" y="{height-35}" text-anchor="middle" font-size="13" font-family="Arial">{group}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation", default="results/evaluation_real.csv")
    parser.add_argument("--check", default="results/check_results_summary_deepseek.csv")
    parser.add_argument("--out-md", default="results/extra_metrics_summary.md")
    parser.add_argument("--fig-dir", default="results/figures")
    args = parser.parse_args()

    eval_rows = list(csv.DictReader(Path(args.evaluation).open("r", encoding="utf-8-sig", newline="")))
    check_rows = list(csv.DictReader(Path(args.check).open("r", encoding="utf-8-sig", newline="")))
    groups = ["baseline", "with_trace", "improved"]

    root_by_group: dict[str, Counter[str]] = defaultdict(Counter)
    label_by_group: dict[str, Counter[str]] = defaultdict(Counter)
    for row in eval_rows:
        root_by_group[row["group"]][row["root_cause_correct"]] += 1
        label_by_group[row["group"]][row["final_label"]] += 1

    amputation_by_group: dict[str, int] = defaultdict(int)
    for row in check_rows:
        if row.get("amputation_suspected") == "True":
            amputation_by_group[row["group"]] += 1

    lines = [
        "# Extra Metrics Summary",
        "",
        "## Root Cause Correctness",
        "",
        "| group | yes | partial | no | yes+partial |",
        "|---|---:|---:|---:|---:|",
    ]
    for group in groups:
        counts = root_by_group[group]
        yp = counts["yes"] + counts["partial"]
        lines.append(f"| {group} | {counts['yes']} | {counts['partial']} | {counts['no']} | {yp} ({pct(yp, sum(counts.values()))}) |")

    lines += [
        "",
        "## Amputation Risk",
        "",
        "| group | amputation_suspected |",
        "|---|---:|",
    ]
    for group in groups:
        lines.append(f"| {group} | {amputation_by_group[group]} |")

    lines += [
        "",
        "## CrashFixer-Style Useful Outputs",
        "",
        "`plausible + helpful` is used as the lightweight useful-output measure, following the paper's manual-analysis categories while keeping this project's validation scope explicit.",
        "",
        "| group | plausible+helpful | total | rate |",
        "|---|---:|---:|---:|",
    ]
    for group in groups:
        counts = label_by_group[group]
        total = sum(counts.values())
        useful = counts["plausible"] + counts["helpful"]
        lines.append(f"| {group} | {useful} | {total} | {pct(useful, total)} |")

    out = Path(args.out_md)
    out.write_text("\n".join(lines), encoding="utf-8")
    fig_dir = Path(args.fig_dir)
    fig_dir.mkdir(parents=True, exist_ok=True)
    write_simple_svg(fig_dir / "root_cause_yes_or_partial.svg", "Root Cause Correct or Partial", groups, [root_by_group[g]["yes"] + root_by_group[g]["partial"] for g in groups], "#1976d2")
    write_simple_svg(fig_dir / "amputation_suspected.svg", "Amputation Suspected", groups, [amputation_by_group[g] for g in groups], "#c62828")
    print(f"wrote {out} and figures")


if __name__ == "__main__":
    main()

