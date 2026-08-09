"""Recommendation Agent - Synthesizes findings into final recommendations with savings and business impact"""

from typing import List, Dict
from dataclasses import dataclass

from agents.calculator import SavingsCalculator

@dataclass
class Recommendation:
    resource_id: str
    resource_name: str
    issue: str
    recommended_action: str
    estimated_monthly_savings: float
    confidence: str
    business_impact: str
    policy_reference: str = ""

class RecommendationAgent:
    """Agent responsible for generating final recommendations"""

    IMPACT_TEMPLATES = {
        "shutdown": "Eliminates ongoing cost for an idle resource with no measurable workload.",
        "downsize": "Reduces spend while keeping headroom for the observed usage pattern.",
        "scale": "Prevents performance degradation and SLO breaches under sustained high load.",
        "investigate cost anomaly": "Flags unexpected spend growth before it compounds next billing cycle.",
        "review lifecycle policy": "Controls runaway storage growth and associated long-term cost.",
        "performance investigation": "Protects user experience by addressing latency outside SLO targets.",
        "review high availability configuration": "Reduces risk of downtime that could breach availability SLOs.",
    }

    def __init__(self, records: List[Dict]):
        self.calculator = SavingsCalculator(records)

    def generate(self, finding: Dict, policy_context: List[Dict] = None) -> Recommendation:
        """Generate one recommendation from a finding dict (works with any *Finding dataclass via __dict__)"""
        action = finding.get("recommendation", finding.get("recommended_action", "Review resource"))
        savings_estimate = self.calculator.calculate_savings({
            "resource_id": finding.get("resource_id", finding.get("resource", "")),
            "resource_name": finding.get("resource_name", finding.get("resource", "unknown")),
            "recommended_action": action,
        })

        impact = self.IMPACT_TEMPLATES.get(action.lower(), "Improves overall cost or performance posture.")
        policy_ref = policy_context[0]["source"] if policy_context else ""

        return Recommendation(
            resource_id=savings_estimate.resource_id,
            resource_name=savings_estimate.resource_name,
            issue=finding.get("issue", ""),
            recommended_action=action,
            estimated_monthly_savings=savings_estimate.estimated_monthly_savings,
            confidence=savings_estimate.confidence,
            business_impact=impact,
            policy_reference=policy_ref,
        )

    def generate_all(self, findings: List[Dict], rag_agent=None) -> List[Recommendation]:
        """Generate recommendations for a list of findings, deduplicated by resource_id"""
        seen = set()
        recommendations = []
        for finding in findings:
            f = finding.__dict__ if hasattr(finding, "__dict__") else finding
            resource_id = f.get("resource_id", f.get("resource", ""))
            if resource_id in seen:
                continue
            seen.add(resource_id)

            policy_context = None
            if rag_agent is not None:
                policy_context = rag_agent.query(f.get("issue", f.get("recommendation", "")))

            recommendations.append(self.generate(f, policy_context))
        return recommendations
