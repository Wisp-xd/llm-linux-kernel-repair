from __future__ import annotations

import argparse
import json
from pathlib import Path


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def compact_patch_json(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    try:
        data = json.loads(read(path))
    except json.JSONDecodeError:
        return read(path)[:2000]
    return json.dumps(data, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export compact review material for manual evaluation.")
    parser.add_argument("--selected-dir", default="data/selected")
    parser.add_argument("--outputs-dir", default="outputs")
    parser.add_argument("--out", default="results/manual_review_pack.md")
    args = parser.parse_args()

    selected_dir = Path(args.selected_dir)
    outputs_dir = Path(args.outputs_dir)
    sections = ["# Manual Review Pack", ""]

    for bug_dir in sorted(selected_dir.glob("bug_*")):
        if not bug_dir.is_dir():
            continue
        metadata = json.loads(read(bug_dir / "metadata.json"))
        sections.append(f"## {metadata['bug_id']} - {metadata.get('title', '')}")
        sections.append("")
        sections.append(f"- type: {metadata.get('bug_type', '')}")
        sections.append(f"- file: {metadata.get('localization_file', '')}")
        sections.append(f"- kbench_bug_id: {metadata.get('kbench_bug_id', '')}")
        sections.append("")
        sections.append("### Developer Patch")
        sections.append("```diff")
        sections.append(read(bug_dir / "developer_patch.diff")[:4000])
        sections.append("```")
        for group in ["baseline", "with_trace", "improved"]:
            out_dir = outputs_dir / group / metadata["bug_id"]
            sections.append(f"### {group}")
            sections.append("")
            sections.append("patch:")
            sections.append("```json")
            sections.append(compact_patch_json(out_dir / "patch.json")[:5000])
            sections.append("```")
            sections.append("check:")
            sections.append("```json")
            sections.append(compact_patch_json(out_dir / "check_result.json")[:2500])
            sections.append("```")
        sections.append("")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(sections), encoding="utf-8")
    print(f"review pack written: {out}")


if __name__ == "__main__":
    main()

