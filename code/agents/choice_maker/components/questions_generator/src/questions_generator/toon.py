from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Set


def _format_value(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(value, ensure_ascii=False)


def record_to_toon(record: Dict[str, object]) -> str:
    lines: List[str] = ["item:"]
    lines.append(f"  id: {_format_value(record['id'])}")
    lines.append(f"  operation: {_format_value(record['operation'])}")
    lines.append(f"  text: {_format_value(record['text'])}")

    intent = record.get("intent", {})
    lines.append("  intent:")
    lines.append(f"    label: {_format_value(intent.get('label'))}")
    lines.append(f"    confidence: {_format_value(intent.get('confidence'))}")

    entities = record.get("entities", []) or []
    lines.append(f"  entities[{len(entities)}]{{type,value,confidence}}:")
    for entity in entities:
        row = ",".join(_format_value(entity.get(key)) for key in ("type", "value", "confidence"))
        lines.append(f"    {row}")

    metadata = record.get("metadata") or {}
    if metadata:
        lines.append("  metadata:")
        for key in sorted(metadata):
            lines.append(f"    {key}: {_format_value(metadata[key])}")
    else:
        lines.append("  metadata: {}")

    source = record.get("source") or {}
    if source:
        lines.append("  source:")
        for key in sorted(source):
            lines.append(f"    {key}: {_format_value(source[key])}")
    lines.append("")
    return "\n".join(lines)


def load_existing_texts(path: Path) -> Set[str]:
    seen: Set[str] = set()
    if not path.exists():
        return seen
    contents = path.read_text(encoding="utf-8")
    for record in parse_toon_records(contents):
        text = record.get("text", "")
        if text:
            seen.add(text.strip().lower())
    return seen


def parse_toon_records(contents: str) -> List[Dict[str, object]]:
    blocks: List[str] = []
    current: List[str] = []
    for raw in contents.splitlines():
        line = raw.rstrip("\n")
        if line.strip() == "item:":
            if current:
                blocks.append("\n".join(current))
            current = ["item:"]
        elif current:
            current.append(line)
        elif line.strip():
            current = [line]
    if current:
        blocks.append("\n".join(current))
    return [parse_toon_block(block) for block in blocks if block.strip()]


def parse_toon_block(block: str) -> Dict[str, object]:
    record: Dict[str, object] = {
        "intent": {},
        "entities": [],
        "metadata": {},
        "source": {},
    }
    state: str | None = None
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        stripped = line.strip()
        if stripped == "item:":
            continue
        indent = len(line) - len(stripped)
        if indent == 2 and stripped.endswith(":"):
            header = stripped[:-1]
            if header in {"intent", "metadata", "source"}:
                state = header
                continue
            if header.startswith("entities["):
                state = "entities"
                continue
        if indent == 2:
            key, value = stripped.split(":", 1)
            record[key.strip()] = _parse_value(value)
            continue
        if indent == 4:
            if state in {"intent", "metadata", "source"}:
                key, value = stripped.split(":", 1)
                target = record.setdefault(state, {})
                target[key.strip()] = _parse_value(value)
            elif state == "entities":
                record.setdefault("entities", []).append(_parse_entity_row(stripped))
    return record


def _parse_value(token: str) -> object:
    candidate = token.strip()
    if not candidate:
        return ""
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return candidate


def _parse_entity_row(row: str) -> Dict[str, object]:
    try:
        values = json.loads(f"[{row}]")
    except json.JSONDecodeError:
        parts = [part.strip() for part in row.split(",")]
        values = [_parse_value(part) for part in parts]
    keys = ("type", "value", "confidence")
    return {key: values[idx] if idx < len(values) else None for idx, key in enumerate(keys)}
