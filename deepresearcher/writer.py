from __future__ import annotations

import json
from typing import Sequence

import requests

from .config import Settings
from .retriever import RetrievedPage


def build_evidence_block(pages: Sequence[RetrievedPage]) -> str:
    blocks: list[str] = []
    for idx, page in enumerate(pages, start=1):
        trimmed = page.content[:4000]
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


def build_messages(question: str, pages: Sequence[RetrievedPage]) -> list[dict[str, str]]:
    evidence = build_evidence_block(pages)
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
) -> str:
    messages = build_messages(question=question, pages=pages)
    payload = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": 0.3,
    }
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        settings.llm_api_url,
        headers=headers,
        data=json.dumps(payload),
        timeout=settings.llm_timeout_seconds,
    )
    if not response.ok:
        response_text = response.text.strip()
        if len(response_text) > 1200:
            response_text = f"{response_text[:1200]}...(truncated)"
        raise RuntimeError(
            f"LLM request failed with status {response.status_code}: {response_text}"
        )
    data = response.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected LLM response format: {data}") from exc
