"""Savings Calculator - Estimates potential savings from optimizations"""

from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class SavingsEstimate:
    resource_id: str
    resource_name: str
    recommended_action: str
    estimated_monthly_savings: float
    confidence: str  # high, medium, low

class SavingsCalculator:
    """Calculate estimated savings from recommendations"""

    SAVINGS_RATES = {
        'shutdown': 0.80,        # 80% savings
        'downsize': 0.30,        # 30% savings
        'storage_optimization': 0.20,  # 20% savings
        'scale': -0.20,          # 20% cost increase (negative savings)
        'investigate': 0.0,      # No immediate savings
        'performance_investigation': 0.0,
        'ha_review': 0.0,
    }

    def __init__(self, records: List[Dict]):
        self.records = records
        self.resource_map = {r['resource_id']: r for r in records}

    def calculate_savings(self, recommendation: Dict) -> SavingsEstimate:
        """Calculate savings for a single recommendation"""
        resource_id = recommendation.get('resource_id', '')
        action = recommendation.get('recommended_action', '').lower()
        resource = self.resource_map.get(resource_id)

        if not resource:
            return SavingsEstimate(
                resource_id=resource_id,
                resource_name=recommendation.get('resource_name', 'Unknown'),
                recommended_action=action,
                estimated_monthly_savings=0,
                confidence="low"
            )

        monthly_cost = resource.get('monthly_cost', 0)
        savings_rate = self._get_savings_rate(action)
        estimated_savings = monthly_cost * savings_rate

        # Determine confidence based on action type
        if action in ['shutdown', 'downsize']:
            confidence = "high"
        elif action == 'storage_optimization':
            confidence = "medium"
        else:
            confidence = "low"

        return SavingsEstimate(
            resource_id=resource_id,
            resource_name=resource.get('resource_name', 'Unknown'),
            recommended_action=action,
            estimated_monthly_savings=round(estimated_savings, 2),
            confidence=confidence
        )

    def _get_savings_rate(self, action: str) -> float:
        """Get savings rate for an action"""
        action_lower = action.lower()

        if 'shutdown' in action_lower:
            return self.SAVINGS_RATES['shutdown']
        elif 'downsize' in action_lower:
            return self.SAVINGS_RATES['downsize']
        elif 'storage' in action_lower or 'lifecycle' in action_lower:
            return self.SAVINGS_RATES['storage_optimization']
        elif 'scale' in action_lower:
            return self.SAVINGS_RATES['scale']
        elif 'investigate' in action_lower:
            return self.SAVINGS_RATES['investigate']
        elif 'performance' in action_lower:
            return self.SAVINGS_RATES['performance_investigation']
        elif 'availability' in action_lower or 'ha' in action_lower:
            return self.SAVINGS_RATES['ha_review']
        else:
            return 0.0

    def calculate_total_savings(self, recommendations: List[Dict]) -> Tuple[float, List[SavingsEstimate]]:
        """Calculate total estimated savings"""
        estimates = []
        total = 0

        for rec in recommendations:
            estimate = self.calculate_savings(rec)
            estimates.append(estimate)
            total += estimate.estimated_monthly_savings

        return round(total, 2), estimates