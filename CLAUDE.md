# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: Halyk Smart Travel Companion

A **demo-day prototype** for Halyk Bank: an AI travel companion that turns a one-shot ticket purchase into an "operations HQ" for a family trip, guiding the client from booking to return and closing each anxiety at the right moment. **Goal is to defend the idea on demo day, not to build production.** Simplicity beats completeness everywhere.

### Current state

**Build complete — vehи 0–10 done.** Runs in one container: `docker compose up` → `localhost:8000`,
end-to-end. The LangGraph core runs the **full journey phases 0→4** (hotel→docs→insurance→budget →
pharmacy→transfer→kino→restaurant→rain-gear → train→taxi → live tracker/reminders/souvenirs →
Итоги+Flywheel), with the **real `claude-haiku-4-5`** LLM and a fallback on every step so it also runs
fully offline. Budget converges 38 000 → 169 500 (Итоги 175 000 vs 169 500 🎯). React SPA served by
WhiteNoise; state on a SQLite volume survives `docker compose restart`. Tests: backend 6 (pytest),
frontend 2 (vitest). **`docs/TASKS.md` is the per-veha tracker** (verification + as-built notes).
**Local dev:** see Commands below (venv + runserver + `npm run dev`).
*(Verified end-to-end in a real browser via Playwright (2026-06-05): the full 5-phase click-through
with the live `claude-haiku-4-5` LLM runs clean — the budget invariant holds at every step
(38 000 → 89 000 → 105 000 → 169 500, Итоги 175 000 vs 169 500 🎯), every request 200, no console errors.)*

Layout: `backend/` — Django project `config/`, app `trips/` (`models.py`, `seed.py`,
`serializers.py` = snapshot + Итоги, `views.py` = 4 endpoints, `graph/` = the LangGraph core
[`state.py`, `steps.py` = all 5 phases declared, `nodes.py`, `journey.py`, `llm.py`, `context.py`],
`tests.py` = pytest smoke, `management/commands/seed_demo.py`). `frontend/` — Vite + React 18 + TS SPA
(`api/client.ts`, `state/trip.tsx`, `types.ts`, `util.ts`, `components/` = ChatColumn/MessageList/
Chips/InputArea/TravelPlan/Budget/EmergencyBlock/SimButtons/ResultsScreen, `styles/companion.css`
= V2-CSS port of the prototype, `App.test.tsx` = vitest render test on captured snapshots).
`Dockerfile` (multi-stage) + `docker-compose.yml` (SQLite on a named volume). Dev DB
`backend/db.sqlite3` (gitignored); the prod SPA build lands in `backend/frontend_dist` (gitignored).

**API:** `POST /api/trip/start` · `GET /api/trip/<id>/state` · `POST /api/trip/<id>/answer` (`{chip_value}`)
· `POST /api/trip/<id>/advance` (`{to_phase}`). Every response is one full render snapshot
(`trip, plan[10], messages[], budget{fact,estimate,total,lines}, emergency[], phase, chips, await_user, results?`);
`chips`/`await_user`/`results` are derived from `steps.py`, not persisted.

Source-of-truth docs:

- `init-info/halyk_smart_travel_spec.md` — **source of truth for product logic & content** (the anxiety map, 10-stage journey, ~18 notifications, budget mechanics, weather adaptation). Russian.
- `docs/ARCHITECTURE.md` — **source of truth for the implementation** (tech stack, Django data model, LangGraph nodes, API contract, full 5-phase scope, build milestones, prototype-vs-spec content corrections; see §16 for as-built deltas). Russian. **Read this first before coding.**
- `docs/TASKS.md` — **build tracker**: the milestones (vehи 0–10, all ✅) expanded into tasks with verification + decisions taken. Russian. Read it to see exactly what was built and why.
- `docs/PLAN.md` — original build-architecture sketch & explicit non-goals (skeleton; superseded in detail by `docs/ARCHITECTURE.md`). Russian.
- `init-info/prototype.html` — **source of truth for visual look only** (single-file vanilla HTML/CSS/JS, ~1500 lines, Halyk brand, chat + Travel Plan). No framework, no build step — open directly in a browser. Will be rebuilt; its *content* (dates, texts, budget, train duration, document trigger) is **superseded** — see `docs/ARCHITECTURE.md` §14.

When these sources conflict: **how to build → `docs/ARCHITECTURE.md`, content/dates/text → `init-info/halyk_smart_travel_spec.md`, visual look → `init-info/prototype.html`.**

### Commands

**Run the demo (one container):** `docker compose up` → `localhost:8000`, end-to-end (first run builds the image; the CMD does `migrate` + `seed_demo` + gunicorn; SQLite state on the `sqlite-data` volume survives `docker compose restart`). Stop with `docker compose down` (add `-v` to wipe demo state). `.env` (gitignored) supplies `ANTHROPIC_API_KEY`/`ANTHROPIC_MODEL`.

**Local dev** (venv is `.venv`, Python 3.11, at the repo root; backend lives in `backend/`, run `manage.py` as `backend\manage.py`):

- **Backend deps:** `.venv\Scripts\python.exe -m pip install -r backend\requirements.txt`
- **Migrate + seed:** `.venv\Scripts\python.exe backend\manage.py migrate` then `... seed_demo` (idempotent reference Trip)
- **Run backend:** `.venv\Scripts\python.exe backend\manage.py runserver` → `localhost:8000` (API under `/api/`)
- **Backend tests:** `.venv\Scripts\python.exe -m pytest backend -q` (6 smoke tests)
- **Frontend dev:** `npm install --prefix frontend`, `npm run dev --prefix frontend` (Vite, proxies `/api` → `:8000`)
- **Frontend build / tests:** `npm run build --prefix frontend` (→ `backend/frontend_dist`) · `npm run test --prefix frontend` (vitest, 2 render tests)
- **Windows notes:** console is cp1252 — keep management-command/script `print` output ASCII (Cyrillic crashes the console; HTTP/JSON is UTF-8 and unaffected). PowerShell `$env:VAR=''` **removes** the var (it won't force-empty a key — use a real empty value path if you need fallback mode).

### Stack (as built; see docs/ARCHITECTURE.md §16 for as-built deltas)

Django 5.2 + DRF (backend) + React 18 / Vite / TS (frontend) + SQLite + **LangChain / LangGraph 1.x** (the orchestration core — this graph *is* the product) + WhiteNoise (serves the SPA) + Gunicorn + Docker (single container). LLM messages generated via Anthropic model **`claude-haiku-4-5`** (env `ANTHROPIC_MODEL`); key in `.env` (gitignored) — **set it for live generation; without a key every step falls back to its canned text, so the demo still runs fully offline.** **Django ORM is the single source of truth for state; LangGraph runs stateless on top** (no LangGraph checkpointer).

- Run target: `docker compose up` → `localhost:8000`, end-to-end in one step.
- **The demo must run fully offline**: every AI step has a prepared `fallback` so no network = still a complete run.
- State persists (the Travel Plan survives a container restart mid-demo).

### The reference scenario (hardcoded)

One family: Aidar / Alia / Aisha (9) / Timur (5). Almaty → Astana, **night train (~13h)**, **June 5–7** (depart Thu June 4 ~20:00, arrive Fri June 5 ~09:00). The client walks the full trip in chat across **5 phases**: Phase 0 (T−14: hotel → documents → insurance → budget) → Phase 1 (T−7/T−3: pharmacy → transfer → entertainment → restaurant → rain gear) → Phase 2 (on the train: groceries/taxi) → Phase 3 (in Astana: live budget tracker, reminders, emergency block, souvenirs) → Phase 4 (Results план/факт + Flywheel). Demo uses the **hotel path** (not apartments) and the **rainy-Saturday** weather scenario (richest logic). The proactive **document-expiry alert (Alia's ID expires July 28 → eGov)** is the key differentiator.

Each AI step emits a short message in "anxiety language"; the client replies with chips (human-in-the-loop). The right column is a live **Travel Plan** of 10 items (locked / wait / done), plus an always-visible **emergency block**. Inline simulation buttons advance phases. Full stage→step→notification mapping is in `docs/ARCHITECTURE.md` §2.

### Budget model (recurring invariant)

Two tiers — **факт** (paid/reserved, fixed) and **расчётное** (system forecast). As items are paid, money moves from расчётное into факт while the **total stays ~175 000 ₸**. Trace: 89 000 → 93 500 → 101 500 → 105 000 факт. Keep this invariant intact when touching budget code.

### Explicit non-goals (do NOT build)

Auth/JWT · Redis/caches · Celery/queues · real partner APIs (Booking, inDrive, Appteka, Kino.kz, KTZh, eGov are all **mock/seed**) · multi-user/concurrency · token streaming · RAG / vector DB / multi-agent · tests beyond smoke. Adding any of these works against the demo.

---

## Behavioral guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
