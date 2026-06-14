from __future__ import annotations

import re
from collections import Counter

from .embeddings import tokenize
from .schemas import AnswerResult, Citation, Evidence


def _sentences(text: str) -> list[str]:
    pieces = re.split(r"(?<=[。！？.!?])\s+|\n+", text)
    return [piece.strip() for piece in pieces if piece.strip()]


def _best_sentence(question: str, evidence: Evidence) -> str:
    query_terms = Counter(tokenize(question))
    best = ""
    best_score = -1
    for sentence in _sentences(evidence.content):
        terms = Counter(tokenize(sentence))
        score = sum(min(query_terms[token], terms[token]) for token in query_terms)
        if score > best_score:
            best = sentence
            best_score = score
    return best or evidence.content.strip()


def generate_mock_answer(question: str, evidences: list[Evidence]) -> AnswerResult:
    """Generate a deterministic citation-style answer without calling an LLM."""

    if not evidences:
        return AnswerResult(
            answer="答案：没有在文档中检索到足够相关的内容。\n来源：[]",
            citations=[],
            evidences=[],
        )

    top = evidences[: min(3, len(evidences))]
    selected = [_best_sentence(question, evidence) for evidence in top]
    compact = " ".join(sentence for sentence in selected if sentence)
    if len(compact) > 520:
        compact = compact[:517] + "..."

    citations = [
        Citation(
            page=evidence.page,
            chunk_id=evidence.chunk_id,
            bbox=evidence.bbox,
            source_type=evidence.source_type,
        )
        for evidence in top
    ]
    source_text = "; ".join(
        f"[page={citation.page}, chunk={citation.chunk_id}]"
        for citation in citations
    )
    answer = (
        "答案：根据检索到的文档片段，"
        f"{compact}\n"
        f"来源：{source_text}"
    )
    return AnswerResult(answer=answer, citations=citations, evidences=evidences)
