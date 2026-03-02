"""
utils/validation.py
-------------------
All input validation and sanitisation logic, ported from app_e5_large.py.
No Streamlit dependency — pure Python only.
"""

import re
from html import escape


# ─────────────────────────────────────────────
# Custom exceptions
# ─────────────────────────────────────────────

class QueryValidationError(Exception):
    """Raised when a query fails any validation step."""

    def __init__(self, message: str, error_type: str = "INVALID_QUERY"):
        super().__init__(message)
        self.error_type = error_type


# ─────────────────────────────────────────────
# Core validators
# ─────────────────────────────────────────────

def validate_and_sanitize_query(query: str, max_length: int = 500) -> str:
    """
    Validate length, sanitise HTML, strip dangerous patterns, normalise whitespace.

    Returns:
        Sanitised query string.

    Raises:
        QueryValidationError
    """
    if not query or not query.strip():
        raise QueryValidationError("Query cannot be empty", "INVALID_QUERY")

    if len(query) > max_length:
        raise QueryValidationError(
            f"Query too long. Maximum {max_length} characters allowed (current: {len(query)})",
            "INVALID_QUERY",
        )

    query = query.strip()

    # HTML-escape to neutralise XSS vectors
    query = escape(query)

    dangerous_patterns = [
        (r"<script.*?>.*?</script>", "Script tags not allowed"),
        (r"javascript:",              "JavaScript protocol not allowed"),
        (r"on\w+\s*=",               "Event handlers not allowed"),
        (r"eval\s*\(",               "Eval calls not allowed"),
        (r"<iframe",                 "iFrame tags not allowed"),
        (r"<object",                 "Object tags not allowed"),
        (r"<embed",                  "Embed tags not allowed"),
    ]
    for pattern, msg in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            raise QueryValidationError(f"Security violation: {msg}", "INVALID_QUERY")

    # Reject queries that are mostly special characters
    special_ratio = len(re.findall(r"[^a-zA-Z0-9\s]", query)) / len(query) if query else 0
    if special_ratio > 0.5:
        raise QueryValidationError(
            "Query contains too many special characters", "INVALID_QUERY"
        )

    # Normalise whitespace
    query = " ".join(query.split())

    if len(query) < 2:
        raise QueryValidationError(
            "Query too short. Please enter at least 2 characters", "INVALID_QUERY"
        )

    return query


def check_query_complexity(query: str) -> tuple[bool, str]:
    """
    Guard against DoS-style queries (extremely long, highly repetitive, etc.).

    Returns:
        (is_valid, error_message)
    """
    words = query.lower().split()

    if len(words) > 100:
        return False, "Query too complex. Maximum 100 words allowed"

    if len(words) > 10:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.3:
            return False, "Query appears to contain excessive repetition"

    if len(words) > 5:
        single_char = [w for w in words if len(w) == 1]
        if len(single_char) / len(words) > 0.5:
            return False, "Query contains too many single characters"

    return True, ""


def detect_sql_injection(query: str) -> bool:
    """Return True if the query looks like a SQL injection attempt."""
    patterns = [
        r"\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC)\b.*\b(FROM|WHERE|TABLE)\b",
        r"[;]\s*(DROP|DELETE|UPDATE)",
        r"--\s*$",
        r"/\*.*\*/",
        r"\bOR\b.*=.*",
        r"\bAND\b.*=.*",
        r"'\s*OR\s*'",
    ]
    for p in patterns:
        if re.search(p, query, re.IGNORECASE):
            return True
    return False


def detect_prompt_injection(query: str) -> tuple[bool, str]:
    """
    Detect prompt injection / jailbreak attempts.

    Returns:
        (is_detected, attack_type_description)
    """
    injection_patterns = [
        # Instruction override
        (r"ignore\s+(previous|above|all|prior)\s+(instructions|prompts|commands|rules)",
         "System instruction override"),
        (r"disregard\s+(previous|above|all|prior)\s+(instructions|prompts|commands)",
         "Instruction disregard"),
        (r"forget\s+(everything|all|previous|above)",
         "Memory manipulation"),
        # Role manipulation
        (r"you\s+are\s+now\s+",         "Role override"),
        (r"act\s+as\s+(if\s+)?you\s+(are|were)", "Role manipulation"),
        (r"pretend\s+(you\s+are|to\s+be)", "Role pretense"),
        (r"new\s+(role|character|persona|instructions)", "New role assignment"),
        # Prompt-structure injection
        (r"system\s*:\s*",    "System prompt injection"),
        (r"assistant\s*:\s*", "Assistant prompt injection"),
        (r"user\s*:\s*",      "User prompt injection"),
        # Special tokens
        (r"<\|im_start\|>",  "Special token injection"),
        (r"<\|im_end\|>",    "Special token injection"),
        (r"\[INST\]",        "Instruction token"),
        (r"\[/INST\]",       "Instruction token"),
        (r"<\|system\|>",    "System token"),
        (r"<\|assistant\|>", "Assistant token"),
        (r"<\|user\|>",      "User token"),
        # Jailbreaks
        (r"(DAN|developer|god)\s+mode", "Jailbreak attempt"),
        (r"jailbreak",                  "Jailbreak keyword"),
        (r"unrestricted",               "Restriction bypass"),
        # Output manipulation
        (r"output\s+format\s*:",    "Output format override"),
        (r"respond\s+only\s+with",  "Response restriction"),
        (r"from\s+now\s+on",        "Behaviour modification"),
        # Delimiter confusion
        (r"---+\s*system",           "Delimiter confusion"),
        (r"###\s*(system|instruction)", "Delimiter confusion"),
        (r"```\s*(system|instruction)", "Code-block confusion"),
    ]

    for pattern, attack_type in injection_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return True, attack_type

    # Heuristic: excessive imperative / control words
    instruction_words = {"must", "should", "always", "never", "only", "exactly", "strictly"}
    word_list = query.lower().split()
    instruction_count = sum(1 for w in word_list if w in instruction_words)
    if len(word_list) > 5 and instruction_count / len(word_list) > 0.3:
        return True, "Excessive instruction language"

    return False, ""


def sanitize_llm_output(output: str, max_length: int = 5000) -> str:
    """
    Strip leaked special tokens, redact credentials, truncate if oversized.
    """
    if not output:
        return ""

    # Remove leaked LLM control tokens
    token_patterns = [
        r"<\|.*?\|>",
        r"\[INST\].*?\[/INST\]",
        r"<\|im_start\|>.*?<\|im_end\|>",
    ]
    for p in token_patterns:
        output = re.sub(p, "", output, flags=re.DOTALL)

    # Remove leaked system-prompt preambles
    for p in [
        r"(?i)system\s*:\s*you\s+are.*?\n\n",
        r"(?i)assistant\s*:\s*",
    ]:
        output = re.sub(p, "", output)

    # Redact dangerous SQL
    for cmd in ["DROP TABLE", "DELETE FROM", "UPDATE", "INSERT INTO", "ALTER TABLE"]:
        output = re.sub(
            rf"\b{re.escape(cmd)}\b.*?(;|\n|$)",
            "[REDACTED SQL COMMAND]",
            output,
            flags=re.IGNORECASE,
        )

    # Redact credential-like patterns
    output = re.sub(
        r"(password|api[_-]?key|token|secret)\s*[:=]\s*\S+",
        "[REDACTED]",
        output,
        flags=re.IGNORECASE,
    )

    if len(output) > max_length:
        output = output[:max_length] + "\n\n[Output truncated for safety]"

    return output.strip()


def detect_offtopic_query(query: str) -> tuple[bool, str]:
    """Return (is_offtopic, reason) for queries clearly unrelated to SAP CDS."""
    q = query.lower()

    offtopic_patterns = [
        (r"\b(computer|laptop|pc|display|screen|monitor)\s+(not|won\'?t|can\'?t|doesn\'?t)\s+(work|turn\s+on|boot|start)",
         "Hardware troubleshooting"),
        (r"\b(fix|repair|troubleshoot)\s+(my|the|a)\s+(computer|laptop|pc|phone|device)",
         "Device troubleshooting"),
        (r"\bwhite\s+screen\b.*\b(problem|issue|error)", "Hardware issue"),
        (r"\bhow\s+are\s+you\b",            "Personal question"),
        (r"\btell\s+me\s+about\s+(yourself|you)\b", "Personal question"),
        (r"\bwho\s+are\s+you\b",            "Personal question"),
        (r"\b(weather|temperature|forecast)\b.*\b(today|tomorrow)", "Weather question"),
        (r"\b(news|current\s+events|latest\s+news)\b", "News question"),
        (r"\b(recipe|cook|bake|ingredient)s?\b.*\b(how\s+to|make)", "Cooking question"),
        (r"\bsolve\s+(this|the)\s+(equation|problem|math)", "Math question"),
        (r"\b(python|javascript|java|c\+\+)\s+(code|function|error)", "General programming"),
        (r"\bhow\s+to\s+(code|program|develop)\s+", "General programming"),
        (r"\b(symptom|disease|medicine|doctor|health)\s", "Medical question"),
        (r"\b(directions|route|navigate)\s+to\b", "Navigation question"),
        (r"\bbest\s+(price|deal|discount)\s+(for|on)\b", "Shopping question"),
    ]

    for pattern, reason in offtopic_patterns:
        if re.search(pattern, q):
            return True, f"{reason} (not related to CDS views)"

    # For long queries: require at least one SAP/business keyword
    relevant_keywords = [
        "sap", "s4hana", "s/4", "erp", "hana", "abap",
        "cds", "view", "views", "core data services",
        "data", "table", "database", "query", "select", "field", "record",
        "customer", "sales", "order", "invoice", "material", "vendor",
        "purchase", "inventory", "financial", "accounting", "employee",
        "product", "warehouse", "delivery", "shipment", "payment",
        "show", "find", "search", "get", "list", "display", "retrieve",
    ]
    words = q.split()
    if len(words) > 20:
        if not any(kw in q for kw in relevant_keywords):
            return True, "Query appears unrelated to SAP CDS views (no relevant keywords found)"

    return False, ""


def validate_query_intent(query: str) -> tuple[bool, str]:
    """
    Check that the overall intent of the query is appropriate.
    Guards against mixed-intent queries that hide off-topic content.
    """
    is_offtopic, reason = detect_offtopic_query(query)
    if is_offtopic:
        return False, f"Off-topic query: {reason}"

    # Multi-sentence queries: check if the majority of sentences are off-topic
    sentences = re.split(r"[.!?]+", query)
    if len(sentences) > 3:
        offtopic_count = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 5:
                continue
            is_off, _ = detect_offtopic_query(sentence)
            if is_off:
                offtopic_count += 1
        if offtopic_count > len(sentences) / 2:
            return False, "Query contains too much off-topic content"

    return True, ""


# ─────────────────────────────────────────────
# Unified entry point used by pipeline_service
# ─────────────────────────────────────────────

def run_all_validations(query: str, max_length: int = 500) -> str:
    """
    Run every validation step in order.

    Returns:
        safe_query (str) — sanitised and validated query.

    Raises:
        QueryValidationError with .error_type set to one of:
            INVALID_QUERY | SQL_INJECTION | PROMPT_INJECTION | OFFTOPIC | COMPLEXITY
    """
    # 1. Basic sanitisation
    safe_query = validate_and_sanitize_query(query, max_length)

    # 2. Prompt injection
    is_injection, attack_type = detect_prompt_injection(safe_query)
    if is_injection:
        raise QueryValidationError(
            f"Potential prompt injection detected: {attack_type}",
            "PROMPT_INJECTION",
        )

    # 3. Off-topic intent
    is_valid_intent, intent_error = validate_query_intent(safe_query)
    if not is_valid_intent:
        raise QueryValidationError(intent_error, "OFFTOPIC")

    # 4. SQL injection
    if detect_sql_injection(safe_query):
        raise QueryValidationError(
            "Potential SQL injection pattern detected in query",
            "SQL_INJECTION",
        )

    # 5. Complexity
    is_valid, complexity_error = check_query_complexity(safe_query)
    if not is_valid:
        raise QueryValidationError(complexity_error, "COMPLEXITY")

    return safe_query
