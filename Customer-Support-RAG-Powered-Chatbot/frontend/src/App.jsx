import { useState, useRef, useEffect, useCallback } from "react";
import {
  Home, Users, Folder, Tag, Settings, ChevronDown,
  Grid3X3, List, Plus, Search, Send, Upload,
  FileText, Mic, Bot, Loader2, X, GitBranch,
  Code2, BookOpen, Megaphone, Zap, AlertCircle,
  Mail, Shield, Database, Cpu, Server, Palette,
} from "lucide-react";

/* ═══════════════════════════════════════════════════════════ *
 *  CONSTANTS & STATIC DATA
 * ═══════════════════════════════════════════════════════════ */

const API_BASE = "http://localhost:8000";

/** File extension → badge CSS class */
const BADGE_CLASS = {
  PDF: "badge-pdf", MD: "badge-md", CSV: "badge-csv",
  DOCX: "badge-docx", TXT: "badge-txt",
};

/** CoreAI team members */
const TEAM_MEMBERS = [
  {
    id: 1, name: "Mariam Ahmed",  initials: "MA",
    role: "Full-Stack & AI Engineer",      squad: "Backend, Frontend & AI Squad",
    color: "from-violet-500 to-indigo-600", icon: Palette,
  },
  {
    id: 2, name: "Rahma Mahmoud", initials: "RM",
    role: "Backend & AI Engineer",         squad: "Backend, Frontend & AI Squad",
    color: "from-sky-500 to-cyan-600",      icon: Server,
  },
  {
    id: 3, name: "Basmala Ahmed", initials: "BA",
    role: "AI Engineer / Workflow Architect", squad: "AI Engine Squad",
    color: "from-emerald-500 to-teal-600",  icon: Cpu,
  },
  {
    id: 4, name: "Sara Zaki",     initials: "SZ",
    role: "Data & Vector Store Specialist", squad: "Data & Vector Store Squad",
    color: "from-rose-500 to-pink-600",     icon: Database,
  },
  {
    id: 5, name: "Aya Mahmoud",   initials: "AM",
    role: "AI Research Scientist",         squad: "AI Engine Squad",
    color: "from-amber-500 to-orange-500",  icon: Zap,
  },
  {
    id: 6, name: "Lojain",        initials: "LJ",
    role: "Data Engineer / Embedding Expert", squad: "Data & Vector Store Squad",
    color: "from-fuchsia-500 to-purple-600", icon: Cpu,
  },
];

/** Initial knowledge base documents */
const INITIAL_DOCS = [
  {
    id: 1, name: "Company_HR_Policy.pdf", ext: "PDF",
    size: "2.4 MB", date: "Jun 28, 2026", status: "indexed",
    prompt: "What is the company's policy on remote work hours and flexible schedules?",
  },
  {
    id: 2, name: "Client_Project_Scope.md", ext: "MD",
    size: "156 KB", date: "Jun 27, 2026", status: "indexed",
    prompt: "What are the key deliverables and milestones in the client project scope?",
  },
  {
    id: 3, name: "customer_support_data.csv", ext: "CSV",
    size: "18.4 MB", date: "Jun 26, 2026", status: "indexed",
    prompt: "What are the most frequent customer support issues found in the dataset?",
  },
  {
    id: 4, name: "RAG_Architecture_Guide.docx", ext: "DOCX",
    size: "890 KB", date: "Jun 25, 2026", status: "processing",
    prompt: "Can you summarize the RAG architecture and retrieval methodology?",
  },
  {
    id: 5, name: "Onboarding_Checklist.txt", ext: "TXT",
    size: "42 KB", date: "Jun 24, 2026", status: "indexed",
    prompt: "What are the key steps in the employee onboarding checklist?",
  },
];

/** Mock bot responses for offline simulation */
const MOCK_RESPONSES = [
  {
    response: "Based on Company_HR_Policy.pdf, remote work core hours are 10:00 AM – 4:00 PM local time. Flexible arrangements beyond these hours require manager approval on a case-by-case basis.",
    sources: [{ instruction: "Company_HR_Policy.pdf", similarity: 96.2 }],
  },
  {
    response: "According to Client_Project_Scope.md, the primary deliverables include: (1) Completed RAG pipeline, (2) FastAPI backend with semantic search endpoints, and (3) a production-ready React frontend. Final milestone is integration testing in Q3 2026.",
    sources: [{ instruction: "Client_Project_Scope.md", similarity: 94.7 }],
  },
  {
    response: "The customer support dataset contains 27,000+ Q&A pairs across 11 categories including Refunds, Shipping, Account, Orders, and Payments. The most frequent issue is 'Order Status Inquiry' at 23.4% of all tickets.",
    sources: [{ instruction: "customer_support_data.csv", similarity: 88.3 }],
  },
  {
    response: "The RAG architecture uses a two-stage pipeline: (1) Semantic retrieval via ChromaDB with all-MiniLM-L6-v2 embeddings, and (2) LLM generation using Llama 3 (8B) via Groq API. Candidates below 0.25 cosine similarity threshold are filtered before context injection.",
    sources: [{ instruction: "RAG_Architecture_Guide.docx", similarity: 91.5 }],
  },
];

/** Format raw bytes to human-readable size */
function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Pick a random mock response */
const pickMock = () => MOCK_RESPONSES[Math.floor(Math.random() * MOCK_RESPONSES.length)];

/** Derive file extension from filename */
function getExt(name) {
  const parts = name.split(".");
  return parts.length > 1 ? parts[parts.length - 1].toUpperCase() : "TXT";
}

/** Today's date formatted nicely */
function todayLabel() {
  return new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

/* ═══════════════════════════════════════════════════════════ *
 *  REUSABLE PRIMITIVES
 * ═══════════════════════════════════════════════════════════ */

/** macOS-style window control dots */
function WindowControls() {
  return (
    <div className="flex items-center gap-1.5 shrink-0">
      <span className="os-dot os-dot-red"    title="Close"    />
      <span className="os-dot os-dot-yellow" title="Minimize" />
      <span className="os-dot os-dot-green"  title="Maximize" />
    </div>
  );
}

/** Sidebar navigation item — highlights when active */
function NavItem({ icon: Icon, label, active, onClick }) {
  return (
    <button
      className={`nav-item w-full text-left ${active ? "active" : ""}`}
      onClick={onClick}
    >
      <Icon size={15} strokeWidth={active ? 2.3 : 1.8} />
      <span>{label}</span>
    </button>
  );
}

/** Animated "Bot is thinking" indicator */
function TypingIndicator() {
  return (
    <div className="flex items-start gap-2.5">
      <div
        className="avatar-sm shrink-0 flex items-center justify-center"
        style={{ background: "linear-gradient(135deg,#6366f1,#8b5cf6)" }}
      >
        <Bot size={11} color="white" />
      </div>
      <div>
        <p className="text-[10px] font-bold tracking-widest text-gray-400 mb-1 uppercase">
          AI ASSISTANT
        </p>
        <div className="chat-bubble-bot flex items-center gap-1.5 py-3 px-4">
          <span className="text-xs text-gray-400 italic mr-1">Assistant is thinking</span>
          <div className="typing-dots flex items-center gap-1">
            <span /><span /><span />
          </div>
        </div>
      </div>
    </div>
  );
}

/** A single chat message bubble */
function ChatMessage({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex items-start gap-2.5 ${isUser ? "flex-row-reverse" : ""}`}>
      {/* Avatar */}
      <div
        className="avatar-sm shrink-0 flex items-center justify-center"
        style={{
          background: isUser
            ? "linear-gradient(135deg,#1f2937,#374151)"
            : "linear-gradient(135deg,#6366f1,#8b5cf6)",
        }}
      >
        {isUser
          ? <span style={{ fontSize: 9, fontWeight: 700, color: "white" }}>MT</span>
          : <Bot size={11} color="white" />}
      </div>

      {/* Content */}
      <div className={`flex flex-col gap-1 ${isUser ? "items-end" : "items-start"}`}>
        <p className={`text-[10px] font-bold tracking-widest text-gray-400 uppercase ${isUser ? "text-right" : ""}`}>
          {isUser ? "YOU" : "AI ASSISTANT"}
        </p>
        <div
          className={isUser ? "chat-bubble-user" : "chat-bubble-bot"}
          style={{ whiteSpace: "pre-wrap", wordBreak: "break-word", lineHeight: "1.65" }}
        >
          {msg.text}
        </div>
        {/* Source citation */}
        {!isUser && msg.sources?.length > 0 && (
          <p className="text-[10px] text-gray-400 mt-0.5 px-1">
            Source Match:{" "}
            <span className="font-semibold text-indigo-500">{msg.sources[0].similarity.toFixed(1)}%</span>
            {" | Ref: "}
            <span className="font-medium text-gray-500">{msg.sources[0].instruction}</span>
          </p>
        )}
      </div>
    </div>
  );
}

/** File extension badge */
function FileBadge({ ext }) {
  return (
    <div className={`file-badge ${BADGE_CLASS[ext] ?? "badge-txt"}`}>{ext}</div>
  );
}

/** Status pill */
function StatusPill({ status }) {
  return status === "indexed"
    ? <span className="pill-indexed">● Indexed</span>
    : <span className="pill-processing">● Processing</span>;
}

/* ═══════════════════════════════════════════════════════════ *
 *  PLACEHOLDER VIEWS (Design System, Docs, Components, etc.)
 * ═══════════════════════════════════════════════════════════ */

function PlaceholderView({ icon: Icon, title, description, accent = "#6366f1" }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center py-20 px-8 text-center">
      <div
        className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4 shadow-md"
        style={{ background: `linear-gradient(135deg, ${accent}22, ${accent}44)` }}
      >
        <Icon size={30} style={{ color: accent }} strokeWidth={1.6} />
      </div>
      <h3 className="text-lg font-bold text-gray-800 mb-1">{title}</h3>
      <p className="text-sm text-gray-400 max-w-xs leading-relaxed">{description}</p>
      <button
        className="btn-dark mt-6"
        style={{ background: accent }}
        onClick={() => {}}
      >
        <Plus size={14} /> Get Started
      </button>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════ *
 *  TEAM VIEW — CoreAI Team Members
 * ═══════════════════════════════════════════════════════════ */

function TeamView() {
  return (
    <div className="flex-1 overflow-y-auto px-5 pb-6">
      {/* Header */}
      <div className="py-5 border-b border-gray-100 mb-5">
        <h2 className="text-xl font-bold text-gray-900 leading-tight">CoreAI Team Members</h2>
        <p className="text-sm text-gray-400 mt-1">
          The 6-member engineering squad building the RAG-Powered Customer Support Chatbot.
        </p>
      </div>

      {/* Team grid */}
      <div className="grid grid-cols-2 gap-4">
        {TEAM_MEMBERS.map((member) => {
          const RoleIcon = member.icon;
          return (
            <div
              key={member.id}
              className="group relative bg-white border border-gray-100 rounded-2xl p-5
                         shadow-sm hover:shadow-md hover:-translate-y-0.5
                         transition-all duration-200 overflow-hidden cursor-pointer"
            >
              {/* Subtle gradient strip at top */}
              <div
                className={`absolute inset-x-0 top-0 h-1 rounded-t-2xl bg-gradient-to-r ${member.color}`}
              />

              {/* Avatar */}
              <div className="flex flex-col items-center text-center mt-2">
                <div
                  className={`w-16 h-16 rounded-full bg-gradient-to-br ${member.color}
                              flex items-center justify-center mb-3 ring-4 ring-white shadow-md`}
                >
                  <span className="text-xl font-bold text-white tracking-tight">
                    {member.initials}
                  </span>
                </div>

                {/* Name */}
                <h4 className="text-sm font-bold text-gray-900 leading-tight mb-0.5">
                  {member.name}
                </h4>

                {/* Role chip */}
                <div
                  className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full
                             text-[10.5px] font-semibold mt-1"
                  style={{
                    background: `linear-gradient(135deg, ${member.color.includes("violet") ? "#ede9fe" :
                      member.color.includes("sky") ? "#e0f2fe" :
                      member.color.includes("emerald") ? "#d1fae5" :
                      member.color.includes("rose") ? "#ffe4e6" :
                      member.color.includes("amber") ? "#fef3c7" : "#fae8ff"})`,
                    color: member.color.includes("violet") ? "#7c3aed" :
                      member.color.includes("sky") ? "#0369a1" :
                      member.color.includes("emerald") ? "#065f46" :
                      member.color.includes("rose") ? "#be123c" :
                      member.color.includes("amber") ? "#92400e" : "#86198f",
                  }}
                >
                  <RoleIcon size={10} strokeWidth={2.2} />
                  {member.role}
                </div>

                {/* Squad label */}
                <p className="text-[10px] text-gray-400 mt-1.5 leading-snug">
                  {member.squad}
                </p>
              </div>

              {/* Action row */}
              <div className="flex items-center justify-center gap-2 mt-4 pt-3 border-t border-gray-100">
                <button
                  className="flex items-center gap-1 text-[10.5px] font-medium text-gray-400
                             hover:text-indigo-600 transition-colors"
                >
                  <Mail size={11} strokeWidth={2} /> Message
                </button>
                <span className="text-gray-200">|</span>
                <button
                  className="flex items-center gap-1 text-[10.5px] font-medium text-gray-400
                             hover:text-indigo-600 transition-colors"
                >
                  <GitBranch size={11} strokeWidth={2} /> Profile
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Squad summary cards */}
      <div className="mt-6 grid grid-cols-1 gap-3">
        {[
          { label: "AI Engine Squad",                    members: "Aya Mahmoud & Basmala Ahmed", color: "#6366f1", desc: "LangGraph • Groq API • Llama 3 (8B)" },
          { label: "Data & Vector Store Squad",           members: "Sara Zaki & Lojain",          color: "#10b981", desc: "ChromaDB • Pandas • all-MiniLM-L6-v2 Embeddings" },
          { label: "Backend, Frontend & AI Squad",        members: "Mariam Ahmed & Rahma Mahmoud", color: "#f59e0b", desc: "FastAPI • React • PySide6 • QThread • Core AI Orchestration" },
        ].map((squad) => (
          <div
            key={squad.label}
            className="flex items-start gap-3 bg-white border border-gray-100 rounded-xl px-4 py-3 shadow-sm"
          >
            <div
              className="w-2 self-stretch rounded-full shrink-0"
              style={{ background: squad.color }}
            />
            <div>
              <p className="text-xs font-bold text-gray-800">{squad.label}</p>
              <p className="text-[10.5px] text-gray-500 mt-0.5">{squad.members}</p>
              <p className="text-[10px] text-gray-400 mt-0.5">{squad.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════ *
 *  SETTINGS VIEW
 * ═══════════════════════════════════════════════════════════ */

function SettingsView() {
  const [apiKey, setApiKey]   = useState("");
  const [model, setModel]     = useState("llama3-8b-8192");
  const [topK, setTopK]       = useState(5);
  const [saved, setSaved]     = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="flex-1 overflow-y-auto px-5 pb-6">
      <div className="py-5 border-b border-gray-100 mb-5">
        <h2 className="text-xl font-bold text-gray-900">System Settings</h2>
        <p className="text-sm text-gray-400 mt-1">Configure your RAG pipeline and API credentials.</p>
      </div>

      <div className="space-y-5">
        {/* API Key */}
        <div className="bg-white border border-gray-100 rounded-xl p-4 shadow-sm">
          <label className="block text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">
            Groq API Key
          </label>
          <input
            type="password"
            placeholder="gsk_••••••••••••••••••••"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm
                       focus:outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-200
                       bg-gray-50 text-gray-800 font-mono"
          />
        </div>

        {/* Model selection */}
        <div className="bg-white border border-gray-100 rounded-xl p-4 shadow-sm">
          <label className="block text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">
            LLM Model
          </label>
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm
                       focus:outline-none focus:border-indigo-400 bg-gray-50 text-gray-800"
          >
            <option value="llama3-8b-8192">Llama 3 (8B) — Fast</option>
            <option value="llama-3.3-70b-versatile">Llama 3.3 (70B) — Versatile</option>
            <option value="mixtral-8x7b-32768">Mixtral 8×7B — High Context</option>
          </select>
        </div>

        {/* Top-K slider */}
        <div className="bg-white border border-gray-100 rounded-xl p-4 shadow-sm">
          <label className="block text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">
            Retrieval Top-K: <span className="text-indigo-600">{topK}</span>
          </label>
          <input
            type="range" min={1} max={20} value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="w-full accent-indigo-500"
          />
          <div className="flex justify-between text-[10px] text-gray-400 mt-1">
            <span>1 (Precise)</span><span>20 (Broad)</span>
          </div>
        </div>

        {/* Backend status */}
        <div className="bg-white border border-gray-100 rounded-xl p-4 shadow-sm">
          <p className="text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">Backend Status</p>
          <div className="flex items-center gap-2">
            <span className="pulse-dot" />
            <span className="text-sm text-gray-600 font-medium">FastAPI — localhost:8000</span>
          </div>
        </div>

        {/* Save button */}
        <button
          onClick={handleSave}
          className="btn-dark w-full justify-center py-3 rounded-xl text-sm"
        >
          {saved ? "✓ Settings Saved!" : "Save Configuration"}
        </button>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════ *
 *  KNOWLEDGE BASE / HOME VIEW (center pane content)
 * ═══════════════════════════════════════════════════════════ */

function KnowledgeView({ docs, setDocs, onDocumentSelect }) {
  const [isUploading, setIsUploading] = useState(false);
  const [isDragOver, setIsDragOver]   = useState(false);
  const [viewMode, setViewMode]       = useState("list");
  const [searchQuery, setSearchQuery] = useState("");
  const fileInputRef = useRef(null);

  /** Process an uploaded File object */
  const processFile = useCallback((file) => {
    if (!file) return;
    setIsUploading(true);

    setTimeout(() => {
      const ext = getExt(file.name);
      setDocs((prev) => [
        {
          id: Date.now(),
          name: file.name,
          ext,
          size: formatBytes(file.size),
          date: todayLabel(),
          status: "processing",
          prompt: `What are the key details inside ${file.name}?`,
        },
        ...prev,
      ]);
      setIsUploading(false);

      // Simulate transition to "indexed" after 3 seconds
      setTimeout(() => {
        setDocs((prev) =>
          prev.map((d) => d.name === file.name ? { ...d, status: "indexed" } : d)
        );
      }, 3000);
    }, 1800);
  }, [setDocs]);

  /** Hidden file input onChange */
  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
    e.target.value = ""; // allow re-upload of same file
  };

  /** Drag events */
  const onDragOver  = (e) => { e.preventDefault(); setIsDragOver(true); };
  const onDragLeave = ()  => setIsDragOver(false);
  const onDrop      = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) processFile(file);
  };

  const filtered = docs.filter((d) =>
    d.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <>
      {/* Hidden file input — triggered by dropzone and Add New */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.txt,.md,.docx,.csv"
        className="hidden"
        onChange={handleFileChange}
      />

      {/* ── Header ── */}
      <div className="px-5 pt-4 pb-3 border-b border-gray-100 shrink-0">
        <p className="text-[11px] text-gray-400 font-medium mb-1">
          Home <span className="mx-1 text-gray-300">›</span>
          <span className="text-gray-600">Knowledge Base</span>
        </p>
        <h2 className="text-xl font-bold text-gray-900 leading-tight">Upload Knowledge</h2>
      </div>

      {/* ── Dropzone ── */}
      <div className="px-5 pt-4 pb-3 shrink-0">
        <div
          className={`dropzone flex flex-col items-center justify-center py-6 px-4 text-center
                      cursor-pointer transition-all duration-200
                      ${isDragOver ? "drag-over" : ""}`}
          onClick={() => !isUploading && fileInputRef.current?.click()}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
        >
          {isUploading ? (
            <>
              <Loader2 size={26} className="text-indigo-500 mb-2 animate-spin" />
              <p className="text-sm font-semibold text-gray-700">Indexing document…</p>
              <p className="text-xs text-gray-400 mt-0.5">Processing embeddings</p>
            </>
          ) : (
            <>
              <Upload size={26} className="text-gray-400 mb-2" strokeWidth={1.5} />
              <p className="text-sm font-semibold text-gray-700">
                Click to upload or drag and drop
              </p>
              <p className="text-xs text-gray-400 mt-0.5">PDF, TXT, MD, DOCX — up to 10 MB</p>
            </>
          )}
        </div>
      </div>

      {/* ── Controls Row ── */}
      <div className="flex items-center justify-between px-5 pb-2 shrink-0">
        <span className="text-xs font-bold text-gray-700 uppercase tracking-wide">
          Knowledge Base
        </span>
        <div className="flex items-center gap-2">
          <button
            title="Grid view"
            onClick={() => setViewMode("grid")}
            className={`p-1 rounded transition-colors ${viewMode === "grid" ? "text-gray-800 bg-gray-100" : "text-gray-400 hover:text-gray-600"}`}
          >
            <Grid3X3 size={14} />
          </button>
          <button
            title="List view"
            onClick={() => setViewMode("list")}
            className={`p-1 rounded transition-colors ${viewMode === "list" ? "text-gray-800 bg-gray-100" : "text-gray-400 hover:text-gray-600"}`}
          >
            <List size={14} />
          </button>
          <button
            className="btn-dark"
            onClick={() => !isUploading && fileInputRef.current?.click()}
            disabled={isUploading}
          >
            <Plus size={13} /> Add New
          </button>
        </div>
      </div>

      {/* ── Search ── */}
      <div className="px-5 pb-3 shrink-0">
        <div className="search-bar">
          <Search size={12} className="text-gray-400 shrink-0" />
          <input
            placeholder="Filter documents…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery("")}>
              <X size={12} className="text-gray-400 hover:text-gray-600" />
            </button>
          )}
        </div>
      </div>

      {/* ── Document List ── */}
      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-0.5">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <FileText size={30} className="text-gray-300 mb-2" strokeWidth={1.5} />
            <p className="text-sm text-gray-400">No documents match your filter.</p>
          </div>
        ) : (
          filtered.map((doc) => (
            <div
              key={doc.id}
              className="file-row"
              onClick={() => onDocumentSelect(doc)}
            >
              <div className={`file-badge ${BADGE_CLASS[doc.ext] ?? "badge-txt"}`}>
                {doc.ext}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">{doc.name}</p>
                <p className="text-[10.5px] text-gray-400">{doc.size} · {doc.date}</p>
              </div>
              <StatusPill status={doc.status} />
            </div>
          ))
        )}
      </div>
    </>
  );
}

/* ═══════════════════════════════════════════════════════════ *
 *  PANE 1 — WORKSPACE SIDEBAR
 * ═══════════════════════════════════════════════════════════ */

function SidebarPane({ activeTab, setActiveTab }) {
  const NAV_GROUPS = [
    {
      label: "WORKSPACE",
      items: [
        { icon: Home,          label: "Home",          id: "home" },
        { icon: Users,         label: "Team",          id: "team" },
      ],
    },
    {
      label: "PROJECTS",
      items: [
        { icon: Palette,       label: "Design System", id: "design" },
        { icon: BookOpen,      label: "Documentation", id: "documentation" },
        { icon: Code2,         label: "Components",    id: "components" },
        { icon: Megaphone,     label: "Marketing",     id: "marketing" },
      ],
    },
    {
      label: "TAGS",
      items: [
        { icon: Tag,           label: "Urgent",        id: "urgent" },
        { icon: Tag,           label: "Reviewed",      id: "reviewed" },
      ],
    },
  ];

  return (
    <aside
      className="flex flex-col border-r border-gray-100 shrink-0"
      style={{ width: "22%", background: "#FAFAFA" }}
    >
      {/* Window controls */}
      <div className="flex items-center gap-3 px-4 pt-4 pb-3">
        <WindowControls />
      </div>

      {/* ── Profile / Workspace header ── */}
      <div className="mx-3 mb-3 px-3 py-2.5 bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="flex items-center gap-2.5">
          <div className="avatar text-sm shrink-0">CA</div>
          <div className="flex-1 min-w-0">
            {/* ★ IDENTITY CHANGE: "CoreAI Team" */}
            <p className="text-sm font-bold text-gray-900 leading-tight truncate tracking-tight">
              CoreAI Team
            </p>
            <span className="text-[10px] font-semibold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded-full">
              Admin Workspace
            </span>
          </div>
          <ChevronDown size={14} className="text-gray-400 shrink-0" />
        </div>
      </div>

      {/* Search */}
      <div className="mx-3 mb-3">
        <div className="search-bar">
          <Search size={13} className="text-gray-400 shrink-0" />
          <input placeholder="Search…" />
        </div>
      </div>

      {/* Navigation groups */}
      <nav className="flex-1 overflow-y-auto px-3 pb-2 space-y-4">
        {NAV_GROUPS.map((group) => (
          <div key={group.label}>
            <p className="text-[10px] font-bold tracking-widest text-gray-400 mb-1.5 px-2 uppercase">
              {group.label}
            </p>
            <div className="space-y-0.5">
              {group.items.map((item) => (
                <NavItem
                  key={item.id}
                  icon={item.icon}
                  label={item.label}
                  active={activeTab === item.id}
                  onClick={() => setActiveTab(item.id)}
                />
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* Bottom: Settings */}
      <div className="px-3 py-3 border-t border-gray-100">
        <NavItem
          icon={Settings}
          label="Settings"
          active={activeTab === "settings"}
          onClick={() => setActiveTab("settings")}
        />
      </div>
    </aside>
  );
}

/* ═══════════════════════════════════════════════════════════ *
 *  PANE 2 — CONTEXT-SWITCHING CENTER PANEL
 * ═══════════════════════════════════════════════════════════ */

function CenterPane({ activeTab, docs, setDocs, onDocumentSelect }) {
  const PLACEHOLDER_VIEWS = {
    design:        { icon: Palette,   title: "Design System",  accent: "#8b5cf6", description: "Manage your UI component library, color tokens, and typography guidelines." },
    documentation: { icon: BookOpen,  title: "Documentation",  accent: "#0ea5e9", description: "Browse API references, integration guides, and developer documentation." },
    components:    { icon: Code2,     title: "Components",     accent: "#10b981", description: "Explore reusable React components and layout building blocks." },
    marketing:     { icon: Megaphone, title: "Marketing",      accent: "#f59e0b", description: "Campaign assets, brand guidelines, and promotional materials." },
    urgent:        { icon: AlertCircle, title: "Urgent Tags",  accent: "#ef4444", description: "Items flagged as urgent and requiring immediate attention." },
    reviewed:      { icon: Shield,    title: "Reviewed",       accent: "#22c55e", description: "Content that has been reviewed and approved by the team." },
  };

  return (
    <section
      className="flex flex-col border-r border-gray-100 overflow-hidden"
      style={{ width: "35%", background: "white" }}
    >
      {/* ── HOME / default: Knowledge Base ── */}
      {(activeTab === "home" || activeTab === "urgent" || activeTab === "reviewed") && (
        activeTab === "home" ? (
          <KnowledgeView docs={docs} setDocs={setDocs} onDocumentSelect={onDocumentSelect} />
        ) : (
          <>
            <div className="px-5 pt-4 pb-3 border-b border-gray-100 shrink-0">
              <p className="text-[11px] text-gray-400 mb-1">Home <span className="mx-1">›</span>
                <span className="text-gray-600">{PLACEHOLDER_VIEWS[activeTab]?.title}</span>
              </p>
              <h2 className="text-xl font-bold text-gray-900">{PLACEHOLDER_VIEWS[activeTab]?.title}</h2>
            </div>
            <PlaceholderView {...PLACEHOLDER_VIEWS[activeTab]} />
          </>
        )
      )}

      {/* ── TEAM ── */}
      {activeTab === "team" && <TeamView />}

      {/* ── PROJECT SECTIONS ── */}
      {["design", "documentation", "components", "marketing"].includes(activeTab) && (
        <>
          <div className="px-5 pt-4 pb-3 border-b border-gray-100 shrink-0">
            <p className="text-[11px] text-gray-400 mb-1">
              Home <span className="mx-1">›</span>
              <span className="text-gray-600">{PLACEHOLDER_VIEWS[activeTab]?.title}</span>
            </p>
            <h2 className="text-xl font-bold text-gray-900">{PLACEHOLDER_VIEWS[activeTab]?.title}</h2>
          </div>
          <PlaceholderView {...PLACEHOLDER_VIEWS[activeTab]} />
        </>
      )}

      {/* ── SETTINGS ── */}
      {activeTab === "settings" && <SettingsView />}
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════ *
 *  PANE 3 — AI CHAT INTERFACE (always visible)
 * ═══════════════════════════════════════════════════════════ */

function ChatPane({ prefillQuery, onPrefillConsumed }) {
  const [messages, setMessages] = useState([
    {
      id: 0, role: "bot",
      text: "Hello! I'm your AI Assistant powered by FastAPI & RAG. Click any document in the Knowledge Base, or type your question below.",
      sources: [],
    },
    { id: 1, role: "user", text: "What is the policy on remote work hours?" },
    {
      id: 2, role: "bot",
      text: "Based on Company_HR_Policy.pdf, employees must maintain core hours between 10:00 AM and 4:00 PM. Flexible arrangements beyond these hours may be approved by your direct manager.",
      sources: [{ instruction: "Company_HR_Policy.pdf", similarity: 96.4 }],
    },
  ]);
  const [inputText, setInputText] = useState("");
  const [isTyping, setIsTyping]   = useState(false);
  const bottomRef   = useRef(null);
  const inputRef    = useRef(null);

  /* Auto-scroll on new messages */
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  /* Pre-fill input when a document row is clicked */
  useEffect(() => {
    if (prefillQuery) {
      setInputText(prefillQuery);
      inputRef.current?.focus();
      onPrefillConsumed();
    }
  }, [prefillQuery, onPrefillConsumed]);

  /** Send message — tries FastAPI, falls back to mock */
  const handleSend = useCallback(async () => {
    const text = inputText.trim();
    if (!text || isTyping) return;

    setMessages((prev) => [...prev, { id: Date.now(), role: "user", text }]);
    setInputText("");
    setIsTyping(true);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text, category: "ALL", top_k: 5 }),
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, role: "bot", text: data.response ?? "No response.", sources: data.sources ?? [] },
      ]);
    } catch {
      /* ── SMART OFFLINE FALLBACK ─────────────────────────────────────────────
       * The FastAPI backend is unreachable. Instead of a misleading hardcoded
       * answer, acknowledge the user's exact query and explain the situation
       * clearly, preserving the typing indicator during the wait.
       * ─────────────────────────────────────────────────────────────────────*/
      await new Promise((r) => setTimeout(r, 1600 + Math.random() * 900));
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "bot",
          text: `[Offline Mode] Your query: "${text}" was captured, but the CoreAI FastAPI server is currently unreachable.\n\nPlease ensure the backend service is running on http://localhost:8000 to process this request against the live Vector Database index.\n\nOnce the server is online, your question will be answered using the RAG pipeline with real-time document retrieval.`,
          sources: [
            {
              instruction: "Reference: System Local Network Fallback Control",
              similarity: 0.0,
            },
          ],
        },
      ]);
    }
  }, [inputText, isTyping]);

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <section className="flex flex-col" style={{ width: "43%", background: "white" }}>
      {/* Header */}
      <div className="px-5 pt-4 pb-3 border-b border-gray-100 shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-gray-900">AI Assistant</h2>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="pulse-dot" />
              <span className="text-[11.5px] font-semibold text-gray-500">
                Powered by FastAPI &amp; RAG
              </span>
            </div>
          </div>
          <Bot size={18} className="text-indigo-500" strokeWidth={1.8} />
        </div>
      </div>

      {/* Message viewport */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
        {messages.map((msg) => <ChatMessage key={msg.id} msg={msg} />)}
        {isTyping && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="px-5 pb-2 pt-2 border-t border-gray-100 shrink-0">
        <div className="chat-input-wrap">
          <Mic size={15} className="text-gray-400 shrink-0" strokeWidth={1.8} />
          <input
            ref={inputRef}
            placeholder="Ask a question about your documents..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={onKeyDown}
            disabled={isTyping}
          />
          <button
            className="send-btn"
            onClick={handleSend}
            disabled={!inputText.trim() || isTyping}
            title="Send"
          >
            <Send size={15} color="white" strokeWidth={2} />
          </button>
        </div>
        <p className="text-center text-[10.5px] text-gray-400 mt-2 pb-1">
          AI can make mistakes. Verify important information.
        </p>
      </div>
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════ *
 *  ROOT APP
 * ═══════════════════════════════════════════════════════════ */

export default function App() {
  /* ── Global navigation state ── */
  const [activeTab, setActiveTab]         = useState("home");

  /* ── Shared document list (lifted so KnowledgeView can mutate it) ── */
  const [docs, setDocs]                   = useState(INITIAL_DOCS);

  /* ── Bridge: doc click in Pane 2 → chat input in Pane 3 ── */
  const [pendingChatQuery, setPendingChatQuery] = useState(null);

  const handleDocumentSelect  = useCallback((doc) => setPendingChatQuery(doc.prompt), []);
  const handlePrefillConsumed = useCallback(() => setPendingChatQuery(null), []);

  return (
    <>
      {/* ── Animated mesh gradient canvas ── */}
      <div className="mesh-bg" aria-hidden="true">
        <div className="mesh-orb-teal" />
      </div>

      {/* ── Full-screen centered layout ── */}
      <div className="fixed inset-0 z-10 flex items-center justify-center p-6">
        <main
          className="dashboard-window w-full flex"
          style={{ maxWidth: "1200px", height: "min(780px, 92vh)" }}
        >
          {/* Pane 1 — Sidebar (always visible, drives activeTab) */}
          <SidebarPane activeTab={activeTab} setActiveTab={setActiveTab} />

          {/* Pane 2 — Context-switched center panel */}
          <CenterPane
            activeTab={activeTab}
            docs={docs}
            setDocs={setDocs}
            onDocumentSelect={handleDocumentSelect}
          />

          {/* Pane 3 — Chat (always pinned, receives doc prompts) */}
          <ChatPane
            prefillQuery={pendingChatQuery}
            onPrefillConsumed={handlePrefillConsumed}
          />
        </main>
      </div>
    </>
  );
}
