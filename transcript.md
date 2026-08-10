# CloudOptima AI — Presentation Transcript

Slide-by-slide speaking script for `index.html`. ~9–12 minutes at a natural pace.
Navigate slides with `→` / `←`.

---

## Slide 1 — Cover

> "Hi everyone, I'm Aniket, and this is my capstone project — **CloudOptima AI**. It's an agentic AI system that finds where a cloud bill is being wasted — idle servers, storage growing out of control, slow or unreliable resources — and turns those findings into concrete, human-approved recommendations. In short: eight nodes in one LangGraph workflow, running on mock data. And here's the nice part — the whole thing runs offline with zero external services by default, but a single API key in a `.env` file turns on real LLM features: executive summaries, grounded chat answers, and real embeddings. Either way, it's a clean demonstration of the full agentic pattern."

---

## Slide 2 — The Problem

> "Let's start with the problem. Cloud spend leaks in three predictable ways. **First, overspend** — idle virtual machines burn money every single month, and nobody notices until the bill arrives. **Second, performance risk** — an overloaded server silently breaches its latency and availability targets; your users feel it before your team does. **Third — and the big one — blind spots.** The data sits in spreadsheets and dashboards, but nothing connects the signal to a recommended action, and nothing enforces it. That's the gap this project fills: automating the whole loop from problem, to fix, to approval."

---

## Slide 3 — What it is

> "So what is it? It's an end-to-end optimization agent with **zero setup**. It reads monitoring data, detects cost, capacity, and performance issues, grounds its advice in a real policy knowledge base — so it's not making things up — then proposes an action plan a human has to approve. Four pillars: **agentic AI** — eight specialized nodes wired into one LangGraph workflow. **Real RAG** — genuine retrieval over policy documents, using OpenRouter embeddings when a key is set and a pure-Python hashing fallback otherwise. **Human-in-the-loop** — nothing changes without a human click. And **fully local** — mock CSV data, no database, no auth, no Docker; the only external piece is the optional LLM API. That's deliberate: the demo runs anywhere, instantly."

---

## Slide 4 — Architecture

> "Here's the architecture — three layers. On top, a **Streamlit UI** on port 8501 — dashboard, recommendations, approval screen, knowledge search, and a chat assistant. It talks over plain HTTP to the **FastAPI backend** on port 8000, which exposes six endpoints: health, analyze, results, approve, search, and chat. The backend runs the **LangGraph workflow**, and that workflow reads from the data directory — two CSVs describing the fleet, plus the policy text files for the knowledge base. So the whole system is: UI calls API, API runs the agent graph, agents read the data."

---

## Slide 5 — The Agentic Pipeline

> "This is the heart of the project — eight nodes, one directed graph. **Data** loads and merges the CSVs. **Cost** finds expensive resources and cost spikes. **Capacity** finds idle, overloaded, and fast-growing-storage resources. **Performance** checks latency and availability. The **RAG agent** pulls in relevant policy context. The **Recommendation agent** turns every finding into a concrete action with an estimated saving. The **Approval agent** queues everything for a human. And a final **Summarize** node writes the executive summary you see on the dashboard — an LLM-authored paragraph when a key is set, a template otherwise. What I love about this slide is the code — the whole graph is about twenty lines of LangGraph, and each node is a small, readable Python class. Every step is inspectable — nothing is a black box."

---

## Slide 6 — The Seven Agents

> "Let me introduce the cast properly — eight nodes, each with one job. The **Data Agent** reads the two CSVs and joins them on `resource_id`. The **Cost Agent** flags anything above the average plus one standard deviation, and any cost increase over thirty percent. The **Capacity Agent** finds idle machines — CPU under ten percent — overloaded ones above eighty-five, and storage growth past twenty percent. The **Performance Agent** catches latency above a thousand milliseconds and availability below ninety-nine point nine. The **RAG Agent** retrieves the relevant policy text for each issue — more on that in a moment. The **Recommendation Agent** is where it becomes useful — it attaches a savings estimate and a business impact to every finding, drafted by the LLM when a key is set and a template otherwise. The **Approval Agent** gates everything. And the **Summarize node** closes the graph with an executive summary of the run. Each one is a small file you can open and read."

---

## Slide 7 — Detection Rules

> "One thing I wanted to be deliberate about: **every rule is readable code.** There's no magic here. Each detector is a threshold you can see and edit — cost above mean plus one sigma, cost up more than thirty percent, CPU under ten or above eighty-five, storage growth over twenty, latency over a thousand, availability under ninety-nine point nine. If you want to change what the system flags, you change a threshold and the demo behaves differently. That makes it a great way to see how an agentic system actually makes decisions."

---

## Slide 8 — Sample Run

> "Let's show it actually working. This is a real run over the mock fleet of eighteen resources, and the system found fifteen optimization opportunities worth about two thousand, one hundred dollars a month. The **database server** is overutilized and expensive at fifteen hundred dollars a month. The **API gateway** is pegged at eighty-five percent CPU — it needs to scale up, which is why the savings is negative; growth costs money. The **batch processor's** cost jumped thirty-three percent. And the three **storage buckets** — media, logs, backup — are all growing past the threshold; a lifecycle policy alone recovers over three hundred dollars a month. Everything on this table was produced by the agents from raw CSV data — no hand-written answers."

---

## Slide 9 — RAG

> "Now the RAG agent, because it was the most interesting engineering problem. Recommendations are grounded in a real policy knowledge base — four policy documents. When an issue is found, the agent retrieves the relevant policy clause before suggesting an action, and it cites its source. Embeddings come from **OpenRouter** when a key is set — real vectors from a hosted model — and fall back to a **hashing trick**, a 256-dimension bag-of-words vector, no ML model, when it isn't. Either way, search is cosine similarity over text chunks in an in-memory index. The original version used ChromaDB, but ChromaDB ships native Rust and ONNX components that crashed the process on some Windows machines. I replaced it with this in-memory index, and the backend now starts reliably anywhere — with the optional OpenRouter embeddings layered on top when you want them. That's a real example of hitting a production issue and engineering around it."

---

## Slide 10 — Human-in-the-loop

> "Nothing in this system changes without a human. The Approval Agent queues every recommendation as **pending**. In the UI you approve or reject each one — and only the approved items become the final action plan. This is the human-in-the-loop pattern, and it matters beyond this demo: for an AI system that touches money and infrastructure, you want the machine to suggest and the person to decide. Here's the endpoint — `POST /approve` — and the response returns the decision and the running action plan."

---

## Slide 11 — Tech Stack

> "The stack is intentionally small — nine Python dependencies, that's the whole thing. **LangGraph** for orchestration, **FastAPI and Uvicorn** for the backend, **Streamlit** for the UI, **Pandas** for the data, **Pydantic** for validation, **Requests** for the HTTP calls, and two newcomers: **LangChain-OpenAI** — the OpenAI-compatible client that talks to OpenRouter — and **python-dotenv**, which loads the model and key config from `.env`. Just as deliberate are the things that aren't there — no cloud SDKs, no database, no authentication, no Docker, no native ML. The only external piece, the LLM API, is optional. That's what makes it beginner-friendly, and why it runs on any laptop with Python 3.10 or newer."

---

## Slide 12 — Run It

> "If you want to run this yourself, it's two commands. Terminal one: `uvicorn main:app --reload` — that's the API, with interactive docs at `localhost:8000/docs`. Terminal two: `streamlit run app.py` — the UI at `localhost:8501`. And if you want the LLM features, one extra step: copy `.env.example` to `.env` and drop in your OpenRouter API key — without it, everything still works on deterministic templates. Inside the UI there are five screens: a **dashboard** that runs the full analysis and shows total resources, opportunities, an executive summary, and potential savings; a **recommendations** table with every issue, action, savings estimate, and impact; an **approval screen** where you approve or reject; a **knowledge search** that queries the policy base directly; and a **chat** assistant that answers cloud-optimization questions and politely refuses anything off-topic. I'm happy to do a live demo after this if you'd like."

---

## Slide 13 — Takeaways

> "To wrap up the technical part — four takeaways. **One:** this is a real agentic pipeline, not a single hardcoded answer — eight nodes, one graph, state flowing end to end. **Two:** real RAG with a dependency-free vector index — real OpenRouter embeddings when you want them, pure-Python hashing fallback when you don't. **Three:** safe automation — the human approval gate sits between recommendation and action. **Four:** it runs anywhere, with mock data and no required external services — which made it the perfect platform to learn the agentic pattern."

---

## Slide 14 — Thank You

> "And that brings me to the end. Thank you for listening — I'm happy to take questions. To bring it full circle: **CloudOptima AI is an agentic, human-approved path from cloud signal to savings.**"

---

## Delivery tips

- Slide 8 and Slide 12 are the strongest "wow" moments — slow down on the numbers there.
- If time is tight, trim Slide 6 (the agents are summarized on Slide 5 anyway) — that buys about a minute.
- The Q&A slide (14) is a good place to jump into the live demo.
