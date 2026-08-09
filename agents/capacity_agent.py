"""Capacity Agent - Identifies underutilized and overutilized resources"""

from typing import List, Dict
from dataclasses import dataclass

@dataclass
class CapacityFinding:
    resource_id: str
    resource_name: str
    resource_type: str
    cpu_avg: float
    cpu_p95: float
    memory_avg: float
    memory_p95: float
    issue: str
    recommendation: str

class CapacityAgent:
    """Agent responsible for identifying capacity issues"""

    def __init__(self, records: List[Dict]):
        self.records = records

    def identify_underutilized(self, cpu_threshold: float = 10.0,
                               memory_threshold: float = 20.0) -> List[CapacityFinding]:
        """Identify underutilized resources"""
        findings = []
        for record in self.records:
            cpu = record.get('cpu_avg', 0)
            memory = record.get('memory_avg', 0)

            if cpu < cpu_threshold and memory < memory_threshold:
                if cpu < 5:
                    issue = "Fully idle - candidate for shutdown"
                    recommendation = "Shutdown resource"
                else:
                    issue = f"Underutilized (CPU: {cpu}%, Memory: {memory}%)"
                    recommendation = "Downsize resource"

                findings.append(CapacityFinding(
                    resource_id=record['resource_id'],
                    resource_name=record['resource_name'],
                    resource_type=record['resource_type'],
                    cpu_avg=cpu,
                    cpu_p95=record.get('cpu_p95', 0),
                    memory_avg=memory,
                    memory_p95=record.get('memory_p95', 0),
                    issue=issue,
                    recommendation=recommendation
                ))

        return findings

    def identify_overutilized(self, cpu_threshold: float = 85.0,
                              memory_threshold: float = 85.0) -> List[CapacityFinding]:
        """Identify overutilized resources"""
        findings = []
        for record in self.records:
            cpu = record.get('cpu_avg', 0)
            memory = record.get('memory_avg', 0)

            if cpu > cpu_threshold or memory > memory_threshold:
                issue = f"Overutilized (CPU: {cpu}%, Memory: {memory}%)"
                recommendation = "Scale resource"

                findings.append(CapacityFinding(
                    resource_id=record['resource_id'],
                    resource_name=record['resource_name'],
                    resource_type=record['resource_type'],
                    cpu_avg=cpu,
                    cpu_p95=record.get('cpu_p95', 0),
                    memory_avg=memory,
                    memory_p95=record.get('memory_p95', 0),
                    issue=issue,
                    recommendation=recommendation
                ))

        return findings

    def identify_storage_growth(self, threshold: float = 20.0) -> List[CapacityFinding]:
        """Identify resources with high storage growth"""
        findings = []
        for record in self.records:
            growth = record.get('storage_growth_pct', 0)
            if growth > threshold:
                findings.append(CapacityFinding(
                    resource_id=record['resource_id'],
                    resource_name=record['resource_name'],
                    resource_type=record['resource_type'],
                    cpu_avg=record.get('cpu_avg', 0),
                    cpu_p95=record.get('cpu_p95', 0),
                    memory_avg=record.get('memory_avg', 0),
                    memory_p95=record.get('memory_p95', 0),
                    issue=f"Storage growth {growth}% - exceeds {threshold}% threshold",
                    recommendation="Review lifecycle policy"
                ))

        return findings