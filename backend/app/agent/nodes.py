"""LangGraph node functions. Each takes AgentState and returns a state delta."""
from .. import llm, prompts, retrieval, websearch
from .routing import parse_reflection, parse_route

TOP_K = 5
MAX_REFLECTIONS = 2


def _history_text(history):
    if not history:
        return "(none)"
    return "\n".join(f"{m['role']}: {m['content']}" for m in history[-6:])


def plan(state):
    raw = llm.chat(
        [
            {
                "role": "system",
                "content": prompts.PLANNER_SYSTEM.format(
                    has_document="yes" if state.get("has_document") else "no"
                ),
            },
            {
                "role": "user",
                "content": prompts.PLANNER_USER.format(
                    history=_history_text(state.get("chat_history")),
                    question=state["question"],
                ),
            },
        ],
        json_mode=True,
    )
    return {
        "route": parse_route(raw, bool(state.get("has_document"))),
        "search_query": state["question"],
        "reflections": 0,
    }


def search_pdf(state):
    query = state.get("search_query") or state["question"]
    hits = retrieval.search_document(state["document_id"], query, TOP_K)
    return {"pdf_context": hits}


def search_web(state):
    query = state.get("search_query") or state["question"]
    return {"web_context": websearch.search_web(query, TOP_K)}


def _context_block(state):
    parts = []
    route = state.get("route")
    if route in ("PDF", "BOTH"):
        pdf = state.get("pdf_context") or []
        if pdf:
            body = "\n\n".join(f"[p. {c['page']}] {c['text']}" for c in pdf)
        else:
            body = "(no matching passages found)"
        parts.append("Document context:\n" + body)
    if route in ("WEB", "BOTH"):
        web = state.get("web_context") or []
        if web:
            body = "\n\n".join(
                f"[{i + 1}] {r['title']} ({r['url']})\n{r['content']}"
                for i, r in enumerate(web)
            )
        else:
            body = "(no results)"
        parts.append("Web context:\n" + body)
    return "\n\n".join(parts)


def generate(state):
    history = state.get("chat_history")
    history_block = f"Recent conversation:\n{_history_text(history)}\n\n" if history else ""
    draft = llm.chat(
        [
            {"role": "system", "content": prompts.GENERATE_SYSTEM},
            {
                "role": "user",
                "content": prompts.GENERATE_USER.format(
                    history_block=history_block,
                    question=state["question"],
                    context=_context_block(state),
                ),
            },
        ]
    )
    return {"draft": draft}


def _build_sources(state):
    sources = []
    seen_pages = set()
    for chunk in state.get("pdf_context") or []:
        if chunk["page"] not in seen_pages:
            seen_pages.add(chunk["page"])
            sources.append({"type": "pdf", "page": chunk["page"]})
    for result in state.get("web_context") or []:
        sources.append({"type": "web", "title": result["title"], "url": result["url"]})
    return sources


def reflect(state):
    reflections = int(state.get("reflections") or 0) + 1
    raw = llm.chat(
        [
            {"role": "system", "content": prompts.REFLECT_SYSTEM},
            {
                "role": "user",
                "content": f"Question: {state['question']}\n\nDraft answer:\n{state.get('draft', '')}",
            },
        ],
        json_mode=True,
    )
    complete, refined = parse_reflection(raw)
    if complete or reflections >= MAX_REFLECTIONS:
        return {
            "complete": True,
            "reflections": reflections,
            "answer": state.get("draft", ""),
            "sources": _build_sources(state),
        }
    return {
        "complete": False,
        "reflections": reflections,
        "search_query": refined or state["question"],
    }


def summarize(state):
    chunks = retrieval.get_all_chunks(state["document_id"])
    batches, current, size = [], [], 0
    for chunk in chunks:
        piece = f"[p. {chunk['page']}] {chunk['text']}"
        if size + len(piece) > 9000 and current:
            batches.append("\n\n".join(current))
            current, size = [], 0
        current.append(piece)
        size += len(piece)
    if current:
        batches.append("\n\n".join(current))

    partials = [
        llm.chat(
            [
                {"role": "system", "content": prompts.SUMMARY_SECTION_SYSTEM},
                {"role": "user", "content": batch},
            ]
        )
        for batch in batches
    ]
    if len(partials) == 1:
        summary = partials[0]
    else:
        summary = llm.chat(
            [
                {"role": "system", "content": prompts.SUMMARY_COMBINE_SYSTEM},
                {"role": "user", "content": "\n\n".join(partials)},
            ],
            max_tokens=1500,
        )
    last_page = chunks[-1]["page"] if chunks else 0
    return {
        "answer": summary,
        "complete": True,
        "reflections": 0,
        "sources": [{"type": "pdf", "label": f"Entire document (pages 1-{last_page})"}],
    }


def clarify(state):
    question = llm.chat(
        [
            {"role": "system", "content": prompts.CLARIFY_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Recent conversation:\n{_history_text(state.get('chat_history'))}\n\n"
                    f"Vague question: {state['question']}"
                ),
            },
        ]
    )
    return {
        "answer": question,
        "clarify": True,
        "complete": True,
        "reflections": 0,
        "sources": [],
    }
