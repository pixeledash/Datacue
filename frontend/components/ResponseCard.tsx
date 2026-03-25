"use client";

import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  Database,
  Rows3,
  Brain,
  Link2,
} from "lucide-react";
import type { ChatResponse } from "@/types";

interface ResponseCardProps {
  response: ChatResponse;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
      aria-label="Copy to clipboard"
    >
      {copied ? (
        <>
          <Check className="w-3.5 h-3.5" />
          Copied
        </>
      ) : (
        <>
          <Copy className="w-3.5 h-3.5" />
          Copy
        </>
      )}
    </button>
  );
}

function CollapsibleSection({
  title,
  icon,
  children,
  defaultOpen = false,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-2.5 bg-slate-50 dark:bg-slate-800/60 hover:bg-slate-100 dark:hover:bg-slate-800 text-sm font-medium text-slate-700 dark:text-slate-300 transition-colors"
      >
        <span className="flex items-center gap-2">
          {icon}
          {title}
        </span>
        {open ? (
          <ChevronUp className="w-4 h-4 text-slate-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-slate-400" />
        )}
      </button>
      {open && <div className="px-4 py-3 bg-white dark:bg-slate-900">{children}</div>}
    </div>
  );
}

export default function ResponseCard({ response }: ResponseCardProps) {
  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-sm p-5">
      {/* Badges row */}
      <div className="flex flex-wrap items-center gap-2">
        {response.cds_view && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400 text-xs font-medium">
            <Database className="w-3 h-3" />
            {response.cds_view}
          </span>
        )}
        {response.row_count > 0 && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-xs font-medium">
            <Rows3 className="w-3 h-3" />
            {response.row_count} row{response.row_count !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Message */}
      <p className="text-sm leading-relaxed text-slate-700 dark:text-slate-200 whitespace-pre-wrap">
        {response.message}
      </p>

      {/* Copy message button */}
      <div className="flex justify-end">
        <CopyButton text={response.message} />
      </div>

      {/* Collapsibles */}
      <div className="flex flex-col gap-2">
        {response.llm1_reasoning && (
          <CollapsibleSection
            title="Why this view?"
            icon={<Brain className="w-4 h-4 text-purple-500" />}
          >
            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
              {response.llm1_reasoning}
            </p>
          </CollapsibleSection>
        )}

        {response.odata_url && (
          <CollapsibleSection
            title="OData URL"
            icon={<Link2 className="w-4 h-4 text-green-500" />}
          >
            <div className="flex items-start justify-between gap-3">
              <code className="text-xs text-slate-600 dark:text-slate-400 font-mono break-all leading-relaxed flex-1">
                {response.odata_url}
              </code>
              <CopyButton text={response.odata_url} />
            </div>
          </CollapsibleSection>
        )}
      </div>
    </div>
  );
}
