export default function SkeletonLoader() {
  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-sm p-5 animate-pulse">
      {/* Badges */}
      <div className="flex gap-2">
        <div className="h-6 w-32 rounded-full bg-slate-200 dark:bg-slate-700" />
        <div className="h-6 w-20 rounded-full bg-slate-200 dark:bg-slate-700" />
      </div>

      {/* Message lines */}
      <div className="flex flex-col gap-2">
        <div className="h-3.5 w-full rounded bg-slate-200 dark:bg-slate-700" />
        <div className="h-3.5 w-5/6 rounded bg-slate-200 dark:bg-slate-700" />
        <div className="h-3.5 w-4/6 rounded bg-slate-200 dark:bg-slate-700" />
      </div>

      {/* Collapsible placeholder */}
      <div className="h-9 w-full rounded-xl bg-slate-100 dark:bg-slate-800" />
      <div className="h-9 w-full rounded-xl bg-slate-100 dark:bg-slate-800" />

      {/* Table skeleton */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
        <div className="h-9 bg-slate-100 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700" />
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-8 border-b border-slate-100 dark:border-slate-800 last:border-0 bg-white dark:bg-slate-900 flex items-center px-3 gap-4"
          >
            <div className="h-2.5 w-24 rounded bg-slate-200 dark:bg-slate-700" />
            <div className="h-2.5 w-16 rounded bg-slate-200 dark:bg-slate-700" />
            <div className="h-2.5 w-20 rounded bg-slate-200 dark:bg-slate-700" />
          </div>
        ))}
      </div>
    </div>
  );
}
