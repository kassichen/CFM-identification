"""Task 1 small-network walkthrough: Phase A (new assignment) and Phase B (new exposure).

Run:
    python examples/task1_walkthrough.py
"""
from fractions import Fraction
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pfn_pipeline._internal.identification.schemas import (
    NetworkExposureSpec, CompleteRandomizationDesignV1, HeterogeneousBernoulliDesignV1)
from pfn_pipeline._internal.identification.randomized_arm_family.assignment import AssignmentSpec
from pfn_pipeline._internal.identification.randomized_arm_family.exposure import ExposureSpec
from pfn_pipeline._internal.identification.randomized_arm_family.task1_assignment import (
    UnequalProbabilityFixedQuotaDesign, RerandomizedBalancedDesign)
from pfn_pipeline._internal.identification.randomized_arm_family.task1_exposure import (
    WeightedExposureSpec, GroupedExposureSpec)
from pfn_pipeline._internal.identification.randomized_arm_family.support import SupportEngine
from pfn_pipeline._internal.identification.randomized_arm_family.task1_verifier import verify_joint_support


NODES = ("a", "b", "c", "d")
EDGES = (("a", "b"), ("a", "c"), ("b", "d"), ("c", "d"))
NET = NetworkExposureSpec(network_id="fixture", node_ids=list(NODES), undirected_edges=list(EDGES))


def check(design, exposure, node_id="a"):
    assignment = design if isinstance(design, AssignmentSpec) else AssignmentSpec(design)
    joint = SupportEngine.joint_support(network=NET, assignment=assignment, exposure=exposure, node_id=node_id)
    report = verify_joint_support(network=NET, design=assignment, exposure=exposure,
                                  node_id=node_id, proposed=joint)
    print(f"  P(T_{node_id}=a, S_{node_id}=s) = {joint}")
    print(f"  independent check: {'PASS' if report['ok'] else 'FAIL ' + str(report['mismatch'])}")
    return report


def main():
    base = UnequalProbabilityFixedQuotaDesign(
        nodes=NODES, m=2,
        assignment_probabilities={
            frozenset(("a", "b")): Fraction(1, 2),
            frozenset(("a", "c")): Fraction(1, 4),
            frozenset(("c", "d")): Fraction(1, 4),
        })

    print("== Phase A1: unequal fixed quota + E1 ==")
    check(base, ExposureSpec("strict_majority_ties_low"))
    print("== Phase A2: unequal fixed quota + E4 ==")
    check(base, ExposureSpec("exact_treated_neighbor_count"))

    balanced = RerandomizedBalancedDesign(base, lambda t: "a" in t)
    print("== Phase A3: rerandomized + E1 ==")
    check(balanced, ExposureSpec("strict_majority_ties_low"))
    print("== Phase A4: rerandomized + E4 ==")
    check(balanced, ExposureSpec("exact_treated_neighbor_count"))

    d2 = AssignmentSpec(CompleteRandomizationDesignV1(m=2))
    d1 = AssignmentSpec(HeterogeneousBernoulliDesignV1(propensities={n: "1/2" for n in NODES}))

    print("== Phase B1: existing D2 + weighted exposure (sum) ==")
    check(d2, WeightedExposureSpec(weights={"b": 1, "c": 2}, mode="sum"))
    print("== Phase B2: existing D1 + weighted exposure (proportion) ==")
    check(d1, WeightedExposureSpec(weights={"b": 1, "c": 2}, mode="proportion"))
    print("== Phase B3: existing D2 + grouped exposure ==")
    check(d2, GroupedExposureSpec(groups={"friend": ("b",), "colleague": ("c",)}))
    print("== Phase B4: existing D1 + grouped exposure ==")
    check(d1, GroupedExposureSpec(groups={"friend": ("b",), "colleague": ("c",)}))


if __name__ == "__main__":
    main()
