"""Internal, non-serialized components of the randomized-network POINT family.

The *public* wire contracts remain TaskSpec / IdentificationSpec and
RandomizedNetworkArmMeanContractV1. This package does not change them or issue
causal certificates by itself; the theorem backend and independent verifier
remain authoritative.
"""
from .assignment import AssignmentSpec, NeighborCountLaw
from .exposure import ExposureSpec
from .support import ArmSupportEvidence, SupportEngine
from .task1_assignment import (
    CovariateBalanceRule, RerandomizedBalancedDesign, UnequalProbabilityFixedQuotaDesign,
)
from .task1_exposure import GroupedExposureSpec, WeightedExposureSpec
from .task1_targets import (
    TargetResult, local_direct_mean, peer_spillover_mean, policy_mean, policy_contrast,
)

__all__ = [
    "AssignmentSpec", "NeighborCountLaw", "ExposureSpec", "ArmSupportEvidence", "SupportEngine",
    "UnequalProbabilityFixedQuotaDesign", "RerandomizedBalancedDesign", "CovariateBalanceRule",
    "WeightedExposureSpec", "GroupedExposureSpec",
    "TargetResult", "local_direct_mean", "peer_spillover_mean", "policy_mean", "policy_contrast",
]
