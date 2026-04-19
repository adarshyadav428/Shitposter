from datetime import datetime, timedelta, timezone

from newsbot.domain import CanonicalEvent, Sector, SourceTier, Witness
from newsbot.pipeline.verify import VerifyEngine


def _w(source_id: str, family: str, tier: SourceTier, rep: float = 0.9) -> Witness:
    now = datetime.now(timezone.utc)
    return Witness(
        source_id=source_id,
        source_family=family,
        source_tier=tier,
        reputation=rep,
        seen_at=now,
        url="https://example.com",
        text="sample",
    )


def test_t1_single_publishes() -> None:
    now = datetime.now(timezone.utc)
    ev = CanonicalEvent(
        event_id="e1",
        sector=Sector.MACRO,
        headline="Fed action",
        body="",
        first_seen_at=now,
        updated_at=now,
        entities=set(),
        witnesses=[_w("sec", "sec", SourceTier.T1)],
    )
    result = VerifyEngine().evaluate(ev)
    assert result.publish is True


def test_two_independent_t2_publish() -> None:
    now = datetime.now(timezone.utc)
    ev = CanonicalEvent(
        event_id="e2",
        sector=Sector.GEOPOLITICS,
        headline="Event",
        body="",
        first_seen_at=now,
        updated_at=now,
        entities=set(),
        witnesses=[
            _w("r1", "reuters", SourceTier.T2),
            _w("a1", "ap", SourceTier.T2),
        ],
    )
    result = VerifyEngine().evaluate(ev)
    assert result.publish is True


def test_single_t2_wait_then_expire() -> None:
    now = datetime.now(timezone.utc)
    ev = CanonicalEvent(
        event_id="e3",
        sector=Sector.CRYPTO,
        headline="Exchange halt",
        body="",
        first_seen_at=now,
        updated_at=now + timedelta(seconds=20),
        entities=set(),
        witnesses=[_w("j1", "journalist", SourceTier.T2)],
    )
    verify = VerifyEngine(t2_hold_seconds=90)
    waiting = verify.evaluate(ev)
    assert waiting.publish is False
    assert waiting.reason == "t2_single_waiting"

    ev.updated_at = now + timedelta(seconds=120)
    expired = verify.evaluate(ev)
    assert expired.publish is False
    assert expired.reason == "t2_single_expired"
