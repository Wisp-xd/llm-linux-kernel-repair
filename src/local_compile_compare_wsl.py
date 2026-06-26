import argparse
import csv
import hashlib
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def apply_developer_patch(repo: Path, patch_path: Path, normalized_path: Path, env: dict[str, str]) -> tuple[bool, str]:
    text = patch_path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    normalized_path.write_text(text, encoding="utf-8")
    proc = subprocess.run(
        ["git", "apply", str(normalized_path)],
        cwd=str(repo),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=120,
    )
    return proc.returncode == 0, proc.stdout.strip()


def apply_model_patch(repo: Path, patch_path: Path) -> tuple[bool, str]:
    patch = json.loads(patch_path.read_text(encoding="utf-8"))
    edits = patch.get("edits") or []
    for idx, edit in enumerate(edits, start=1):
        file_name = edit.get("file")
        original = edit.get("original", "")
        replaced = edit.get("replaced", "")
        if not file_name or not original:
            return False, f"edit {idx}: missing file/original"
        path = repo / file_name
        text = path.read_text(encoding="utf-8", errors="replace")
        if original not in text:
            return False, f"edit {idx}: original snippet not found"
        path.write_text(text.replace(original, replaced, 1), encoding="utf-8")
    return True, f"applied {len(edits)} edit(s)"


def build_env(tool_prefix: str) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = f"{tool_prefix}/bin:{env.get('PATH', '')}"
    env["ARCH"] = "x86"
    env["CROSS_COMPILE"] = "x86_64-conda-linux-gnu-"
    env["CC"] = "x86_64-conda-linux-gnu-gcc"
    env["HOSTCC"] = "x86_64-conda-linux-gnu-gcc"
    env["HOSTCXX"] = "x86_64-conda-linux-gnu-g++"
    env["HOSTCFLAGS"] = f"-I{tool_prefix}/include"
    env["HOSTLDFLAGS"] = f"-L{tool_prefix}/lib -Wl,-rpath,{tool_prefix}/lib"
    return env


def make_command(build_dir: Path, tool_prefix: str) -> list[str]:
    return [
        "make",
        f"O={build_dir}",
        "ARCH=x86",
        "CROSS_COMPILE=x86_64-conda-linux-gnu-",
        "CC=x86_64-conda-linux-gnu-gcc",
        "HOSTCC=x86_64-conda-linux-gnu-gcc",
        "HOSTCXX=x86_64-conda-linux-gnu-g++",
        f"HOSTCFLAGS=-I{tool_prefix}/include",
        f"HOSTLDFLAGS=-L{tool_prefix}/lib -Wl,-rpath,{tool_prefix}/lib",
    ]


def verify_variant(
    variant: str,
    repo: Path,
    commit: str,
    target: str,
    tool_prefix: str,
    out_root: Path,
    build_root: Path,
    env: dict[str, str],
) -> dict:
    out_dir = out_root / variant
    out_dir.mkdir(parents=True, exist_ok=True)
    build_dir = build_root / f"out-compare-bug_008-{variant}"
    build_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "variant": variant,
        "commit": commit,
        "target": target,
        "checkout_ok": False,
        "patch_apply": "not_applicable" if variant == "parent" else "failed",
        "defconfig_ok": False,
        "local_compile_ok": False,
        "source_diff_sha256": "",
        "object_sha256": "",
        "notes": "",
    }

    code, tail = run(["git", "checkout", "--force", commit], repo, env, out_dir / "01_checkout.log", 300)
    if code != 0:
        result["notes"] = tail
        return result
    code, tail = run(["git", "reset", "--hard", commit], repo, env, out_dir / "02_reset.log", 120)
    if code != 0:
        result["notes"] = tail
        return result
    result["checkout_ok"] = True

    if variant == "developer":
        patch_path = ROOT / "data" / "selected" / "bug_008" / "developer_patch.diff"
        ok, note = apply_developer_patch(repo, patch_path, out_dir / "03_developer_patch.diff", env)
        result["patch_apply"] = "passed" if ok else "failed"
        if not ok:
            result["notes"] = note
            return result
    elif variant == "llm_improved":
        patch_path = ROOT / "outputs" / "improved" / "bug_008" / "patch.json"
        ok, note = apply_model_patch(repo, patch_path)
        result["patch_apply"] = "passed" if ok else "failed"
        if not ok:
            result["notes"] = note
            return result

    source_diff = out_dir / "04_source.diff"
    code, tail = run(["git", "diff", "--", "fs/namespace.c"], repo, env, source_diff, 120)
    if code != 0:
        result["notes"] = tail
        return result
    result["source_diff_sha256"] = sha256(source_diff)

    make_common = make_command(build_dir, tool_prefix)
    code, tail = run(make_common + ["defconfig"], repo, env, out_dir / "05_defconfig.log", 600)
    result["defconfig_ok"] = code == 0
    if code != 0:
        result["notes"] = tail
        return result

    code, tail = run(make_common + ["-j2", target], repo, env, out_dir / "06_local_compile.log", 1800)
    result["local_compile_ok"] = code == 0
    object_path = build_dir / target
    if code == 0 and object_path.exists():
        result["object_sha256"] = sha256(object_path)
        result["notes"] = "local compile passed"
    else:
        result["notes"] = tail
    return result


def write_markdown(results: list[dict], path: Path) -> None:
    by_variant = {row["variant"]: row for row in results}
    developer_hash = by_variant["developer"]["object_sha256"]
    llm_hash = by_variant["llm_improved"]["object_sha256"]
    same = bool(developer_hash and developer_hash == llm_hash)
    developer_diff_hash = by_variant["developer"]["source_diff_sha256"]
    llm_diff_hash = by_variant["llm_improved"]["source_diff_sha256"]
    diff_same = bool(developer_diff_hash and developer_diff_hash == llm_diff_hash)
    lines = [
        "# bug_008 Local Compile Comparison",
        "",
        "All three variants use the same Linux 6.3-rc4 parent commit, toolchain, defconfig procedure, and `fs/namespace.o` target.",
        "",
        "| variant | patch apply | defconfig | local compile | object SHA-256 |",
        "|---|---|---|---|---|",
    ]
    for row in results:
        digest = row["object_sha256"] or "-"
        lines.append(
            f"| {row['variant']} | {row['patch_apply']} | {'pass' if row['defconfig_ok'] else 'fail'} | "
            f"{'pass' if row['local_compile_ok'] else 'fail'} | `{digest}` |"
        )
    lines += [
        "",
        f"Developer and LLM improved source diff hashes identical: **{'yes' if diff_same else 'no'}**.",
        f"Developer and LLM improved object hashes identical: **{'yes' if same else 'no'}**.",
        "",
        "Interpretation: compilation success establishes build-level feasibility for this target. An identical object hash provides additional evidence that the LLM patch is compilation-equivalent to the developer patch for this case. It does not replace runtime reproducer validation.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="/home/wisp/linux-local-compile/linux")
    parser.add_argument("--commit", default="197b6b60ae7bc51dd0814953c562833143b292aa")
    parser.add_argument("--target", default="fs/namespace.o")
    parser.add_argument("--tool-prefix", default="/home/wisp/kernel-build-env")
    parser.add_argument("--out-dir", default=str(ROOT / "results" / "local_compile_comparison"))
    parser.add_argument("--build-root", default="/home/wisp/linux-local-compile")
    args = parser.parse_args()

    repo = Path(args.repo)
    out_root = Path(args.out_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    env = build_env(args.tool_prefix)
    results = [
        verify_variant(
            variant,
            repo,
            args.commit,
            args.target,
            args.tool_prefix,
            out_root,
            Path(args.build_root),
            env,
        )
        for variant in ["parent", "developer", "llm_improved"]
    ]

    (out_root / "summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    with (out_root / "summary.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    write_markdown(results, out_root / "summary.md")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
