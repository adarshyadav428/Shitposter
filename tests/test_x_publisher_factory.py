from newsbot.config import settings
from newsbot.publish.base import NoopPublisher
from newsbot.publish.channels import XPublisher, build_x_publisher


def test_x_factory_returns_noop_without_credentials() -> None:
    original = (
        settings.x_enabled,
        settings.x_api_key,
        settings.x_api_secret,
        settings.x_access_token,
        settings.x_access_token_secret,
    )
    settings.x_enabled = True
    settings.x_api_key = None
    settings.x_api_secret = None
    settings.x_access_token = None
    settings.x_access_token_secret = None
    try:
        publisher = build_x_publisher()
        assert isinstance(publisher, NoopPublisher)
    finally:
        (
            settings.x_enabled,
            settings.x_api_key,
            settings.x_api_secret,
            settings.x_access_token,
            settings.x_access_token_secret,
        ) = original


def test_x_factory_returns_real_publisher_with_credentials() -> None:
    original = (
        settings.x_enabled,
        settings.x_api_key,
        settings.x_api_secret,
        settings.x_access_token,
        settings.x_access_token_secret,
    )
    settings.x_enabled = True
    settings.x_api_key = "k"
    settings.x_api_secret = "s"
    settings.x_access_token = "t"
    settings.x_access_token_secret = "ts"
    try:
        publisher = build_x_publisher()
        assert isinstance(publisher, XPublisher)
    finally:
        (
            settings.x_enabled,
            settings.x_api_key,
            settings.x_api_secret,
            settings.x_access_token,
            settings.x_access_token_secret,
        ) = original
