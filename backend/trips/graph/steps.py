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
    requires_apartments: bool = False   # step active only on the apartments branch (skipped in demo)
    chips: list = field(default_factory=list)
    # silent steps only:
    emits: list = field(default_factory=list)   # [{"as": "sys"/"time"/"concern", ...}]
    tx: list = field(default_factory=list)      # [(budget_category, amount)] — additive transactions
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


# ── ФАЗА 2: в поезде, утро прибытия (spec §4 этап 7, §7). Branch_housing: hotel → airba skip ──
PHASE_2 = [
    Step(
        key="train_entry", phase=2, silent=True,
        emits=[
            {"as": "time", "text": "📲 Уведомление · Пт 5 июня · ~08:50 · В поезде"},
            {"as": "concern", "title": "Через 10 минут — Астана",
             "sub": "Отель {hotel} уже ждёт. Сейчас удобно вызвать такси — маршрут готов.",
             "hint": "Выберите действие"},
        ],
    ),
    # airba — только апарт-ветка; в hotel-path пропускается (остаётся locked).
    Step(
        key="airba", phase=2, plan_item="airba", requires_apartments=True,
        concern="Продукты к приезду — с детьми в магазин с чемоданами неудобно",
        ai_prompt=("Семья едет в апартаменты, через 40 минут Астана. Airba Fresh доставит продукты "
                   "к приезду, пока они едут — с детьми и чемоданами в магазин неудобно."),
        fallback=("Через 40 минут Астана. Airba Fresh успеет доставить продукты к приезду — "
                  "с детьми и чемоданами по магазинам неудобно."),
        chips=[
            Chip(label="🛒 Заказать через Airba Fresh", sub="доставка к приезду", value="airba",
                 plan_value="Продукты · Airba Fresh ✓", plan_tag="g"),
            Chip(label="✕ Сами купим", sub="пропустить", value="skip",
                 plan_value="Продукты самостоятельно", plan_tag="a"),
        ],
    ),
    Step(
        key="taxi_arrival", phase=2, plan_item="taxi",
        concern="Стоять в проходе с детьми и чемоданами — нужно такси сразу",
        ai_prompt=("Через 10 минут Астана. Маршрут готов: вокзал Нурлы Жол → {hotel}. Один тап — "
                   "и такси уже едет. Говори коротко: клиент стоит в проходе с детьми и чемоданами."),
        fallback=("Через 10 минут Астана. Маршрут готов: вокзал Нурлы Жол → {hotel}. "
                  "Один тап — и такси уже едет."),
        chips=[
            Chip(label="🚖 Вызвать такси", sub="Вокзал → {hotel} · ~3 500 ₸", value="taxi",
                 plan_value="Такси с вокзала ✓", plan_tag="g"),
            Chip(label="✕ Сами доберёмся", sub="пропустить", value="skip",
                 plan_value="Самостоятельно", plan_tag="a"),
        ],
    ),
]


# ── ФАЗА 3: в поездке, Этап 8 (spec §8). Живой трекер: переменные категории накапливаются
# транзакциями → факт 105 000 → 169 500. Трансфер 3500+4000+4000, Питание 12200+14000+12000,
# Сувениры 10300, Непредвиденное 4500. #13 (перерасход) вычислимо; #14 (экономия) — нота в wrapup.
PHASE_3 = [
    Step(
        key="tracker_entry", phase=3, silent=True,
        emits=[
            {"as": "time", "text": "🏁 Пятница 5 июня · Астана · вы на месте"},
            {"as": "sys", "level": "ok",
             "text": "Трекер расходов запущен — платежи картой Halyk сами попадут в бюджет. "
                     "Экстренная помощь (Appteka 17 мин, детская больница, ассистанс 24/7) — в плане."},
        ],
        tx=[("Трансфер", 3500)],   # такси с вокзала (вызвано в фазе 2, списывается сейчас)
    ),
    Step(
        key="resto_reminder", phase=3, silent=True,
        emits=[{"as": "sys", "level": "ok",
                "text": "🍽️ Ресторан: столик в 20:00, 12 минут пешком от {hotel}. Приятного вечера!"}],
        tx=[("Питание", 12200)],   # ужин пятницы
    ),
    Step(
        key="duman_morning", phase=3, silent=True,
        emits=[{"as": "sys", "level": "ok",
                "text": "☔ Суббота: Думан в 11:00. На улице {sat} — возьмите детям куртки."}],
        tx=[("Питание", 14000), ("Непредвиденное", 4500)],   # день в Думане: еда + мелочи
    ),
    Step(
        key="duman_taxi", phase=3,
        concern="Через 30 минут Думан, на улице дождь и пробки",
        ai_prompt=("Суббота 10:30, до Думана 30 минут, дождь и пробки. Предложи вызвать такси одним "
                   "тапом — с детьми в дождь пешком неудобно."),
        fallback=("До Думана ~30 минут, на улице дождь и пробки. Вызвать такси? С детьми так удобнее."),
        chips=[
            Chip(label="🚖 Вызвать такси", sub="пробки · ~4 000 ₸", value="taxi",
                 budget_category="Трансфер", budget_fact=4000),
            Chip(label="🚶 Дойдём сами", sub="пропустить", value="skip"),
        ],
    ),
    Step(
        key="souvenirs", phase=3,
        concern="Что привезти домой? Последний день",
        ai_prompt=("Воскресенье, последний день в Астане. Предложи сувениры — сладости Рахат, шоколад "
                   "Баян Сулу через Halyk Market с доставкой к отелю. Говори тепло, не рекламно."),
        fallback=("Последний день в Астане — что привезти домой? Сладости Рахат и шоколад Баян Сулу "
                  "через Halyk Market, доставят прямо к {hotel}."),
        chips=[
            Chip(label="🛍️ Сувениры — Рахат, Баян Сулу", sub="Halyk Market · доставка к отелю", value="buy",
                 budget_category="Сувениры", budget_fact=10300),
            Chip(label="✕ Без сувениров", sub="пропустить", value="skip"),
        ],
    ),
    Step(
        key="sunday_plan", phase=3, silent=True,
        emits=[{"as": "sys", "level": "ok",
                "text": "🕒 Воскресенье 15:00 — до поезда ~5 часов. Успеваете на ЭКСПО или прогулку."}],
        tx=[("Питание", 12000)],   # питание воскресенья → Питание превышает план (нота #13)
    ),
    Step(
        key="station_taxi", phase=3,
        concern="Пора выдвигаться на вокзал",
        ai_prompt=("Воскресенье 19:00 — пора на вокзал к ночному поезду. Предложи вызвать такси "
                   "отель → вокзал одним тапом."),
        fallback=("Воскресенье 19:00 — пора на вокзал. Вызвать такси {hotel} → вокзал Нурлы Жол?"),
        chips=[
            Chip(label="🚖 Такси на вокзал", sub="~4 000 ₸", value="taxi",
                 budget_category="Трансфер", budget_fact=4000),
            Chip(label="✕ Сами доберёмся", sub="пропустить", value="skip"),
        ],
    ),
    Step(
        key="trip_wrapup", phase=3, silent=True,
        emits=[{"as": "sys", "level": "ok",
                "text": "✓ Трансфер вышел дешевле плана на 2 500 ₸, буфер почти не тронут — "
                        "поездка идёт с экономией. Факт {fact} ₸."}],
    ),
]


# ── ФАЗА 4: Итоги + Flywheel, Этап 10 (spec §10). Таблица план/факт собирается из BudgetLine
# в serializers.build_results; здесь — сопроводительное сообщение и чипсы следующей поездки.
FLYWHEEL = [
    {"emoji": "🏞️", "label": "Бурабай", "sub": "2 дня · озёра и скалы", "price": "от 45 000 ₸", "value": "burabay"},
    {"emoji": "🌊", "label": "Алаколь", "sub": "3 дня · пляжный отдых",  "price": "от 60 000 ₸", "value": "alakol"},
    {"emoji": "🏛️", "label": "Шымкент", "sub": "2 дня · юг и история",   "price": "от 40 000 ₸", "value": "shymkent"},
]

PHASE_4 = [
    Step(
        key="results", phase=4,
        concern="Сколько вышло в итоге?",
        ai_prompt=("Поездка завершена. Тепло подведи итог: уложились в бюджет — план 175 000, факт "
                   "169 500, на 5 500 меньше. Бонусы Halyk+ начислены, категория повышена. Спроси, "
                   "куда поедем дальше."),
        fallback=("Астана позади — поездка прошла отлично! Уложились в бюджет: план 175 000 ₸, факт "
                  "169 500 ₸ — на 5 500 ₸ меньше. Бонусы Halyk+ начислены, категория повышена. "
                  "Куда поедем дальше?"),
        chips=[Chip(label=f"{f['emoji']} {f['label']}", sub=f["price"], value=f["value"])
               for f in FLYWHEEL],
    ),
]


# phase → ordered steps.
PHASES: dict[int, list] = {
    0: PHASE_0,
    1: PHASE_1,
    2: PHASE_2,
    3: PHASE_3,
    4: PHASE_4,
}

# Closing sys-notice emitted when a phase's steps are exhausted (await_user=false).
PHASE_END: dict[int, str] = {
    0: "Основное готово. За 7 дней напомним про аптечку, за 3 дня — трансфер и план на выходные.",
    1: "Всё готово к поездке. Увидимся в поезде — за 40 минут до Астаны напомню про такси.",
    2: "Вы в Астане! Дальше — живой трекер бюджета, напоминания и экстренная помощь под рукой.",
    3: "Поездка завершена! Готовы Итоги план/факт и бонусы Halyk+.",
    4: "Halyk Travel открыт с поиском — бонусы применятся к следующей покупке. Хорошей дороги! 👋",
}


def _step_active(trip, step):
    """A step is inactive if it needs the apartments branch and we're hotel-path (demo)."""
    return not step.requires_apartments or trip.is_apartments


def active_chips_and_await(trip):
    """Derive current chips + await_user from steps (not persisted; ARCHITECTURE.md §4)."""
    from .context import text_ctx

    steps = PHASES.get(trip.phase, [])
    idx = trip.step_index
    if idx < len(steps) and not steps[idx].silent and _step_active(trip, steps[idx]):
        ctx = text_ctx(trip)
        chips = [{"label": c.label.format(**ctx), "sub": c.sub.format(**ctx), "value": c.value}
                 for c in steps[idx].chips]
        return chips, True
    return [], False
