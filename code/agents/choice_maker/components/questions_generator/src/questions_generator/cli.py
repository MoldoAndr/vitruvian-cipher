from __future__ import annotations

import argparse
from pathlib import Path

from .corpus_builder import build_corpus
from .generator import DatasetGenerator
from .llm_providers import build_provider
from .prompts import PromptSpec
from .validator import DatasetValidator


def cmd_generate(args: argparse.Namespace) -> None:
    prompt = PromptSpec.from_file(args.prompt)
    provider = build_provider(
        name=args.provider,
        model=args.model,
        temperature=args.temperature,
        top_p=args.top_p,
    )
    generator = DatasetGenerator(
        prompt=prompt,
        provider=provider,
        output_path=Path(args.output),
        target=args.target,
        batch_size=args.batch_size,
        max_per_call=args.max_per_call,
    )
    generator.run()


def cmd_validate(args: argparse.Namespace) -> None:
    validator = DatasetValidator(
        min_length=args.min_length,
        max_length=args.max_length,
        sim_threshold=args.similarity,
    )
    validator.validate(Path(args.input), Path(args.output))


def cmd_build(args: argparse.Namespace) -> None:
    build_corpus(
        clean_dir=Path(args.clean_dir),
        per_class=args.per_class,
        train_out=Path(args.train_out),
        val_out=Path(args.val_out),
        test_out=Path(args.test_out),
        seed=args.seed,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Synthetic question generation framework")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate raw data for a class")
    gen.add_argument("--prompt", required=True)
    gen.add_argument("--provider", required=True, choices=["openai", "ollama"])
    gen.add_argument("--model", required=True)
    gen.add_argument("--target", type=int, required=True)
    gen.add_argument("--output", required=True)
    gen.add_argument("--batch-size", type=int, default=None)
    gen.add_argument(
        "--max-per-call",
        type=int,
        default=None,
        help="Maximum samples requested per LLM call (default uses prompt batch size)",
    )
    gen.add_argument("--temperature", type=float, default=0.6)
    gen.add_argument("--top-p", type=float, default=0.9)
    gen.set_defaults(func=cmd_generate)

    val = sub.add_parser("validate", help="Validate and deduplicate a raw dataset")
    val.add_argument("--input", required=True)
    val.add_argument("--output", required=True)
    val.add_argument("--min-length", type=int, default=12)
    val.add_argument("--max-length", type=int, default=240)
    val.add_argument("--similarity", type=int, default=92, help="Max allowed fuzz ratio (0-100)")
    val.set_defaults(func=cmd_validate)

    build = sub.add_parser("build-corpus", help="Assemble balanced corpus from clean datasets")
    build.add_argument("--clean-dir", required=True)
    build.add_argument("--per-class", type=int, required=True)
    build.add_argument("--train-out", required=True)
    build.add_argument("--val-out", required=True)
    build.add_argument("--test-out", required=True)
    build.add_argument("--seed", type=int, default=42)
    build.set_defaults(func=cmd_build)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
