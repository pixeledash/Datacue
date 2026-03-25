export function exportToCsv(
  columns: string[],
  rows: Record<string, string>[],
  filename = "datacue-export.csv"
): void {
  const escape = (val: string) => `"${String(val ?? "").replace(/"/g, '""')}"`;

  const header = columns.map(escape).join(",");
  const body = rows
    .map((row) => columns.map((col) => escape(row[col] ?? "")).join(","))
    .join("\n");

  const csv = `${header}\n${body}`;
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
