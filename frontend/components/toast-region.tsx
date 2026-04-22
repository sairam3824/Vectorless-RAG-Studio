"use client";

import { CheckCircle2, CircleAlert, Info } from "lucide-react";


export interface ToastItem {
  id: string;
  tone: "success" | "error" | "info";
  title: string;
  message: string;
}


const toneMap = {
  success: { icon: CheckCircle2, border: "border-emerald-300/60", bg: "bg-emerald-50/90 dark:bg-emerald-900/35" },
  error: { icon: CircleAlert, border: "border-rose-300/70", bg: "bg-rose-50/90 dark:bg-rose-900/35" },
  info: { icon: Info, border: "border-sky-300/60", bg: "bg-sky-50/90 dark:bg-sky-900/35" },
};


export function ToastRegion({ items }: { items: ToastItem[] }) {
  return (
    <div className="pointer-events-none fixed right-4 top-4 z-50 flex w-full max-w-sm flex-col gap-3">
      {items.map((item) => {
        const tone = toneMap[item.tone];
        const Icon = tone.icon;
        return (
          <div
            key={item.id}
            className={`pointer-events-auto rounded-3xl border px-4 py-3 shadow-panel ${tone.border} ${tone.bg}`}
          >
            <div className="flex items-start gap-3">
              <Icon className="mt-0.5 h-5 w-5 shrink-0" />
              <div>
                <p className="text-sm font-semibold">{item.title}</p>
                <p className="mt-1 text-sm text-[rgb(var(--muted))]">{item.message}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
