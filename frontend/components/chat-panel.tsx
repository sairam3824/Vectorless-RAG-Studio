"use client";

import { ArrowUpRight, LoaderCircle, MessageSquareDashed, Radar, SearchCheck } from "lucide-react";
import { FormEvent } from "react";

import { ChatMessage } from "@/types";


const sampleQuestions = [
  "What does the handbook say about remote work expectations?",
  "Which page explains how indexing works in the product notes?",
  "Summarize the onboarding checklist with citations.",
];


interface ChatPanelProps {
  query: string;
  setQuery: (value: string) => void;
  messages: ChatMessage[];
  isQuerying: boolean;
  indexReady: boolean;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onApplySample: (question: string) => void;
  onCitationClick: (unitId: string) => void;
  activeTab: "ask" | "explorer";
  onChangeTab: (tab: "ask" | "explorer") => void;
}


export function ChatPanel({
  query,
  setQuery,
  messages,
  isQuerying,
  indexReady,
  onSubmit,
  onApplySample,
  onCitationClick,
  activeTab,
  onChangeTab,
}: ChatPanelProps) {
  return (
    <section className="panel flex min-h-[70vh] flex-col rounded-[2rem] p-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.26em] text-[rgb(var(--muted))]">Workspace</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight">Ask your documents</h2>
          <p className="mt-2 text-sm text-[rgb(var(--muted))]">
            Retrieval stays transparent: pages and sections are ranked lexically, fused, and shown alongside the answer.
          </p>
        </div>
        <div className="flex rounded-2xl border border-[rgb(var(--border))] bg-white/60 p-1 dark:bg-white/5">
          {[
            { key: "ask", label: "Q&A" },
            { key: "explorer", label: "Explorer" },
          ].map((item) => (
            <button
              key={item.key}
              className={`rounded-xl px-4 py-2 text-sm font-medium transition ${
                activeTab === item.key ? "bg-[rgb(var(--text))] text-white" : "text-[rgb(var(--muted))]"
              }`}
              onClick={() => onChangeTab(item.key as "ask" | "explorer")}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {activeTab === "ask" ? (
        <>
          <div className="mt-5 flex flex-wrap gap-2">
            {sampleQuestions.map((sample) => (
              <button
                key={sample}
                type="button"
                onClick={() => onApplySample(sample)}
                className="rounded-full border border-[rgb(var(--border))] bg-white/70 px-3 py-2 text-sm text-[rgb(var(--muted))] transition hover:border-[rgb(var(--accent))] hover:text-[rgb(var(--text))] dark:bg-white/5"
              >
                {sample}
              </button>
            ))}
          </div>

          <form onSubmit={onSubmit} className="mt-5 rounded-[1.75rem] border border-[rgb(var(--border))] bg-white/65 p-4 dark:bg-white/5">
            <label className="block text-sm font-medium">Question</label>
            <textarea
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              rows={4}
              placeholder="Ask a grounded question about your uploaded documents."
              className="mt-3 w-full resize-none rounded-2xl border border-[rgb(var(--border))] bg-[rgb(var(--panel-soft))] px-4 py-3 outline-none transition focus:border-[rgb(var(--accent))]"
            />
            <div className="mt-4 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm text-[rgb(var(--muted))]">
                {indexReady ? <SearchCheck className="h-4 w-4" /> : <Radar className="h-4 w-4" />}
                {indexReady ? "Index ready for retrieval" : "Build the index after uploading documents"}
              </div>
              <button
                type="submit"
                disabled={!query.trim() || isQuerying || !indexReady}
                className="inline-flex items-center gap-2 rounded-2xl bg-[rgb(var(--accent))] px-4 py-3 text-sm font-semibold text-white transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isQuerying ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <ArrowUpRight className="h-4 w-4" />}
                {isQuerying ? "Retrieving..." : "Ask"}
              </button>
            </div>
          </form>

          <div className="mt-5 flex-1 space-y-4 overflow-y-auto pr-1 scrollbar-thin">
            {messages.length ? (
              messages.map((message) => (
                <div key={message.id} className="space-y-3 rounded-[1.75rem] border border-[rgb(var(--border))] bg-white/70 p-5 dark:bg-white/5">
                  <div className="inline-flex items-center gap-2 rounded-full bg-[rgb(var(--accent-soft))] px-3 py-1 text-xs font-semibold text-[rgb(var(--accent))]">
                    <MessageSquareDashed className="h-3.5 w-3.5" />
                    User question
                  </div>
                  <p className="text-base font-medium">{message.question}</p>

                  <div className="rounded-[1.5rem] bg-[rgb(var(--panel-soft))] p-4">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-semibold">Grounded answer</p>
                      <span className="rounded-full bg-white/70 px-3 py-1 text-xs capitalize text-[rgb(var(--muted))] dark:bg-white/10">
                        {message.answerStatus.replaceAll("_", " ")}
                      </span>
                    </div>
                    <div className="markdown-answer mt-3 whitespace-pre-wrap text-sm leading-7 text-[rgb(var(--text))]">
                      {message.answer}
                    </div>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {message.citations.map((citation) => (
                        <button
                          key={citation.unit_id}
                          type="button"
                          onClick={() => onCitationClick(citation.unit_id)}
                          className="rounded-full border border-[rgb(var(--border))] bg-white/80 px-3 py-1 text-xs font-medium transition hover:border-[rgb(var(--accent))] dark:bg-white/10"
                        >
                          {citation.filename} p.{citation.page_number}
                          {citation.section_title ? ` · ${citation.section_title}` : ""}
                        </button>
                      ))}
                    </div>
                    <p className="mt-3 text-xs text-[rgb(var(--muted))]">
                      {message.retrievalSummary.returned_count} evidence block
                      {message.retrievalSummary.returned_count === 1 ? "" : "s"} returned from{" "}
                      {message.retrievalSummary.candidate_count} lexical candidates.
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="panel-soft flex h-full min-h-[280px] flex-col items-center justify-center rounded-[1.75rem] border-dashed p-10 text-center">
                <MessageSquareDashed className="h-10 w-10 text-[rgb(var(--muted))]" />
                <h3 className="mt-4 text-lg font-semibold">No questions yet</h3>
                <p className="mt-2 max-w-xl text-sm leading-6 text-[rgb(var(--muted))]">
                  Upload documents, build the structured index, and ask a question to see lexical retrieval, citations,
                  and evidence side by side.
                </p>
              </div>
            )}
          </div>
        </>
      ) : null}
    </section>
  );
}
