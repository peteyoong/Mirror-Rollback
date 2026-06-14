"""
Slice A — Forum Chat UX Simplification + Auto Relationship Context Resolution (FKR v1)
HTTP-level regression suite (secondary independent verification).

Goal: confirm the 7 scenarios in the review_request return 200 from
POST /api/mirror/chat and that no internal taxonomy strings leak into the
LLM-visible response text.

Auto-detected frames (SELF, MEMBER, FORUM, PAIRWISE, MULTI_PERSON,
AMBIGUOUS, scope_class, forum_intent, covenant_partner, steward_guardian)
must remain inside the receipt envelope and never appear in
`response` / `message` text.
"""
import os
import re
import time
import pytest
import requests


def _load_base_url() -> str:
    for k in ("EXPO_PUBLIC_BACKEND_URL", "EXPO_BACKEND_URL"):
        v = os.environ.get(k)
        if v:
            return v.rstrip("/")
    # Fallback: read frontend/.env (canonical preview URL)
    env_path = "/app/frontend/.env"
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    return ""


BASE_URL = _load_base_url()
assert BASE_URL, "EXPO_PUBLIC_BACKEND_URL not configured"

PETE_ID = "697f0c6abf35c0528ff06954"
MEL_ID = "697ec826ad4b18f75bf42616"
THADDEUS_ID = "69dd0b2cc92ba973f8838c11"
ISAAC_ID = "69dda348de9cb1c83c0780f8"

# Internal taxonomy tokens that must NOT leak into LLM-visible response text.
LEAK_TOKENS = [
    "PAIRWISE",
    "MULTI_PERSON",
    "AMBIGUOUS",
    "scope_class",
    "forum_intent",
    "covenant_partner",
    "steward_guardian",
]

TIMEOUT_S = 120


@pytest.fixture(scope="module")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _extract_response_text(body: dict) -> str:
    """Pull all LLM-visible surfaces. Receipts are internal and excluded."""
    surfaces = []
    for k in ("response", "message", "answer", "text", "reply", "content"):
        v = body.get(k)
        if isinstance(v, str):
            surfaces.append(v)
    return "\n".join(surfaces)


def _assert_no_leakage(text: str, scenario: str):
    found = [t for t in LEAK_TOKENS if re.search(rf"\b{re.escape(t)}\b", text)]
    assert not found, (
        f"[{scenario}] Internal taxonomy leaked into LLM-visible text: {found}. "
        f"Snippet: {text[:300]!r}"
    )


def _post_chat(api_client, body: dict, scenario: str) -> dict:
    url = f"{BASE_URL}/api/mirror/chat"
    r = api_client.post(url, json=body, timeout=TIMEOUT_S)
    assert r.status_code == 200, (
        f"[{scenario}] expected 200, got {r.status_code}: {r.text[:500]}"
    )
    data = r.json()
    assert isinstance(data, dict), f"[{scenario}] response is not JSON object"
    # response_model=MirrorChatResponse → expect at least one text surface
    text = _extract_response_text(data)
    assert text.strip(), f"[{scenario}] empty response text. Keys: {list(data.keys())}"
    _assert_no_leakage(text, scenario)
    return data


# ── Scenario 1 (Slice 2 regression): explicit about_person_id=MEL ────────
def test_s1_tell_me_about_mel_with_about_person_id(api_client):
    body = {
        "user_id": PETE_ID,
        "message": "Tell me about Mel",
        "about_person_id": MEL_ID,
    }
    _post_chat(api_client, body, "S1 about_person_id=MEL")


# ── Scenario 2 (Slice A name-only): no about_person_id provided ──────────
def test_s2_thaddeus_name_only_resolution(api_client):
    body = {
        "user_id": PETE_ID,
        "message": "What does Thaddeus need from me?",
    }
    _post_chat(api_client, body, "S2 name-only Thaddeus")


# ── Scenario 3: SELF baseline ────────────────────────────────────────────
def test_s3_tell_me_about_myself_self(api_client):
    body = {
        "user_id": PETE_ID,
        "message": "Tell me about myself",
    }
    _post_chat(api_client, body, "S3 SELF baseline")


# ── Scenario 4: PAIRWISE (Mel + Thaddeus) ────────────────────────────────
def test_s4_pairwise_mel_thaddeus(api_client):
    body = {
        "user_id": PETE_ID,
        "message": "How are Mel and Thaddeus affecting each other?",
    }
    _post_chat(api_client, body, "S4 pairwise Mel+Thaddeus")


# ── Scenario 5: MULTI_PERSON ('my children') ─────────────────────────────
def test_s5_multi_person_my_children(api_client):
    body = {
        "user_id": PETE_ID,
        "message": "What about my children right now?",
    }
    _post_chat(api_client, body, "S5 multi-person my children")


# ── Scenario 6: FORUM whole ─────────────────────────────────────────────
def test_s6_forum_whole_energy(api_client):
    body = {
        "user_id": PETE_ID,
        "message": "What's the energy of this forum as a whole?",
    }
    _post_chat(api_client, body, "S6 forum whole energy")


# ── Scenario 7: explicit no-leakage cross-check (apostrophe variant) ─────
def test_s7_no_leakage_explicit_check(api_client):
    body = {
        "user_id": PETE_ID,
        "message": "What is the energy of this forum as a whole?",
    }
    _post_chat(api_client, body, "S7 forum whole energy variant")
