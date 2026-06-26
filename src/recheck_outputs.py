from __future__ import annotations

import argparse
import json
from pathlib import Path

from check_patch import check_patch
from load_bug import load_bug


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-run lightweight patch checks for existing outputs.")
    parser.add_argument("--selected-dir", default="data/selected")
    parser.add_argument("--outputs-dir", default="outputs")
    parser.add_argument("--groups", default="baseline,with_trace,improved")
    args = parser.parse_args()

    groups = [g.strip() for g in args.groups.split(",") if g.strip()]
    count = 0
    for bug_dir in sorted(Path(args.selected_dir).glob("bug_*")):
        if not bug_dir.is_dir():
            continue
        bug = load_bug(bug_dir)
        for group in groups:
            out_dir = Path(args.outputs_dir) / group / bug["bug_id"]
            patch_path = out_dir / "patch.json"
            if not patch_path.exists():
                continue
            patch = json.loads(patch_path.read_text(encoding="utf-8"))
            check = check_patch(bug.get("source_code", ""), patch, bug.get("localization_file", ""))
            check["bug_id"] = bug["bug_id"]
            check["bug_type"] = bug.get("bug_type", "")
            check["group"] = group
            (out_dir / "check_result.json").write_text(json.dumps(check, ensure_ascii=False, indent=2), encoding="utf-8")
            count += 1
    print(f"rechecked {count} outputs")


if __name__ == "__main__":
    main()

