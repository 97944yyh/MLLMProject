"""Lightweight vector index with a FAISS-free fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .embeddings import HashEmbedding, dot
from .io_utils import read_json, write_json
from .models import MockEmbedder
from .schemas import Chunk, Evidence


class VectorIndex:
    """Small in-memory index used before FAISS is wired in."""

    def __init__(self, embedder: Any | None = None) -> None:
        self.embedder = embedder or MockEmbedder()
        self.chunks: list[Chunk] = []
        self.vectors: Any = []

    def build(self, chunks: list[Chunk]) -> None:
        self.chunks = list(chunks)
        self.vectors = self.embedder.embed_text([chunk.content for chunk in self.chunks])

    def search(self, query: str, top_k: int = 5, source_types: set[str] | None = None) -> list[Evidence]:
        if not self.chunks:
            return []
        query_vector = self.embedder.embed_text([query])[0]
        scored: list[tuple[float, Chunk]] = []
        for chunk, vector in zip(self.chunks, self.vectors):
            if source_types and chunk.source_type not in source_types:
                continue
            scored.append((similarity(query_vector, vector), chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [Evidence.from_chunk(chunk, score=score) for score, chunk in scored[:top_k]]

    def save(self, path: str | Path) -> None:
        payload = {
            "chunks": [chunk.to_dict() for chunk in self.chunks],
            "vectors": vectors_to_jsonable(self.vectors),
        }
        write_json(path, payload)

    @classmethod
    def load(cls, path: str | Path, embedder: Any | None = None) -> "VectorIndex":
        payload = read_json(path)
        index = cls(embedder=embedder)
        index.chunks = [Chunk.from_dict(item) for item in payload.get("chunks", [])]
        index.vectors = payload.get("vectors", [])
        return index


class LocalVectorIndex(VectorIndex):
    """Compatibility wrapper used by the text baseline CLI/tests."""

    def __init__(self, embedder: Any | None = None) -> None:
        super().__init__(embedder=embedder or HashEmbedding())

    @classmethod
    def from_chunks(cls, chunks: list[Chunk], embedder: Any | None = None) -> "LocalVectorIndex":
        index = cls(embedder=embedder)
        index.build(chunks)
        return index


SimpleVectorIndex = VectorIndex


def similarity(left: Any, right: Any) -> float:
    if isinstance(left, dict) and isinstance(right, dict):
        return float(dot(left, right))

    if hasattr(left, "tolist"):
        left = left.tolist()
    if hasattr(right, "tolist"):
        right = right.tolist()

    left_values = [float(value) for value in left]
    right_values = [float(value) for value in right]
    numerator = sum(a * b for a, b in zip(left_values, right_values))
    left_norm = sum(a * a for a in left_values) ** 0.5 or 1.0
    right_norm = sum(b * b for b in right_values) ** 0.5 or 1.0
    return float(numerator / (left_norm * right_norm))


def vectors_to_jsonable(vectors: Any) -> Any:
    if hasattr(vectors, "tolist"):
        return vectors.tolist()
    return vectors
