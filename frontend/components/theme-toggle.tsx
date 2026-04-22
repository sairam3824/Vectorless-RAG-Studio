"use client";

import { MoonStar, SunMedium } from "lucide-react";
import { useEffect, useState } from "react";


export function ThemeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem("vectorless-theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const enabled = stored ? stored === "dark" : prefersDark;
    document.documentElement.classList.toggle("dark", enabled);
    setDark(enabled);
  }, []);

  function toggleTheme() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    window.localStorage.setItem("vectorless-theme", next ? "dark" : "light");
  }

  return (
    <button
      onClick={toggleTheme}
      className="panel-soft inline-flex h-10 w-10 items-center justify-center rounded-2xl text-[rgb(var(--muted))] transition hover:-translate-y-0.5 hover:text-[rgb(var(--text))]"
      aria-label="Toggle theme"
      type="button"
    >
      {dark ? <SunMedium className="h-4 w-4" /> : <MoonStar className="h-4 w-4" />}
    </button>
  );
}
