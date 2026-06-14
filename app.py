from __future__ import annotations

import html
import os
import sys
import argparse
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mllmproject import RagDemoEngine  # noqa: E402
from mllmproject.text_utils import compact_preview  # noqa: E402


ENGINE = RagDemoEngine()


def _load_gradio() -> Any:
    _disable_proxy_env_for_local_demo()
    try:
        import gradio as gr
    except ImportError as exc:  # pragma: no cover - user-facing startup guard
        raise SystemExit(
            "Gradio is not installed. Run `uv sync` or "
            "`pip install gradio pymupdf numpy pillow` before `python app.py`."
        ) from exc
    return gr


def _disable_proxy_env_for_local_demo() -> None:
    for key in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ):
        os.environ.pop(key, None)
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"
    os.environ["no_proxy"] = "127.0.0.1,localhost"


def _uploaded_path(file_obj: Any) -> str:
    if file_obj is None:
        raise ValueError("请先上传 PDF 或图片文件。")
    if isinstance(file_obj, str):
        return file_obj
    if hasattr(file_obj, "name"):
        return str(file_obj.name)
    raise ValueError("无法识别上传文件路径。")


def _type_label(source_type: str) -> str:
    labels = {
        "text": "Text",
        "page_visual": "Page",
        "figure": "Figure",
        "table": "Table",
        "visual": "Visual",
    }
    return labels.get(source_type, source_type.title())


def _doc_stats_html() -> str:
    document = ENGINE.document
    chunks = ENGINE.index_chunks
    if document is None:
        return """
        <div class="stats-grid">
          <div><b>0</b><span>Pages</span></div>
          <div><b>0</b><span>Chunks</span></div>
          <div><b>0</b><span>Visual</span></div>
          <div><b>Ready</b><span>Status</span></div>
        </div>
        """
    visual_count = sum(1 for chunk in chunks if chunk.source_type != "text")
    return f"""
    <div class="stats-grid">
      <div><b>{len(document.pages)}</b><span>Pages</span></div>
      <div><b>{len(chunks)}</b><span>Chunks</span></div>
      <div><b>{visual_count}</b><span>Visual</span></div>
      <div><b>Indexed</b><span>Status</span></div>
    </div>
    """


def _empty_knowledge_html() -> str:
    return """
    <div class="empty-knowledge">
      <div class="empty-mark">KB</div>
      <h3>上传文档后查看知识库</h3>
      <p>chunk、页面来源和 visual evidence 会在这里以知识库条目的形式展示。</p>
    </div>
    """


def _chunk_card_html(chunks: list[Any], selected_ids: set[str] | None = None) -> str:
    if not chunks:
        return _empty_knowledge_html()

    selected_ids = selected_ids or set()
    cards: list[str] = []
    for index, chunk in enumerate(chunks[:25], start=1):
        selected = chunk.chunk_id in selected_ids
        preview = html.escape(compact_preview(chunk.content, 520))
        bbox = html.escape(str(chunk.bbox or "-"))
        chip = html.escape(_type_label(chunk.source_type))
        page = html.escape(str(chunk.page))
        chunk_id = html.escape(chunk.region_id or chunk.chunk_id)
        active = "is-selected" if selected else ""
        checked = "checked" if selected else ""
        cards.append(
            f"""
            <article class="kb-card {active}">
              <div class="kb-select"><span class="check {checked}"></span></div>
              <div class="thumb">
                <span>{chip}</span>
                <b>{index:02d}</b>
              </div>
              <div class="kb-body">
                <div class="kb-meta">
                  <span>Page {page}</span>
                  <span>{chip}</span>
                  <span>{chunk_id}</span>
                </div>
                <p>{preview}</p>
                <div class="kb-foot">
                  <span>bbox {bbox}</span>
                  <span class="switch on"><i></i></span>
                </div>
              </div>
            </article>
            """
        )

    total = len(chunks)
    return f"""
    <div class="kb-list">
      {''.join(cards)}
    </div>
    <div class="pager">
      <span>Total {total}</span>
      <button class="page active">1</button>
      <button class="page">2</button>
      <button class="page">3</button>
      <span class="page-size">10 / page</span>
      <span>Go to</span>
      <span class="goto"></span>
      <span>Page</span>
    </div>
    """


def _result_html(answer: str, route_info: dict[str, Any], evidences: list[list[Any]]) -> str:
    if not answer:
        return """
        <div class="result-empty">
          <h3>查询结果</h3>
          <p>在底部输入问题后，这里会展示回答、路由和引用 evidence。</p>
        </div>
        """

    route = html.escape(str(route_info.get("route", "auto")))
    reason = html.escape(str(route_info.get("route_reason", "")))
    cards = []
    for row in evidences[:6]:
        evidence_id, page, source_type, score, chunk_id, _bbox, content = row
        cards.append(
            f"""
            <div class="evidence-hit">
              <div>
                <b>{html.escape(str(evidence_id))}</b>
                <span>Page {html.escape(str(page))} · {html.escape(str(source_type))}</span>
              </div>
              <em>{float(score):.4f}</em>
              <p>{html.escape(str(content))}</p>
              <small>{html.escape(str(chunk_id))}</small>
            </div>
            """
        )
    return f"""
    <section class="answer-panel">
      <div class="answer-head">
        <span>{route}</span>
        <p>{reason}</p>
      </div>
      <div class="answer-text">{html.escape(answer)}</div>
      <div class="hit-grid">{''.join(cards)}</div>
    </section>
    """


def parse_document(file_obj: Any) -> tuple[str, str, list[tuple[str, str]], str, dict[str, Any]]:
    try:
        document = ENGINE.ingest_document(_uploaded_path(file_obj))
    except Exception as exc:  # noqa: BLE001 - displayed in local demo UI.
        return f"解析失败：{exc}", _chunk_card_html([]), [], _doc_stats_html(), {}

    page_gallery = [
        (page.image_path, f"Page {page.page}")
        for page in document.pages
        if page.image_path
    ]
    metadata = {
        "doc_id": document.doc_id,
        "file_name": document.file_name,
        "pages": len(document.pages),
        "chunks": len(ENGINE.index_chunks),
        "source_path": document.source_path,
    }
    status = f"已索引 {document.file_name}：{len(document.pages)} 页，{len(ENGINE.index_chunks)} 个 chunks。"
    return status, _chunk_card_html(ENGINE.index_chunks), page_gallery, _doc_stats_html(), metadata


def ask_question(question: str, mode: str, top_k: int) -> tuple[str, str, list[list[Any]], list[tuple[str, str]], str]:
    try:
        result = ENGINE.ask(question, mode=mode, top_k=int(top_k))
    except Exception as exc:  # noqa: BLE001 - displayed in local demo UI.
        error = f"问答失败：{exc}"
        return error, _result_html(error, {}, []), [], [], _chunk_card_html(ENGINE.index_chunks)

    evidence_rows = [
        [
            evidence.evidence_id,
            evidence.page,
            evidence.source_type,
            round(evidence.score, 4),
            evidence.chunk_id or evidence.region_id or evidence.evidence_id,
            evidence.bbox,
            compact_preview(evidence.content, 260),
        ]
        for evidence in result.evidences
    ]
    route_info = {
        "route": result.route,
        "route_reason": result.route_reason,
        "citations": [citation.to_dict() for citation in result.citations],
    }
    previews = ENGINE.make_citation_previews(result.evidences)
    selected_ids = {evidence.chunk_id for evidence in result.evidences if evidence.chunk_id}
    selected_ids.update({evidence.evidence_id for evidence in result.evidences})
    return (
        result.answer,
        _result_html(result.answer, route_info, evidence_rows),
        evidence_rows,
        previews,
        _chunk_card_html(ENGINE.index_chunks, selected_ids=selected_ids),
    )


def clear_session() -> tuple[str, str, list[Any], str, dict[str, Any], str, str, list[Any], list[Any]]:
    global ENGINE
    ENGINE = RagDemoEngine()
    return (
        "已清空当前会话。",
        _chunk_card_html([]),
        [],
        _doc_stats_html(),
        {},
        "",
        _result_html("", {}, []),
        [],
        [],
    )


def build_demo() -> Any:
    gr = _load_gradio()

    css = """
    :root {
      --paper: #f7f9fb;
      --panel: rgba(255, 255, 255, 0.82);
      --line: rgba(119, 137, 151, 0.24);
      --ink: #1d2733;
      --muted: #637083;
      --blue: #3c82f6;
      --green: #43b284;
      --warm: #fff3d8;
    }

    .gradio-container {
      background:
        radial-gradient(circle at 18% 12%, rgba(255, 243, 216, 0.65), transparent 28%),
        linear-gradient(145deg, #f8fbff 0%, #f4f7f2 48%, #fff8ec 100%) !important;
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }

    #app-shell {
      max-width: 1480px;
      margin: 0 auto;
      padding: 18px 18px 96px;
    }

    #topbar {
      align-items: center;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.74);
      box-shadow: 0 18px 50px rgba(45, 56, 70, 0.08);
      padding: 12px 16px;
      backdrop-filter: blur(18px);
    }

    #brand h1 {
      margin: 0;
      font-size: 22px;
      line-height: 1.15;
      font-weight: 700;
      color: #172033;
    }

    #brand p {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 13px;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(88px, 1fr));
      gap: 8px;
      width: 100%;
    }

    .stats-grid div {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.72);
      padding: 10px 12px;
    }

    .stats-grid b {
      display: block;
      color: #162334;
      font-size: 17px;
      line-height: 1.1;
    }

    .stats-grid span {
      color: var(--muted);
      font-size: 12px;
    }

    #kb-workspace, #result-workspace {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.56);
      box-shadow: 0 18px 50px rgba(45, 56, 70, 0.07);
      overflow: hidden;
      min-height: 690px;
    }

    #kb-left, #kb-right {
      padding: 0;
      min-height: 690px;
    }

    #kb-left {
      border-right: 1px solid var(--line);
      background: rgba(235, 240, 244, 0.56);
    }

    .pane-title {
      border-bottom: 1px solid var(--line);
      padding: 14px 16px 12px;
      background: rgba(255, 255, 255, 0.58);
    }

    .pane-title h2 {
      margin: 0;
      font-size: 15px;
      line-height: 1.25;
      font-weight: 700;
    }

    .pane-title p {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 12px;
    }

    #upload-strip {
      padding: 12px 16px;
      border-bottom: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.5);
    }

    #parse-status textarea {
      min-height: 42px !important;
      font-size: 12px !important;
      color: var(--muted) !important;
    }

    .kb-list {
      height: 540px;
      overflow: auto;
      padding: 14px 16px;
    }

    .kb-card {
      display: grid;
      grid-template-columns: 28px 92px 1fr;
      gap: 14px;
      align-items: center;
      margin-bottom: 12px;
      border: 1px solid rgba(125, 140, 153, 0.2);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.84);
      padding: 14px;
      box-shadow: 0 8px 22px rgba(32, 42, 54, 0.05);
    }

    .kb-card.is-selected {
      border-color: rgba(60, 130, 246, 0.55);
      background: rgba(233, 242, 255, 0.9);
    }

    .kb-select .check {
      display: block;
      width: 16px;
      height: 16px;
      border-radius: 4px;
      border: 1px solid #a7b2bd;
      background: #fff;
    }

    .kb-select .check.checked {
      border-color: var(--blue);
      background: var(--blue);
      box-shadow: inset 0 0 0 4px #fff;
    }

    .thumb {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      width: 92px;
      height: 74px;
      border: 1px solid #dfe7ee;
      border-radius: 6px;
      background: linear-gradient(160deg, #ffffff, #edf5ff 58%, #fff4dc);
      padding: 9px;
      color: #4a5a6a;
    }

    .thumb span {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
    }

    .thumb b {
      font-size: 20px;
      color: rgba(60, 130, 246, 0.78);
    }

    .kb-body {
      min-width: 0;
    }

    .kb-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 6px;
    }

    .kb-meta span {
      border: 1px solid rgba(125, 140, 153, 0.24);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.76);
      padding: 3px 8px;
      color: #4d5d70;
      font-size: 11px;
    }

    .kb-body p {
      display: -webkit-box;
      -webkit-line-clamp: 4;
      -webkit-box-orient: vertical;
      overflow: hidden;
      margin: 0;
      color: #243142;
      font-size: 13px;
      line-height: 1.55;
    }

    .kb-foot {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 10px;
      color: var(--muted);
      font-size: 11px;
    }

    .switch {
      position: relative;
      width: 38px;
      height: 20px;
      border-radius: 999px;
      background: #ccd6df;
    }

    .switch i {
      position: absolute;
      top: 3px;
      left: 3px;
      width: 14px;
      height: 14px;
      border-radius: 999px;
      background: #fff;
    }

    .switch.on {
      background: var(--blue);
    }

    .switch.on i {
      left: 21px;
    }

    .pager {
      display: flex;
      gap: 8px;
      align-items: center;
      border-top: 1px solid var(--line);
      padding: 10px 16px;
      color: #465567;
      font-size: 13px;
      background: rgba(255, 255, 255, 0.7);
    }

    .page {
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: #334155;
      min-width: 28px;
      height: 26px;
    }

    .page.active {
      border-color: var(--blue);
      background: var(--blue);
      color: white;
    }

    .page-size, .goto {
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      padding: 4px 9px;
    }

    .goto {
      width: 40px;
      height: 25px;
    }

    .empty-knowledge, .result-empty {
      margin: 24px;
      border: 1px dashed rgba(125, 140, 153, 0.42);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.58);
      padding: 46px 24px;
      text-align: center;
      color: var(--muted);
    }

    .empty-mark {
      display: inline-grid;
      place-items: center;
      width: 58px;
      height: 58px;
      border-radius: 8px;
      background: #eaf2ff;
      color: var(--blue);
      font-weight: 800;
      margin-bottom: 14px;
    }

    .empty-knowledge h3, .result-empty h3 {
      margin: 0 0 6px;
      color: var(--ink);
      font-size: 16px;
    }

    #page-preview {
      padding: 16px;
      background: rgba(255, 255, 255, 0.7);
    }

    #page-preview .grid-wrap {
      border-radius: 8px;
      background: #fff;
    }

    #composer {
      position: fixed;
      left: 50%;
      bottom: 24px;
      z-index: 50;
      transform: translateX(-50%);
      width: min(920px, calc(100vw - 48px));
      border: 1px solid rgba(120, 136, 150, 0.25);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.68);
      box-shadow: 0 22px 70px rgba(29, 39, 51, 0.18);
      backdrop-filter: blur(24px);
      padding: 10px;
    }

    #composer textarea {
      background: transparent !important;
      border: 0 !important;
      box-shadow: none !important;
      font-size: 14px !important;
    }

    #composer .form {
      border: 0 !important;
      background: transparent !important;
    }

    #composer button {
      border-radius: 8px !important;
      min-width: 98px;
    }

    .answer-panel {
      padding: 18px;
    }

    .answer-head {
      border: 1px solid rgba(60, 130, 246, 0.18);
      border-radius: 8px;
      background: rgba(237, 246, 255, 0.8);
      padding: 12px 14px;
      margin-bottom: 12px;
    }

    .answer-head span {
      color: var(--blue);
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
    }

    .answer-head p {
      margin: 5px 0 0;
      color: #4c5c70;
      font-size: 13px;
    }

    .answer-text {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 16px;
      color: #223041;
      line-height: 1.7;
      white-space: pre-wrap;
    }

    .hit-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-top: 12px;
    }

    .evidence-hit {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.82);
      padding: 13px;
    }

    .evidence-hit div {
      display: flex;
      justify-content: space-between;
      gap: 12px;
    }

    .evidence-hit b {
      color: #223041;
      font-size: 13px;
    }

    .evidence-hit span, .evidence-hit small {
      color: var(--muted);
      font-size: 11px;
    }

    .evidence-hit em {
      color: var(--green);
      font-style: normal;
      font-weight: 800;
      font-size: 12px;
    }

    .evidence-hit p {
      margin: 8px 0;
      color: #354356;
      font-size: 12px;
      line-height: 1.5;
    }

    @media (max-width: 920px) {
      #topbar, #kb-workspace {
        border-radius: 0;
      }
      .stats-grid, .hit-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .kb-card {
        grid-template-columns: 24px 1fr;
      }
      .thumb {
        display: none;
      }
    }
    """

    with gr.Blocks(title="MLLM Evidence Knowledge Base", theme=gr.themes.Soft(), css=css) as demo:
        with gr.Column(elem_id="app-shell"):
            with gr.Row(elem_id="topbar"):
                gr.HTML(
                    """
                    <div id="brand">
                      <h1>MLLM Evidence Knowledge Base</h1>
                      <p>知识库查看、文档预览和多模态 RAG 查询工作台</p>
                    </div>
                    """
                )
                stats_html = gr.HTML(_doc_stats_html())

            with gr.Tabs():
                with gr.Tab("知识库"):
                    with gr.Row(elem_id="kb-workspace"):
                        with gr.Column(scale=7, elem_id="kb-left"):
                            gr.HTML(
                                """
                                <div class="pane-title">
                                  <h2>Evidence Chunks</h2>
                                  <p>按页面和类型查看 chunk 后的 evidence 内容</p>
                                </div>
                                """
                            )
                            with gr.Column(elem_id="upload-strip"):
                                with gr.Row():
                                    file_input = gr.UploadButton(
                                    "上传 PDF / 图片",
                                    file_types=[".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp"],
                                    )
                                    parse_button = gr.Button("解析并构建知识库", variant="primary")
                                    clear_button = gr.Button("清空")
                                with gr.Row():
                                    mode = gr.Dropdown(
                                        choices=["Auto Router", "Text-RAG", "MM-RAG"],
                                        value="Auto Router",
                                        label="检索模式",
                                        scale=2,
                                    )
                                    top_k = gr.Slider(1, 8, value=5, step=1, label="Top-K", scale=3)
                                parse_status = gr.Textbox(
                                    label="状态",
                                    value="等待上传文档。",
                                    lines=1,
                                    interactive=False,
                                    elem_id="parse-status",
                                )
                            knowledge_cards = gr.HTML(_chunk_card_html([]))

                        with gr.Column(scale=5, elem_id="kb-right"):
                            gr.HTML(
                                """
                                <div class="pane-title">
                                  <h2>Page Preview</h2>
                                  <p>文档页面预览与引用高亮</p>
                                </div>
                                """
                            )
                            page_gallery = gr.Gallery(
                                label="",
                                columns=1,
                                height=640,
                                object_fit="contain",
                                show_label=False,
                                elem_id="page-preview",
                            )
                            document_meta = gr.JSON(label="Document Metadata")

                with gr.Tab("查询结果"):
                    with gr.Row(elem_id="result-workspace"):
                        with gr.Column(scale=6):
                            result_panel = gr.HTML(_result_html("", {}, []))
                            answer_text = gr.Textbox(label="Answer Text", visible=False)
                        with gr.Column(scale=4):
                            evidence_table = gr.Dataframe(
                                headers=[
                                    "evidence_id",
                                    "page",
                                    "type",
                                    "score",
                                    "chunk/region",
                                    "bbox",
                                    "content",
                                ],
                                label="引用 Evidence",
                                wrap=True,
                                interactive=False,
                            )
                            cited_gallery = gr.Gallery(
                                label="引用页 / bbox 高亮",
                                columns=1,
                                height=420,
                                object_fit="contain",
                            )

            with gr.Row(elem_id="composer"):
                question = gr.Textbox(
                    label="",
                    placeholder="Ask about this evidence...",
                    lines=1,
                    max_lines=4,
                    container=False,
                    scale=10,
                )
                ask_button = gr.Button("查询", variant="primary", scale=1)

        parse_button.click(
            parse_document,
            inputs=[file_input],
            outputs=[parse_status, knowledge_cards, page_gallery, stats_html, document_meta],
        )
        ask_button.click(
            ask_question,
            inputs=[question, mode, top_k],
            outputs=[answer_text, result_panel, evidence_table, cited_gallery, knowledge_cards],
        )
        clear_button.click(
            clear_session,
            outputs=[
                parse_status,
                knowledge_cards,
                page_gallery,
                stats_html,
                document_meta,
                answer_text,
                result_panel,
                evidence_table,
                cited_gallery,
            ],
        )

    return demo


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the MLLM evidence demo.")
    parser.add_argument("--server-name", default="127.0.0.1")
    parser.add_argument("--server-port", type=int, default=7860)
    args = parser.parse_args()
    build_demo().launch(server_name=args.server_name, server_port=args.server_port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
