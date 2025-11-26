from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def load_clean_dir(clean_dir: Path) -> Dict[str, List[dict]]:
    buckets: Dict[str, List[dict]] = defaultdict(list)
    for path in clean_dir.glob("*.jsonl"):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                op = record.get("operation")
                if not op:
                    continue
                buckets[op].append(record)
    return buckets


def stratified_split(records: List[dict], per_class: int, seed: int = 42) -> Dict[str, List[dict]]:
    rng = random.Random(seed)
    rng.shuffle(records)
    subset = records[:per_class] if per_class else records
    n = len(subset)
    train_end = int(n * 0.8)
    val_end = train_end + int(n * 0.1)
    return {
        "train": subset[:train_end],
        "val": subset[train_end:val_end],
        "test": subset[val_end:],
    }


def build_corpus(clean_dir: Path, per_class: int, train_out: Path, val_out: Path, test_out: Path, seed: int = 42) -> None:
    buckets = load_clean_dir(clean_dir)
    accum = {"train": [], "val": [], "test": []}
    for operation, records in buckets.items():
        splits = stratified_split(records, per_class=per_class, seed=seed)
        for split_name, split_records in splits.items():
            accum[split_name].extend(split_records)
    for name, path in [("train", train_out), ("val", val_out), ("test", test_out)]:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for record in accum[name]:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
