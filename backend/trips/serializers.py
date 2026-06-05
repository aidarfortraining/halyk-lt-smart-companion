"""Snapshot serialization (ARCHITECTURE.md §6). Every API response is one full
render snapshot for the frontend, which replaces its state wholesale."""
from rest_framework import serializers

from .graph.context import budget_now
from .graph.steps import FLYWHEEL, active_chips_and_await, active_step
from .models import BudgetLine, Message, PlanItem, Trip


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = ["id", "route", "transport", "depart_at", "arrive_at", "pax", "kids",
                  "hotel_name", "hotel_address", "is_apartments", "weather",
                  "phase", "step_index"]


class PlanItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanItem
        fields = ["key", "order", "icon", "service", "phase", "state", "value", "tag", "badge"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["order", "kind", "text", "meta"]


class BudgetLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetLine
        fields = ["category", "plan_amount", "fact_amount", "kind", "order"]


def build_budget(trip):
    """Live budget derived from BudgetLine: fact = Σ paid, estimate = Σ unpaid plan."""
    fact, estimate, total = budget_now(trip)
    return {
        "fact": fact,
        "estimate": estimate,
        "total": total,
        "lines": BudgetLineSerializer(trip.budget_lines.all(), many=True).data,
    }


def build_results(trip):
    """Итоги table (spec §10) from BudgetLine: prepaid lines fold into 'Предоплата',
    variable lines are their own rows. Returns None unless the trip reached phase 4."""
    if trip.phase < 4:
        return None
    lines = list(trip.budget_lines.all())
    prepaid = [l for l in lines if l.kind == BudgetLine.PREPAID]
    rows = [{
        "category": "Предоплата",
        "plan": sum(l.plan_amount for l in prepaid),
        "fact": sum((l.fact_amount or 0) for l in prepaid),
    }]
    rows += [{"category": l.category, "plan": l.plan_amount, "fact": l.fact_amount or 0}
             for l in lines if l.kind == BudgetLine.VARIABLE]
    for r in rows:
        r["delta"] = r["fact"] - r["plan"]
    total_plan = sum(l.plan_amount for l in lines)
    total_fact = sum((l.fact_amount or 0) for l in lines)
    return {
        "rows": rows,
        "totals": {"plan": total_plan, "fact": total_fact, "delta": total_fact - total_plan},
        "bonuses": {"earned": 8500, "tier": "повышена",
                    "note": "Категория клиента повышена — выше кешбэк в следующем месяце."},
        "flywheel": FLYWHEEL,
    }


def build_snapshot(trip):
    """Full render snapshot. chips/await_user/results are derived from state (not persisted)."""
    chips, await_user = active_chips_and_await(trip)
    step = active_step(trip)
    return {
        "trip": TripSerializer(trip).data,
        "plan": PlanItemSerializer(trip.plan_items.all(), many=True).data,
        "messages": MessageSerializer(trip.messages.all(), many=True).data,
        "budget": build_budget(trip),
        "emergency": trip.emergency,
        "phase": trip.phase,
        "chips": chips,
        "await_user": await_user,
        "input_hint": step.input_hint if (step and step.text_input) else "",
        "results": build_results(trip),
    }
