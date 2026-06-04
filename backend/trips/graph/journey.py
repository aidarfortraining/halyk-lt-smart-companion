"""Graph assembly (ARCHITECTURE.md §5.3). The graph IS the product.

Linear for now: apply_answer → advance → generate. Conditional branches
(weather_branch, branch_housing, tracker, results) are added in later vehи.
"""
from langgraph.graph import END, START, StateGraph

from .nodes import n_advance, n_apply_answer, n_generate
from .state import RunState


def _build():
    g = StateGraph(RunState)
    g.add_node("apply_answer", n_apply_answer)
    g.add_node("advance", n_advance)
    g.add_node("generate", n_generate)
    g.add_edge(START, "apply_answer")
    g.add_edge("apply_answer", "advance")
    g.add_edge("advance", "generate")
    g.add_edge("generate", END)
    return g.compile()


GRAPH = _build()


def run(trip, action, chip_value=None):
    """Invoke one graph move. Trip is the source of truth; caller wraps this in a transaction."""
    GRAPH.invoke({"trip_id": trip.id, "action": action, "chip_value": chip_value})
    trip.refresh_from_db()
    return trip
