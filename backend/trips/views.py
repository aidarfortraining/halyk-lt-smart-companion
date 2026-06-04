from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .graph.journey import run
from .models import Trip
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
    """Commit the current step's chip, run silent steps, generate the next awaiting step."""
    trip = get_object_or_404(Trip, pk=pk)
    chip_value = request.data.get("chip_value")
    with transaction.atomic():
        run(trip, action="answer", chip_value=chip_value)
    return Response(build_snapshot(trip))
