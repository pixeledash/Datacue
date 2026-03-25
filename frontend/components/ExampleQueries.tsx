import { Sparkles } from "lucide-react";

const EXAMPLES = [
  "Show me sales orders for customer C001",
  "List open purchase orders from last month",
  "What are the top 10 materials by stock quantity?",
  "Show delivery schedules for vendor V100",
  "Give me a summary of accounts payable invoices",
  "List all customers with overdue payments",
];

interface ExampleQueriesProps {
  onSelect: (query: string) => void;
}

export default function ExampleQueries({ onSelect }: ExampleQueriesProps) {
  return (
    <div className="flex flex-col items-center gap-6 py-8">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-blue-100 dark:bg-blue-900/40 mb-3">
          <Sparkles className="w-6 h-6 text-blue-600 dark:text-blue-400" />
        </div>
        <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
          Ask about your SAP data
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Type a question in plain English and get instant insights
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-2xl">
        {EXAMPLES.map((example) => (
          <button
            key={example}
            onClick={() => onSelect(example)}
            className="text-left px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-blue-400 dark:hover:border-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 text-sm text-slate-600 dark:text-slate-300 transition-all shadow-sm"
          >
            {example}
          </button>
        ))}
      </div>
    </div>
  );
}
