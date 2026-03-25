export const ERROR_MESSAGES: Record<string, string> = {
  INVALID_QUERY:
    "Query is too short, too long, or contains invalid characters.",
  PROMPT_INJECTION:
    "This query was flagged as a potential injection attempt.",
  OFFTOPIC: "This query doesn't relate to SAP business data.",
  SQL_INJECTION: "Query contains disallowed patterns.",
  COMPLEXITY: "Query is too complex — try simplifying it.",
  SEARCH_ERROR: "No matching SAP data views were found.",
  NO_RESULTS: "No matching SAP data views were found.",
  ODATA_BUILD_ERROR: "Could not construct a valid SAP query.",
  BAD_REQUEST: "Invalid request sent to the server.",
  INTERNAL_ERROR: "An internal server error occurred. Please try again.",
};

export function getErrorMessage(errorType: string | null | undefined): string {
  if (!errorType) return "An unexpected error occurred. Please try again.";
  return (
    ERROR_MESSAGES[errorType] ??
    "An unexpected error occurred. Please try again."
  );
}
