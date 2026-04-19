from datetime import datetime, timezone

from newsbot.domain import CanonicalEvent, Sector
from newsbot.state.snapshot import load_snapshot, save_snapshot
from newsbot.state.store import StateStore


def test_snapshot_roundtrip(tmp_path) -> None:
    snapshot_path = tmp_path / "state.json"
    store = StateStore(x_monthly_budget=40, x_correction_budget=10)
    now = datetime.now(timezone.utc)
    store.add_event(
        CanonicalEvent(
            event_id="evt-1",
            sector=Sector.MACRO,
            headline="Fed decision",
            body="Policy update",
            first_seen_at=now,
            updated_at=now,
            entities={"FED"},
            witnesses=[],
        )
    )
    store.x_used = 3

    save_snapshot(str(snapshot_path), store)
    loaded = load_snapshot(str(snapshot_path))

    assert loaded is not None
    assert loaded.get_event("evt-1") is not None
    assert loaded.x_used == 3
