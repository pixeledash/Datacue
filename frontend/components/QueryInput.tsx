"use client";

import { useRef, useState, type KeyboardEvent } from "react";
import { Send, Loader2 } from "lucide-react";

const MAX_CHARS = 500;

interface QueryInputProps {
  onSubmit: (query: string) => void;
  loading: boolean;
}

export default function QueryInput({ onSubmit, loading }: QueryInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || loading || trimmed.length > MAX_CHARS) return;
    onSubmit(trimmed);
    setValue("");
    textareaRef.current?.focus();
  };

  const remaining = MAX_CHARS - value.length;
  const isOverLimit = remaining < 0;

  return (
    <div className="relative flex flex-col gap-2">
      <div className="relative flex items-end gap-2 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-sm px-4 py-3 focus-within:ring-2 focus-within:ring-blue-500 transition-all">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your SAP data… (e.g. 'Show sales orders for customer C001')"
          rows={2}
          disabled={loading}
          className="flex-1 resize-none bg-transparent text-sm text-slate-800 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 outline-none leading-relaxed disabled:opacity-60"
          style={{ maxHeight: "160px" }}
        />
        <button
          onClick={handleSubmit}
          disabled={loading || !value.trim() || isOverLimit}
          className="flex-shrink-0 flex items-center justify-center w-9 h-9 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 dark:disabled:bg-slate-600 text-white transition-colors disabled:cursor-not-allowed"
          aria-label="Send query"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </button>
      </div>
      <div className="flex items-center justify-between px-1">
        <p className="text-xs text-slate-400 dark:text-slate-500">
          Press <kbd className="px-1 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400 font-mono text-xs">Enter</kbd> to send,{" "}
          <kbd className="px-1 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400 font-mono text-xs">Shift+Enter</kbd> for new line
        </p>
        <span
          className={`text-xs tabular-nums ${
            isOverLimit
              ? "text-red-500 font-medium"
              : remaining <= 50
              ? "text-amber-500"
              : "text-slate-400 dark:text-slate-500"
          }`}
        >
          {remaining}
        </span>
      </div>
    </div>
  );
}
