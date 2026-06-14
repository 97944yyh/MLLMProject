# 开发日志

## 2026-06-08：Text-RAG baseline 流程打通

### 本次目标

先不下载 BGE、Qwen、Qwen2.5-VL 等模型，优先完成一个可以运行的文本检索问答 baseline。目标是让团队后续能够在同一套接口上替换真实 embedding、reranker 和 LLM，同时前端 Demo 也能提前开始展示。

### 已完成内容

#### 1. 项目骨架

- 新增 `src/mllmproject/` 作为核心代码目录。
- 将原来的 `main.py` 从 hello world 改成命令行入口。
- 新增 `app.py` 作为简易网页 Demo 入口。
- 新增 `tests/test_text_baseline.py` 做最小流程测试。

#### 2. 统一数据结构

在 `src/mllmproject/schemas.py` 中定义了基础对象：

- `PageText`：保存每页文本。
- `Chunk`：保存文本块，包含 `doc_id`、`page`、`chunk_id`、`source_type`、`content`。
- `Evidence`：保存检索结果，包含分数和来源信息。
- `Citation`：保存回答引用。
- `AnswerResult`：保存最终答案、引用、证据和路由信息。

这些结构后续可以直接扩展到多模态版本，例如给 `Chunk/Evidence` 增加 `bbox` 和 `image_path`。

#### 3. PDF/TXT 文档解析

在 `src/mllmproject/pdf.py` 中实现：

- 支持 PDF、TXT、MD 文件。
- PDF 抽文本优先尝试 `PyMuPDF`。
- 如果没有安装 `PyMuPDF`，自动回退到系统命令 `pdftotext`。
- 当前环境已有 `pdftotext`，所以 baseline 不需要额外下载依赖。

#### 4. 文本切块

在 `src/mllmproject/chunking.py` 中实现：

- 按页处理文本。
- 优先按段落切分。
- 过长段落按固定长度切分。
- 每个 chunk 保留页码和唯一 `chunk_id`，格式类似：

```text
docid_p3_c0012
```

#### 5. Mock embedding 与本地检索

在 `src/mllmproject/embeddings.py` 和 `src/mllmproject/index.py` 中实现：

- 不下载模型，使用确定性的哈希词袋向量作为 mock embedding。
- 支持中英文 token。
- 用余弦相似度做本地 top-k 检索。
- 接口命名保持接近真实向量检索流程，后续可替换为 BGE-M3 + FAISS。
- 支持保存：

```text
data/processed/{doc_id}/chunks.json
data/processed/{doc_id}/index.json
data/processed/{doc_id}/document.json
```

#### 6. Mock 回答生成

在 `src/mllmproject/answer.py` 中实现：

- 不调用 LLM。
- 从 top-k evidence 中选择和问题关键词最相关的句子。
- 强制输出统一引用格式：

```text
答案：...
来源：[page=3, chunk=xxx]
```

这保证前端和评测可以先跑通，后续再替换为真实 Qwen/LLM 生成。

#### 7. Pipeline 串联

在 `src/mllmproject/pipeline.py` 中实现完整 Text-RAG 流程：

```text
文档输入 -> 抽文本 -> chunk -> mock embedding -> 本地索引 -> 检索 -> mock answer
```

提供两个主要接口：

- `TextRAGPipeline.from_document(...)`
- `pipeline.ask(question, top_k=5)`

#### 8. 命令行工具

`main.py` 当前支持：

```bash
python main.py build "多模态大模型大作业说明.pdf"
```

用于解析文档并保存索引。

```bash
python main.py ask "多模态大模型大作业说明.pdf" "期末验收需要提交什么？"
```

用于直接提问。

也支持 JSON 输出：

```bash
python main.py ask "多模态大模型大作业说明.pdf" "期末验收需要提交什么？" --json
```

#### 9. 早期临时前端 Demo（已替换）

早期曾用 Python 标准库 HTTP server 做过一个临时 Text-RAG 页面，用于快速验证上传、索引、问答和 evidence 展示流程。

该临时页面已经被后续 Gradio 前端替换，不再作为团队展示入口。当前唯一前端展示入口是：

```bash
python app.py
```

访问：

```text
http://127.0.0.1:7860
```

### 当前能力

当前 baseline 已经可以完成：

- 解析课程作业说明 PDF。
- 按页/段落生成文本 chunk。
- 建立本地 mock 索引。
- 输入问题并检索相关 chunk。
- 输出带来源引用的答案。
- 通过网页页面完成上传、索引、问答、证据展示。

### 当前限制

- 还没有接入 BGE-M3，所以检索效果只是 baseline 水平。
- 还没有接入 BGE reranker，目前按 mock embedding 分数排序。
- 还没有接入真实 LLM，回答是抽取式 mock answer，不是生成式问答。
- 还没有页面图片渲染、bbox、高亮和多模态 evidence。
- 还没有评测脚本。

### 下一步开发任务

1. 接入页面图片渲染，为 MM-RAG 做准备。
2. 增加规则路由器：`text_route/table_route/vision_route/hybrid_route`。
3. 新增评测集 JSON 格式和 `scripts/run_eval.py`。
4. 安装模型后替换：
   - mock embedding -> BGE-M3
   - mock rerank -> BGE-reranker-v2-m3
   - mock answer -> Qwen/LLM
5. 前端增加模式选择：
   - `Text-RAG`
   - `MM-RAG`
   - `Auto Router`
6. 前端增加引用页面截图和 bbox 高亮。

## 2026-06-08：评测框架与多模态组件补齐

### 本次目标

在不等待大模型下载的情况下，补齐后续 Demo 和报告最需要的组件：规则路由、多模态页面 evidence、评测指标、批量评测脚本和 Gradio 展示链路。

### 已完成内容

#### 1. 多模态 evidence 组件

- 在 `DocumentIngestor` 中增加 PDF 页面渲染能力。
- 每页 PDF 会生成页面图片路径，供前端预览和视觉 evidence 使用。
- 在 `RagDemoEngine._build_index_chunks` 中为每页加入 mock 视觉摘要 chunk。
- 视觉 evidence 当前使用 `source_type="figure"`，后续可替换为真实图表/表格/公式区域。
- 新增 bbox 预览函数 `draw_bbox_preview`，用于在引用页面上高亮区域。

#### 2. 规则路由器

在 `src/mllmproject/router.py` 中实现：

- `Text-RAG`：只检索文本 chunk。
- `MM-RAG`：检索文本、表格、图像、页面等多类型 evidence。
- `Auto Router`：
  - 图、趋势、柱状、折线等关键词 -> `vision_route`
  - 表格、数值、最大、最小等关键词 -> `table_route`
  - 摘要、定义、主要结论等关键词 -> `text_route`
  - 未命中关键词 -> `hybrid_route`

#### 3. 评测指标

新增 `src/mllmproject/metrics.py`，支持：

- `Recall@1`
- `Recall@5`
- `MRR`
- `EM`
- `ANLS`
- `Citation Accuracy`
- 平均响应时间 `latency_ms`

#### 4. 批量评测框架

新增 `src/mllmproject/evaluation.py` 和 `scripts/run_eval.py`。

评测输入 JSON 格式示例：

```json
{
  "sample_id": "course_req_001",
  "question": "期末验收需要提交什么？",
  "answer": "最终报告、上台展示、系统实现细节、代码仓库、定量实验结果",
  "gold_page": 1,
  "gold_type": "text",
  "question_type": "text"
}
```

评测输出：

- `{mode}_summary.json`
- `{mode}_scores.csv`
- `{mode}_details.json`

#### 5. 示例评测集

新增 `data/eval/sample_questions.json`，先放入少量课程作业说明 PDF 的样例问题，后续可扩展到 30-40 条，用于报告中的 Text-RAG vs MM-RAG 对比。

#### 6. 前端 Demo 兼容

当前 `app.py` 使用 `RagDemoEngine`：

- 上传文档。
- 解析并建索引。
- 选择 `Text-RAG`、`MM-RAG`、`Auto Router`。
- 展示答案、路由信息、Top-k evidence、页面预览和引用区域。

### 当前能力

现在项目已经具备：

- Text-RAG baseline。
- 页面级 mock MM-RAG。
- Auto Router。
- Gradio 前端展示链路。
- 评测脚本和指标输出。
- 模型替换接口。

### 后续任务

1. 安装依赖后实际运行 Gradio 前端，截取 Demo 页面。
2. 将 mock embedding 替换为 BGE-M3。
3. 将 mock reranker 替换为 BGE-reranker-v2-m3。
4. 将 mock visual summary 替换为 Qwen2.5-VL。
5. 扩充 `data/eval/sample_questions.json` 到 30-40 条。
6. 根据评测结果整理成功/失败案例。

### 团队分工记录

- 刘天翔：负责总集成、前端 Demo、README 和开发日志维护。
- 杨毅涵：负责 Text-RAG baseline、索引检索、后续 BGE/FAISS 替换。
- 郭翊涛：负责多模态页面渲染、视觉 evidence、路由和评测脚本。

## 2026-06-08：Gradio 前端 Demo 与接口设计补充

### 本次目标

在已有 Text-RAG baseline 基础上，补齐可展示的前端 Demo 和接口设计文档。模型下载暂不作为阻塞项，继续使用 mock embedding、mock reranker、mock generator 和 mock visual summary。

### 已完成内容

#### 1. Gradio 前端 Demo

重写 `app.py` 为 Gradio 三栏式页面：

- 左栏：文档上传、解析状态、文档 metadata、chunk 预览、页面缩略图。
- 中栏：问题输入、模式选择、Top-K 控制、答案输出、路由和引用 JSON。
- 右栏：Top-K evidence 表格、引用页面或区域高亮图。

页面支持三种模式：

- `Text-RAG`
- `MM-RAG`
- `Auto Router`

运行方式：

```bash
python app.py
```

访问：

```text
http://127.0.0.1:7860
```

#### 2. 前端状态管理

新增前端状态封装 `RagDemoEngine`：

- `ingest_document(file_path)`：解析文档并建索引。
- `ask(question, mode, top_k)`：执行检索、路由、rerank 和 mock 回答。
- `make_citation_previews(evidences)`：生成引用页面截图，支持 bbox 高亮。

该封装对前端隐藏底层 pipeline 细节，后续替换真实模型时不需要改页面结构。

#### 3. 兼容统一数据结构

扩展 `src/mllmproject/schemas.py`，同时兼容已有 Text-RAG baseline 和前端多模态 Demo：

- 保留 `PageText`、`EvalPrediction`、`Chunk.to_evidence()` 等 baseline 需要的接口。
- 增加 `Page`、`Document`、`Evidence` 中的 `image_path`、`bbox`、`region_id`、`metadata` 字段。
- 让 `AnswerResult` 同时支持 baseline 和前端路由展示。

#### 4. 接口设计文档

新增 `docs/API_DESIGN.md`，记录：

- `Page`、`Chunk`、`Evidence`、`Citation`、`AnswerResult` 数据结构。
- mock 模型接口和后续真实模型替换点。
- `RagPipeline` 接口。
- 前端事件接口。
- 当前限制和后续开发顺序。

#### 5. README 更新

更新 `README.md`：

- 说明当前有 Text-RAG baseline 和 Gradio 前端 Demo 两条线。
- 补充 Demo 运行方式。
- 补充接口设计文档入口。
- 补充后续 BGE-M3、FAISS、BGE-reranker、Qwen2.5-VL 替换点。

#### 6. 依赖与忽略规则

更新 `pyproject.toml`：

- 增加 Gradio、PyMuPDF、Pillow、NumPy 依赖。
- 增加 `setuptools` build 配置。

更新 `.gitignore`：

- 忽略 Demo 运行产物，如 `data/processed/`、`data/indexes/`、`data/eval/results/`、`outputs/`。

### 当前能力

当前系统已经具备一个可用于期末展示雏形的前端：

1. 上传 PDF 或图片。
2. 点击解析并建索引。
3. 查看页面缩略图和 chunk 预览。
4. 输入问题。
5. 选择 `Text-RAG`、`MM-RAG` 或 `Auto Router`。
6. 查看答案、路由、citation、Top-K evidence。
7. 查看引用页面截图和 bbox 高亮。

### 当前限制

- 当前 `MM-RAG` 仍是页面级 mock visual summary，不是真实 Qwen2.5-VL。
- 当前 bbox 多数是整页级别，还没有接入真实图表/表格检测。
- 当前 Gradio 依赖需要安装后才能启动。
- 当前索引仍是本地 mock 向量索引，尚未接入 FAISS。

### 下一步开发任务

1. 安装依赖并启动 Gradio 页面做截图。
2. 接入真实 BGE-M3 embedding。
3. 将本地索引替换为 FAISS。
4. 接入 BGE-reranker-v2-m3。
5. 接入 Qwen2.5-VL 生成视觉摘要。
6. 补自建评测样本 JSON，跑 Text-RAG vs MM-RAG vs Auto Router。

## 2026-06-08：Text-RAG baseline 收敛为纯文本流程

### 本次目标

先不下载任何模型，完成一个可复现、可被后续 MM-RAG 对比的纯文本 baseline。该 baseline 不做页面渲染、不接 OCR、不生成视觉 evidence，只验证文本 RAG 主流程。

### 已完成内容

- 新增 `src/mllmproject/text_baseline.py`，实现独立的 `TextBaselinePipeline`。
- `TextRAGPipeline` 现在直接指向纯文本 baseline，避免混入多模态页面渲染逻辑。
- baseline 流程固定为：

```text
PDF/TXT/MD -> 文本抽取 -> 按页/段落切 chunk -> 本地哈希 embedding -> 本地余弦检索 -> 词重叠 rerank -> mock 引用式回答
```

- `max_chars` 和 `overlap` 参数现在在 baseline 中真实生效。
- 保存产物统一为：

```text
data/processed/{doc_id}/chunks.json
data/processed/{doc_id}/index.json
data/processed/{doc_id}/metadata.json
```

- `metadata.json` 会记录页数、chunk 数、embedding/index/generator 的 mock 类型。
- 补充 `tests/test_text_baseline.py`，覆盖 TXT 文档端到端 baseline、保存产物和索引加载。

### 已验证命令

```bash
python -m unittest discover -s tests
python main.py build "多模态大模型大作业说明.pdf" --output-dir data\processed_text_baseline_check
python main.py ask "多模态大模型大作业说明.pdf" "期末验收需要提交什么？" --top-k 3 --output-dir data\processed_text_baseline_check
python main.py ask "多模态大模型大作业说明.pdf" "文档理解多模态检索问答系统的最低验收标准是什么？" --top-k 3 --output-dir data\processed_text_baseline_check
python -m compileall src scripts main.py app.py
```

### 当前结论

Text-RAG baseline 已经可以作为后续实验中的 `Text-RAG` 对照组。当前回答仍是 mock 抽取式回答，检索是本地 hash embedding + 词重叠 rerank，后续替换 BGE-M3、FAISS、BGE-reranker 时不需要改变 CLI 使用方式。

## 2026-06-08：前端口径统一

### 本次目标

统一团队对“前端 Demo”的理解，避免 README、接口文档和 `app.py` 实际实现不一致。

### 已完成内容

- 将 `app.py` 统一为 Gradio 三栏式前端，不再使用标准库 HTTP server 作为展示入口。
- 明确 `app.py` 是唯一前端展示入口。
- 保留 `main.py`、`scripts/demo_query.py`、`scripts/run_eval.py` 作为命令行和评测入口。
- README 中将项目入口统一描述为：
  - 前端展示：`python app.py`
  - CLI baseline：`python main.py ask ...`
  - 批量评测：`python scripts/run_eval.py ...`
- API 设计文档中补充：前端方向已统一为 Gradio。

### 当前前端能力

- 上传 PDF / 图片。
- 解析文本 chunk 和页面图。
- 展示页面预览。
- 展示 chunk / visual evidence 预览。
- 支持 `Text-RAG`、`MM-RAG`、`Auto Router`。
- 展示答案、路由原因、citation JSON。
- 展示 Top-K evidence。
- 展示引用页面和 bbox 高亮图。

### 注意事项

- 当前环境如果没有安装 Gradio，运行 `python app.py` 会提示安装依赖。
- 当前 `uv.lock` 尚未同步 `pyproject.toml` 中新增的 Gradio/PyMuPDF/Pillow/NumPy 依赖，正式复现前需要更新 lock。

## 2026-06-08：Text-RAG baseline 接口修正与纯文本模式加固

### 本次目标

在不下载任何模型、不改动 Gradio 前端口径的前提下，继续加固 Text-RAG baseline，使它可以稳定作为后续 Text-RAG 对照组使用。

### 已完成内容

- 修复 `Chunk.from_dict` 缺失问题：索引 JSON 保存后可以重新加载并继续检索。
- 修复误放在 `Page` 上的反序列化逻辑，补回 `PageText.from_dict`。
- 为 `RagPipeline.from_file` 增加 `render_pages` 开关：
  - 多模态 Demo 默认仍然可以渲染页面图。
  - 纯文本 baseline 可以显式关闭页面渲染，避免产生不必要的图片文件。
- 为通用 `load_document` / `extract_pages` 增加 TXT/MD 支持，便于快速构造小样例测试 baseline。
- `TextBaselinePipeline.save()` 现在同时保存：
  - `chunks.json`
  - `index.json`
  - `metadata.json`
  - `document.json`
- `main.py build` 输出新增 `Document JSON` 路径，便于团队成员确认落盘产物。
- 补充单元测试：
  - TXT 文档的 Text-RAG pipeline。
  - 保存索引后重新加载检索。
  - 通用 `RagPipeline` 的纯文本模式。

### 当前结论

Text-RAG baseline 当前主流程为：

```text
PDF/TXT/MD -> 文本抽取 -> chunk -> hash embedding -> 本地向量检索 -> mock answer -> citation
```

该流程不需要下载 BGE/Qwen 模型，可以先用于前端联调、评测脚本联调和报告中的 Text-RAG baseline 说明。后续替换真实模型时，优先替换 embedding、reranker 和 generator 接口，不需要改前端结构。

## 2026-06-08：评测框架和多模态组件工程化

### 本次目标

在前端口径已经统一为 Gradio 后，继续补齐后续报告和 Demo 需要的工程组件：三模式评测对比、失败案例初筛、多模态 evidence 组件层，以及对应测试。

### 已完成内容

#### 1. 新增多模态组件层

新增 `src/mllmproject/multimodal.py`，集中管理多模态相关结构和工具：

- `VisualRegion`：表示未来真实图表、表格、公式区域。
- `EvidencePreview`：表示前端 gallery 可直接展示的引用预览。
- `make_page_visual_chunks`：把每页渲染图片转成页面级 visual evidence。
- `make_mock_region_chunks`：生成占位 figure/table bbox，用于后续联调真实 layout detector。
- `draw_evidence_preview`：根据 evidence 的 `image_path` 和 `bbox` 生成高亮截图。
- `clamp_bbox` / `format_evidence_caption`：处理 bbox 边界和前端 caption。

#### 2. 接入现有 ingest 和前端 engine

- `ingest.add_page_visual_evidence` 改为调用 `make_page_visual_chunks`。
- `engine.RagDemoEngine.make_citation_previews` 改为调用 `draw_evidence_preview`。
- 保留 `ingest.draw_bbox_preview` 的导入兼容，避免其他组员已有引用失效。
- 去掉 `engine.py` 顶层 Pillow 导入，降低无前端/无图像环境下的导入风险。

#### 3. 增强评测框架

在 `src/mllmproject/evaluation.py` 中新增：

- `run_comparison`：一次运行 `Text-RAG`、`MM-RAG`、`Auto Router` 对比。
- `load_eval_samples`：校验评测集 JSON。
- `enrich_score_row`：为每条样本增加问题类型、gold 类型、top1 page、引用页等字段。
- `label_failure`：自动标注失败类型：
  - `retrieval_miss`
  - `citation_miss`
  - `rerank_miss`
  - `answer_mismatch`
  - `ok`
- `aggregate_by` / `count_by`：按 route、question_type 和 failure_label 做分组统计。

#### 4. 更新评测 CLI

`scripts/run_eval.py` 新增：

```bash
python scripts/run_eval.py --doc "多模态大模型大作业说明.pdf" --samples data/eval/sample_questions.json --mode all
```

会生成：

```text
data/eval/results/comparison_summary.csv
data/eval/results/comparison_summary.json
```

单模式评测仍然保留：

```bash
--mode text-rag
--mode mm-rag
--mode auto
```

#### 5. 补充测试

新增测试文件：

- `tests/test_multimodal_components.py`
- `tests/test_evaluation_framework.py`

覆盖内容：

- 页面级 visual chunk 的 `bbox/image_path/region_id`。
- mock figure/table region 的结构。
- bbox clamp 和 evidence caption。
- 单模式评测输出文件。
- 多模式 comparison summary 输出。
- failure label 优先级。

#### 6. 更新文档

- README 增加 `--mode all`、comparison 输出、失败标签和多模态组件说明。
- `docs/API_DESIGN.md` 增加 `multimodal.py` 组件设计和后续替换点。

### 已验证命令

```bash
python -m unittest discover -s tests
python -m compileall src scripts main.py app.py
```

### 当前结论

项目现在不下载模型也可以完成：

```text
文档解析 -> Text-RAG baseline -> MM-RAG mock evidence -> Auto Router -> 批量评测 -> 三模式对比表 -> 前端引用高亮
```

评测框架已经能为报告提供初版指标表和失败案例初筛。多模态组件层也已经把页面图、bbox、高亮预览和 visual evidence 的接口固定下来，后续接真实 Qwen2.5-VL、表格检测、图表检测时可以按模块替换。
