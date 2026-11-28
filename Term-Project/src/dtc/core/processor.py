"""Base Processor: on_trigger() and on_message() hooks that algorithms subclass."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dtc.core.network import Message, Network


class Processor(ABC):
    def __init__(self, pid: int, network: Network) -> None:
        self.pid = pid
        self.network = network

    @abstractmethod
    def on_trigger(self) -> None:
        """Called when the adversary delivers an external trigger to this processor."""

    @abstractmethod
    def on_message(self, msg: Message) -> None:
        """Called when a message from another processor is delivered."""

    def send(self, dst: int, kind: str, round: int = 0, data: Any = None) -> None:
        self.network.send(self.pid, dst, kind, round, data)
