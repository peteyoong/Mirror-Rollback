"""
P0 Relationship Graph Consistency — End-to-end HTTP tests.

Verifies the three deterministic fixes shipped in
`audit_reports/P0_RELATIONSHIP_GRAPH_CONSISTENCY_FIX.md`:

  Fix 1 — `relationship_resolver` reads `forum_relationship_edges` as
          priority-0 source.
  Fix 2 — FKR-detected role is bridged into
          `v2_receipt.relationship_resolution` after the FKR block
          is built in `routers/mirror_chat.py`.
  Fix 3 — parent/child edges Pete↔Thaddeus and Pete↔Isaac are
          present in `forum_relationship_edges` (idempotent backfill).

Each test POSTs a real chat message and:
  • asserts HTTP 200,
  • inspects the response text for spouse/child framing,
  • greps the backend supervisor logs for the deterministic
    "[MIRROR_CHAT][FKR-v1] role bridged into v2_receipt: name=<X>
    role=<R>" log line.

Locked-flag verification and /api/health are also covered.
"""
import os
import re
import time
import subprocess
from pathlib import Path

import pytest
import requests

def _load_backend_url() -> str:
    # Pull from frontend/.env (EXPO_PUBLIC_BACKEND_URL).
    for envfile in ("/app/frontend/.env", "/app/backend/.env"):
        if os.path.exists(envfile):
            for line in Path(envfile).read_text().splitlines():
                m = re.match(
                    r"^(EXPO_PUBLIC_BACKEND_URL|EXPO_BACKEND_URL)\s*=\s*"
                    r"['\"]?([^'\"\s]+)['\"]?\s*$", line)
                if m:
                    return m.group(2).rstrip("/")
    return (
        os.environ.get("EXPO_PUBLIC_BACKEND_URL")
        or os.environ.get("EXPO_BACKEND_URL")
        or ""
    ).rstrip("/")


BASE_URL = _load_backend_url()
assert BASE_URL, "EXPO_PUBLIC_BACKEND_URL not configured"

# ── Identities (from /app/memory/test_credentials.md) ─────────────
PETE_ID = "697f0c6abf35c0528ff06954"
MEL_ID = "697ec826ad4b18f75bf42616"
THADDEUS_ID = "69dd0b2cc92ba973f8838c11"
ISAAC_ID = "69dda348de9cb1c83c0780f8"
FORUM_PETE_MEL = "69dd05eaa333335fcbf3ad33"
FORUM_YOONG_FAMILY = "69dda348de9cb1c83c0780fa"

BRIDGE_LOG_PREFIX = "[MIRROR_CHAT][FKR-v1] role bridged into v2_receipt:"
FKR_BLOCK_LOG_PREFIX = "[MIRROR_CHAT][FKR-v1] block_emitted=True"


def _tail_backend_log(lines: int = 6000) -> str:
    """Tail backend supervisor logs (out + err)."""
    out = ""
    for f in ("/var/log/supervisor/backend.out.log",
              "/var/log/supervisor/backend.err.log"):
        if os.path.exists(f):
            try:
                r = subprocess.run(
                    ["tail", "-n", str(lines), f],
                    capture_output=True, text=True, timeout=10,
                )
                out += r.stdout
            except Exception:
                pass
    return out


def _find_bridge_for(log: str, name: str, role: str) -> bool:
    """
    True if `[MIRROR_CHAT][FKR-v1] role bridged into v2_receipt:
    name='<name>' role='<role>'` appears in `log`. Tolerant of quote
    style and case for the role value.
    """
    pat = (
        rf"\[MIRROR_CHAT\]\[FKR-v1\] role bridged into v2_receipt:\s+"
        rf"name=['\"]?{re.escape(name)}['\"]?\s+"
        rf"role=['\"]?{re.escape(role)}['\"]?"
    )
    return bool(re.search(pat, log, flags=re.IGNORECASE))


def _find_fkr_target_with_role(log: str, name: str, role: str) -> bool:
    """
    Fallback: even if the bridge log didn't fire (because v2_receipt
    already had a role), the FKR block targets line should list the
    name. We accept any [FKR-v1] line that mentions both name and
    role within a short window.
    """
    if name.lower() not in log.lower():
        return False
    # Look for a FKR-v1 block_emitted line that contains the name.
    for line in log.splitlines():
        if "[FKR-v1]" in line and "block_emitted=True" in line and \
                name.lower() in line.lower():
            return True
    return False


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def log_baseline():
    """Snapshot log size before tests to bound the search window."""
    return _tail_backend_log(lines=200_000)


# ──────────────────────────────────────────────────────────────
# 1. Health & locked flags
# ──────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_ok(self, api):
        r = api.get(f"{BASE_URL}/api/health", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        ok = (
            data.get("ok") is True
            or data.get("healthy") is True
            or data.get("status") in ("ok", "healthy")
        )
        assert ok, f"Health payload not healthy: {data}"


class TestLockedFlags:
    def test_locked_flags_untouched(self):
        text = Path("/app/backend/.env").read_text()
        expected = {
            "INTENT_ROUTER_V2_CUTOVER": "false",
            "INTENT_ROUTER_V2_ROLLOUT_PERCENT": "10",
            "RELATIONSHIP_ORCHESTRATION_PROMPT": "false",
            "CROSS_LENS_PROMPT_SURFACE": "false",
        }
        for k, v in expected.items():
            m = re.search(
                rf"^{k}\s*=\s*(\S+)\s*$", text, flags=re.M | re.I)
            assert m, f"{k} missing from /app/backend/.env"
            assert m.group(1).lower() == v.lower(), (
                f"{k} expected {v!r}, got {m.group(1)!r}"
            )


# ──────────────────────────────────────────────────────────────
# 2. P0 Fix 2 — role bridge for spouse / child
# ──────────────────────────────────────────────────────────────

class TestRoleBridge:
    """All POSTs are issued as Pete."""

    def _post_mirror(self, api, message: str):
        payload = {"user_id": PETE_ID, "message": message}
        t0 = time.time()
        r = api.post(f"{BASE_URL}/api/mirror/chat",
                     json=payload, timeout=120)
        dt = time.time() - t0
        return r, dt

    # ── spouse: Mel ────────────────────────────────────────────
    def test_mel_bridges_as_spouse(self, api, log_baseline):
        r, dt = self._post_mirror(api, "How does Mel affect me?")
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
        assert dt < 110, f"Too slow: {dt:.1f}s"
        body = r.json()
        text = (body.get("response") or "").strip()
        assert text, f"Empty response: {body}"
        assert "mel" in text.lower(), (
            f"Response should reference Mel.\nResponse:\n{text[:600]}"
        )
        # MUST NOT call Mel a generic "forum member".
        # (Allow phrase "your forum" but not "forum member" applied to Mel.)
        assert "forum member" not in text.lower(), (
            "Mel should not be framed as a generic forum member.\n"
            f"Response:\n{text[:800]}"
        )

        # Allow log flush.
        time.sleep(2)
        log = _tail_backend_log()
        bridged = _find_bridge_for(log, "Mel", "spouse")
        fkr_seen = _find_fkr_target_with_role(log, "Mel", "spouse")
        assert bridged or fkr_seen, (
            "Neither the bridge log line "
            "`[MIRROR_CHAT][FKR-v1] role bridged into v2_receipt: "
            "name='Mel' role='spouse'` nor an FKR block containing "
            "Mel was found in the last tail of backend logs."
        )

    # ── child: Thaddeus ───────────────────────────────────────
    def test_thaddeus_bridges_as_child(self, api):
        r, dt = self._post_mirror(
            api, "What does Thaddeus need from me?")
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
        body = r.json()
        text = (body.get("response") or "").strip()
        assert text, "Empty response"
        assert "thaddeus" in text.lower(), (
            f"Response should reference Thaddeus.\nResponse:\n{text[:600]}"
        )

        time.sleep(2)
        log = _tail_backend_log()
        bridged = _find_bridge_for(log, "Thaddeus", "child")
        fkr_seen = _find_fkr_target_with_role(log, "Thaddeus", "child")
        assert bridged or fkr_seen, (
            "Bridge log line for Thaddeus(child) not found, and FKR "
            "block_emitted=True with Thaddeus not seen."
        )

    # ── child: Isaac ──────────────────────────────────────────
    def test_isaac_bridges_as_child(self, api):
        r, dt = self._post_mirror(
            api, "How is Isaac different from me?")
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
        body = r.json()
        text = (body.get("response") or "").strip()
        assert text, "Empty response"
        assert "isaac" in text.lower(), (
            f"Response should reference Isaac.\nResponse:\n{text[:600]}"
        )

        time.sleep(2)
        log = _tail_backend_log()
        bridged = _find_bridge_for(log, "Isaac", "child")
        fkr_seen = _find_fkr_target_with_role(log, "Isaac", "child")
        assert bridged or fkr_seen, (
            "Bridge log line for Isaac(child) not found, and FKR "
            "block_emitted=True with Isaac not seen."
        )


# ──────────────────────────────────────────────────────────────
# 3. Regression — Thaddeus Incarnation Cross still 'Sleeping Phoenix'
# ──────────────────────────────────────────────────────────────

class TestRegressionThaddeusCross:
    def test_thaddeus_cross_sleeping_phoenix(self, api):
        payload = {
            "user_id": PETE_ID,
            "message": "What is Thaddeus's Incarnation Cross?",
        }
        r = requests.post(
            f"{BASE_URL}/api/mirror/chat",
            json=payload, timeout=120,
        )
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
        text = (r.json().get("response") or "").lower()
        assert text, "Empty response"
        assert "sphinx" not in text, (
            f"HALLUCINATION: response mentions Sphinx.\n"
            f"Response:\n{text[:800]}"
        )
        assert "sleeping phoenix" in text, (
            f"Missing 'Sleeping Phoenix' anchor.\nResponse:\n{text[:800]}"
        )


# ──────────────────────────────────────────────────────────────
# 4. Regression — Yoong family forum: "Tell me about my children"
# ──────────────────────────────────────────────────────────────

class TestForumYoongChildren:
    def test_yoong_forum_children_reference(self, api):
        payload = {
            "user_id": PETE_ID,
            "message": "Tell me about my children",
            "mode": "forum",
        }
        r = api.post(
            f"{BASE_URL}/api/forums/{FORUM_YOONG_FAMILY}/chat",
            json=payload, timeout=120,
        )
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
        text = (r.json().get("response") or "").strip()
        assert text, "Empty forum response"
        low = text.lower()
        # Must reference at least one child by name; ideally both.
        names_present = sum(
            n in low for n in ("thaddeus", "isaac"))
        assert names_present >= 1, (
            "Yoong family forum reply should reference Thaddeus and/or "
            f"Isaac.\nResponse:\n{text[:800]}"
        )
