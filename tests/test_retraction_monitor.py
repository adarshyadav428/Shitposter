import pytest

from newsbot.main import build_default_orchestrator
from newsbot.retraction_monitor import RetractionMonitor


@pytest.mark.asyncio
async def test_monitor_triggers_retraction_on_changed_keyword_content() -> None:
    orchestrator = build_default_orchestrator()
    await orchestrator.run_once()
    event = orchestrator.store.list_events()[0]

    calls = {"n": 0}

    async def fake_fetcher(_url: str) -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            return "original content from source"
        return "updated article with correction and clarification"

    monitor = RetractionMonitor(
        orchestrator=orchestrator,
        interval_seconds=300,
        fetcher=fake_fetcher,
    )
    first = await monitor.scan_once()
    second = await monitor.scan_once()

    assert first == 0
    assert second >= 1
    assert orchestrator.store.is_retracted(event.event_id) is True
