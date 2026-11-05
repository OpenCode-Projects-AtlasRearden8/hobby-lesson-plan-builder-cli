"""Optional drafting help from any OpenAI-compatible chat endpoint.

This module is strictly opt-in: `lesson-builder --draft`. By default the
CLI never talks to the network. Drafting only suggested friendly blurbs;
the pacing, cards, supplies, and checkboxes are always computed locally.

Defaults target a local Ollama server, which needs no API key. If you
point at a hosted endpoint that requires a key, export it yourself (e.g.
OPENAI_API_KEY will not be read by this tool; use --api-key) — never put
keys in files.
"""

import json
import socket
import urllib.error
import urllib.request
from typing import List, Optional, Sequence

DEFAULT_API_BASE = "http://localhost:11434/v1"
DEFAULT_MODEL = "llama3.2"
TIMEOUT_SECONDS = 120


def build_prompt(items: Sequence[str], session_number: int) -> str:
    topic_lines = "\n".join(f"- {t}" for t in items)
    return (
        "You are a warm, plain-English tutor helping an absolute beginner. "
        "Never condescending. For this lesson session, for each bullet topic "
        "write ONE short encouraging blurb (max 15 words) that says what to "
        "do first in the simplest words. Return plain text, one line per "
        "topic, in the same order. No numbering, no markdown.\n\n"
        f"Session {session_number} topics:\n{topic_lines}"
    )


def request_blurbs(
    items: Sequence[str],
    session_number: int,
    api_base: str = DEFAULT_API_BASE,
    model: str = DEFAULT_MODEL,
    api_key: Optional[str] = None,
    timeout: float = TIMEOUT_SECONDS,
) -> List[str]:
    """POST to {api_base}/chat/completions and return one blurb per topic.

    Raises on network/HTTP errors; callers should catch and fall back to
    local text. Returns [] when the model answered with nothing useful.
    """
    if not items:
        return []
    url = api_base.rstrip("/") + "/chat/completions"
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a friendly tutor. Plain English."},
            {"role": "user", "content": build_prompt(items, session_number)},
        ],
        "stream": False,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, socket.timeout, TimeoutError, json.JSONDecodeError):
        raise ConnectionError(
            f"could not reach drafting endpoint at {url!r} "
            "(it may be offline; drafting is optional)"
        ) from None
    try:
        text = payload["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError):
        return []
    lines = [ln.strip(" -*\t") for ln in text.splitlines() if ln.strip()]
    return lines[: len(items)]


def draft_session_notes(
    items: Sequence[str],
    session_number: int,
    **kwargs,
) -> str:
    """Best-effort friendly note lines; falls back to local text offline."""
    try:
        blurbs = request_blurbs(items, session_number, **kwargs)
    except ConnectionError as exc:
        return f"(Drafting unavailable: {exc})"
    if not blurbs or not any(blurbs):
        return "(The model returned nothing useful — local plan is fine as-is.)"
    return "First things first:\n" + "\n".join(
        f"  - {blurb}" for blurb in blurbs
    )
