"""Read-only adapters for the two frozen reference repositories."""

from rep_audit.data.adapters.air import AIRRepositoryAdapter
from rep_audit.data.adapters.feasibility import FeasibilityRepositoryAdapter

__all__ = ("AIRRepositoryAdapter", "FeasibilityRepositoryAdapter")
