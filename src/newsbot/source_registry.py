from __future__ import annotations

from newsbot.config import settings
from newsbot.domain import Sector, SourceTier
from newsbot.ingest.base import Ingestor, SourceSpec
from newsbot.ingest.mock import MockIngestor
from newsbot.ingest.rss import RSSIngestor


def _rss_fleet() -> list[Ingestor]:
    return [
        RSSIngestor(
            spec=SourceSpec("reuters-world", "reuters", SourceTier.T2, Sector.GEOPOLITICS.value),
            feed_url="https://feeds.reuters.com/reuters/worldNews",
            sector=Sector.GEOPOLITICS,
        ),
        RSSIngestor(
            spec=SourceSpec("ap-news", "ap", SourceTier.T2, Sector.GEOPOLITICS.value),
            feed_url="https://rsshub.app/ap/news",
            sector=Sector.GEOPOLITICS,
        ),
        RSSIngestor(
            spec=SourceSpec("federal-reserve", "fed", SourceTier.T1, Sector.MACRO.value),
            feed_url="https://www.federalreserve.gov/feeds/press_all.xml",
            sector=Sector.MACRO,
        ),
        RSSIngestor(
            spec=SourceSpec("ecb", "ecb", SourceTier.T1, Sector.MACRO.value),
            feed_url="https://www.ecb.europa.eu/rss/press.html",
            sector=Sector.MACRO,
        ),
        RSSIngestor(
            spec=SourceSpec("coindesk", "coindesk", SourceTier.T2, Sector.CRYPTO.value),
            feed_url="https://www.coindesk.com/arc/outboundfeeds/rss/",
            sector=Sector.CRYPTO,
        ),
        RSSIngestor(
            spec=SourceSpec("theblock", "theblock", SourceTier.T2, Sector.CRYPTO.value),
            feed_url="https://www.theblock.co/rss.xml",
            sector=Sector.CRYPTO,
        ),
    ]


def _mock_fleet() -> list[Ingestor]:
    return [
        MockIngestor(
            source_id="sec-edgar",
            family="sec",
            tier=SourceTier.T1,
            sector=Sector.MACRO,
            items=[
                {
                    "headline": "Federal Reserve announces emergency liquidity operation",
                    "body": "The operation size is 50 billion and starts immediately.",
                    "entities": ["FED", "USD"],
                    "url": "https://example.com/fed",
                }
            ],
        ),
        MockIngestor(
            source_id="nitter-journalist-1",
            family="independent-journalist",
            tier=SourceTier.T2,
            sector=Sector.CRYPTO,
            items=[
                {
                    "headline": "Major exchange pauses withdrawals for BTC and ETH",
                    "body": "Exchange statement cites infrastructure incident.",
                    "entities": ["BTC", "ETH"],
                    "url": "https://example.com/exchange",
                }
            ],
        ),
    ]


def build_ingestor_fleet() -> list[Ingestor]:
    fleet: list[Ingestor] = []
    if settings.enable_real_rss:
        fleet.extend(_rss_fleet())
    if settings.use_mock_ingestors or not fleet:
        fleet.extend(_mock_fleet())
    return fleet
