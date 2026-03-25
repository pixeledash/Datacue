export type VisualizationType = "table" | "bar_chart" | "line_chart" | "pie_chart" | "none";

export interface Visualization {
  type: VisualizationType;
  title: string;
  columns: string[];
  rows: Record<string, string>[];
  x_axis: string | null;
  y_axis: string | null;
  label_field: string | null;
  value_field: string | null;
}

export interface ChatResponse {
  success: boolean;
  message: string;
  cds_view: string;
  llm1_reasoning: string;
  odata_url: string;
  row_count: number;
  visualization: Visualization;
  error: string | null;
  error_type: string | null;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  faiss_index: string;
  meta_count: number;
  ollama: string;
  sap: string;
  embedding_model: string;
  llm_model: string;
}

export interface HistoryEntry {
  id: string;
  query: string;
  timestamp: number;
  response: ChatResponse;
}
