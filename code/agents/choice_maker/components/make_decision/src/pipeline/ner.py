from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Sequence

from transformers import PreTrainedTokenizerBase

from .data import EntityRecord, SampleRecord


@dataclass
class EntitySpan:
    type: str
    start: int
    end: int


def find_entity_spans(text: str, entities: Sequence[EntityRecord]) -> List[EntitySpan]:
    spans: List[EntitySpan] = []
    lower_text = text.lower()
    for entity in entities:
        value = entity.value.strip()
        if not value:
            continue
        pattern = re.escape(value.lower())
        for match in re.finditer(pattern, lower_text):
            spans.append(EntitySpan(entity.type, match.start(), match.end()))
            break
    return spans


def build_label_list(records: Sequence[SampleRecord]) -> List[str]:
    types = sorted({entity.type for record in records for entity in record.entities})
    labels = ["O"]
    for etype in types:
        labels.append(f"B-{etype}")
        labels.append(f"I-{etype}")
    return labels


def tokenize_and_align_labels(
    examples: Dict[str, List],
    tokenizer: PreTrainedTokenizerBase,
    label2id: Dict[str, int],
    max_length: int = 256,
) -> Dict[str, List]:
    texts = examples["text"]
    entities = examples["entities"]
    encodings = tokenizer(
        texts,
        truncation=True,
        padding="max_length",
        max_length=max_length,
        return_offsets_mapping=True,
    )
    all_labels: List[List[int]] = []
    for idx, offsets in enumerate(encodings["offset_mapping"]):
        spans = find_entity_spans(texts[idx], [EntityRecord(**entity) for entity in entities[idx]])
        labels = [-100 if start == end else label2id["O"] for start, end in offsets]
        for span in spans:
            for token_idx, (start, end) in enumerate(offsets):
                if end <= span.start or start >= span.end:
                    continue
                label = f"B-{span.type}" if start == span.start else f"I-{span.type}"
                labels[token_idx] = label2id.get(label, label2id["O"])
        all_labels.append(labels)
    encodings["labels"] = all_labels
    encodings.pop("offset_mapping")
    return encodings
