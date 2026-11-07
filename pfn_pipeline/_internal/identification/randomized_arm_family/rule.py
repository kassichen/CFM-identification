"""Publicly named Task 1 rule module.

The implementation lives in :mod:`task1_targets` to keep the legacy randomized
arm adapter untouched.  This module gives downstream code a stable, concise
import path for the four target families requested by the PDF.
"""
from .task1_targets import (
    TargetResult,
    local_direct_mean,
    peer_spillover_mean,
    policy_mean,
    policy_contrast,
)

__all__ = ["TargetResult", "local_direct_mean", "peer_spillover_mean",
           "policy_mean", "policy_contrast"]
