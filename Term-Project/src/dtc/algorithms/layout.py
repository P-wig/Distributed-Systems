"""Overlay structures on the complete graph: heap-ordered binary tree layers and the ring.

Processors are numbered 0..n-1. In the tree, processor `i` has children `2i+1` and `2i+2`,
so layer `l` holds ids `2^l - 1 .. 2^(l+1) - 2` (layer 0 is the root, id 0). The paper
assumes n = 2^L - 1 (LayeredRand) or n = 2^L (CoinRand); here the last layer may be
partially filled so any n works, and for those n the layout is exactly the paper's.
"""


def heap_parent(i: int) -> int:
    return (i - 1) // 2


def heap_children(i: int, n: int) -> list[int]:
    return [c for c in (2 * i + 1, 2 * i + 2) if c < n]


def heap_layer(i: int) -> int:
    return (i + 1).bit_length() - 1


def layer_start(layer: int) -> int:
    """Id of the first processor in `layer`."""
    return (1 << layer) - 1


def layer_size(layer: int) -> int:
    """Number of processors in a full layer."""
    return 1 << layer


def num_layers(n: int) -> int:
    """Layers of the LayeredRand tree over all n processors (log2(n+1) when n = 2^L - 1)."""
    return n.bit_length()


def coin_internal_layers(n: int) -> int:
    """CoinRand's L: internal layers 0..L-1 use 2^L - 1 <= n - 1 processors; all n are leaves."""
    return n.bit_length() - 1


def ring_right(i: int, n: int) -> int:
    return (i + 1) % n
