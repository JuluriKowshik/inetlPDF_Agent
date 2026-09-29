"""Groq chat completions over plain HTTPS. One retry with backoff on 429/5xx."""
import os
import time

import requests

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-20b"


class LLMError(Exception):
    pass


def chat(messages, json_mode=False, temperature=0.2, max_tokens=1024):
    """Sends messages to Groq and returns the assistant text."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise LLMError("GROQ_API_KEY is not set. Add it to backend/.env and restart the backend.")

    payload = {
        "model": os.getenv("GROQ_MODEL", DEFAULT_MODEL),
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    last_error = "Unknown Groq error"
    for attempt in (1, 2):
        retryable = False
        try:
            resp = requests.post(
                GROQ_URL,
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=60,
            )
        except requests.RequestException as exc:
            last_error = f"Could not reach Groq: {exc}"
            retryable = True
        else:
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"].get("content")
                return (content or "").strip()
            last_error = f"Groq error {resp.status_code}: {resp.text[:300]}"
            retryable = resp.status_code in (429, 500, 502, 503)
        if attempt == 1 and retryable:
            time.sleep(2)
            continue
        break
    raise LLMError(last_error)
