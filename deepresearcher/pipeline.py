from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

from .config import Settings
from .retriever import RetrievedPage, retrieve_pages
from .writer import call_llm_to_write_article


def build_research_notes(question: str, pages: list[RetrievedPage]) -> str:
    lines: list[str] = [
        f"# Research Notes",
        "",
        f"Question: {question}",
        f"Collected Sources: {len(pages)}",
        "",
    ]
    for idx, page in enumerate(pages, start=1):
        lines.extend(
            [
                f"## Source {idx}",
                f"- Title: {page.title}",
                f"- URL: {page.url}",
                f"- Snippet: {page.snippet}",
                "",
                page.content[:2000],
                "",
            ]
        )
    return "\n".join(lines)


def run_pipeline(
    question: str,
    settings: Settings,
    progress: Callable[[str], None] | None = None,
) -> tuple[Path, Path]:
    emit = progress or (lambda _: None)
    emit("Step 1/4: Retrieving web pages...")
    pages = retrieve_pages(
        question=question,
        results_per_query=settings.search_results_per_query,
        max_pages=settings.max_pages_to_read,
        progress=emit,
    )
    if not pages:
        raise RuntimeError("No web pages could be retrieved. Please try another question.")

    emit(f"Step 2/4: Retrieved {len(pages)} pages. Generating article with LLM...")
    article = call_llm_to_write_article(
        question=question,
        pages=pages,
        settings=settings,
        progress=emit,
    )

    emit("Step 3/4: Writing files to output directory...")
    output_dir = Path(settings.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    article_path = output_dir / f"article_{ts}.md"
    notes_path = output_dir / f"research_notes_{ts}.md"

    article_path.write_text(article, encoding="utf-8")
    notes = build_research_notes(question=question, pages=pages)
    notes_path.write_text(notes, encoding="utf-8")
    emit("Step 4/4: Completed.")
    return article_path, notes_path
