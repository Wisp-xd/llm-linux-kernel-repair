from __future__ import annotations

import argparse
import csv
import difflib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GROUP_ORDER = ["baseline", "with_trace", "improved"]
STATUS_VALUES = {"passed", "failed", "not_run", "unknown"}


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_path(value: str) -> str:
    return value.strip().replace("\\", "/").lstrip("ab/")


def patch_files(patch: dict[str, Any]) -> set[str]:
    return {
        normalize_path(str(edit.get("file", "")))
        for edit in patch.get("edits", [])
        if edit.get("file")
    }


def changed_lines(before: str, after: str) -> tuple[list[str], list[str]]:
    removed: list[str] = []
    added: list[str] = []
    for line in difflib.ndiff(before.splitlines(), after.splitlines()):
        value = " ".join(line[2:].split())
        if not value:
            continue
        if line.startswith("- "):
            removed.append(value)
        elif line.startswith("+ "):
            added.append(value)
    return removed, added


def model_change_text(patch: dict[str, Any]) -> str:
    removed: list[str] = []
    added: list[str] = []
    for edit in patch.get("edits", []):
        old, new = changed_lines(str(edit.get("original", "")), str(edit.get("replaced", "")))
        removed.extend(old)
        added.extend(new)
    return "\n".join([f"- {line}" for line in removed] + [f"+ {line}" for line in added])


def developer_change_text(diff_text: str) -> str:
    lines: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith(("+++", "---")):
            continue
        if line.startswith(("+", "-")):
            value = " ".join(line[1:].split())
            if value:
                lines.append(f"{line[0]} {value}")
    return "\n".join(lines)


def similarity(model_text: str, developer_text: str) -> float | None:
    if not model_text:
        return 0.0
    if not developer_text:
        return None
    return round(difflib.SequenceMatcher(None, model_text, developer_text).ratio(), 4)


def bool_status(value: str | bool | None) -> str:
    if value is True or str(value).lower() == "true":
        return "passed"
    if value is False or str(value).lower() == "false":
        return "failed"
    return "unknown"


def load_apply_results(path: Path) -> dict[tuple[str, str], str]:
    if not path.exists():
        return {}
    rows = csv.DictReader(path.open("r", encoding="utf-8-sig", newline=""))
    return {
        (row["bug_id"], row["group"]): bool_status(row.get("model_apply_ok"))
        for row in rows
        if row.get("group") in GROUP_ORDER
    }


def load_compile_evidence(path: Path) -> dict[tuple[str, str], str]:
    rows = read_json(path, [])
    result: dict[tuple[str, str], str] = {}
    for row in rows:
        if row.get("variant") == "llm_improved":
            result[("bug_008", "improved")] = bool_status(row.get("local_compile_ok"))
    return result


def load_dynamic_evidence(path: Path) -> dict[tuple[str, str], tuple[str, int | None]]:
    data = read_json(path, {})
    runs = data.get("runs", [])
    if data.get("bug") == "bug_008" and data.get("variant") == "llm_improved" and runs:
        passed = all(run.get("clean_pass") and not run.get("target_crash_reproduced") for run in runs)
        return {("bug_008", "improved"): ("passed" if passed else "failed", len(runs))}
    return {}


def pct(numerator: int, denominator: int) -> str:
    return f"{numerator / denominator * 100:.1f}%" if denominator else "n/a"


def mean_known(values: list[float | None]) -> str:
    known = [value for value in values if value is not None]
    return f"{sum(known) / len(known):.4f}" if known else "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build RGym-inspired metrics for every LLM patch output.")
    parser.add_argument("--evaluation", default="results/evaluation_real.csv")
    parser.add_argument("--apply-results", default="results/kernel_verify_summary.csv")
    parser.add_argument("--out-csv", default="results/extended_metrics.csv")
    parser.add_argument("--out-json", default="results/extended_metrics.json")
    parser.add_argument("--out-md", default="results/extended_metrics_summary.md")
    args = parser.parse_args()

    evaluation_rows = list(
        csv.DictReader((ROOT / args.evaluation).open("r", encoding="utf-8-sig", newline=""))
    )
    apply_results = load_apply_results(ROOT / args.apply_results)
    compile_results = load_compile_evidence(ROOT / "results/local_compile_comparison/summary.json")
    dynamic_results = load_dynamic_evidence(
        ROOT / "results/dynamic_validation/repeated_dynamic_validation_summary.json"
    )

    rows: list[dict[str, Any]] = []
    for evaluation in evaluation_rows:
        bug_id = evaluation["bug_id"]
        group = evaluation["group"]
        key = (bug_id, group)
        data_dir = ROOT / "data" / "selected" / bug_id
        output_dir = ROOT / "outputs" / group / bug_id
        metadata = read_json(data_dir / "metadata.json", {})
        patch = read_json(output_dir / "patch.json", {})
        run_metadata = read_json(output_dir / "run_metadata.json", {})

        expected_file = normalize_path(str(metadata.get("localization_file", "")))
        files = patch_files(patch)
        if not files:
            localization_status = "not_proposed"
        else:
            localization_status = "correct" if expected_file in files else "incorrect"

        developer_text = developer_change_text(
            (data_dir / "developer_patch.diff").read_text(encoding="utf-8")
        )
        model_text = model_change_text(patch)
        dynamic_status, dynamic_runs = dynamic_results.get(key, ("not_run", None))
        api_cost = run_metadata.get("api_cost_usd")
        retry_count = run_metadata.get("retry_count")

        rows.append(
            {
                "bug_id": bug_id,
                "bug_type": evaluation["bug_type"],
                "group": group,
                "final_label": evaluation["final_label"],
                "expected_localization_file": expected_file,
                "proposed_files": ";".join(sorted(files)),
                "localization_status": localization_status,
                "localization_correct": localization_status == "correct",
                "patch_apply_status": apply_results.get(key, "not_run"),
                "compile_status": compile_results.get(key, "not_run"),
                "crash_elimination_status": dynamic_status,
                "dynamic_validation_runs": dynamic_runs,
                "developer_file_overlap": round(len(files & {expected_file}) / len(files | {expected_file}), 4)
                if files and expected_file
                else 0.0,
                "developer_diff_similarity": similarity(model_text, developer_text),
                "api_cost_usd": api_cost,
                "api_cost_status": "recorded" if api_cost is not None else "unknown",
                "prompt_tokens": run_metadata.get("prompt_tokens"),
                "completion_tokens": run_metadata.get("completion_tokens"),
                "retry_count": retry_count,
                "retry_count_status": "recorded" if retry_count is not None else "unknown",
            }
        )

    out_csv = ROOT / args.out_csv
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (ROOT / args.out_json).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["group"]].append(row)

    lines = [
        "# Extended Evaluation Metrics",
        "",
        "`not_run` means that the experiment was not executed; `unknown` means that historical metadata was not recorded. Neither is counted as failure.",
        "",
        "| group | localization accuracy | patch apply rate | compile pass | crash elimination | mean diff similarity | API cost | retries |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for group in GROUP_ORDER:
        items = grouped[group]
        located = [item for item in items if item["localization_status"] != "not_proposed"]
        applied = [item for item in items if item["patch_apply_status"] in {"passed", "failed"}]
        compiled = [item for item in items if item["compile_status"] in {"passed", "failed"}]
        dynamic = [item for item in items if item["crash_elimination_status"] in {"passed", "failed"}]
        costs = [item["api_cost_usd"] for item in items if item["api_cost_usd"] is not None]
        retries = [item["retry_count"] for item in items if item["retry_count"] is not None]
        localization_passes = sum(item["localization_correct"] for item in located)
        apply_passes = sum(item["patch_apply_status"] == "passed" for item in applied)
        compile_passes = sum(item["compile_status"] == "passed" for item in compiled)
        dynamic_passes = sum(item["crash_elimination_status"] == "passed" for item in dynamic)
        cost_text = f"${sum(costs):.6f}" if costs else "unknown"
        retry_text = str(sum(retries)) if retries else "unknown"
        lines.append(
            f"| {group} | {localization_passes}/{len(located)} ({pct(localization_passes, len(located))}) | "
            f"{apply_passes}/{len(applied)} ({pct(apply_passes, len(applied))}) | "
            f"{compile_passes}/{len(compiled)} | "
            f"{dynamic_passes}/{len(dynamic)} | "
            f"{mean_known([item['developer_diff_similarity'] for item in items])} | "
            f"{cost_text} | {retry_text} |"
        )

    lines += [
        "",
        "## Coverage",
        "",
        f"- Outputs: {len(rows)}",
        f"- Patch apply evaluated: {sum(row['patch_apply_status'] in {'passed', 'failed'} for row in rows)}/{len(rows)}",
        f"- Compile evaluated: {sum(row['compile_status'] in {'passed', 'failed'} for row in rows)}/{len(rows)}",
        f"- Dynamic crash elimination evaluated: {sum(row['crash_elimination_status'] in {'passed', 'failed'} for row in rows)}/{len(rows)}",
        f"- API cost recorded: {sum(row['api_cost_status'] == 'recorded' for row in rows)}/{len(rows)}",
        f"- Retry count recorded: {sum(row['retry_count_status'] == 'recorded' for row in rows)}/{len(rows)}",
        "",
        "Localization accuracy uses only outputs that proposed at least one edit file. Because the prompt discloses one localization file, it is an edit-target hit rate rather than end-to-end fault-localization accuracy. Developer similarity is a reproducible lexical diff metric and does not replace semantic review.",
    ]
    (ROOT / args.out_md).write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out_csv}, {args.out_json}, {args.out_md}")


if __name__ == "__main__":
    main()
