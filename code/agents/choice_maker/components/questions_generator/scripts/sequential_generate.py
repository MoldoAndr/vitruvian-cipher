#!/usr/bin/env python3
"""Sequential multi-subject generator optimized for one-shot batches."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.questions_generator.generator import DatasetGenerator
from src.questions_generator.llm_providers import build_provider
from src.questions_generator.prompts import PromptSpec


DEFAULT_TARGETS: Dict[str, int] = {
    "encryption": 600,
    "decryption": 600,
    "password_strength": 400,
    "theory_question": 300,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run all cybersecurity subjects sequentially with large one-shot batches"
    )
    parser.add_argument("--provider", choices=["openai", "ollama"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--subjects", nargs="*", default=list(DEFAULT_TARGETS.keys()))
    parser.add_argument(
        "--output-dir",
        default="data/raw",
        help="Directory where per-subject JSONL files will be written",
    )
    parser.add_argument(
        "--target",
        type=int,
        default=None,
        help="Override target count per subject (default uses built-in target map)",
    )
    parser.add_argument(
        "--max-per-call",
        type=int,
        default=24,
        help="Maximum samples per LLM call so prompts stay concise but efficient",
    )
    parser.add_argument("--temperature", type=float, default=0.6)
    parser.add_argument("--top-p", type=float, default=0.9)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    provider = build_provider(
        name=args.provider,
        model=args.model,
        temperature=args.temperature,
        top_p=args.top_p,
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for subject in args.subjects:
        if subject not in DEFAULT_TARGETS:
            raise ValueError(f"Unknown subject '{subject}'. Supported: {', '.join(DEFAULT_TARGETS)}")
        prompt_path = Path("prompts") / f"{subject}.yaml"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file missing for subject '{subject}'")

        prompt = PromptSpec.from_file(prompt_path)
        target = args.target or DEFAULT_TARGETS[subject]
        output_path = output_dir / f"{subject}.jsonl"

        print(f"\n[run] Generating {target} samples for {subject} (one-shot size={args.max_per_call})")
        generator = DatasetGenerator(
            prompt=prompt,
            provider=provider,
            output_path=output_path,
            target=target,
            max_per_call=args.max_per_call,
        )
        generator.run()

    print("\n[done] Sequential generation finished for all selected subjects")


if __name__ == "__main__":
    main()
