"""FastAPI backend for CloudOptima AI - runs the LangGraph workflow and exposes results"""

from dataclasses import asdict
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from graph import Workflow

app = FastAPI(title="CloudOptima AI")

workflow = Workflow()
_last_result: Optional[dict] = None


def _to_plain(obj):
    """Convert dataclass instances (or lists of them) to plain dicts for JSON responses"""
    if isinstance(obj, list):
        return [_to_plain(o) for o in obj]
    if hasattr(obj, "__dict__") and not isinstance(obj, dict):
        return asdict(obj)
    return obj


class ApproveRequest(BaseModel):
    resource_id: str
    approved: bool


class SearchRequest(BaseModel):
    query: str
    n_results: int = 3


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze():
    """Run the full agent workflow: Data -> Cost -> Capacity -> Performance -> RAG -> Recommendation -> Approval"""
    global _last_result
    state = workflow.run()
    _last_result = {
        "resources": state["resources"],
        "cost_findings": _to_plain(state["cost_findings"]),
        "capacity_findings": _to_plain(state["capacity_findings"]),
        "performance_findings": _to_plain(state["performance_findings"]),
        "recommendations": _to_plain(state["recommendations"]),
        "approval_status": state["approval_status"],
        "summary": state["executive_summary"],
    }
    return _last_result


@app.get("/results")
def results():
    if _last_result is None:
        raise HTTPException(status_code=404, detail="No analysis has been run yet. Call POST /analyze first.")
    return _last_result


@app.post("/approve")
def approve(request: ApproveRequest):
    try:
        decision = workflow.approval_agent.decide(request.resource_id, request.approved)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "decision": asdict(decision),
        "action_plan": workflow.approval_agent.get_action_plan(),
    }


@app.post("/search")
def search(request: SearchRequest):
    """Query the ChromaDB knowledge base directly"""
    return {"results": workflow.rag_agent.query(request.query, n_results=request.n_results)}
