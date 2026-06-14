"""Small text helpers used by the mock retrieval stack."""

from __future__ import annotations

import re


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def tokenize(text: str) -> list[str]:
    normalized = normalize_text(text)
    return TOKEN_PATTERN.findall(normalized)


def split_into_chunks(text: str, max_chars: int = 900, overlap: int = 80) -> list[str]:
    """Split page text into stable paragraph-like chunks."""

    text = re.sub(r"\r\n?", "\n", text).strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_split_long_text(paragraph, max_chars=max_chars, overlap=overlap))
            continue

        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            current = paragraph

    if current:
        chunks.append(current.strip())

    return chunks


def _split_long_text(text: str, max_chars: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(text_len, start + max_chars)
        chunks.append(text[start:end].strip())
        if end == text_len:
            break
        start = max(0, end - overlap)
    return [chunk for chunk in chunks if chunk]


def compact_preview(text: str, max_chars: int = 220) -> str:
    text = normalize_text(text)
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars - 3]}..."
