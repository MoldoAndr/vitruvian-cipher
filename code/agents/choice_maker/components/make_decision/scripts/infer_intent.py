#!/usr/bin/env python3
"""Run inference with the trained intent classifier."""

from __future__ import annotations

import argparse
from pathlib import Path

from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Intent classification inference")
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--text", required=True)
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(args.model_dir)
    clf = pipeline("text-classification", model=model, tokenizer=tokenizer)
    output = clf(args.text, truncation=True)
    for pred in output:
        print(pred)


if __name__ == "__main__":
    main()
