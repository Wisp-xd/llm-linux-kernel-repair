from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect check_result.json files into a CSV table.")
    parser.add_argument("--outputs-dir", default="outputs")
    parser.add_argument("--out", default="results/check_results_summary.csv")
    parser.add_argument("--selected-csv", default="data/selected_bugs.csv")
    parser.add_argument("--selected-only", action="store_true", help="Only collect cases listed in selected_bugs.csv.")
    parser.add_argument("--exclude-demo", action="store_true", help="Skip bug ids containing 'demo'.")
    args = parser.parse_args()

    selected_ids = None
    if args.selected_only:
        selected_path = Path(args.selected_csv)
        with selected_path.open("r", encoding="utf-8-sig", newline="") as f:
            selected_ids = {row["bug_id"] for row in csv.DictReader(f) if row.get("status", "selected") == "selected"}

    rows = []
    for path in Path(args.outputs_dir).glob("*/*/check_result.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        bug_id = data.get("bug_id", path.parent.name)
        if args.exclude_demo and "demo" in bug_id:
            continue
        if selected_ids is not None and bug_id not in selected_ids:
            continue
        rows.append(
            {
                "bug_id": bug_id,
                "bug_type": data.get("bug_type", ""),
                "group": data.get("group", path.parent.parent.name),
                "edit_count": data.get("edit_count", ""),
                "all_original_matched": data.get("all_original_matched", ""),
                "modified_only_localization_file": data.get("modified_only_localization_file", ""),
                "large_deletion_detected": data.get("large_deletion_detected", ""),
                "early_return_detected": data.get("early_return_detected", ""),
                "comment_out_detected": data.get("comment_out_detected", ""),
                "amputation_suspected": data.get("amputation_suspected", ""),
                "risk_level": data.get("risk_level", ""),
                "warnings": " | ".join(data.get("warnings", [])),
            }
        )

    rows.sort(key=lambda r: (r["bug_id"], r["group"]))
    fieldnames = [
        "bug_id",
        "bug_type",
        "group",
        "edit_count",
        "all_original_matched",
        "modified_only_localization_file",
        "large_deletion_detected",
        "early_return_detected",
        "comment_out_detected",
        "amputation_suspected",
        "risk_level",
        "warnings",
    ]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"collected {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
