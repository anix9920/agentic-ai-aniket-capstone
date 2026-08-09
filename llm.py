"""Shared LLM client - OpenRouter (OpenAI-compatible) via .env, graceful fallback to templates when no API key."""

import os

from dotenv import load_dotenv

load_dotenv()

_api_key = os.getenv("OPENROUTER_API_KEY", "")
_base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
_model = os.getenv("MODEL", "meta-llama/llama-3.1-8b-instruct")
embedding_model = os.getenv("EMBEDDING_MODEL") or os.getenv("OPENROUTER_EMBEDDING_MODEL") or "openai/text-embedding-3-small"
_temperature = float(os.getenv("TEMPERATURE", "0.2"))


def llm_enabled() -> bool:
    """True when an API key is configured, so callers can skip LLM work offline."""
    return bool(_api_key)


def generate(system: str, user: str) -> str:
    """Run one chat completion and return the text. Raises on failure - callers decide the fallback."""
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model=_model, temperature=_temperature, api_key=_api_key, base_url=_base_url)
    response = llm.invoke([("system", system), ("human", user)])
    return response.content.strip()


def embed(texts) -> list[list[float]]:
    """Embed a batch of texts via OpenRouter's /embeddings endpoint. Raises on failure."""
    from langchain_openai import OpenAIEmbeddings

    embeddings = OpenAIEmbeddings(model=embedding_model, api_key=_api_key, base_url=_base_url)
    return embeddings.embed_documents(list(texts))
