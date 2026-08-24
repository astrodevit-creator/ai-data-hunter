"""ai-data-hunter.

"AI Data Hunter" — discover isn't required to be online, but extraction,
normalization, deduplication and validation are. This module takes raw scraped
records (from any source: Firecrawl, requests, Playwright) and turns them into a
clean, deduplicated, schema-validated dataset. Pure stdlib; the fetcher is
pluggable so it works with or without network.

> Original project, aligned with the "AI Web Scraping / Data Hunter" trend.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


PRICE_RE = re.compile(r"[\$€£]?\s*([\d][\d.,]*)")


def parse_price(raw: str) -> Optional[float]:
    """Parse a price from messy text. Handles $89.99, 89,99 MAD, 1.234,50 €."""
    if not raw:
        return None
    # normalize: keep digits, dot, comma
    s = raw.replace(" ", "")
    # EU format like 1.234,50 -> 1234.50 ; simple 89,99 -> 89.99
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        # comma as decimal if it's the last separator with 1-2 digits after
        parts = s.split(",")
        if len(parts) == 2 and len(parts[1]) in (1, 2):
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
    m = PRICE_RE.search(s)
    if not m:
        return None
    try:
        return round(float(m.group(1)), 2)
    except ValueError:
        return None


@dataclass
class Record:
    source: str
    name: str
    price: Optional[float] = None
    url: str = ""
    extra: Dict = field(default_factory=dict)
    _hash: str = ""

    def __post_init__(self):
        self._hash = self.fingerprint()

    def fingerprint(self) -> str:
        base = f"{self.source.lower()}|{self.name.lower().strip()}"
        return hashlib.sha256(base.encode()).hexdigest()[:16]


def normalize(records: List[Record]) -> List[Record]:
    out: List[Record] = []
    seen = set()
    for r in records:
        if r._hash in seen:
            continue
        seen.add(r._hash)
        if r.price is not None:
            r.price = round(r.price, 2)
        out.append(r)
    return out


def validate(records: List[Record], *, require_price: bool = False,
             max_price: Optional[float] = None) -> List[Record]:
    out: List[Record] = []
    for r in records:
        if not r.name or not r.name.strip():
            continue
        if require_price and r.price is None:
            continue
        if max_price is not None and r.price is not None and r.price > max_price:
            continue
        out.append(r)
    return out


def hunt(fetch: Callable[[str], List[Record]], urls: List[str]) -> List[Record]:
    """Run the full pipeline: fetch from each url, normalize, validate."""
    raw: List[Record] = []
    for u in urls:
        raw.extend(fetch(u))
    return validate(normalize(raw))
