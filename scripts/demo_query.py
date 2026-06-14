from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mllmproject import RagService
from mllmproject.text_baseline import TextBaselinePipeline
from mllmproject.text_utils import compact_preview


def main() -> None:
    configure_console()
    parser = argparse.ArgumentParser(description="Ask one question against a document with the mock RAG pipeline.")
    parser.add_argument("--doc", required=True, help="PDF or image document path.")
    parser.add_argument("--question", required=True, help="Question to ask.")
    parser.add_argument("--mode", default="auto", choices=["auto", "text-rag", "mm-rag"], help="Retrieval mode.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of evidences to keep.")
    args = parser.parse_args()

    if args.mode == "text-rag":
        engine = TextBaselinePipeline.from_document(args.doc)
        result = engine.ask(args.question, top_k=args.top_k)
    else:
        engine = RagService()
        engine.ingest_document(args.doc)
        result = engine.ask(args.question, mode=normalize_mode(args.mode), top_k=args.top_k)
    print(result.answer)
    print()
    print(f"Route: {result.route} ({result.route_reason})")
    print()
    print("Evidence:")
    for index, evidence in enumerate(result.evidences, start=1):
        print(
            f"{index}. page={evidence.page}, type={evidence.source_type}, "
            f"score={evidence.score:.3f}, id={evidence.chunk_id or evidence.region_id}"
        )
        print(f"   {compact_preview(evidence.content, 180)}")


def normalize_mode(mode: str) -> str:
    if mode == "text-rag":
        return "Text-RAG"
    if mode == "mm-rag":
        return "MM-RAG"
    return "Auto Router"


def configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


if __name__ == "__main__":
    main()
