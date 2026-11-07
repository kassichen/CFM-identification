"""Independent small-network verifier for Task 1 support tables.

Uses its own direct enumeration loop; does not call SupportEngine.
"""
from __future__ import annotations

from fractions import Fraction
from itertools import product
from collections.abc import Mapping

from .task1_exposure import GroupedExposureSpec, WeightedExposureSpec
from .exposure import ExposureSpec


def _network_parts(network):
    nodes = tuple(network.node_ids)
    edges = list(network.undirected_edges)
    if not nodes or len(set(nodes)) != len(nodes):
        raise ValueError("network node_ids must be nonempty and unique")
    return nodes, edges


def _neighbors(nodes, edges):
    out = {n: set() for n in nodes}
    index = set(nodes)
    for edge in edges:
        left, right = edge
        if left not in index or right not in index:
            raise ValueError("edge endpoint is absent from node_ids")
        out[left].add(right)
        out[right].add(left)
    return {n: frozenset(v) for n, v in out.items()}


class _Net:
    def __init__(self, nodes, edges):
        self.node_ids = list(nodes)
        self.undirected_edges = list(edges)


def verify_joint_support(*, network, design, exposure, node_id, proposed):
    nodes, edges = _network_parts(network)
    if len(nodes) > 8:
        raise ValueError("independent verification is limited to N<=8")
    if node_id not in nodes:
        raise ValueError(f"unknown node {node_id!r}")
    nbrs = _neighbors(nodes, edges)[node_id]
    netobj = _Net(nodes, edges)
    oracle = {}
    total = Fraction(0)
    for bits in product((0, 1), repeat=len(nodes)):
        treatment = dict(zip(nodes, bits))
        if hasattr(design, "assignment_probability") and not isinstance(design, Mapping):
            p = design.assignment_probability(treatment)
        elif isinstance(design, Mapping):
            treated = frozenset(n for n, t in treatment.items() if t)
            p = design.get(treated, Fraction(0))
        elif hasattr(design, "full_assignment_probability"):
            p = design.full_assignment_probability(network, treatment)
        else:
            raise TypeError("design must expose complete assignment probabilities")
        p = p if isinstance(p, Fraction) else Fraction(str(p))
        total += p
        if isinstance(exposure, (WeightedExposureSpec, GroupedExposureSpec)):
            state = exposure.statistic(treatment, node_id, nbrs)
        elif isinstance(exposure, ExposureSpec):
            reference = exposure.reference_nodes(netobj, node_id)
            refs = set(reference) if reference is not None else set(nbrs)
            state = exposure.classify(sum(treatment[j] for j in refs), len(refs))
        else:
            raise TypeError("unsupported exposure specification")
        key = (treatment[node_id], state)
        oracle[key] = oracle.get(key, Fraction(0)) + p
    keys = set(proposed) | set(oracle)
    mismatch = {k: (proposed.get(k, Fraction(0)), oracle.get(k, Fraction(0)))
                for k in keys
                if proposed.get(k, Fraction(0)) != oracle.get(k, Fraction(0))}
    return {"ok": total == 1 and not mismatch,
            "normalization": total,
            "oracle": oracle,
            "proposed": dict(proposed),
            "mismatch": mismatch}
