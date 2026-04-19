from __future__ import annotations

import hashlib

from newsbot.domain import RawEvent


def _token_hash(token: str) -> int:
    return int(hashlib.md5(token.encode()).hexdigest(), 16)


def simhash(text: str, bits: int = 64) -> int:
    v = [0] * bits
    for token in text.lower().split():
        h = _token_hash(token)
        for i in range(bits):
            bit = 1 if (h >> i) & 1 else -1
            v[i] += bit
    result = 0
    for i, weight in enumerate(v):
        if weight >= 0:
            result |= 1 << i
    return result


def hamming_distance(a: int, b: int) -> int:
    return (a ^ b).bit_count()


class DedupeIndex:
    def __init__(self, max_distance: int = 6) -> None:
        self.max_distance = max_distance
        self.fingerprints: dict[str, int] = {}

    def seen_duplicate(self, event: RawEvent) -> bool:
        key = f"{event.headline} {event.body}".strip()
        fp = simhash(key)
        for old in self.fingerprints.values():
            if hamming_distance(fp, old) <= self.max_distance:
                return True
        self.fingerprints[event.event_id] = fp
        return False
