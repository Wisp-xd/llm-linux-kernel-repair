from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List


DEFAULT_SELECTED = [
    ("bug_001", "memory leak", "6c4345574ac937d9ccc195fdadb44f7cc95a19f9"),
    ("bug_002", "memory leak", "5f4efc25ef5c6175138a39105a204749b5c83b1c"),
    ("bug_003", "out_of_bounds", "7d0e7e183df07b0c306cca5dfd022a64c302dd4f"),
    ("bug_004", "out_of_bounds", "b72d20070b541e44e5b91326de68930e51654c81"),
    ("bug_005", "out_of_bounds", "4ed0d6eea4561854b366170155a78652da4cef29"),
    ("bug_006", "null_pointer", "d21cb12ee03822236d82ba4e83a1f8968e7832fb"),
    ("bug_007", "null_pointer", "17535f4bf5b322437f7c639b59161ce343fc55a9"),
    ("bug_008", "null_pointer", "e675fbaf856bd1465eed8b8f51ae182b58b8d656"),
]


def find_item(data: Iterable[Dict[str, Any]], bug_id: str) -> Dict[str, Any]:
    for item in data:
        if item.get("bugId") == bug_id:
            return item
    raise KeyError(f"bugId not found: {bug_id}")


def patch_stats(patch: str) -> tuple[int, int]:
    added = sum(1 for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in patch.splitlines() if line.startswith("-") and not line.startswith("---"))
    return added, removed


def first_modified_file(item: Dict[str, Any]) -> str:
    files = item.get("patchModifiedFiles") or []
    if files:
        return files[0]
    patch = item.get("patch") or ""
    m = re.search(r"^\+\+\+ b/(.+)$", patch, re.M)
    return m.group(1) if m else "unknown.c"


def source_excerpt_from_patch(patch: str) -> str:
    lines: List[str] = [
        "/*",
        " * Source excerpt reconstructed from developer patch context.",
        " * Replace with the full localization file when a Linux checkout is available.",
        " */",
        "",
    ]
    current_file = ""
    in_hunk = False
    for raw in patch.splitlines():
        if raw.startswith("diff --git "):
            current_file = raw
            in_hunk = False
            lines.append("")
            lines.append(f"/* {current_file} */")
            continue
        if raw.startswith("@@"):
            in_hunk = True
            lines.append("")
            lines.append(f"/* {raw} */")
            continue
        if not in_hunk:
            continue
        if raw.startswith("\\ No newline"):
            continue
        if raw.startswith(" ") or raw.startswith("-"):
            lines.append(raw[1:])
        elif raw.startswith("+"):
            continue
        elif raw == "":
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def trace_summary_from_report(report: str) -> str:
    selected: List[str] = []
    for line in report.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if (
            "Call Trace" in stripped
            or re.search(r"\bRIP:|\bPC is at|\bin [A-Za-z0-9_]+\b", stripped)
            or re.search(r"[A-Za-z0-9_]+(\+0x[0-9a-f]+/0x[0-9a-f]+)?", stripped)
            and (".c:" in stripped or "+0x" in stripped)
        ):
            selected.append(stripped)
        if len(selected) >= 40:
            break
    if not selected:
        selected = report.splitlines()[:20]
    return "Trace summary extracted from crash report:\n" + "\n".join(selected).strip() + "\n"


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(normalize_text(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value)


def write_case(out_dir: Path, case_id: str, bug_type: str, item: Dict[str, Any]) -> Dict[str, str]:
    case_dir = out_dir / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    patch = item.get("patch") or ""
    crash_report = normalize_text(item.get("cleanCrashReport") or item.get("rawCrashReport") or item.get("title") or "")
    source_excerpt = source_excerpt_from_patch(patch)
    trace_summary = trace_summary_from_report(crash_report)
    localization_file = first_modified_file(item)
    added, removed = patch_stats(patch)
    fix_files = item.get("patchModifiedFiles") or []

    metadata = {
        "bug_id": case_id,
        "kbench_bug_id": item.get("bugId", ""),
        "bug_type": bug_type,
        "title": item.get("title", ""),
        "display_title": item.get("displayTitle", ""),
        "status": item.get("status", ""),
        "subsystem": ", ".join(item.get("subsystems") or []),
        "localization_file": localization_file,
        "fix_files_count": len(fix_files) if fix_files else 1,
        "patch_added_lines": added,
        "patch_removed_lines": removed,
        "crash_report_path": "crash_report.txt",
        "source_file_path": "source.c",
        "developer_patch_path": "developer_patch.diff",
        "trace_summary_path": "trace_summary.txt",
        "source_note": "source.c is a patch-context excerpt, not the full Linux source file.",
    }

    (case_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    (case_dir / "crash_report.txt").write_text(crash_report, encoding="utf-8", errors="replace")
    (case_dir / "source.c").write_text(source_excerpt, encoding="utf-8", errors="replace")
    (case_dir / "developer_patch.diff").write_text(patch, encoding="utf-8", errors="replace")
    (case_dir / "trace_summary.txt").write_text(trace_summary, encoding="utf-8", errors="replace")
    (case_dir / "note.md").write_text(
        "# Case Note\n\n"
        "This case was exported from kBenchSyz JSON data. The `source.c` file is a source excerpt reconstructed from developer patch context. "
        "For final experiments, it is acceptable for a prompt-only course project, but a full Linux checkout can provide richer source context.\n",
        encoding="utf-8",
    )

    return {
        "bug_id": case_id,
        "bug_type": bug_type,
        "subsystem": metadata["subsystem"],
        "localization_file": localization_file,
        "crash_report_path": f"data/selected/{case_id}/crash_report.txt",
        "source_file_path": f"data/selected/{case_id}/source.c",
        "developer_patch_path": f"data/selected/{case_id}/developer_patch.diff",
        "trace_summary_path": f"data/selected/{case_id}/trace_summary.txt",
        "patch_size": str(added + removed),
        "fix_files_count": str(metadata["fix_files_count"]),
        "selected_reason": "single-file or short developer patch; representative crash type",
        "excluded_risk": "source excerpt only; no full kernel build validation",
        "status": "selected",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export selected kBenchSyz cases into the project format.")
    parser.add_argument("--dataset", default=r"D:\SQA\kbench_data\dataset-kb.json")
    parser.add_argument("--out-dir", default="data/selected")
    parser.add_argument("--selected-csv", default="data/selected_bugs.csv")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for case_id, bug_type, kbench_id in DEFAULT_SELECTED:
        item = find_item(data, kbench_id)
        rows.append(write_case(out_dir, case_id, bug_type, item))

    fieldnames = [
        "bug_id",
        "bug_type",
        "subsystem",
        "localization_file",
        "crash_report_path",
        "source_file_path",
        "developer_patch_path",
        "trace_summary_path",
        "patch_size",
        "fix_files_count",
        "selected_reason",
        "excluded_risk",
        "status",
    ]
    selected_csv = Path(args.selected_csv)
    selected_csv.parent.mkdir(parents=True, exist_ok=True)
    with selected_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"exported {len(rows)} cases to {out_dir}")
    print(f"updated {selected_csv}")


if __name__ == "__main__":
    main()
