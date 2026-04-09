from __future__ import annotations

import argparse
import sys

from deepresearcher.config import load_settings
from deepresearcher.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deep researcher: question -> web search -> article generation"
    )
    parser.add_argument(
        "question",
        type=str,
        help="User question for deep research",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    question = args.question.strip()
    if not question:
        print("Question cannot be empty.", file=sys.stderr)
        return 1

    try:
        settings = load_settings()
        print("[INFO] 已加载配置，开始执行深度研究流程...", flush=True)
        article_path, notes_path = run_pipeline(
            question=question,
            settings=settings,
            progress=lambda msg: print(msg, flush=True),
        )
    except Exception as exc:  # pragma: no cover - cli safety
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Done.")
    print(f"Article: {article_path}")
    print(f"Research Notes: {notes_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
