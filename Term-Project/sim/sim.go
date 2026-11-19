// Package sim defines the shared simulation interfaces used by every DTC
// algorithm: processors, messages, the network and the metrics counters.
package sim

// Message is anything sent between processors. Each algorithm defines its own
// concrete message types (coin, RoundReset, Reduce, Inform, ...).
type Message interface {
	Kind() string
}

// Network delivers messages and records every send and receive.
type Network interface {
	Send(from, to int, m Message)
	Alert()
}

// Processor is one node of the distributed system.
type Processor interface {
	// OnTrigger is called when the external source delivers a trigger.
	OnTrigger(net Network)
	// OnMessage is called when a message from another processor arrives.
	OnMessage(from int, m Message, net Network)
}

// Metrics holds the per-processor counters behind the three comparison metrics.
type Metrics struct {
	Sent []int64
	Recv []int64
}

func NewMetrics(n int) *Metrics {
	return &Metrics{Sent: make([]int64, n), Recv: make([]int64, n)}
}

func (m *Metrics) Total() int64 {
	var t int64
	for _, s := range m.Sent {
		t += s
	}
	return t
}

func (m *Metrics) MaxRcvLoad() int64 {
	var mx int64
	for _, r := range m.Recv {
		if r > mx {
			mx = r
		}
	}
	return mx
}

func (m *Metrics) MaxMsgLoad() int64 {
	var mx int64
	for i := range m.Sent {
		if l := m.Sent[i] + m.Recv[i]; l > mx {
			mx = l
		}
	}
	return mx
}
