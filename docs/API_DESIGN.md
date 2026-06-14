# 接口设计文档：文档多模态 RAG Demo

## 1. 设计目标

当前项目采用 mock-first 的接口设计：先让前端 Demo、解析、索引、检索、路由、回答展示完整跑通，再逐步替换真实模型。

本接口文档服务三人并行开发：

- 刘天翔：前端 Demo、总集成、README、开发日志。
- 杨毅涵：Text-RAG baseline、文本索引、检索、rerank 替换。
- 郭翊涛：页面图、多模态 evidence、路由、评测。

## 2. 核心数据结构

代码位置：`src/mllmproject/schemas.py`

### Page

表示文档中的一页。

```json
{
  "doc_id": "doc_xxx",
  "page": 1,
  "text": "本页文本",
  "image_path": "data/processed/doc_xxx/pages/page_001.png",
  "width": 1240,
  "height": 1754
}
```

### Chunk

表示进入索引的最小检索单元。

```json
{
  "chunk_id": "doc001_p3_c001",
  "doc_id": "doc001",
  "page": 3,
  "source_type": "text",
  "content": "文本内容",
  "bbox": null,
  "image_path": null,
  "region_id": null,
  "metadata": {}
}
```

`source_type` 约定：

- `text`：文本 chunk。
- `table`：表格 Markdown 或表格摘要。
- `figure`：图表、公式、图片区域。
- `page`：整页视觉 evidence，占位用于 MM-RAG 原型。

### Evidence

表示检索返回的证据。

```json
{
  "evidence_id": "doc001_p3_visual",
  "doc_id": "doc001",
  "page": 3,
  "source_type": "page",
  "content": "第 3 页的页面截图，可能包含图表或表格。",
  "score": 0.87,
  "chunk_id": "doc001_p3_visual",
  "bbox": [0, 0, 1240, 1754],
  "image_path": "data/processed/doc001/pages/page_003.png",
  "region_id": null,
  "metadata": {}
}
```

### Citation

表示回答引用。

```json
{
  "page": 3,
  "source_type": "text",
  "chunk_id": "doc001_p3_c001",
  "bbox": null,
  "region_id": null,
  "evidence_id": "doc001_p3_c001"
}
```

### AnswerResult

表示一次问答最终结果。

```json
{
  "answer": "答案：...\n来源：[page=3, chunk=doc001_p3_c001]",
  "citations": [],
  "evidences": [],
  "route": "text_route",
  "route_reason": "手动选择 Text-RAG，仅检索文本 chunk"
}
```

## 3. 模型替换接口

模型抽象接口在 `src/mllmproject/model_interfaces.py`，当前 mock 实现在 `src/mllmproject/models.py`。

### MockEmbedder

```python
embed_text(texts: list[str]) -> list[list[float]]
```

后续替换为 BGE-M3。要求输入多条文本，输出等长向量列表。

### VectorIndex

代码位置：`src/mllmproject/index.py`

```python
index.build(chunks)
index.search(query, top_k=5, source_types=None)
```

当前使用本地余弦相似度。后续可替换为 FAISS，但保持 `build/search/save/load` 接口不变。

### MockReranker

```python
rerank(query: str, evidences: list[Evidence]) -> list[Evidence]
```

后续替换为 BGE-reranker-v2-m3。要求返回按相关性降序排列的 evidence。

### MockGenerator

```python
generate_answer(query, evidences, route, route_reason) -> tuple[str, list[Citation]]
```

后续替换为 Qwen 或 Qwen2.5-VL。要求回答必须包含：

```text
答案：...
来源：[page=..., chunk=...]
```

### MockVisualSummarizer

```python
generate_visual_summary(image_path: str) -> str
```

后续替换为 Qwen2.5-VL。输出文本会作为视觉 evidence 进入索引。

## 3.5 多模态组件

代码位置：`src/mllmproject/multimodal.py`

该模块负责把页面图、bbox、视觉摘要和前端预览统一起来，避免多模态逻辑散落在前端和 ingest 模块里。

主要组件：

- `VisualRegion`：表示表格、图表、公式等页面区域，字段包含 `region_id/page/source_type/bbox/image_path/content`。
- `make_page_visual_chunks(document, summary_fn)`：把每页渲染图片转换为 `source_type="page"` 的 visual chunk。
- `make_mock_region_chunks(document)`：生成占位 figure/table bbox，用来提前联调 bbox-aware evidence 结构；默认不进入主索引，避免假区域影响检索。
- `draw_evidence_preview(evidence, output_path)`：根据 evidence 的页面图和 bbox 生成前端高亮预览。

后续接入真实多模态能力时，优先替换：

- 页面级摘要：`MockVisualSummarizer.generate_visual_summary` -> Qwen2.5-VL。
- 区域检测：`make_mock_region_chunks` -> PaddleOCR/PP-Structure/LayoutParser/自定义检测器。
- 表格内容：`source_type="table"` 的 `content` 从占位摘要替换为 Markdown 表格。

## 4. Pipeline 接口

代码位置：`src/mllmproject/pipeline.py`

### 构建 Pipeline

```python
pipeline = RagPipeline.from_file(
    source_path="demo.pdf",
    output_dir="data/processed",
    include_visual=True
)
```

功能：

- 解析文档。
- 抽取文本 chunk。
- 渲染页面图。
- 添加页面级视觉 evidence。
- 构建本地向量索引。

### 提问

```python
result, latency_ms = pipeline.answer(
    question="图 3 表示什么趋势？",
    mode="auto",
    top_k=5
)
```

`mode` 取值：

- `text-rag`：只检索 `text`。
- `mm-rag`：检索全部 evidence。
- `auto`：使用规则路由。

## 5. 前端接口

代码位置：`app.py`

前端方向已统一为 Gradio。`app.py` 是唯一展示入口；命令行 baseline 和评测入口保留在 `main.py` 与 `scripts/`。

前端、脚本和评测共用 `src/mllmproject/service.py` 中的 `RagService`。`src/mllmproject/engine.py` 只保留 `RagDemoEngine` 这个前端兼容包装，避免评测层依赖 Gradio 页面状态。

### parse_document

输入：Gradio 上传文件。

输出：

- 解析状态文本。
- 页面预览 Gallery。
- chunk 预览表。
- 文档 metadata JSON。

### ask_question

输入：

- `question`
- `mode`
- `top_k`

输出：

- 答案文本。
- 路由和 citation JSON。
- evidence 表格。
- 引用页面/高亮区域 Gallery。

## 6. 当前限制

- 视觉 evidence 目前是整页级别，真实表格/图表 bbox 尚未接入。
- `MM-RAG` 当前使用页面级 mock visual summary，不是真实 VLM 摘要。
- 前端可展示 bbox 高亮，但 bbox 当前多为整页框。
- 评测脚本已支持单模式和三模式对比，但后续需要把 eval samples 扩展到 30-40 条。
- 当前失败标签是规则判断，适合报告初筛；最终案例仍建议人工复核引用页和 bbox 是否正确。

## 7. 后续开发顺序

1. 保持当前接口不变，替换 BGE-M3 embedding。
2. 保持 `VectorIndex.search` 接口不变，替换 FAISS。
3. 替换 BGE-reranker。
4. 替换 Qwen/Qwen2.5-VL 回答生成。
5. 接入 PaddleOCR/PP-Structure，生成真实 `table/figure` bbox。
