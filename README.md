# [CloudOptima AI](https://anix9920.github.io/agentic-ai-aniket-capstone/)

Cloud Cost, Performance & Capacity Optimization Agent — a beginner-friendly Agentic AI
demo on mock CSV data. No database, no authentication, no Docker. Runs fully offline by
default; set an OpenRouter API key in `.env` to enable LLM-written summaries,
recommendation impact text, real RAG embeddings, and a cloud-optimization chat assistant.

## Architecture

```
LangGraph workflow (graph.py):

  START -> Data Agent -> Cost Agent -> Capacity Agent -> Performance Agent
        -> RAG Agent -> Recommendation Agent -> Approval Agent -> Summarize -> END

FastAPI (main.py)  <-- calls -->  Streamlit UI (app.py)
      |
      v
  Workflow (graph.py) -> agents/*.py -> data/*.csv, data/knowledge/*.txt
```

- **Data Agent** — reads `data/cloud_cost.csv` and `data/resource_metrics.csv`, merges them.
- **Cost Agent** — flags expensive resources and cost spikes > 30%.
- **Capacity Agent** — flags idle/underutilized (CPU < 10%), overutilized (CPU > 85%),
  and high storage growth (> 20%) resources.
- **Performance Agent** — flags high latency (> 1000ms) and low availability (< 99.9%).
- **RAG Agent** — retrieves relevant policy text from `data/knowledge/*.txt` via an
  in-memory vector index (OpenRouter embeddings when a key is set, pure-Python hashing
  otherwise — no native dependencies).
- **Summarize** — writes an executive summary of the analysis (LLM-written when a key is
  set, template otherwise).
- **Chat** — answers cloud-optimization questions grounded in the policy knowledge base;
  off-topic questions are refused.
- **Recommendation Agent** — turns findings into recommendations with estimated savings
  and a plain-English business impact statement.
- **Approval Agent** — mock approve/reject workflow; only approved items make the final
  action plan.

## Mock data

The app runs entirely on hand-authored mock data in `data/` — no real cloud
account or database is ever contacted. The only external API is the *optional*
OpenRouter LLM (see below); without a key the app stays fully offline. Two CSV
files hold the fleet, and four policy `.txt` files make up the RAG knowledge base.

### `data/cloud_cost.csv` — billing snapshot

One row per resource. Drives the **Cost Agent**:

| Column | Meaning |
|---|---|
| `resource_id` | unique key, e.g. `vm-001`, `storage-001` |
| `resource_name` | friendly name, e.g. `web-server-01` |
| `resource_type` | `VM` or `Storage` |
| `monthly_cost` | current monthly cost (USD) |
| `previous_month_cost` | last month's cost (USD) |

The Cost Agent flags resources above *mean + 1 std dev* as expensive, and any
with a month-over-month cost increase over 30% as a cost anomaly.

### `data/resource_metrics.csv` — utilization snapshot

Shares the same `resource_id`s as the cost file (the two are joined on
`resource_id`). Drives the **Capacity** and **Performance Agents**:

| Column | Meaning |
|---|---|
| `cpu_avg` / `cpu_p95` | average / p95 CPU utilization % |
| `memory_avg` / `memory_p95` | average / p95 memory utilization % |
| `storage_growth_pct` | month-over-month storage growth % |
| `latency_ms` | average request latency |
| `availability` | uptime percentage |

### `data/knowledge/*.txt` — RAG knowledge base

`rightsizing_guide.txt`, `optimization_policy.txt`, `slo_policy.txt`, and
`approval_policy.txt`. Loaded and chunked into an in-memory vector index at
startup (pure-Python hashing embeddings, no ChromaDB), then searched by the RAG
Agent for policy context and via the Knowledge Search page.

### Detection thresholds

| Rule | Threshold |
|---|---|
| Idle / fully idle | CPU avg < 10% / < 5% → downsize / shutdown |
| Overutilized | CPU avg > 85% → scale |
| Cost anomaly | monthly cost up > 30% |
| Storage growth | growth > 20% → lifecycle review |
| High latency | latency > 1000 ms |
| Low availability | availability < 99.9% |

### Caveat: savings are computed, not stored

Estimated savings don't come from the CSVs — `agents/calculator.py` applies
hardcoded rates to `monthly_cost` (shutdown 80%, downsize 30%, storage
optimization 20%, scale −20%). The mock data only drives *which findings*
appear; the dollar figures are derived from constants.

## Optional LLM (OpenRouter)

Everything above runs with zero API calls. To enable the LLM features (executive
summary, per-recommendation impact text, real embeddings, chat answers):

1. `cp .env.example .env`
2. Set `OPENROUTER_API_KEY` in `.env` (get one at https://openrouter.ai/keys).
3. Optionally change `MODEL` (default `meta-llama/llama-3.1-8b-instruct`) or
   `EMBEDDING_MODEL` (default `openai/text-embedding-3-small`).

Without a key the app still works end-to-end using deterministic templates and
hashing embeddings. The key stays in your local `.env`, which is gitignored.

## Setup

Requires Python 3.10+.

```powershell
cd cloudoptima-ai
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

(macOS/Linux: `source .venv/bin/activate` instead of the `Activate.ps1` line.)

## Running the app

Two processes, in two terminals, both from the `cloudoptima-ai` folder with the venv active.

**Terminal 1 — API backend:**

```powershell
uvicorn main:app --reload
```

Runs at http://localhost:8000. Check http://localhost:8000/docs for interactive API docs.

**Terminal 2 — Streamlit UI:**

```powershell
streamlit run app.py
```

Opens at http://localhost:8501.

### Using the UI

1. **Dashboard** — click "Run New Analysis" in the sidebar to execute the full agent
   workflow. Shows total resources, optimization opportunities, and potential savings.
2. **Recommendations** — table of every issue found, the recommended action, estimated
   monthly savings, and business impact.
3. **Approval Screen** — approve or reject each recommendation; approved items form the
   final action plan shown at the bottom.
4. **Knowledge Search** — free-text search over the policy documents in
   `data/knowledge/`, served by the pure-Python RAG index.
5. **Chat** — ask cloud-optimization questions (sample prompts provided). Answers are
   grounded in the policy knowledge base; off-topic questions are refused.

## API only (no UI)

```powershell
curl http://localhost:8000/health
curl -X POST http://localhost:8000/analyze
curl http://localhost:8000/results
curl -X POST http://localhost:8000/approve -H "Content-Type: application/json" -d "{\"resource_id\": \"vm-003\", \"approved\": true}"
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"message\": \"What are the rightsizing guidelines?\"}"
```

## Editing the mock data

Everything is driven off the two CSVs above plus the four policy `.txt` files.
Edit them and re-run `/analyze` to see different results — no other code changes
needed.

## Known issue (resolved)

Earlier versions stored the knowledge base in ChromaDB. On some Windows setups ChromaDB's
native Rust/SQLite/HNSW backend and ONNX Runtime crash the Python process (access
violation on `count()`/`add()`), which killed the whole API at startup. Rather than depend
on the Microsoft Visual C++ Redistributable being present, the RAG Agent now uses a
pure-Python in-memory vector index built on a small hashing embedder — no native
dependencies at all, so the backend starts reliably on any machine. If you still have a
stale `chroma_db/` directory it is no longer used and can be deleted.

---

Maintained by anix9920.
