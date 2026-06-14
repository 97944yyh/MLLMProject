# MLLM Demo 前后端接口交付文档

本文档面向后端开发人员，目标是让后端可以按照当前 `frontend/src/App.tsx` 中已经完成的 React Demo 对齐接口、数据结构和业务状态。

当前前端是 mock 数据驱动，不要求后端完全照搬 mock 文案，但后端返回的数据必须满足本文档定义的字段、状态和交互语义。前端不需要改版，后端只需要把 mock 数据替换为真实接口输出。

## 1. 项目定位

### 1.1 前端 Demo 要做什么

该前端是一个“多模态证据知识库问答 Demo”，核心流程如下：

1. 用户上传 PDF 或图片证据文件。
2. 后端解析文件，生成页面预览图、文本 chunk、图表/table/visual evidence。
3. 用户在左侧知识库列表中浏览和选择 evidence chunk。
4. 用户在右侧预览面板查看当前文件、当前页和当前选中 evidence 的高亮内容。
5. 用户在底部问题输入器中选择模型并提问。
6. 后端基于上传文件和用户选择的 evidence 生成带引用的回答。
7. 前端展示答案、模型、命中的 evidence 和引用来源。

### 1.2 后端需要提供什么

后端需要提供以下能力：

- 文件上传和文件列表管理。
- 文件解析任务和解析状态查询。
- 文件页图预览。
- 知识库 chunk 列表。
- evidence chunk 选择状态同步，可选。
- 模型列表。
- 问答接口。
- 问答引用 evidence 和高亮预览图。
- 统一错误返回。

建议接口基础路径：

```text
/api/v1
```

所有 JSON 接口均使用：

```http
Content-Type: application/json; charset=utf-8
```

上传接口使用：

```http
Content-Type: multipart/form-data
```

图片预览接口直接返回 `image/png`、`image/jpeg` 或 `image/webp`。

## 2. 当前前端组件总览

当前所有组件都在 `frontend/src/App.tsx`。虽然尚未拆分文件，但后端交付时必须覆盖每个组件的数据需求。

| 组件 | UI 作用 | 后端数据需求 |
| --- | --- | --- |
| `App` | 全局状态容器，控制欢迎页、知识库页、结果页、预览页和底部输入器 | 文件列表、当前文件、chunk 列表、当前选中 chunk、问答结果 |
| `Header` | 顶部栏，显示应用名、当前视图、返回按钮、分享按钮、主题按钮 | 当前是否已上传、当前视图；分享和主题当前可先不接后端 |
| `WelcomePanel` | 首屏欢迎页，上传文件或加载样例 | 上传接口；样例文件接口可选 |
| `UploadButton` | 文件上传控件 | 支持多文件上传，文件类型限制 |
| `KnowledgePage` | 左侧知识库 chunk 列表页 | 当前文件的解析状态、总 chunk 数、页数、visual region 数、分页 chunk 数据 |
| `ChunkRow` | 单个 evidence chunk 条目 | chunk id、类型、页码、标题、内容、分数、是否选中 |
| `PreviewPanel` | 右侧文件预览和文件切换 | 文件列表、当前页图、当前 evidence 高亮、当前文件名 |
| `ResultPage` | 问答结果页 | 问题、回答、模型、引用 evidence、分数、内容 |
| `Composer` | 底部问题输入器、模型选择器、提交按钮 | 模型列表、提问接口、提交中的 loading 状态 |
| `ProjectLogoMark` | 前端纯展示 Logo | 不需要后端 |
| `InfoCard` | 欢迎页信息卡片 | 不需要后端 |

## 3. 按组件说明视觉展示效果和数据展示方式

本节是后端对齐时最重要的部分。重点是说明每个组件在界面上要呈现什么效果、每个位置需要展示什么数据，以及后端应该返回哪些字段。

### 3.1 `App`：整体页面布局和视图切换

视觉效果：

- 整体是一个左右两栏工作台。
- 顶部固定显示标题栏。
- 左侧是主工作区：未上传时显示欢迎页，上传后显示知识库，提问后显示问答结果。
- 右侧是预览区：始终显示文件预览、文件 tab 和当前 evidence 信息。
- 底部悬浮一个问题输入器，展开时是横向输入栏，收起时是圆形悬浮入口。

数据展示方式：

| 前端区域 | 展示内容 | 后端数据 |
| --- | --- | --- |
| 顶部标题栏 | 当前页面状态：`Knowledge Base` 或 `Query Result` | 当前视图由前端控制，后端不需要返回 |
| 左侧主区 | 欢迎页、chunk 列表或问答结果 | 文件状态、chunks、answer |
| 右侧预览区 | 文件名、页码、页图、当前 evidence | `FileAsset`、`EvidenceChunk`、页面图片 |
| 底部输入器 | 问题、模型、提交状态 | `ModelOption[]`、`AnswerResult` |

核心后端字段：

```ts
files: FileAsset[];
chunks: EvidenceChunk[];
models: ModelOption[];
answerResult: AnswerResult;
```

### 3.2 `Header`：顶部状态栏

视觉效果：

- 左侧显示返回按钮和项目名 `MLLM Demo`。
- 文件上传后，在项目名右侧显示一个胶囊状态标签：
  - 知识库页显示 `Knowledge Base`
  - 结果页显示 `Query Result`
- 右侧显示说明文字 `Evidence knowledge base`、`Share` 按钮和主题按钮。
- 未上传文件时不显示返回按钮和状态标签。

数据展示方式：

| UI 元素 | 展示内容 | 后端数据 |
| --- | --- | --- |
| 项目名 | 固定 `MLLM Demo` | 不需要 |
| 返回按钮 | 文件上传后显示 | 前端根据是否有文件判断 |
| 状态标签 | `Knowledge Base` / `Query Result` | 前端根据当前视图判断 |
| Share 按钮 | 仅视觉占位 | 当前不需要 |
| 主题按钮 | 仅视觉占位 | 当前不需要 |

### 3.3 `WelcomePanel`：首屏欢迎卡片

视觉效果：

- 左侧主区域显示一个白色卡片，顶部有一条彩色渐变细条。
- 卡片内先显示蓝色胶囊标签 `Evidence Workspace`。
- 主标题显示 `Multimodal Evidence Demo`。
- 下方是一段说明文字，说明可以上传报告、PDF、截图和图表。
- 中间有两个按钮：
  - 蓝色主按钮 `Upload evidence`
  - 白色描边按钮 `Use sample files`
- 下方有三个步骤卡片：
  - `1 Upload files`
  - `2 Preview evidence`
  - `3 Ask questions`
- 底部有两个说明卡片：
  - `Demo flow`
  - `Backend handoff`

数据展示方式：

| UI 元素 | 展示内容 | 后端数据 |
| --- | --- | --- |
| 上传按钮 | 用户选择文件 | `POST /api/v1/files` 返回文件列表 |
| 样例按钮 | 加载样例文件 | 可选 `POST /api/v1/demo/sample-session` |
| 步骤卡片 | 固定文案 | 不需要 |
| 底部说明卡片 | 固定文案 | 不需要 |

后端需要返回的最小数据：

```json
{
  "files": [
    {
      "file_id": "file_001",
      "file_name": "IDC_REIT_evidence.pdf",
      "status": "uploaded"
    }
  ]
}
```

### 3.4 `UploadButton`：上传按钮

视觉效果：

- 有两种样式：
  - `primary`：蓝底白字，用于欢迎页主上传按钮。
  - `plain`：白底描边，用于右侧预览区的 `Add file`。
- 按钮左侧有上传图标，右侧显示按钮文字。
- 文件选择器隐藏，点击按钮区域触发文件选择。

数据展示方式：

| 行为 | 后端数据 |
| --- | --- |
| 用户选择一个文件 | 返回一个 `FileAsset` |
| 用户选择多个文件 | 返回多个 `FileAsset` |
| 继续添加文件 | 新文件追加到已有文件列表 |

文件类型：

```text
.pdf, .png, .jpg, .jpeg, .webp
```

后端必须保证：

- 支持多文件上传。
- 文件名只用于展示，不作为唯一 ID。
- 每个文件都有稳定 `file_id`。

### 3.5 `KnowledgePage`：知识库 evidence 列表

视觉效果：

- 左侧主工作区显示一个白色面板。
- 面板顶部左侧显示标题 `Indexed evidence` 和说明文字。
- 面板顶部右侧显示三组胶囊信息：
  - 绿色 `Parsed`
  - 灰色 `{n} selected`
  - 蓝色当前文件名
- 中间是可滚动的 evidence chunk 列表。
- 底部显示统计文字和分页大小：
  - `Total 128 chunks / 36 pages / 42 visual regions`
  - `10 / page`

数据展示方式：

| UI 位置 | 展示内容 | 后端字段 |
| --- | --- | --- |
| 绿色状态胶囊 | `Parsed` | `file.status = "ready"` |
| 已选数量胶囊 | `2 selected` | 前端根据选中 chunk 数计算 |
| 文件名胶囊 | 当前文件名 | `file.file_name` |
| 底部统计 | chunk 总数 | `chunk_count` 或 chunks 响应 `total` |
| 底部统计 | 页数 | `page_count` |
| 底部统计 | visual 区域数 | `visual_region_count` |
| 列表主体 | evidence rows | `EvidenceChunk[]` |

推荐 chunks 响应：

```json
{
  "file_id": "file_001",
  "file_name": "IDC_REIT_evidence.pdf",
  "total": 128,
  "page_count": 36,
  "visual_region_count": 42,
  "chunks": []
}
```

### 3.6 `ChunkRow`：单条 evidence 行

视觉效果：

- 每条 evidence 是一整行可点击区域。
- 左侧是一个方形 checkbox：
  - 选中时蓝底白色勾。
  - 未选中时白底灰边。
- 中间是 evidence 信息：
  - 第一行显示类型标签、页码、chunk id。
  - 第二行显示标题。
  - 第三行显示内容摘要，最多两行。
- 右侧显示相关性分数，保留三位小数。
- 选中行背景为浅蓝色。
- hover 或 focused 行背景为浅灰色。

数据展示方式：

| UI 位置 | 示例 | 后端字段 |
| --- | --- | --- |
| 类型标签 | `FIGURE` / `TABLE` / `TEXT` / `VISUAL` | `source_type` |
| 页码 | `Page 3` | `page` |
| chunk id | `chunk_001` | `chunk_id` |
| 标题 | `Figure 2 - Hyperscale IDC growth` | `title` |
| 内容摘要 | `Growth trend and country share...` | `content` |
| 分数 | `0.941` | `score` |
| checkbox 状态 | 选中或未选中 | 前端根据 `selected_chunk_ids` 判断 |

后端返回示例：

```json
{
  "chunk_id": "chunk_001",
  "source_type": "figure",
  "page": 3,
  "score": 0.941,
  "title": "Figure 2 - Hyperscale IDC growth",
  "content": "Growth trend and country share of worldwide hyperscale IDCs.",
  "enabled": true
}
```

### 3.7 `PreviewPanel`：右侧文件和页面预览

视觉效果：

- 右侧是一个固定高度的白色预览面板。
- 顶部显示标题 `Preview`。
- 标题下方显示当前文件名；未上传时显示 `Upload files to preview evidence`。
- 右上角有 `Add file` 上传按钮。
- 上传文件后，面板顶部下方显示一排横向文件 tab。
- 当前文件 tab 使用蓝色浅底和蓝色文字。
- 主体区域显示一个白色页面预览卡片：
  - 顶部左侧显示文件名。
  - 顶部右侧显示 `Page {page}`。
  - 中间显示页面图或页面 skeleton。
  - evidence 区域用浅蓝色卡片高亮，显示标题和内容。
- 未上传时，面板中间显示空状态：
  - 图标
  - `No preview yet`
  - 上传提示
  - 上传按钮

数据展示方式：

| UI 位置 | 展示内容 | 后端字段或接口 |
| --- | --- | --- |
| 当前文件名 | `IDC_REIT_evidence.pdf` | `file.file_name` |
| 文件 tab | 所有上传文件名 | `files[].file_name` |
| 当前页码 | `Page 3` | `selectedEvidence.page` |
| 页面图 | 当前页图片 | `GET /files/{file_id}/pages/{page}/image` |
| 高亮图 | 当前 evidence 高亮页图 | `GET /evidence/{evidence_id}/preview` |
| evidence 标题 | `Figure 2 - ...` | `selectedEvidence.title` |
| evidence 内容 | evidence 摘要 | `selectedEvidence.content` |

后端注意：

- 页面图片 URL 必须能被浏览器直接访问。
- 如果返回 `bbox`，高亮图应按同一张页图的像素坐标绘制。
- 如果暂时没有高亮能力，可以只返回整页图片。

### 3.8 `Composer`：底部悬浮提问框

视觉效果：

- 展开时是固定在底部中间的半透明白色输入框。
- 第一行是问题输入区：
  - 未上传时 placeholder 为 `Upload evidence before asking`，输入禁用。
  - 上传后 placeholder 为 `Ask a follow-up question`。
- 第二行左侧是模型选择按钮：
  - 显示图标、`Model` 文案、当前模型名和下拉箭头。
  - 点击后向上弹出模型菜单。
  - 当前模型行有浅蓝底和勾选图标。
- 第二行右侧是圆形提交按钮：
  - 未提交时显示右箭头。
  - 提交中显示 loading spinner。
  - 未上传或正在提交时禁用。
- 收起时是可拖动的圆形悬浮按钮，中间显示项目 logo。

数据展示方式：

| UI 位置 | 展示内容 | 后端字段 |
| --- | --- | --- |
| 模型按钮 | 当前模型名 | `ModelOption.label` |
| 模型菜单 | 可用模型列表 | `models[]` |
| 当前模型选中态 | 勾选图标 | `model.id === selectedModelId` |
| 输入框 | 用户问题 | 提交为 `question` |
| 提交按钮 loading | 查询中状态 | 前端根据请求状态控制 |

模型数据示例：

```json
{
  "id": "qwen2_5_vl",
  "label": "Qwen2.5-VL",
  "enabled": true,
  "is_default": true
}
```

### 3.9 `ResultPage`：问答结果页

视觉效果：

- 左上角显示 `Back to knowledge base` 返回按钮。
- 右上角显示 `Reset demo` 按钮。
- 主标题显示用户刚才输入的问题。
- 标题下方显示两组胶囊：
  - 蓝色模型胶囊，例如 `Qwen2.5-VL`
  - 灰色 evidence 数量胶囊，例如 `2 selected chunks`
- 下方白色文章面板显示回答正文。
- 回答正文下方显示 `Referenced evidence` 区域。
- 每个引用 evidence 是一个浅灰卡片：
  - 左侧显示 evidence 标题。
  - 右侧显示 score。
  - 下方显示 evidence 内容。

数据展示方式：

| UI 位置 | 展示内容 | 后端字段 |
| --- | --- | --- |
| 页面标题 | 用户问题 | `question` |
| 模型胶囊 | 模型名 | `model_label` |
| evidence 数量 | `2 selected chunks` | `evidences.length` 或 `selected_chunk_ids.length` |
| 回答正文 | 自然语言答案 | `answer` |
| 引用标题 | evidence 标题 | `evidences[].title` |
| 引用分数 | `0.913` | `evidences[].score` |
| 引用内容 | evidence 摘要 | `evidences[].content` |

问答结果示例：

```json
{
  "question": "What does Figure 3 show?",
  "answer": "Based on the retrieved evidence...",
  "model_label": "Qwen2.5-VL",
  "selected_chunk_ids": ["chunk_001", "chunk_002"],
  "evidences": [
    {
      "chunk_id": "chunk_002",
      "title": "Figure 3 - EQIX assets and equity",
      "content": "Shareholders' equity and total assets rose from 2015 to 2019.",
      "score": 0.913
    }
  ]
}
```

### 3.10 `InfoCard`：欢迎页底部说明卡片

视觉效果：

- 欢迎页底部有两个小卡片。
- 卡片是白色半透明背景、细边框、轻微阴影。
- 每个卡片显示一个短标题和一行说明文字。

数据展示方式：

- 当前是固定文案。
- 后端不需要返回数据。

### 3.11 `ProjectLogoMark`：圆形项目 Logo

视觉效果：

- 圆形白色半透明底。
- 内部有三根竖条和两个小圆点。
- 用于 Composer 收起后的悬浮按钮。

数据展示方式：

- 纯前端视觉元素。
- 后端不需要返回数据。

## 4. 前端状态流转

### 4.1 初始状态

前端状态：

```ts
hasUploaded = false
view = "knowledge"
attachments = []
activeFile = ""
query = ""
```

页面表现：

- 左侧显示 `WelcomePanel`。
- 右侧 `PreviewPanel` 显示空预览。
- 底部 `Composer` 禁止提问，placeholder 为 `Upload evidence before asking`。

后端要求：

- 此时不需要主动请求数据。
- 如果接入登录态或历史会话，可以额外调用会话恢复接口，但当前 Demo 不强制。

### 4.2 上传文件后

前端状态：

```ts
hasUploaded = true
attachments = ["文件名1", "文件名2"]
activeFile = attachments[0]
view = "knowledge"
```

页面表现：

- 左侧切换为 `KnowledgePage`。
- 右侧显示文件 tab 和当前文件预览。
- 底部输入器允许输入问题。

后端要求：

- 接收一个或多个文件。
- 为每个文件生成稳定 `file_id`。
- 启动解析任务，或上传后自动进入解析。
- 返回文件元信息和解析状态。
- 解析完成后可以返回 chunk 列表和页面预览图 URL。

### 4.3 浏览知识库

前端状态：

```ts
selectedIds = ["chunk_001"]
focusedId = "chunk_001"
```

页面表现：

- 左侧 chunk 列表显示类型、页码、chunk id、标题、内容摘要、score。
- 点击 chunk 后选中或取消选中。
- 当前 focused chunk 会同步到右侧预览。

后端要求：

- `/files/{file_id}/chunks` 必须返回分页列表。
- chunk 的 `chunk_id` 必须稳定。
- chunk 的 `page` 必须能映射到预览图接口。
- 如果 chunk 有 `bbox`，右侧预览可以进一步显示局部高亮。

### 4.4 提问并查看结果

前端状态：

```ts
view = "result"
query = "用户问题"
model = "Qwen2.5-VL"
selectedIds = ["chunk_001", "chunk_002"]
```

页面表现：

- 左侧切换为 `ResultPage`。
- 顶部显示用户问题。
- 显示模型 badge。
- 显示 selected chunks 数量。
- answer 正文下方列出引用 evidence。
- 右侧预览仍保留当前文件和当前 evidence。

后端要求：

- 问答接口需要接收用户问题、文件范围、模型、可选 selected chunk ids。
- 返回自然语言回答。
- 返回引用 evidence 列表。
- 返回 citations，供后续高亮引用页或生成报告使用。
- 返回 route 和 route_reason，方便展示系统选择了 text/table/vision/hybrid 路由。

### 4.5 重置 Demo

前端行为：

- 清空上传文件。
- 清空问题。
- 恢复默认选中的 chunk。
- 回到欢迎页。

后端要求：

- 可选提供会话清空接口。
- 如果不做会话管理，前端本地清空即可。

## 5. 核心数据结构

### 5.1 `FileAsset`

表示一个上传文件。

```ts
type FileAsset = {
  file_id: string;
  file_name: string;
  original_name: string;
  mime_type: string;
  size_bytes: number;
  status: "uploaded" | "queued" | "parsing" | "ready" | "failed";
  page_count: number | null;
  chunk_count: number | null;
  visual_region_count: number | null;
  created_at: string;
  updated_at: string;
  error_message?: string | null;
};
```

字段说明：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `file_id` | 是 | 后端生成的稳定文件 ID，例如 `file_001` |
| `file_name` | 是 | 展示在前端 tab 上的文件名 |
| `original_name` | 是 | 用户上传时的原始文件名 |
| `mime_type` | 是 | MIME 类型，例如 `application/pdf`、`image/png` |
| `size_bytes` | 是 | 文件大小 |
| `status` | 是 | 文件处理状态 |
| `page_count` | 否 | PDF 页数；图片可为 1 |
| `chunk_count` | 否 | 解析出的 chunk 总数 |
| `visual_region_count` | 否 | 图表、表格、整页视觉 evidence 数量 |
| `created_at` | 是 | ISO 8601 时间 |
| `updated_at` | 是 | ISO 8601 时间 |
| `error_message` | 否 | 解析失败时给用户看的错误说明 |

### 5.2 `EvidenceChunk`

对应前端 `ChunkRow` 和 `KnowledgePage` 的核心数据。

```ts
type EvidenceType = "text" | "figure" | "table" | "visual";

type EvidenceChunk = {
  chunk_id: string;
  evidence_id: string;
  file_id: string;
  file_name: string;
  page: number;
  source_type: EvidenceType;
  title: string;
  content: string;
  score: number;
  bbox: [number, number, number, number] | null;
  region_id: string | null;
  image_url: string | null;
  preview_url: string | null;
  enabled: boolean;
  metadata: Record<string, unknown>;
};
```

字段说明：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `chunk_id` | 是 | chunk 稳定 ID，用于选择和提交 |
| `evidence_id` | 是 | evidence 稳定 ID；可以与 `chunk_id` 相同 |
| `file_id` | 是 | 所属文件 ID |
| `file_name` | 是 | 所属文件名，便于前端兜底展示 |
| `page` | 是 | 1-based 页码 |
| `source_type` | 是 | `text` 文本、`figure` 图、`table` 表格、`visual` 页面视觉摘要 |
| `title` | 是 | chunk 标题；没有标题时后端需生成短标题 |
| `content` | 是 | chunk 摘要或正文，前端会展示两行摘要 |
| `score` | 是 | 检索或排序分数，范围建议 0-1 |
| `bbox` | 否 | 页面坐标 `[x1, y1, x2, y2]`，基于原始页图像素坐标 |
| `region_id` | 否 | 图表/table 区域 ID |
| `image_url` | 否 | 所在页图片 URL |
| `preview_url` | 否 | evidence 高亮预览图 URL |
| `enabled` | 是 | 是否参与检索 |
| `metadata` | 是 | 扩展信息，例如 OCR confidence、section、tokens |

注意：

- 前端当前 mock 类型叫 `type`，后端建议统一使用 `source_type`。
- 接入时前端可做字段映射：`source_type -> type`。
- `score` 即使不是查询结果，也可以返回后端构建阶段的默认 relevance 或 confidence，前端会显示三位小数。

### 5.3 `Citation`

表示答案引用来源。

```ts
type Citation = {
  citation_id: string;
  evidence_id: string;
  chunk_id: string | null;
  file_id: string;
  file_name: string;
  page: number;
  source_type: EvidenceType;
  bbox: [number, number, number, number] | null;
  quote: string | null;
  preview_url: string | null;
};
```

### 5.4 `ModelOption`

对应 `Composer` 中的模型下拉菜单。

```ts
type ModelOption = {
  id: string;
  label: string;
  provider: "local" | "openai" | "anthropic" | "mock" | string;
  description: string;
  enabled: boolean;
  is_default: boolean;
  supports_vision: boolean;
  supports_text: boolean;
};
```

前端当前展示的模型：

```text
Qwen2.5-VL
GPT-4.1
Claude 3.7
Local Mock
```

建议后端返回：

```json
{
  "models": [
    {
      "id": "qwen2_5_vl",
      "label": "Qwen2.5-VL",
      "provider": "local",
      "description": "默认多模态问答模型",
      "enabled": true,
      "is_default": true,
      "supports_vision": true,
      "supports_text": true
    },
    {
      "id": "local_mock",
      "label": "Local Mock",
      "provider": "mock",
      "description": "本地 mock 回答，用于无模型环境联调",
      "enabled": true,
      "is_default": false,
      "supports_vision": false,
      "supports_text": true
    }
  ]
}
```

### 5.5 `AnswerResult`

对应 `ResultPage`。

```ts
type AnswerResult = {
  answer_id: string;
  question: string;
  answer: string;
  model: string;
  model_label: string;
  route: "text_route" | "table_route" | "vision_route" | "hybrid_route";
  route_reason: string;
  citations: Citation[];
  evidences: EvidenceChunk[];
  selected_chunk_ids: string[];
  latency_ms: number;
  created_at: string;
};
```

## 6. 接口清单

### 6.1 上传文件

```http
POST /api/v1/files
Content-Type: multipart/form-data
```

表单字段：

```text
files: File[]
```

前端允许的文件类型：

```text
.pdf, .png, .jpg, .jpeg, .webp
```

建议后端也支持：

```text
.bmp
```

请求说明：

- 支持一次上传多个文件。
- 文件名可能重复，后端必须用 `file_id` 区分。
- 上传成功后可以自动创建解析任务，也可以只返回 `uploaded` 状态并由前端调用解析接口。

推荐响应：

```json
{
  "files": [
    {
      "file_id": "file_001",
      "file_name": "IDC_REIT_evidence.pdf",
      "original_name": "IDC_REIT_evidence.pdf",
      "mime_type": "application/pdf",
      "size_bytes": 482190,
      "status": "uploaded",
      "page_count": null,
      "chunk_count": null,
      "visual_region_count": null,
      "created_at": "2026-06-11T10:00:00+08:00",
      "updated_at": "2026-06-11T10:00:00+08:00",
      "error_message": null
    }
  ]
}
```

### 6.2 启动解析

```http
POST /api/v1/files/{file_id}/parse
```

请求：

```json
{
  "include_visual": true,
  "include_region_detection": true,
  "include_table_extraction": true,
  "chunking": {
    "max_chars": 900,
    "overlap": 80
  }
}
```

响应：

```json
{
  "job_id": "job_001",
  "file_id": "file_001",
  "status": "queued",
  "message": "Parse job created."
}
```

后端处理内容：

- PDF 文本抽取。
- PDF 页面渲染成图片。
- 图片文件作为单页文档处理。
- 文本 chunk 切分。
- 整页 visual summary。
- 图表/table bbox 检测，可先 mock，但字段必须保留。
- 构建检索索引。

### 6.3 查询解析任务状态

```http
GET /api/v1/jobs/{job_id}
```

响应：

```json
{
  "job_id": "job_001",
  "file_id": "file_001",
  "status": "ready",
  "progress": 1.0,
  "stage": "indexing",
  "message": "Parsed 36 pages and 128 chunks.",
  "result": {
    "page_count": 36,
    "chunk_count": 128,
    "visual_region_count": 42
  },
  "error": null
}
```

状态枚举：

```text
queued
parsing
rendering_pages
extracting_regions
indexing
ready
failed
```

### 6.4 获取文件列表

```http
GET /api/v1/files
```

响应：

```json
{
  "files": [
    {
      "file_id": "file_001",
      "file_name": "IDC_REIT_evidence.pdf",
      "original_name": "IDC_REIT_evidence.pdf",
      "mime_type": "application/pdf",
      "size_bytes": 482190,
      "status": "ready",
      "page_count": 36,
      "chunk_count": 128,
      "visual_region_count": 42,
      "created_at": "2026-06-11T10:00:00+08:00",
      "updated_at": "2026-06-11T10:00:08+08:00",
      "error_message": null
    }
  ]
}
```

前端用途：

- `PreviewPanel` 的文件 tab。
- `Header` 和 `KnowledgePage` 的当前文件信息。
- 问答时传入 `file_ids`。

### 6.5 获取单个文件详情

```http
GET /api/v1/files/{file_id}
```

响应：

```json
{
  "file": {
    "file_id": "file_001",
    "file_name": "IDC_REIT_evidence.pdf",
    "original_name": "IDC_REIT_evidence.pdf",
    "mime_type": "application/pdf",
    "size_bytes": 482190,
    "status": "ready",
    "page_count": 36,
    "chunk_count": 128,
    "visual_region_count": 42,
    "created_at": "2026-06-11T10:00:00+08:00",
    "updated_at": "2026-06-11T10:00:08+08:00",
    "error_message": null
  }
}
```

### 6.6 获取知识库 chunks

```http
GET /api/v1/files/{file_id}/chunks?page=1&page_size=10
```

可选查询参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `page` | number | 分页页码，1-based |
| `page_size` | number | 每页数量，当前 UI 文案为 `10 / page` |
| `source_type` | string | 可按 `text/figure/table/visual` 过滤 |
| `enabled` | boolean | 可只看启用或禁用 chunk |
| `q` | string | 可选关键词搜索 |

响应：

```json
{
  "file_id": "file_001",
  "file_name": "IDC_REIT_evidence.pdf",
  "total": 128,
  "page": 1,
  "page_size": 10,
  "page_count": 36,
  "visual_region_count": 42,
  "chunks": [
    {
      "chunk_id": "chunk_001",
      "evidence_id": "chunk_001",
      "file_id": "file_001",
      "file_name": "IDC_REIT_evidence.pdf",
      "page": 3,
      "source_type": "figure",
      "title": "Figure 2 - Hyperscale IDC growth",
      "content": "Growth trend and country share of worldwide hyperscale IDCs.",
      "score": 0.941,
      "bbox": [84, 112, 518, 296],
      "region_id": "region_003_001",
      "image_url": "/api/v1/files/file_001/pages/3/image",
      "preview_url": "/api/v1/evidence/chunk_001/preview",
      "enabled": true,
      "metadata": {
        "section": "Market analysis",
        "tokens": 43
      }
    }
  ]
}
```

前端对应：

- `KnowledgePage` 的 `Total 128 chunks / 36 pages / 42 visual regions`。
- `ChunkRow` 的 type、page、id、title、content、score。
- `PreviewPanel` 根据当前 selected chunk 的 page、title、content 展示预览。

### 6.7 更新 chunk 是否参与检索

当前前端点击 chunk 是本地选择，不一定需要后端保存。如果后端希望支持持久化启用/禁用，可提供此接口。

```http
PATCH /api/v1/chunks/{chunk_id}
```

请求：

```json
{
  "enabled": true
}
```

响应：

```json
{
  "chunk_id": "chunk_001",
  "enabled": true
}
```

### 6.8 获取页面图片

```http
GET /api/v1/files/{file_id}/pages/{page}/image
```

响应：

```http
200 OK
Content-Type: image/png
```

要求：

- `page` 使用 1-based 页码。
- PDF 页图建议统一渲染为 PNG。
- 图片原文件可直接返回处理后的预览图。
- 若文件未解析完成，返回 `409 Conflict`。

### 6.9 获取 evidence 高亮预览图

```http
GET /api/v1/evidence/{evidence_id}/preview
```

响应：

```http
200 OK
Content-Type: image/png
```

要求：

- 如果 evidence 有 `bbox`，返回带高亮框或半透明覆盖层的页图。
- 如果 evidence 没有 `bbox`，返回整页图即可。
- 如果预览生成失败，返回统一 JSON 错误，不要返回空图片。

### 6.10 获取模型列表

```http
GET /api/v1/models
```

响应：

```json
{
  "models": [
    {
      "id": "qwen2_5_vl",
      "label": "Qwen2.5-VL",
      "provider": "local",
      "description": "默认多模态问答模型",
      "enabled": true,
      "is_default": true,
      "supports_vision": true,
      "supports_text": true
    },
    {
      "id": "gpt_4_1",
      "label": "GPT-4.1",
      "provider": "openai",
      "description": "文本与多模态问答模型",
      "enabled": true,
      "is_default": false,
      "supports_vision": true,
      "supports_text": true
    },
    {
      "id": "claude_3_7",
      "label": "Claude 3.7",
      "provider": "anthropic",
      "description": "外部模型选项",
      "enabled": true,
      "is_default": false,
      "supports_vision": true,
      "supports_text": true
    },
    {
      "id": "local_mock",
      "label": "Local Mock",
      "provider": "mock",
      "description": "本地 mock 模型，用于接口联调",
      "enabled": true,
      "is_default": false,
      "supports_vision": false,
      "supports_text": true
    }
  ]
}
```

前端要求：

- 只展示 `enabled = true` 的模型。
- 默认选择 `is_default = true` 的模型。
- 提问时提交 `id`，显示时使用 `label`。

### 6.11 提问接口

```http
POST /api/v1/query
```

请求：

```json
{
  "question": "What does Figure 3 show?",
  "file_ids": ["file_001", "file_002"],
  "selected_chunk_ids": ["chunk_001", "chunk_002"],
  "model": "qwen2_5_vl",
  "mode": "auto",
  "top_k": 5,
  "include_disabled": false
}
```

字段说明：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `question` | 是 | 用户输入问题，不能为空 |
| `file_ids` | 是 | 检索范围，支持多文件 |
| `selected_chunk_ids` | 否 | 用户手动选中的 evidence；后端应优先参考 |
| `model` | 是 | 来自 `/models` 的模型 ID |
| `mode` | 否 | `auto`、`text-rag`、`mm-rag` |
| `top_k` | 否 | 返回 evidence 数量，默认 5 |
| `include_disabled` | 否 | 是否包含 disabled chunk，默认 false |

响应：

```json
{
  "answer_id": "ans_001",
  "question": "What does Figure 3 show?",
  "answer": "Based on the retrieved evidence, Figure 3 shows that EQIX assets and shareholders' equity increased from 2015 to 2019, indicating continued IDC asset expansion.",
  "model": "qwen2_5_vl",
  "model_label": "Qwen2.5-VL",
  "route": "hybrid_route",
  "route_reason": "Question references figure/table evidence and requires both textual and visual context.",
  "selected_chunk_ids": ["chunk_001", "chunk_002"],
  "citations": [
    {
      "citation_id": "cite_001",
      "evidence_id": "chunk_002",
      "chunk_id": "chunk_002",
      "file_id": "file_001",
      "file_name": "IDC_REIT_evidence.pdf",
      "page": 3,
      "source_type": "table",
      "bbox": [90, 360, 530, 590],
      "quote": "Shareholders' equity and total assets rose from 2015 to 2019.",
      "preview_url": "/api/v1/evidence/chunk_002/preview"
    }
  ],
  "evidences": [
    {
      "chunk_id": "chunk_002",
      "evidence_id": "chunk_002",
      "file_id": "file_001",
      "file_name": "IDC_REIT_evidence.pdf",
      "page": 3,
      "source_type": "table",
      "title": "Figure 3 - EQIX assets and equity",
      "content": "Shareholders' equity and total assets rose from 2015 to 2019, showing continued acquisition and expansion of IDC assets.",
      "score": 0.913,
      "bbox": [90, 360, 530, 590],
      "region_id": "region_003_002",
      "image_url": "/api/v1/files/file_001/pages/3/image",
      "preview_url": "/api/v1/evidence/chunk_002/preview",
      "enabled": true,
      "metadata": {}
    }
  ],
  "latency_ms": 860,
  "created_at": "2026-06-11T10:05:00+08:00"
}
```

前端对应：

- `ResultPage` 的主标题使用 `question`。
- 模型 badge 使用 `model_label`。
- answer 正文使用 `answer`。
- `Referenced evidence` 使用 `evidences`。
- 右侧预览可以使用第一条 citation 或用户 focused chunk 的 `preview_url`。

### 6.12 样例文件接口，可选

当前前端 mock 中有：

```ts
const sampleFiles = ["IDC_REIT_evidence.pdf", "course_requirements.pdf", "chart_appendix.png"];
```

如果需要保留“Use sample files”按钮并接入真实后端，可提供：

```http
POST /api/v1/demo/sample-session
```

响应：

```json
{
  "files": [
    {
      "file_id": "sample_001",
      "file_name": "IDC_REIT_evidence.pdf",
      "original_name": "IDC_REIT_evidence.pdf",
      "mime_type": "application/pdf",
      "size_bytes": 482190,
      "status": "ready",
      "page_count": 36,
      "chunk_count": 128,
      "visual_region_count": 42,
      "created_at": "2026-06-11T10:00:00+08:00",
      "updated_at": "2026-06-11T10:00:00+08:00",
      "error_message": null
    }
  ],
  "active_file_id": "sample_001"
}
```

## 7. 组件级交付要求

### 7.1 `Header`

显示内容：

- 应用名：`MLLM Demo`。
- 当前视图：
  - `Knowledge Base`
  - `Query Result`
- 返回按钮：
  - 在结果页返回知识库。
  - 在知识库页返回欢迎页并清空状态。
- `Share` 按钮和暗色按钮当前没有后端逻辑。

后端影响：

- 暂无强依赖。
- 如果后续要实现分享，可新增会话分享接口。

建议分享接口：

```http
POST /api/v1/sessions/{session_id}/share
```

### 7.2 `WelcomePanel`

显示内容：

- 上传入口。
- 使用样例文件入口。
- 三步说明：上传、预览、提问。

后端要求：

- 上传接口必须稳定。
- 样例文件如果不实现，前端可继续使用本地 mock。
- 上传后必须能尽快返回 `file_id`，即使解析还没完成。

### 7.3 `KnowledgePage`

显示内容：

- `Indexed evidence` 标题。
- 状态 badge：`Parsed`。
- 已选数量：`{selectedIds.length} selected`。
- 当前文件名。
- chunk 列表。
- 底部统计：`Total 128 chunks / 36 pages / 42 visual regions`。
- 分页大小：`10 / page`。

后端要求：

- 必须提供文件维度统计：
  - `chunk_count`
  - `page_count`
  - `visual_region_count`
- 必须提供分页 chunks。
- 解析中状态不要返回空列表假装 ready，应返回 `status = parsing`。

### 7.4 `ChunkRow`

显示内容：

- checkbox 选中态。
- `source_type` 类型标签。
- `Page {page}`。
- `chunk_id`。
- `title`。
- `content`。
- `score.toFixed(3)`。

后端要求：

- `score` 必须是 number。
- `title` 不能为空；没有真实标题时用规则生成，例如：
  - `Page 3 text chunk`
  - `Page 3 figure region`
  - `Table 1 - extracted table`
- `content` 必须适合作为 evidence 摘要展示，不要返回超长全文。建议单 chunk 不超过 1200 字符。

### 7.5 `PreviewPanel`

显示内容：

- 当前文件名。
- 文件 tab 列表。
- 当前页码。
- 当前 evidence 标题和内容。
- 页面预览区域。

后端要求：

- 文件列表必须包含 `file_id` 和 `file_name`。
- 当前 evidence 必须包含 `page`。
- 页面图片接口必须可直接放入 `<img src>`。
- 如果有 `bbox`，建议额外提供高亮图 `preview_url`。

当前 Demo 右侧预览图是前端 skeleton，并不真实加载图片。接入后建议渲染：

```ts
selected.preview_url ?? selected.image_url
```

### 7.6 `Composer`

显示内容：

- 问题输入框。
- 模型选择器。
- 提交按钮。
- thinking loading。
- 收起后变成可拖动圆形入口。

后端要求：

- `/models` 返回模型列表。
- `/query` 处理提问。
- 提问时前端应阻止空问题；后端也必须校验。
- 文件未 ready 时应返回明确错误或让前端禁用提交。

### 7.7 `ResultPage`

显示内容：

- 用户问题。
- 模型 label。
- selected chunks 数量。
- answer 正文。
- referenced evidence 卡片：
  - title
  - score
  - content

后端要求：

- `/query` 返回 `answer` 和 `evidences`。
- `evidences` 最好按相关性降序排列。
- 如果用户传了 `selected_chunk_ids`，后端需要在结果中体现：
  - 要么优先使用这些 chunk。
  - 要么在 `route_reason` 中说明未使用这些 chunk 的原因。

## 8. 字段与当前 mock 数据映射

当前前端 mock：

```ts
type EvidenceChunk = {
  id: string;
  type: "text" | "figure" | "table" | "visual";
  page: number;
  score: number;
  title: string;
  content: string;
  enabled: boolean;
};
```

后端字段映射：

| 前端 mock 字段 | 后端字段 | 说明 |
| --- | --- | --- |
| `id` | `chunk_id` | 接入时可映射 |
| `type` | `source_type` | 建议后端使用 `source_type` |
| `page` | `page` | 1-based |
| `score` | `score` | number |
| `title` | `title` | string |
| `content` | `content` | string |
| `enabled` | `enabled` | boolean |

当前 mock 文件名：

```ts
["IDC_REIT_evidence.pdf", "course_requirements.pdf", "chart_appendix.png"]
```

后端应替换为：

```ts
FileAsset[]
```

前端展示 `file_name`，业务提交使用 `file_id`。

当前 mock 模型：

```ts
["Qwen2.5-VL", "GPT-4.1", "Claude 3.7", "Local Mock"]
```

后端应替换为：

```ts
ModelOption[]
```

前端展示 `label`，业务提交使用 `id`。

## 9. 错误格式

所有 JSON 接口错误统一返回：

```json
{
  "error": {
    "code": "parse_failed",
    "message": "Could not parse PDF.",
    "details": {
      "file_id": "file_001"
    }
  }
}
```

建议错误码：

| HTTP 状态 | code | 场景 |
| --- | --- | --- |
| 400 | `invalid_request` | 参数缺失或格式错误 |
| 400 | `empty_question` | 问题为空 |
| 404 | `file_not_found` | 文件不存在 |
| 404 | `chunk_not_found` | chunk 不存在 |
| 404 | `job_not_found` | 任务不存在 |
| 409 | `file_not_ready` | 文件未解析完成 |
| 413 | `file_too_large` | 文件过大 |
| 415 | `unsupported_file_type` | 文件类型不支持 |
| 422 | `parse_failed` | 解析失败 |
| 429 | `rate_limited` | 模型或接口限流 |
| 500 | `internal_error` | 未预期错误 |

前端展示原则：

- `message` 应可直接展示给用户。
- `details` 给开发调试使用。

## 10. 后端解析与检索建议

### 10.1 文件处理

PDF：

- 抽取每页文本。
- 渲染每页图片。
- 生成文本 chunk。
- 生成整页 visual evidence。
- 可选识别表格、图、公式等区域。

图片：

- 当作单页文档。
- OCR 生成文本 evidence。
- VLM 生成 visual summary。
- 如果是图表，生成 `source_type = "figure"` 或 `source_type = "table"`。

### 10.2 chunk 类型约定

```text
text   文本段落、标题、说明文字
figure 图、图表、流程图、截图区域
table  表格，content 建议返回 Markdown 表格或表格摘要
visual 整页视觉摘要或无法精确归类的视觉 evidence
```

### 10.3 bbox 坐标约定

```ts
bbox = [x1, y1, x2, y2]
```

要求：

- 坐标基于页面渲染图片的像素坐标。
- `x1 < x2`，`y1 < y2`。
- 页面左上角为 `(0, 0)`。
- 若无局部区域，返回 `null`。
- 整页 bbox 可以返回 `[0, 0, width, height]`，但更建议 `null` 并用 `source_type = "visual"` 标明整页。

### 10.4 问答路由

后端建议支持三种模式：

```text
auto
text-rag
mm-rag
```

返回 route：

```text
text_route
table_route
vision_route
hybrid_route
```

示例：

```json
{
  "route": "hybrid_route",
  "route_reason": "Question references chart/table evidence and requires both text and visual retrieval."
}
```

## 11. 最小可联调版本

如果后端时间有限，至少实现以下接口即可让前端从 mock 切到真实数据：

1. `POST /api/v1/files`
2. `POST /api/v1/files/{file_id}/parse`
3. `GET /api/v1/jobs/{job_id}`
4. `GET /api/v1/files`
5. `GET /api/v1/files/{file_id}/chunks`
6. `GET /api/v1/files/{file_id}/pages/{page}/image`
7. `GET /api/v1/models`
8. `POST /api/v1/query`

最小 chunk 返回必须包含：

```json
{
  "chunk_id": "chunk_001",
  "evidence_id": "chunk_001",
  "file_id": "file_001",
  "file_name": "demo.pdf",
  "page": 1,
  "source_type": "text",
  "title": "Page 1 text chunk",
  "content": "Chunk content...",
  "score": 0.8,
  "bbox": null,
  "region_id": null,
  "image_url": "/api/v1/files/file_001/pages/1/image",
  "preview_url": null,
  "enabled": true,
  "metadata": {}
}
```

最小 query 返回必须包含：

```json
{
  "answer_id": "ans_001",
  "question": "用户问题",
  "answer": "回答正文",
  "model": "qwen2_5_vl",
  "model_label": "Qwen2.5-VL",
  "route": "text_route",
  "route_reason": "Text retrieval was sufficient.",
  "selected_chunk_ids": [],
  "citations": [],
  "evidences": [],
  "latency_ms": 500,
  "created_at": "2026-06-11T10:05:00+08:00"
}
```

## 12. 后端验收清单

后端交付时请逐项确认：

- 上传多个文件后，每个文件都有稳定 `file_id`。
- 文件解析状态能从 `uploaded/queued/parsing` 变为 `ready` 或 `failed`。
- `GET /files` 能返回所有已上传文件。
- `GET /files/{file_id}/chunks` 能返回分页 chunk。
- chunk 的 `chunk_id` 稳定，刷新后不变。
- chunk 的 `page` 能正确打开页面图片。
- `source_type` 只使用 `text/figure/table/visual`。
- `score` 是 number，不是字符串。
- `title` 和 `content` 不为空。
- 页面图片接口可以被浏览器直接访问。
- evidence 高亮图可选，但有 `preview_url` 时必须可访问。
- `/models` 返回启用模型，并且有且只有一个默认模型。
- `/query` 能接收多文件和 selected chunks。
- `/query` 返回 answer、citations、evidences、route、latency。
- 错误统一使用 `{ error: { code, message, details } }`。

## 13. 与现有 Python 数据结构的对应关系

仓库中已有后端侧数据结构位于 `src/mllmproject/schemas.py`。接口字段建议与其保持兼容：

| Python dataclass | 接口概念 |
| --- | --- |
| `Document` | `FileAsset` 的解析后文档对象 |
| `Page` | 页面文本和页面图片信息 |
| `Chunk` | `EvidenceChunk` 的基础来源 |
| `Evidence` | 检索命中的 evidence |
| `Citation` | 回答引用来源 |
| `AnswerResult` | `/query` 响应主体 |

需要补充或映射的字段：

- `doc_id` 可以映射为 `file_id`，也可以后端保留二者。
- `source_type` 已存在，应与接口枚举统一。
- `image_path` 不应直接暴露本地路径，接口应转换为 `image_url`。
- `bbox` 已存在，需保证坐标约定统一。
- `AnswerResult` 当前没有 `answer_id`、`model`、`latency_ms`，接口层可包装补充。

## 14. 推荐开发顺序

1. 先实现文件上传、文件列表和解析状态。
2. 再实现 chunks 列表，让 `KnowledgePage` 可以显示真实数据。
3. 实现页面图片接口，让 `PreviewPanel` 可以显示真实页图。
4. 实现模型列表。
5. 实现 `/query`，先返回 mock answer + 真实 retrieved evidences。
6. 接入真实 embedding、reranker 和 generator。
7. 最后补 evidence 高亮图、样例文件、分享会话等增强能力。
