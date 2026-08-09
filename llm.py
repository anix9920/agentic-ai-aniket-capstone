"""Shared LLM client - config from .env, graceful fallback to templates when no API key."""

import os

from dotenv import load_dotenv

load_dotenv()

_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
_api_key = os.getenv("OPENAI_API_KEY", "")


def llm_enabled() -> bool:
    """True when an API key is configured, so callers can skip LLM work offline."""
    return bool(_api_key)


def generate(system: str, user: str) -> str:
    """Run one chat completion and return the text. Raises on failure - callers decide the fallback."""
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model=_MODEL, temperature=_TEMPERATURE)
    response = llm.invoke([("system", system), ("human", user)])
    return response.content.strip()
