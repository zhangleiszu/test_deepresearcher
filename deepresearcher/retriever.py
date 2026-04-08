from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import trafilatura
from duckduckgo_search import DDGS


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str


@dataclass(frozen=True)
class RetrievedPage:
    title: str
    url: str
    snippet: str
    content: str


def generate_search_queries(question: str) -> list[str]:
    """
    Produce multiple web search queries from one user question.
    """
    q = question.strip()
    if not q:
        return []

    return [
        q,
        f"{q} background",
        f"{q} latest developments",
        f"{q} expert analysis",
    ]


def search_web(query: str, max_results: int) -> list[SearchResult]:
    results: list[SearchResult] = []
    with DDGS() as ddgs:
        raw = ddgs.text(query, max_results=max_results)
        for item in raw:
            title = (item.get("title") or "").strip()
            url = (item.get("href") or "").strip()
            snippet = (item.get("body") or "").strip()
            if not url:
                continue
            results.append(SearchResult(title=title, url=url, snippet=snippet))
    return results


def dedupe_results(results: Iterable[SearchResult]) -> list[SearchResult]:
    deduped: list[SearchResult] = []
    seen: set[str] = set()
    for r in results:
        if r.url in seen:
            continue
        seen.add(r.url)
        deduped.append(r)
    return deduped


def fetch_page_text(url: str) -> str:
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return ""
    text = trafilatura.extract(
        downloaded,
        include_links=False,
        include_comments=False,
        include_tables=False,
    )
    return (text or "").strip()


def retrieve_pages(question: str, results_per_query: int, max_pages: int) -> list[RetrievedPage]:
    queries = generate_search_queries(question)
    all_results: list[SearchResult] = []
    for q in queries:
        all_results.extend(search_web(q, max_results=results_per_query))

    unique_results = dedupe_results(all_results)
    pages: list[RetrievedPage] = []
    for result in unique_results:
        if len(pages) >= max_pages:
            break
        content = fetch_page_text(result.url)
        if not content:
            continue
        pages.append(
            RetrievedPage(
                title=result.title,
                url=result.url,
                snippet=result.snippet,
                content=content,
            )
        )
    return pages
