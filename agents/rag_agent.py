"""RAG Agent - Knowledge base retrieval.

Pure-Python in-memory vector store. Uses a small hashing embedding function instead of
ChromaDB, whose native Rust/SQLite/HNSW backend crashes the process on some Windows setups
(and ONNX Runtime, its default embedder, needs a native DLL that isn't always available).
"""

import hashlib
import math
import re
from pathlib import Path
from typing import List, Dict

from llm import embed, embedding_model, llm_enabled

_VECTOR_DIM = 256
_WORD_RE = re.compile(r"[a-z0-9]+")


class HashingEmbeddingFunction:
    """Deterministic bag-of-words embedding via the hashing trick. No ML model, no native deps."""

    def __call__(self, input: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in input]

    def _embed(self, text: str) -> List[float]:
        vec = [0.0] * _VECTOR_DIM
        words = _WORD_RE.findall(text.lower())
        for word in words:
            idx = int(hashlib.md5(word.encode()).hexdigest(), 16) % _VECTOR_DIM
            vec[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def name(self) -> str:
        return "hashing-bow-256"


class OpenRouterEmbeddingFunction:
    """Real embeddings via OpenRouter (/embeddings endpoint). Silently falls back to hashing per batch on any API failure."""

    def __init__(self):
        self._fallback = HashingEmbeddingFunction()

    def __call__(self, input: List[str]) -> List[List[float]]:
        try:
            return embed(input)
        except Exception:
            return self._fallback(input)

    def name(self) -> str:
        return embedding_model


class RAGAgent:
    """Agent responsible for knowledge base retrieval.

    Loads data/knowledge/*.txt into an in-memory index at startup and answers queries by
    cosine similarity over the hashing embeddings. Distances use ChromaDB's convention
    (distance = 1 - cosine similarity) so callers see the same shape as before.
    """

    def __init__(self, knowledge_dir: str = None, embedding_function=None):
        base_dir = Path(__file__).resolve().parent.parent
        self.knowledge_dir = Path(knowledge_dir) if knowledge_dir else base_dir / "data" / "knowledge"
        self.embedding_function = embedding_function or (
            OpenRouterEmbeddingFunction() if llm_enabled() else HashingEmbeddingFunction()
        )
        self._docs: List[Dict] = []
        self.load_documents()

    def load_documents(self):
        """Chunk every knowledge .txt file and embed all chunks in one batch (one API call when using real embeddings)."""
        chunks: List[str] = []
        ids, sources = [], []
        for file_path in sorted(self.knowledge_dir.glob("*.txt")):
            content = file_path.read_text()
            for i, chunk in enumerate(self._chunk_text(content, chunk_size=500, overlap=50)):
                chunks.append(chunk)
                ids.append(f"{file_path.stem}_{i}")
                sources.append(file_path.name)

        vectors = self.embedding_function(chunks) if chunks else []
        for doc_id, chunk, source, vector in zip(ids, chunks, sources, vectors):
            self._docs.append({
                "id": doc_id,
                "content": chunk,
                "source": source,
                "vector": vector,
            })

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks

    def query(self, question: str, n_results: int = 3) -> List[Dict]:
        """Query the knowledge base. Returns top matches with content/source/distance."""
        if not self._docs:
            return []
        query_vector = self.embedding_function([question])[0]
        key = lambda d: self._distance(query_vector, d["vector"])
        return [
            {"content": d["content"], "source": d["source"], "distance": key(d)}
            for d in sorted(self._docs, key=key)[:n_results]
        ]

    def _distance(self, a: List[float], b: List[float]) -> float:
        """1 - cosine similarity; vectors are L2-normalized so cosine is just the dot product."""
        return 1.0 - sum(x * y for x, y in zip(a, b))

    def get_context_for_query(self, question: str) -> str:
        """Get relevant context as formatted string for LLM"""
        if not self._docs:
            return "No relevant knowledge found."
        query_vector = self.embedding_function([question])[0]
        return self._format_context(self._top_matches(query_vector))

    def get_contexts_for_queries(self, questions: List[str]) -> List[str]:
        """Embed all questions in one batch call; return formatted context per question."""
        if not self._docs:
            return ["No relevant knowledge found."] * len(questions)
        if not questions:
            return []
        query_vectors = self.embedding_function(list(questions))
        return [self._format_context(self._top_matches(qv)) for qv in query_vectors]

    def _top_matches(self, query_vector, n_results: int = 3) -> List[Dict]:
        key = lambda d: self._distance(query_vector, d["vector"])
        return sorted(self._docs, key=key)[:n_results]

    def _format_context(self, results: List[Dict]) -> str:
        context_parts = [f"[Source: {r['source']}]\n{r['content']}" for r in results]
        return "\n\n---\n\n".join(context_parts) if context_parts else "No relevant knowledge found."
