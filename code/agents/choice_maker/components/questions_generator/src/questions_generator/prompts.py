from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import yaml


@dataclass
class PromptSpec:
    operation: str
    label: str
    batch_size: int
    system_prompt: str
    user_prompt: str
    post_rules: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: str | Path) -> "PromptSpec":
        path = Path(path)
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        data["__file__"] = str(path)
        return cls(
            operation=data["operation"],
            label=data.get("label", data["operation"]),
            batch_size=int(data.get("batch_size", 8)),
            system_prompt=data["system_prompt"].strip(),
            user_prompt=data["user_prompt"].strip(),
            post_rules=list(data.get("post_rules", [])),
            raw=data,
        )

    def build_prompt(self, count: int | None = None) -> Dict[str, str]:
        size = count or self.batch_size
        # The YAML user prompts use literal braces for JSON, so avoid str.format
        user_text = self.user_prompt.replace("{count}", str(size))
        return {
            "system": self.system_prompt,
            "user": user_text,
        }
