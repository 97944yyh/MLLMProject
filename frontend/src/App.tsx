import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  FileText,
  Layers3,
  Moon,
  PanelRightOpen,
  RotateCcw,
  Search,
  Share2,
  Sparkles,
  Upload,
  Zap,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

type View = "knowledge" | "result";
type EvidenceType = "text" | "figure" | "table" | "visual";

type EvidenceChunk = {
  id: string;
  type: EvidenceType;
  page: number;
  score: number;
  title: string;
  content: string;
  enabled: boolean;
};

const sampleFiles = ["IDC_REIT_evidence.pdf", "course_requirements.pdf", "chart_appendix.png"];
const models = ["Qwen2.5-VL", "GPT-4.1", "Claude 3.7", "Local Mock"];

const chunks: EvidenceChunk[] = [
  {
    id: "chunk_001",
    type: "figure",
    page: 3,
    score: 0.941,
    title: "Figure 2 - Hyperscale IDC growth",
    content:
      "Growth trend and country share of worldwide hyperscale IDCs. China, Japan, the UK, Germany and the United States are compared in the figure.",
    enabled: true,
  },
  {
    id: "chunk_002",
    type: "table",
    page: 3,
    score: 0.913,
    title: "Figure 3 - EQIX assets and equity",
    content:
      "Shareholders' equity and total assets rose from 2015 to 2019, showing continued acquisition and expansion of IDC assets.",
    enabled: true,
  },
  {
    id: "chunk_003",
    type: "text",
    page: 4,
    score: 0.886,
    title: "Conclusion paragraph",
    content:
      "The report argues that technology-enhanced real estate can be a stable underlying asset for infrastructure REIT pilot programs.",
    enabled: true,
  },
  {
    id: "chunk_004",
    type: "visual",
    page: 4,
    score: 0.842,
    title: "Page visual summary",
    content:
      "A page-level visual chunk containing conclusion panels and layout evidence used for multimodal citation preview.",
    enabled: false,
  },
];

function App() {
  const [view, setView] = useState<View>("knowledge");
  const [query, setQuery] = useState("");
  const [attachments, setAttachments] = useState<string[]>([]);
  const [activeFile, setActiveFile] = useState("");
  const [selectedIds, setSelectedIds] = useState<string[]>([chunks[0].id]);
  const [focusedId, setFocusedId] = useState(chunks[0].id);
  const [model, setModel] = useState(models[0]);
  const [isThinking, setIsThinking] = useState(false);
  const [isComposerOpen, setIsComposerOpen] = useState(true);

  const hasUploaded = attachments.length > 0;
  const selected = useMemo(
    () => chunks.find((chunk) => chunk.id === focusedId) ?? chunks[0],
    [focusedId],
  );
  const selectedChunks = useMemo(
    () => selectedIds.map((id) => chunks.find((chunk) => chunk.id === id)).filter(Boolean) as EvidenceChunk[],
    [selectedIds],
  );

  const addFiles = (files: FileList | null) => {
    if (!files?.length) return;
    const names = Array.from(files).map((file) => file.name);
    setAttachments((current) => {
      const next = Array.from(new Set([...current, ...names]));
      setActiveFile((active) => active || next[0]);
      return next;
    });
    setIsComposerOpen(true);
    setView("knowledge");
  };

  const loadSample = () => {
    setAttachments(sampleFiles);
    setActiveFile(sampleFiles[0]);
    setIsComposerOpen(true);
    setView("knowledge");
  };

  const returnToCover = () => {
    setAttachments([]);
    setActiveFile("");
    setQuery("");
    setSelectedIds([chunks[0].id]);
    setFocusedId(chunks[0].id);
    setView("knowledge");
  };

  const toggleChunkSelection = (id: string) => {
    setFocusedId(id);
    setSelectedIds((current) =>
      current.includes(id) ? current.filter((selectedId) => selectedId !== id) : [...current, id],
    );
  };

  const runQuery = () => {
    if (!query.trim() || !hasUploaded) return;
    setIsThinking(true);
    window.setTimeout(() => {
      setIsThinking(false);
      setView("result");
    }, 520);
  };

  return (
    <div className="min-h-screen bg-[linear-gradient(135deg,#fbfbfa_0%,#f8fbff_48%,#fffaf2_100%)] text-[#202833]">
      <Header
        hasUploaded={hasUploaded}
        view={view}
        onBack={view === "result" ? () => setView("knowledge") : returnToCover}
      />

      <main
        className="mx-auto grid min-h-[calc(100vh-68px)] max-w-[2020px] grid-cols-1 border-x border-dashed border-zinc-200 px-8 pb-8 pt-10 lg:grid-cols-[minmax(520px,820px)_minmax(420px,1fr)] lg:gap-10"
        onMouseDown={() => setIsComposerOpen(false)}
      >
        <section className="min-w-0 lg:h-[calc(100vh-140px)]">
          <AnimatePresence mode="wait">
            {!hasUploaded ? (
              <WelcomePanel key="welcome" onUpload={addFiles} onSample={loadSample} />
            ) : view === "knowledge" ? (
              <KnowledgePage
                key="knowledge"
                activeFile={activeFile}
                selectedIds={selectedIds}
                focusedId={focusedId}
                onSelect={toggleChunkSelection}
              />
            ) : (
              <ResultPage
                key="result"
                query={query}
                model={model}
                selected={selected}
                selectedChunks={selectedChunks}
                onBack={() => setView("knowledge")}
                onReturnToCover={returnToCover}
              />
            )}
          </AnimatePresence>
        </section>

        <PreviewPanel
          activeFile={activeFile}
          attachments={attachments}
          hasUploaded={hasUploaded}
          selected={selected}
          onActiveFile={setActiveFile}
          onUpload={addFiles}
        />
      </main>

      <Composer
        isOpen={isComposerOpen}
        hasUploaded={hasUploaded}
        query={query}
        model={model}
        isThinking={isThinking}
        onOpen={() => setIsComposerOpen(true)}
        onModelChange={setModel}
        onQueryChange={setQuery}
        onSubmit={runQuery}
      />
    </div>
  );
}

function Header({
  hasUploaded,
  view,
  onBack,
}: {
  hasUploaded: boolean;
  view: View;
  onBack: () => void;
}) {
  return (
    <header className="flex h-[68px] items-center justify-between border-b border-zinc-100 bg-white/92 px-9 backdrop-blur">
      <div className="flex min-w-0 items-center gap-4">
        {hasUploaded ? (
          <button
            className="inline-flex items-center gap-2 rounded-lg px-2.5 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100"
            onClick={onBack}
          >
            <ArrowLeft size={17} />
            Back
          </button>
        ) : null}
        <div className="text-[26px] font-semibold tracking-tight text-zinc-900">MLLM Demo</div>
        {hasUploaded ? (
          <span className="hidden rounded-full border border-zinc-200 bg-zinc-50 px-3 py-1 text-sm font-medium text-zinc-500 sm:inline-flex">
            {view === "result" ? "Query Result" : "Knowledge Base"}
          </span>
        ) : null}
      </div>
      <div className="flex items-center gap-5 text-sm text-zinc-500">
        <span className="hidden sm:inline">Evidence knowledge base</span>
        <button className="inline-flex h-11 items-center gap-2 rounded-xl bg-[#3178f6] px-4 font-medium text-white shadow-sm transition hover:bg-[#246be8]">
          <Share2 size={18} />
          Share
        </button>
        <button className="grid h-10 w-10 place-items-center rounded-full text-zinc-700 transition hover:bg-zinc-100">
          <Moon size={22} />
        </button>
      </div>
    </header>
  );
}

function UploadButton({
  children,
  onUpload,
  variant = "plain",
}: {
  children: React.ReactNode;
  onUpload: (files: FileList | null) => void;
  variant?: "plain" | "primary";
}) {
  return (
    <label
      className={`inline-flex cursor-pointer items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition ${
        variant === "primary"
          ? "bg-[#3178f6] text-white shadow-sm hover:bg-[#246be8]"
          : "border border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50"
      }`}
    >
      <Upload size={16} />
      {children}
      <input
        className="hidden"
        type="file"
        multiple
        accept=".pdf,.png,.jpg,.jpeg,.webp"
        onChange={(event) => onUpload(event.target.files)}
      />
    </label>
  );
}

function WelcomePanel({
  onUpload,
  onSample,
}: {
  onUpload: (files: FileList | null) => void;
  onSample: () => void;
}) {
  return (
    <motion.section
      className="flex h-full max-w-[820px] flex-col overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-[0_18px_55px_rgba(36,48,64,0.06)]"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.24 }}
    >
      <div className="h-2 bg-[linear-gradient(90deg,#d8ecff,#e8f7ef,#fff0d0,#f1e8ff)]" />
      <div className="flex flex-1 flex-col bg-[linear-gradient(180deg,#ffffff_0%,#fbfdff_48%,#fffdf8_100%)] px-8 py-7">
        <div className="mb-5 inline-flex w-fit items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-sm font-medium text-[#246be8]">
          <Sparkles size={15} />
          Evidence Workspace
        </div>

        <h1 className="max-w-[620px] text-[38px] font-semibold leading-tight tracking-tight text-zinc-950">
          Multimodal Evidence Demo
        </h1>
        <p className="mt-5 max-w-[720px] text-[17px] leading-8 text-zinc-600">
          Upload reports, PDFs, screenshots, or charts. The left panel will show indexed
          knowledge-base chunks, while the right panel stays focused on file preview and attachment
          switching.
        </p>

        <div className="mt-7 flex flex-wrap items-center gap-3">
          <UploadButton onUpload={onUpload} variant="primary">
            Upload evidence
          </UploadButton>
          <button
            className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50"
            onClick={onSample}
          >
            <Sparkles size={16} />
            Use sample files
          </button>
        </div>

        <div className="mt-8 grid gap-3 sm:grid-cols-3">
          {[
            ["1", "Upload files", "PDFs, images, screenshots, or report attachments"],
            ["2", "Preview evidence", "Switch files and inspect the selected page region"],
            ["3", "Ask questions", "Choose a model and generate cited answers"],
          ].map(([step, title, text], index) => (
            <div
              key={step}
              className={`rounded-xl border p-4 ${
                index === 0
                  ? "border-blue-100 bg-blue-50/70"
                  : index === 1
                    ? "border-emerald-100 bg-emerald-50/60"
                    : "border-amber-100 bg-amber-50/60"
              }`}
            >
              <div className="mb-3 grid h-7 w-7 place-items-center rounded-full bg-white text-sm font-semibold text-[#3178f6]">
                {step}
              </div>
              <h2 className="font-medium text-zinc-950">{title}</h2>
              <p className="mt-1 text-sm leading-6 text-zinc-500">{text}</p>
            </div>
          ))}
        </div>

        <div className="mt-auto grid gap-3 pt-8 sm:grid-cols-2">
          <InfoCard
            title="Demo flow"
            text="Cover first, knowledge base after upload, query result after asking."
          />
          <InfoCard
            title="Backend handoff"
            text="The frontend API contract is documented and ready for backend integration."
          />
        </div>
      </div>
    </motion.section>
  );
}

function InfoCard({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white/78 p-4 shadow-sm">
      <div className="text-sm font-medium text-zinc-950">{title}</div>
      <p className="mt-1 text-sm leading-6 text-zinc-500">{text}</p>
    </div>
  );
}

function KnowledgePage({
  activeFile,
  selectedIds,
  focusedId,
  onSelect,
}: {
  activeFile: string;
  selectedIds: string[];
  focusedId: string;
  onSelect: (id: string) => void;
}) {
  return (
    <motion.section
      className="flex h-full max-w-[820px] flex-col"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.22 }}
    >
      <div className="min-h-0 flex-1 overflow-hidden rounded-xl border border-zinc-200 bg-white">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-100 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-zinc-950">Indexed evidence</h2>
            <p className="mt-1 text-sm leading-6 text-zinc-500">
              Select multiple chunks for retrieval. Click again to remove a chunk.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-[#edf7f3] px-3 py-1.5 text-sm font-medium text-[#26765b]">
              <CheckCircle2 size={15} />
              Parsed
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-zinc-100 px-3 py-1.5 text-sm font-medium text-zinc-600">
              <Layers3 size={15} />
              {selectedIds.length} selected
            </span>
            <span className="inline-flex max-w-[220px] items-center gap-1.5 truncate rounded-full bg-[#eef4ff] px-3 py-1.5 text-sm font-medium text-[#3178f6]">
              <FileText size={15} className="shrink-0" />
              <span className="truncate">{activeFile}</span>
            </span>
          </div>
        </div>

        <div className="thin-scrollbar max-h-[calc(100%-132px)] divide-y divide-zinc-100 overflow-y-auto">
          {chunks.map((chunk) => (
            <ChunkRow
              key={chunk.id}
              chunk={chunk}
              active={selectedIds.includes(chunk.id)}
              focused={chunk.id === focusedId}
              onSelect={() => onSelect(chunk.id)}
            />
          ))}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-4 text-sm text-zinc-500">
          <span>Total 128 chunks · 36 pages · 42 visual regions</span>
          <button className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1 font-medium text-zinc-700 transition hover:bg-zinc-100">
            10 / page
            <ChevronDown size={15} />
          </button>
        </div>
      </div>
    </motion.section>
  );
}

function ChunkRow({
  chunk,
  active,
  focused,
  onSelect,
}: {
  chunk: EvidenceChunk;
  active: boolean;
  focused: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      className={`grid w-full grid-cols-[22px_1fr_auto] gap-4 px-6 py-5 text-left transition ${
        active
          ? "bg-blue-50/55"
          : focused
            ? "bg-zinc-50/80"
            : "hover:bg-zinc-50/70"
      }`}
      onClick={onSelect}
      aria-pressed={active}
    >
      <span
        className={`mt-1 grid h-4 w-4 place-items-center rounded border ${
          active
            ? "border-[#3178f6] bg-[#3178f6] text-white"
            : focused
              ? "border-[#3178f6]/60 bg-white"
              : "border-zinc-300 bg-white"
        }`}
      >
        {active ? <CheckCircle2 size={12} /> : null}
      </span>
      <span className="min-w-0">
        <span className="mb-1.5 flex flex-wrap items-center gap-2">
          <span className="rounded-md bg-zinc-100 px-2 py-0.5 text-xs font-medium uppercase text-zinc-600">
            {chunk.type}
          </span>
          <span className="text-xs text-zinc-500">Page {chunk.page}</span>
          <span className="text-xs text-zinc-400">{chunk.id}</span>
        </span>
        <span className="block truncate text-[15px] font-medium text-zinc-950">{chunk.title}</span>
        <span className="mt-1 block line-clamp-2 text-sm leading-6 text-zinc-600">
          {chunk.content}
        </span>
      </span>
      <span className="mt-1 text-sm font-medium text-zinc-500">{chunk.score.toFixed(3)}</span>
    </button>
  );
}

function PreviewPanel({
  activeFile,
  attachments,
  hasUploaded,
  selected,
  onActiveFile,
  onUpload,
}: {
  activeFile: string;
  attachments: string[];
  hasUploaded: boolean;
  selected: EvidenceChunk;
  onActiveFile: (file: string) => void;
  onUpload: (files: FileList | null) => void;
}) {
  return (
    <motion.aside
      className="mt-10 min-w-0 lg:sticky lg:top-24 lg:mt-0 lg:h-[calc(100vh-140px)]"
      initial={{ opacity: 0, x: 12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.24 }}
    >
      <div className="flex h-full flex-col overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-[0_18px_55px_rgba(36,48,64,0.06)]">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-100 px-5 py-4">
          <div>
            <h2 className="font-semibold text-zinc-950">Preview</h2>
            <p className="mt-0.5 text-sm text-zinc-500">
              {hasUploaded ? activeFile : "Upload files to preview evidence"}
            </p>
          </div>
          <UploadButton onUpload={onUpload}>Add file</UploadButton>
        </div>

        {hasUploaded ? (
          <>
            <div className="flex gap-2 overflow-x-auto border-b border-zinc-100 px-5 py-3">
              {attachments.map((file) => (
                <button
                  key={file}
                  className={`shrink-0 rounded-lg border px-3 py-1.5 text-sm transition ${
                    activeFile === file
                      ? "border-[#3178f6]/30 bg-blue-50 text-[#246be8]"
                      : "border-zinc-200 bg-white text-zinc-600 hover:bg-zinc-50"
                  }`}
                  onClick={() => onActiveFile(file)}
                >
                  {file}
                </button>
              ))}
            </div>
            <AnimatePresence mode="wait">
              <motion.div
                key={`${activeFile}-${selected.id}`}
                className="thin-scrollbar min-h-0 flex-1 overflow-y-auto bg-[#fbfbfa] p-5"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2 }}
              >
                <div className="mx-auto min-h-[680px] max-w-[520px] rounded-lg border border-zinc-200 bg-white p-7 shadow-sm">
                  <div className="mb-7 flex items-center justify-between border-b border-zinc-100 pb-4 text-sm text-zinc-400">
                    <span>{activeFile}</span>
                    <span>Page {selected.page}</span>
                  </div>
                  <div className="space-y-3">
                    <div className="h-3 w-56 rounded bg-zinc-200" />
                    {Array.from({ length: 7 }).map((_, index) => (
                      <div
                        key={index}
                        className="h-2 rounded bg-zinc-100"
                        style={{ width: `${96 - index * 6}%` }}
                      />
                    ))}
                  </div>
                  <div className="my-8 rounded-lg bg-[#fff7e6] p-4">
                    <div className="mb-3 flex h-40 items-end gap-2">
                      {[42, 56, 64, 82, 96, 118, 132].map((height, index) => (
                        <motion.span
                          key={index}
                          className="flex-1 rounded-t bg-[#61bfc8]"
                          initial={{ height: 12 }}
                          animate={{ height }}
                          transition={{ delay: index * 0.035, duration: 0.22 }}
                        />
                      ))}
                    </div>
                  </div>
                  <motion.div
                    layout
                    className="rounded-lg border border-[#3178f6]/30 bg-blue-50/55 p-4 text-sm leading-6 text-zinc-700"
                  >
                    <div className="mb-1 font-medium text-[#246be8]">{selected.title}</div>
                    {selected.content}
                  </motion.div>
                </div>
              </motion.div>
            </AnimatePresence>
          </>
        ) : (
          <div className="grid flex-1 place-items-center bg-[#fbfbfa] p-8 text-center">
            <div className="max-w-sm">
              <div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-full bg-blue-50 text-[#3178f6]">
                <PanelRightOpen size={22} />
              </div>
              <h3 className="text-lg font-semibold text-zinc-950">No preview yet</h3>
              <p className="mt-2 text-sm leading-6 text-zinc-500">
                Upload one or more attachments to preview pages and switch between files.
              </p>
              <div className="mt-5">
                <UploadButton onUpload={onUpload} variant="primary">
                  Upload evidence
                </UploadButton>
              </div>
            </div>
          </div>
        )}
      </div>
    </motion.aside>
  );
}

function ResultPage({
  query,
  model,
  selected,
  selectedChunks,
  onBack,
  onReturnToCover,
}: {
  query: string;
  model: string;
  selected: EvidenceChunk;
  selectedChunks: EvidenceChunk[];
  onBack: () => void;
  onReturnToCover: () => void;
}) {
  const referencedChunks = selectedChunks.length ? selectedChunks : [selected];

  return (
    <motion.section
      className="flex h-full max-w-[820px] flex-col"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.22 }}
    >
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <button
          className="inline-flex items-center gap-2 text-xl font-medium text-zinc-950"
          onClick={onBack}
        >
          <ArrowLeft size={22} />
          <span>Back to knowledge base</span>
        </button>
        <button
          className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50"
          onClick={onReturnToCover}
        >
          <RotateCcw size={16} />
          Reset demo
        </button>
      </div>

      <h1 className="mb-5 text-[34px] font-semibold tracking-tight text-zinc-950">
        {query || "Query result"}
      </h1>

      <div className="mb-5 flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1.5 text-sm font-medium text-[#246be8]">
          <Sparkles size={15} />
          {model}
        </span>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-zinc-100 px-3 py-1.5 text-sm font-medium text-zinc-600">
          <Search size={15} />
          {referencedChunks.length} selected chunks
        </span>
      </div>

      <article className="min-h-0 flex-1 overflow-y-auto rounded-xl border border-zinc-200 bg-white px-7 py-6">
        <p className="text-[17px] leading-8 text-zinc-800">
          Based on the retrieved evidence, the document argues that IDC infrastructure has become a
          stable technology-enhanced real estate asset. The strongest support comes from the selected
          figure/table chunks and the conclusion paragraph, which connect hyperscale IDC growth with
          REIT asset expansion.
        </p>

        <div className="mt-7">
          <h2 className="mb-3 text-base font-semibold text-zinc-950">Referenced evidence</h2>
          <div className="space-y-3">
            {referencedChunks.map((chunk) => (
              <div key={chunk.id} className="rounded-lg border border-zinc-100 bg-zinc-50 px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-medium text-zinc-900">{chunk.title}</span>
                  <span className="shrink-0 text-sm text-zinc-500">{chunk.score.toFixed(3)}</span>
                </div>
                <p className="mt-1 text-sm leading-6 text-zinc-600">{chunk.content}</p>
              </div>
            ))}
          </div>
        </div>
      </article>
    </motion.section>
  );
}

function ProjectLogoMark({ compact = false }: { compact?: boolean }) {
  return (
    <div
      className={`relative grid place-items-center rounded-full border border-white/80 bg-white/72 shadow-inner backdrop-blur-xl ${
        compact ? "h-11 w-11" : "h-12 w-12"
      }`}
    >
      <div className="absolute left-2 top-2 h-2 w-2 rounded-full bg-[#61bfc8]" />
      <div className="absolute bottom-2 right-2 h-2 w-2 rounded-full bg-[#f4c86a]" />
      <div className="relative flex items-end gap-[2px]">
        <span className="h-5 w-[5px] rounded-full bg-[#3178f6]" />
        <span className="h-7 w-[5px] rounded-full bg-[#7c8cf7]" />
        <span className="h-4 w-[5px] rounded-full bg-[#61bfc8]" />
      </div>
    </div>
  );
}

function Composer({
  isOpen,
  hasUploaded,
  query,
  model,
  isThinking,
  onOpen,
  onModelChange,
  onQueryChange,
  onSubmit,
}: {
  isOpen: boolean;
  hasUploaded: boolean;
  query: string;
  model: string;
  isThinking: boolean;
  onOpen: () => void;
  onModelChange: (model: string) => void;
  onQueryChange: (query: string) => void;
  onSubmit: () => void;
}) {
  const iosSpring = {
    type: "spring" as const,
    stiffness: 520,
    damping: 44,
    mass: 0.86,
  };
  const orbSize = 64;
  const openHeight = 130;
  const margin = 20;
  const dragGraceTimer = useRef<number | null>(null);
  const wasDraggingRef = useRef(false);
  const lastDragAtRef = useRef(0);
  const dragStateRef = useRef<{
    pointerId: number;
    startX: number;
    startY: number;
    startLeft: number;
    startTop: number;
    moved: boolean;
  } | null>(null);
  const [viewport, setViewport] = useState(() => ({
    width: typeof window === "undefined" ? 1280 : window.innerWidth,
    height: typeof window === "undefined" ? 760 : window.innerHeight,
  }));
  const [orbPosition, setOrbPosition] = useState<{ left: number; top: number } | null>(null);
  const [isModelMenuOpen, setIsModelMenuOpen] = useState(false);

  const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);
  const clampOrbPosition = (position: { left: number; top: number }, width = viewport.width, height = viewport.height) => ({
    left: clamp(position.left, 16, Math.max(16, width - orbSize - 16)),
    top: clamp(position.top, 16, Math.max(16, height - orbSize - 16)),
  });

  useEffect(() => {
    const updateViewport = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      setViewport({ width, height });
      setOrbPosition((current) => (current ? clampOrbPosition(current, width, height) : current));
    };

    updateViewport();
    window.addEventListener("resize", updateViewport);
    return () => {
      window.removeEventListener("resize", updateViewport);
      if (dragGraceTimer.current) window.clearTimeout(dragGraceTimer.current);
    };
  }, []);

  useEffect(() => {
    if (!isOpen) setIsModelMenuOpen(false);
  }, [isOpen]);

  const openWidth = Math.min(1110, Math.max(320, viewport.width - margin * 2));
  const openLeft = (viewport.width - openWidth) / 2;
  const openTop = Math.max(margin, viewport.height - 24 - openHeight);
  const defaultOrbPosition = {
    left: (viewport.width - orbSize) / 2,
    top: viewport.height - 28 - orbSize,
  };
  const closedPosition = clampOrbPosition(orbPosition ?? defaultOrbPosition);
  const beginOrbDrag = (event: React.PointerEvent<HTMLDivElement>) => {
    if (isOpen) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    if (dragGraceTimer.current) window.clearTimeout(dragGraceTimer.current);
    dragStateRef.current = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      startLeft: closedPosition.left,
      startTop: closedPosition.top,
      moved: false,
    };
  };
  const moveOrb = (event: React.PointerEvent<HTMLDivElement>) => {
    const dragState = dragStateRef.current;
    if (!dragState || dragState.pointerId !== event.pointerId) return;
    const deltaX = event.clientX - dragState.startX;
    const deltaY = event.clientY - dragState.startY;

    if (Math.abs(deltaX) > 3 || Math.abs(deltaY) > 3) {
      dragState.moved = true;
      wasDraggingRef.current = true;
      lastDragAtRef.current = performance.now();
    }

    setOrbPosition(
      clampOrbPosition({
        left: dragState.startLeft + deltaX,
        top: dragState.startTop + deltaY,
      }),
    );
  };
  const endOrbDrag = (event: React.PointerEvent<HTMLDivElement>) => {
    const dragState = dragStateRef.current;
    if (!dragState || dragState.pointerId !== event.pointerId) return;
    event.currentTarget.releasePointerCapture(event.pointerId);
    dragStateRef.current = null;

    if (dragState.moved) {
      dragGraceTimer.current = window.setTimeout(() => {
        wasDraggingRef.current = false;
      }, 140);
    }
  };
  const beginOrbMouseDrag = (event: React.MouseEvent<HTMLDivElement>) => {
    event.stopPropagation();
    if (isOpen || event.button !== 0) return;

    if (dragGraceTimer.current) window.clearTimeout(dragGraceTimer.current);
    const startX = event.clientX;
    const startY = event.clientY;
    const startLeft = closedPosition.left;
    const startTop = closedPosition.top;
    let moved = false;

    const handleMove = (moveEvent: MouseEvent) => {
      const deltaX = moveEvent.clientX - startX;
      const deltaY = moveEvent.clientY - startY;

      if (Math.abs(deltaX) > 3 || Math.abs(deltaY) > 3) {
        moved = true;
        wasDraggingRef.current = true;
        lastDragAtRef.current = performance.now();
      }

      setOrbPosition(
        clampOrbPosition({
          left: startLeft + deltaX,
          top: startTop + deltaY,
        }),
      );
    };
    const handleUp = () => {
      window.removeEventListener("mousemove", handleMove);
      if (moved) {
        dragGraceTimer.current = window.setTimeout(() => {
          wasDraggingRef.current = false;
        }, 140);
      }
    };

    window.addEventListener("mousemove", handleMove);
    window.addEventListener("mouseup", handleUp, { once: true });
  };

  return (
    <motion.div
      className={`fixed z-40 border bg-white/84 shadow-[0_20px_70px_rgba(59,91,180,0.18)] backdrop-blur-2xl ${
        isOpen ? "" : "cursor-grab active:cursor-grabbing"
      } ${isOpen ? "overflow-visible" : "overflow-hidden"}`}
      style={{ maxWidth: "calc(100vw - 40px)", willChange: "transform,width,height,border-radius" }}
      animate={{
        width: isOpen ? openWidth : orbSize,
        height: isOpen ? openHeight : orbSize,
        borderRadius: isOpen ? 12 : 999,
        left: isOpen ? openLeft : closedPosition.left,
        top: isOpen ? openTop : closedPosition.top,
        x: 0,
        y: 0,
        borderColor: isOpen ? "rgba(228,228,231,0.9)" : "rgba(255,255,255,0.78)",
        boxShadow: isOpen
          ? "0 20px 70px rgba(59,91,180,0.18)"
          : "0 18px 56px rgba(59,91,180,0.22)",
        backgroundColor: isOpen ? "rgba(255,255,255,0.84)" : "rgba(255,255,255,0.58)",
      }}
      transition={iosSpring}
      onPointerDown={beginOrbDrag}
      onPointerMove={moveOrb}
      onPointerUp={endOrbDrag}
      onPointerCancel={endOrbDrag}
      onMouseDown={beginOrbMouseDrag}
      onClick={() => {
        const recentlyDragged = performance.now() - lastDragAtRef.current < 180;
        if (!isOpen && !recentlyDragged) {
          onOpen();
        }
        wasDraggingRef.current = false;
      }}
      role={isOpen ? "dialog" : "button"}
      aria-label={isOpen ? "Question composer" : "Open question composer"}
    >
      <motion.div
        className="absolute inset-0 flex flex-col"
        animate={{ opacity: isOpen ? 1 : 0, scale: isOpen ? 1 : 0.92, filter: isOpen ? "blur(0px)" : "blur(2px)" }}
        transition={{ duration: isOpen ? 0.18 : 0.1, ease: [0.25, 0.1, 0.25, 1] }}
        style={{ pointerEvents: isOpen ? "auto" : "none" }}
      >
        <div className="flex min-h-[72px] items-center gap-3 px-5">
          <input
            value={query}
            disabled={!hasUploaded}
            onChange={(event) => onQueryChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") onSubmit();
            }}
            className="min-w-0 flex-1 border-0 bg-transparent text-[20px] text-zinc-800 outline-none placeholder:text-zinc-400 disabled:cursor-not-allowed disabled:text-zinc-400"
            placeholder={hasUploaded ? "Ask a follow-up question" : "Upload evidence before asking"}
          />
        </div>
        <div className="flex h-[58px] items-center justify-between border-t border-zinc-200 px-5">
          <div className="relative">
            <button
              type="button"
              className="group inline-flex h-10 items-center gap-2 rounded-full border border-zinc-200/80 bg-white/70 px-3 text-sm font-medium text-zinc-600 shadow-sm backdrop-blur transition hover:border-blue-200 hover:bg-blue-50/40"
              onClick={(event) => {
                event.stopPropagation();
                setIsModelMenuOpen((current) => !current);
              }}
            >
            <Zap size={18} />
            <span className="text-zinc-500">Model</span>
            <span className="inline-flex items-center gap-1">
              <span className="text-sm font-semibold text-zinc-800 transition group-hover:text-[#246be8]">
                {model}
              </span>
              <ChevronDown
                size={15}
                className={`text-zinc-400 transition group-hover:text-[#246be8] ${
                  isModelMenuOpen ? "rotate-180" : ""
                }`}
              />
            </span>
            </button>

            <AnimatePresence>
              {isModelMenuOpen ? (
                <motion.div
                  className="absolute bottom-12 left-0 w-[210px] overflow-hidden rounded-xl border border-zinc-200 bg-white p-1.5 shadow-[0_18px_42px_rgba(36,48,64,0.18)] ring-1 ring-white"
                  initial={{ opacity: 0, y: 8, scale: 0.96 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 8, scale: 0.96 }}
                  transition={{ duration: 0.16, ease: [0.25, 0.1, 0.25, 1] }}
                  onClick={(event) => event.stopPropagation()}
                >
                  {models.map((item) => {
                    const active = item === model;
                    return (
                      <button
                        key={item}
                        type="button"
                        className={`flex h-10 w-full items-center justify-between rounded-lg px-3 text-left text-sm font-medium transition ${
                          active
                            ? "bg-[#eef4ff] text-[#246be8]"
                            : "text-zinc-700 hover:bg-[#f7f9fc] hover:text-zinc-950"
                        }`}
                        onClick={() => {
                          onModelChange(item);
                          setIsModelMenuOpen(false);
                        }}
                      >
                        <span>{item}</span>
                        {active ? <CheckCircle2 size={16} /> : null}
                      </button>
                    );
                  })}
                </motion.div>
              ) : null}
            </AnimatePresence>
          </div>
          <button
            className="grid h-10 w-10 place-items-center rounded-full bg-zinc-100 text-zinc-400 transition hover:bg-[#3178f6] hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
            disabled={!hasUploaded || isThinking}
            onClick={onSubmit}
          >
            {isThinking ? (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-zinc-300 border-t-[#3178f6]" />
            ) : (
              <ArrowRight size={20} />
            )}
          </button>
        </div>
      </motion.div>

      <motion.div
        className="absolute inset-0 grid place-items-center"
        animate={{ opacity: isOpen ? 0 : 1, scale: isOpen ? 0.76 : 1 }}
        transition={{ duration: isOpen ? 0.1 : 0.18, ease: [0.25, 0.1, 0.25, 1] }}
        style={{ pointerEvents: isOpen ? "none" : "auto" }}
      >
        {!isOpen ? (
          <motion.span
            className="absolute inset-0 rounded-full border border-[#3178f6]/18 bg-[#dbeafe]/28"
            animate={{ scale: [1, 1.18, 1], opacity: [0.3, 0, 0.3] }}
            transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
          />
        ) : null}
        <ProjectLogoMark compact />
      </motion.div>
    </motion.div>
  );
}

export default App;
