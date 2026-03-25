"use client";

import {
  LineChart as ReLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Dot,
} from "recharts";

interface LineChartProps {
  rows: Record<string, string>[];
  x_axis: string;
  y_axis: string;
  title?: string;
}

export default function LineChartViz({ rows, x_axis, y_axis, title }: LineChartProps) {
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
        <ReLineChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 32 }}>
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
          <Line
            type="monotone"
            dataKey={y_axis}
            stroke="#3b82f6"
            strokeWidth={2}
            dot={<Dot r={3} fill="#3b82f6" />}
            activeDot={{ r: 5 }}
          />
        </ReLineChart>
      </ResponsiveContainer>
    </div>
  );
}
