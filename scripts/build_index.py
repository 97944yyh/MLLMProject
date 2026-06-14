from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mllmproject import RagService
from mllmproject.io_utils import ensure_dir, write_json


def configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    configure_console()
    parser = argparse.ArgumentParser(description="Build a local mock vector index for a document.")
    parser.add_argument("--doc", required=True, help="PDF or image document path.")
    parser.add_argument("--output", default=None, help="Index JSON output path.")
    args = parser.parse_args()

    engine = RagService()
    document = engine.ingest_document(args.doc)
    output = Path(args.output) if args.output else Path("data/indexes") / f"{document.doc_id}_chunks.json"
    ensure_dir(output.parent)
    write_json(output, [chunk.to_dict() for chunk in engine.index_chunks])
    print(f"Built {len(engine.index_chunks)} chunks for {document.doc_id}")
    print(f"Index saved to {output}")


if __name__ == "__main__":
    main()
