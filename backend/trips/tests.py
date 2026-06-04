"""Smoke tests (ARCHITECTURE.md §15) — the only tests, per the non-goals.

Grows phase by phase; for now covers the phase-0 graph flow and the stray-answer guard.
"""
import json

import pytest
from django.test import Client


def _answer(c, tid, value):
    return c.post(
        f"/api/trip/{tid}/answer",
        data=json.dumps({"chip_value": value}),
        content_type="application/json",
    ).json()


def _advance(c, tid, to_phase):
    return c.post(
        f"/api/trip/{tid}/advance",
        data=json.dumps({"to_phase": to_phase}),
        content_type="application/json",
    ).json()


def _finish_phase0(c):
    tid = c.post("/api/trip/start").json()["trip"]["id"]
    _answer(c, tid, "booking")
    _answer(c, tid, "family")
    return tid


@pytest.mark.django_db
def test_phase0_flow():
    c = Client()
    s = c.post("/api/trip/start").json()
    tid = s["trip"]["id"]

    # START → hotel awaits
    assert s["await_user"] is True
    assert [ch["value"] for ch in s["chips"]] == ["booking", "appart", "booked"]
    assert s["budget"]["fact"] == 38000
    assert s["budget"]["estimate"] == 137000
    assert s["budget"]["total"] == 175000

    # answer hotel → docs silent (the УТП) → insurance awaits
    s = _answer(c, tid, "booking")
    assert s["budget"]["fact"] == 86000
    assert s["budget"]["total"] == 175000
    sysm = [m for m in s["messages"] if m["kind"] == "sys"]
    assert any("eGov" in m["text"] for m in sysm)        # proactive doc alert
    assert any("28" in m["text"] for m in sysm)          # expires 28 July
    assert [ch["value"] for ch in s["chips"]] == ["base", "family", "premium"]

    # answer insurance → budget silent → phase closes
    s = _answer(c, tid, "family")
    assert s["budget"]["fact"] == 89000
    assert s["budget"]["estimate"] == 86000
    assert s["budget"]["total"] == 175000
    assert sum(1 for p in s["plan"] if p["state"] == "done") == 4
    assert s["await_user"] is False
    assert any("175 000" in m["text"] for m in s["messages"] if m["kind"] == "sys")


@pytest.mark.django_db
def test_phase1_flow_rain():
    c = Client()
    tid = _finish_phase0(c)

    # advance to phase 1 → pharmacy (T−7) awaits
    s = _advance(c, tid, 1)
    assert s["phase"] == 1
    assert s["await_user"] is True
    assert [ch["value"] for ch in s["chips"]] == ["kids", "allergy", "skip"]

    # pharmacy paid → fact 93 500
    s = _answer(c, tid, "kids")
    assert s["budget"]["fact"] == 93500
    assert any(m["kind"] == "concern" for m in s["messages"])      # prep_entry rain card
    assert [ch["value"] for ch in s["chips"]] == ["taxi", "public", "own"]

    # transfer → расчётное, fact unchanged
    s = _answer(c, tid, "taxi")
    assert s["budget"]["fact"] == 93500

    # kino (Думан) paid → fact 101 500
    s = _answer(c, tid, "duman")
    assert s["budget"]["fact"] == 101500

    # restaurant → расчётное, fact unchanged
    s = _answer(c, tid, "book")
    assert s["budget"]["fact"] == 101500

    # market (дождевики) paid → fact 105 000, phase closes
    s = _answer(c, tid, "market")
    assert s["budget"]["fact"] == 105000
    assert s["budget"]["estimate"] == 70000
    assert s["budget"]["total"] == 175000
    assert s["await_user"] is False

    done = {p["key"] for p in s["plan"] if p["state"] == "done"}
    assert done == {"hotel", "docs", "insur", "budget", "pharma", "transfer", "kino", "resto"}
    locked = {p["key"] for p in s["plan"] if p["state"] == "locked"}
    assert locked == {"airba", "taxi"}


@pytest.mark.django_db
def test_stray_answer_is_noop():
    c = Client()
    s = c.post("/api/trip/start").json()
    tid = s["trip"]["id"]
    _answer(c, tid, "booking")
    s = _answer(c, tid, "family")          # phase 0 now closed (await_user False)

    before, step = len(s["messages"]), s["trip"]["step_index"]
    s2 = _answer(c, tid, "family")         # stray duplicate answer
    assert len(s2["messages"]) == before
    assert s2["trip"]["step_index"] == step

    s3 = _answer(c, tid, "nope")           # unknown chip
    assert len(s3["messages"]) == before
