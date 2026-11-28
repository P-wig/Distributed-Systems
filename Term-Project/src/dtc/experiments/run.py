"""Run an experiment config over all seeds (in parallel) and write CSV to data/results/."""

from dataclasses import asdict, dataclass

from dtc.adversary import make_adversary
from dtc.algorithms.registry import get_algorithm
from dtc.core.engine import run_simulation
from dtc.core.metrics import Metrics
from dtc.core.network import Network
from dtc.core.rng import make_rng
from dtc.experiments.config import TrialSpec


@dataclass(frozen=True)
class TrialResult:
    """One CSV row; columns match docs/DATA_FORMATS.md."""

    algorithm: str
    variant: str
    n: int
    w: int
    adversary: str
    seed: int
    alert_fired: bool
    triggers_at_alert: int
    rounds: int
    total_msgs: int
    max_rcv_load: int
    max_msg_load: int

    def as_row(self) -> dict:
        return asdict(self)


def run_trial(spec: TrialSpec) -> TrialResult:
    """Build the network, algorithm and adversary for `spec`, run it, and collect metrics."""
    if spec.variant:
        raise NotImplementedError("derandomized variants are not implemented yet")
    metrics = Metrics(spec.n)
    network = Network(spec.n, metrics)
    algorithm = get_algorithm(spec.algorithm)(spec.n, spec.w, make_rng(spec.seed, "algorithm"))
    algorithm.setup(network)
    adversary = make_adversary(spec.adversary, spec.n, spec.w, make_rng(spec.seed, "adversary"))
    result = run_simulation(algorithm, network, adversary, spec.w)
    return TrialResult(
        algorithm=spec.algorithm,
        variant=spec.variant,
        n=spec.n,
        w=spec.w,
        adversary=spec.adversary,
        seed=spec.seed,
        alert_fired=result.alert_fired,
        triggers_at_alert=result.triggers_delivered,
        rounds=metrics.rounds,
        total_msgs=metrics.total_msgs,
        max_rcv_load=metrics.max_rcv_load,
        max_msg_load=metrics.max_msg_load,
    )


def main() -> None:
    raise NotImplementedError("experiment runner is not implemented yet")


if __name__ == "__main__":
    main()
