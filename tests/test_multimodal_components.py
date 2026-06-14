from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mllmproject.multimodal import (
    clamp_bbox,
    draw_evidence_preview,
    format_evidence_caption,
    make_mock_region_chunks,
    make_page_visual_chunks,
)
from mllmproject.schemas import Document, Evidence, Page


class MultimodalComponentsTest(unittest.TestCase):
    def test_page_visual_chunks_keep_bbox_and_image_path(self) -> None:
        document = Document(
            doc_id="demo_doc",
            pages=[
                Page(
                    doc_id="demo_doc",
                    page=1,
                    image_path="page_001.png",
                    width=100,
                    height=200,
                )
            ],
        )

        chunks = make_page_visual_chunks(document, summary_fn=lambda path: f"summary for {path}")

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].source_type, "page")
        self.assertEqual(chunks[0].bbox, [0.0, 0.0, 100.0, 200.0])
        self.assertEqual(chunks[0].image_path, "page_001.png")
        self.assertEqual(chunks[0].region_id, "demo_doc_p1_page")
        self.assertIn("summary for page_001.png", chunks[0].content)

    def test_mock_region_chunks_match_future_layout_schema(self) -> None:
        document = Document(
            doc_id="demo_doc",
            pages=[
                Page(
                    doc_id="demo_doc",
                    page=2,
                    image_path="page_002.png",
                    width=1000,
                    height=800,
                )
            ],
        )

        chunks = make_mock_region_chunks(document)

        self.assertEqual([chunk.source_type for chunk in chunks], ["figure", "table"])
        self.assertTrue(all(chunk.bbox for chunk in chunks))
        self.assertTrue(all(chunk.region_id for chunk in chunks))
        self.assertTrue(all(chunk.metadata.get("is_placeholder") for chunk in chunks))

    def test_bbox_clamp_and_caption(self) -> None:
        self.assertEqual(clamp_bbox([-10, 5, 120, 250], width=100, height=200), [0, 5, 100, 200])
        self.assertIsNone(clamp_bbox([120, 10, 130, 30], width=100, height=200))

        evidence = Evidence(
            evidence_id="ev1",
            doc_id="demo",
            page=3,
            source_type="figure",
            content="figure summary",
            score=0.75,
            chunk_id="chunk1",
            bbox=[0, 5, 100, 200],
            image_path="page.png",
            region_id="fig1",
        )
        caption = format_evidence_caption(evidence)
        self.assertIn("page=3", caption)
        self.assertIn("type=figure", caption)
        self.assertIn("bbox=[0, 5, 100, 200]", caption)

    def test_draw_evidence_preview_falls_back_without_bbox(self) -> None:
        evidence = Evidence(
            evidence_id="ev1",
            doc_id="demo",
            page=1,
            source_type="page",
            content="page summary",
            score=0.5,
            image_path="missing.png",
        )
        with tempfile.TemporaryDirectory() as tmp:
            preview = draw_evidence_preview(evidence, Path(tmp) / "preview.png")
        self.assertIsNotNone(preview)
        self.assertEqual(preview.image_path, "missing.png")


if __name__ == "__main__":
    unittest.main()
