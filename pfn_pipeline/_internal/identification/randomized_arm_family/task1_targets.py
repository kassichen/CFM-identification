"""Task 1 target adapters: four POINT identification target families.

They consume the unified exact support table from :class:`SupportEngine` and do
not infer causal assumptions or outcomes: callers supply the potential-response
table and explicitly confirm the required assumptions.  A requested cell without
positive support therefore returns ``UNSUPPORTED`` rather than a point value.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from collections.abc import Mapping, Callable
from typing import Any, Literal

from .assignment import AssignmentSpec
from .exposure import ExposureSpec
from .support import SupportEngine
from .task1_assignment import MAX_EXACT_ENUMERATION_N
from .task1_exposure import GroupedExposureSpec, WeightedExposureSpec

Status = Literal["POINT", "UNSUPPORTED"]


@dataclass(frozen=True)
class TargetResult:
    target: str
    status: Status
    value: Fraction | None
    reason: str
    support: tuple[Any, ...] = ()
    population: tuple[str, ...] = ()
    unit_weights: tuple[tuple[str, Fraction], ...] = ()
    estimand: str = ""


_REQUIRED_ASSUMPTIONS = {
    "local_direct_mean": ("consistency", "random_assignment", "exposure_sufficiency"),
    "peer_spillover_mean": ("consistency", "random_assignment", "exposure_sufficiency"),
    "policy_mean": ("consistency", "random_assignment"),
    "policy_contrast": ("consistency", "random_assignment"),
}


def _as_assignment(design):
    return design if isinstance(design, AssignmentSpec) else AssignmentSpec(design)


def _network_nodes(network):
    return tuple(network.node_ids)


def _gate(target: str, assumptions: Mapping[str, bool] | None) -> TargetResult | None:
    if assumptions is None:
        return TargetResult(target, "UNSUPPORTED", None,
                            "causal assumptions were not explicitly confirmed")
    required = _REQUIRED_ASSUMPTIONS.get(target, ())
    missing = tuple(name for name in required if assumptions.get(name) is not True)
    rejected = tuple(name for name, ok in assumptions.items() if ok is False)
    if missing:
        return TargetResult(target, "UNSUPPORTED", None,
                            "unconfirmed assumptions: " + ", ".join(missing))
    if rejected:
        return TargetResult(target, "UNSUPPORTED", None,
                            "rejected assumptions: " + ", ".join(rejected))
    return None


def _outcome(table: Mapping[Any, Any], key: Any) -> Fraction | None:
    if key not in table:
        return None
    value = table[key]
    return value if isinstance(value, Fraction) else Fraction(str(value))


def _population_and_weights(
        nodes: tuple[str, ...], population: Any = None,
        unit_weights: Mapping[str, Any] | None = None,
) -> tuple[tuple[str, ...], dict[str, Fraction]]:
    selected = tuple(nodes if population is None else population)
    if not selected or len(set(selected)) != len(selected):
        raise ValueError("population must be a non-empty sequence of unique node ids")
    unknown = set(selected).difference(nodes)
    if unknown:
        raise ValueError(f"population contains unknown nodes: {sorted(unknown)!r}")
    if unit_weights is None:
        weights = {node: Fraction(1, len(selected)) for node in selected}
    else:
        if set(unit_weights) != set(selected):
            raise ValueError("unit_weights must cover exactly the evaluation population")
        raw = {node: (value if isinstance(value, Fraction) else Fraction(str(value)))
               for node, value in unit_weights.items()}
        if any(value < 0 for value in raw.values()):
            raise ValueError("unit_weights must be non-negative")
        total = sum(raw.values(), Fraction(0))
        if total <= 0:
            raise ValueError("unit_weights must have positive total")
        weights = {node: value / total for node, value in raw.items()}
    return selected, weights


def _meta(target: str, population: tuple[str, ...], weights: Mapping[str, Fraction],
          estimand: str, *, support: tuple[Any, ...] = ()) -> dict[str, Any]:
    return {"population": population,
            "unit_weights": tuple((node, weights[node]) for node in population),
            "estimand": estimand,
            "support": support}


def _joint(network: Any, design: Any, exposure: Any, node: str):
    return SupportEngine.joint_support(network=network, assignment=_as_assignment(design),
                                       exposure=exposure, node_id=node)


def _assignment_rows(design: Any, network: Any) -> list[tuple[dict[str, int], Fraction]]:
    """All full assignments with positive probability, as (treatment, mass) pairs."""
    assignment = _as_assignment(design)
    nodes = _network_nodes(network)
    if len(nodes) > MAX_EXACT_ENUMERATION_N:
        raise ValueError(f"assignment enumeration is limited to N<={MAX_EXACT_ENUMERATION_N}")
    rows: list[tuple[dict[str, int], Fraction]] = []
    for bits in product((0, 1), repeat=len(nodes)):
        treatment = dict(zip(nodes, bits))
        probability = assignment.full_assignment_probability(network, treatment)
        if probability:
            rows.append((treatment, probability))
    return rows


def _positive_cells(node: str, joint: dict) -> tuple[tuple[str, int, Any, Fraction], ...]:
    return tuple((node, a, s, p) for (a, s), p in joint.items() if p)


def local_direct_mean(*, network: Any, design: Any,
                      exposure: WeightedExposureSpec | GroupedExposureSpec | ExposureSpec,
                      outcomes: Mapping[tuple[str, int, Any], Any],
                      exposure_state: Any,
                      assumptions: Mapping[str, bool] | None = None,
                      population: Any = None,
                      unit_weights: Mapping[str, Any] | None = None) -> TargetResult:
    """Weighted average of ``Y_i(1,s)-Y_i(0,s)`` at a fixed exposure state."""
    target = "local_direct_mean"
    blocked = _gate(target, assumptions)
    if blocked:
        return blocked
    nodes = _network_nodes(network)
    selected, weights = _population_and_weights(nodes, population, unit_weights)
    estimand = f"E_w[Y_i(1,{exposure_state!r})-Y_i(0,{exposure_state!r})]"
    joints: dict[str, dict] = {}
    support: list[tuple[str, int, Any, Fraction]] = []
    for node in selected:
        joint = _joint(network, design, exposure, node)
        joints[node] = joint
        present = {(a, s) for (a, s), p in joint.items() if p}
        if (0, exposure_state) not in present or (1, exposure_state) not in present:
            return TargetResult(target, "UNSUPPORTED", None,
                                f"zero support for node {node!r} at exposure {exposure_state!r}",
                                **_meta(target, selected, weights, estimand,
                                        support=tuple(support)))
        if _outcome(outcomes, (node, 1, exposure_state)) is None or \
           _outcome(outcomes, (node, 0, exposure_state)) is None:
            return TargetResult(target, "UNSUPPORTED", None,
                                f"missing potential response for node {node!r}",
                                **_meta(target, selected, weights, estimand,
                                        support=tuple(support)))
        support.extend(_positive_cells(node, joint))
    value = sum((weights[node] * (_outcome(outcomes, (node, 1, exposure_state))
                                  - _outcome(outcomes, (node, 0, exposure_state)))
                 for node in selected), Fraction(0))
    return TargetResult(target, "POINT", value,
                        "all requested own-treatment/exposure cells have positive support",
                        **_meta(target, selected, weights, estimand, support=tuple(support)))


def peer_spillover_mean(*, network: Any, design: Any,
                        exposure: WeightedExposureSpec | GroupedExposureSpec | ExposureSpec,
                        outcomes: Mapping[tuple[str, int, Any], Any],
                        own_treatment_value: int,
                        exposed_state: Any, reference_state: Any,
                        assumptions: Mapping[str, bool] | None = None,
                        population: Any = None,
                        unit_weights: Mapping[str, Any] | None = None) -> TargetResult:
    """Weighted average of ``Y_i(a,s_exposed)-Y_i(a,s_reference)`` at fixed own treatment."""
    target = "peer_spillover_mean"
    blocked = _gate(target, assumptions)
    if blocked:
        return blocked
    nodes = _network_nodes(network)
    selected, weights = _population_and_weights(nodes, population, unit_weights)
    estimand = (f"E_w[Y_i({own_treatment_value},{exposed_state!r})"
                f"-Y_i({own_treatment_value},{reference_state!r})]")
    support: list[tuple[str, int, Any, Fraction]] = []
    for node in selected:
        joint = _joint(network, design, exposure, node)
        present = {s for (a, s), p in joint.items() if a == own_treatment_value and p}
        if exposed_state not in present or reference_state not in present:
            return TargetResult(target, "UNSUPPORTED", None,
                                f"zero support for a peer exposure state at node {node!r}",
                                **_meta(target, selected, weights, estimand,
                                        support=tuple(support)))
        if _outcome(outcomes, (node, own_treatment_value, exposed_state)) is None or \
           _outcome(outcomes, (node, own_treatment_value, reference_state)) is None:
            return TargetResult(target, "UNSUPPORTED", None,
                                f"missing potential response for node {node!r}",
                                **_meta(target, selected, weights, estimand,
                                        support=tuple(support)))
        support.extend(_positive_cells(node, joint))
    value = sum((weights[node] * (_outcome(outcomes, (node, own_treatment_value, exposed_state))
                                  - _outcome(outcomes, (node, own_treatment_value, reference_state)))
                 for node in selected), Fraction(0))
    return TargetResult(target, "POINT", value,
                        "both peer exposure cells have positive support",
                        **_meta(target, selected, weights, estimand, support=tuple(support)))


def policy_mean(*, network: Any, design: Any,
                outcomes: Mapping[Any, Any] | Callable[[Any], Any],
                policy: Callable[[frozenset[str]], Any] | None = None,
                assumptions: Mapping[str, bool] | None = None,
                population: Any = None,
                unit_weights: Mapping[str, Any] | None = None) -> TargetResult:
    """Expectation of a full-assignment response under a known assignment law."""
    target = "policy_mean"
    blocked = _gate(target, assumptions)
    if blocked:
        return blocked
    nodes = _network_nodes(network)
    selected, weights = _population_and_weights(nodes, population, unit_weights)
    estimand = "E_policy[Y(policy assignment)]"
    total = Fraction(0)
    value = Fraction(0)
    support: list[Any] = []
    for treatment, probability in _assignment_rows(design, network):
        if probability == 0:
            continue
        treated = frozenset(n for n, t in treatment.items() if t)
        key = policy(treated) if policy else treated
        y = outcomes(key) if callable(outcomes) else outcomes.get(key)
        if y is None:
            return TargetResult(target, "UNSUPPORTED", None,
                                f"missing response for assignment {sorted(treated)!r}",
                                **_meta(target, selected, weights, estimand,
                                        support=tuple(support)))
        y = y if isinstance(y, Fraction) else Fraction(str(y))
        total += probability
        value += probability * y
        support.append((treated, probability, y))
    if total == 0:
        return TargetResult(target, "UNSUPPORTED", None,
                            "assignment law has zero positive support",
                            **_meta(target, selected, weights, estimand, support=tuple(support)))
    return TargetResult(target, "POINT", value / total,
                        "all positive-probability assignments have responses",
                        **_meta(target, selected, weights, estimand, support=tuple(support)))


def policy_contrast(*, network: Any, design_a: Any, design_b: Any,
                    outcomes: Mapping[Any, Any] | Callable[[Any], Any],
                    policy_a: Callable[[frozenset[str]], Any] | None = None,
                    policy_b: Callable[[frozenset[str]], Any] | None = None,
                    assumptions: Mapping[str, bool] | None = None,
                    population: Any = None,
                    unit_weights: Mapping[str, Any] | None = None) -> TargetResult:
    """Difference between two policy means, each with its own support check."""
    target = "policy_contrast"
    blocked = _gate(target, assumptions)
    if blocked:
        return blocked
    left = policy_mean(network=network, design=design_a, outcomes=outcomes,
                       policy=policy_a, assumptions=assumptions,
                       population=population, unit_weights=unit_weights)
    right = policy_mean(network=network, design=design_b, outcomes=outcomes,
                        policy=policy_b, assumptions=assumptions,
                        population=population, unit_weights=unit_weights)
    if left.status != "POINT" or right.status != "POINT":
        return TargetResult(target, "UNSUPPORTED", None,
                            f"policy support failure: {left.reason}; {right.reason}",
                            population=left.population, unit_weights=left.unit_weights,
                            estimand="E_policyA[Y]-E_policyB[Y]")
    return TargetResult(target, "POINT", left.value - right.value,
                        "both policy means are supported",
                        population=left.population, unit_weights=left.unit_weights,
                        estimand="E_policyA[Y]-E_policyB[Y]")


__all__ = ["TargetResult", "local_direct_mean", "peer_spillover_mean", "policy_mean", "policy_contrast"]
