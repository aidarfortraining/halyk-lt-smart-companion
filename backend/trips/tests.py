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


def _finish_phase1(c, tid):
    _advance(c, tid, 1)
    for v in ("kids", "taxi", "duman", "book", "market"):
        _answer(c, tid, v)


def _finish_phase2(c, tid):
    _advance(c, tid, 2)
    _answer(c, tid, "taxi")


def _finish_phase3(c, tid):
    _advance(c, tid, 3)
    for v in ("taxi", "buy", "taxi"):       # duman_taxi, souvenirs, station_taxi
        _answer(c, tid, v)


def _line(snapshot, category):
    return next(l for l in snapshot["budget"]["lines"] if l["category"] == category)


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
def test_phase2_hotel_path_skips_airba():
    c = Client()
    tid = _finish_phase0(c)
    _finish_phase1(c, tid)

    # advance to phase 2 → train_entry silent → taxi_arrival awaits (airba skipped)
    s = _advance(c, tid, 2)
    assert s["phase"] == 2
    assert s["await_user"] is True
    assert [ch["value"] for ch in s["chips"]] == ["taxi", "skip"]
    assert any(m["kind"] == "concern" for m in s["messages"])        # "через 10 минут Астана"
    # message text placeholders are rendered, not literal
    assert not any("{hotel}" in m["text"] for m in s["messages"])
    assert any("Holiday Inn" in m["text"] for m in s["messages"] if m["kind"] == "ai")

    # call taxi → done; airba stays locked; budget unchanged (realized in phase 3 tracker)
    s = _answer(c, tid, "taxi")
    assert s["await_user"] is False
    plan = {p["key"]: p["state"] for p in s["plan"]}
    assert plan["taxi"] == "done"
    assert plan["airba"] == "locked"
    assert s["budget"]["fact"] == 105000
    assert s["budget"]["total"] == 175000


@pytest.mark.django_db
def test_phase3_tracker_converges_to_169500():
    c = Client()
    tid = _finish_phase0(c)
    _finish_phase1(c, tid)
    _finish_phase2(c, tid)

    # advance to phase 3 → entry + resto + duman_morning run silently → duman_taxi awaits
    s = _advance(c, tid, 3)
    assert s["phase"] == 3
    assert s["await_user"] is True
    assert [ch["value"] for ch in s["chips"]] == ["taxi", "skip"]
    # 105000 + 3500(arrival) + 12200(fri) + 14000(sat food) + 4500(misc)
    assert s["budget"]["fact"] == 139200

    s = _answer(c, tid, "taxi")        # Duman taxi +4000
    assert s["budget"]["fact"] == 143200
    assert [ch["value"] for ch in s["chips"]] == ["buy", "skip"]   # souvenirs

    s = _answer(c, tid, "buy")         # souvenirs +10300 → then sunday_plan +12000 (#13 fires)
    assert s["budget"]["fact"] == 165500
    # overspend notice (#13) for Питание: 38 200 of 36 000
    assert any("38 200" in m["text"] and "36 000" in m["text"]
               for m in s["messages"] if m["kind"] == "sys")
    assert [ch["value"] for ch in s["chips"]] == ["taxi", "skip"]  # station_taxi

    s = _answer(c, tid, "taxi")        # station taxi +4000 → trip_wrapup → phase closes
    assert s["await_user"] is False
    assert s["budget"]["fact"] == 169500
    assert s["budget"]["estimate"] == 0
    assert s["budget"]["total"] == 169500

    # category facts match the Итоги table (spec §10)
    assert _line(s, "Трансфер")["fact_amount"] == 11500
    assert _line(s, "Питание")["fact_amount"] == 38200
    assert _line(s, "Сувениры")["fact_amount"] == 10300
    assert _line(s, "Непредвиденное")["fact_amount"] == 4500


@pytest.mark.django_db
def test_phase4_results_and_flywheel():
    c = Client()
    tid = _finish_phase0(c)
    _finish_phase1(c, tid)
    _finish_phase2(c, tid)
    _finish_phase3(c, tid)

    # advance to phase 4 → results presented, flywheel awaits
    s = _advance(c, tid, 4)
    assert s["phase"] == 4
    assert s["await_user"] is True
    assert [ch["value"] for ch in s["chips"]] == ["burabay", "alakol", "shymkent"]

    r = s["results"]
    assert r is not None
    assert r["totals"] == {"plan": 175000, "fact": 169500, "delta": -5500}   # 🎯
    rows = r["rows"]
    assert len(rows) == 5
    assert rows[0] == {"category": "Предоплата", "plan": 105000, "fact": 105000, "delta": 0}
    assert (rows[1]["plan"], rows[1]["fact"], rows[1]["delta"]) == (14000, 11500, -2500)   # Трансфер
    assert (rows[2]["plan"], rows[2]["fact"], rows[2]["delta"]) == (36000, 38200, 2200)    # Питание
    assert (rows[3]["plan"], rows[3]["fact"], rows[3]["delta"]) == (10000, 10300, 300)     # Сувениры
    assert (rows[4]["plan"], rows[4]["fact"], rows[4]["delta"]) == (10000, 4500, -5500)    # Непредвид.
    assert len(r["flywheel"]) == 3

    # pick a next trip → demo closes
    s = _answer(c, tid, "burabay")
    assert s["await_user"] is False
    assert s["phase"] == 4
    assert s["results"] is not None        # results persist after the pick


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
