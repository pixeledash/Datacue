"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sun, Moon, Activity } from "lucide-react";
import StatusIndicator from "./StatusIndicator";
import { getHealth } from "@/lib/api";

export default function Navbar() {
  const [dark, setDark] = useState(false);
  const [systemStatus, setSystemStatus] = useState<"ok" | "degraded" | "unknown" | "loading">("loading");

  // Sync dark mode class on <html>
  useEffect(() => {
    const stored = localStorage.getItem("datacue_theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const isDark = stored ? stored === "dark" : prefersDark;
    setDark(isDark);
    document.documentElement.classList.toggle("dark", isDark);
  }, []);

  const toggleDark = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("datacue_theme", next ? "dark" : "light");
  };

  // Poll health status every 30s
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const h = await getHealth();
        setSystemStatus(h.status);
      } catch {
        setSystemStatus("unknown");
      }
    };
    fetchStatus();
    const id = setInterval(fetchStatus, 30_000);
    return () => clearInterval(id);
  }, []);

  return (
    <nav className="sticky top-0 z-50 flex items-center justify-between px-5 py-3 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-950/80 backdrop-blur-sm">
      <Link href="/" className="flex items-center gap-2">
        <span className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white text-xs font-bold">
          DC
        </span>
        <span className="font-semibold text-slate-800 dark:text-slate-100 text-sm">
          Datacue
        </span>
      </Link>

      <div className="flex items-center gap-3">
        <Link
          href="/health"
          className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-100 transition-colors"
        >
          <StatusIndicator status={systemStatus} />
          <Activity className="w-3.5 h-3.5" />
          Status
        </Link>

        <button
          onClick={toggleDark}
          className="flex items-center justify-center w-8 h-8 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-500 dark:text-slate-400"
          aria-label="Toggle dark mode"
        >
          {dark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
      </div>
    </nav>
  );
}
