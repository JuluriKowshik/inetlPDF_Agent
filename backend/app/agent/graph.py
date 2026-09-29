"""LangGraph wiring for the IntelliPDF agent.

Flow:
    START -> planner -> (search_pdf | search_web | summarize | clarify)
    BOTH runs search_pdf then search_web, so streamed statuses show real timing.
    search nodes -> generate -> reflect -> (retry search | END)
    summarize -> END, clarify -> END
"""
from langgraph.graph import END, START, StateGraph

from . import nodes
from .state import AgentState


def _after_planner(state):
    return state["route"]


def _after_search_pdf(state):
    return "search_web" if state.get("route") == "BOTH" else "generate"


def _after_reflect(state):
    if state.get("complete"):
        return "end"
    return {"PDF": "search_pdf", "BOTH": "search_pdf", "WEB": "search_web"}.get(
        state.get("route"), "end"
    )


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("planner", nodes.plan)
    graph.add_node("search_pdf", nodes.search_pdf)
    graph.add_node("search_web", nodes.search_web)
    graph.add_node("summarize", nodes.summarize)
    graph.add_node("clarify", nodes.clarify)
    graph.add_node("generate", nodes.generate)
    graph.add_node("reflect", nodes.reflect)

    graph.add_edge(START, "planner")
    graph.add_conditional_edges(
        "planner",
        _after_planner,
        {
            "PDF": "search_pdf",
            "BOTH": "search_pdf",
            "WEB": "search_web",
            "SUMMARY": "summarize",
            "CLARIFY": "clarify",
        },
    )
    graph.add_conditional_edges(
        "search_pdf",
        _after_search_pdf,
        {"search_web": "search_web", "generate": "generate"},
    )
    graph.add_edge("search_web", "generate")
    graph.add_edge("generate", "reflect")
    graph.add_conditional_edges(
        "reflect",
        _after_reflect,
        {"search_pdf": "search_pdf", "search_web": "search_web", "end": END},
    )
    graph.add_edge("summarize", END)
    graph.add_edge("clarify", END)
    return graph.compile()


agent_graph = build_graph()
