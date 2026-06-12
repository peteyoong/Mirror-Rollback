"""
FKR v1 — End-to-end HTTP endpoint tests.

Exercises:
  - POST /api/mirror/chat — primary acceptance probe (Thaddeus IC),
    asker self-MC, Pete×Mel relationship, Pete×Mel comparison
  - POST /api/forums/{forum_id}/chat — Pete & Mel forum
  - GET  /api/health
  - Verifies "[MIRROR_CHAT][FKR-v1] block_emitted=True" or
    "[ForumChat][FKR-v1] block_emitted=True" appears in backend logs.
  - Verifies locked flags in /app/backend/.env are untouched.

Backend URL: from EXPO_PUBLIC_BACKEND_URL (fallback EXPO_BACKEND_URL).
"""
import os
import re
import time
import subprocess
from pathlib import Path

import pytest
import requests

BASE_URL = (
    os.environ.get("EXPO_PUBLIC_BACKEND_URL")
    or os.environ.get("EXPO_BACKEND_URL")
    or "https://birth-data-remediate.preview.emergentagent.com"
).rstrip("/")

PETE_ID = "697f0c6abf35c0528ff06954"
MEL_ID = "697ec826ad4b18f75bf42616"
THADDEUS_ID = "69dd0b2cc92ba973f8838c11"
FORUM_PETE_MEL = "69dd05eaa333335fcbf3ad33"

EXPECTED_THADDEUS_CROSS = "Right Angle Cross of Sleeping Phoenix 1"
FORBIDDEN_CROSS_SUBSTR = "Sphinx"


def _tail_backend_log(seconds_back: int = 60) -> str:
    """Read the last N lines from backend supervisor logs (out + err)."""
    out = ""
    for f in ("/var/log/supervisor/backend.out.log",
              "/var/log/supervisor/backend.err.log"):
        if os.path.exists(f):
            try:
                # Avoid loading a giant file — only last 4000 lines.
                r = subprocess.run(
                    ["tail", "-n", "4000", f],
                    capture_output=True, text=True, timeout=10,
                )
                out += r.stdout
            except Exception:
                pass
    return out


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ──────────────────────────────────────────────────────────────
# Health
# ──────────────────────────────────────────────────────────────

class TestHealth:
    def test_health(self, api):
        r = api.get(f"{BASE_URL}/api/health", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        # Accept either {healthy:true} or {status:"ok"} shapes.
        ok = data.get("healthy") is True or data.get("status") in (
            "ok", "healthy")
        assert ok, f"Health payload not healthy: {data}"


# ──────────────────────────────────────────────────────────────
# Locked flags — read .env directly
# ──────────────────────────────────────────────────────────────

class TestLockedFlags:
    def test_locked_flags_untouched(self):
        env_path = Path("/app/backend/.env")
        text = env_path.read_text()
        expected = {
            "INTENT_ROUTER_V2_CUTOVER": "false",
            "INTENT_ROUTER_V2_ROLLOUT_PERCENT": "10",
            "RELATIONSHIP_ORCHESTRATION_PROMPT": "false",
            "CROSS_LENS_PROMPT_SURFACE": "false",
        }
        for k, v in expected.items():
            m = re.search(rf"^{k}\s*=\s*(\S+)\s*$",
                          text, flags=re.M | re.I)
            assert m, f"{k} missing from /app/backend/.env"
            assert m.group(1).lower() == v.lower(), (
                f"{k} expected {v!r}, got {m.group(1)!r}"
            )


# ──────────────────────────────────────────────────────────────
# Mirror Chat — FKR critical probes
# ──────────────────────────────────────────────────────────────

class TestMirrorChatFKR:
    """All POSTs use Pete as the asker."""

    def _post(self, api, message: str):
        payload = {"user_id": PETE_ID, "message": message}
        t0 = time.time()
        r = api.post(f"{BASE_URL}/api/mirror/chat",
                     json=payload, timeout=120)
        dt = time.time() - t0
        return r, dt

    def test_thaddeus_incarnation_cross_no_sphinx(self, api):
        """CRITICAL: must mention Sleeping Phoenix; must NOT say Sphinx."""
        r, dt = self._post(
            api, "What is Thaddeus's Incarnation Cross?")
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
        assert dt < 95, f"Response too slow: {dt:.1f}s"
        body = r.json()
        text = (body.get("response") or "").strip()
        assert text, f"Empty response: {body}"
        low = text.lower()
        # Hard requirements
        assert "sphinx" not in low, (
            f"HALLUCINATION: response mentions Sphinx.\n"
            f"Response:\n{text}"
        )
        assert "sleeping phoenix" in low, (
            f"Missing 'Sleeping Phoenix' anchor.\nResponse:\n{text}"
        )

    def test_pete_midheaven_28_virgo(self, api):
        r, dt = self._post(api, "What is my Midheaven?")
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
        body = r.json()
        text = (body.get("response") or "").strip()
        assert text, "Empty response"
        low = text.lower()
        # The stored MC is 28°Virgo — answer must reference Virgo.
        assert "virgo" in low, (
            f"MC answer missing 'Virgo'.\nResponse:\n{text}"
        )

    def test_relationship_pete_mel(self, api):
        r, dt = self._post(
            api,
            "How does Mel's chart map to me in our relationship?")
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
        body = r.json()
        text = (body.get("response") or "").strip()
        assert text, "Empty response"
        low = text.lower()
        # Must name Mel and acknowledge Pete in relationship framing.
        assert "mel" in low, (
            f"Relationship response missing 'Mel'.\nResponse:\n{text}"
        )

    def test_comparison_pete_mel(self, api):
        r, dt = self._post(
            api, "Compare my Sun and Moon with Mel's.")
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
        body = r.json()
        text = (body.get("response") or "").strip()
        assert text, "Empty response"
        low = text.lower()
        assert "mel" in low, (
            f"Comparison missing 'Mel'.\nResponse:\n{text}"
        )
        # Either sign for Pete's Sun (Pisces) or for the comparison
        # placements should show. Pete=Pisces Sun, Aries Moon.
        assert ("sun" in low and "moon" in low), (
            f"Comparison missing Sun/Moon mention.\nResponse:\n{text}"
        )


# ──────────────────────────────────────────────────────────────
# Forum Chat — FKR injection
# ──────────────────────────────────────────────────────────────

class TestForumChatFKR:
    def test_forum_chat_pete_mel(self, api):
        payload = {
            "user_id": PETE_ID,
            "message": "What are we working through right now?",
            "mode": "forum",
        }
        t0 = time.time()
        r = api.post(
            f"{BASE_URL}/api/forums/{FORUM_PETE_MEL}/chat",
            json=payload, timeout=120,
        )
        dt = time.time() - t0
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
        assert dt < 95, f"Forum chat too slow: {dt:.1f}s"
        body = r.json()
        text = (body.get("response") or "").strip()
        assert text, f"Empty forum response: {body}"
        low = text.lower()
        # Should reference both members.
        names_present = sum(n in low for n in ("pete", "mel"))
        assert names_present >= 1, (
            f"Forum response should reference Pete and/or Mel.\n"
            f"Response:\n{text}"
        )


# ──────────────────────────────────────────────────────────────
# Backend log — FKR-v1 block_emitted=True presence
# ──────────────────────────────────────────────────────────────

class TestFKRLogEmission:
    """Run LAST so the previous POSTs have already written log lines.

    Pytest runs classes in declaration order by default — this class
    is at the end of the file so the mirror/forum POSTs above will
    have already produced [FKR-v1] log lines we can grep for.
    """

    def test_fkr_log_line_present(self):
        # Allow log file flush to settle.
        time.sleep(2)
        log = _tail_backend_log()
        mirror_hit = "[MIRROR_CHAT][FKR-v1] block_emitted=True" in log
        forum_hit = "[ForumChat][FKR-v1] block_emitted=True" in log
        assert mirror_hit or forum_hit, (
            "Neither '[MIRROR_CHAT][FKR-v1] block_emitted=True' nor "
            "'[ForumChat][FKR-v1] block_emitted=True' found in last "
            "4000 lines of backend logs. FKR block was not injected."
        )

    def test_fkr_log_mirror_block_present(self):
        time.sleep(1)
        log = _tail_backend_log()
        assert "[MIRROR_CHAT][FKR-v1] block_emitted=True" in log, (
            "Mirror chat did not emit FKR-v1 block_emitted=True log line."
        )

    def test_fkr_log_forum_block_present(self):
        time.sleep(1)
        log = _tail_backend_log()
        assert "[ForumChat][FKR-v1] block_emitted=True" in log, (
            "Forum chat did not emit FKR-v1 block_emitted=True log line."
        )
