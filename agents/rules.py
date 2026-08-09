"""Rules Engine - Simple rule-based detection for optimization"""

from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class RuleResult:
    rule_id: int
    rule_name: str
    triggered: bool
    resource: str
    recommendation: str
    severity: str  # low, medium, high, critical

class RulesEngine:
    """Simple rules engine for cloud resource optimization"""

    RULES = [
        {"id": 1, "name": "Idle Resource",
         "description": "CPU < 10%",
         "condition": lambda r: r.get('cpu_avg', 0) < 10},
        {"id": 2, "name": "Fully Idle Resource",
         "description": "CPU < 5%",
         "condition": lambda r: r.get('cpu_avg', 0) < 5},
        {"id": 3, "name": "Overutilized Resource",
         "description": "CPU > 85%",
         "condition": lambda r: r.get('cpu_avg', 0) > 85},
        {"id": 4, "name": "Cost Anomaly",
         "description": "Monthly cost increased > 30%",
         "condition": lambda r: r.get('cost_increase_pct', 0) > 30},
        {"id": 5, "name": "Storage Growth Concern",
         "description": "Storage growth > 20%",
         "condition": lambda r: r.get('storage_growth_pct', 0) > 20},
        {"id": 6, "name": "High Latency",
         "description": "Latency > 1000 ms",
         "condition": lambda r: r.get('latency_ms', 0) > 1000},
        {"id": 7, "name": "Low Availability",
         "description": "Availability < 99.9",
         "condition": lambda r: r.get('availability', 100) < 99.9},
    ]

    RECOMMENDATIONS = {
        1: "Downsize resource",
        2: "Shutdown resource",
        3: "Scale resource",
        4: "Investigate cost anomaly",
        5: "Review lifecycle policy",
        6: "Performance investigation",
        7: "Review high availability configuration",
    }

    SEVERITY_MAP = {
        1: "medium",   # downsize
        2: "high",     # shutdown
        3: "high",     # scale up
        4: "medium",   # cost anomaly
        5: "low",      # storage review
        6: "medium",   # latency
        7: "critical", # availability
    }

    def evaluate_resource(self, record: Dict) -> List[RuleResult]:
        """Evaluate a single resource against all rules"""
        results = []
        resource_name = record.get('resource_name', record.get('resource_id', 'unknown'))

        # Calculate cost increase percentage
        current_cost = record.get('monthly_cost', 0)
        previous_cost = record.get('previous_month_cost', 0)
        if previous_cost > 0:
            cost_increase_pct = ((current_cost - previous_cost) / previous_cost) * 100
        else:
            cost_increase_pct = 0

        record['cost_increase_pct'] = cost_increase_pct

        for rule in self.RULES:
            rule_result = RuleResult(
                rule_id=rule['id'],
                rule_name=rule['name'],
                triggered=False,
                resource=resource_name,
                recommendation="",
                severity=self.SEVERITY_MAP.get(rule['id'], "low")
            )

            if rule['condition'](record):
                rule_result.triggered = True
                rule_result.recommendation = self.RECOMMENDATIONS[rule['id']]

            results.append(rule_result)

        return results

    def evaluate_all_resources(self, records: List[Dict]) -> List[RuleResult]:
        """Evaluate all resources against all rules"""
        all_results = []
        for record in records:
            results = self.evaluate_resource(record)
            all_results.extend([r for r in results if r.triggered])
        return all_results