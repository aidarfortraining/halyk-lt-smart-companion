"""LLM message generation (ARCHITECTURE.md §7).

Веха 7 swaps the body for a real claude-haiku-4-5 call (LangChain + langchain-anthropic)
wrapped in try/except + timeout → step.fallback. Until then, generation IS the fallback
(with placeholders rendered), so the whole journey already runs offline.
"""
from .context import text_ctx


def generate(step, trip):
    return step.fallback.format(**text_ctx(trip))
