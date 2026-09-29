"""Maps a finished graph node to the next streamed status. Pure function."""

FIRST_STATUS = {
    "PDF": "searching_pdf",
    "BOTH": "searching_pdf",
    "WEB": "searching_web",
    "SUMMARY": "summarizing",
    "CLARIFY": "generating",
}


def status_after(node, state):
    """Status to emit after `node` finished, or None if nothing to emit."""
    route = state.get("route")
    if node == "planner":
        return FIRST_STATUS.get(route, "generating")
    if node == "search_pdf":
        return "searching_web" if route == "BOTH" else "generating"
    if node == "search_web":
        return "generating"
    if node == "generate":
        return "reflecting"
    if node == "reflect" and not state.get("complete"):
        return "searching_web" if route == "WEB" else "searching_pdf"
    return None
