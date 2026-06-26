import argparse
import csv
import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GROUPS = ["baseline", "with_trace", "improved"]


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 300) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )
    return proc.returncode, proc.stdout.strip()


def normalize_path(path: str) -> Path:
    path = path.replace("\\", "/")
    if len(path) >= 3 and path[1] == ":" and path[2] == "/":
        drive = path[0].lower()
        return Path(f"/mnt/{drive}/{path[3:]}")
    return Path(path)


def ensure_repo(repo_dir: Path, paths: list[str], remote_url: str) -> None:
    repo_dir.mkdir(parents=True, exist_ok=True)
    if not (repo_dir / ".git").exists():
        code, out = run(["git", "init"], repo_dir)
        if code != 0:
            raise RuntimeError(out)
        code, out = run(["git", "remote", "add", "origin", remote_url], repo_dir)
        if code != 0:
            raise RuntimeError(out)
        run(["git", "config", "advice.detachedHead", "false"], repo_dir)
        run(["git", "config", "extensions.partialClone", "origin"], repo_dir)
        run(["git", "config", "remote.origin.promisor", "true"], repo_dir)
        run(["git", "config", "remote.origin.partialclonefilter", "blob:none"], repo_dir)
    else:
        run(["git", "remote", "set-url", "origin", remote_url], repo_dir)

    sparse = sorted(set(paths + ["scripts/checkpatch.pl", "scripts/spelling.txt", "scripts/const_structs.checkpatch"]))
    info_dir = repo_dir / ".git" / "info"
    info_dir.mkdir(parents=True, exist_ok=True)
    (info_dir / "sparse-checkout").write_text("\n".join(sparse) + "\n", encoding="utf-8")
    run(["git", "config", "core.sparseCheckout", "true"], repo_dir)


def fetch_commit(repo_dir: Path, commit: str) -> tuple[bool, str]:
    if not commit:
        return False, "missing commit"
    code, out = run(
        ["git", "fetch", "--filter=blob:none", "--no-tags", "--depth=1", "origin", commit],
        repo_dir,
        timeout=900,
    )
    return code == 0, out


def checkout_commit(repo_dir: Path, commit: str) -> tuple[bool, str]:
    code, out = run(["git", "checkout", "--force", commit], repo_dir, timeout=300)
    if code != 0:
        return False, out
    run(["git", "reset", "--hard"], repo_dir, timeout=120)
    run(["git", "clean", "-fd"], repo_dir, timeout=120)
    return True, "checked out"


def check_developer_patch(repo_dir: Path, patch_path: Path) -> tuple[bool, str]:
    normalized = repo_dir / ".codex_developer_patch.diff"
    text = patch_path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    normalized.write_text(text, encoding="utf-8")
    code, out = run(["git", "apply", "--check", str(normalized)], repo_dir, timeout=120)
    return code == 0, out


def apply_model_patch(repo_dir: Path, source_file: str, patch_path: Path) -> dict:
    patch = json.loads(patch_path.read_text(encoding="utf-8"))
    edits = patch.get("edits") or []
    file_path = repo_dir / source_file
    result = {
        "edit_count": len(edits),
        "model_original_matched": False,
        "model_apply_ok": False,
        "diff_check_ok": False,
        "checkpatch_errors": None,
        "checkpatch_warnings": None,
        "notes": "",
    }
    if not file_path.exists():
        result["notes"] = f"source file not found: {source_file}"
        return result

    text = file_path.read_text(encoding="utf-8", errors="replace")
    if not edits:
        result["notes"] = "no edits"
        return result

    changed = text
    missing = []
    for idx, edit in enumerate(edits, start=1):
        original = edit.get("original", "")
        replaced = edit.get("replaced", "")
        if not original or original not in changed:
            missing.append(str(idx))
            continue
        changed = changed.replace(original, replaced, 1)

    if missing:
        result["notes"] = "original not matched for edit(s): " + ",".join(missing)
        return result

    file_path.write_text(changed, encoding="utf-8")
    result["model_original_matched"] = True
    result["model_apply_ok"] = True

    code, out = run(["git", "diff", "--check", "--", source_file], repo_dir, timeout=120)
    result["diff_check_ok"] = code == 0
    if out:
        result["notes"] = out[:500]

    checkpatch = repo_dir / "scripts" / "checkpatch.pl"
    if checkpatch.exists():
        code, out = run(["git", "diff", "--", source_file], repo_dir, timeout=120)
        if code == 0 and out.strip():
            diff_file = repo_dir / ".codex_model_patch.diff"
            diff_file.write_text(out, encoding="utf-8")
            code, cp_out = run(["perl", "scripts/checkpatch.pl", "--no-tree", "--terse", str(diff_file)], repo_dir, timeout=180)
            result["checkpatch_errors"] = cp_out.count("ERROR:")
            result["checkpatch_warnings"] = cp_out.count("WARNING:")
            if cp_out and not result["notes"]:
                result["notes"] = cp_out[:500]

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default=str(ROOT / "results" / "kernel_verify_cases.json"))
    parser.add_argument("--repo-dir", default="/mnt/d/SQA/linux-kernel-verify/linux")
    parser.add_argument(
        "--remote-url",
        default="https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git",
    )
    parser.add_argument("--out", default=str(ROOT / "results" / "kernel_verify_summary.csv"))
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    if args.limit:
        cases = cases[: args.limit]
    repo_dir = Path(args.repo_dir)
    ensure_repo(repo_dir, [case["localization_file"] for case in cases], args.remote_url)

    rows = []
    for case in cases:
        fetch_ok, fetch_log = fetch_commit(repo_dir, case["parent_commit"])
        if not fetch_ok:
            rows.append(
                {
                    "bug_id": case["bug_id"],
                    "group": "developer",
                    "parent_commit": case["parent_commit"],
                    "checkout_ok": False,
                    "developer_patch_check_ok": False,
                    "model_original_matched": "",
                    "model_apply_ok": "",
                    "diff_check_ok": "",
                    "checkpatch_errors": "",
                    "checkpatch_warnings": "",
                    "notes": fetch_log[:500],
                }
            )
            continue

        checkout_ok, checkout_log = checkout_commit(repo_dir, case["parent_commit"])
        developer_ok = False
        dev_notes = checkout_log
        if checkout_ok:
            developer_ok, dev_notes = check_developer_patch(repo_dir, normalize_path(case["developer_patch"]))
        rows.append(
            {
                "bug_id": case["bug_id"],
                "group": "developer",
                "parent_commit": case["parent_commit"],
                "checkout_ok": checkout_ok,
                "developer_patch_check_ok": developer_ok,
                "model_original_matched": "",
                "model_apply_ok": "",
                "diff_check_ok": "",
                "checkpatch_errors": "",
                "checkpatch_warnings": "",
                "notes": dev_notes[:500],
            }
        )

        for group in GROUPS:
            checkout_ok, checkout_log = checkout_commit(repo_dir, case["parent_commit"])
            model = apply_model_patch(repo_dir, case["localization_file"], normalize_path(case["model_patches"][group])) if checkout_ok else {
                "model_original_matched": False,
                "model_apply_ok": False,
                "diff_check_ok": False,
                "checkpatch_errors": "",
                "checkpatch_warnings": "",
                "notes": checkout_log,
            }
            rows.append(
                {
                    "bug_id": case["bug_id"],
                    "group": group,
                    "parent_commit": case["parent_commit"],
                    "checkout_ok": checkout_ok,
                    "developer_patch_check_ok": "",
                    "model_original_matched": model["model_original_matched"],
                    "model_apply_ok": model["model_apply_ok"],
                    "diff_check_ok": model["diff_check_ok"],
                    "checkpatch_errors": model["checkpatch_errors"],
                    "checkpatch_warnings": model["checkpatch_warnings"],
                    "notes": str(model["notes"])[:500],
                }
            )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(out_path)


if __name__ == "__main__":
    main()
