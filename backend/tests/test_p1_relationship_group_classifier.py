"""
P1 Relationship Orchestration Readiness — Group Resolution + Classifier
Expansion — End-to-end HTTP tests.

Verifies the two display/classification-layer changes shipped in
`audit_reports/P1_RELATIONSHIP_GROUP_AND_CLASSIFIER.md`:

  A. classify_query() gained patterns for natural-language
     relationship/forum phrasings.
  B. resolve_targets() expands kinship plurals ("the boys", "my kids",
     "the children", "which child", "our family", ...) into the
     underlying set of forum_relationship_edges-typed people.

Each test POSTs a real chat message against /api/mirror/chat, asserts
HTTP 200, and greps the backend supervisor logs for the deterministic
[MIRROR_CHAT][FKR-v1] block_emitted=True line — inspecting the
`targets=[...]` and `modes=[...]` payload to confirm the new behaviour
is fully wired end-to-end.

Locked flags and regression checks are also covered.
"""
import os
import re
import time
import subprocess
from pathlib import Path

import pytest
import requests


def _load_backend_url() -> str:
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
FORUM_YOONG_FAMILY = "69dda348de9cb1c83c0780fa"

FKR_BLOCK_LINE = "[MIRROR_CHAT][FKR-v1] block_emitted=True"


def _tail_backend_log(lines: int = 8000) -> str:
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


def _latest_fkr_block_line(log: str) -> str | None:
    """Return the most recent `[FKR-v1] block_emitted=True ...` line."""
    last = None
    for line in log.splitlines():
        if FKR_BLOCK_LINE in line:
            last = line
    return last


def _parse_targets(line: str) -> list[str]:
    m = re.search(r"targets=\[(.*?)\]\s+chars=", line)
    if not m:
        # tolerate no chars suffix (False branch)
        m = re.search(r"targets=\[(.*?)\]", line)
    if not m:
        return []
    inside = m.group(1).strip()
    if not inside:
        return []
    return [
        s.strip().strip("'").strip('"')
        for s in inside.split(",")
    ]


def _parse_modes(line: str) -> list[str]:
    m = re.search(r"modes=\[(.*?)\]", line)
    if not m:
        # tolerate enum-style {RELATIONSHIP, COMPARISON}
        m = re.search(r"modes=\{(.*?)\}", line)
    if not m:
        return []
    inside = m.group(1).strip()
    if not inside:
        return []
    tokens = [
        s.strip().strip("'").strip('"')
        for s in inside.split(",")
    ]
    return [t.split(".")[-1].upper() for t in tokens if t]


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _post_chat(api, message: str, user_id: str = PETE_ID,
               forum_id: str | None = None):
    payload = {"user_id": user_id, "message": message}
    if forum_id:
        payload["forum_id"] = forum_id
    t0 = time.time()
    r = api.post(
        f"{BASE_URL}/api/mirror/chat",
        json=payload, timeout=180,
    )
    dt = time.time() - t0
    return r, dt


# ──────────────────────────────────────────────────────────────
# 0. Health & locked flags
# ──────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_ok(self, api):
        r = api.get(f"{BASE_URL}/api/health", timeout=15)
        assert r.status_code == 200, r.text


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
# 1. Group expansion — "the boys", "which child", "our family"
# ──────────────────────────────────────────────────────────────

class TestGroupExpansion:

    def test_the_boys_differ_emotionally(self, api):
        r, dt = _post_chat(api, "How do the boys differ emotionally?")
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
        text = (r.json().get("response") or "").lower()
        assert text, "Empty response"

        time.sleep(2)
        log = _tail_backend_log()
        line = _latest_fkr_block_line(log)
        assert line, (
            "No `[FKR-v1] block_emitted=True` log line found.\n"
            f"Tail snippet:\n{log[-2000:]}"
        )
        targets = _parse_targets(line)
        assert "Thaddeus" in targets and "Isaac" in targets, (
            "FKR targets MUST include BOTH 'Thaddeus' AND 'Isaac' "
            f"after group expansion. Got targets={targets!r}\n"
            f"Line: {line}"
        )
        # The LLM response should reference both children by name.
        assert "thaddeus" in text and "isaac" in text, (
            "Response should reference both children by name (not just "
            f"'the boys' generically). Got:\n{text[:800]}"
        )

    def test_which_child_more_like_me(self, api):
        r, _ = _post_chat(api, "Which child is more like me?")
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
        text = (r.json().get("response") or "").lower()
        assert text, "Empty response"

        time.sleep(2)
        log = _tail_backend_log()
        line = _latest_fkr_block_line(log)
        assert line, "No FKR block_emitted log line found"
        targets = _parse_targets(line)
        assert "Thaddeus" in targets and "Isaac" in targets, (
            "FKR targets MUST include both 'Thaddeus' and 'Isaac' "
            f"for 'Which child ...' Got targets={targets!r}\n"
            f"Line: {line}"
        )
        assert "thaddeus" in text and "isaac" in text, (
            "Response should compare both children by name. "
            f"Got:\n{text[:800]}"
        )

    def test_our_family(self, api):
        r, _ = _post_chat(api, "What is happening in our family?")
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
        text = (r.json().get("response") or "").lower()
        assert text, "Empty response"

        time.sleep(2)
        log = _tail_backend_log()
        line = _latest_fkr_block_line(log)
        assert line, "No FKR block_emitted log line found"
        targets = _parse_targets(line)
        for required in ("Mel", "Thaddeus", "Isaac"):
            assert required in targets, (
                f"FKR targets MUST include {required!r} for "
                f"'our family' expansion. Got targets={targets!r}\n"
                f"Line: {line}"
            )
        # Response should reference all three family members.
        for name in ("mel", "thaddeus", "isaac"):
            assert name in text, (
                f"Response should reference {name!r}. "
                f"Got:\n{text[:800]}"
            )


# ──────────────────────────────────────────────────────────────
# 2. Classifier expansion — RELATIONSHIP & FORUM_DYNAMICS modes
# ──────────────────────────────────────────────────────────────

class TestClassifierExpansion:

    def test_thaddeus_need_from_me_relationship_mode(self, api):
        r, _ = _post_chat(api, "What does Thaddeus need from me?")
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"

        time.sleep(2)
        log = _tail_backend_log()
        line = _latest_fkr_block_line(log)
        assert line, "No FKR block_emitted=True log line found"
        modes = _parse_modes(line)
        assert "RELATIONSHIP" in modes, (
            "Modes MUST include RELATIONSHIP after classifier "
            f"expansion. Got modes={modes!r}\nLine: {line}"
        )
        targets = _parse_targets(line)
        assert "Thaddeus" in targets, (
            "Thaddeus should be a target. "
            f"Got targets={targets!r}"
        )

    def test_group_blind_spot_forum_dynamics(self, api):
        r, _ = _post_chat(
            api, "What is this group's blind spot?",
            forum_id=FORUM_YOONG_FAMILY,
        )
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"

        time.sleep(2)
        log = _tail_backend_log()
        line = _latest_fkr_block_line(log)
        # The FKR block may or may not emit if there are no targets;
        # we need either block_emitted=True OR block_emitted=False
        # — check both.
        if not line:
            # fall back to False-branch line
            for ln in reversed(log.splitlines()):
                if "[FKR-v1] block_emitted=False" in ln:
                    line = ln
                    break
        assert line, "No FKR block_emitted log line found at all"
        modes = _parse_modes(line)
        assert "FORUM_DYNAMICS" in modes, (
            "Modes MUST include FORUM_DYNAMICS for "
            "'What is this group's blind spot?'. "
            f"Got modes={modes!r}\nLine: {line}"
        )


# ──────────────────────────────────────────────────────────────
# 3. Regression — must remain intact after P1
# ──────────────────────────────────────────────────────────────

class TestRegressionThaddeusCross:
    def test_thaddeus_cross_sleeping_phoenix(self, api):
        r, _ = _post_chat(
            api, "What is Thaddeus's Incarnation Cross?")
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
        text = (r.json().get("response") or "").lower()
        assert text, "Empty response"
        assert "sphinx" not in text, (
            f"HALLUCINATION: response mentions Sphinx.\n"
            f"Response:\n{text[:800]}"
        )
        assert "sleeping phoenix" in text, (
            f"Missing 'Sleeping Phoenix' anchor.\n"
            f"Response:\n{text[:800]}"
        )


class TestRegressionMelSpouse:
    def test_mel_treated_as_spouse(self, api):
        r, _ = _post_chat(api, "How does Mel affect me?")
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
        text = (r.json().get("response") or "").lower()
        assert "mel" in text, "Response must mention Mel"
        assert "forum member" not in text, (
            "Mel should NOT be framed as a generic forum member.\n"
            f"Response:\n{text[:800]}"
        )

        time.sleep(2)
        log = _tail_backend_log()
        # Either bridge fired or FKR block lists Mel with spouse role
        bridge_pat = re.compile(
            r"\[MIRROR_CHAT\]\[FKR-v1\] role bridged into v2_receipt:"
            r".*name=['\"]?Mel['\"]?\s+role=['\"]?spouse['\"]?",
            flags=re.IGNORECASE,
        )
        bridge_hit = bool(bridge_pat.search(log))
        line = _latest_fkr_block_line(log)
        mel_in_fkr = bool(line and "Mel" in _parse_targets(line))
        assert bridge_hit or mel_in_fkr, (
            "Mel should be bridged as spouse OR appear in FKR targets."
        )
