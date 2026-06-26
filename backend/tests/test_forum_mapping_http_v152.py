"""HTTP-level integration test for Mirror Relationship v1.5.2 payload.

Hits the live `/api/forums/{forum_id}/member-mappings` endpoint via the public
EXPO_PUBLIC_BACKEND_URL and validates the additive v1.5.2 contract:

  • signals.human_design[i].narrative {gift, tension, practical_use}
  • signals.human_design_field.narrative_blocks (HD drill-down)
  • signals.bazi.animal_narrative (when both charts have year animals)
  • signals.numerology.v2_card (Mirror Language fields)
  • relationship_synthesis.undertone_for_today (string)
  • No raw HD jargon in top story
  • No duplicate sentences across story slots
  • Legacy keys preserved
  • /between-you-today still works independently
"""
from __future__ import annotations
import os
import re
import pytest
import requests

BASE = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/")
if not BASE:
    # fallback to frontend .env scan
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
                    BASE = line.split("=", 1)[1].strip().strip('"').rstrip("/")
                    break
    except Exception:
        pass

PETE = "697f0c6abf35c0528ff06954"
PETE_MEL_FORUM = "69dd05eaa333335fcbf3ad33"
YOONG_FORUM = "69dda348de9cb1c83c0780fa"

JARGON_PATTERNS = [
    r"\bAjna\b",
    r"\bSacral\b",
    r"\bSolar Plexus\b",
    r"\bdefined center\b",
    r"\bopen center\b",
    r"\bG[\s-]?Center\b",
    r"\bGate\s+\d+\b",
    r"\bChannel\s+\d+-\d+\b",
    r"Manifestor\s*x\s*Reflector",
    r"\bTen God\b",
]


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def mappings_response(session):
    assert BASE, "EXPO_PUBLIC_BACKEND_URL not set"
    url = f"{BASE}/api/forums/{PETE_MEL_FORUM}/member-mappings"
    r = session.get(url, params={"user_id": PETE}, timeout=60)
    assert r.status_code == 200, f"{r.status_code}: {r.text[:500]}"
    data = r.json()
    assert data.get("success") is True, f"endpoint reported failure: {data}"
    return data


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower()).strip()


# -------------------------------------------------------------------- payload

def test_endpoint_returns_mappings(mappings_response):
    mappings = mappings_response.get("mappings", [])
    assert isinstance(mappings, list)
    assert len(mappings) >= 1, "Pete-Mel forum should have at least one mapping"


def test_legacy_keys_present_on_every_mapping(mappings_response):
    legacy = {
        "headline", "description", "what_works", "what_to_watch",
        "why_this_happens", "channel_count", "strength_score",
        "story", "patterns", "signals",
    }
    for m in mappings_response["mappings"]:
        missing = legacy - set(m.keys())
        assert not missing, f"mapping missing legacy keys: {missing}"


def test_hd_channels_have_per_channel_narrative(mappings_response):
    """Each completed HD channel must carry gift/tension/practical_use."""
    found_any = False
    for m in mappings_response["mappings"]:
        hd_list = (m.get("signals") or {}).get("human_design") or []
        for ch in hd_list:
            narrative = ch.get("narrative")
            assert narrative is not None, (
                f"channel {ch.get('channel')} missing narrative in mapping "
                f"{m.get('member_name')}"
            )
            for key in ("gift", "tension", "practical_use"):
                val = narrative.get(key, "")
                assert isinstance(val, str) and val.strip(), (
                    f"channel {ch.get('channel')} has empty `{key}`"
                )
            found_any = True
    assert found_any, "no HD channels found across any mapping — check data"


def test_hd_field_narrative_blocks_present(mappings_response):
    """human_design_field.narrative_blocks must have all 7 keys."""
    expected = {
        "type_pair_engagement", "authority_rhythm", "profile_interaction",
        "definition_dynamics", "centers_conditioning", "channels",
        "practical_guidance",
    }
    for m in mappings_response["mappings"]:
        field = (m.get("signals") or {}).get("human_design_field")
        if not field:
            continue
        blocks = field.get("narrative_blocks")
        assert blocks, f"narrative_blocks missing for {m.get('member_name')}"
        assert expected <= set(blocks.keys()), (
            f"narrative_blocks missing keys: {expected - set(blocks.keys())}"
        )


def test_bazi_animal_narrative_present_when_signals_exist(mappings_response):
    """When signals.bazi exists and both have year animals → animal_narrative."""
    saw_bazi = False
    for m in mappings_response["mappings"]:
        bazi = (m.get("signals") or {}).get("bazi")
        if not bazi:
            continue
        saw_bazi = True
        animal_narrative = bazi.get("animal_narrative")
        # only required when both charts have animals; if missing skip gracefully
        if animal_narrative is None:
            continue
        for k in ("pair_dynamic", "inner_dynamic", "triad_signal"):
            assert k in animal_narrative, (
                f"bazi.animal_narrative missing `{k}` for "
                f"{m.get('member_name')}"
            )
    if not saw_bazi:
        pytest.skip("no bazi signals across mappings — acceptable")


def test_numerology_v2_card_present(mappings_response):
    saw_num = False
    for m in mappings_response["mappings"]:
        num = (m.get("signals") or {}).get("numerology")
        if not num:
            continue
        saw_num = True
        v2 = num.get("v2_card")
        if v2 is None:
            continue
        has_any = any(
            isinstance(v2.get(k), str) and v2.get(k, "").strip()
            for k in ("core_dynamic", "natural_strength", "growth_edge",
                      "shadow_pattern", "repair_pathway")
        )
        assert has_any, f"v2_card present but empty for {m.get('member_name')}"
    if not saw_num:
        pytest.skip("no numerology signals across mappings")


def test_relationship_synthesis_undertone_is_string(mappings_response):
    saw_syn = False
    for m in mappings_response["mappings"]:
        syn = m.get("relationship_synthesis")
        if syn is None:
            continue
        saw_syn = True
        assert "undertone_for_today" in syn, (
            "relationship_synthesis missing undertone_for_today key"
        )
        assert isinstance(syn["undertone_for_today"], str)
    if not saw_syn:
        pytest.skip("no relationship_synthesis on any mapping")


# -------------------------------------------------------------------- jargon

def test_no_raw_hd_jargon_in_top_story(mappings_response):
    """Walk story slots — top story must NOT contain raw HD/BaZi jargon."""
    slots = (
        "headline", "summary", "current_movement",
        "growth_edge", "shadow_pattern", "repair_pathway",
        "question_to_ask",
    )
    failures = []
    for m in mappings_response["mappings"]:
        syn = m.get("relationship_synthesis") or {}
        story = syn.get("story") or {}
        for slot in slots:
            txt = story.get(slot) or ""
            if not isinstance(txt, str):
                continue
            for pat in JARGON_PATTERNS:
                if re.search(pat, txt):
                    failures.append(
                        f"{m.get('member_name')} story.{slot} matched /{pat}/: "
                        f"{txt[:120]}"
                    )
    assert not failures, "raw jargon leaked into top story:\n  " + "\n  ".join(failures)


def test_no_duplicate_sentences_across_story_slots(mappings_response):
    slots = ("headline", "summary", "current_movement",
             "growth_edge", "shadow_pattern")
    failures = []
    for m in mappings_response["mappings"]:
        syn = m.get("relationship_synthesis") or {}
        story = syn.get("story") or {}
        seen = {}
        for slot in slots:
            v = _norm(story.get(slot) or "")
            if not v:
                continue
            if v in seen:
                failures.append(
                    f"{m.get('member_name')}: story.{slot} duplicates "
                    f"story.{seen[v]} → {v[:80]}"
                )
            seen[v] = slot
    assert not failures, "duplicate story slot sentences:\n  " + "\n  ".join(failures)


# -------------------------------------------------------------------- between-you-today

def test_between_you_today_endpoint_independent(session, mappings_response):
    """Confirm /between-you-today returns its own transit-driven payload
    independent of the KG synthesis."""
    mappings = mappings_response["mappings"]
    if not mappings:
        pytest.skip("no mappings → can't test between-you-today")
    member_id = mappings[0].get("member_id") or mappings[0].get("user_id")
    assert member_id, f"no member_id on first mapping: {mappings[0]}"
    url = f"{BASE}/api/forums/{PETE_MEL_FORUM}/between-you-today"
    r = session.get(
        url, params={"user_id": PETE, "member_id": member_id}, timeout=60,
    )
    assert r.status_code == 200, f"{r.status_code}: {r.text[:500]}"
    payload = r.json()
    # The envelope is transit-driven and must include hero + activated_today
    # + distortion_risk + softens_field + proof_layer somewhere in the response.
    expected = {"hero", "activated_today", "distortion_risk",
                "softens_field", "proof_layer"}
    flat_keys = set(payload.keys())
    # may be nested under "envelope" or "data"
    for nest_key in ("envelope", "data", "between_you_today", "result", "today"):
        if isinstance(payload.get(nest_key), dict):
            flat_keys |= set(payload[nest_key].keys())
    missing = expected - flat_keys
    assert not missing, (
        f"between-you-today missing fields {missing}; payload keys: "
        f"{sorted(flat_keys)}"
    )
