"""Reusable multimodal evidence helpers for the demo pipeline.

The real model stack is intentionally not required here. These helpers create
page-level visual chunks, reserve a structure for future region/bbox evidence,
and render citation previews for the frontend.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

from .io_utils import ensure_dir
from .schemas import Chunk, Document, Evidence, Page


SummaryFn = Callable[[str], str]


@dataclass(slots=True)
class VisualRegion:
    """A future-compatible table/figure/formula region on a rendered page."""

    region_id: str
    doc_id: str
    page: int
    source_type: str
    bbox: list[float] | None
    image_path: str
    content: str
    metadata: dict = field(default_factory=dict)

    def to_chunk(self) -> Chunk:
        return Chunk(
            chunk_id=self.region_id,
            doc_id=self.doc_id,
            page=self.page,
            source_type=self.source_type,
            content=self.content,
            bbox=self.bbox,
            image_path=self.image_path,
            region_id=self.region_id,
            metadata=dict(self.metadata),
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class EvidencePreview:
    """Frontend-friendly preview image plus caption."""

    image_path: str
    caption: str

    def as_gallery_item(self) -> tuple[str, str]:
        return (self.image_path, self.caption)


def make_page_visual_chunks(
    document: Document,
    summary_fn: SummaryFn | None = None,
    source_type: str = "page",
) -> list[Chunk]:
    """Create one visual evidence chunk for each rendered page image."""

    chunks: list[Chunk] = []
    for page in document.pages:
        if not page.image_path:
            continue
        bbox = page_bbox(page)
        content = summary_fn(page.image_path) if summary_fn else default_page_summary(page)
        region_id = f"{document.doc_id}_p{page.page}_page"
        chunks.append(
            Chunk(
                chunk_id=region_id,
                doc_id=document.doc_id,
                page=page.page,
                source_type=source_type,
                content=content,
                bbox=bbox,
                image_path=page.image_path,
                region_id=region_id,
                metadata={
                    "summary_type": "mock_page_visual",
                    "region_kind": "page",
                    "component": "multimodal.make_page_visual_chunks",
                },
            )
        )
    return chunks


def make_mock_region_chunks(document: Document) -> list[Chunk]:
    """Create coarse placeholder regions for future table/figure detectors.

    This is not wired into the default index because synthetic regions can hurt
    retrieval quality. It gives the team a stable output shape for bbox-aware
    components while real layout detection is still pending.
    """

    chunks: list[Chunk] = []
    for page in document.pages:
        if not page.image_path:
            continue
        width, height = resolve_page_size(page)
        if not width or not height:
            continue
        regions = [
            (
                "figure",
                [0.10 * width, 0.22 * height, 0.90 * width, 0.58 * height],
                "候选图表区域，可用于后续图表趋势、坐标轴、颜色和曲线类问题。",
            ),
            (
                "table",
                [0.10 * width, 0.58 * height, 0.90 * width, 0.84 * height],
                "候选表格区域，可用于后续数值、最大最小、占比和对比类问题。",
            ),
        ]
        for local_index, (source_type, bbox, content) in enumerate(regions, start=1):
            region_id = f"{document.doc_id}_p{page.page}_{source_type}{local_index}"
            chunks.append(
                VisualRegion(
                    region_id=region_id,
                    doc_id=document.doc_id,
                    page=page.page,
                    source_type=source_type,
                    bbox=[round(value, 2) for value in bbox],
                    image_path=page.image_path,
                    content=content,
                    metadata={
                        "summary_type": "mock_layout_region",
                        "region_kind": source_type,
                        "is_placeholder": True,
                    },
                ).to_chunk()
            )
    return chunks


def page_bbox(page: Page) -> list[float] | None:
    width, height = resolve_page_size(page)
    if not width or not height:
        return None
    return [0.0, 0.0, float(width), float(height)]


def resolve_page_size(page: Page) -> tuple[int | None, int | None]:
    if page.width and page.height:
        return int(page.width), int(page.height)
    if not page.image_path:
        return None, None
    try:
        from PIL import Image
    except ImportError:
        return None, None

    try:
        with Image.open(page.image_path) as image:
            width, height = image.size
    except OSError:
        return None, None
    page.width = width
    page.height = height
    return width, height


def default_page_summary(page: Page) -> str:
    return f"第 {page.page} 页页面截图，可能包含正文、图表、表格、公式或图片区域。"


def draw_evidence_preview(evidence: Evidence, output_path: str | Path) -> EvidencePreview | None:
    """Draw a bbox-highlighted preview if possible, otherwise return the page image."""

    if not evidence.image_path:
        return None

    target = Path(output_path)
    preview_path = evidence.image_path
    if evidence.bbox:
        preview_path = draw_bbox_preview(evidence.image_path, evidence.bbox, target)
    caption = format_evidence_caption(evidence)
    return EvidencePreview(image_path=preview_path, caption=caption)


def draw_bbox_preview(
    image_path: str,
    bbox: list[float] | list[int] | None,
    output_path: str | Path,
) -> str:
    if not bbox:
        return image_path
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return image_path

    output = Path(output_path)
    ensure_dir(output.parent)
    try:
        with Image.open(image_path) as image:
            preview = image.convert("RGB")
            box = clamp_bbox(bbox, preview.width, preview.height)
            if box:
                draw = ImageDraw.Draw(preview, "RGBA")
                draw.rectangle(box, outline=(255, 48, 48, 255), width=6)
                draw.rectangle(box, fill=(255, 48, 48, 36))
            preview.save(output)
    except OSError:
        return image_path
    return str(output)


def clamp_bbox(
    bbox: list[float] | list[int],
    width: int,
    height: int,
) -> list[int] | None:
    if len(bbox) != 4 or width <= 0 or height <= 0:
        return None
    x1, y1, x2, y2 = [int(round(float(value))) for value in bbox]
    x1 = max(0, min(width, x1))
    x2 = max(0, min(width, x2))
    y1 = max(0, min(height, y1))
    y2 = max(0, min(height, y2))
    x1, x2 = sorted((x1, x2))
    y1, y2 = sorted((y1, y2))
    if x2 <= x1 or y2 <= y1:
        return None
    return [x1, y1, x2, y2]


def format_evidence_caption(evidence: Evidence) -> str:
    parts = [
        f"page={evidence.page}",
        f"type={evidence.source_type}",
        f"score={evidence.score:.3f}",
    ]
    if evidence.chunk_id:
        parts.append(f"chunk={evidence.chunk_id}")
    if evidence.region_id:
        parts.append(f"region={evidence.region_id}")
    if evidence.bbox:
        parts.append(f"bbox={format_bbox(evidence.bbox)}")
    return ", ".join(parts)


def format_bbox(bbox: list[float] | list[int]) -> str:
    return "[" + ", ".join(str(int(round(float(value)))) for value in bbox) + "]"
