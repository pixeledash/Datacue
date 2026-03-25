"use client";

import { useState, useEffect, useRef } from "react";
import { sendChat } from "@/lib/api";
import {
  addHistoryEntry,
  loadHistory,
  clearHistory,
  saveLastResult,
  loadLastResult,
} from "@/lib/session";
import type { ChatResponse, HistoryEntry } from "@/types";

import QueryInput from "@/components/QueryInput";
import ResponseCard from "@/components/ResponseCard";
import ErrorBanner from "@/components/ErrorBanner";
import QueryHistory from "@/components/QueryHistory";
import ExampleQueries from "@/components/ExampleQueries";
import SkeletonLoader from "@/components/SkeletonLoader";
import VisualizationPanel from "@/components/visualization/VisualizationPanel";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [pendingQuery, setPendingQuery] = useState<string | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);

  // Load persisted state on mount
  useEffect(() => {
    setHistory(loadHistory());
    const last = loadLastResult();
    if (last) setResponse(last);
  }, []);

  // If a query is selected from history, fill input and optionally auto-run
  useEffect(() => {
    if (pendingQuery !== null) {
      handleSubmit(pendingQuery);
      setPendingQuery(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingQuery]);

  const handleSubmit = async (q: string) => {
    const trimmed = q.trim();
    if (!trimmed) return;

    setQuery(trimmed);
    setLoading(true);
    setResponse(null);

    try {
      const result = await sendChat(trimmed);
      setResponse(result);
      saveLastResult(result);

      if (result.success) {
        const updated = addHistoryEntry(trimmed, result);
        setHistory(updated);
      }

      setTimeout(() => {
        resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 50);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Network error";
      setResponse({
        success: false,
        message: msg,
        cds_view: "",
        llm1_reasoning: "",
        odata_url: "",
        row_count: 0,
        visualization: {
          type: "none",
          title: "",
          columns: [],
          rows: [],
          x_axis: null,
          y_axis: null,
          label_field: null,
          value_field: null,
        },
        error: msg,
        error_type: "INTERNAL_ERROR",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleHistorySelect = (q: string) => {
    setPendingQuery(q);
  };

  const handleClearHistory = () => {
    clearHistory();
    setHistory([]);
  };

  const isEmpty = !loading && !response;

  return (
    <div className="flex h-[calc(100vh-53px)]">
      {/* Sidebar */}
      <aside
        className={`flex-shrink-0 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 transition-all duration-200 overflow-hidden ${
          sidebarOpen ? "w-60" : "w-0"
        }`}
      >
        <div className="w-60 h-full">
          <QueryHistory
            history={history}
            onSelect={handleHistorySelect}
            onClear={handleClearHistory}
          />
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Sidebar toggle */}
        <div className="flex items-center px-4 pt-3 pb-1">
          <button
            onClick={() => setSidebarOpen((o) => !o)}
            className="flex items-center gap-1.5 text-xs text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
            aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
          >
            {sidebarOpen ? (
              <PanelLeftClose className="w-4 h-4" />
            ) : (
              <PanelLeftOpen className="w-4 h-4" />
            )}
          </button>
        </div>

        <div className="flex-1 flex flex-col max-w-3xl w-full mx-auto px-4 pb-6 gap-4">
          {/* Empty state */}
          {isEmpty && (
            <ExampleQueries onSelect={(q) => handleSubmit(q)} />
          )}

          {/* Query that was submitted */}
          {(loading || response) && query && (
            <div className="flex justify-end">
              <div className="max-w-md px-4 py-2.5 rounded-2xl rounded-tr-sm bg-blue-600 text-white text-sm shadow-sm">
                {query}
              </div>
            </div>
          )}

          {/* Loading skeleton */}
          {loading && <SkeletonLoader />}

          {/* Response */}
          {!loading && response && (
            <div ref={resultRef} className="flex flex-col gap-4">
              {response.success ? (
                <>
                  <ResponseCard response={response} />
                  {response.visualization && response.visualization.rows.length > 0 && (
                    <VisualizationPanel visualization={response.visualization} />
                  )}
                </>
              ) : (
                <ErrorBanner
                  errorType={response.error_type}
                  message={response.message || response.error}
                />
              )}
            </div>
          )}

          {/* Spacer to push input to bottom when empty */}
          {isEmpty && <div className="flex-1" />}

          {/* Input always at bottom */}
          <div className="sticky bottom-0 pb-2 pt-3 bg-[var(--background)]">
            <QueryInput onSubmit={handleSubmit} loading={loading} />
          </div>
        </div>
      </div>
    </div>
  );
}
