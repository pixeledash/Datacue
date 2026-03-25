"use client";

import { Clock, Trash2 } from "lucide-react";
import type { HistoryEntry } from "@/types";

interface QueryHistoryProps {
  history: HistoryEntry[];
  onSelect: (query: string) => void;
  onClear: () => void;
}

export default function QueryHistory({
  history,
  onSelect,
  onClear,
}: QueryHistoryProps) {
  if (history.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-32 text-center px-4">
        <Clock className="w-6 h-6 text-slate-300 dark:text-slate-600 mb-2" />
        <p className="text-xs text-slate-400 dark:text-slate-500">
          No history yet
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b border-slate-200 dark:border-slate-700">
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
          History
        </span>
        <button
          onClick={onClear}
          className="flex items-center gap-1 text-xs text-slate-400 hover:text-red-500 dark:hover:text-red-400 transition-colors"
          aria-label="Clear history"
        >
          <Trash2 className="w-3.5 h-3.5" />
          Clear
        </button>
      </div>
      <ul className="flex-1 overflow-y-auto py-1">
        {history.map((entry) => (
          <li key={entry.id}>
            <button
              onClick={() => onSelect(entry.query)}
              className="w-full text-left px-3 py-2.5 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors group"
            >
              <p className="text-xs text-slate-700 dark:text-slate-300 line-clamp-2 leading-snug group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                {entry.query}
              </p>
              <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">
                {new Date(entry.timestamp).toLocaleString(undefined, {
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
