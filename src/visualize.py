from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


COLORS = {
    "plausible": "#2e7d32",
    "helpful": "#f9a825",
    "incorrect": "#c62828",
}


def svg_bar_chart(data, out_path: Path, title: str) -> None:
    width = 720
    height = 420
    margin = 60
    labels = list(data.keys())
    max_value = max([max(values.values()) if values else 0 for values in data.values()] + [1])
    bar_w = 42
    group_gap = 120

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f'<text x="{width/2}" y="30" text-anchor="middle" font-size="20">{title}</text>',
    ]
    x = margin
    for group in labels:
        offset = 0
        for label in ["plausible", "helpful", "incorrect"]:
            value = data[group].get(label, 0)
            h = int((height - 140) * value / max_value)
            y = height - margin - h
            parts.append(f'<rect x="{x+offset}" y="{y}" width="{bar_w}" height="{h}" fill="{COLORS[label]}"/>')
            parts.append(f'<text x="{x+offset+bar_w/2}" y="{y-6}" text-anchor="middle" font-size="12">{value}</text>')
            offset += bar_w + 8
        parts.append(f'<text x="{x+65}" y="{height-30}" text-anchor="middle" font-size="13">{group}</text>')
        x += group_gap + 60
    legend_x = width - 180
    legend_y = 70
    for idx, label in enumerate(["plausible", "helpful", "incorrect"]):
        y = legend_y + idx * 24
        parts.append(f'<rect x="{legend_x}" y="{y}" width="14" height="14" fill="{COLORS[label]}"/>')
        parts.append(f'<text x="{legend_x+22}" y="{y+12}" font-size="13">{label}</text>')
    parts.append("</svg>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts), encoding="utf-8")


def visualize(evaluation_csv: Path, out_dir: Path) -> None:
    rows = list(csv.DictReader(evaluation_csv.open("r", encoding="utf-8-sig", newline="")))
    labels_by_group = defaultdict(Counter)
    for row in rows:
        labels_by_group[row.get("group", "unknown")][row.get("final_label", "unknown")] += 1
    svg_bar_chart(labels_by_group, out_dir / "label_distribution.svg", "Patch Quality Distribution")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation-csv", default="results/evaluation_template.csv")
    parser.add_argument("--out-dir", default="results/figures")
    args = parser.parse_args()
    visualize(Path(args.evaluation_csv), Path(args.out_dir))
    print(f"figures written: {args.out_dir}")


if __name__ == "__main__":
    main()

