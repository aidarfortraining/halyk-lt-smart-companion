"""Domain model — the single source of truth for run state (ARCHITECTURE.md §4).

LangGraph runs stateless on top of these tables; no LangGraph checkpointer.
State after a restart is fully described by Trip.phase + Trip.step_index + PlanItem
states + BudgetLine facts + the Message log.
"""
from django.db import models


class Trip(models.Model):
    """Root of one demo run (one Trip for the whole demo)."""

    route = models.CharField(max_length=120)
    transport = models.CharField(max_length=60)
    depart_at = models.DateTimeField()
    arrive_at = models.DateTimeField()
    pax = models.PositiveSmallIntegerField()
    kids = models.JSONField(default=list)          # [{"name": "Айша", "age": 9}, ...]
    hotel_name = models.CharField(max_length=120)
    hotel_address = models.CharField(max_length=200)
    is_apartments = models.BooleanField(default=False)  # demo = hotel-path (False)
    weather = models.JSONField(default=dict)        # {"fri": "...", "sat": "🌧 +14° дождь", "sun": "..."}
    emergency = models.JSONField(default=list)      # [{"label": "...", "value": "..."}, ...]
    address_pending = models.BooleanField(default=False)  # True after appart/booked → awaiting typed address
    phase = models.PositiveSmallIntegerField(default=0)   # 0..4
    step_index = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trip #{self.pk} · {self.route} · phase {self.phase}"


class PlanItem(models.Model):
    """One of exactly 10 Travel Plan rows (spec §7)."""

    LOCKED, WAIT, DONE = "locked", "wait", "done"
    STATE_CHOICES = [(LOCKED, "locked"), (WAIT, "wait"), (DONE, "done")]

    trip = models.ForeignKey(Trip, related_name="plan_items", on_delete=models.CASCADE)
    key = models.CharField(max_length=20)   # hotel/docs/insur/budget/pharma/transfer/kino/resto/airba/taxi
    order = models.PositiveSmallIntegerField()
    icon = models.CharField(max_length=8)
    service = models.CharField(max_length=80)
    phase = models.PositiveSmallIntegerField()
    state = models.CharField(max_length=8, choices=STATE_CHOICES, default=LOCKED)
    value = models.CharField(max_length=200, blank=True)
    tag = models.CharField(max_length=2, blank=True)   # "g" | "a" | ""
    badge = models.CharField(max_length=40, blank=True)

    class Meta:
        ordering = ["order"]
        constraints = [models.UniqueConstraint(fields=["trip", "key"], name="uniq_trip_planitem")]

    def __str__(self):
        return f"{self.key} [{self.state}]"


class Message(models.Model):
    """Chat feed entry — the history survives a restart."""

    AI, USER, TIME, CONCERN, SYS, RESULTS = "ai", "user", "time", "concern", "sys", "results"
    KIND_CHOICES = [(AI, "ai"), (USER, "user"), (TIME, "time"),
                    (CONCERN, "concern"), (SYS, "sys"), (RESULTS, "results")]

    trip = models.ForeignKey(Trip, related_name="messages", on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    text = models.TextField(blank=True)
    meta = models.JSONField(default=dict, blank=True)   # sys-notice level, concern title/sub/hint, etc.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"#{self.order} {self.kind}"


class BudgetLine(models.Model):
    """Cross-cutting budget. Detailed spec §3 lines; live budget and the Итоги table
    are derived from these (prepaid lines fold into 'Предоплата' at Итоги)."""

    PREPAID, VARIABLE = "prepaid", "variable"
    KIND_CHOICES = [(PREPAID, "prepaid"), (VARIABLE, "variable")]

    trip = models.ForeignKey(Trip, related_name="budget_lines", on_delete=models.CASCADE)
    category = models.CharField(max_length=60)
    plan_amount = models.PositiveIntegerField()
    fact_amount = models.PositiveIntegerField(null=True, blank=True)  # null until paid/reserved
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.category} {self.plan_amount}/{self.fact_amount}"
