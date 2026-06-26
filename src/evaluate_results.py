from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


def evaluate(evaluation_csv: Path, out_csv: Path) -> None:
    rows = list(csv.DictReader(evaluation_csv.open("r", encoding="utf-8-sig", newline="")))
    by_group = defaultdict(Counter)
    by_group_risk = defaultdict(Counter)

    for row in rows:
        group = row.get("group", "unknown")
        label = row.get("final_label", "unknown")
        risk = row.get("amputation_risk", "unknown")
        by_group[group][label] += 1
        by_group_risk[group][risk] += 1

    fieldnames = ["group", "total", "plausible", "helpful", "incorrect", "amputation_yes", "amputation_medium_or_high"]
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for group, counts in sorted(by_group.items()):
            total = sum(counts.values())
            risks = by_group_risk[group]
            writer.writerow(
                {
                    "group": group,
                    "total": total,
                    "plausible": counts.get("plausible", 0),
                    "helpful": counts.get("helpful", 0),
                    "incorrect": counts.get("incorrect", 0),
                    "amputation_yes": risks.get("yes", 0),
                    "amputation_medium_or_high": risks.get("medium", 0) + risks.get("high", 0),
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation-csv", default="results/evaluation_template.csv")
    parser.add_argument("--out", default="results/summary.csv")
    args = parser.parse_args()
    evaluate(Path(args.evaluation_csv), Path(args.out))
    print(f"summary written: {args.out}")


if __name__ == "__main__":
    main()

