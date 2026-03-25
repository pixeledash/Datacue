"use client";

import { useState } from "react";
import { Table2, BarChart2 } from "lucide-react";
import type { Visualization } from "@/types";
import DataTable from "./DataTable";
import BarChartViz from "./BarChart";
import LineChartViz from "./LineChart";
import PieChartViz from "./PieChart";

interface VisualizationPanelProps {
  visualization: Visualization;
}

export default function VisualizationPanel({ visualization }: VisualizationPanelProps) {
  const { type, title, columns, rows, x_axis, y_axis, label_field, value_field } = visualization;

  const hasChart = type !== "none" && type !== "table";
  const [showTable, setShowTable] = useState(false);

  if (type === "none" || rows.length === 0) return null;

  const renderChart = () => {
    if (!hasChart || showTable) return null;

    if (type === "bar_chart" && x_axis && y_axis) {
      return (
        <BarChartViz rows={rows} x_axis={x_axis} y_axis={y_axis} title={title} />
      );
    }
    if (type === "line_chart" && x_axis && y_axis) {
      return (
        <LineChartViz rows={rows} x_axis={x_axis} y_axis={y_axis} title={title} />
      );
    }
    if (type === "pie_chart" && label_field && value_field) {
      return (
        <PieChartViz
          rows={rows}
          label_field={label_field}
          value_field={value_field}
          title={title}
        />
      );
    }
    return null;
  };

  const showingTable = !hasChart || showTable;

  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-sm p-5">
      {/* Toggle row */}
      {hasChart && (
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
            {title || "Results"}
          </h3>
          <div className="flex items-center rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
            <button
              onClick={() => setShowTable(false)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs transition-colors ${
                !showTable
                  ? "bg-blue-600 text-white"
                  : "bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700"
              }`}
            >
              <BarChart2 className="w-3.5 h-3.5" />
              Chart
            </button>
            <button
              onClick={() => setShowTable(true)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs transition-colors border-l border-slate-200 dark:border-slate-700 ${
                showTable
                  ? "bg-blue-600 text-white"
                  : "bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700"
              }`}
            >
              <Table2 className="w-3.5 h-3.5" />
              Table
            </button>
          </div>
        </div>
      )}

      {/* Content */}
      {showingTable ? (
        <DataTable columns={columns} rows={rows} title={hasChart ? undefined : title} />
      ) : (
        renderChart()
      )}
    </div>
  );
}
