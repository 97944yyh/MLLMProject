from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mllmproject.chunking import chunk_pages
from mllmproject.index import LocalVectorIndex
from mllmproject.pipeline import RagPipeline
from mllmproject.schemas import PageText
from mllmproject.answer import generate_mock_answer
from mllmproject.text_baseline import TextBaselinePipeline


class TextBaselineTest(unittest.TestCase):
    def test_chunk_index_answer_flow(self) -> None:
        pages = [
            PageText(
                page=1,
                text=(
                    "本项目构建文档智能助手，支持 PDF 文档问答。\n\n"
                    "期末验收需要最终报告、Demo 视频、代码仓库和实验结果。"
                ),
            ),
            PageText(page=2, text="系统使用 Text-RAG 检索文本 chunk，并输出引用页码。"),
        ]
        chunks = chunk_pages("demo", pages, max_chars=80, overlap=10)
        self.assertGreaterEqual(len(chunks), 2)

        index = LocalVectorIndex.from_chunks(chunks)
        evidences = index.search("期末验收需要提交什么", top_k=2)
        self.assertGreaterEqual(len(evidences), 1)
        self.assertEqual(evidences[0].page, 1)

        result = generate_mock_answer("期末验收需要提交什么", evidences)
        self.assertIn("答案：", result.answer)
        self.assertIn("来源：", result.answer)
        self.assertIn("page=1", result.answer)

    def test_text_rag_pipeline_from_txt_document(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "demo.txt"
            doc.write_text(
                "第一段介绍项目背景。\n\n"
                "期末验收需要提交最终报告、Demo 视频、代码仓库和实验结果。\n\n"
                "第三段介绍多模态 RAG 的后续扩展。",
                encoding="utf-8",
            )

            pipeline = TextBaselinePipeline.from_document(
                doc,
                output_dir=root / "processed",
                max_chars=45,
                overlap=5,
            )
            self.assertEqual(pipeline.doc_id, "demo")
            self.assertGreaterEqual(len(pipeline.chunks), 2)
            self.assertTrue(all(chunk.source_type == "text" for chunk in pipeline.chunks))
            self.assertTrue(all(chunk.image_path is None for chunk in pipeline.chunks))

            result = pipeline.ask("期末验收需要提交什么", top_k=2)
            self.assertEqual(result.route, "text_route")
            self.assertIn("来源：", result.answer)
            self.assertTrue(result.citations)
            self.assertEqual(result.citations[0].source_type, "text")

            saved = pipeline.save()
            for path in saved.values():
                self.assertTrue(path.exists())

            loaded_index = LocalVectorIndex.load(saved["index_path"])
            evidences = loaded_index.search("最终报告 Demo 视频", top_k=1, source_types={"text"})
            self.assertEqual(len(evidences), 1)
            self.assertEqual(evidences[0].source_type, "text")

    def test_common_rag_pipeline_supports_text_only_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "notes.md"
            doc.write_text(
                "# Demo Notes\n\n"
                "The text baseline extracts document text, chunks by page or paragraph, "
                "builds a local mock vector index, retrieves top-k evidence, and returns citations.",
                encoding="utf-8",
            )

            pipeline = RagPipeline.from_file(
                doc,
                output_dir=root / "processed",
                include_visual=False,
                render_pages=False,
            )

            self.assertGreaterEqual(len(pipeline.document.pages), 1)
            self.assertGreaterEqual(len(pipeline.document.chunks), 1)
            self.assertTrue(all(page.image_path is None for page in pipeline.document.pages))
            self.assertTrue(all(chunk.source_type == "text" for chunk in pipeline.document.chunks))

            result, latency_ms = pipeline.answer("What does the text baseline build?", mode="text-rag", top_k=2)
            self.assertEqual(result.route, "text_route")
            self.assertGreaterEqual(latency_ms, 0.0)
            self.assertTrue(result.citations)
            self.assertTrue(all(citation.source_type == "text" for citation in result.citations))


if __name__ == "__main__":
    unittest.main()
