from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mllmproject.text_baseline import TextBaselinePipeline


def configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Text-RAG baseline for the MLLM document QA project."
    )
    subparsers = parser.add_subparsers(dest="command")

    build = subparsers.add_parser("build", help="Parse a document and build a local index.")
    build.add_argument("document", type=Path, help="PDF/TXT/MD file path.")
    build.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory for chunks and index JSON files.",
    )

    ask = subparsers.add_parser("ask", help="Ask a question against a document.")
    ask.add_argument("document", type=Path, help="PDF/TXT/MD file path.")
    ask.add_argument("question", type=str, help="Question to answer.")
    ask.add_argument("--top-k", type=int, default=5, help="Number of retrieved chunks.")
    ask.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory for chunks and index JSON files.",
    )
    ask.add_argument(
        "--json",
        action="store_true",
        help="Print the full AnswerResult as JSON.",
    )

    return parser


def cmd_build(args: argparse.Namespace) -> int:
    pipeline = TextBaselinePipeline.from_document(args.document, output_dir=args.output_dir)
    saved = pipeline.save()
    print(f"Built index for: {pipeline.doc_id}")
    print(f"Chunks: {len(pipeline.index.chunks)}")
    print(f"Chunks JSON: {saved['chunks_path']}")
    print(f"Index JSON: {saved['index_path']}")
    print(f"Document JSON: {saved['document_json_path']}")
    return 0


def cmd_ask(args: argparse.Namespace) -> int:
    pipeline = TextBaselinePipeline.from_document(args.document, output_dir=args.output_dir)
    result = pipeline.ask(args.question, top_k=args.top_k)

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return 0

    print(result.answer)
    print()
    print("Top evidence:")
    for evidence in result.evidences:
        preview = evidence.content.replace("\n", " ")
        if len(preview) > 160:
            preview = preview[:157] + "..."
        print(
            f"- page={evidence.page}, chunk={evidence.chunk_id}, "
            f"score={evidence.score:.3f}: {preview}"
        )
    return 0


def main() -> int:
    configure_console()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "build":
        return cmd_build(args)
    if args.command == "ask":
        return cmd_ask(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
