"""Streamlit UI for CloudOptima AI - talks to the FastAPI backend at localhost:8000"""

import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(page_title="CloudOptima AI", layout="wide")


def call_api(method: str, path: str, **kwargs):
    try:
        resp = requests.request(method, f"{API_URL}{path}", timeout=30, **kwargs)
        if resp.status_code >= 400:
            st.error(f"API error ({resp.status_code}): {resp.json().get('detail', resp.text)}")
            return None
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach the backend. Start it with: uvicorn main:app --reload")
        return None


def ensure_results():
    """Fetch cached results, or run analysis if none exist yet"""
    if "results" not in st.session_state:
        results = call_api("GET", "/results")
        if results is None:
            results = call_api("POST", "/analyze")
        st.session_state["results"] = results
    return st.session_state["results"]


st.sidebar.title("CloudOptima AI")
page = st.sidebar.radio("Navigate", ["Dashboard", "Recommendations", "Approval Screen", "Knowledge Search", "Chat"])

if st.sidebar.button("Run New Analysis"):
    with st.spinner("Running agent workflow..."):
        results = call_api("POST", "/analyze")
        if results is not None:
            st.session_state["results"] = results
            st.session_state.pop("approval_status", None)
    st.rerun()


if page == "Dashboard":
    st.title("Dashboard")
    results = ensure_results()

    if results:
        resources = results["resources"]
        recommendations = results["recommendations"]
        total_savings = sum(r["estimated_monthly_savings"] for r in recommendations)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Resources", len(resources))
        col2.metric("Optimization Opportunities", len(recommendations))
        col3.metric("Potential Monthly Savings", f"${total_savings:,.2f}")

        if results.get("summary"):
            st.subheader("Executive Summary")
            st.markdown(results["summary"])

        st.subheader("All Monitored Resources")
        st.dataframe(resources, use_container_width=True)


elif page == "Recommendations":
    st.title("Recommendations")
    results = ensure_results()

    if results:
        recommendations = results["recommendations"]
        if not recommendations:
            st.info("No optimization opportunities found.")
        else:
            table = [
                {
                    "Resource": r["resource_name"],
                    "Issue": r["issue"],
                    "Recommendation": r["recommended_action"],
                    "Savings ($/mo)": r["estimated_monthly_savings"],
                    "Confidence": r["confidence"],
                    "Business Impact": r["business_impact"],
                }
                for r in recommendations
            ]
            st.dataframe(table, use_container_width=True)


elif page == "Approval Screen":
    st.title("Approval Screen")
    results = ensure_results()

    if results:
        recommendations = results["recommendations"]
        decisions = st.session_state.get("approval_status", {})

        if not recommendations:
            st.info("No recommendations pending approval.")

        for rec in recommendations:
            resource_id = rec["resource_id"]
            status = decisions.get(resource_id, "pending")

            with st.container(border=True):
                cols = st.columns([3, 2, 2, 1, 1])
                cols[0].write(f"**{rec['resource_name']}** — {rec['issue']}")
                cols[1].write(rec["recommended_action"])
                cols[2].write(f"${rec['estimated_monthly_savings']:,.2f}/mo")

                if status == "pending":
                    if cols[3].button("Approve", key=f"approve_{resource_id}"):
                        resp = call_api("POST", "/approve", json={"resource_id": resource_id, "approved": True})
                        if resp:
                            decisions[resource_id] = "approved"
                            st.session_state["approval_status"] = decisions
                            st.rerun()
                    if cols[4].button("Reject", key=f"reject_{resource_id}"):
                        resp = call_api("POST", "/approve", json={"resource_id": resource_id, "approved": False})
                        if resp:
                            decisions[resource_id] = "rejected"
                            st.session_state["approval_status"] = decisions
                            st.rerun()
                else:
                    cols[3].write("✅ Approved" if status == "approved" else "❌ Rejected")

        approved = [rid for rid, s in decisions.items() if s == "approved"]
        if approved:
            st.subheader("Final Action Plan (Approved)")
            approved_recs = [r for r in recommendations if r["resource_id"] in approved]
            st.dataframe(approved_recs, use_container_width=True)


elif page == "Knowledge Search":
    st.title("Knowledge Search")
    st.write("Search the optimization policy knowledge base (ChromaDB).")

    query = st.text_input("Search query", placeholder="e.g. what is the availability SLO target?")
    if query:
        resp = call_api("POST", "/search", json={"query": query, "n_results": 3})
        if resp:
            for r in resp["results"]:
                with st.container(border=True):
                    st.caption(f"Source: {r['source']}")
                    st.write(r["content"])


elif page == "Chat":
    st.title("Cloud Optimization Assistant")
    st.caption("Ask about cloud cost optimization — rightsizing, capacity, SLOs, cost anomalies, and approval policies. Off-topic questions are refused.")

    SAMPLE_QUESTIONS = [
        "What are the rightsizing guidelines for underutilized instances?",
        "What are the availability and latency SLO targets?",
        "How are shutdown recommendations approved?",
        "What triggers a cost anomaly investigation?",
        "How should idle resources be handled to cut costs?",
    ]

    if "messages" not in st.session_state:
        st.session_state.messages = []

    def respond(text: str):
        st.session_state.messages.append({"role": "user", "content": text})
        resp = call_api("POST", "/chat", json={"message": text})
        answer = resp["answer"] if resp else "Cannot reach the backend. Start it with: uvicorn main:app --reload"
        st.session_state.messages.append({"role": "assistant", "content": answer})

    picked = st.pills("Sample questions", SAMPLE_QUESTIONS, selection_mode="single", key="sample_pill")
    if picked:
        respond(picked)
        st.session_state.pop("sample_pill", None)
        st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about cloud optimization..."):
        respond(prompt)
        st.rerun()
