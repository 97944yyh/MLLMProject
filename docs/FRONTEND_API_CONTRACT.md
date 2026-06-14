# MLLM Demo Frontend API Contract

This document defines the backend API expected by the React frontend demo in
`frontend/`. The current frontend is mock-only, but the UI is designed around
these contracts.

## 1. Scope

The frontend needs to support four workflows:

- Upload one or more evidence files.
- Parse uploaded files and show processing status.
- Browse the knowledge base chunks generated from uploaded files.
- Ask a question, then show the answer, citations, and referenced evidence.

Recommended base URL:

```text
/api/v1
```

All responses should use JSON except file upload and preview image endpoints.

## 2. Shared Types

### FileAsset

```ts
type FileAsset = {
  file_id: string;
  file_name: string;
  mime_type: string;
  size_bytes: number;
  status: "uploaded" | "parsing" | "ready" | "failed";
  page_count?: number;
  chunk_count?: number;
  created_at: string;
};
```

### EvidenceChunk

```ts
type EvidenceChunk = {
  chunk_id: string;
  file_id: string;
  page: number;
  source_type: "text" | "figure" | "table" | "visual";
  title?: string;
  content: string;
  score?: number;
  bbox?: [number, number, number, number] | null;
  enabled: boolean;
  metadata?: Record<string, unknown>;
};
```

### Citation

```ts
type Citation = {
  evidence_id: string;
  chunk_id?: string;
  file_id: string;
  page: number;
  source_type: "text" | "figure" | "table" | "visual";
  bbox?: [number, number, number, number] | null;
};
```

### ModelOption

```ts
type ModelOption = {
  id: string;
  label: string;
  provider?: string;
  description?: string;
  is_default?: boolean;
  enabled: boolean;
};
```

## 3. Endpoints

### Upload Evidence Files

```http
POST /api/v1/files
Content-Type: multipart/form-data
```

Form field:

```text
files: File[]
```

Response:

```json
{
  "files": [
    {
      "file_id": "file_001",
      "file_name": "IDC_REIT_evidence.pdf",
      "mime_type": "application/pdf",
      "size_bytes": 482190,
      "status": "uploaded",
      "created_at": "2026-06-08T13:00:00Z"
    }
  ]
}
```

### Start Parsing

```http
POST /api/v1/files/{file_id}/parse
```

Request:

```json
{
  "include_visual": true,
  "chunking": {
    "max_chars": 900,
    "overlap": 80
  }
}
```

Response:

```json
{
  "job_id": "job_001",
  "file_id": "file_001",
  "status": "parsing"
}
```

### Get Parse Status

```http
GET /api/v1/jobs/{job_id}
```

Response:

```json
{
  "job_id": "job_001",
  "file_id": "file_001",
  "status": "ready",
  "progress": 1,
  "message": "Parsed 36 pages and 128 chunks."
}
```

### List Uploaded Files

```http
GET /api/v1/files
```

Response:

```json
{
  "files": []
}
```

### List Knowledge Base Chunks

```http
GET /api/v1/files/{file_id}/chunks?page=1&page_size=10
```

Response:

```json
{
  "file_id": "file_001",
  "total": 128,
  "page": 1,
  "page_size": 10,
  "chunks": [
    {
      "chunk_id": "chunk_001",
      "file_id": "file_001",
      "page": 3,
      "source_type": "figure",
      "title": "Figure 2 - Hyperscale IDC growth",
      "content": "Growth trend and country share...",
      "score": 0.941,
      "bbox": [84, 112, 518, 296],
      "enabled": true,
      "metadata": {}
    }
  ]
}
```

### List Available Models

The frontend renders the model picker from this endpoint. Return enabled models
in display order. If this endpoint is not available yet, the frontend can fall
back to the mock model list.

```http
GET /api/v1/models
```

Response:

```json
{
  "models": [
    {
      "id": "qwen2_5_vl",
      "label": "Qwen2.5-VL",
      "provider": "local",
      "description": "Default multimodal model for evidence QA.",
      "is_default": true,
      "enabled": true
    },
    {
      "id": "gpt_4_1",
      "label": "GPT-4.1",
      "provider": "openai",
      "enabled": true
    },
    {
      "id": "claude_3_7",
      "label": "Claude 3.7",
      "provider": "anthropic",
      "enabled": true
    },
    {
      "id": "local_mock",
      "label": "Local Mock",
      "provider": "mock",
      "enabled": true
    }
  ]
}
```

### Toggle Chunk Availability

```http
PATCH /api/v1/chunks/{chunk_id}
```

Request:

```json
{
  "enabled": true
}
```

Response:

```json
{
  "chunk_id": "chunk_001",
  "enabled": true
}
```

### Get Page Preview

The frontend preview pane should render page images through a normal image URL.

```http
GET /api/v1/files/{file_id}/pages/{page}/image
```

Response:

```text
image/png
```

Optional highlighted preview:

```http
GET /api/v1/evidence/{evidence_id}/preview
```

Response:

```text
image/png
```

### Ask Question

```http
POST /api/v1/query
```

Request:

```json
{
  "question": "What does Figure 3 show?",
  "file_ids": ["file_001", "file_002"],
  "model": "qwen2_5_vl",
  "mode": "auto",
  "top_k": 5
}
```

`model` should use the `ModelOption.id` returned by `GET /api/v1/models`.
The UI label can remain user-facing, for example:

```text
Qwen2.5-VL
GPT-4.1
Claude 3.7
Local Mock
```

`mode` values:

```text
auto
text-rag
mm-rag
```

Response:

```json
{
  "answer_id": "ans_001",
  "answer": "Based on the retrieved evidence...",
  "model": "qwen2_5_vl",
  "model_label": "Qwen2.5-VL",
  "route": "hybrid_route",
  "route_reason": "Question references chart/table evidence.",
  "citations": [
    {
      "evidence_id": "chunk_001",
      "chunk_id": "chunk_001",
      "file_id": "file_001",
      "page": 3,
      "source_type": "figure",
      "bbox": [84, 112, 518, 296]
    }
  ],
  "evidences": [
    {
      "chunk_id": "chunk_001",
      "file_id": "file_001",
      "page": 3,
      "source_type": "figure",
      "title": "Figure 2 - Hyperscale IDC growth",
      "content": "Growth trend and country share...",
      "score": 0.941,
      "bbox": [84, 112, 518, 296],
      "enabled": true,
      "metadata": {}
    }
  ],
  "latency_ms": 860
}
```

## 4. Frontend State Mapping

The React frontend expects these states:

- No uploaded files: show welcome copy on the left and empty preview on the right.
- Files uploaded but parsing: show file tabs in preview and parsing status.
- Files ready: show chunk list on the left and preview on the right.
- Query submitted: switch left content to query result while preserving right preview.
- Model picker: show a small custom popover with the enabled models from
  `GET /api/v1/models`; submit the selected model `id` in `/query`.

## 5. Error Format

All JSON endpoints should return this error shape:

```json
{
  "error": {
    "code": "parse_failed",
    "message": "Could not parse PDF.",
    "details": {}
  }
}
```

Recommended HTTP status codes:

- `400`: invalid request.
- `404`: file, chunk, or job not found.
- `413`: uploaded file too large.
- `422`: unsupported file type or parse failure.
- `500`: unexpected backend failure.

## 6. Implementation Notes

- Keep `file_id`, `chunk_id`, and `evidence_id` stable for frontend selection.
- The preview panel should work with multiple files, so `/files` and `/chunks` must be file-scoped.
- Query can receive multiple `file_ids`; backend may search all selected files.
- Model options should be stable by `id`; labels can change without breaking saved frontend state.
- Image URLs can be plain endpoints; the frontend does not require base64 image payloads.
- The current frontend only simulates parsing. Backend integration should replace mock `chunks`, `sampleFiles`, and query result generation.
