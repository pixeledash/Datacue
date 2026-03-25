"use client";

import { useState } from "react";
import { ChevronUp, ChevronDown, ChevronsUpDown, Download } from "lucide-react";
import { exportToCsv } from "@/lib/exportCsv";

const PAGE_SIZE = 10;

interface DataTableProps {
  columns: string[];
  rows: Record<string, string>[];
  title?: string;
}

type SortDir = "asc" | "desc" | null;

export default function DataTable({ columns, rows, title }: DataTableProps) {
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>(null);
  const [page, setPage] = useState(0);

  const handleSort = (col: string) => {
    if (sortCol === col) {
      if (sortDir === "asc") setSortDir("desc");
      else if (sortDir === "desc") { setSortCol(null); setSortDir(null); }
      else setSortDir("asc");
    } else {
      setSortCol(col);
      setSortDir("asc");
    }
    setPage(0);
  };

  const sorted = [...rows].sort((a, b) => {
    if (!sortCol || !sortDir) return 0;
    const va = String(a[sortCol] ?? "");
    const vb = String(b[sortCol] ?? "");
    const numA = Number(va);
    const numB = Number(vb);
    const isNum = !isNaN(numA) && !isNaN(numB);
    const cmp = isNum ? numA - numB : va.localeCompare(vb);
    return sortDir === "asc" ? cmp : -cmp;
  });

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE);
  const pageRows = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        {title && (
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
            {title}
          </h3>
        )}
        <button
          onClick={() => exportToCsv(columns, rows, `${title ?? "datacue"}.csv`)}
          className="ml-auto flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          Export CSV
        </button>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-slate-50 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
              {columns.map((col) => (
                <th
                  key={col}
                  onClick={() => handleSort(col)}
                  className="px-3 py-2.5 text-left font-semibold text-slate-600 dark:text-slate-400 cursor-pointer hover:text-blue-600 dark:hover:text-blue-400 whitespace-nowrap select-none"
                >
                  <span className="inline-flex items-center gap-1">
                    {col}
                    {sortCol === col ? (
                      sortDir === "asc" ? (
                        <ChevronUp className="w-3 h-3" />
                      ) : (
                        <ChevronDown className="w-3 h-3" />
                      )
                    ) : (
                      <ChevronsUpDown className="w-3 h-3 opacity-30" />
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-3 py-6 text-center text-slate-400 dark:text-slate-500"
                >
                  No data
                </td>
              </tr>
            ) : (
              pageRows.map((row, i) => (
                <tr
                  key={i}
                  className="border-b border-slate-100 dark:border-slate-800 last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                >
                  {columns.map((col) => (
                    <td
                      key={col}
                      className="px-3 py-2 text-slate-700 dark:text-slate-300 whitespace-nowrap max-w-[200px] truncate"
                      title={String(row[col] ?? "")}
                    >
                      {row[col] ?? "—"}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <span>
            Rows {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, sorted.length)} of {sorted.length}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-2 py-1 rounded-md hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              ‹ Prev
            </button>
            <span className="px-2">
              {page + 1} / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="px-2 py-1 rounded-md hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Next ›
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
