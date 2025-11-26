from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from rapidfuzz import fuzz

from .toon import parse_toon_records, record_to_toon


class DatasetValidator:
    def __init__(self, min_length: int = 12, max_length: int = 240, sim_threshold: int = 92) -> None:
        self.min_length = min_length
        self.max_length = max_length
        self.sim_threshold = sim_threshold

    def _too_similar(self, text: str, accepted: List[str]) -> bool:
        for existing in accepted[-500:]:  # limit comparisons for speed
            if fuzz.ratio(text, existing) >= self.sim_threshold:
                return True
        return False

    def validate(self, input_path: Path, output_path: Path) -> None:
        accepted: List[str] = []
        output_path.parent.mkdir(parents=True, exist_ok=True)
        contents = input_path.read_text(encoding="utf-8")
        records = parse_toon_records(contents)
        if not records:
            for line in contents.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        with output_path.open("w", encoding="utf-8") as dst:
            for record in records:
                text = (record.get("text") or "").strip()
                if not (self.min_length <= len(text) <= self.max_length):
                    continue
                if self._too_similar(text, accepted):
                    continue
                accepted.append(text)
                record["metadata"] = record.get("metadata", {})
                record["metadata"].setdefault("validated", True)
                dst.write(record_to_toon(record))
