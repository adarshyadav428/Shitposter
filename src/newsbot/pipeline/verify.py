from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from newsbot.domain import CanonicalEvent, SourceTier

TIER_WEIGHT = {
    SourceTier.T1: 1.0,
    SourceTier.T2: 0.4,
    SourceTier.T3: 0.1,
}


@dataclass(slots=True)
class VerifyResult:
    publish: bool
    reason: str
    confidence: float


class VerifyEngine:
    def __init__(self, t2_hold_seconds: int = 90, min_confidence: float = 0.6) -> None:
        self.t2_hold = timedelta(seconds=t2_hold_seconds)
        self.min_confidence = min_confidence

    def evaluate(self, event: CanonicalEvent) -> VerifyResult:
        witnesses = event.witnesses
        t1 = [w for w in witnesses if w.source_tier == SourceTier.T1]
        t2 = [w for w in witnesses if w.source_tier == SourceTier.T2]
        t3 = [w for w in witnesses if w.source_tier == SourceTier.T3]

        confidence = sum(TIER_WEIGHT[w.source_tier] * w.reputation for w in witnesses)

        if t1:
            if confidence >= self.min_confidence:
                return VerifyResult(True, "t1_single_witness", confidence)
            return VerifyResult(False, "t1_low_confidence", confidence)

        if len(t2) >= 2:
            independent_families = {w.source_family for w in t2}
            if len(independent_families) >= 2 and confidence >= self.min_confidence:
                return VerifyResult(True, "t2_two_independent", confidence)
            return VerifyResult(False, "t2_not_independent", confidence)

        if len(t2) == 1 and not t1:
            age = event.updated_at - event.first_seen_at
            if age >= self.t2_hold:
                return VerifyResult(False, "t2_single_expired", confidence)
            return VerifyResult(False, "t2_single_waiting", confidence)

        if t3 and not (t1 or t2):
            return VerifyResult(False, "t3_only_signal", confidence)

        return VerifyResult(False, "insufficient_witnesses", confidence)
