"""
Web search integration for the RAG system (Tavily).
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from threading import Lock
from typing import List, Optional

import requests
from sqlalchemy.orm import Session

from .config import Settings, get_settings
from .models import WebSearchResult

logger = logging.getLogger(__name__)

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    score: float = 1.0
    published_date: Optional[str] = None
    source: str = "tavily"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "score": self.score,
            "published_date": self.published_date,
            "source": self.source,
        }


class TavilyProvider:
    name = "tavily"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session = requests.Session()

    def search(self, query: str, max_results: int) -> List[SearchResult]:
        if not self.settings.tavily_api_key:
            raise ValueError("TAVILY_API_KEY not configured")

        payload = {
            "api_key": self.settings.tavily_api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False,
            "include_images": False,
        }
        response = self.session.post(
            TAVILY_SEARCH_URL,
            json=payload,
            timeout=self.settings.web_search_timeout,
        )
        response.raise_for_status()
        data = response.json()

        results: List[SearchResult] = []
        for item in data.get("results", []):
            url = str(item.get("url", "")).strip()
            title = str(item.get("title", "")).strip()
            if not url or not title:
                continue
            snippet = str(item.get("content", "")).strip()
            score = float(item.get("score", 1.0) or 1.0)
            results.append(
                SearchResult(
                    title=title[:200],
                    url=url,
                    snippet=snippet[:800],
                    score=score,
                    published_date=item.get("published_date"),
                    source=self.name,
                )
            )
        return results


class WebSearchManager:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._provider = TavilyProvider(self.settings)
        self._cache: dict[str, tuple[List[SearchResult], float]] = {}
        self._cache_lock = Lock()

    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        session: Optional[Session] = None,
    ) -> List[SearchResult]:
        if not self.settings.enable_web_search:
            return []

        normalized = self._sanitize_query(query)
        if not normalized:
            return []

        if self.settings.web_search_provider.lower() != "tavily":
            logger.warning(
                "Unsupported web search provider '%s'; only Tavily is configured.",
                self.settings.web_search_provider,
            )
            return []

        if not self.settings.tavily_api_key:
            logger.warning("Web search enabled but TAVILY_API_KEY not set.")
            return []

        max_results = max_results or self.settings.web_search_top_k
        cache_key = f"{normalized}:{max_results}"

        with self._cache_lock:
            cached = self._cache.get(cache_key)
            if cached:
                results, timestamp = cached
                if time.time() - timestamp < self.settings.web_search_cache_ttl:
                    return results

        try:
            results = self._search_with_retry(normalized, max_results)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Web search failed for query '%s': %s", normalized, exc)
            return []

        min_score = self.settings.web_search_min_relevance_score
        if min_score > 0:
            results = [r for r in results if r.score >= min_score]

        with self._cache_lock:
            self._cache[cache_key] = (results, time.time())
            if len(self._cache) > 100:
                oldest_key = min(self._cache, key=lambda k: self._cache[k][1])
                self._cache.pop(oldest_key, None)

        if session and results:
            self._cache_results_in_db(session, normalized, results)

        return results

    def _search_with_retry(self, query: str, max_results: int) -> List[SearchResult]:
        last_exc: Optional[Exception] = None
        for attempt in range(max(self.settings.web_search_max_retries, 1)):
            try:
                return self._provider.search(query, max_results)
            except Exception as exc:  # pylint: disable=broad-except
                last_exc = exc
                if attempt < self.settings.web_search_max_retries - 1:
                    wait_time = 2 ** (attempt + 1)
                    time.sleep(wait_time)
        if last_exc:
            raise last_exc
        return []

    @staticmethod
    def _sanitize_query(query: str) -> str:
        cleaned = re.sub(r"<[^>]+>", " ", query or "")
        cleaned = " ".join(cleaned.split())
        return cleaned.strip()

    def _cache_results_in_db(
        self,
        session: Session,
        query: str,
        results: List[SearchResult],
    ) -> None:
        try:
            for result in results:
                session.add(
                    WebSearchResult(
                        query=query,
                        title=result.title,
                        url=result.url,
                        snippet=result.snippet,
                        score=result.score,
                        provider=result.source,
                    )
                )
            session.commit()
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to cache web search results: %s", exc)
            session.rollback()

