from __future__ import annotations

from xml.sax.saxutils import escape

from newsbot.state.store import StateStore


def render_events_json(store: StateStore, limit: int = 100) -> list[dict]:
    out = []
    for event in store.list_events()[:limit]:
        out.append(
            {
                "event_id": event.event_id,
                "sector": event.sector.value,
                "headline": event.headline,
                "body": event.body,
                "updated_at": event.updated_at.isoformat(),
                "witness_count": len(event.witnesses),
            }
        )
    return out


def render_rss_xml(store: StateStore, site_url: str, limit: int = 50) -> str:
    channel_title = "Autonomous News Broadcaster"
    items: list[str] = []
    for event in store.list_events()[:limit]:
        title = escape(event.headline)
        description = escape(event.body or event.headline)
        guid = escape(event.event_id)
        link = f"{site_url.rstrip('/')}/events/{escape(event.event_id)}"
        pub_date = event.updated_at.strftime("%a, %d %b %Y %H:%M:%S GMT")
        items.append(
            """
            <item>
              <title>{title}</title>
              <description>{description}</description>
              <guid>{guid}</guid>
              <link>{link}</link>
              <pubDate>{pub_date}</pubDate>
            </item>
            """.format(
                title=title,
                description=description,
                guid=guid,
                link=link,
                pub_date=pub_date,
            ).strip()
        )

    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<rss version=\"2.0\"><channel>"
        f"<title>{escape(channel_title)}</title>"
        f"<link>{escape(site_url)}</link>"
        "<description>Verified autonomous breaking news feed</description>"
        + "".join(items)
        + "</channel></rss>"
    )
