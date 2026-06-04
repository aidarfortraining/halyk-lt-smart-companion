# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: Halyk Smart Travel Companion

A **demo-day prototype** for Halyk Bank: an AI travel companion that turns a one-shot ticket purchase into an "operations HQ" for a family trip, guiding the client from booking to return and closing each anxiety at the right moment. **Goal is to defend the idea on demo day, not to build production.** Simplicity beats completeness everywhere.

### Current state

The repo currently contains **only specs and a UI prototype — no application code yet.**

- `halyk_smart_travel_spec.md` — **source of truth for product logic & content** (the anxiety map, 10-stage journey, ~18 notifications, budget mechanics, weather adaptation). Russian.
- `ARCHITECTURE.md` — **source of truth for the implementation** (finalized: tech stack, Django data model, LangGraph nodes, API contract, full 5-phase scope, build milestones, prototype-vs-spec content corrections). Russian. **Read this first before coding.**
- `PLAN.md` — original build-architecture sketch & explicit non-goals (skeleton; superseded in detail by `ARCHITECTURE.md`). Russian.
- `prototype.html` — **source of truth for visual look only** (single-file vanilla HTML/CSS/JS, ~1500 lines, Halyk brand, chat + Travel Plan). No framework, no build step — open directly in a browser. Will be rebuilt; its *content* (dates, texts, budget, train duration, document trigger) is **superseded** — see `ARCHITECTURE.md` §14.

When these sources conflict: **how to build → `ARCHITECTURE.md`, content/dates/text → `halyk_smart_travel_spec.md`, visual look → `prototype.html`.**

### Planned stack (see ARCHITECTURE.md)

Django + DRF (backend) + React 18 / Vite / TS (frontend) + SQLite + **LangChain / LangGraph** (the orchestration core — this graph *is* the product) + WhiteNoise + Gunicorn + Docker (single container). LLM messages generated via Anthropic API model **`claude-haiku-4-5`** (env `ANTHROPIC_MODEL`), key in `.env` (gitignored, currently empty). **Django ORM is the single source of truth for state; LangGraph runs stateless on top** (no LangGraph checkpointer).

- Run target: `docker compose up` → `localhost:8000`, end-to-end in one step.
- **The demo must run fully offline**: every AI step has a prepared `fallback` so no network = still a complete run.
- State persists (the Travel Plan survives a container restart mid-demo).

### The reference scenario (hardcoded)

One family: Aidar / Alia / Aisha (9) / Timur (5). Almaty → Astana, **night train (~13h)**, **June 5–7** (depart Thu June 4 ~20:00, arrive Fri June 5 ~09:00). The client walks the full trip in chat across **5 phases**: Phase 0 (T−14: hotel → documents → insurance → budget) → Phase 1 (T−7/T−3: pharmacy → transfer → entertainment → restaurant → rain gear) → Phase 2 (on the train: groceries/taxi) → Phase 3 (in Astana: live budget tracker, reminders, emergency block, souvenirs) → Phase 4 (Results план/факт + Flywheel). Demo uses the **hotel path** (not apartments) and the **rainy-Saturday** weather scenario (richest logic). The proactive **document-expiry alert (Alia's ID expires July 28 → eGov)** is the key differentiator.

Each AI step emits a short message in "anxiety language"; the client replies with chips (human-in-the-loop). The right column is a live **Travel Plan** of 10 items (locked / wait / done), plus an always-visible **emergency block**. Inline simulation buttons advance phases. Full stage→step→notification mapping is in `ARCHITECTURE.md` §2.

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
