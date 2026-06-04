# TASKS.md — исполняемый чеклист сборки

> **СТАТУС: всё готово ✅ — вехи 0–10 закрыты.** Проект собран и запускается одним контейнером
> (`docker compose up` → `localhost:8000`). Тесты: backend 6/6 (pytest), frontend 2/2 (vitest).
> Браузерный клик-прогон через Playwright выполнен (2026-06-05): сквозной путь всех 5 фаз с живым
> `claude-haiku-4-5` проходит без ошибок, бюджет сходится на каждом шаге (38 000 → 89 000 → 105 000
> → 169 500, Итоги 175 000/169 500 🎯), все запросы 200, ошибок в консоли нет.
>
> **Что это.** Пошаговый план сборки Halyk Smart Travel Companion, развёрнутый из
> `ARCHITECTURE.md §13` в конкретные задачи с файлами и критериями проверки.
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

## Веха 4 — Фаза 2: в поезде (ARCHITECTURE §2, §5.3) ✅

- [x] Шаги фазы 2: `train_entry`(silent: time-divider + concern «через 10 мин Астана»),
      `airba`(`requires_apartments` — в hotel-path skip), `taxi_arrival`.
- [x] `branch_housing` свёрнут в `advance`: неактивные (apartments-only) шаги пропускаются без эмита;
      `/advance` не разблокирует `airba` в hotel-path. `_step_active` учитывается и в выводе chips.
- [x] **Фикс из Вехи 3:** fallback-тексты и подписи чипов теперь форматируются контекстом
      (`graph/context.py`: `text_ctx`/`full_ctx`/`budget_now`) — плейсхолдеры `{hotel}`/`{sat}` больше
      не утекают буквально. DRY бюджета (serializers ← `budget_now`).
- [x] Smoke-тест `test_phase2_hotel_path_skips_airba` (вкл. проверку рендера плейсхолдеров).
- **Проверка:** ✅ в hotel-path `airba` пропущен (chips `taxi/skip`), остаётся `locked`; concern-карточка
      эмитится; «Такси с вокзала» → `done`; бюджет 105 000/175 000 без изменений (трансфер реализуется
      трекером в фазе 3).

---

## Веха 5 — Фаза 3: в поездке, Этап 8 (ARCHITECTURE §2, §5.3-tracker, §9) ✅

- [x] 8 шагов пт–вс: `tracker_entry → resto_reminder → duman_morning → duman_taxi → souvenirs →
      sunday_plan → station_taxi → trip_wrapup` (тайминги пт прибытие → вс 19:00, спека §8).
- [x] **Аддитивные транзакции** (`_apply_budget_tx`: `fact += amount`) — унифицируют prepaid и трекер;
      переменные категории накапливаются: Трансфер 11 500, Питание 38 200, Сувениры 10 300,
      Непредвиденное 4 500. Поле `Step.tx`; silent-шаги и чипы применяют транзакции.
- [x] Нотис #13 (перерасход) — **вычислимо** при пересечении плана категории (Питание 26 200→38 200
      пересекает 36 000); #14 (экономия) — нота в `trip_wrapup`.
- [x] `EmergencyBlock` — `emergency[]` в каждом снапшоте из seed (всегда виден).
- [x] Smoke-тест `test_phase3_tracker_converges_to_169500`.
- **Проверка:** ✅ факт 139 200→143 200→165 500→**169 500**, расчётное **0**; #13 срабатывает
      (38 200 из 36 000); строки категорий = таблица Итогов §10; трекер живой.

---

## Веха 6 — Фаза 4: Итоги + Flywheel, Этап 10 (ARCHITECTURE §5.3-results, §9) ✅

- [x] Шаг `results` (фаза 4): сопроводительное сообщение + чипсы Flywheel (Бурабай/Алаколь/Шымкент).
- [x] `serializers.build_results` — таблица план/факт из `BudgetLine` (prepaid → «Предоплата»),
      бонусы Halyk+, flywheel; снапшот отдаёт `results{rows, totals, bonuses, flywheel}` при фазе 4.
- [x] Smoke-тест `test_phase4_results_and_flywheel` (он же гоняет весь путь 0→4).
- **Проверка:** ✅ Итого **175 000 / 169 500 / Δ −5 500 🎯**; 5 строк сходятся (Предоплата 105 000,
      Трансфер −2 500, Питание +2 200, Сувениры +300, Непредвиденное −5 500); 3 поездки flywheel;
      `results` сохраняется после выбора. **Полный путь 0→4 проходит оффлайн.**

---

## Веха 7 — Реальный LLM (ARCHITECTURE §7, §15) ✅

- [x] `graph/llm.py`: `ChatAnthropic(model=settings.ANTHROPIC_MODEL, api_key=…, max_tokens=200,
      temperature=0.7, timeout=20, max_retries=1)`; system-промпт = travel-контекст + `step.ai_prompt`
      (плейсхолдеры рендерятся); `try/except` → `step.fallback`. Контент Anthropic (str/блоки) извлекается.
- [x] Без стриминга, только русский, без markdown, 1–2 предложения; пустой ключ → сразу fallback.
- [x] Smoke-тесты форсируют offline (autouse-фикстура с пустым ключом) — детерминированы, без сети.
- **Проверка:** ✅ с реальным ключом `claude-haiku-4-5` — живой русский текст (≠ fallback, прямой вызов
      и `generate()` ок); пустой ключ → fallback, весь путь 0→4 зелёный без 5xx (6 тестов).
      Любая ошибка LLM перехватывается → fallback (API не отдаёт 5xx из-за модели).

---

## Веха 8 — Frontend (ARCHITECTURE §8) ✅

- [x] Перенос V2-CSS из `prototype.html` (328–477) в `styles/companion.css` 1:1 + добавления
      (emergency / sim-кнопки / трекер-категории / results-card) в той же палитре.
- [x] `state/trip.tsx` (Context + useReducer, снапшот заменяется целиком), `api/client.ts` (4 обёртки),
      `types.ts`, `util.ts`.
- [x] Компоненты: `ChatColumn`(`MessageList`: ai/user/time/concern/sys, `Chips`, `InputArea`),
      `TravelPlan`(phase-bar 5 сегм., `PlanItem`×10, `Budget`+трекер-категории, `EmergencyBlock`),
      `SimButtons`, `ResultsScreen` (таблица Итогов + flywheel-карточки).
- [x] `App.tsx`: `TripProvider` зовёт `POST /start` при маунте (guard StrictMode); каждый ответ API
      заменяет снапшот целиком. Прокси `/api`→`:8000`.
- **Проверка:** ✅ прод-сборка чистая (tsc+vite); **render-тесты vitest+jsdom** на реальных
      снапшотах (`App.test.tsx`): монтирование, фаза 0 (10 пунктов, чипсы, бюджет 175 000, emergency,
      phase-bar) и фаза 4 (таблица 175 000/169 500, 3 flywheel) рендерятся без ошибок.
- **Заметка:** браузерный клик-тест выполнен позже через Playwright (2026-06-05): все 5 фаз
      прокликаны в реальном браузере на `localhost:8000` с живым LLM, рендер и бюджетный инвариант
      подтверждены, все запросы 200. Вид — порт V2-CSS 1:1, рантайм также покрыт jsdom.

---

## Веха 9 — Docker, один контейнер (ARCHITECTURE §11, §10) ✅

- [x] `Dockerfile` multi-stage: node:24-slim (`npm ci` + `vite build` → `dist`) → python:3.12-slim
      (requirements, копия `frontend_dist`, `collectstatic`); CMD: `migrate` + `seed_demo` + gunicorn.
- [x] `docker-compose.yml`: сервис `web`, `8000:8000`, `env_file: .env`, `SQLITE_PATH=/data/db.sqlite3`
      на named volume `sqlite-data`, `DJANGO_DEBUG=0`. `.dockerignore`.
- [x] SPA: **WhiteNoise** отдаёт `frontend_dist` в корне (`WHITENOISE_ROOT` + index-file) — `/`→index.html,
      `/assets/*` → хешированный бандл; storage без manifest (Vite уже хеширует).
- **Проверка:** ✅ `docker compose build` ок; `up` → `GET /` 200 (#root), `/assets/*.js` 200, `/api/*`
      работает (LLM из `.env`); поток `start→booking` факт 38 000→86 000. **`docker compose restart`
      середине → `GET /state` восстановил phase 0 / факт 86 000 / 5 сообщений / 2 done** (volume жив).

## Веха 10 — Smoke-тест (ARCHITECTURE §15) ✅

- [x] `pytest` (6 тестов): полный путь `/start → /answer×N → /advance` по фазам 0→4; проверка
      `phase/step`, состояний пунктов, бюджетной трассы и сходимости Итогов (**175 000 vs 169 500**);
      guard ложного `/answer`; пропуск `airba` в hotel-path; offline-форс (autouse-фикстура).
- [x] Frontend: `vitest` (2 теста) — render фаз 0 и 4 на реальных снапшотах.
- **Проверка:** ✅ backend 6/6, frontend 2/2 зелёные.

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
