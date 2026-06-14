"""Model contracts for replaceable retrieval and generation components."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .schemas import Evidence


class EmbeddingModel(ABC):
    @abstractmethod
    def embed_text(self, texts: list[str]):
        """Return one embedding vector per input text."""


class RerankerModel(ABC):
    @abstractmethod
    def rerank(self, query: str, evidences: list[Evidence]) -> list[Evidence]:
        """Return evidences sorted by relevance."""


class AnswerGenerator(ABC):
    @abstractmethod
    def generate_answer(self, query: str, evidences: list[Evidence], route: str, route_reason: str):
        """Generate an answer and citations for the selected evidence."""


class VisionSummaryModel(ABC):
    @abstractmethod
    def generate_visual_summary(self, image_path: str) -> str:
        """Generate a concise visual summary for a page or region image."""
