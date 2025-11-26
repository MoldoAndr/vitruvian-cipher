from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from sklearn.model_selection import train_test_split

from src.toon import parse_toon_records


@dataclass
class EntityRecord:
    type: str
    value: str
    confidence: float | None


@dataclass
class SampleRecord:
    text: str
    intent_label: str
    intent_confidence: float | None
    entities: List[EntityRecord]
    metadata: Dict[str, object]
    source: Dict[str, object]
    operation: str


def _normalize_entities(raw_entities: Iterable[Dict[str, object]]) -> List[EntityRecord]:
    entities: List[EntityRecord] = []
    for entity in raw_entities or []:
        etype = str(entity.get("type", "")).strip()
        value = str(entity.get("value", "")).strip()
        if not etype or not value:
            continue
        confidence = entity.get("confidence")
        if isinstance(confidence, str):
            try:
                confidence = float(confidence)
            except ValueError:
                confidence = None
        entities.append(
            EntityRecord(etype, value, confidence if isinstance(confidence, (int, float)) else None)
        )
    return entities


def cast_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def load_records_from_dir(raw_dir: Path, operations: Sequence[str] | None = None) -> List[SampleRecord]:
    records: List[SampleRecord] = []
    targets = set(op.lower() for op in operations) if operations else None
    for path in sorted(raw_dir.glob("*.jsonl")):
        for raw in parse_toon_records(path.read_text(encoding="utf-8")):
            operation = (raw.get("operation") or raw.get("intent", {}).get("label") or "").lower()
            if targets and operation not in targets:
                continue
            intent = raw.get("intent") or {}
            record = SampleRecord(
                text=str(raw.get("text", "")).strip(),
                intent_label=str(intent.get("label", operation or "other")).strip(),
                intent_confidence=cast_float(intent.get("confidence")),
                entities=_normalize_entities(raw.get("entities")),
                metadata=raw.get("metadata") or {},
                source=raw.get("source") or {},
                operation=operation or str(raw.get("operation", "")),
            )
            if record.text:
                records.append(record)
    return records


def split_records(
    records: List[SampleRecord],
    seed: int = 42,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
):
    if not 0 < train_ratio < 1 or not 0 < val_ratio < 1:
        raise ValueError("train and val ratios must be between 0 and 1")
    labels = [record.intent_label for record in records]
    train_idx, temp_idx = train_test_split(
        range(len(records)),
        test_size=1 - train_ratio,
        random_state=seed,
        stratify=labels if len(set(labels)) > 1 else None,
    )
    val_size = val_ratio / (1 - train_ratio)
    val_idx, test_idx = train_test_split(
        temp_idx,
        test_size=1 - val_size,
        random_state=seed,
        stratify=[labels[i] for i in temp_idx] if len(set(labels)) > 1 else None,
    )
    return (
        [records[i] for i in train_idx],
        [records[i] for i in val_idx],
        [records[i] for i in test_idx],
    )
