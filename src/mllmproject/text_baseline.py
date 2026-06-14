"""Pure text RAG baseline without model downloads or multimodal preprocessing."""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .answer import generate_mock_answer
from .chunking import chunk_pages
from .embeddings import tokenize
from .index import LocalVectorIndex
from .io_utils import ensure_dir, write_json
from .pdf import extract_document_text, make_doc_id
from .schemas import AnswerResult, Chunk, PageText


@dataclass(slots=True)
class TextBaselineArtifacts:
    doc_id: str
    chunks_path: Path
    index_path: Path
    metadata_path: Path
    document_json_path: Path
    document_path: Path


class TextBaselinePipeline:
    """End-to-end text-only RAG baseline.

    This class intentionally avoids page rendering, OCR, VLM calls, FAISS, and
    external embedding models. It is the stable baseline used to compare later
    MM-RAG work against.
    """

    def __init__(
        self,
        doc_id: str,
        document_path: str | Path,
        pages: list[PageText],
        chunks: list[Chunk],
        index: LocalVectorIndex,
        output_dir: str | Path = "data/processed",
    ) -> None:
        self.doc_id = doc_id
        self.document_path = Path(document_path)
        self.pages = pages
        self.chunks = chunks
        self.index = index
        self.output_dir = Path(output_dir)

    @classmethod
    def from_document(
        cls,
        document_path: str | Path,
        output_dir: str | Path = "data/processed",
        max_chars: int = 900,
        overlap: int = 120,
    ) -> "TextBaselinePipeline":
        source = Path(document_path)
        if not source.exists():
            raise FileNotFoundError(source)

        doc_id = make_doc_id(source)
        pages = extract_document_text(source)
        chunks = chunk_pages(doc_id, pages, max_chars=max_chars, overlap=overlap)
        index = LocalVectorIndex.from_chunks(chunks)
        return cls(
            doc_id=doc_id,
            document_path=source,
            pages=pages,
            chunks=chunks,
            index=index,
            output_dir=output_dir,
        )

    def ask(self, question: str, top_k: int = 5) -> AnswerResult:
        if not question.strip():
            raise ValueError("Question cannot be empty.")
        start = time.perf_counter()
        candidates = self.index.search(question, top_k=max(top_k * 4, top_k), source_types={"text"})
        evidences = rerank_by_token_overlap(question, candidates)[:top_k]
        result = generate_mock_answer(question, evidences)
        result.route = "text_route"
        result.route_reason = "Text baseline: extract text, chunk, hash-embed, retrieve, and mock-answer with citations."
        result.evidences = evidences
        result_latency_ms = (time.perf_counter() - start) * 1000
        for evidence in result.evidences:
            evidence.metadata["latency_ms"] = result_latency_ms
        return result

    def save(self) -> dict[str, Path]:
        artifacts = self.artifacts
        ensure_dir(artifacts.document_path)
        write_json(artifacts.chunks_path, [chunk.to_dict() for chunk in self.chunks])
        self.index.save(artifacts.index_path)
        write_json(artifacts.metadata_path, self.metadata())
        write_json(artifacts.document_json_path, self.document_payload())
        return {
            "chunks_path": artifacts.chunks_path,
            "index_path": artifacts.index_path,
            "metadata_path": artifacts.metadata_path,
            "document_json_path": artifacts.document_json_path,
        }

    @property
    def artifacts(self) -> TextBaselineArtifacts:
        doc_dir = self.output_dir / self.doc_id
        return TextBaselineArtifacts(
            doc_id=self.doc_id,
            chunks_path=doc_dir / "chunks.json",
            index_path=doc_dir / "index.json",
            metadata_path=doc_dir / "metadata.json",
            document_json_path=doc_dir / "document.json",
            document_path=doc_dir,
        )

    def metadata(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "source_path": str(self.document_path),
            "mode": "text_baseline",
            "page_count": len(self.pages),
            "chunk_count": len(self.chunks),
            "embedding": "local_hash_embedding",
            "index": "local_cosine_index",
            "generator": "mock_extract_answer",
        }

    def document_payload(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "source_path": str(self.document_path),
            "pages": [page.to_dict() for page in self.pages],
            "chunks": [chunk.to_dict() for chunk in self.chunks],
            "metadata": self.metadata(),
        }


def rerank_by_token_overlap(question: str, evidences: list) -> list:
    query_counts = Counter(tokenize(question))
    if not query_counts:
        return evidences

    reranked = []
    for evidence in evidences:
        evidence_counts = Counter(tokenize(evidence.content))
        overlap = sum(min(query_counts[token], evidence_counts[token]) for token in query_counts)
        coverage = overlap / max(sum(query_counts.values()), 1)
        evidence.score = evidence.score + coverage
        reranked.append(evidence)
    return sorted(reranked, key=lambda item: item.score, reverse=True)
