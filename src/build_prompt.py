from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[1]


def render_template(template_name: str, variables: Dict[str, Any]) -> str:
    template_path = Path(template_name)
    if not template_path.exists():
        template_path = ROOT / "prompts" / template_name
    text = template_path.read_text(encoding="utf-8")
    rendered = text
    for key, value in variables.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False, indent=2)
        rendered = rendered.replace("{{" + key + "}}", str(value))
    return rendered


def bug_variables(bug: Dict[str, Any], **extra: Any) -> Dict[str, Any]:
    variables = {
        "bug_id": bug.get("bug_id", ""),
        "bug_type": bug.get("bug_type", ""),
        "localization_file": bug.get("localization_file", ""),
        "crash_report": bug.get("crash_report", ""),
        "source_code": bug.get("source_code", ""),
        "developer_patch": bug.get("developer_patch", ""),
        "trace_summary": bug.get("trace_summary", ""),
    }
    variables.update(extra)
    return variables

