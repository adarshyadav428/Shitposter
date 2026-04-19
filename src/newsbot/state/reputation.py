from __future__ import annotations

from collections import defaultdict


class ReputationModel:
    def __init__(self) -> None:
        self.alpha = defaultdict(lambda: 9.0)
        self.beta = defaultdict(lambda: 1.0)

    def score(self, source_id: str) -> float:
        a = self.alpha[source_id]
        b = self.beta[source_id]
        return a / (a + b)

    def mark_success(self, source_id: str) -> float:
        self.alpha[source_id] += 1.0
        return self.score(source_id)

    def mark_retraction(self, source_id: str) -> float:
        self.beta[source_id] += 1.0
        return self.score(source_id)
