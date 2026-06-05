# Halyk Smart Travel Companion

**Демо-прототип** для Halyk Bank: AI-ассистент, который превращает разовую покупку билета
в операционный штаб семейной поездки — ведёт клиента от брони до возвращения и закрывает
каждую тревогу в нужный момент.

> Продукт строится **не на списке сервисов, а на карте тревог клиента**: каждое сообщение
> отвечает на конкретную мысль в конкретный момент. Клиент чувствует заботу, а не продажу.

Оркестрация диалога — **LangGraph**, генерация сообщений — **claude-haiku-4-5** (с fallback
на каждом шаге, поэтому демо работает полностью офлайн).

---

## Сценарий

Семья Айдар / Алия / Айша (9) / Тимур (5). Алматы → Астана, ночной поезд ~13 ч, 5–7 июня,
дождливая суббота. Клиент проходит весь путь в чате за **5 фаз**:

`Фаза 0` жильё → документы → страховка → бюджет ·
`Фаза 1` аптечка → трансфер → развлечения → ресторан → погода ·
`Фаза 2` в поезде: такси / продукты ·
`Фаза 3` в Астане: живой трекер, напоминания, экстренный блок, сувениры ·
`Фаза 4` Итоги план/факт + Flywheel.

Ключевой дифференциатор — **проактивная проверка документов** (удостоверение Алии истекает
28 июля → eGov). Бюджет сходится: план 175 000 ₸ → факт 169 500 ₸ 🎯.

## Быстрый старт

```bash
docker compose up        # → http://localhost:8000  (migrate + seed + gunicorn, end-to-end)
```

`.env` (gitignored) задаёт `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL`. **Без ключа** каждый шаг
отдаёт канонический fallback — демо проходит до конца офлайн.

## Локальная разработка

```bash
# Backend (venv .venv, Python 3.11)
.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
.venv/Scripts/python.exe backend/manage.py migrate
.venv/Scripts/python.exe backend/manage.py seed_demo
.venv/Scripts/python.exe backend/manage.py runserver        # → localhost:8000

# Frontend (Vite, проксирует /api → :8000)
npm install --prefix frontend
npm run dev --prefix frontend

# Тесты
.venv/Scripts/python.exe -m pytest backend -q               # 9 smoke
npm run test --prefix frontend                              # 2 render
```

## Стек

Django 5 + DRF · React 18 / Vite / TS · SQLite · **LangChain / LangGraph** · WhiteNoise ·
Gunicorn · Docker (один контейнер). **Django ORM — единый источник правды; LangGraph
работает stateless поверх** (без чекпойнтера).

## API

Каждый ответ — полный render-снапшот (`trip, plan[10], messages[], budget, emergency, phase,
chips, await_user, results?`).

| Метод | Endpoint | Назначение |
|---|---|---|
| POST | `/api/trip/start` | идемпотентный старт (refresh резюмирует) |
| POST | `/api/trip/reset` | сброс и реплей с фазы 0 |
| GET  | `/api/trip/<id>/state` | снапшот |
| POST | `/api/trip/<id>/answer` | ответ чипсом `{chip_value}` |
| POST | `/api/trip/<id>/advance` | переход к следующей фазе `{to_phase}` |

## Структура

```
backend/    Django (config/ + app trips/: models, seed, serializers, views,
            graph/ = LangGraph-ядро [state, steps, nodes, journey, llm, context])
frontend/   React + Vite + TS SPA (components/, wizard/, state/, styles/)
docs/       ARCHITECTURE.md · TASKS.md · PLAN.md · CODE_REVIEW_PREP.md (рус.)
init-info/  halyk_smart_travel_spec.md (источник продуктовой логики) · prototype.html
presentation/  демо-дей дек (.pptx/.pdf), генератор build_deck.py, сценарий выступления
```

## Документация

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — **как построено** (читать первым)
- [`init-info/halyk_smart_travel_spec.md`](init-info/halyk_smart_travel_spec.md) — продуктовая логика и контент
- [`docs/TASKS.md`](docs/TASKS.md) — трекер сборки (вехи 0–10)
- [`docs/CODE_REVIEW_PREP.md`](docs/CODE_REVIEW_PREP.md) — разбор для code-review

## Презентация

`presentation/Halyk_Smart_Travel.pptx` (21 слайд) — пересборка из исходника:

```bash
.venv/Scripts/python.exe presentation/build_deck.py
```

Текст докладчика по каждому слайду — `presentation/Сценарий_выступления.md`.

---

*Демо-прототип для защиты идеи на demo-day, не production. Партнёрские интеграции
(Booking, inDrive, Appteka, Kino.kz, KTZh, eGov) — mock/seed.*
