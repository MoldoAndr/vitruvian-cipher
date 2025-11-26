#!/usr/bin/env python3
"""Fine-tune token classification head for entity extraction."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
from datasets import Dataset, DatasetDict
from seqeval.metrics import classification_report, f1_score
from transformers import (AutoModelForTokenClassification, AutoTokenizer, DataCollatorForTokenClassification,
                          Trainer, TrainingArguments)

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.pipeline.data import load_records_from_dir, split_records
from src.pipeline.ner import build_label_list, tokenize_and_align_labels


def build_dataset(raw_dir: Path, seed: int, max_samples: int | None = None) -> tuple[DatasetDict, Dict[str, int]]:
    records = [record for record in load_records_from_dir(raw_dir) if record.entities]
    if not records:
        raise RuntimeError("No entity-bearing samples found; generate more data first")
    if max_samples:
        records = records[:max_samples]
    train_records, val_records, test_records = split_records(records, seed=seed)
    labels = build_label_list(records)
    label2id = {label: idx for idx, label in enumerate(labels)}

    def to_dict(samples: List) -> Dict[str, List]:
        return {
            "text": [sample.text for sample in samples],
            "entities": [[entity.__dict__ for entity in sample.entities] for sample in samples],
        }

    dataset = DatasetDict(
        {
            "train": Dataset.from_dict(to_dict(train_records)),
            "validation": Dataset.from_dict(to_dict(val_records)),
            "test": Dataset.from_dict(to_dict(test_records)),
        }
    )
    return dataset, label2id


def main() -> None:
    default_raw = PROJECT_ROOT / "questions_generator" / "data" / "raw"
    default_out = BASE_DIR / "artifacts" / "entities"

    parser = argparse.ArgumentParser(description="Train NER model on TOON data")
    parser.add_argument("--raw-dir", type=Path, default=default_raw)
    parser.add_argument("--model-name", default="SecureBERT-2")
    parser.add_argument("--output-dir", type=Path, default=default_out)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    dataset, label2id = build_dataset(args.raw_dir, args.seed)
    id2label = {idx: label for label, idx in label2id.items()}

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    def tokenize(batch: Dict[str, List]):
        return tokenize_and_align_labels(batch, tokenizer, label2id, max_length=args.max_length)

    tokenized = dataset.map(tokenize, batched=True)
    data_collator = DataCollatorForTokenClassification(tokenizer)

    model = AutoModelForTokenClassification.from_pretrained(
        args.model_name,
        num_labels=len(label2id),
        label2id=label2id,
        id2label=id2label,
    )

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        true_predictions = [
            [id2label[p] for p, l in zip(pred, label) if l != -100]
            for pred, label in zip(predictions, labels)
        ]
        true_labels = [
            [id2label[l] for p, l in zip(pred, label) if l != -100]
            for pred, label in zip(predictions, labels)
        ]
        return {"f1": f1_score(true_labels, true_predictions)}

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
        metric_for_best_model="f1",
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

    predictions = trainer.predict(tokenized["test"])
    logits = predictions.predictions
    labels = predictions.label_ids
    pred_ids = np.argmax(logits, axis=-1)
    true_predictions = [
        [id2label[p] for p, l in zip(pred, label) if l != -100]
        for pred, label in zip(pred_ids, labels)
    ]
    true_labels = [
        [id2label[l] for p, l in zip(pred, label) if l != -100]
        for pred, label in zip(pred_ids, labels)
    ]
    report = classification_report(true_labels, true_predictions)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "test_report.txt").write_text(report)
    trainer.save_model()


if __name__ == "__main__":
    main()
