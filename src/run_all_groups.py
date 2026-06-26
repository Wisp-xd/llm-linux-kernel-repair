from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

from experiment_runner import run_group


ROOT = Path(__file__).resolve().parents[1]
GROUPS = ["baseline", "with_trace", "improved"]


def read_selected_cases(selected_csv: Path, limit: int | None = None) -> List[Dict[str, str]]:
    rows = list(csv.DictReader(selected_csv.open("r", encoding="utf-8-sig", newline="")))
    rows = [row for row in rows if row.get("status", "selected") == "selected"]
    if limit:
        rows = rows[:limit]
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all experiment groups on selected cases.")
    parser.add_argument("--selected-csv", default="data/selected_bugs.csv")
    parser.add_argument("--provider", default="mock", choices=["mock", "gemini", "openai", "deepseek"])
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--groups", default="baseline,with_trace,improved")
    parser.add_argument("--summary-out", default="results/run_all_summary.json")
    parser.add_argument("--input-price-per-million", type=float, default=None)
    parser.add_argument("--output-price-per-million", type=float, default=None)
    parser.add_argument("--output-root", default=None, help="Optional isolated output directory.")
    args = parser.parse_args()

    selected_csv = Path(args.selected_csv)
    cases = read_selected_cases(selected_csv, args.limit)
    groups = [g.strip() for g in args.groups.split(",") if g.strip()]
    invalid = [g for g in groups if g not in GROUPS]
    if invalid:
        raise ValueError(f"invalid groups: {invalid}")

    summary = {
        "provider": args.provider,
        "model": args.model,
        "temperature": args.temperature,
        "case_count": len(cases),
        "groups": groups,
        "runs": [],
    }

    for case in cases:
        bug_id = case["bug_id"]
        bug_dir = ROOT / "data" / "selected" / bug_id
        for group in groups:
            print(f"running {group} {bug_id} ...")
            out_dir = run_group(
                str(bug_dir),
                group,
                provider=args.provider,
                model=args.model,
                temperature=args.temperature,
                input_price_per_million=args.input_price_per_million,
                output_price_per_million=args.output_price_per_million,
                output_root=args.output_root,
            )
            summary["runs"].append({"bug_id": bug_id, "group": group, "out_dir": str(out_dir)})

    out_path = Path(args.summary_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"summary written: {out_path}")


if __name__ == "__main__":
    main()
