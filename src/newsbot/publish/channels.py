from __future__ import annotations

from typing import Any

import httpx

from newsbot.config import settings
from newsbot.publish.base import NoopPublisher, Publisher


class TelegramPublisher(Publisher):
    name = "telegram"

    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id

    async def publish(self, text: str) -> str:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload)
        response.raise_for_status()
        body = response.json()
        if not body.get("ok"):
            raise RuntimeError("telegram_publish_failed")
        message_id = body.get("result", {}).get("message_id", "unknown")
        return f"telegram:{message_id}"


class MastodonPublisher(Publisher):
    name = "mastodon"

    def __init__(self, base_url: str, access_token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token

    async def publish(self, text: str) -> str:
        url = f"{self.base_url}/api/v1/statuses"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {"status": text}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, data=payload)
        response.raise_for_status()
        body = response.json()
        return f"mastodon:{body.get('id', 'unknown')}"


class BlueskyPublisher(Publisher):
    name = "bluesky"

    def __init__(
        self,
        identifier: str,
        app_password: str,
        service_url: str = "https://bsky.social",
    ) -> None:
        self.identifier = identifier
        self.app_password = app_password
        self.service_url = service_url.rstrip("/")

    async def publish(self, text: str) -> str:
        async with httpx.AsyncClient(timeout=20.0) as client:
            session = await self._create_session(client)
            access_jwt = session["accessJwt"]
            did = session["did"]
            payload = {
                "repo": did,
                "collection": "app.bsky.feed.post",
                "record": {
                    "$type": "app.bsky.feed.post",
                    "text": text,
                    "createdAt": self._timestamp(),
                },
            }
            response = await client.post(
                f"{self.service_url}/xrpc/com.atproto.repo.createRecord",
                headers={"Authorization": f"Bearer {access_jwt}"},
                json=payload,
            )
        response.raise_for_status()
        body = response.json()
        uri = body.get("uri", "unknown")
        return f"bluesky:{uri}"

    async def _create_session(self, client: httpx.AsyncClient) -> dict[str, Any]:
        response = await client.post(
            f"{self.service_url}/xrpc/com.atproto.server.createSession",
            json={"identifier": self.identifier, "password": self.app_password},
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _timestamp() -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_publishers() -> list[Publisher]:
    publishers: list[Publisher] = []

    if settings.telegram_enabled and settings.telegram_bot_token and settings.telegram_chat_id:
        publishers.append(TelegramPublisher(settings.telegram_bot_token, settings.telegram_chat_id))
    else:
        publishers.append(NoopPublisher("telegram"))

    if settings.bluesky_enabled and settings.bluesky_identifier and settings.bluesky_app_password:
        publishers.append(
            BlueskyPublisher(settings.bluesky_identifier, settings.bluesky_app_password)
        )
    else:
        publishers.append(NoopPublisher("bluesky"))

    if settings.mastodon_enabled and settings.mastodon_base_url and settings.mastodon_access_token:
        publishers.append(
            MastodonPublisher(settings.mastodon_base_url, settings.mastodon_access_token)
        )
    else:
        publishers.append(NoopPublisher("mastodon"))

    publishers.append(NoopPublisher("site"))
    return publishers
