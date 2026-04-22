"use client";

import { BarChart3, DatabaseZap, FilePlus2, FileStack, Filter, LoaderCircle, Trash2 } from "lucide-react";

import { formatBytes, formatDateTime } from "@/lib/utils";
import { DocumentSummary, HealthResponse } from "@/types";
import { ThemeToggle } from "./theme-toggle";


interface SidebarProps {
  documents: DocumentSummary[];
  health: HealthResponse | null;
  selectedDocumentIds: string[];
  activeDocumentId: string | null;
  isUploading: boolean;
  isIndexing: boolean;
  onUpload: (files: File[]) => void;
  onToggleDocument: (documentId: string) => void;
  onSetActiveDocument: (documentId: string) => void;
  onIndex: () => void;
  onDeleteDocument: (documentId: string) => void;
}


export function Sidebar({
  documents,
  health,
  selectedDocumentIds,
  activeDocumentId,
  isUploading,
  isIndexing,
  onUpload,
  onToggleDocument,
  onSetActiveDocument,
  onIndex,
  onDeleteDocument,
}: SidebarProps) {
  const selectedDocument = documents.find((document) => document.id === activeDocumentId) ?? null;

  return (
    <aside className="panel flex flex-col rounded-[2rem] p-5 lg:sticky lg:top-6 lg:h-[calc(100vh-3rem)] lg:overflow-hidden">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full bg-[rgb(var(--accent-soft))] px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-[rgb(var(--accent))]">
            <DatabaseZap className="h-3.5 w-3.5" />
            Vectorless RAG
          </div>
          <h1 className="mt-4 text-2xl font-semibold tracking-tight">Structured retrieval studio</h1>
          <p className="mt-2 text-sm leading-6 text-[rgb(var(--muted))]">
            Upload files, build lexical indexes, and inspect grounded evidence without a vector database.
          </p>
        </div>
        <ThemeToggle />
      </div>

      <label className="mt-6 flex cursor-pointer items-center justify-center gap-2 rounded-2xl bg-[rgb(var(--text))] px-4 py-3 text-sm font-semibold text-white transition hover:-translate-y-0.5">
        {isUploading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <FilePlus2 className="h-4 w-4" />}
        {isUploading ? "Uploading..." : "Upload documents"}
        <input
          hidden
          type="file"
          accept=".pdf,.txt,.md"
          multiple
          onChange={(event) => {
            const files = Array.from(event.target.files ?? []);
            if (files.length) onUpload(files);
            event.currentTarget.value = "";
          }}
        />
      </label>

      <button
        className="mt-3 flex w-full items-center justify-center gap-2 rounded-2xl border border-[rgb(var(--border))] bg-white/60 px-4 py-3 text-sm font-semibold transition hover:-translate-y-0.5 dark:bg-white/5"
        onClick={onIndex}
        disabled={isIndexing || !documents.length}
        type="button"
      >
        {isIndexing ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <BarChart3 className="h-4 w-4" />}
        {isIndexing ? "Building index..." : "Rebuild lexical index"}
      </button>

      <div className="mt-5 grid grid-cols-3 gap-3">
        <div className="panel-soft rounded-2xl p-3">
          <p className="text-xs uppercase tracking-[0.2em] text-[rgb(var(--muted))]">Docs</p>
          <p className="mt-2 text-lg font-semibold">{health?.documents ?? 0}</p>
        </div>
        <div className="panel-soft rounded-2xl p-3">
          <p className="text-xs uppercase tracking-[0.2em] text-[rgb(var(--muted))]">Pages</p>
          <p className="mt-2 text-lg font-semibold">{health?.pages ?? 0}</p>
        </div>
        <div className="panel-soft rounded-2xl p-3">
          <p className="text-xs uppercase tracking-[0.2em] text-[rgb(var(--muted))]">Ready</p>
          <p className="mt-2 text-lg font-semibold">{health?.index_ready ? "Yes" : "No"}</p>
        </div>
      </div>

      <div className="mt-6 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-[rgb(var(--muted))]">
        <Filter className="h-3.5 w-3.5" />
        Retrieval filters
      </div>
      <p className="mt-2 text-sm text-[rgb(var(--muted))]">
        {selectedDocumentIds.length
          ? `${selectedDocumentIds.length} document filter${selectedDocumentIds.length > 1 ? "s" : ""} active`
          : "No filter applied. Queries search every indexed document."}
      </p>

      <div className="mt-5 flex-1 space-y-3 overflow-y-auto pr-1 scrollbar-thin">
        {documents.length ? (
          documents.map((document) => {
            const isSelected = selectedDocumentIds.includes(document.id);
            const isActive = activeDocumentId === document.id;
            return (
              <div
                key={document.id}
                className={`rounded-3xl border p-4 transition ${isActive ? "border-[rgb(var(--accent))] bg-[rgb(var(--accent-soft))]/60" : "border-[rgb(var(--border))] bg-white/60 dark:bg-white/5"}`}
              >
                <div className="flex items-start justify-between gap-2">
                  <button
                    type="button"
                    className="flex-1 text-left"
                    onClick={() => onSetActiveDocument(document.id)}
                  >
                    <p className="text-sm font-semibold">{document.title}</p>
                    <p className="mt-1 text-xs text-[rgb(var(--muted))]">{document.filename}</p>
                  </button>
                  <button
                    type="button"
                    className="rounded-full border border-[rgb(var(--border))] p-2 text-[rgb(var(--muted))] transition hover:text-rose-500"
                    onClick={() => onDeleteDocument(document.id)}
                    aria-label={`Delete ${document.filename}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>

                <div className="mt-3 flex flex-wrap gap-2 text-xs">
                  <span className="rounded-full bg-white/80 px-2.5 py-1 dark:bg-white/10">{document.file_type.toUpperCase()}</span>
                  <span className="rounded-full bg-white/80 px-2.5 py-1 dark:bg-white/10">{document.page_count} pages</span>
                  <span className="rounded-full bg-white/80 px-2.5 py-1 dark:bg-white/10">{document.section_count} sections</span>
                </div>

                <div className="mt-3 flex items-center justify-between">
                  <label className="flex items-center gap-2 text-sm text-[rgb(var(--muted))]">
                    <input
                      checked={isSelected}
                      onChange={() => onToggleDocument(document.id)}
                      type="checkbox"
                      className="h-4 w-4 rounded border-[rgb(var(--border))]"
                    />
                    Filter in search
                  </label>
                  <span className="rounded-full bg-white/80 px-2.5 py-1 text-xs font-medium capitalize dark:bg-white/10">
                    {document.indexing_status}
                  </span>
                </div>
              </div>
            );
          })
        ) : (
          <div className="panel-soft rounded-3xl p-5 text-sm text-[rgb(var(--muted))]">
            <FileStack className="mb-3 h-5 w-5" />
            No documents yet. Upload a PDF, TXT, or MD file to start building a page-aware lexical index.
          </div>
        )}
      </div>

      {selectedDocument ? (
        <div className="panel-soft mt-5 rounded-3xl p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[rgb(var(--muted))]">Selected document</p>
          <p className="mt-2 text-base font-semibold">{selectedDocument.title}</p>
          <p className="mt-1 text-sm text-[rgb(var(--muted))]">{selectedDocument.filename}</p>
          <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-[rgb(var(--muted))]">Size</p>
              <p className="font-medium">{formatBytes(selectedDocument.size_bytes)}</p>
            </div>
            <div>
              <p className="text-[rgb(var(--muted))]">Indexed</p>
              <p className="font-medium">{formatDateTime(selectedDocument.last_indexed_at)}</p>
            </div>
          </div>
        </div>
      ) : null}
    </aside>
  );
}
