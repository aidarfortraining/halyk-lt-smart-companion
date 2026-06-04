"""Graph nodes (ARCHITECTURE.md §5.3). Named by stage so the graph reads as a journey map.

Stateless: each node reads the current state from Django, computes one move, writes back.
The view wraps the whole run in one transaction (atomicity without a persist accumulator).
"""
from ..models import BudgetLine, Message, PlanItem, Trip
from . import llm
from .steps import PHASE_END, PHASES


# ── helpers ──
def _fmt(n):
    return f"{n:,}".replace(",", " ")


def _next_order(trip):
    last = trip.messages.order_by("-order").first()
    return (last.order + 1) if last else 0


def _emit(trip, kind, text="", meta=None):
    Message.objects.create(trip=trip, order=_next_order(trip), kind=kind, text=text, meta=meta or {})


def _mark_plan(trip, key, value, tag="", state=PlanItem.DONE):
    PlanItem.objects.filter(trip=trip, key=key).update(state=state, value=value, tag=tag)


def _pay_budget(trip, category, fact):
    if category and fact:
        BudgetLine.objects.filter(trip=trip, category=category).update(fact_amount=fact)


def _budget_now(trip):
    lines = trip.budget_lines.all()
    fact = sum(l.fact_amount for l in lines if l.fact_amount is not None)
    estimate = sum(l.plan_amount for l in lines if l.fact_amount is None)
    return fact, estimate, fact + estimate


def _ctx(trip):
    """Render context for templated step text (weather, hotel, budget)."""
    fact, estimate, total = _budget_now(trip)
    return {
        "fact": _fmt(fact), "estimate": _fmt(estimate), "total": _fmt(total),
        "fri": trip.weather.get("fri", ""), "sat": trip.weather.get("sat", ""),
        "sun": trip.weather.get("sun", ""), "hotel": trip.hotel_name,
    }


def _run_silent(trip, step):
    """Emit a silent step's notices/cards and apply its plan mutation."""
    fmt = _ctx(trip)
    for e in step.emits:
        kind = e["as"]
        if kind == "sys":
            _emit(trip, "sys", e["text"].format(**fmt), {"level": e.get("level", "ok")})
        elif kind == "time":
            _emit(trip, "time", e["text"].format(**fmt))
        elif kind == "concern":
            _emit(trip, "concern", "", {"title": e.get("title", "").format(**fmt),
                                        "sub": e.get("sub", "").format(**fmt),
                                        "hint": e.get("hint", "").format(**fmt)})
    if step.plan_item:
        _mark_plan(trip, step.plan_item, step.plan_value.format(**fmt), step.plan_tag)


# ── nodes ──
def n_apply_answer(state):
    """action=answer: emit the user's chip and apply its plan/budget effects to the answered step."""
    if state["action"] != "answer":
        return {}
    trip = Trip.objects.get(pk=state["trip_id"])
    steps = PHASES.get(trip.phase, [])
    if trip.step_index >= len(steps):
        return {}
    step = steps[trip.step_index]
    chip = next((c for c in step.chips if c.value == state["chip_value"]), None)
    if chip is None:
        return {}
    _emit(trip, "user", chip.label)
    if step.plan_item:
        _mark_plan(trip, step.plan_item, chip.plan_value or step.plan_item, chip.plan_tag)
    _pay_budget(trip, chip.budget_category, chip.budget_fact)
    if chip.is_apartments and not trip.is_apartments:
        trip.is_apartments = True
        trip.save(update_fields=["is_apartments"])
    return {}


def n_advance(state):
    """Move to the next step and run leading silent steps; stop at the next interactive step / end."""
    trip = Trip.objects.get(pk=state["trip_id"])
    steps = PHASES.get(trip.phase, [])
    idx = trip.step_index + 1 if state["action"] == "answer" else trip.step_index
    while idx < len(steps) and steps[idx].silent:
        _run_silent(trip, steps[idx])
        idx += 1
    trip.step_index = min(idx, len(steps))   # clamp: never drift past the phase end
    trip.save(update_fields=["step_index"])
    return {}


def n_generate(state):
    """Present the awaiting interactive step (AI message), or close the phase if exhausted."""
    trip = Trip.objects.get(pk=state["trip_id"])
    steps = PHASES.get(trip.phase, [])
    idx = trip.step_index
    if idx < len(steps):
        _emit(trip, "ai", llm.generate(steps[idx], trip))
    else:
        closing = PHASE_END.get(trip.phase)
        if closing:
            _emit(trip, "sys", closing, {"level": "ok"})
    return {}
