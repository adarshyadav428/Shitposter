from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable

from newsbot.domain import RawEvent, SourceTier


@dataclass(slots=True)
class SourceSpec:
    source_id: str
    source_family: str
    tier: SourceTier
    sector_hint: str
    reputation_floor: float = 0.6


class Ingestor(ABC):
    spec: SourceSpec

    @abstractmethod
    async def poll(self) -> Iterable[RawEvent]:
        raise NotImplementedError
