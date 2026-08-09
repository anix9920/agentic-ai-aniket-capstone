"""LangGraph Implementation - wires the 7 agents into one workflow"""

from typing import Dict, List, TypedDict
from langgraph.graph import StateGraph, END

from agents.data_agent import DataAgent
from agents.cost_agent import CostAgent
from agents.capacity_agent import CapacityAgent
from agents.performance_agent import PerformanceAgent
from agents.rag_agent import RAGAgent
from agents.recommendation_agent import RecommendationAgent
from agents.approval_agent import ApprovalAgent


class AnalysisState(TypedDict):
    resources: List[Dict]
    cost_findings: List
    capacity_findings: List
    performance_findings: List
    policy_context: List[Dict]
    recommendations: List
    approval_status: Dict


class Workflow:
    """Main LangGraph workflow: Data -> Cost -> Capacity -> Performance -> RAG -> Recommendation -> Approval"""

    def __init__(self, data_agent: DataAgent = None):
        self.data_agent = data_agent or DataAgent()
        records = self.data_agent.get_all_records()

        self.cost_agent = CostAgent(records)
        self.capacity_agent = CapacityAgent(records)
        self.performance_agent = PerformanceAgent(records)
        self.rag_agent = RAGAgent()
        self.recommendation_agent = RecommendationAgent(records)
        self.approval_agent = ApprovalAgent()

    def data_node(self, state: AnalysisState) -> AnalysisState:
        state["resources"] = self.data_agent.get_all_records()
        return state

    def cost_node(self, state: AnalysisState) -> AnalysisState:
        findings = self.cost_agent.identify_expensive_resources()
        findings += self.cost_agent.detect_cost_increases()
        state["cost_findings"] = findings
        return state

    def capacity_node(self, state: AnalysisState) -> AnalysisState:
        findings = self.capacity_agent.identify_underutilized()
        findings += self.capacity_agent.identify_overutilized()
        findings += self.capacity_agent.identify_storage_growth()
        state["capacity_findings"] = findings
        return state

    def performance_node(self, state: AnalysisState) -> AnalysisState:
        findings = self.performance_agent.identify_latency_issues()
        findings += self.performance_agent.identify_availability_gaps()
        state["performance_findings"] = findings
        return state

    def rag_node(self, state: AnalysisState) -> AnalysisState:
        state["policy_context"] = [
            *self.rag_agent.query("rightsizing guidelines"),
            *self.rag_agent.query("SLO requirements"),
        ]
        return state

    def recommendation_node(self, state: AnalysisState) -> AnalysisState:
        all_findings = state["cost_findings"] + state["capacity_findings"] + state["performance_findings"]
        state["recommendations"] = self.recommendation_agent.generate_all(all_findings, self.rag_agent)
        return state

    def approval_node(self, state: AnalysisState) -> AnalysisState:
        decisions = self.approval_agent.queue_for_approval(state["recommendations"])
        state["approval_status"] = {"pending": [d.__dict__ for d in decisions]}
        return state

    def build_graph(self) -> StateGraph:
        graph = StateGraph(AnalysisState)

        graph.add_node("data", self.data_node)
        graph.add_node("cost", self.cost_node)
        graph.add_node("capacity", self.capacity_node)
        graph.add_node("performance", self.performance_node)
        graph.add_node("rag", self.rag_node)
        graph.add_node("recommendation", self.recommendation_node)
        graph.add_node("approval", self.approval_node)

        graph.set_entry_point("data")
        graph.add_edge("data", "cost")
        graph.add_edge("cost", "capacity")
        graph.add_edge("capacity", "performance")
        graph.add_edge("performance", "rag")
        graph.add_edge("rag", "recommendation")
        graph.add_edge("recommendation", "approval")
        graph.add_edge("approval", END)

        return graph

    def run(self) -> AnalysisState:
        compiled_graph = self.build_graph().compile()
        return compiled_graph.invoke({
            "resources": [],
            "cost_findings": [],
            "capacity_findings": [],
            "performance_findings": [],
            "policy_context": [],
            "recommendations": [],
            "approval_status": {},
        })
