"""
Lightweight BM25 lexical index for hybrid retrieval.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable, List


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*")


@dataclass(frozen=True)
class LexicalDocument:
    chunk_id: str
    text: str
    metadata: dict
    tokens: List[str]


@dataclass(frozen=True)
class LexicalResult:
    chunk_id: str
    text: str
    metadata: dict
    score: float


class LexicalIndex:
    """Simple BM25 index for keyword retrieval."""

    def __init__(
        self,
        documents: Iterable[LexicalDocument],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self._docs: List[LexicalDocument] = list(documents)
        self._k1 = k1
        self._b = b

        self._doc_lens = [len(doc.tokens) for doc in self._docs]
        self._avgdl = (sum(self._doc_lens) / len(self._doc_lens)) if self._doc_lens else 1.0

        self._inverted: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for idx, doc in enumerate(self._docs):
            counts = Counter(doc.tokens)
            for term, freq in counts.items():
                self._inverted[term].append((idx, freq))

        self._idf = {
            term: self._calc_idf(len(postings))
            for term, postings in self._inverted.items()
        }

    @staticmethod
    def tokenize(text: str) -> List[str]:
        return [token.lower() for token in TOKEN_RE.findall(text)]

    def search(self, query: str, top_k: int) -> List[LexicalResult]:
        tokens = self.tokenize(query)
        if not tokens or not self._docs:
            return []

        scores: dict[int, float] = defaultdict(float)
        for term in tokens:
            postings = self._inverted.get(term)
            if not postings:
                continue
            idf = self._idf.get(term, 0.0)
            for doc_idx, freq in postings:
                doc_len = self._doc_lens[doc_idx] or 1
                denom = freq + self._k1 * (1 - self._b + self._b * doc_len / self._avgdl)
                scores[doc_idx] += idf * (freq * (self._k1 + 1) / denom)

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]
        results: List[LexicalResult] = []
        for doc_idx, score in ranked:
            doc = self._docs[doc_idx]
            results.append(
                LexicalResult(
                    chunk_id=doc.chunk_id,
                    text=doc.text,
                    metadata=dict(doc.metadata),
                    score=float(score),
                )
            )
        return results

    def _calc_idf(self, doc_freq: int) -> float:
        doc_count = max(len(self._docs), 1)
        return math.log((doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)
