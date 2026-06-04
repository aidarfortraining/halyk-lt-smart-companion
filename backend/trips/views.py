from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Trip
from .serializers import build_snapshot


@api_view(["GET"])
def trip_state(request, pk):
    """Full snapshot for rendering / restoring the screen after a restart (ARCHITECTURE.md §6)."""
    trip = get_object_or_404(Trip, pk=pk)
    return Response(build_snapshot(trip))
