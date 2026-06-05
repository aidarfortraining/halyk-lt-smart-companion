from django.urls import path

from . import views

urlpatterns = [
    path("trip/start", views.trip_start, name="trip-start"),
    path("trip/reset", views.trip_reset, name="trip-reset"),
    path("trip/<int:pk>/state", views.trip_state, name="trip-state"),
    path("trip/<int:pk>/answer", views.trip_answer, name="trip-answer"),
    path("trip/<int:pk>/advance", views.trip_advance, name="trip-advance"),
]
