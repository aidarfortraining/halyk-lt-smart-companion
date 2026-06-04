from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .graph.journey import run
from .graph.steps import active_chips_and_await
from .models import PlanItem, Trip
from .seed import ensure_seed
from .serializers import build_snapshot


@api_view(["POST"])
def trip_start(request):
    """Idempotently seed the reference Trip and emit the first AI step (ARCHITECTURE.md §6)."""
    trip = ensure_seed()
    if not trip.messages.exists():   # run start only once; later calls just return state
        with transaction.atomic():
            run(trip, action="start")
    return Response(build_snapshot(trip))


@api_view(["GET"])
def trip_state(request, pk):
    """Full snapshot for rendering / restoring the screen after a restart (ARCHITECTURE.md §6)."""
    trip = get_object_or_404(Trip, pk=pk)
    return Response(build_snapshot(trip))


@api_view(["POST"])
def trip_answer(request, pk):
    """Commit the current step's chip, run silent steps, generate the next awaiting step.

    No-op (returns current snapshot) if the trip isn't awaiting input or the chip is unknown —
    guards against stray/duplicate answers drifting the step index.
    """
    trip = get_object_or_404(Trip, pk=pk)
    chip_value = request.data.get("chip_value")
    chips, awaiting = active_chips_and_await(trip)
    valid = awaiting and any(c["value"] == chip_value for c in chips)
    if valid:
        with transaction.atomic():
            run(trip, action="answer", chip_value=chip_value)
    return Response(build_snapshot(trip))


@api_view(["POST"])
def trip_advance(request, pk):
    """Simulation button: jump to the next phase, unlock its plan items, run its first step.

    No-op unless the current phase is closed (await_user False) and to_phase == phase + 1.
    """
    trip = get_object_or_404(Trip, pk=pk)
    try:
        to_phase = int(request.data.get("to_phase"))
    except (TypeError, ValueError):
        return Response(build_snapshot(trip))

    _, awaiting = active_chips_and_await(trip)
    if not awaiting and to_phase == trip.phase + 1 and 1 <= to_phase <= 4:
        with transaction.atomic():
            items = PlanItem.objects.filter(trip=trip, phase=to_phase, state=PlanItem.LOCKED)
            if not trip.is_apartments:
                items = items.exclude(key="airba")   # apartments-only — stays locked in hotel-path
            items.update(state=PlanItem.WAIT)
            trip.phase = to_phase
            trip.step_index = 0
            trip.save(update_fields=["phase", "step_index"])
            run(trip, action="advance")
    return Response(build_snapshot(trip))
