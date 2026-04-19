from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class Sector(str, Enum):
    GEOPOLITICS = "geopolitics"
    MACRO = "macroeconomics"
    CRYPTO = "crypto"


class SourceTier(int, Enum):
    T1 = 1
    T2 = 2
    T3 = 3


@dataclass(slots=True)
class Witness:
    source_id: str
    source_family: str
    source_tier: SourceTier
    reputation: float
    seen_at: datetime
    url: str
    text: str


@dataclass(slots=True)
class RawEvent:
    event_id: str
    sector: Sector
    headline: str
    body: str
    seen_at: datetime
    witness: Witness
    entities: set[str] = field(default_factory=set)


@dataclass(slots=True)
class CanonicalEvent:
    event_id: str
    sector: Sector
    headline: str
    body: str
    first_seen_at: datetime
    updated_at: datetime
    entities: set[str]
    witnesses: list[Witness] = field(default_factory=list)

    def add_witness(self, witness: Witness) -> None:
        self.witnesses.append(witness)
        self.updated_at = max(self.updated_at, witness.seen_at)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
