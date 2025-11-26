from __future__ import annotations

import json
import uuid
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

from .llm_providers import BaseProvider, build_provider
from .prompts import PromptSpec
from .toon import load_existing_texts, record_to_toon


class DatasetGenerator:
    _INVALID_ESCAPE = re.compile(r"\\(?![\"\\/bfnrt]|u[0-9a-fA-F]{4})")

    def __init__(
        self,
        prompt: PromptSpec,
        provider: BaseProvider,
        output_path: Path,
        target: int,
        batch_size: int | None = None,
        max_per_call: int | None = None,
    ) -> None:
        self.prompt = prompt
        self.provider = provider
        self.output_path = output_path
        self.target = target
        base_batch = batch_size or prompt.batch_size
        self.max_per_call = max_per_call or base_batch
        if self.max_per_call <= 0:
            raise ValueError("max_per_call must be positive")
        self._seen: Set[str] = set()
        if output_path.exists():
            self._seen.update(load_existing_texts(output_path))

    def run(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        collected = len(self._seen)
        with self.output_path.open("a", encoding="utf-8") as handle:
            while collected < self.target:
                remaining = self.target - collected
                request_size = min(self.max_per_call, remaining)
                prompt_payload = self.prompt.build_prompt(count=request_size)
                raw = self.provider.generate(prompt_payload["system"], prompt_payload["user"])
                cleaned = self._clean_response(raw)
                if not cleaned:
                    continue
                if cleaned.strip().lower().startswith(("i'm sorry", "i am sorry", "im sorry", "i’m sorry")):
                    continue
                try:
                    data = json.loads(cleaned)
                    if isinstance(data, dict) and "items" in data:
                        items = data["items"]
                    elif isinstance(data, list):
                        items = data
                    else:
                        raise ValueError("Unexpected JSON root")
                except json.JSONDecodeError:
                    fixed = self._fix_invalid_escapes(cleaned)
                    try:
                        data = json.loads(fixed)
                        if isinstance(data, dict) and "items" in data:
                            items = data["items"]
                        elif isinstance(data, list):
                            items = data
                        else:
                            raise ValueError("Unexpected JSON root")
                    except Exception as exc:  # noqa: BLE001
                        raise RuntimeError(f"LLM output not valid JSON: {raw[:200]}...") from exc
                except Exception as exc:  # noqa: BLE001
                    raise RuntimeError(f"LLM output not valid JSON: {raw[:200]}...") from exc

                for item in items:
                    if not isinstance(item, dict):
                        continue
                    text = item.get("text")
                    intent = item.get("intent")
                    if not text or not isinstance(intent, dict) or not intent.get("label"):
                        continue

                    normalized = text.strip().lower()
                    if normalized in self._seen:
                        continue
                    self._seen.add(normalized)

                    entities: List[Dict[str, object]] = []
                    for entity in item.get("entities", []) or []:
                        if not isinstance(entity, dict):
                            continue
                        if "type" not in entity or "value" not in entity:
                            continue
                        entities.append(
                            {
                                "type": entity["type"],
                                "value": entity["value"],
                                "confidence": entity.get("confidence"),
                            }
                        )

                    record: Dict[str, object] = {
                        "id": str(uuid.uuid4()),
                        "text": text.strip(),
                        "intent": {
                            "label": intent["label"],
                            "confidence": intent.get("confidence"),
                        },
                        "entities": entities,
                        "operation": intent.get("label", self.prompt.operation),
                        "metadata": item.get("metadata", {}),
                        "source": {
                            "prompt_file": str(self.prompt.raw.get("__file__", "")),
                            "provider": type(self.provider).__name__,
                            "model": self.provider.model,
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                        },
                    }
                    handle.write(record_to_toon(record))
                    collected += 1
                    if collected >= self.target:
                        break

    def _clean_response(self, raw: str) -> str:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        if text.lower().startswith("json"):
            text = text[4:].lstrip()
        return text

    def _fix_invalid_escapes(self, text: str) -> str:
        return self._INVALID_ESCAPE.sub(r"\\\\", text)
