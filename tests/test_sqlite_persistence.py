from datetime import datetime, timezone

from newsbot.config import settings
from newsbot.domain import CanonicalEvent, Sector
from newsbot.state.persistence import load_state, save_state
from newsbot.state.snapshot import save_snapshot
from newsbot.state.sqlite_snapshot import load_sqlite_snapshot, save_sqlite_snapshot
from newsbot.state.store import StateStore


def test_sqlite_snapshot_roundtrip(tmp_path) -> None:
    db_path = tmp_path / "state.sqlite"
    store = StateStore(x_monthly_budget=40, x_correction_budget=10)
    now = datetime.now(timezone.utc)
    store.add_event(
        CanonicalEvent(
            event_id="evt-sqlite",
            sector=Sector.GEOPOLITICS,
            headline="Headline",
            body="Body",
            first_seen_at=now,
            updated_at=now,
            entities={"NATO"},
            witnesses=[],
        )
    )

    save_sqlite_snapshot(str(db_path), store)
    loaded = load_sqlite_snapshot(str(db_path))

    assert loaded is not None
    assert loaded.get_event("evt-sqlite") is not None


def test_persistence_facade_uses_sqlite_backend(tmp_path) -> None:
    original_backend = settings.state_backend
    original_sqlite_path = settings.state_sqlite_path
    settings.state_backend = "sqlite"
    settings.state_sqlite_path = str(tmp_path / "facade.sqlite")
    try:
        store = StateStore(x_monthly_budget=40, x_correction_budget=10)
        save_state(store)
        loaded = load_state()
        assert loaded is not None
    finally:
        settings.state_backend = original_backend
        settings.state_sqlite_path = original_sqlite_path


def test_sqlite_backend_falls_back_to_json_and_migrates(tmp_path) -> None:
    original_backend = settings.state_backend
    original_sqlite_path = settings.state_sqlite_path
    original_json_path = settings.state_snapshot_path

    json_path = tmp_path / "legacy.json"
    sqlite_path = tmp_path / "migrated.sqlite"

    store = StateStore(x_monthly_budget=40, x_correction_budget=10)
    now = datetime.now(timezone.utc)
    store.add_event(
        CanonicalEvent(
            event_id="evt-legacy",
            sector=Sector.CRYPTO,
            headline="Legacy",
            body="Legacy body",
            first_seen_at=now,
            updated_at=now,
            entities={"BTC"},
            witnesses=[],
        )
    )
    save_snapshot(str(json_path), store)

    settings.state_backend = "sqlite"
    settings.state_snapshot_path = str(json_path)
    settings.state_sqlite_path = str(sqlite_path)
    try:
        loaded = load_state()
        assert loaded is not None
        assert loaded.get_event("evt-legacy") is not None

        migrated = load_sqlite_snapshot(str(sqlite_path))
        assert migrated is not None
        assert migrated.get_event("evt-legacy") is not None
    finally:
        settings.state_backend = original_backend
        settings.state_sqlite_path = original_sqlite_path
        settings.state_snapshot_path = original_json_path
