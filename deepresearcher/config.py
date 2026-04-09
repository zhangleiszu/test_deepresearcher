from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    llm_api_url: str
    llm_api_key: str
    llm_model: str
    llm_connect_timeout_seconds: int
    llm_timeout_seconds: int
    llm_max_retries: int
    llm_retry_backoff_seconds: int
    llm_max_sources: int
    llm_max_chars_per_source: int
    search_results_per_query: int
    max_pages_to_read: int
    output_dir: str


def load_settings() -> Settings:
    load_dotenv()

    llm_api_url = os.getenv("LLM_API_URL", "").strip()
    llm_api_key = os.getenv("LLM_API_KEY", "").strip()
    llm_model = os.getenv("LLM_MODEL", "GLM4.7").strip()
    output_dir = os.getenv("OUTPUT_DIR", "outputs").strip() or "outputs"

    llm_connect_timeout_seconds = int(os.getenv("LLM_CONNECT_TIMEOUT_SECONDS", "20"))
    llm_timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
    llm_max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
    llm_retry_backoff_seconds = int(os.getenv("LLM_RETRY_BACKOFF_SECONDS", "2"))
    llm_max_sources = int(os.getenv("LLM_MAX_SOURCES", "6"))
    llm_max_chars_per_source = int(os.getenv("LLM_MAX_CHARS_PER_SOURCE", "1800"))
    search_results_per_query = int(os.getenv("SEARCH_RESULTS_PER_QUERY", "5"))
    max_pages_to_read = int(os.getenv("MAX_PAGES_TO_READ", "8"))

    if not llm_api_url:
        raise ValueError("Missing LLM_API_URL in .env")
    if not llm_api_key:
        raise ValueError("Missing LLM_API_KEY in .env")

    return Settings(
        llm_api_url=llm_api_url,
        llm_api_key=llm_api_key,
        llm_model=llm_model,
        llm_connect_timeout_seconds=llm_connect_timeout_seconds,
        llm_timeout_seconds=llm_timeout_seconds,
        llm_max_retries=max(1, llm_max_retries),
        llm_retry_backoff_seconds=max(1, llm_retry_backoff_seconds),
        llm_max_sources=max(1, llm_max_sources),
        llm_max_chars_per_source=max(200, llm_max_chars_per_source),
        search_results_per_query=search_results_per_query,
        max_pages_to_read=max_pages_to_read,
        output_dir=output_dir,
    )
