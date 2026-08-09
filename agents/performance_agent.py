"""Performance Agent - Analyzes latency and availability metrics"""

from typing import List, Dict
from dataclasses import dataclass

@dataclass
class PerformanceFinding:
    resource_id: str
    resource_name: str
    resource_type: str
    latency_ms: float
    availability_percent: float
    issue: str
    recommendation: str

class PerformanceAgent:
    """Agent responsible for performance monitoring"""

    def __init__(self, records: List[Dict]):
        self.records = records

    def identify_latency_issues(self, latency_threshold: float = 1000) -> List[PerformanceFinding]:
        """Identify resources with latency issues"""
        findings = []
        for record in self.records:
            latency = record.get('latency_ms', 0)
            if latency > latency_threshold:
                issue = f"Latency {latency}ms exceeds threshold"
                recommendation = self._get_latency_recommendation(latency)

                findings.append(PerformanceFinding(
                    resource_id=record['resource_id'],
                    resource_name=record['resource_name'],
                    resource_type=record['resource_type'],
                    latency_ms=latency,
                    availability_percent=record.get('availability', 100),
                    issue=issue,
                    recommendation=recommendation
                ))
        return findings

    def _get_latency_recommendation(self, latency: float) -> str:
        """Get appropriate recommendation based on latency"""
        if latency < 1500:
            return "Implement caching"
        elif latency < 2000:
            return "Scale vertically"
        elif latency < 2500:
            return "Optimize database queries"
        else:
            return "Review architecture and redesign"

    def identify_availability_gaps(self, availability_threshold: float = 99.9) -> List[PerformanceFinding]:
        """Identify resources below availability requirements"""
        findings = []
        for record in self.records:
            availability = record.get('availability', 100)
            if availability < availability_threshold:
                issue = f"Availability {availability:.1f}% below requirement"
                recommendation = "Review high availability configuration"

                findings.append(PerformanceFinding(
                    resource_id=record['resource_id'],
                    resource_name=record['resource_name'],
                    resource_type=record['resource_type'],
                    latency_ms=record.get('latency_ms', 0),
                    availability_percent=availability,
                    issue=issue,
                    recommendation=recommendation
                ))
        return findings