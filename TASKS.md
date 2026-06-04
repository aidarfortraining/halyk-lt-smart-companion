# TASKS.md — исполняемый чеклист сборки

> **Что это.** Пошаговый план сборки Halyk Smart Travel Companion, развёрнутый из
> `ARCHITECTURE.md §13` (9 вех) в конкретные задачи с файлами и критериями проверки.
> **Источники правды:** как строить → `ARCHITECTURE.md`; контент/даты/тексты →
> `halyk_smart_travel_spec.md`; внешний вид → `prototype.html` (V2-стили, строки 328–477).
> Этот файл — живой: отмечаем `[x]` по мере выполнения, правим при расхождениях.

## Рабочие соглашения

- **Темп:** по вехам с чекпоинтами — после каждой вехи показываю результат + проверку, жду ОК.
- **Dev локально** (Docker — только веха 9):
  - Backend: `python -m venv .venv` → `.venv\Scripts\activate` → `pip install -r backend/requirements.txt`
    → `python backend/manage.py migrate` → `python backend/manage.py runserver` (порт 8000).
  - Frontend: `cd frontend` → `npm install` → `npm run dev` (Vite, прокси `/api` → `:8000`).
- **Тулчейн (проверено):** Node 24 / npm 11, Docker 29 + Compose v2.40, Python 3.11 локально
  (образ зафиксирует 3.12). Django 5 / langgraph совместимы с 3.11.
- **LLM:** код под живой `claude-haiku-4-5` + `try/except`→`fallback`. Ключ в `.env` (gitignored).
- **Проверка каждой вехи** — явный критерий ниже. Не идём дальше, пока критерий не зелёный.

---

## Веха 0 — Каркас репозитория и dev-окружение ✅

- [x] `backend/requirements.txt` (Django 5.2.15, DRF 3.17.1, langgraph 1.2.4, langchain-anthropic
      1.4.4, whitenoise 6.12.0, gunicorn 23, python-dotenv 1.2.2, pytest-django 4.11.1).
- [x] `backend/manage.py`, `backend/config/` (settings, urls, wsgi, asgi). SQLite на файле (путь
      override через `SQLITE_PATH` для Docker-volume), DRF, WhiteNoise, чтение `.env` через dotenv.
- [x] `frontend/` — Vite 8 + React 18 + TS скелет; `vite.config.ts` с прокси `/api`→`:8000` на dev и
      `build.outDir → backend/frontend_dist` для прод.
- [x] `.venv` (Python 3.11), зависимости установлены; `migrate` применён; `.gitignore` дополнен.
- **Проверка:** ✅ `manage.py check` без ошибок; `runserver` отдал HTTP 200 на `/admin/login/`;
      `npm run build` прошёл (бандл React 18 → `backend/frontend_dist`).

---

## Веха 1 — Доменная модель и снапшот (ARCHITECTURE §4, §6, §12) ✅

- [x] `trips/models.py`: `Trip`, `PlanItem` (10 шт.), `Message`, `BudgetLine` — поля строго по §4.
- [x] Миграция `0001_initial` применена.
- [x] `trips/seed.py` + команда `seed_demo` — идемпотентный засев референсного Trip.
- [x] `trips/serializers.py` — единый снапшот: `trip`, `plan[]`, `messages[]`,
      `budget{fact, estimate, total, lines[]}` (живой бюджет выводится из BudgetLine), `emergency[]`,
      `phase`, `chips`, `await_user`, `results?`.
- [x] `trips/views.py` + `trips/urls.py`: `GET /api/trip/<id>/state`.
- **Проверка:** ✅ `seed_demo` идемпотентен (Trip #1, без дублей); `GET /state` → HTTP 200,
      10 пунктов (фаза 0 wait / фазы 1–2 locked), бюджет 38 000 / 137 000 / 175 000, 3 emergency.
- **Заметка:** консольные команды держим ASCII (Windows cp1252 не печатает кириллицу; на HTTP не влияет).

---

## Веха 2 — LangGraph скелет, фаза 0 (ARCHITECTURE §5, §6, §7-fallback) ✅

- [x] `trips/graph/state.py` — transient TypedDict (`trip_id`, `action`, `chip_value`).
- [x] `trips/graph/steps.py` — шаги фазы 0 (`hotel`/`docs`-silent/`insurance`/`budget`-silent),
      dataclasses `Chip`/`Step`, контент из спеки; `active_chips_and_await` (вывод, не персист).
- [x] `trips/graph/nodes.py` — `apply_answer`, `advance` (прогон silent + плановые/бюджетные мутации),
      `generate` (fallback + закрытие фазы). Узлы пишут в Django; вью оборачивает в `transaction.atomic`.
- [x] `trips/graph/journey.py` — сборка `StateGraph` (apply_answer → advance → generate) + `run()`.
- [x] `trips/graph/llm.py` — заглушка → `step.fallback` (реальный вызов в Вехе 7).
- [x] Эндпоинты `POST /api/trip/start` (идемпотентно), `POST /api/trip/<id>/answer`.
- **Проверка:** ✅ `start`→hotel (chips booking/appart/booked); answer(booking) → docs silent
      («удостоверение **Алии** до **28.07** → eGov», tag a) → insurance (3 тарифа); answer(family) →
      budget silent → закрытие фазы. Все 4 пункта `done`; **факт 38 000→86 000→89 000**, итог
      стабилен 175 000; `await_user` корректно true→false. Состояние пережило рестарт сервера
      (`GET /state` восстановил экран без повторного прогона графа).
- **Фикс на ревью:** ложный/повторный `/answer` после закрытия фазы (await=false) дрейфил
      `step_index` и дублировал нотис — добавлен guard во вью (валидация awaiting + чипа) + кламп в
      `advance`. Покрыто `trips/tests.py` (smoke-тесты заведены досрочно, фундамент Вехи 10).

---

## Веха 3 — Фаза 1 + развилки (ARCHITECTURE §2, §5.3, §9) ✅

- [x] Шаги фазы 1 в `steps.py`: `pharmacy`(T−7) → `prep_entry`(silent: time-divider + concern-карточка
      дождя) → `transfer` → `kino` → `restaurant` → `market_rain`(не plan-item) → `checklist_card`(silent).
- [x] `_run_silent` подставляет погоду/отель в тексты (concern дождя из `trip.weather`).
- [x] `POST /api/trip/<id>/advance` (`{to_phase}`) — разблокирует пункты фазы, ставит `phase/step`,
      прогоняет первый шаг через граф; guard: только `phase+1` и только при закрытой фазе.
- [x] Smoke-тест `test_phase1_flow_rain`.
- **Проверка:** ✅ факт 93 500→101 500→**105 000**, расчётное **70 000**, итог 175 000; `transfer`/
      `restaurant` — расчётное (факт не растёт); `market_rain` платит «Дождевики», не создавая пункт;
      concern-карточка дождя эмитится; 8 пунктов done, `airba/taxi` locked.
- **Решение (упрощение §5.3):** отдельный узел `weather_branch` не делаю — демо всегда дождевой
      (§9), погодный контент зашит в шаги + `trip.weather` подаётся в тексты. Холод/жара/норма —
      не-цель (не активируются). Если нужна полная развилка — добавлю по запросу.

---

## Веха 4 — Фаза 2: в поезде (ARCHITECTURE §2, §5.3)

- [ ] Шаги фазы 2: вход (silent, time-divider + concern «через 10 мин Астана»),
      `airba`(только апарты — в hotel-path skip), `taxi_arrival`.
- [ ] `branch_housing` (conditional) — hotel → `airba` остаётся locked, идём к такси.
- **Проверка:** в hotel-path шаг `airba` пропускается; «Такси с вокзала» → `done`.

---

## Веха 5 — Фаза 3: в поездке, Этап 8 (ARCHITECTURE §2, §5.3-tracker, §9)

- [ ] Шаги-напоминания пт–вс: `resto_reminder`, `duman_morning`, `duman_taxi`, `sunday_plan`,
      `souvenirs`, `station_taxi` (из спеки §8.1, тайминги пт 19:30 → вс 19:00).
- [ ] Узел `tracker`: применяет «транзакции» поездки (трансфер/питание/сувениры), двигает живой
      бюджет расчётное→факт; нотисы #13 (перерасход) / #14 (экономия → IMAX).
- [ ] `EmergencyBlock` в снапшоте — всегда виден (Appteka 17 мин / детская больница / ассистанс 24/7).
- **Проверка:** факт идёт к 169 500; трекер живой; нотисы перерасхода/экономии срабатывают;
      emergency виден на всех фазах после страховки.

---

## Веха 6 — Фаза 4: Итоги + Flywheel, Этап 10 (ARCHITECTURE §5.3-results, §9)

- [ ] Узел `results`: таблица план/факт из `BudgetLine`, бонусы Halyk+, 3 чипса Flywheel
      (Бурабай / Алаколь / Шымкент).
- [ ] Снапшот отдаёт `results{rows[], totals, bonuses, flywheel[]}` на фазе 4.
- **Проверка:** Итого **175 000 vs 169 500 🎯**; строки сходятся (см. «Данные бюджета»);
      3 варианта следующей поездки.

---

## Веха 7 — Реальный LLM (ARCHITECTURE §7, §15)

- [ ] `graph/llm.py`: `ChatAnthropic(model=os.environ.get("ANTHROPIC_MODEL","claude-haiku-4-5"))`,
      system-промпт = travel-контекст + `step.ai_prompt`; `try/except` + таймаут → `step.fallback`.
- [ ] Без стриминга, только русский, без markdown, 1–2 предложения.
- **Проверка:** с ключом — живые тексты; пустой/битый ключ → fallback, весь путь 0→4 проходит без 5xx.

---

## Веха 8 — Frontend (ARCHITECTURE §8)

- [ ] Перенос V2-CSS из `prototype.html` (328–477) в `styles/companion.css` 1:1 (бренд, Golos Text).
- [ ] `state/tripReducer.ts` (Context + useReducer), `api/client.ts` (4 типизированные fetch-обёртки).
- [ ] Компоненты: `ChatColumn`(`MessageList`: Ai/User/TimeDivider/ConcernCard/SysNotice, `Chips`,
      `InputArea`), `TravelPlan`(`PhaseBar`, `PlanItem`×10, `Budget`+`BudgetTracker`, `EmergencyBlock`),
      `SimButtons`, `ResultsScreen`.
- [ ] `App.tsx` при маунте: `POST /start` → `GET /state`; каждый ответ API заменяет снапшот целиком.
- **Проверка:** вид совпадает с прототипом; полный путь 0→4 живой в браузере; рестарт бэка +
      перезагрузка фронта восстанавливают экран на текущем шаге.

---

## Веха 9 — Docker, один контейнер (ARCHITECTURE §11, §10)

- [ ] `Dockerfile` multi-stage: node build → python runtime (`collectstatic`, `migrate`, seed,
      `gunicorn config.wsgi`).
- [ ] `docker-compose.yml`: сервис `web`, `8000:8000`, `env_file: .env`, named volume на `db.sqlite3`.
- [ ] Django-вью `index.html` на `/`, WhiteNoise отдаёт статику.
- **Проверка:** `docker compose up` → `localhost:8000` проходит end-to-end; `docker compose restart`
      в середине демо сохраняет фазу/шаг/историю/бюджет.

---

## Веха 10 — Smoke-тест (единственные тесты, ARCHITECTURE §15)

- [ ] `pytest`: `/start` → `/answer`×N → `/advance` до фазы 4; проверка `phase/step`, состояний
      пунктов и сходимости Итогов (175 000 vs 169 500).

---

## Данные seed и бюджета (согласовать ДО кода — из спеки §3/§8/§10)

**Trip:** Айдар/Алия/Айша(9)/Тимур(5) · Алматы→Астана · ночной поезд ~13 ч ·
отпр. чт 4 июня ~20:00 → приб. пт 5 июня ~09:00 · отель (hotel-path) · погода = дождь сб +14° ·
emergency: Appteka 17 мин / ближайшая детская больница / ассистанс СК Халык 24/7.
*(Год — 2026; даты в основном display-строки.)*

**Стартовый бюджет (после билетов):** факт 38 000 / расчётное 137 000 / итог 175 000.

**Живая смета (факт↑ / расчётное↓, итог ≈175 000):**

| Этап | Факт | Расчётное |
|---|---|---|
| После отеля (+48 000) | 86 000 | 89 000 |
| После страховки (+3 000) | 89 000 | 86 000 |
| После аптечки T−7 (+4 500) | 93 500 | 81 500 |
| После Думана + дождевиков T−3 (+8 000 +3 500) | 105 000 | 70 000 |
| В поездке (трекер) | растёт по транзакциям | уменьшается |

**Таблица Итогов (фаза 4):** Предоплата 105 000/105 000 · Трансфер 14 000/11 500 ·
Питание 36 000/38 200 · Сувениры 10 000/10 300 · Непредвиденное 10 000/4 500 ·
**Итого 175 000/169 500 🎯**.
*(Предоплата 105 000 = билеты 38 000 + отель 48 000 + страховка 3 000 + аптечка 4 500 +
Думан 8 000 + дождевики 3 500 — всё оплаченное к T−3.)*

---

## Решения (подтверждены)

1. **Имя файла** — `TASKS.md`.
2. **Вид фаз 3–4** (трекер / экстренный блок / Итоги / Flywheel) — проектируем в языке V2-стилей;
   экран Итогов опираем на стиль `recap-hero / pie / next-trips` из V1-визарда `prototype.html`.
3. **Год УТП-документа** — удостоверение Алии истекает **28 июля 2026**.
4. **Кнопки симуляции** (`/advance`) — 4 перехода фаз inline в чате
   (за 3 дня / в поезде / выходные в Астане / итоги), как в прототипе.
