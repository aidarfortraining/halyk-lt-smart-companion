"""LLM message generation (ARCHITECTURE.md §7).

Real claude-haiku-4-5 call via langchain-anthropic, wrapped in try/except + timeout → step.fallback.
Empty key or any error → fallback (rendered), so the whole journey still runs offline.
No streaming; Russian only; no markdown; 1–2 sentences.
"""
from django.conf import settings

from .context import text_ctx

_SYSTEM = (
    "Ты — AI-ассистент Halyk Travel. Говоришь языком тревоги и заботы клиента, "
    "не языком продажи сервисов.\n"
    "Поездка: {route}, {transport}, июнь, семья 4 человека (дети {kids}). "
    "Погода в Астане: пятница {fri}, суббота {sat}, воскресенье {sun}. Отель: {hotel}.\n"
    "Принцип: каждое сообщение отвечает на конкретную мысль-тревогу клиента — он чувствует "
    "заботу, не продажу.\n"
    "Только русский язык. Без markdown, без списков. Максимум 1–2 коротких предложения."
)


def _kids(trip):
    return ", ".join(f"{k.get('name', '')} {k.get('age', '')}".strip() for k in trip.kids)


def _extract(content):
    """Anthropic content may be a string or a list of blocks — return the text."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
        return "".join(parts).strip()
    return ""


def generate(step, trip):
    ctx = text_ctx(trip)
    fallback = step.fallback.format(**ctx)
    if not settings.ANTHROPIC_API_KEY or not step.ai_prompt:
        return fallback
    try:
        from langchain_anthropic import ChatAnthropic

        model = ChatAnthropic(
            model=settings.ANTHROPIC_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=200, temperature=0.7, timeout=20, max_retries=1,
        )
        system = _SYSTEM.format(route=trip.route, transport=trip.transport, kids=_kids(trip), **ctx)
        resp = model.invoke([("system", system), ("human", step.ai_prompt.format(**ctx))])
        return _extract(resp.content) or fallback
    except Exception:
        return fallback
