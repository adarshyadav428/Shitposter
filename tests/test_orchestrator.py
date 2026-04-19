import pytest

from newsbot.main import build_default_orchestrator


@pytest.mark.asyncio
async def test_orchestrator_run_once_generates_publications() -> None:
    orchestrator = build_default_orchestrator()
    stats = await orchestrator.run_once()
    assert stats["raw"] > 0
    assert stats["accepted"] >= 1
    assert len(orchestrator.store.publications) >= 1
