"""Tavily web search over plain HTTPS."""
import os

import requests

TAVILY_URL = "https://api.tavily.com/search"


class WebSearchError(Exception):
    pass


def search_web(query, max_results=5):
    """Returns [{"title", "url", "content"}] for the top web results."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise WebSearchError(
            "TAVILY_API_KEY is not set. Add it to backend/.env and restart the backend."
        )
    try:
        resp = requests.post(
            TAVILY_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
                "include_answer": False,
            },
            timeout=30,
        )
    except requests.RequestException as exc:
        raise WebSearchError(f"Could not reach Tavily: {exc}")
    if resp.status_code != 200:
        raise WebSearchError(f"Tavily error {resp.status_code}: {resp.text[:300]}")
    results = resp.json().get("results", [])
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": (r.get("content") or "")[:800],
        }
        for r in results
    ]
