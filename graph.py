"""LangGraph Implementation - wires the 7 agents into one workflow"""

import re
from typing import Dict, List, TypedDict
from langgraph.graph import StateGraph, END

from llm import generate, llm_enabled
from agents.data_agent import DataAgent
from agents.cost_agent import CostAgent
from agents.capacity_agent import CapacityAgent
from agents.performance_agent import PerformanceAgent
from agents.rag_agent import RAGAgent
from agents.recommendation_agent import RecommendationAgent
from agents.approval_agent import ApprovalAgent


_CLOUD_TOPIC_RE = re.compile(
    r"(cloud|aws|azure|gcp|ec2|s3|vm\b|instance|server|host\b|cluster|kubernetes|container|docker|storage|"
    r"bucket|database|\bdb\b|load balancer|network|bandwidth|cpu|memory|ram\b|disk|utilization|capacity|"
    r"rightsiz|downsize|scale|shutdown|idle|cost|spend|billing|\bbill\b|budget|pric|saving|save|"
    r"optimiz|anomaly|slo|availability|latency|policy|approval|resource|autoscaling|monitor|efficiency|waste)",
    re.IGNORECASE,
)

_CHAT_SYSTEM = (
    "You are CloudOptima AI, a cloud cost optimization assistant. "
    "Answer ONLY questions about cloud cost optimization: rightsizing, capacity, SLOs, cost anomalies, "
    "and approval policies. Ground your answer in the provided policy context and cite its source when relevant. "
    "If the question is not about cloud optimization, politely decline and say you can only help with cloud "
    "optimization topics. Be concise."
)


class AnalysisState(TypedDict):
    resources: List[Dict]
    cost_findings: List
    capacity_findings: List
    performance_findings: List
    policy_context: List[Dict]
    recommendations: List
    approval_status: Dict
    executive_summary: str


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

    def summarize_node(self, state: AnalysisState) -> AnalysisState:
        state["executive_summary"] = self._executive_summary(state)
        return state

    def _executive_summary(self, state: AnalysisState) -> str:
        """Concise summary of the analysis; LLM-written when available, template fallback otherwise."""
        recs = state["recommendations"]
        total_savings = sum(r.estimated_monthly_savings for r in recs)
        template = (
            f"Analysis reviewed {len(state['resources'])} cloud resources and surfaced "
            f"{len(recs)} optimization opportunities worth an estimated ${total_savings:,.2f}/month. "
            "Recommendations are queued for approval."
        )
        if not llm_enabled() or not recs:
            return template

        lines = "\n".join(
            f"- {r.resource_name}: {r.recommended_action} (${r.estimated_monthly_savings:,.2f}/mo)"
            for r in recs
        )
        try:
            return generate(
                "You are a cloud cost optimization engineer writing a short executive summary for leadership.",
                (
                    f"Analyzed {len(state['resources'])} cloud resources. "
                    f"{len(recs)} optimization opportunities totaling ${total_savings:,.2f}/month.\n\n"
                    f"Recommendations:\n{lines}\n\n"
                    "Write a 2-3 sentence executive summary of the situation and the key actions proposed. "
                    "No preamble."
                ),
            )
        except Exception:
            return template

    def build_graph(self) -> StateGraph:
        graph = StateGraph(AnalysisState)

        graph.add_node("data", self.data_node)
        graph.add_node("cost", self.cost_node)
        graph.add_node("capacity", self.capacity_node)
        graph.add_node("performance", self.performance_node)
        graph.add_node("rag", self.rag_node)
        graph.add_node("recommendation", self.recommendation_node)
        graph.add_node("approval", self.approval_node)
        graph.add_node("summarize", self.summarize_node)

        graph.set_entry_point("data")
        graph.add_edge("data", "cost")
        graph.add_edge("cost", "capacity")
        graph.add_edge("capacity", "performance")
        graph.add_edge("performance", "rag")
        graph.add_edge("rag", "recommendation")
        graph.add_edge("recommendation", "approval")
        graph.add_edge("approval", "summarize")
        graph.add_edge("summarize", END)

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
            "executive_summary": "",
        })

    def chat(self, message: str) -> str:
        """Answer a cloud-optimization question, grounded in the RAG knowledge base. Refuses off-topic queries."""
        message = message.strip()
        if not _CLOUD_TOPIC_RE.search(message):
            return ("I can only help with cloud cost optimization questions — rightsizing, capacity, SLOs, "
                    "cost anomalies, and approval policies. Try one of the sample questions.")

        context = self.rag_agent.get_context_for_query(message)
        if not context:
            return "I couldn't find relevant policy guidance for that question."
        if not llm_enabled():
            return context  # already formatted "[Source: ...]\n..."
        try:
            return generate(_CHAT_SYSTEM, f"Question: {message}\n\nRelevant policy context:\n{context}")
        except Exception:
            return "I couldn't reach the language model right now. Please try again in a moment."
