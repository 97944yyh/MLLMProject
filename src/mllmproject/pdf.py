from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from .schemas import PageText


def make_doc_id(path: Path) -> str:
    stem = re.sub(r"[^a-zA-Z0-9_\-\u4e00-\u9fff]+", "_", path.stem).strip("_")
    return stem or "document"


def extract_document_text(path: Path) -> list[PageText]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf_text(path)
    if suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="replace")
        return [PageText(page=1, text=text)]
    raise ValueError(f"Unsupported document type: {path.suffix}")


def extract_pdf_text(path: Path) -> list[PageText]:
    try:
        return _extract_with_pymupdf(path)
    except ModuleNotFoundError:
        return _extract_with_pdftotext(path)


def _extract_with_pymupdf(path: Path) -> list[PageText]:
    import fitz  # type: ignore[import-not-found]

    pages: list[PageText] = []
    with fitz.open(path) as document:
        for idx, page in enumerate(document, start=1):
            pages.append(PageText(page=idx, text=page.get_text("text")))
    return pages


def _extract_with_pdftotext(path: Path) -> list[PageText]:
    if shutil.which("pdftotext") is None:
        raise RuntimeError(
            "PDF parsing requires PyMuPDF (`fitz`) or the `pdftotext` command."
        )

    completed = subprocess.run(
        ["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    raw_pages = completed.stdout.split("\f")
    pages = [
        PageText(page=idx, text=text.strip())
        for idx, text in enumerate(raw_pages, start=1)
        if text.strip()
    ]
    if not pages:
        raise RuntimeError(f"No text extracted from PDF: {path}")
    return pages
