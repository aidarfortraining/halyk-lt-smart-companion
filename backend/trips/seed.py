"""Idempotent seed of the reference scenario (ARCHITECTURE.md §12, content from spec).

Family Айдар/Алия/Айша(9)/Тимур(5), Алматы→Астана, night train ~13h,
depart Thu 4 June ~20:00 → arrive Fri 5 June ~09:00 (2026), hotel-path, rainy Saturday +14°.
Budget invariant: fact 38 000 / estimate 137 000 / total 175 000 at seed (see §9).
"""
import datetime

from django.utils import timezone

from .models import BudgetLine, PlanItem, Trip

DEPART_AT = datetime.datetime(2026, 6, 4, 20, 0)   # Thu 4 June, evening
ARRIVE_AT = datetime.datetime(2026, 6, 5, 9, 0)    # Fri 5 June, morning

# 10 Travel Plan items (spec §7). Phase 0 → wait, phases 1–2 → locked.
PLAN_ITEMS = [
    dict(key="hotel",    order=0, icon="🏨", service="Жильё · Booking",        phase=0, state=PlanItem.WAIT,   value="ожидаем…"),
    dict(key="docs",     order=1, icon="📋", service="Документы · 66 госуслуг", phase=0, state=PlanItem.WAIT,   value="проверяем…"),
    dict(key="insur",    order=2, icon="🛡️", service="Страховка · СК Халык",    phase=0, state=PlanItem.WAIT,   value="ожидаем…"),
    dict(key="budget",   order=3, icon="💰", service="Бюджет поездки",          phase=0, state=PlanItem.WAIT,   value="считаем…"),
    dict(key="pharma",   order=4, icon="💊", service="Аптечка · Appteka",       phase=1, state=PlanItem.LOCKED, value="за 7 дней до поездки"),
    dict(key="transfer", order=5, icon="🚖", service="Трансфер · inDrive",      phase=1, state=PlanItem.LOCKED, value="за 3 дня до поездки"),
    dict(key="kino",     order=6, icon="🎬", service="Развлечения · Kino.kz",   phase=1, state=PlanItem.LOCKED, value="за 3 дня до поездки"),
    dict(key="resto",    order=7, icon="🍽️", service="Рестораны · Halyk",       phase=1, state=PlanItem.LOCKED, value="за 3 дня до поездки"),
    dict(key="airba",    order=8, icon="🛒", service="Продукты · Airba Fresh",  phase=2, state=PlanItem.LOCKED, value="в поезде за 40 мин до Астаны"),
    dict(key="taxi",     order=9, icon="🚖", service="Такси с вокзала",         phase=2, state=PlanItem.LOCKED, value="при прибытии"),
]

# Detailed budget lines (spec §3). fact_amount=None → still "расчётное".
# prepaid → folds into "Предоплата" at Итоги; variable → own Итоги rows.
BUDGET_LINES = [
    dict(category="Билеты ЖД",        plan_amount=38000, fact_amount=38000, kind=BudgetLine.PREPAID,  order=0),
    dict(category="Отель",            plan_amount=48000, fact_amount=None,  kind=BudgetLine.PREPAID,  order=1),
    dict(category="Страховка",        plan_amount=3000,  fact_amount=None,  kind=BudgetLine.PREPAID,  order=2),
    dict(category="Аптечка",          plan_amount=4500,  fact_amount=None,  kind=BudgetLine.PREPAID,  order=3),
    dict(category="Развлечения",      plan_amount=8000,  fact_amount=None,  kind=BudgetLine.PREPAID,  order=4),
    dict(category="Дождевики/зонты",  plan_amount=3500,  fact_amount=None,  kind=BudgetLine.PREPAID,  order=5),
    dict(category="Трансфер",         plan_amount=14000, fact_amount=None,  kind=BudgetLine.VARIABLE, order=6),
    dict(category="Питание",          plan_amount=36000, fact_amount=None,  kind=BudgetLine.VARIABLE, order=7),
    dict(category="Сувениры",         plan_amount=10000, fact_amount=None,  kind=BudgetLine.VARIABLE, order=8),
    dict(category="Непредвиденное",   plan_amount=10000, fact_amount=None,  kind=BudgetLine.VARIABLE, order=9),
]

EMERGENCY = [
    {"label": "Appteka — срочная доставка", "value": "17 минут · от 5 000 ₸ бесплатно"},
    {"label": "Ближайшая детская больница", "value": "адрес и телефон в приложении"},
    {"label": "Ассистанс СК Халык",         "value": "24/7 · по полису"},
]

WEATHER = {"fri": "☀️ +18°", "sat": "🌧 +14° дождь", "sun": "⛅ +20°"}


def ensure_seed():
    """Return the single demo Trip, creating it (with plan + budget) on first call."""
    trip = Trip.objects.first()
    if trip is not None:
        return trip

    trip = Trip.objects.create(
        route="Алматы → Астана",
        transport="ночной поезд (~13 ч)",
        depart_at=timezone.make_aware(DEPART_AT),
        arrive_at=timezone.make_aware(ARRIVE_AT),
        pax=4,
        kids=[{"name": "Айша", "age": 9}, {"name": "Тимур", "age": 5}],
        hotel_name="Holiday Inn Астана",
        hotel_address="пр. Кабанбай батыра, Астана",
        is_apartments=False,
        weather=WEATHER,
        emergency=EMERGENCY,
        phase=0,
        step_index=0,
    )
    PlanItem.objects.bulk_create([PlanItem(trip=trip, **row) for row in PLAN_ITEMS])
    BudgetLine.objects.bulk_create([BudgetLine(trip=trip, **row) for row in BUDGET_LINES])
    return trip
