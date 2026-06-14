from __future__ import annotations

import re

from .schemas import Chunk, PageText


def _paragraphs(text: str) -> list[str]:
    normalized = re.sub(r"[ \t]+", " ", text)
    parts = re.split(r"\n\s*\n+", normalized)
    paragraphs = [part.strip() for part in parts if part.strip()]
    if paragraphs:
        return paragraphs
    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    return lines


def _split_long_text(text: str, max_chars: int, overlap: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def chunk_pages(
    doc_id: str,
    pages: list[PageText],
    max_chars: int = 900,
    overlap: int = 120,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    counter = 0

    for page in pages:
        current = ""
        for paragraph in _paragraphs(page.text):
            if len(paragraph) > max_chars:
                if current:
                    counter += 1
                    chunks.append(
                        Chunk(
                            chunk_id=f"{doc_id}_p{page.page}_c{counter:04d}",
                            doc_id=doc_id,
                            page=page.page,
                            source_type="text",
                            content=current.strip(),
                        )
                    )
                    current = ""
                for piece in _split_long_text(paragraph, max_chars, overlap):
                    counter += 1
                    chunks.append(
                        Chunk(
                            chunk_id=f"{doc_id}_p{page.page}_c{counter:04d}",
                            doc_id=doc_id,
                            page=page.page,
                            source_type="text",
                            content=piece,
                        )
                    )
                continue

            next_text = f"{current}\n\n{paragraph}".strip() if current else paragraph
            if len(next_text) > max_chars and current:
                counter += 1
                chunks.append(
                    Chunk(
                        chunk_id=f"{doc_id}_p{page.page}_c{counter:04d}",
                        doc_id=doc_id,
                        page=page.page,
                        source_type="text",
                        content=current.strip(),
                    )
                )
                current = paragraph
            else:
                current = next_text

        if current:
            counter += 1
            chunks.append(
                Chunk(
                    chunk_id=f"{doc_id}_p{page.page}_c{counter:04d}",
                    doc_id=doc_id,
                    page=page.page,
                    source_type="text",
                    content=current.strip(),
                )
            )

    return chunks
