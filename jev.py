"""Jev client (TypeSafe's decision model) via Vercel AI Gateway.

Jev answers narrow typed questions (boolean / choice / score) about a small
``state`` string. Use it to gate or triage scraped records, e.g. "is this a
real product listing?". Stdlib-only; the transport is pluggable for tests.

Set the key in the environment (never commit it):

    export AI_GATEWAY_API_KEY=...
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Callable, Dict, List, Optional, Tuple

from data_hunter import Record

JEV_URL = "https://ai-gateway.vercel.sh/v1/evaluate"
JEV_MODEL = "typesafe-ai/jev"

Transport = Callable[[str, Dict, Dict], Dict]


class JevError(RuntimeError):
    pass


def _load_dotenv(path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")) -> None:
    """Load KEY=VALUE lines from the repo's .env without overriding real env vars."""
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))
    except FileNotFoundError:
        pass


def _http_post(url: str, headers: Dict, payload: Dict) -> Dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise JevError(f"Jev HTTP {e.code}: {e.read().decode(errors='replace')}") from e


def evaluate(state: str, questions: Dict[str, Dict], *,
             api_key: Optional[str] = None,
             transport: Transport = _http_post) -> Dict:
    """Send one evaluate request and return the parsed JSON response.

    ``questions`` maps a name to a spec, e.g.
    ``{"isProduct": {"type": "boolean", "instructions": "Is this a product?"}}``.
    """
    if not api_key:
        _load_dotenv()
    key = api_key or os.environ.get("AI_GATEWAY_API_KEY")
    if not key:
        raise JevError("AI_GATEWAY_API_KEY is not set")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {"model": JEV_MODEL, "state": state, "questions": questions}
    return transport(JEV_URL, headers, payload)


def boolean_probability(response: Dict, name: str) -> Optional[float]:
    """Probability for boolean question ``name``.

    Gateway response shape (confirmed against a live call)::

        {"answers": {"<name>": {"type": "boolean", "probability": 0.68}}, ...}
    """
    answer = (response.get("answers") or {}).get(name) or {}
    p = answer.get("probability")
    if isinstance(p, (int, float)) and not isinstance(p, bool):
        return float(p)
    return None


def jev_filter(records: List[Record], instructions: str, *,
               keep_at: float = 0.8, drop_at: float = 0.2,
               **kwargs) -> Tuple[List[Record], List[Record]]:
    """Gate records with a Jev yes/no question.

    Returns ``(kept, uncertain)``. Records with p >= keep_at are kept,
    p <= drop_at are dropped, anything in between is returned as uncertain
    for a human (or a bigger model) to review.
    """
    kept: List[Record] = []
    uncertain: List[Record] = []
    q = {"keep": {"type": "boolean", "instructions": instructions}}
    for r in records:
        state = json.dumps({"source": r.source, "name": r.name,
                            "price": r.price, "url": r.url})
        p = boolean_probability(evaluate(state, q, **kwargs), "keep")
        if p is None:
            uncertain.append(r)
        elif p >= keep_at:
            kept.append(r)
        elif p > drop_at:
            uncertain.append(r)
    return kept, uncertain
