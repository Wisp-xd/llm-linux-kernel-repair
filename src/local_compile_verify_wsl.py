import argparse
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], cwd: Path, env: dict[str, str], log_path: Path, timeout: int) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )
    log_path.write_text(proc.stdout, encoding="utf-8", errors="replace")
    return proc.returncode, proc.stdout[-3000:]


def apply_replace_patch(repo: Path, patch_json: Path) -> tuple[bool, str]:
    patch = json.loads(patch_json.read_text(encoding="utf-8"))
    edits = patch.get("edits") or []
    for idx, edit in enumerate(edits, start=1):
        file_name = edit.get("file")
        original = edit.get("original", "")
        replaced = edit.get("replaced", "")
        if not file_name or not original:
            return False, f"edit {idx}: missing file/original"
        path = repo / file_name
        if not path.exists():
            return False, f"edit {idx}: file not found: {file_name}"
        text = path.read_text(encoding="utf-8", errors="replace")
        if original not in text:
            return False, f"edit {idx}: original snippet not found"
        path.write_text(text.replace(original, replaced, 1), encoding="utf-8")
    return True, f"applied {len(edits)} edit(s)"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="/home/wisp/linux-local-compile/linux")
    parser.add_argument("--out-dir", default=str(ROOT / "results" / "local_compile"))
    parser.add_argument("--bug-id", default="bug_008")
    parser.add_argument("--group", default="improved")
    parser.add_argument("--commit", default="197b6b60ae7bc51dd0814953c562833143b292aa")
    parser.add_argument("--target", default="fs/namespace.o")
    parser.add_argument("--tool-prefix", default="/home/wisp/kernel-build-env")
    args = parser.parse_args()

    repo = Path(args.repo)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    build_dir = Path(f"/home/wisp/linux-local-compile/out-{args.bug_id}-{args.group}")
    patch_json = ROOT / "outputs" / args.group / args.bug_id / "patch.json"

    base_env = os.environ.copy()
    tool_bin = Path(args.tool_prefix) / "bin"
    base_env["PATH"] = f"{tool_bin}:{base_env.get('PATH', '')}"
    base_env["ARCH"] = "x86"
    base_env["CROSS_COMPILE"] = "x86_64-conda-linux-gnu-"
    base_env["CC"] = "x86_64-conda-linux-gnu-gcc"
    base_env["HOSTCC"] = "x86_64-conda-linux-gnu-gcc"
    base_env["HOSTCXX"] = "x86_64-conda-linux-gnu-g++"
    base_env["HOSTCFLAGS"] = f"-I{args.tool_prefix}/include"
    base_env["HOSTLDFLAGS"] = f"-L{args.tool_prefix}/lib -Wl,-rpath,{args.tool_prefix}/lib"

    summary = {
        "bug_id": args.bug_id,
        "group": args.group,
        "commit": args.commit,
        "target": args.target,
        "repo": str(repo),
        "build_dir": str(build_dir),
        "patch_apply_ok": False,
        "defconfig_ok": False,
        "local_compile_ok": False,
        "notes": "",
    }

    code, tail = run(["git", "checkout", "--force", args.commit], repo, base_env, out_dir / "01_checkout.log", 300)
    if code != 0:
        summary["notes"] = tail
        (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return
    run(["git", "reset", "--hard"], repo, base_env, out_dir / "02_reset.log", 120)
    run(["git", "clean", "-fdx"], repo, base_env, out_dir / "03_clean.log", 120)

    patch_ok, patch_note = apply_replace_patch(repo, patch_json)
    summary["patch_apply_ok"] = patch_ok
    if not patch_ok:
        summary["notes"] = patch_note
        (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return

    code, diff_tail = run(["git", "diff", "--", "fs/namespace.c"], repo, base_env, out_dir / "04_model_patch.diff", 120)

    build_dir.mkdir(parents=True, exist_ok=True)
    make_common = [
        "make",
        f"O={build_dir}",
        "ARCH=x86",
        "CROSS_COMPILE=x86_64-conda-linux-gnu-",
        "CC=x86_64-conda-linux-gnu-gcc",
        "HOSTCC=x86_64-conda-linux-gnu-gcc",
        "HOSTCXX=x86_64-conda-linux-gnu-g++",
        f"HOSTCFLAGS=-I{args.tool_prefix}/include",
        f"HOSTLDFLAGS=-L{args.tool_prefix}/lib -Wl,-rpath,{args.tool_prefix}/lib",
    ]

    code, tail = run(make_common + ["defconfig"], repo, base_env, out_dir / "05_defconfig.log", 600)
    summary["defconfig_ok"] = code == 0
    if code != 0:
        summary["notes"] = tail
        (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return

    code, tail = run(make_common + ["-j2", args.target], repo, base_env, out_dir / "06_local_compile.log", 1800)
    summary["local_compile_ok"] = code == 0
    summary["notes"] = "local compile passed" if code == 0 else tail
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
