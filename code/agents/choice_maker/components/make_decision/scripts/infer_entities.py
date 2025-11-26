#!/usr/bin/env python3
"""Run inference with the trained entity extractor."""

from __future__ import annotations

import argparse
from pathlib import Path

from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Entity extraction inference")
    parser.add_argument("--model-dir", type=Path, required=True, help="Path to trained entity artifacts")
    parser.add_argument("--text", required=True, help="Input text to analyze")
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.model_dir)
    model = AutoModelForTokenClassification.from_pretrained(args.model_dir)
    ner_pipe = pipeline("token-classification", model=model, tokenizer=tokenizer, aggregation_strategy="simple")
    predictions = ner_pipe(args.text)
    for pred in predictions:
        print(pred)


if __name__ == "__main__":
    main()
