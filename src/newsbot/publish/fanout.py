from __future__ import annotations

from datetime import datetime, timezone

from newsbot.config import settings
from newsbot.publish.base import NoopPublisher, Publisher
from newsbot.publish.x_policy import can_publish_x, can_publish_x_correction
from newsbot.state.store import PublicationRecord, StateStore


class Fanout:
    def __init__(self, store: StateStore, publishers: list[Publisher] | None = None) -> None:
        self.store = store
        self.publishers = publishers or [
            NoopPublisher("telegram"),
            NoopPublisher("bluesky"),
            NoopPublisher("mastodon"),
            NoopPublisher("site"),
        ]
        self.x_publisher = NoopPublisher("x")

    async def publish(self, event_id: str, text: str) -> dict[str, str]:
        out: dict[str, str] = {}
        now = datetime.now(timezone.utc)
        for publisher in self.publishers:
            receipt = await publisher.publish(text)
            out[publisher.name] = receipt
            self.store.add_publication(PublicationRecord(event_id, publisher.name, now, text))

        can_x, reason = can_publish_x(self.store)
        if can_x:
            receipt = await self.x_publisher.publish(text)
            out["x"] = receipt
            self.store.x_used += 1
            self.store.x_last_post_at = now
            self.store.add_publication(PublicationRecord(event_id, "x", now, text))
        else:
            out["x"] = f"skipped:{reason}"

        return out

    async def publish_correction(self, event_id: str, text: str) -> dict[str, str]:
        out: dict[str, str] = {}
        now = datetime.now(timezone.utc)
        correction_text = f"CORRECTION: {text}"
        for publisher in self.publishers:
            receipt = await publisher.publish(correction_text)
            out[publisher.name] = receipt
            self.store.add_publication(
                PublicationRecord(event_id, publisher.name, now, correction_text)
            )

        can_x, reason = can_publish_x_correction(self.store)
        if can_x and settings.x_enabled:
            receipt = await self.x_publisher.publish(correction_text)
            out["x"] = receipt
            self.store.x_correction_used += 1
            self.store.add_publication(PublicationRecord(event_id, "x", now, correction_text))
        else:
            out["x"] = f"skipped:{reason}"

        return out
