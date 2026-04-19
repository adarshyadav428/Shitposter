from __future__ import annotations

import re

from newsbot.domain import CanonicalEvent


def extract_claims(event: CanonicalEvent) -> dict:
    text = f"{event.headline}. {event.body}".strip()
    numbers = re.findall(r"\b\d+(?:\.\d+)?%?\b", text)
    entities = sorted(event.entities)
    return {
        "headline": event.headline,
        "numbers": numbers,
        "entities": entities,
        "source_count": len(event.witnesses),
        "raw": text,
    }
