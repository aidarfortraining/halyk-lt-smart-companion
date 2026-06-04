"""Render context for templated step/chip text (weather, hotel, budget).

Shared by nodes (silent emits, budget), llm (fallback text), and steps (chip labels),
so placeholders like {hotel}/{sat}/{total} resolve everywhere.
"""


def fmt_money(n):
    return f"{n:,}".replace(",", " ")


def budget_now(trip):
    lines = trip.budget_lines.all()
    fact = sum(l.fact_amount for l in lines if l.fact_amount is not None)
    estimate = sum(l.plan_amount for l in lines if l.fact_amount is None)
    return fact, estimate, fact + estimate


def text_ctx(trip):
    """Weather + hotel placeholders for message/chip text."""
    return {
        "fri": trip.weather.get("fri", ""), "sat": trip.weather.get("sat", ""),
        "sun": trip.weather.get("sun", ""), "hotel": trip.hotel_name,
    }


def full_ctx(trip):
    """text_ctx + formatted budget (for silent-step notices/cards)."""
    fact, estimate, total = budget_now(trip)
    return {**text_ctx(trip),
            "fact": fmt_money(fact), "estimate": fmt_money(estimate), "total": fmt_money(total)}
