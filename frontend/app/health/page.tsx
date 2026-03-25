"use client";

import { useEffect, useState } from "react";
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  Database,
  Cpu,
  Server,
  BrainCircuit,
  RefreshCw,
} from "lucide-react";
import { getHealth } from "@/lib/api";
import type { HealthResponse } from "@/types";
import StatusIndicator from "@/components/StatusIndicator";

function StatusCard({
  label,
  value,
  icon,
  ok,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  ok: boolean | null;
}) {
  return (
    <div className="flex items-start gap-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
      <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500 dark:text-slate-400">
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-0.5">
          {label}
        </p>
        <p className="text-sm text-slate-800 dark:text-slate-100 truncate font-medium">
          {value}
        </p>
      </div>
      <div className="flex-shrink-0 mt-0.5">
        {ok === null ? (
          <AlertCircle className="w-4 h-4 text-slate-400" />
        ) : ok ? (
          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
        ) : (
          <XCircle className="w-4 h-4 text-red-500" />
        )}
      </div>
    </div>
  );
}

export default function HealthPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getHealth();
      setHealth(data);
      setLastUpdated(new Date());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch health status");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const id = setInterval(fetchHealth, 30_000);
    return () => clearInterval(id);
  }, []);

  const overallStatus =
    health?.status === "ok"
      ? "ok"
      : health?.status === "degraded"
      ? "degraded"
      : error
      ? "unknown"
      : "loading";

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100">
            System Status
          </h1>
          {lastUpdated && (
            <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <div
            className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold ${
              overallStatus === "ok"
                ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400"
                : overallStatus === "degraded"
                ? "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400"
                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
            }`}
          >
            <StatusIndicator status={overallStatus} />
            {overallStatus === "loading"
              ? "Checking…"
              : overallStatus === "ok"
              ? "All Systems OK"
              : overallStatus === "degraded"
              ? "Degraded"
              : "Unknown"}
          </div>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 flex items-center gap-2 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-xl px-4 py-3">
          <XCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {loading && !health && (
        <div className="flex flex-col gap-3 animate-pulse">
          {[1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="h-16 rounded-xl bg-slate-100 dark:bg-slate-800"
            />
          ))}
        </div>
      )}

      {health && (
        <div className="flex flex-col gap-3">
          <StatusCard
            label="FAISS Index"
            value={health.faiss_index}
            icon={<Database className="w-4 h-4" />}
            ok={health.faiss_index === "loaded"}
          />
          <StatusCard
            label="Metadata Records"
            value={health.meta_count.toLocaleString() + " views indexed"}
            icon={<Database className="w-4 h-4" />}
            ok={health.meta_count > 0}
          />
          <StatusCard
            label="Ollama LLM"
            value={`${health.ollama} · ${health.llm_model}`}
            icon={<BrainCircuit className="w-4 h-4" />}
            ok={health.ollama === "reachable"}
          />
          <StatusCard
            label="SAP System"
            value={health.sap}
            icon={<Server className="w-4 h-4" />}
            ok={health.sap === "reachable"}
          />
          <StatusCard
            label="Embedding Model"
            value={health.embedding_model}
            icon={<Cpu className="w-4 h-4" />}
            ok={null}
          />
        </div>
      )}
    </div>
  );
}
