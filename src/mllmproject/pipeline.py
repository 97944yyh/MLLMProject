"""End-to-end mock RAG pipeline used by CLI, evaluation, and future UI."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from .index import VectorIndex
from .ingest import add_page_visual_evidence, load_document
from .models import MockGenerator, MockReranker, MockVisualSummarizer
from .router import route_question
from .schemas import AnswerResult, Document, Evidence


@dataclass
class RagPipeline:
    document: Document
    index: VectorIndex
    reranker: MockReranker
    generator: MockGenerator

    @classmethod
    def from_file(
        cls,
        source_path: str | Path,
        output_dir: str | Path = "data/processed",
        include_visual: bool = True,
        render_pages: bool = True,
    ) -> "RagPipeline":
        document = load_document(source_path, output_dir=output_dir, render_pages=render_pages)
        if include_visual:
            add_page_visual_evidence(document, summarizer=MockVisualSummarizer())
        index = VectorIndex()
        index.build(document.chunks)
        return cls(document=document, index=index, reranker=MockReranker(), generator=MockGenerator())

    def answer(self, question: str, mode: str = "auto", top_k: int = 5) -> tuple[AnswerResult, float]:
        start = time.perf_counter()
        route, reason, source_types = self._resolve_mode(question, mode)
        evidences = self.index.search(question, top_k=top_k * 2, source_types=source_types)
        evidences = self.reranker.rerank(question, evidences)[:top_k]
        answer, citations = self.generator.generate_answer(question, evidences, route=route, route_reason=reason)
        result = AnswerResult(
            answer=answer,
            citations=citations,
            route=route,
            route_reason=reason,
            evidences=evidences,
        )
        latency_ms = (time.perf_counter() - start) * 1000
        return result, latency_ms

    def _resolve_mode(self, question: str, mode: str) -> tuple[str, str, set[str] | None]:
        decision = route_question(question, mode=mode)
        source_types = set(decision.retrieval_modes) if decision.retrieval_modes else None
        return decision.route, decision.reason, source_types


def evidence_to_markdown(evidences: list[Evidence]) -> str:
    if not evidences:
        return "未检索到证据。"
    lines: list[str] = []
    for index, evidence in enumerate(evidences, start=1):
        chunk = evidence.chunk_id or evidence.evidence_id
        lines.append(
            f"{index}. page={evidence.page}, type={evidence.source_type}, score={evidence.score:.3f}, id={chunk}\n"
            f"   {evidence.content[:180]}"
        )
    return "\n".join(lines)
