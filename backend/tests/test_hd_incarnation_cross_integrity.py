"""
HD Incarnation Cross Output Integrity Tests
P0 fix verification:
- /api/human-design/mechanics/{user_id} must return correct cross + canonical gates string
- FKR v1 regression: mirror chat must continue to return correct cross for self/relational queries
- Locked feature flags must remain untouched
"""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL")
assert BASE_URL, "EXPO_PUBLIC_BACKEND_URL must be set"
BASE_URL = BASE_URL.rstrip("/")

THADDEUS_ID = "69dd0b2cc92ba973f8838c11"
ISAAC_ID = "69dda348de9cb1c83c0780f8"
PETE_ID = "697f0c6abf35c0528ff06954"

EXPECTED = {
    THADDEUS_ID: {
        "incarnation_cross": "Right Angle Cross of Sleeping Phoenix",
        "incarnation_cross_gates": "20/34 | 55/59",
    },
    ISAAC_ID: {
        "incarnation_cross": "Right Angle Cross of Consciousness",
        "incarnation_cross_gates": "63/64 | 5/35",
    },
    PETE_ID: {
        "incarnation_cross": "Left Angle Cross of Migration",
        "incarnation_cross_gates": "37/40 | 5/35",
    },
}


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- Health ----------
def test_health(api):
    r = api.get(f"{BASE_URL}/api/health", timeout=30)
    assert r.status_code == 200, f"Health failed: {r.status_code} {r.text[:200]}"


# ---------- HD mechanics endpoint per-user ----------
@pytest.mark.parametrize("user_id", list(EXPECTED.keys()))
def test_hd_mechanics_cross(api, user_id):
    r = api.get(f"{BASE_URL}/api/human-design/mechanics/{user_id}", timeout=60)
    assert r.status_code == 200, f"{user_id}: status {r.status_code} body={r.text[:300]}"
    data = r.json()
    cm = data.get("core_mechanics") or data.get("data", {}).get("core_mechanics") or {}
    assert cm, f"{user_id}: core_mechanics missing in response keys={list(data.keys())}"

    expected = EXPECTED[user_id]
    actual_cross = cm.get("incarnation_cross")
    actual_gates = cm.get("incarnation_cross_gates")

    assert actual_cross == expected["incarnation_cross"], (
        f"{user_id}: incarnation_cross expected={expected['incarnation_cross']!r} got={actual_cross!r}"
    )
    assert actual_gates == expected["incarnation_cross_gates"], (
        f"{user_id}: incarnation_cross_gates expected={expected['incarnation_cross_gates']!r} got={actual_gates!r}"
    )


# ---------- Locked feature flags ----------
def test_locked_flags_untouched():
    env_path = "/app/backend/.env"
    with open(env_path) as f:
        content = f.read()
    required = {
        "INTENT_ROUTER_V2_CUTOVER": "false",
        "INTENT_ROUTER_V2_ROLLOUT_PERCENT": "10",
        "RELATIONSHIP_ORCHESTRATION_PROMPT": "false",
        "CROSS_LENS_PROMPT_SURFACE": "false",
    }
    for k, v in required.items():
        m = re.search(rf"^{k}\s*=\s*(.+)$", content, re.MULTILINE)
        assert m, f"Flag missing: {k}"
        assert m.group(1).strip() == v, f"Flag {k} expected={v} got={m.group(1).strip()}"


# ---------- FKR v1 regression: mirror chat ----------
def _post_mirror_chat(api, user_id, message):
    """Try /api/mirror/chat with common payload shapes."""
    url = f"{BASE_URL}/api/mirror/chat"
    payloads = [
        {"user_id": user_id, "message": message},
        {"user_id": user_id, "query": message},
        {"user_id": user_id, "text": message},
    ]
    last = None
    for p in payloads:
        r = api.post(url, json=p, timeout=120)
        last = r
        if r.status_code == 200:
            return r
    return last


def _extract_text(resp_json):
    if isinstance(resp_json, str):
        return resp_json
    for key in ("response", "message", "answer", "text", "content", "reply", "output"):
        v = resp_json.get(key) if isinstance(resp_json, dict) else None
        if isinstance(v, str) and v:
            return v
        if isinstance(v, dict):
            for k2 in ("text", "content", "message"):
                if isinstance(v.get(k2), str):
                    return v[k2]
    # fall back to entire stringified body
    import json as _j
    return _j.dumps(resp_json)


def test_mirror_chat_pete_about_thaddeus_returns_sleeping_phoenix(api):
    """FKR v1 regression: Pete asking about Thaddeus must return Sleeping Phoenix and NOT Sphinx."""
    r = _post_mirror_chat(api, PETE_ID, "What is Thaddeus's Incarnation Cross?")
    assert r is not None and r.status_code == 200, (
        f"mirror/chat failed: status={getattr(r,'status_code',None)} body={getattr(r,'text','')[:300]}"
    )
    text = _extract_text(r.json()).lower()
    assert "sphinx" not in text, f"Forbidden 'Sphinx' present in response: {text[:400]}"
    assert ("sleeping phoenix" in text) or ("sleeping_phoenix" in text), (
        f"Expected 'Sleeping Phoenix' in response, got: {text[:400]}"
    )


def test_mirror_chat_pete_self_returns_migration(api):
    """Pete asking about himself must surface Left Angle Cross of Migration, not generic 'Personal destiny'."""
    r = _post_mirror_chat(api, PETE_ID, "What is my Incarnation Cross?")
    assert r is not None and r.status_code == 200, (
        f"mirror/chat failed: status={getattr(r,'status_code',None)} body={getattr(r,'text','')[:300]}"
    )
    text = _extract_text(r.json())
    low = text.lower()
    assert "migration" in low, f"Expected 'Migration' in Pete self-query response: {text[:500]}"
    assert "personal destiny" not in low, f"Forbidden generic 'Personal destiny' phrase present: {text[:500]}"
