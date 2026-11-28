"""Metric counting tests."""

from dtc.core.metrics import Metrics
from dtc.core.network import Network


def test_metrics_derived_values():
    m = Metrics(3)
    m.record_message(0, 1, "a")
    m.record_message(0, 2, "a")
    m.record_message(2, 1, "b")
    assert m.total_msgs == 3
    assert m.max_rcv_load == 2  # processor 1
    assert m.max_msg_load == 2  # processor 0 sent 2; processor 1 received 2
    assert m.by_kind == {"a": 2, "b": 1}


def test_network_counts_every_send_and_ignores_self_sends():
    net = Network(3)
    net.send(0, 1, "x")
    net.send(1, 1, "self")
    assert net.metrics.total_msgs == 1
    assert net.metrics.sent == [1, 0, 0]
    assert net.metrics.received == [0, 1, 0]
