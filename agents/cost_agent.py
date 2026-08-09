"""Cost Agent - Identifies expensive resources and cost anomalies"""

from typing import List, Dict
from dataclasses import dataclass

@dataclass
class CostFinding:
    resource_id: str
    resource_name: str
    monthly_cost: float
    previous_month_cost: float
    cost_increase_pct: float
    issue: str

class CostAgent:
    """Agent responsible for identifying cost-related issues"""

    def __init__(self, records: List[Dict]):
        self.records = records

    def identify_expensive_resources(self, threshold: float = None) -> List[CostFinding]:
        """Identify resources above cost threshold"""
        if not self.records:
            return []

        # Default threshold: mean + 1 std dev
        if threshold is None:
            costs = [r['monthly_cost'] for r in self.records]
            mean_cost = sum(costs) / len(costs)
            std_cost = (sum((c - mean_cost) ** 2 for c in costs) / len(costs)) ** 0.5
            threshold = mean_cost + std_cost

        findings = []
        for record in self.records:
            if record['monthly_cost'] > threshold:
                findings.append(CostFinding(
                    resource_id=record['resource_id'],
                    resource_name=record['resource_name'],
                    monthly_cost=record['monthly_cost'],
                    previous_month_cost=record['previous_month_cost'],
                    cost_increase_pct=record.get('cost_increase_pct', 0),
                    issue="High cost resource"
                ))

        return findings

    def detect_cost_increases(self, threshold: float = 30.0) -> List[CostFinding]:
        """Detect resources with significant cost increases"""
        findings = []
        for record in self.records:
            cost_increase = record.get('cost_increase_pct', 0)
            if cost_increase > threshold:
                findings.append(CostFinding(
                    resource_id=record['resource_id'],
                    resource_name=record['resource_name'],
                    monthly_cost=record['monthly_cost'],
                    previous_month_cost=record['previous_month_cost'],
                    cost_increase_pct=cost_increase,
                    issue=f"Cost increased {cost_increase:.1f}%"
                ))

        return findings

    def get_cost_summary(self) -> Dict:
        """Get overall cost summary statistics"""
        if not self.records:
            return {}

        total_current = sum(r['monthly_cost'] for r in self.records)
        total_previous = sum(r['previous_month_cost'] for r in self.records)
        total_increase = total_current - total_previous

        return {
            'total_current_month': total_current,
            'total_previous_month': total_previous,
            'total_change': total_increase,
            'percentage_change': (total_increase / total_previous * 100) if total_previous > 0 else 0,
            'resource_count': len(self.records)
        }