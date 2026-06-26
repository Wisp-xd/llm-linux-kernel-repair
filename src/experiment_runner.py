from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from build_prompt import bug_variables, render_template
from call_llm import call_llm, extract_json, get_last_call_metadata
from check_patch import check_patch
from load_bug import load_bug


ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def safe_json(raw: str) -> Dict[str, Any]:
    try:
        return extract_json(raw)
    except Exception as exc:
        return {"parse_error": str(exc), "raw_output": raw}


def select_hypothesis(hypotheses: Dict[str, Any], reflection: Dict[str, Any]) -> Dict[str, Any]:
    selected_id = reflection.get("selected_hypothesis_id", "H1")
    for item in hypotheses.get("hypotheses", []):
        if item.get("id") == selected_id:
            return item
    if hypotheses.get("hypotheses"):
        return hypotheses["hypotheses"][0]
    return {"id": selected_id, "root_cause_hypothesis": reflection.get("selection_reason", "")}


def run_group(
    bug_dir: str,
    group: str,
    provider: str = "mock",
    model: str = "gemini-1.5-pro",
    temperature: float = 0.2,
    input_price_per_million: float | None = None,
    output_price_per_million: float | None = None,
    output_root: str | Path | None = None,
) -> Path:
    bug = load_bug(bug_dir)
    use_trace = group in {"with_trace", "improved"}
    trace_summary = bug.get("trace_summary", "") if use_trace else ""

    base_output = Path(output_root) if output_root is not None else ROOT / "outputs"
    out_dir = base_output / group / bug["bug_id"]
    out_dir.mkdir(parents=True, exist_ok=True)

    common_vars = bug_variables(bug, trace_summary=trace_summary)
    calls: list[Dict[str, Any]] = []

    def record_call(stage: str) -> None:
        metadata = get_last_call_metadata()
        metadata["stage"] = stage
        calls.append(metadata)

    hypothesis_prompt = render_template("hypothesis_generation.txt", common_vars)
    write_text(out_dir / "prompt_hypothesis.txt", hypothesis_prompt)
    hypothesis_raw = call_llm(hypothesis_prompt, provider=provider, model=model, temperature=temperature)
    record_call("hypothesis")
    write_text(out_dir / "hypotheses.raw.txt", hypothesis_raw)
    hypotheses = safe_json(hypothesis_raw)
    write_json(out_dir / "hypotheses.json", hypotheses)

    reflection_prompt = render_template(
        "self_reflection.txt",
        bug_variables(
            bug,
            trace_summary=trace_summary,
            hypotheses_json=json.dumps(hypotheses, ensure_ascii=False, indent=2),
        ),
    )
    write_text(out_dir / "prompt_reflection.txt", reflection_prompt)
    reflection_raw = call_llm(reflection_prompt, provider=provider, model=model, temperature=temperature)
    record_call("reflection")
    write_text(out_dir / "reflection.raw.txt", reflection_raw)
    reflection = safe_json(reflection_raw)
    write_json(out_dir / "reflection.json", reflection)

    selected = select_hypothesis(hypotheses, reflection)
    patch_template = "semantic_guard_patch.txt" if group == "improved" else "patch_generation.txt"
    patch_prompt = render_template(
        patch_template,
        bug_variables(
            bug,
            trace_summary=trace_summary,
            selected_hypothesis=json.dumps(selected, ensure_ascii=False, indent=2),
        ),
    )
    write_text(out_dir / "prompt_patch.txt", patch_prompt)
    patch_raw = call_llm(patch_prompt, provider=provider, model=model, temperature=temperature)
    record_call("patch")
    write_text(out_dir / "patch.raw.txt", patch_raw)
    patch = safe_json(patch_raw)
    write_json(out_dir / "patch.json", patch)

    check = check_patch(bug.get("source_code", ""), patch, bug.get("localization_file", ""))
    check["bug_id"] = bug["bug_id"]
    check["bug_type"] = bug.get("bug_type", "")
    check["group"] = group
    write_json(out_dir / "check_result.json", check)

    prompt_tokens = sum(item.get("prompt_tokens") or 0 for item in calls)
    completion_tokens = sum(item.get("completion_tokens") or 0 for item in calls)
    usage_known = all(item.get("prompt_tokens") is not None and item.get("completion_tokens") is not None for item in calls)
    api_cost_usd = None
    if usage_known and input_price_per_million is not None and output_price_per_million is not None:
        api_cost_usd = round(
            prompt_tokens * input_price_per_million / 1_000_000
            + completion_tokens * output_price_per_million / 1_000_000,
            8,
        )
    write_json(
        out_dir / "run_metadata.json",
        {
            "bug_id": bug["bug_id"],
            "group": group,
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "call_count": len(calls),
            "retry_count": 0,
            "prompt_tokens": prompt_tokens if usage_known else None,
            "completion_tokens": completion_tokens if usage_known else None,
            "total_tokens": prompt_tokens + completion_tokens if usage_known else None,
            "input_price_per_million_usd": input_price_per_million,
            "output_price_per_million_usd": output_price_per_million,
            "api_cost_usd": api_cost_usd,
            "calls": calls,
        },
    )

    return out_dir
