from datetime import datetime, timedelta, timezone

from newsbot.domain import CanonicalEvent, Sector
from newsbot.state.store import FailedPublicationRecord, PublicationRecord, StateStore


def test_store_prune_limits_collections_and_sets() -> None:
    store = StateStore(x_monthly_budget=40, x_correction_budget=10)
    now = datetime.now(timezone.utc)

    for i in range(6):
        event_id = f"evt-{i}"
        store.add_event(
            CanonicalEvent(
                event_id=event_id,
                sector=Sector.MACRO,
                headline=f"h-{i}",
                body=f"b-{i}",
                first_seen_at=now - timedelta(minutes=10 - i),
                updated_at=now - timedelta(minutes=10 - i),
                entities={"FED"},
                witnesses=[],
            )
        )
        store.mark_published(event_id)
        if i % 2 == 0:
            store.mark_retracted(event_id)

    for i in range(8):
        store.add_publication(PublicationRecord("evt-5", "site", now, f"pub-{i}"))
        store.add_failed_publication(
            FailedPublicationRecord("evt-5", "x", now, f"fail-{i}", "boom")
        )

    result = store.prune(max_events=3, max_publications=4, max_failed_publications=2)

    assert result["removed_events"] == 3
    assert result["removed_publications"] == 4
    assert result["removed_failed_publications"] == 6
    assert len(store.events) == 3
    assert len(store.publications) == 4
    assert len(store.failed_publications) == 2
    assert store.published_event_ids.issubset(store.events.keys())
    assert store.retracted_event_ids.issubset(store.events.keys())
