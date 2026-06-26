from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List


EARLY_RETURN_PATTERNS = [
    r"\breturn\s+0\s*;",
    r"\breturn\s+NULL\s*;",
    r"\breturn\s+-?\w+\s*;",
    r"\bgoto\s+\w+\s*;",
]


COMMENT_ONLY_LINE = re.compile(r"^\s*(//|/\*|\*|\*/)")


def line_count(text: str) -> int:
    return len([line for line in text.splitlines() if line.strip()])


def normalize_snippet(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def snippet_matches(source_code: str, original: str) -> bool:
    if not original.strip():
        return False
    if original in source_code:
        return True
    return normalize_snippet(original) in normalize_snippet(source_code)


def executable_line_count(text: str) -> int:
    count = 0
    in_block_comment = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if in_block_comment:
            if "*/" in stripped:
                in_block_comment = False
            continue
        if stripped.startswith("/*"):
            if "*/" not in stripped:
                in_block_comment = True
            continue
        if stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("*/"):
            continue
        count += 1
    return count


def deleted_executable_lines(original: str, replaced: str) -> int:
    original_lines = {
        normalize_snippet(line)
        for line in original.splitlines()
        if normalize_snippet(line) and not COMMENT_ONLY_LINE.match(line)
    }
    replaced_lines = {
        normalize_snippet(line)
        for line in replaced.splitlines()
        if normalize_snippet(line) and not COMMENT_ONLY_LINE.match(line)
    }
    return len(original_lines - replaced_lines)


def comments_out_original_code(original: str, replaced: str) -> bool:
    original_exec = {
        normalize_snippet(line).strip(";")
        for line in original.splitlines()
        if normalize_snippet(line) and not COMMENT_ONLY_LINE.match(line)
    }
    for line in replaced.splitlines():
        stripped = line.strip()
        if not COMMENT_ONLY_LINE.match(stripped):
            continue
        comment_text = re.sub(r"^\s*(//|/\*+|\*+|/)+\s*", "", stripped).strip()
        comment_text = comment_text.rstrip("*/").strip().strip(";")
        if comment_text and comment_text in original_exec:
            return True
    return False


def check_patch(source_code: str, patch: Dict[str, Any], localization_file: str = "") -> Dict[str, Any]:
    edits = patch.get("edits") or []
    warnings: List[str] = []
    all_original_matched = True
    modified_only_localization_file = True
    empty_or_too_short = False
    large_deletion = False
    early_return = False
    comment_out = False
    reason_provided = True
    semantic_reason_provided = True

    for idx, edit in enumerate(edits, start=1):
        original = edit.get("original", "")
        replaced = edit.get("replaced", "")
        reason = edit.get("reason", "")
        file_name = edit.get("file", "")

        if localization_file and file_name and file_name != localization_file:
            modified_only_localization_file = False
            warnings.append(f"edit {idx}: modifies file outside localization target")

        if not snippet_matches(source_code, original):
            all_original_matched = False
            warnings.append(f"edit {idx}: original snippet not found in source")

        if len(replaced.strip()) < 8 or line_count(replaced) == 0:
            empty_or_too_short = True
            warnings.append(f"edit {idx}: replacement is empty or too short")

        original_exec_lines = executable_line_count(original)
        replaced_exec_lines = executable_line_count(replaced)
        if original_exec_lines >= 4 and replaced_exec_lines <= max(1, original_exec_lines // 3):
            large_deletion = True
            warnings.append(f"edit {idx}: possible large deletion")

        if any(re.search(pattern, replaced) for pattern in EARLY_RETURN_PATTERNS):
            if "return" in replaced or "goto" in replaced:
                early_return = True
                warnings.append(f"edit {idx}: early return or goto requires manual review")

        if comments_out_original_code(original, replaced):
            comment_out = True
            warnings.append(f"edit {idx}: executable code appears to be commented out")

        if not reason.strip():
            reason_provided = False
            warnings.append(f"edit {idx}: missing reason")

        if "semantic_preservation_reason" in edit and not edit.get("semantic_preservation_reason", "").strip():
            semantic_reason_provided = False
            warnings.append(f"edit {idx}: missing semantic preservation reason")

    amputation_suspected = large_deletion or comment_out
    risk_level = "low"
    if amputation_suspected:
        risk_level = "high"
    elif early_return or not all_original_matched or not modified_only_localization_file:
        risk_level = "medium"

    return {
        "patch_json_valid": isinstance(patch, dict),
        "edit_count": len(edits),
        "all_original_matched": all_original_matched,
        "modified_only_localization_file": modified_only_localization_file,
        "empty_or_too_short_replacement": empty_or_too_short,
        "large_deletion_detected": large_deletion,
        "early_return_detected": early_return,
        "comment_out_detected": comment_out,
        "reason_provided": reason_provided,
        "semantic_reason_provided": semantic_reason_provided,
        "amputation_suspected": amputation_suspected,
        "risk_level": risk_level,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--patch", required=True)
    parser.add_argument("--localization-file", default="")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    source = Path(args.source).read_text(encoding="utf-8", errors="replace")
    patch = json.loads(Path(args.patch).read_text(encoding="utf-8"))
    result = check_patch(source, patch, args.localization_file)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
