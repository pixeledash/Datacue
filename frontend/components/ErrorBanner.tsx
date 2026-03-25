import { AlertCircle, ShieldAlert, Ban, AlertTriangle, MessageSquareOff } from "lucide-react";
import { getErrorMessage } from "@/lib/errorMessages";

const ERROR_ICONS: Record<string, React.ReactNode> = {
  INVALID_QUERY: <AlertCircle className="w-4 h-4" />,
  PROMPT_INJECTION: <ShieldAlert className="w-4 h-4" />,
  SQL_INJECTION: <ShieldAlert className="w-4 h-4" />,
  OFFTOPIC: <MessageSquareOff className="w-4 h-4" />,
  COMPLEXITY: <AlertTriangle className="w-4 h-4" />,
  SEARCH_ERROR: <Ban className="w-4 h-4" />,
  NO_RESULTS: <Ban className="w-4 h-4" />,
  ODATA_BUILD_ERROR: <AlertCircle className="w-4 h-4" />,
};

interface ErrorBannerProps {
  errorType: string | null | undefined;
  message?: string | null;
}

export default function ErrorBanner({ errorType, message }: ErrorBannerProps) {
  const icon = errorType
    ? (ERROR_ICONS[errorType] ?? <AlertCircle className="w-4 h-4" />)
    : <AlertCircle className="w-4 h-4" />;

  const displayMessage = message || getErrorMessage(errorType);

  return (
    <div className="flex items-start gap-3 rounded-xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/40 px-4 py-3 text-red-700 dark:text-red-400">
      <span className="mt-0.5 flex-shrink-0">{icon}</span>
      <div>
        {errorType && (
          <p className="text-xs font-semibold uppercase tracking-wide text-red-500 dark:text-red-500 mb-0.5">
            {errorType.replace(/_/g, " ")}
          </p>
        )}
        <p className="text-sm">{displayMessage}</p>
      </div>
    </div>
  );
}
