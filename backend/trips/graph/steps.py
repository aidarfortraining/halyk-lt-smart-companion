"""Declarative journey — phases → steps → chips (ARCHITECTURE.md §5.2).

Ports the prototype's PHASES structure to the server, but content comes from the spec
(halyk_smart_travel_spec.md), NOT the prototype (see ARCHITECTURE.md §14).

Phase 0 here; phases 1–4 are appended in later vehи.
"""
from dataclasses import dataclass, field


@dataclass
class Chip:
    label: str
    value: str
    sub: str = ""
    plan_value: str = ""        # value written to the plan item when chosen
    plan_tag: str = ""          # "g" | "a" | ""
    budget_category: str = ""   # BudgetLine to mark as paid (fact)
    budget_fact: int = 0        # fact_amount to set (0 = no payment)
    is_apartments: bool = False


@dataclass
class Step:
    key: str
    phase: int
    silent: bool = False
    concern: str = ""           # client's thought — grounds the LLM message (Веха 7)
    ai_prompt: str = ""
    fallback: str = ""          # offline text (spec) — used until Веха 7
    plan_item: str = ""         # interactive: plan item this step completes
    chips: list = field(default_factory=list)
    # silent steps only:
    emits: list = field(default_factory=list)   # [{"as": "sys"/"time"/"concern", ...}]
    plan_value: str = ""        # silent: value template for plan_item (supports {total} etc.)
    plan_tag: str = ""


PHASE_0 = [
    Step(
        key="hotel", phase=0, plan_item="hotel",
        concern="Надо отель — на эти даты разберут быстро",
        ai_prompt=("Семья только что купила билеты. Первая мысль — отель. Тепло подтверди, что "
                   "билеты готовы, и спроси про жильё: на эти даты в Астане отели разбирают быстро, "
                   "через Halyk Homebank бронь Booking.com даёт +7% бонусов."),
        fallback=("Билеты оформлены — отлично! Теперь жильё: на эти даты в Астане отели разбирают "
                  "быстро. Забронируем через Booking.com — оплата картой Halyk, +7% бонусов."),
        chips=[
            Chip(label="🏨 Бронирую через Booking", sub="Halyk · +7% бонусов", value="booking",
                 plan_value="Booking.com · +7% бонусов ✓", plan_tag="g",
                 budget_category="Отель", budget_fact=48000),
            Chip(label="🏠 Апартаменты", sub="krisha.kz / ввод адреса", value="appart",
                 plan_value="Апартаменты · Airba Fresh активирован", plan_tag="g",
                 budget_category="Отель", budget_fact=35000, is_apartments=True),
            Chip(label="✓ Уже забронировал", sub="адрес добавлю позже", value="booked",
                 plan_value="Уже забронировано ✓", plan_tag="g",
                 budget_category="Отель", budget_fact=48000),
        ],
    ),
    Step(
        key="docs", phase=0, silent=True, plan_item="docs",
        emits=[
            {"as": "sys", "level": "ok",
             "text": "Цифровые документы детей (Айша, Тимур) в порядке — проводнику "
                     "показываются с телефона, бумажные брать не нужно."},
            {"as": "sys", "level": "warn",
             "text": "Удостоверение личности Алии истекает 28 июля 2026 — на июньскую поездку "
                     "не влияет, но лучше обновить заранее через eGov."},
        ],
        plan_value="Дети ✓ · Алия: удостоверение до 28.07 → eGov", plan_tag="a",
    ),
    Step(
        key="insurance", phase=0, plan_item="insur",
        concern="Страховка — надо, пока не забыл",
        ai_prompt=("Клиент выбрал жильё. Следующая мысль — страховка, пока не забыл. Данные семьи "
                   "уже заполнены автоматически, это 3 минуты. Говори языком заботы, не продажи."),
        fallback=("Пока не забыли — оформим страховку на семью. Данные уже заполнены, это займёт "
                  "3 минуты. Семейный тариф покрывает медицину и багаж."),
        chips=[
            Chip(label="🛡️ Базовая", sub="медицина · 1 500 ₸", value="base",
                 plan_value="Базовая · СК Халык ✓", plan_tag="g",
                 budget_category="Страховка", budget_fact=1500),
            Chip(label="🛡️ Семейная", sub="медицина + багаж · 3 000 ₸ · +20% бонусов", value="family",
                 plan_value="Семейный полис · СК Халык ✓", plan_tag="g",
                 budget_category="Страховка", budget_fact=3000),
            Chip(label="🛡️ Премиум", sub="всё включено · 5 000 ₸", value="premium",
                 plan_value="Премиум · СК Халык ✓", plan_tag="g",
                 budget_category="Страховка", budget_fact=5000),
        ],
    ),
    Step(
        key="budget", phase=0, silent=True, plan_item="budget",
        emits=[
            {"as": "sys", "level": "ok",
             "text": "Посчитали бюджет поездки: факт {fact} ₸ + расчётное {estimate} ₸ "
                     "= ~{total} ₸. Вся картина под контролем."},
        ],
        plan_value="~{total} ₸ · факт + расчётное", plan_tag="g",
    ),
]

# phase → ordered steps. Phases 1–4 appended in later vehи.
PHASES: dict[int, list] = {
    0: PHASE_0,
}

# Closing sys-notice emitted when a phase's steps are exhausted (await_user=false).
PHASE_END: dict[int, str] = {
    0: "Основное готово. За 7 дней напомним про аптечку, за 3 дня — трансфер и план на выходные.",
}


def active_chips_and_await(trip):
    """Derive current chips + await_user from steps (not persisted; ARCHITECTURE.md §4)."""
    steps = PHASES.get(trip.phase, [])
    idx = trip.step_index
    if idx < len(steps) and not steps[idx].silent:
        step = steps[idx]
        chips = [{"label": c.label, "sub": c.sub, "value": c.value} for c in step.chips]
        return chips, True
    return [], False
