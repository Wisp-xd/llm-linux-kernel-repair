from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


LABELS = ["plausible", "helpful", "incorrect"]


def pct(num: int, den: int) -> str:
    return f"{(num / den * 100):.1f}%" if den else "0.0%"


def write_svg_bar(path: Path, group_counts: dict[str, Counter[str]]) -> None:
    groups = list(group_counts.keys())
    width = 820
    height = 430
    top = 60
    bottom = 70
    left = 70
    max_count = max([max(c.values()) if c else 0 for c in group_counts.values()] + [1])
    colors = {"plausible": "#2e7d32", "helpful": "#f9a825", "incorrect": "#c62828"}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width/2}" y="30" text-anchor="middle" font-size="20" font-family="Arial">Patch Quality Distribution</text>',
        f'<line x1="{left}" y1="{height-bottom}" x2="{width-40}" y2="{height-bottom}" stroke="#333"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#333"/>',
    ]
    group_w = 180
    bar_w = 38
    for gi, group in enumerate(groups):
        x0 = left + 45 + gi * group_w
        for li, label in enumerate(LABELS):
            val = group_counts[group].get(label, 0)
            bar_h = int((height - top - bottom - 30) * val / max_count)
            x = x0 + li * (bar_w + 8)
            y = height - bottom - bar_h
            parts.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bar_h}" fill="{colors[label]}"/>')
            parts.append(f'<text x="{x + bar_w/2}" y="{y - 6}" text-anchor="middle" font-size="12" font-family="Arial">{val}</text>')
        parts.append(f'<text x="{x0 + 65}" y="{height-38}" text-anchor="middle" font-size="13" font-family="Arial">{group}</text>')
    legend_x = width - 185
    for i, label in enumerate(LABELS):
        y = 70 + i * 24
        parts.append(f'<rect x="{legend_x}" y="{y}" width="14" height="14" fill="{colors[label]}"/>')
        parts.append(f'<text x="{legend_x+22}" y="{y+12}" font-size="13" font-family="Arial">{label}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize plausible/helpful/incorrect evaluation.")
    parser.add_argument("--evaluation", default="results/evaluation_real.csv")
    parser.add_argument("--summary-csv", default="results/evaluation_summary_by_group.csv")
    parser.add_argument("--summary-md", default="results/evaluation_summary.md")
    parser.add_argument("--fig", default="results/figures/evaluation_label_distribution.svg")
    args = parser.parse_args()

    rows = list(csv.DictReader(Path(args.evaluation).open("r", encoding="utf-8-sig", newline="")))
    group_counts: dict[str, Counter[str]] = defaultdict(Counter)
    type_counts: dict[str, Counter[str]] = defaultdict(Counter)
    overall = Counter()
    for row in rows:
        label = row["final_label"]
        group = row["group"]
        bug_type = row["bug_type"]
        group_counts[group][label] += 1
        type_counts[bug_type][label] += 1
        overall[label] += 1

    group_order = ["baseline", "with_trace", "improved"]
    out_csv = Path(args.summary_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["group", "total"] + LABELS + [f"{label}_rate" for label in LABELS] + ["plausible_or_helpful", "plausible_or_helpful_rate"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for group in group_order:
            counts = group_counts[group]
            total = sum(counts.values())
            row = {"group": group, "total": total}
            for label in LABELS:
                row[label] = counts[label]
                row[f"{label}_rate"] = pct(counts[label], total)
            ph = counts["plausible"] + counts["helpful"]
            row["plausible_or_helpful"] = ph
            row["plausible_or_helpful_rate"] = pct(ph, total)
            writer.writerow(row)

    total = sum(overall.values())
    lines = [
        "# Evaluation Summary",
        "",
        "## Overall",
        "",
        f"- Total evaluated outputs: {total}",
        f"- Plausible: {overall['plausible']}/{total} ({pct(overall['plausible'], total)})",
        f"- Helpful: {overall['helpful']}/{total} ({pct(overall['helpful'], total)})",
        f"- Incorrect: {overall['incorrect']}/{total} ({pct(overall['incorrect'], total)})",
        f"- Plausible + Helpful: {overall['plausible'] + overall['helpful']}/{total} ({pct(overall['plausible'] + overall['helpful'], total)})",
        "",
        "## By Group",
        "",
        "| group | total | plausible | helpful | incorrect | plausible+helpful |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for group in group_order:
        counts = group_counts[group]
        gtotal = sum(counts.values())
        ph = counts["plausible"] + counts["helpful"]
        lines.append(
            f"| {group} | {gtotal} | {counts['plausible']} ({pct(counts['plausible'], gtotal)}) | "
            f"{counts['helpful']} ({pct(counts['helpful'], gtotal)}) | "
            f"{counts['incorrect']} ({pct(counts['incorrect'], gtotal)}) | {ph} ({pct(ph, gtotal)}) |"
        )
    lines += ["", "## By Bug Type", "", "| bug_type | total | plausible | helpful | incorrect |", "|---|---:|---:|---:|---:|"]
    for bug_type in sorted(type_counts):
        counts = type_counts[bug_type]
        btotal = sum(counts.values())
        lines.append(f"| {bug_type} | {btotal} | {counts['plausible']} | {counts['helpful']} | {counts['incorrect']} |")
    lines += [
        "",
        "## Interpretation",
        "",
        "The calculation follows the CrashFixer-style manual analysis categories: plausible, helpful, and incorrect. "
        "Because this project does not perform full kernel builds or reproducer validation, these labels are based on manual semantic comparison against developer patches and lightweight replace-edit checks.",
    ]
    Path(args.summary_md).write_text("\n".join(lines), encoding="utf-8")
    fig = Path(args.fig)
    fig.parent.mkdir(parents=True, exist_ok=True)
    write_svg_bar(fig, {group: group_counts[group] for group in group_order})
    print(f"wrote {out_csv}, {args.summary_md}, {fig}")


if __name__ == "__main__":
    main()
