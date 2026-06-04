"""LLM message generation (ARCHITECTURE.md §7).

Веха 7 swaps the body for a real claude-haiku-4-5 call (LangChain + langchain-anthropic)
wrapped in try/except + timeout → step.fallback. Until then, generation IS the fallback,
so the whole journey already runs offline.
"""


def generate(step, trip):
    return step.fallback
