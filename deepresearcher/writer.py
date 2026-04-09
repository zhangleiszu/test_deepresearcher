from __future__ import annotations

import json
import time
from typing import Callable, Sequence

import requests

from .config import Settings
from .retriever import RetrievedPage


def build_evidence_block(
    pages: Sequence[RetrievedPage],
    *,
    max_sources: int,
    max_chars_per_source: int,
) -> str:
    blocks: list[str] = []
    for idx, page in enumerate(pages[:max_sources], start=1):
        trimmed = page.content[:max_chars_per_source]
        blocks.append(
            "\n".join(
                [
                    f"[Source {idx}]",
                    f"Title: {page.title}",
                    f"URL: {page.url}",
                    f"Snippet: {page.snippet}",
                    "Content:",
                    trimmed,
                ]
            )
        )
    return "\n\n".join(blocks)


def build_messages(question: str, pages: Sequence[RetrievedPage], settings: Settings) -> list[dict[str, str]]:
    evidence = build_evidence_block(
        pages,
        max_sources=settings.llm_max_sources,
        max_chars_per_source=settings.llm_max_chars_per_source,
    )
    system_prompt = (
        "You are a senior research writer. "
        "Given the user's question and retrieved web evidence, write a deep-thinking Chinese article. "
        "Requirements: "
        "1) clear thesis, "
        "2) layered analysis, "
        "3) compare viewpoints, "
        "4) concrete examples, "
        "5) practical suggestions, "
        "6) add a 'Sources' section listing cited links.\n"
        "If evidence is weak, explicitly state uncertainty and avoid fabrication."
    )
    user_prompt = (
        f"User question:\n{question}\n\n"
        "Retrieved evidence:\n"
        f"{evidence}\n\n"
        "Please produce the final article in Chinese, structured with headings."
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def call_llm_to_write_article(
    question: str,
    pages: Sequence[RetrievedPage],
    settings: Settings,
    progress: Callable[[str], None] | None = None,
) -> str:
    emit = progress or (lambda _: None)
    messages = build_messages(question=question, pages=pages, settings=settings)
    payload = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": 0.3,
    }
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    total_attempts = settings.llm_max_retries
    for attempt in range(1, total_attempts + 1):
        emit(
            f"[llm] request attempt {attempt}/{total_attempts} "
            f"(model={settings.llm_model}, timeout={settings.llm_timeout_seconds}s)"
        )
        try:
            response = requests.post(
                settings.llm_api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=(settings.llm_connect_timeout_seconds, settings.llm_timeout_seconds),
            )
        except requests.exceptions.Timeout as exc:
            if attempt < total_attempts:
                sleep_seconds = settings.llm_retry_backoff_seconds * (2 ** (attempt - 1))
                emit(f"[llm] timeout, retrying in {sleep_seconds}s...")
                time.sleep(sleep_seconds)
                continue
            raise RuntimeError(
                f"LLM request timed out after {total_attempts} attempts "
                f"(read timeout={settings.llm_timeout_seconds}s)."
            ) from exc
        except requests.RequestException as exc:
            if attempt < total_attempts:
                sleep_seconds = settings.llm_retry_backoff_seconds * (2 ** (attempt - 1))
                emit(f"[llm] network error, retrying in {sleep_seconds}s...")
                time.sleep(sleep_seconds)
                continue
            raise RuntimeError(f"LLM request failed due to network error: {exc}") from exc

        if not response.ok:
            response_text = response.text.strip()
            if len(response_text) > 1200:
                response_text = f"{response_text[:1200]}...(truncated)"
            if response.status_code in {429, 500, 502, 503, 504} and attempt < total_attempts:
                sleep_seconds = settings.llm_retry_backoff_seconds * (2 ** (attempt - 1))
                emit(f"[llm] server busy ({response.status_code}), retrying in {sleep_seconds}s...")
                time.sleep(sleep_seconds)
                continue
            raise RuntimeError(
                f"LLM request failed with status {response.status_code}: {response_text}"
            )

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected LLM response format: {data}") from exc

    raise RuntimeError("LLM request failed after retries.")
