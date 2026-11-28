"""Network wiring, delivery order and validation tests."""

import pytest

from dtc.core.network import Message, Network
from dtc.core.processor import Processor


class Recorder(Processor):
    def __init__(self, pid, network, log):
        super().__init__(pid, network)
        self.log = log

    def on_trigger(self):
        pass

    def on_message(self, msg: Message):
        self.log.append((self.pid, msg.src, msg.kind))
        if msg.kind == "ping":
            self.send(msg.src, "pong")


def make_network(n):
    log = []
    net = Network(n)
    net.attach([Recorder(i, net, log) for i in range(n)])
    return net, log


def test_complete_graph_any_pair_can_communicate():
    net, log = make_network(4)
    for src in range(4):
        for dst in range(4):
            if src != dst:
                net.send(src, dst, "hello")
    assert net.deliver_all() == 12
    assert len(log) == 12


def test_deliver_all_drains_messages_sent_during_delivery_in_fifo_order():
    net, log = make_network(3)
    net.send(0, 1, "ping")
    net.send(0, 2, "ping")
    assert net.deliver_all() == 4
    assert log == [(1, 0, "ping"), (2, 0, "ping"), (0, 1, "pong"), (0, 2, "pong")]
    assert net.metrics.total_msgs == 4


def test_invalid_endpoints_and_attach_are_rejected():
    net, _ = make_network(2)
    with pytest.raises(ValueError):
        net.send(0, 2, "x")
    with pytest.raises(ValueError):
        net.attach([Recorder(0, net, [])])
    with pytest.raises(ValueError):
        net.attach([Recorder(1, net, []), Recorder(0, net, [])])
