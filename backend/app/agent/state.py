"""Shared state that flows through the LangGraph agent."""
from typing import List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    question: str
    chat_history: List[dict]
    document_id: Optional[str]
    has_document: bool
    route: str            # PDF | WEB | BOTH | SUMMARY | CLARIFY
    search_query: str     # refined by the reflection loop
    pdf_context: List[dict]
    web_context: List[dict]
    draft: str
    answer: str
    sources: List[dict]
    reflections: int
    complete: bool
    clarify: bool
