"""Parsing for planner and reflection LLM output. Standard library only."""
import json
import re

VALID_ROUTES = {"PDF", "WEB", "BOTH", "SUMMARY", "CLARIFY"}
_ROUTE_WORD = re.compile(r"\b(PDF|WEB|BOTH|SUMMARY|CLARIFY)\b", re.IGNORECASE)


def parse_route(raw, has_document):
    """Turns raw planner output into a valid route.

    Fallback order: JSON "route" field, then the first route word found in the
    text, then PDF if a document is loaded, otherwise WEB. Routes that need a
    document are downgraded to WEB when none is loaded.
    """
    route = None
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                value = data.get("route")
                if isinstance(value, str):
                    route = value.strip().upper()
        except (json.JSONDecodeError, TypeError):
            pass
        if route not in VALID_ROUTES:
            match = _ROUTE_WORD.search(raw)
            route = match.group(1).upper() if match else None
    if route not in VALID_ROUTES:
        route = "PDF" if has_document else "WEB"
    if not has_document and route in ("PDF", "BOTH", "SUMMARY"):
        route = "WEB"
    return route


def parse_reflection(raw):
    """Returns (complete, refined_query). Defaults to complete=True so an
    unparseable reflection delivers the draft instead of looping."""
    complete, refined = True, ""
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                complete = bool(data.get("complete", True))
                refined = str(data.get("refined_query") or "").strip()
        except (json.JSONDecodeError, TypeError):
            lowered = raw.lower()
            if '"complete": false' in lowered or "'complete': false" in lowered:
                complete = False
    return complete, refined
