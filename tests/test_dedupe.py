from datetime import datetime, timezone

from newsbot.domain import RawEvent, Sector, SourceTier, Witness
from newsbot.pipeline.dedupe import DedupeIndex


def _raw(event_id: str, family: str) -> RawEvent:
    now = datetime.now(timezone.utc)
    witness = Witness(
        source_id=f"{family}-{event_id}",
        source_family=family,
        source_tier=SourceTier.T2,
        reputation=0.8,
        seen_at=now,
        url="https://example.com",
        text="Exchange halts withdrawals",
    )
    return RawEvent(
        event_id=event_id,
        sector=Sector.CRYPTO,
        headline="Exchange halts withdrawals",
        body="Infrastructure incident reported.",
        seen_at=now,
        witness=witness,
        entities={"BTC", "ETH"},
    )


def test_duplicate_from_same_family_is_dropped() -> None:
    idx = DedupeIndex()
    a = _raw("a", "family-1")
    b = _raw("b", "family-1")
    assert idx.seen_duplicate(a) is False
    assert idx.seen_duplicate(b) is True


def test_similar_item_from_different_family_is_allowed() -> None:
    idx = DedupeIndex()
    a = _raw("a", "family-1")
    b = _raw("b", "family-2")
    assert idx.seen_duplicate(a) is False
    assert idx.seen_duplicate(b) is False
