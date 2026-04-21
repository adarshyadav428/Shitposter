import pytest

from newsbot.publish.base import NoopPublisher, Publisher
from newsbot.publish.fanout import Fanout
from newsbot.state.store import StateStore


class FailingPublisher(Publisher):
    name = "failing"

    async def publish(self, text: str) -> str:
        raise RuntimeError("fail")


@pytest.mark.asyncio
async def test_fanout_isolates_channel_failures() -> None:
    store = StateStore(x_monthly_budget=40, x_correction_budget=10)
    fanout = Fanout(store=store, publishers=[FailingPublisher(), NoopPublisher("site")])

    result = await fanout.publish("event-1", "hello")

    assert result["failing"].startswith("error:")
    assert result["site"].startswith("site:")
    channels = [row.channel for row in store.list_publications()]
    assert "site" in channels
    failures = store.list_failed_publications()
    assert len(failures) >= 1
    assert failures[-1].channel == "failing"
