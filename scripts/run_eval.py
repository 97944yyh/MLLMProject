from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mllmproject.evaluation import run_comparison, run_evaluation


def configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    configure_console()
    parser = argparse.ArgumentParser(description="Run document RAG evaluation.")
    parser.add_argument("--doc", required=True, help="PDF or image document path.")
    parser.add_argument("--samples", required=True, help="Evaluation samples JSON.")
    parser.add_argument("--output-dir", default="data/eval/results", help="Directory for JSON/CSV outputs.")
    parser.add_argument(
        "--mode",
        default="auto",
        choices=["auto", "text-rag", "mm-rag", "all"],
        help="Evaluation mode. Use 'all' to compare Text-RAG, MM-RAG, and Auto Router.",
    )
    parser.add_argument("--top-k", type=int, default=5, help="Number of evidences to keep.")
    args = parser.parse_args()

    if args.mode == "all":
        result = run_comparison(
            doc_path=args.doc,
            samples_path=args.samples,
            output_dir=args.output_dir,
            top_k=args.top_k,
        )
        print("Comparison summary:")
        for row in result["summary"]:
            metrics = ", ".join(f"{key}={value:.4f}" for key, value in row.items() if isinstance(value, float))
            print(f"  {row['mode']}: {metrics}")
        return

    result = run_evaluation(
        doc_path=args.doc,
        samples_path=args.samples,
        output_dir=args.output_dir,
        mode=args.mode,
        top_k=args.top_k,
    )
    print("Evaluation summary:")
    for key, value in result["summary"].items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
