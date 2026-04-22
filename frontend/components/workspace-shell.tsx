"use client";

import { FormEvent, startTransition, useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import { ChatMessage, DocumentDetail, DocumentSummary, HealthResponse, QueryDebug, RetrievedPassage } from "@/types";
import { ChatPanel } from "./chat-panel";
import { DocumentExplorer } from "./document-explorer";
import { EvidencePanel } from "./evidence-panel";
import { Sidebar } from "./sidebar";
import { ToastItem, ToastRegion } from "./toast-region";
import { usePersistedState } from "@/hooks/use-persisted-state";


export function WorkspaceShell() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(null);
  const [activeDocument, setActiveDocument] = useState<DocumentDetail | null>(null);
  const [loadingDocumentDetail, setLoadingDocumentDetail] = useState(false);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<RetrievedPassage[]>([]);
  const [debug, setDebug] = useState<QueryDebug | null>(null);
  const [highlightedUnitId, setHighlightedUnitId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"ask" | "explorer">("ask");
  const [messages, setMessages, messagesReady] = usePersistedState<ChatMessage[]>("vectorless-chat-history", []);
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [isBooting, setIsBooting] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);

  useEffect(() => {
    void refreshData();
  }, []);

  useEffect(() => {
    if (!activeDocumentId) {
      setActiveDocument(null);
      return;
    }
    void loadDocument(activeDocumentId);
  }, [activeDocumentId, documents]);

  useEffect(() => {
    if (!documents.length) {
      setActiveDocumentId(null);
      setSelectedDocumentIds([]);
      return;
    }
    if (!activeDocumentId || !documents.some((document) => document.id === activeDocumentId)) {
      setActiveDocumentId(documents[0].id);
    }
    setSelectedDocumentIds((current) => current.filter((id) => documents.some((document) => document.id === id)));
  }, [activeDocumentId, documents]);

  const indexedDocuments = useMemo(
    () => documents.filter((document) => document.indexing_status === "indexed"),
    [documents],
  );

  async function refreshData() {
    try {
      const [nextHealth, nextDocuments] = await Promise.all([api.health(), api.listDocuments()]);
      setHealth(nextHealth);
      setDocuments(nextDocuments);
    } catch (error) {
      pushToast("error", "Backend unavailable", getErrorMessage(error));
    } finally {
      setIsBooting(false);
    }
  }

  async function loadDocument(documentId: string) {
    setLoadingDocumentDetail(true);
    try {
      const detail = await api.getDocument(documentId);
      setActiveDocument(detail);
    } catch (error) {
      pushToast("error", "Could not load document", getErrorMessage(error));
    } finally {
      setLoadingDocumentDetail(false);
    }
  }

  function pushToast(tone: ToastItem["tone"], title: string, message: string) {
    const nextToast = { id: `${Date.now()}-${Math.random()}`, tone, title, message };
    setToasts((current) => [nextToast, ...current].slice(0, 4));
    window.setTimeout(() => {
      setToasts((current) => current.filter((item) => item.id !== nextToast.id));
    }, 4200);
  }

  async function handleUpload(files: File[]) {
    setIsUploading(true);
    try {
      const response = await api.upload(files);
      await refreshData();
      pushToast("success", "Documents uploaded", `${response.total_uploaded} file(s) are ready to index.`);
      if (response.skipped.length) {
        pushToast("info", "Some files were skipped", response.skipped.map((item) => `${item.filename}: ${item.reason}`).join(" | "));
      }
    } catch (error) {
      pushToast("error", "Upload failed", getErrorMessage(error));
    } finally {
      setIsUploading(false);
    }
  }

  async function handleIndex() {
    setIsIndexing(true);
    try {
      const response = await api.buildIndex(selectedDocumentIds.length ? selectedDocumentIds : undefined);
      await refreshData();
      pushToast(
        "success",
        "Index rebuilt",
        `${response.retrieval_unit_count} retrieval units indexed across ${response.document_count} document(s).`,
      );
    } catch (error) {
      pushToast("error", "Index build failed", getErrorMessage(error));
    } finally {
      setIsIndexing(false);
    }
  }

  async function handleDeleteDocument(documentId: string) {
    try {
      await api.deleteDocument(documentId);
      if (activeDocumentId === documentId) {
        setActiveDocument(null);
      }
      setResults([]);
      setDebug(null);
      await refreshData();
      pushToast("success", "Document deleted", "The document was removed and the retrieval index was invalidated.");
    } catch (error) {
      pushToast("error", "Delete failed", getErrorMessage(error));
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!query.trim()) return;
    setIsQuerying(true);
    setHighlightedUnitId(null);
    try {
      const response = await api.query({
        question: query.trim(),
        top_k: 6,
        selected_document_ids: selectedDocumentIds.length ? selectedDocumentIds : undefined,
        include_debug: true,
      });

      setResults(response.retrieved_chunks);
      setDebug(response.debug);
      if (response.retrieved_chunks.length) {
        setHighlightedUnitId(response.retrieved_chunks[0].unit_id);
      }

      const message: ChatMessage = {
        id: crypto.randomUUID(),
        question: response.question,
        answer: response.answer,
        citations: response.citations,
        retrievalSummary: response.retrieval_summary,
        answerStatus: response.answer_status,
        createdAt: new Date().toISOString(),
      };

      startTransition(() => {
        setMessages((current) => [message, ...current].slice(0, 12));
      });
      setQuery("");
      pushToast("success", "Answer ready", response.llm_used ? "Grounded answer generated with citations." : "Showing retrieval-grounded fallback output.");
    } catch (error) {
      pushToast("error", "Query failed", getErrorMessage(error));
    } finally {
      setIsQuerying(false);
    }
  }

  function toggleDocument(documentId: string) {
    setSelectedDocumentIds((current) =>
      current.includes(documentId) ? current.filter((id) => id !== documentId) : [...current, documentId],
    );
  }

  if (isBooting || !messagesReady) {
    return (
      <main className="flex min-h-screen items-center justify-center px-6">
        <div className="panel rounded-[2rem] px-8 py-7 text-center">
          <p className="text-sm text-[rgb(var(--muted))]">Loading Vectorless RAG Studio...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-4 py-4 md:px-6 md:py-6">
      <ToastRegion items={toasts} />
      <div className="mx-auto grid max-w-[1600px] gap-4 lg:grid-cols-[320px_minmax(0,1fr)_360px]">
        <Sidebar
          documents={documents}
          health={health}
          selectedDocumentIds={selectedDocumentIds}
          activeDocumentId={activeDocumentId}
          isUploading={isUploading}
          isIndexing={isIndexing}
          onUpload={handleUpload}
          onToggleDocument={toggleDocument}
          onSetActiveDocument={setActiveDocumentId}
          onIndex={handleIndex}
          onDeleteDocument={handleDeleteDocument}
        />

        <div className="min-w-0">
          <ChatPanel
            query={query}
            setQuery={setQuery}
            messages={messages}
            isQuerying={isQuerying}
            indexReady={Boolean(health?.index_ready)}
            onSubmit={handleSubmit}
            onApplySample={setQuery}
            onCitationClick={setHighlightedUnitId}
            activeTab={activeTab}
            onChangeTab={setActiveTab}
          />

          {activeTab === "explorer" ? (
            <DocumentExplorer
              documents={documents}
              activeDocument={activeDocument}
              isLoading={loadingDocumentDetail}
            />
          ) : null}

          {!documents.length ? (
            <div className="panel-soft mt-4 rounded-[1.75rem] p-5 text-sm leading-6 text-[rgb(var(--muted))]">
              This dashboard is empty until you upload files. Once documents are indexed, the app will preserve recent
              chat history in your browser and show evidence-backed answers here.
            </div>
          ) : null}

          {documents.length && !indexedDocuments.length ? (
            <div className="panel-soft mt-4 rounded-[1.75rem] p-5 text-sm leading-6 text-[rgb(var(--muted))]">
              Documents are uploaded but not indexed yet. Use the sidebar action to build the lexical page and section
              index before asking questions.
            </div>
          ) : null}
        </div>

        <EvidencePanel results={results} debug={debug} highlightedUnitId={highlightedUnitId} />
      </div>
    </main>
  );
}


function getErrorMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  return "Something unexpected happened.";
}
