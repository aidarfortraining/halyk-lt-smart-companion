from django.urls import path

from . import views

# Веха 3 adds: trip/<id>/advance.
urlpatterns = [
    path("trip/start", views.trip_start, name="trip-start"),
    path("trip/<int:pk>/state", views.trip_state, name="trip-state"),
    path("trip/<int:pk>/answer", views.trip_answer, name="trip-answer"),
]
