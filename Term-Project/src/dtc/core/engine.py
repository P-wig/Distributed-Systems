"""Discrete-event engine that feeds triggers from an adversary to an algorithm."""

from dataclasses import dataclass
from typing import Protocol

from dtc.core.network import Network


class TriggerSource(Protocol):
    def next_node(self) -> int: ...


class AlertSource(Protocol):
    alert_fired: bool


@dataclass(frozen=True)
class SimulationResult:
    alert_fired: bool
    triggers_delivered: int


def run_simulation(
    algorithm: AlertSource, network: Network, adversary: TriggerSource, w: int
) -> SimulationResult:
    """Deliver up to `w` triggers, fully processing each before the next.

    Stops at the first alert. An exact algorithm must alert on trigger number `w`
    exactly; an alert that never fires within `w` triggers is a failure.
    """
    processors = network.processors
    for count in range(1, w + 1):
        processors[adversary.next_node()].on_trigger()
        network.deliver_all()
        if algorithm.alert_fired:
            return SimulationResult(True, count)
    return SimulationResult(False, w)
