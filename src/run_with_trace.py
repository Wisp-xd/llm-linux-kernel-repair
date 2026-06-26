from __future__ import annotations

import argparse

from experiment_runner import run_group


def main() -> None:
    parser = argparse.ArgumentParser(description="Run with-trace experiment.")
    parser.add_argument("--bug-dir", required=True)
    parser.add_argument("--provider", default="mock", choices=["mock", "gemini", "openai", "deepseek"])
    parser.add_argument("--model", default="gemini-1.5-pro")
    parser.add_argument("--temperature", type=float, default=0.2)
    args = parser.parse_args()
    out_dir = run_group(args.bug_dir, "with_trace", args.provider, args.model, args.temperature)
    print(f"with_trace output: {out_dir}")


if __name__ == "__main__":
    main()
