from __future__ import annotations

from abc import ABC, abstractmethod


class Publisher(ABC):
    name: str

    @abstractmethod
    async def publish(self, text: str) -> str:
        raise NotImplementedError


class NoopPublisher(Publisher):
    def __init__(self, name: str) -> None:
        self.name = name

    async def publish(self, text: str) -> str:
        return f"{self.name}:ok"
