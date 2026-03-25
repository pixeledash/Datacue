import type { ChatResponse, HistoryEntry } from "@/types";

const HISTORY_KEY = "datacue_history";
const LAST_RESULT_KEY = "datacue_last_result";
const MAX_HISTORY = 30;

export function loadHistory(): HistoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? (JSON.parse(raw) as HistoryEntry[]) : [];
  } catch {
    return [];
  }
}

export function saveHistory(entries: HistoryEntry[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(
      HISTORY_KEY,
      JSON.stringify(entries.slice(0, MAX_HISTORY))
    );
  } catch {
    // Ignore quota errors
  }
}

export function addHistoryEntry(
  query: string,
  response: ChatResponse
): HistoryEntry[] {
  const existing = loadHistory();
  const entry: HistoryEntry = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    query,
    timestamp: Date.now(),
    response,
  };
  const updated = [entry, ...existing].slice(0, MAX_HISTORY);
  saveHistory(updated);
  return updated;
}

export function clearHistory(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(HISTORY_KEY);
}

export function saveLastResult(response: ChatResponse): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(LAST_RESULT_KEY, JSON.stringify(response));
  } catch {
    // Ignore quota errors
  }
}

export function loadLastResult(): ChatResponse | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(LAST_RESULT_KEY);
    return raw ? (JSON.parse(raw) as ChatResponse) : null;
  } catch {
    return null;
  }
}
