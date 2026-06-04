from django.urls import path

from . import views

# Веха 2–3 add: trip/start, trip/<id>/answer, trip/<id>/advance.
urlpatterns = [
    path("trip/<int:pk>/state", views.trip_state, name="trip-state"),
]
