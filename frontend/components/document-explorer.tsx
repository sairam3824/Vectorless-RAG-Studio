"use client";

import { BookOpenText, Layers3, NotebookText } from "lucide-react";

import { DocumentDetail, DocumentSummary } from "@/types";


interface DocumentExplorerProps {
  documents: DocumentSummary[];
  activeDocument: DocumentDetail | null;
  isLoading: boolean;
}


export function DocumentExplorer({ documents, activeDocument, isLoading }: DocumentExplorerProps) {
  if (!documents.length) {
    return (
      <div className="panel-soft mt-5 rounded-[1.75rem] p-8 text-center text-sm text-[rgb(var(--muted))]">
        Upload a document to inspect extracted pages and sections here.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="panel-soft mt-5 rounded-[1.75rem] p-8 text-sm text-[rgb(var(--muted))]">
        Loading extracted document structure...
      </div>
    );
  }

  if (!activeDocument) {
    return (
      <div className="panel-soft mt-5 rounded-[1.75rem] p-8 text-sm text-[rgb(var(--muted))]">
        Select a document from the sidebar to browse its pages and headings.
      </div>
    );
  }

  return (
    <div className="mt-5 space-y-5 overflow-y-auto pr-1 scrollbar-thin">
      <div className="grid gap-4 md:grid-cols-3">
        <div className="panel-soft rounded-3xl p-4">
          <BookOpenText className="h-5 w-5 text-[rgb(var(--accent))]" />
          <p className="mt-3 text-sm text-[rgb(var(--muted))]">Pages</p>
          <p className="mt-1 text-2xl font-semibold">{activeDocument.page_count}</p>
        </div>
        <div className="panel-soft rounded-3xl p-4">
          <Layers3 className="h-5 w-5 text-[rgb(var(--accent))]" />
          <p className="mt-3 text-sm text-[rgb(var(--muted))]">Sections</p>
          <p className="mt-1 text-2xl font-semibold">{activeDocument.section_count}</p>
        </div>
        <div className="panel-soft rounded-3xl p-4">
          <NotebookText className="h-5 w-5 text-[rgb(var(--accent))]" />
          <p className="mt-3 text-sm text-[rgb(var(--muted))]">Status</p>
          <p className="mt-1 text-lg font-semibold capitalize">{activeDocument.indexing_status}</p>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="panel-soft rounded-[1.75rem] p-4">
          <p className="text-sm font-semibold">Section graph</p>
          <div className="mt-4 space-y-3">
            {activeDocument.sections.map((section) => (
              <div
                key={section.id}
                className="rounded-2xl border border-[rgb(var(--border))] bg-white/70 p-3 dark:bg-white/5"
                style={{ marginLeft: `${Math.max(section.heading_level - 1, 0) * 12}px` }}
              >
                <p className="text-sm font-semibold">{section.title}</p>
                <p className="mt-1 text-xs text-[rgb(var(--muted))]">
                  p.{section.start_page}
                  {section.end_page !== section.start_page ? `-${section.end_page}` : ""} · level {section.heading_level}
                </p>
                <p className="mt-2 text-sm leading-6 text-[rgb(var(--muted))]">{section.snippet}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="panel-soft rounded-[1.75rem] p-4">
          <p className="text-sm font-semibold">Page snapshots</p>
          <div className="mt-4 space-y-3">
            {activeDocument.pages.map((page) => (
              <details
                key={page.id}
                className="rounded-2xl border border-[rgb(var(--border))] bg-white/70 p-3 dark:bg-white/5"
              >
                <summary className="cursor-pointer list-none">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold">
                        {page.label}
                        {page.title ? ` · ${page.title}` : ""}
                      </p>
                      <p className="mt-1 text-xs text-[rgb(var(--muted))]">
                        {page.word_count} words · {page.token_count} lexical tokens
                      </p>
                    </div>
                    <span className="rounded-full bg-white/80 px-2.5 py-1 text-xs dark:bg-white/10">Expand</span>
                  </div>
                </summary>
                <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-[rgb(var(--muted))]">{page.text}</p>
              </details>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
