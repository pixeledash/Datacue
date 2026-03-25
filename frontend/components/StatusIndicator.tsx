interface StatusIndicatorProps {
  status: "ok" | "degraded" | "unknown" | "loading";
  size?: "sm" | "md";
}

const STATUS_COLORS = {
  ok: "bg-emerald-500",
  degraded: "bg-amber-400",
  unknown: "bg-slate-400",
  loading: "bg-slate-300 animate-pulse",
};

export default function StatusIndicator({
  status,
  size = "sm",
}: StatusIndicatorProps) {
  const sizeClass = size === "sm" ? "w-2 h-2" : "w-2.5 h-2.5";
  return (
    <span
      className={`inline-block rounded-full ${sizeClass} ${STATUS_COLORS[status]}`}
      aria-label={`System status: ${status}`}
    />
  );
}
