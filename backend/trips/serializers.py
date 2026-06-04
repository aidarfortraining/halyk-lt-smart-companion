"""Snapshot serialization (ARCHITECTURE.md §6). Every API response is one full
render snapshot for the frontend, which replaces its state wholesale."""
from rest_framework import serializers

from .graph.context import budget_now
from .graph.steps import active_chips_and_await
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


def build_snapshot(trip, *, results=None):
    """Full render snapshot. chips/await_user are derived from steps (not persisted)."""
    chips, await_user = active_chips_and_await(trip)
    return {
        "trip": TripSerializer(trip).data,
        "plan": PlanItemSerializer(trip.plan_items.all(), many=True).data,
        "messages": MessageSerializer(trip.messages.all(), many=True).data,
        "budget": build_budget(trip),
        "emergency": trip.emergency,
        "phase": trip.phase,
        "chips": chips,
        "await_user": await_user,
        "results": results,
    }
