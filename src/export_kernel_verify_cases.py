import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path(r"D:\SQA\kbench_data_fresh\dataset-kb.json")


def main() -> None:
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    by_bug_id = {item["bugId"]: item for item in dataset}
    cases = []

    for meta_path in sorted((ROOT / "data" / "selected").glob("bug_*/metadata.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        raw = by_bug_id[meta["kbench_bug_id"]]
        fix_commits = raw.get("fixCommits") or []
        cases.append(
            {
                "bug_id": meta["bug_id"],
                "bug_type": meta["bug_type"],
                "title": meta["title"],
                "localization_file": meta["localization_file"],
                "kbench_bug_id": meta["kbench_bug_id"],
                "fix_commit": fix_commits[0]["hashValue"] if fix_commits else "",
                "parent_commit": raw.get("parentOfFixCommit") or "",
                "developer_patch": str((meta_path.parent / "developer_patch.diff").resolve()),
                "model_patches": {
                    group: str((ROOT / "outputs" / group / meta["bug_id"] / "patch.json").resolve())
                    for group in ["baseline", "with_trace", "improved"]
                },
            }
        )

    out = ROOT / "results" / "kernel_verify_cases.json"
    out.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
