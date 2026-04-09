from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

import requests
import trafilatura
from ddgs import DDGS


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

    keyword_query = build_keyword_query(q)
    contains_cjk = bool(re.search(r"[\u4e00-\u9fff]", q))
    suffixes = (
        ["深度分析", "案例", "风险", "最新进展"]
        if contains_cjk
        else ["background", "case study", "risks", "latest developments"]
    )

    candidates: list[str] = [q]
    if keyword_query and keyword_query != q:
        candidates.append(keyword_query)
    for suffix in suffixes:
        base = keyword_query or q
        candidates.append(f"{base} {suffix}")

    # Keep order while removing duplicates and empty strings.
    return [item for item in dict.fromkeys(candidates) if item.strip()]


def build_keyword_query(question: str) -> str:
    english_tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9-]{1,}", question)
    chinese_common_keywords = [
        "企业",
        "公司",
        "行业",
        "落地",
        "应用",
        "路径",
        "风险",
        "挑战",
        "治理",
        "安全",
        "成本",
        "效率",
    ]
    chinese_tokens = [kw for kw in chinese_common_keywords if kw in question]

    if not chinese_tokens:
        chinese_chunks = re.findall(r"[\u4e00-\u9fff]{2,}", question)
        if chinese_chunks:
            chinese_tokens.append(chinese_chunks[0][:10])

    tokens = english_tokens[:4] + chinese_tokens[:6]
    return " ".join(dict.fromkeys(tokens))


def search_web(query: str, max_results: int) -> list[SearchResult]:
    results: list[SearchResult] = []
    try:
        with DDGS() as ddgs:
            raw = ddgs.text(query, max_results=max_results)
            for item in raw:
                title = (item.get("title") or "").strip()
                url = (item.get("href") or "").strip()
                snippet = (item.get("body") or "").strip()
                if not url:
                    continue
                results.append(SearchResult(title=title, url=url, snippet=snippet))
    except Exception:
        return []
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
        # Fallback for sites that block default trafilatura fetching.
        try:
            response = requests.get(
                url,
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0 (DeepResearcherBot/1.0)"},
            )
            if response.ok:
                downloaded = response.text
        except requests.RequestException:
            return ""

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
            # Keep snippet as minimum viable evidence to avoid empty retrieval.
            content = result.snippet.strip()
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
