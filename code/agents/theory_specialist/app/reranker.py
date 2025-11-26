"""
ONNX-based cross-encoder reranker without PyTorch dependencies.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List

import numpy as np
import onnxruntime as ort
from huggingface_hub import snapshot_download
from tokenizers import Tokenizer


class OnnxCrossEncoder:
    """
    Minimal cross-encoder wrapper using ONNX Runtime and Hugging Face tokenizers.
    """

    def __init__(
        self,
        model_name: str,
        cache_dir: str,
        max_length: int = 512,
        providers: Iterable[str] | None = None,
    ) -> None:
        self.model_name = model_name
        self.max_length = max_length
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        local_dir = Path(
            snapshot_download(
                repo_id=model_name,
                cache_dir=str(self.cache_dir),
                allow_patterns=[
                    "onnx/model.onnx",
                    "tokenizer.json",
                ],
            )
        )

        self.tokenizer = Tokenizer.from_file(str(local_dir / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=max_length)

        provider_list = list(providers) if providers else ["CPUExecutionProvider"]
        self.session = ort.InferenceSession(
            str(local_dir / "onnx" / "model.onnx"),
            providers=provider_list,
        )

    def score(self, query: str, documents: Iterable[str]) -> List[float]:
        """
        Return sigmoid-normalized relevance scores for the given query/doc pairs.
        """
        scores: list[float] = []
        for doc in documents:
            encoding = self.tokenizer.encode(query, doc)
            input_ids = np.array([encoding.ids], dtype=np.int64)
            attention_mask = np.array([encoding.attention_mask], dtype=np.int64)

            logits = self.session.run(
                None,
                {
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                },
            )[0]
            logit = float(logits[0][0])
            scores.append(self._sigmoid(logit))
        return scores

    @staticmethod
    @lru_cache(maxsize=1024)
    def _sigmoid(value: float) -> float:
        return 1.0 / (1.0 + math.exp(-value))

