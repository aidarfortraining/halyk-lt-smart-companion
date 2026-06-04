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

# ── ФАЗА 1: Т−7 аптечка → Т−3 подготовка (дождевой сценарий, spec §4–5, §9) ──
# Budget: transfer и restaurant НЕ платятся сейчас (расчётное, реальный вызов в поездке);
# pharma/kino/market платятся → факт 89 000 → 105 000.
PHASE_1 = [
    Step(
        key="pharmacy", phase=1, plan_item="pharma",
        concern="Аптечку собрать — с детьми лучше заранее",
        ai_prompt=("За 7 дней до поездки. Семья с детьми 5 и 9 лет. В ночном поезде ~13 часов важно "
                   "средство от укачивания. Appteka привезёт готовый набор «Семья в дорогу» домой, "
                   "обычная доставка дешевле экспресса в поездке."),
        fallback=("За неделю до поездки соберём аптечку: в ночном поезде ~13 часов пригодится "
                  "средство от укачивания. Appteka привезёт готовый набор «Семья в дорогу» домой — "
                  "обычная доставка дешевле экспресса."),
        chips=[
            Chip(label="💊 Детская аптечка", sub="жаропонижающее, пластыри, от укачивания", value="kids",
                 plan_value="Детская аптечка · Appteka ✓", plan_tag="g",
                 budget_category="Аптечка", budget_fact=4500),
            Chip(label="🤧 Есть аллергики", sub="Appteka подберёт", value="allergy",
                 plan_value="Аптечка + антигистаминные ✓", plan_tag="g",
                 budget_category="Аптечка", budget_fact=4500),
            Chip(label="✓ Уже собрана", sub="пропустить", value="skip",
                 plan_value="Аптечка готова ✓", plan_tag="g"),
        ],
    ),
    Step(
        key="prep_entry", phase=1, silent=True,
        emits=[
            {"as": "time", "text": "📲 Уведомление · Пн 1 июня · 19:00 · за 3 дня до поездки"},
            {"as": "concern", "title": "Послезавтра в Астану — что с погодой и трансфером?",
             "sub": "В субботу {sat} — лучше выбрать крытые активности. Трансфер с вокзала ещё не выбран.",
             "hint": "Открываем подготовку к поездке"},
        ],
    ),
    Step(
        key="transfer", phase=1, plan_item="transfer",
        concern="Как с вокзала доедем? Дети, чемоданы",
        ai_prompt=("За 3 дня. Маршрут готов: вокзал Нурлы Жол → {hotel}, ~15 минут. В субботу дождь — "
                   "с детьми и чемоданами пешком неудобно, рекомендуй такси. inDrive не бронирует за "
                   "3 дня — в план добавим напоминание, реальный вызов в день приезда."),
        fallback=("Маршрут с вокзала готов: Нурлы Жол → {hotel}, ~15 минут. В дождь с детьми и "
                  "чемоданами лучше такси — добавим в план, вызовем в день приезда одним тапом."),
        chips=[
            Chip(label="🚖 Такси — комфорт", sub="~3 500 ₸ · напомним при прибытии", value="taxi",
                 plan_value="Такси · напомним при прибытии", plan_tag="g"),
            Chip(label="🚌 Общественный", sub="самостоятельно", value="public",
                 plan_value="Общественный транспорт", plan_tag="a"),
            Chip(label="🚗 Своя машина", sub="парковка у отеля", value="own",
                 plan_value="Своя машина", plan_tag="a"),
        ],
    ),
    Step(
        key="kino", phase=1, plan_item="kino",
        concern="Что делать с детьми в субботу? Дождь…",
        ai_prompt=("Суббота дождливая, {sat}. Дети 5 и 9 лет. Думан — крытый аттракционный комплекс, "
                   "в дождь идеально; билеты через Kino.kz без комиссии, +5% бонусов. Говори языком "
                   "тревоги «чем занять детей в дождь»."),
        fallback=("Суббота дождливая, {sat} — для детей 5 и 9 лет лучше крытое. Думан: крытый "
                  "аттракционный комплекс, билеты через Kino.kz без комиссии, +5% бонусов."),
        chips=[
            Chip(label="🎢 Думан — аттракционы", sub="крытый · в дождь идеально", value="duman",
                 plan_value="Думан · Kino.kz ✓", plan_tag="g",
                 budget_category="Развлечения", budget_fact=8000),
            Chip(label="🎬 IMAX", sub="без комиссии · Kino.kz", value="imax",
                 plan_value="Кино IMAX ✓", plan_tag="g",
                 budget_category="Развлечения", budget_fact=8000),
            Chip(label="🏛️ ЭКСПО · Нур-Алем", sub="музей будущего · крытый", value="expo",
                 plan_value="ЭКСПО · Нур-Алем ✓", plan_tag="g",
                 budget_category="Развлечения", budget_fact=8000),
            Chip(label="✕ Сами решим", sub="пропустить", value="skip",
                 plan_value="Без мероприятий", plan_tag="a"),
        ],
    ),
    Step(
        key="restaurant", phase=1, plan_item="resto",
        concern="Где поужинаем в пятницу? После ночного поезда готовить не хочется",
        ai_prompt=("Семья приедет в пятницу утром после ночного поезда — уставшая. Их мысль: где "
                   "поужинать, не искать на ходу. Halyk Рестораны: заведения рядом с {hotel} с детским "
                   "меню, можно забронировать столик на пятницу. Реальная оплата — на месте, в поездке."),
        fallback=("После ночного поезда ужин лучше не искать на ходу. Halyk Рестораны: заведения "
                  "рядом с {hotel} с детским меню — забронируем столик на пятницу."),
        chips=[
            Chip(label="🍽️ Подобрать рестораны рядом", sub="детское меню · бронь столика", value="book",
                 plan_value="Ресторан · бронь на пт ✓", plan_tag="g"),
            Chip(label="🛵 Доставка в номер", sub="навынос из ресторана", value="delivery",
                 plan_value="Доставка в номер ✓", plan_tag="g"),
            Chip(label="✕ Сами найдём", sub="пропустить", value="skip",
                 plan_value="Без рекомендаций", plan_tag="a"),
        ],
    ),
    # market_rain — НЕ plan-item: погодная экипировка, влияет только на бюджет (spec §5 погодный блок).
    Step(
        key="market_rain", phase=1,
        concern="Дождь в субботу — что надеть детям?",
        ai_prompt=("В субботу дождь {sat}. Система знает возраст детей — 5 и 9 лет. Предложи зонты и "
                   "детские дождевики через Halyk Market с доставкой до отеля, рассрочка 0-0-6. "
                   "Говори языком заботы о детях в дождь, не рекламы."),
        fallback=("В субботу дождь {sat}. Для детей 5 и 9 лет — зонты и дождевики через Halyk Market, "
                  "доставка до отеля, рассрочка 0-0-6."),
        chips=[
            Chip(label="🛍️ Зонты + куртки детям", sub="Halyk Market · доставка до отеля", value="market",
                 budget_category="Дождевики/зонты", budget_fact=3500),
            Chip(label="✕ Есть своё", sub="пропустить", value="skip"),
        ],
    ),
    Step(
        key="checklist_card", phase=1, silent=True,
        emits=[
            {"as": "time", "text": "✅ Финальный чеклист · день отъезда · Чт 4 июня"},
            {"as": "sys", "level": "ok",
             "text": "Всё собрано: билеты в Wallet, отель, документы, страховка, аптечка, Думан, "
                     "ресторан. Трансфер — напомним при прибытии. Бюджет: факт {fact} ₸ из ~{total} ₸."},
        ],
    ),
]


# phase → ordered steps. Phases 2–4 appended in later vehи.
PHASES: dict[int, list] = {
    0: PHASE_0,
    1: PHASE_1,
}

# Closing sys-notice emitted when a phase's steps are exhausted (await_user=false).
PHASE_END: dict[int, str] = {
    0: "Основное готово. За 7 дней напомним про аптечку, за 3 дня — трансфер и план на выходные.",
    1: "Всё готово к поездке. Увидимся в поезде — за 40 минут до Астаны напомню про такси.",
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
