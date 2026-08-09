"""Approval Agent - Simulates human approval of recommendations (mock, no real workflow)"""

from typing import List, Dict
from dataclasses import dataclass, asdict

@dataclass
class ApprovalDecision:
    resource_id: str
    resource_name: str
    recommended_action: str
    estimated_monthly_savings: float
    status: str  # "pending", "approved", "rejected"

class ApprovalAgent:
    """Agent responsible for mock approval of recommendations before a final action plan is produced"""

    def __init__(self):
        self._decisions: Dict[str, ApprovalDecision] = {}

    def queue_for_approval(self, recommendations: List) -> List[ApprovalDecision]:
        """Register recommendations as pending approval"""
        self._decisions = {}
        for rec in recommendations:
            r = rec.__dict__ if hasattr(rec, "__dict__") else rec
            decision = ApprovalDecision(
                resource_id=r["resource_id"],
                resource_name=r["resource_name"],
                recommended_action=r["recommended_action"],
                estimated_monthly_savings=r["estimated_monthly_savings"],
                status="pending",
            )
            self._decisions[decision.resource_id] = decision
        return list(self._decisions.values())

    def decide(self, resource_id: str, approved: bool) -> ApprovalDecision:
        """Record a human approve/reject decision for one resource"""
        decision = self._decisions.get(resource_id)
        if decision is None:
            raise KeyError(f"No pending recommendation for resource_id={resource_id}")
        decision.status = "approved" if approved else "rejected"
        return decision

    def get_all_decisions(self) -> List[ApprovalDecision]:
        return list(self._decisions.values())

    def get_action_plan(self) -> List[Dict]:
        """Final action plan = only the approved recommendations"""
        return [asdict(d) for d in self._decisions.values() if d.status == "approved"]
