from django.core.management.base import BaseCommand

from trips.seed import ensure_seed


class Command(BaseCommand):
    help = "Idempotently seed the reference demo Trip (ARCHITECTURE.md §12)."

    def handle(self, *args, **options):
        trip = ensure_seed()
        # ASCII-only: Windows console (cp1252) can't encode the Cyrillic route.
        self.stdout.write(self.style.SUCCESS(f"Seed OK: Trip #{trip.pk}"))
