from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def load_bug(bug_dir: str | Path) -> Dict[str, Any]:
    root = Path(bug_dir)
    metadata_path = root / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"metadata.json not found in {root}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    bug = {
        "bug_dir": str(root),
        "metadata": metadata,
        "bug_id": metadata.get("bug_id", root.name),
        "bug_type": metadata.get("bug_type", "unknown"),
        "subsystem": metadata.get("subsystem", "unknown"),
        "localization_file": metadata.get("localization_file", ""),
    }

    file_map = {
        "crash_report": metadata.get("crash_report_path", "crash_report.txt"),
        "source_code": metadata.get("source_file_path", "source.c"),
        "developer_patch": metadata.get("developer_patch_path", "developer_patch.diff"),
        "trace_summary": metadata.get("trace_summary_path", "trace_summary.txt"),
    }
    for key, rel_path in file_map.items():
        bug[key] = read_text(root / rel_path)

    return bug


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("bug_dir")
    args = parser.parse_args()
    print(json.dumps(load_bug(args.bug_dir), ensure_ascii=False, indent=2))

