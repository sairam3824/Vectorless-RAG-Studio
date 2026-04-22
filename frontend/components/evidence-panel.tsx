"use client";

import type { ReactNode } from "react";
import { Code2, FileSearch, Gauge, Sparkles } from "lucide-react";

import { highlightTerms, scoreLabel } from "@/lib/utils";
import { QueryDebug, RetrievedPassage } from "@/types";


interface EvidencePanelProps {
  results: RetrievedPassage[];
  debug: QueryDebug | null;
  highlightedUnitId: string | null;
}


export function EvidencePanel({ results, debug, highlightedUnitId }: EvidencePanelProps) {
  return (
    <aside className="panel rounded-[2rem] p-5 lg:sticky lg:top-6 lg:h-[calc(100vh-3rem)] lg:overflow-y-auto scrollbar-thin">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.24em] text-[rgb(var(--muted))]">
        <FileSearch className="h-3.5 w-3.5" />
        Evidence panel
      </div>
      <h3 className="mt-3 text-2xl font-semibold">Retrieved pages and sections</h3>
      <p className="mt-2 text-sm leading-6 text-[rgb(var(--muted))]">
        Inspect score fusion, snippets, and the exact evidence passed into generation.
      </p>

      <div className="mt-5 space-y-3">
        {results.length ? (
          results.map((result) => (
            <details
              key={result.unit_id}
              open={highlightedUnitId === result.unit_id}
              className={`rounded-[1.6rem] border p-4 transition ${
                highlightedUnitId === result.unit_id
                  ? "border-[rgb(var(--accent))] bg-[rgb(var(--accent-soft))]/50"
                  : "border-[rgb(var(--border))] bg-white/60 dark:bg-white/5"
              }`}
            >
              <summary className="list-none cursor-pointer">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold">{result.filename}</p>
                    <p className="mt-1 text-xs text-[rgb(var(--muted))]">
                      p.{result.start_page}
                      {result.end_page !== result.start_page ? `-${result.end_page}` : ""} · {result.unit_type}
                      {result.section_title ? ` · ${result.section_title}` : ""}
                    </p>
                  </div>
                  <div className="rounded-full bg-white/80 px-3 py-1 text-xs font-semibold dark:bg-white/10">
                    {scoreLabel(result.score)} {result.score.toFixed(2)}
                  </div>
                </div>
              </summary>

              <div className="mt-4 space-y-4">
                <p className="rounded-2xl bg-white/75 px-3 py-3 text-sm leading-7 dark:bg-white/10">
                  {highlightTerms(result.snippet, result.matched_terms).map((part, index) => {
                    const match = result.matched_terms.some((term) => part.toLowerCase() === term.toLowerCase());
                    return match ? (
                      <mark key={`${result.unit_id}-${index}`} className="rounded bg-yellow-200 px-1 text-ink">
                        {part}
                      </mark>
                    ) : (
                      <span key={`${result.unit_id}-${index}`}>{part}</span>
                    );
                  })}
                </p>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <ScorePill label="BM25" value={result.bm25_score} />
                  <ScorePill label="TF-IDF" value={result.tfidf_score} />
                  <ScorePill label="Keywords" value={result.keyword_score} />
                  <ScorePill label="Title boost" value={result.title_score} />
                </div>

                <details className="rounded-2xl bg-white/70 px-3 py-3 text-sm dark:bg-white/10">
                  <summary className="cursor-pointer font-medium">View full evidence</summary>
                  <p className="mt-3 whitespace-pre-wrap leading-7 text-[rgb(var(--muted))]">{result.text}</p>
                </details>
              </div>
            </details>
          ))
        ) : (
          <div className="panel-soft rounded-[1.75rem] p-5 text-sm text-[rgb(var(--muted))]">
            Ask a question to populate the evidence stack. Retrieval results and citations will appear here.
          </div>
        )}
      </div>

      <details className="panel-soft mt-5 rounded-[1.75rem] p-4" open={Boolean(debug)}>
        <summary className="flex cursor-pointer list-none items-center gap-2 text-sm font-semibold">
          <Code2 className="h-4 w-4" />
          Query debug view
        </summary>
        {debug ? (
          <div className="mt-4 space-y-4 text-sm">
            <DebugBlock icon={<Sparkles className="h-4 w-4" />} label="Normalized query" value={debug.normalized_query || "No normalized terms"} />
            <DebugBlock icon={<Gauge className="h-4 w-4" />} label="Top candidate count" value={String(debug.candidate_count)} />
            <DebugBlock icon={<FileSearch className="h-4 w-4" />} label="Query terms" value={debug.query_terms.join(", ") || "No terms"} />
            <div className="rounded-2xl bg-white/70 p-3 dark:bg-white/10">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[rgb(var(--muted))]">Context passed to the LLM</p>
              <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap text-xs leading-6 text-[rgb(var(--muted))]">
                {debug.context_preview || "No context was assembled."}
              </pre>
            </div>
          </div>
        ) : (
          <p className="mt-3 text-sm text-[rgb(var(--muted))]">Debug details appear after you run a query.</p>
        )}
      </details>
    </aside>
  );
}


function ScorePill({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl bg-white/70 px-3 py-2 dark:bg-white/10">
      <p className="text-[11px] uppercase tracking-[0.18em] text-[rgb(var(--muted))]">{label}</p>
      <p className="mt-1 font-semibold">{value.toFixed(3)}</p>
    </div>
  );
}


function DebugBlock({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-white/70 px-3 py-3 dark:bg-white/10">
      <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-[rgb(var(--muted))]">
        {icon}
        {label}
      </p>
      <p className="mt-2 text-sm leading-6">{value}</p>
    </div>
  );
}
