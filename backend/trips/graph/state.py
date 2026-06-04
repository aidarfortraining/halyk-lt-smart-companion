"""Transient run state for one graph invocation (ARCHITECTURE.md §5.1).

The durable state lives in Django (Trip.phase + Trip.step_index + PlanItem/BudgetLine/Message).
This TypedDict only carries the inputs of a single move; nodes read/write Django directly
and the view wraps the whole run in one transaction.
"""
from typing import Optional, TypedDict


class RunState(TypedDict):
    trip_id: int
    action: str               # "start" | "answer" | "advance"
    chip_value: Optional[str]
