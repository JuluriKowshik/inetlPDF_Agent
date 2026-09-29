"""Planner routing tests with a mocked LLM. Run from backend/:

    python -m pytest tests -q
"""
import pytest

from app.agent import nodes
from app.agent.routing import parse_reflection, parse_route

SCENARIOS = [
    ("What is the leave policy?", '{"route": "PDF"}', "PDF"),
    ("Is this leave policy similar to Microsoft's?", '{"route": "BOTH"}', "BOTH"),
    ("Summarize the entire document", '{"route": "SUMMARY"}', "SUMMARY"),
    ("Who is Narendra Modi?", '{"route": "WEB"}', "WEB"),
    ("What about that thing?", '{"route": "CLARIFY"}', "CLARIFY"),
]


@pytest.mark.parametrize("question,llm_reply,expected", SCENARIOS)
def test_planner_routes_each_scenario(monkeypatch, question, llm_reply, expected):
    monkeypatch.setattr(nodes.llm, "chat", lambda *args, **kwargs: llm_reply)
    result = nodes.plan({"question": question, "chat_history": [], "has_document": True})
    assert result["route"] == expected
    assert result["search_query"] == question
    assert result["reflections"] == 0


def test_parse_route_bad_json_falls_back_to_pdf_with_document():
    assert parse_route("this is not json at all", True) == "PDF"


def test_parse_route_bad_json_falls_back_to_web_without_document():
    assert parse_route("still not json", False) == "WEB"


def test_parse_route_downgrades_document_routes_without_document():
    assert parse_route('{"route": "PDF"}', False) == "WEB"
    assert parse_route('{"route": "BOTH"}', False) == "WEB"
    assert parse_route('{"route": "SUMMARY"}', False) == "WEB"


def test_parse_route_reads_route_word_from_messy_text():
    assert parse_route("The best route here is BOTH because it compares.", True) == "BOTH"


def test_parse_reflection_retry_and_finalize():
    assert parse_reflection('{"complete": true}') == (True, "")
    complete, refined = parse_reflection(
        '{"complete": false, "refined_query": "leave policy notice period"}'
    )
    assert complete is False
    assert refined == "leave policy notice period"
    # Unparseable output must fail safe and deliver the draft.
    assert parse_reflection("garbage output")[0] is True
