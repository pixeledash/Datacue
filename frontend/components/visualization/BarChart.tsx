"use client";

import {
  BarChart as ReBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface BarChartProps {
  rows: Record<string, string>[];
  x_axis: string;
  y_axis: string;
  title?: string;
}

const COLORS = [
  "#3b82f6", "#6366f1", "#8b5cf6", "#ec4899", "#f59e0b",
  "#10b981", "#14b8a6", "#f43f5e", "#84cc16", "#06b6d4",
];

export default function BarChartViz({ rows, x_axis, y_axis, title }: BarChartProps) {
  const data = rows.map((row) => ({
    ...row,
    [y_axis]: isNaN(Number(row[y_axis])) ? 0 : Number(row[y_axis]),
  }));

  return (
    <div className="flex flex-col gap-2">
      {title && (
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">{title}</h3>
      )}
      <ResponsiveContainer width="100%" height={280}>
        <ReBarChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 32 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey={x_axis}
            tick={{ fontSize: 11, fill: "#94a3b8" }}
            angle={-30}
            textAnchor="end"
            interval="preserveStartEnd"
          />
          <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} width={56} />
          <Tooltip
            contentStyle={{
              background: "#1e293b",
              border: "none",
              borderRadius: "8px",
              fontSize: "12px",
              color: "#f1f5f9",
            }}
          />
          <Bar dataKey={y_axis} radius={[4, 4, 0, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </ReBarChart>
      </ResponsiveContainer>
    </div>
  );
}
