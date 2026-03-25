"use client";

import {
  PieChart as RePieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface PieChartProps {
  rows: Record<string, string>[];
  label_field: string;
  value_field: string;
  title?: string;
}

const COLORS = [
  "#3b82f6", "#6366f1", "#8b5cf6", "#ec4899", "#f59e0b",
  "#10b981", "#14b8a6", "#f43f5e", "#84cc16", "#06b6d4",
];

export default function PieChartViz({ rows, label_field, value_field, title }: PieChartProps) {
  const data = rows
    .map((row) => ({
      name: row[label_field] ?? "Unknown",
      value: isNaN(Number(row[value_field])) ? 0 : Number(row[value_field]),
    }))
    .filter((d) => d.value > 0);

  return (
    <div className="flex flex-col gap-2">
      {title && (
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">{title}</h3>
      )}
      <ResponsiveContainer width="100%" height={300}>
        <RePieChart>
          <Pie
            data={data}
            cx="50%"
            cy="45%"
            outerRadius={100}
            dataKey="value"
            nameKey="name"
            label={({ name, percent }) =>
              `${name} (${((percent ?? 0) * 100).toFixed(1)}%)`
            }
            labelLine={true}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "#1e293b",
              border: "none",
              borderRadius: "8px",
              fontSize: "12px",
              color: "#f1f5f9",
            }}
          />
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: "11px", color: "#94a3b8" }}
          />
        </RePieChart>
      </ResponsiveContainer>
    </div>
  );
}
