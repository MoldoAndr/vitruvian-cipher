#!/usr/bin/env python3
"""Fine-tune a SecureBERT-style classifier on TOON data."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
from datasets import Dataset, DatasetDict
from sklearn.metrics import accuracy_score, f1_score
from transformers import (AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding,
                          Trainer, TrainingArguments)

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.pipeline.data import load_records_from_dir, split_records


def build_dataset(raw_dir: Path, seed: int) -> tuple[DatasetDict, Dict[str, int]]:
    records = load_records_from_dir(raw_dir)
    train_records, val_records, test_records = split_records(records, seed=seed)
    label_list = sorted({record.intent_label for record in records})
    label2id = {label: idx for idx, label in enumerate(label_list)}

    def to_dict(samples: List) -> Dict[str, List]:
        return {
            "text": [sample.text for sample in samples],
            "label": [label2id[sample.intent_label] for sample in samples],
        }

    dataset = DatasetDict(
        {
            "train": Dataset.from_dict(to_dict(train_records)),
            "validation": Dataset.from_dict(to_dict(val_records)),
            "test": Dataset.from_dict(to_dict(test_records)),
        }
    )
    return dataset, label2id


def tokenize_function(tokenizer, max_length):
    def _tokenize(batch: Dict[str, List[str]]) -> Dict[str, List[List[int]]]:
        return tokenizer(batch["text"], truncation=True, padding=False, max_length=max_length)

    return _tokenize


def main() -> None:
    default_raw = PROJECT_ROOT / "questions_generator" / "data" / "raw"
    default_out = BASE_DIR / "artifacts" / "intent"

    parser = argparse.ArgumentParser(description="Train intent classifier on TOON data")
    parser.add_argument("--raw-dir", type=Path, default=default_raw)
    parser.add_argument("--model-name", default="SecureBERT-2")
    parser.add_argument("--output-dir", type=Path, default=default_out)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    dataset, label2id = build_dataset(args.raw_dir, args.seed)
    id2label = {idx: label for label, idx in label2id.items()}

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    tokenized = dataset.map(tokenize_function(tokenizer, args.max_length), batched=True)

    data_collator = DataCollatorWithPadding(tokenizer)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=len(label2id),
        label2id=label2id,
        id2label=id2label,
    )

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=-1)
        return {
            "accuracy": accuracy_score(labels, preds),
            "f1_macro": f1_score(labels, preds, average="macro"),
        }

    training_args = TrainingArguments(
        output_dir=str(args.output_dir),
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.lr,
        num_train_epochs=args.epochs,
        seed=args.seed,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )
    trainer.train()

    metrics = trainer.evaluate(tokenized["test"])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "test_metrics.json").write_text(json.dumps(metrics, indent=2))
    trainer.save_model()


if __name__ == "__main__":
    main()
