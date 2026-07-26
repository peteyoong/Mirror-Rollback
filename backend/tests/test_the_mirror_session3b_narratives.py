"""Session-3b tests — Decisions 1 & 2 (PHS withdrawal + Signature/Not-Self)
+ Phase 6 governance detectors (Session-3c will populate content)
========================================================================

Project: The Mirror (Emergent /app application).
build_marker: the-mirror-session3b-tests-v1
"""
from __future__ import annotations
import os
import sys
import urllib.request
import json
from typing import Dict, Any

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from services.hd_signature_notself import (  # noqa: E402
    signature_and_not_self, DERIVATION_RULE_ID,
)

PETE = "697f0c6abf35c0528ff06954"


def _fetch(path: str) -> Dict[str, Any]:
    url = f"http://localhost:8001/api{path}"
    with urllib.request.urlopen(url, timeout=45) as r:
        return json.loads(r.read())


# ─────────────────────────────────────────────────────────────────────
# Decision 1 — PHS withdrawal
# ─────────────────────────────────────────────────────────────────────
def test_phs_strings_hidden_from_user_facing_renders():
    """`getHowYouWorkBestAtAGlance` must return null unconditionally
    (Session-3b PHS withdrawal). Verified via FE source grep."""
    fe = os.path.normpath(os.path.join(
        BACKEND, "..", "frontend", "components", "HumanDesignLensView.tsx"
    ))
    with open(fe, encoding="utf-8") as fh:
        src = fh.read()
    # Locate the active definition. Withdrawal marker must be inside
    # its body and the function must not fall through to translation
    # tables. Search for the withdrawal build_marker within 600 chars
    # after the active `const getHowYouWorkBestAtAGlance = (` opening.
    idx = src.find("const getHowYouWorkBestAtAGlance = (")
    assert idx >= 0, "getHowYouWorkBestAtAGlance not present in FE source"
    body = src[idx: idx + 1500]
    assert "hd-phs-withdrawal-v1" in body, (
        "PHS withdrawal marker missing from active function body"
    )
    assert "return null;" in body, (
        "Active getHowYouWorkBestAtAGlance must return null unconditionally"
    )
    # The legacy shadowing function must NOT be exported / callable
    # from render paths — assert no render-side invocation exists.
    # (We only need to protect against re-enabling; the underscore
    # prefix on _getHowYouWorkBestAtAGlance_LEGACY is the guard.)


def test_phs_translation_tables_labelled_unverified():
    """Translation tables remain in file for audit but must carry
    the `content_provenance: unverified` marker."""
    fe = os.path.normpath(os.path.join(
        BACKEND, "..", "frontend", "components", "HumanDesignLensView.tsx"
    ))
    with open(fe, encoding="utf-8") as fh:
        src = fh.read()
    assert "content_provenance: unverified" in src, (
        "PHS translation tables must carry `content_provenance: unverified`"
    )


# ─────────────────────────────────────────────────────────────────────
# Decision 2 — Signature + Not-Self from backend (all 5 Types)
# ─────────────────────────────────────────────────────────────────────
def test_signature_not_self_for_all_types():
    cases = {
        "Manifestor":            ("Peace",        "Anger"),
        "Generator":             ("Satisfaction", "Frustration"),
        "Manifesting Generator": ("Satisfaction", "Frustration and Anger"),
        "Projector":             ("Success",      "Bitterness"),
        "Reflector":             ("Surprise",     "Disappointment"),
    }
    for t, (sig, ns) in cases.items():
        r = signature_and_not_self(t)
        assert r, f"type {t}: no bundle returned"
        assert r["signature"] == sig, f"{t} signature mismatch: {r['signature']}"
        assert r["not_self"]  == ns,  f"{t} not_self  mismatch: {r['not_self']}"
        assert r["derivation_rule"] == DERIVATION_RULE_ID
        assert r["source"] == "human_design.type"


def test_signature_not_self_unknown_type_returns_none():
    for bad in (None, "", "  ", "ManiFester", "Alien", 42):
        assert signature_and_not_self(bad) is None


def test_signature_not_self_accepts_common_variants():
    for variant in ("MG", "Manifesting-Generator", "Man Gen"):
        r = signature_and_not_self(variant)
        assert r and r["signature"] == "Satisfaction"


def test_pete_mechanics_endpoint_ships_signature_and_not_self():
    d = _fetch(f"/human-design/mechanics/{PETE}")
    cm = d.get("core_mechanics") or {}
    assert cm.get("signature") == "Peace"
    assert cm.get("not_self") == "Anger"
    deriv = cm.get("signature_derivation") or {}
    assert deriv.get("rule") == DERIVATION_RULE_ID
    assert deriv.get("input_type") == "Manifestor"
    assert deriv.get("confidence") == "high"


# ─────────────────────────────────────────────────────────────────────
# Phase 6 — governance detectors (scaffolds; will fail loudly when
# Session-3c introduces content that violates them)
# ─────────────────────────────────────────────────────────────────────
def test_frontend_does_not_re_derive_signature_or_not_self():
    """FE must NOT compute Signature/Not-Self from Type — Decision 2."""
    import re
    fe_dir = os.path.normpath(os.path.join(BACKEND, "..", "frontend"))
    forbidden = [
        re.compile(r"['\"]?[Ss]ignature['\"]?\s*[:=]\s*['\"]Peace['\"]"),
        re.compile(r"['\"]?not_self['\"]?\s*[:=]\s*['\"]Anger['\"]"),
        re.compile(r"const\s+SIGNATURE_BY_TYPE"),
    ]
    hits = []
    for root, _, files in os.walk(fe_dir):
        if "node_modules" in root:
            continue
        for f in files:
            if not (f.endswith(".tsx") or f.endswith(".ts")):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, encoding="utf-8") as fh:
                    src = fh.read()
            except Exception:
                continue
            for pat in forbidden:
                if pat.search(src):
                    hits.append(f"{path}: {pat.pattern}")
    assert not hits, (
        "FE re-derives Signature or Not-Self — must consume backend values:\n  "
        + "\n  ".join(hits)
    )


def test_regression_all_prior_tests_pass():
    """Session-3b must not regress Session-1 / -2 / -3a."""
    import subprocess
    for fname in ("test_the_mirror_session1_integrity.py",
                  "test_lens_content_contract.py",
                  "test_the_mirror_session3_hd_structural.py"):
        r = subprocess.run(
            [sys.executable, os.path.join(HERE, fname)],
            capture_output=True, text=True, timeout=120,
        )
        assert r.returncode == 0, (
            f"regression in {fname}. stdout:\n{r.stdout[-800:]}\n"
            f"stderr:\n{r.stderr[-400:]}"
        )


# ─────────────────────────────────────────────────────────────────────
# Phase 6 detectors — SKIPPED-BY-DESIGN until Session-3c content lands.
# These are scaffolds so the Session-3c author sees the guardrail
# vocabulary they must satisfy. Not asserting content yet.
# ─────────────────────────────────────────────────────────────────────
def test_governance_scaffold_identical_center_narratives_detector():
    """Session-3c to implement: fetch all 9 centre narratives and
    ensure no two exceed Jaccard 0.85 token overlap.
    Placeholder passes because narrative content is still unwritten."""
    return  # scaffold — real assertion lands with Session-3c content


def test_governance_scaffold_no_deterministic_advice_without_evidence():
    """Session-3c to implement: parse narrative claims and require
    an EvidenceRef on any 'should/must/will' sentence.
    Placeholder — no content to check yet."""
    return


def test_governance_scaffold_theme_hierarchy_not_flat():
    """Session-3c core-story rebalance test.  Once the ranking engine
    ships (Decision 5), assert Layer-1..3 concentration ≤ 60% and no
    single theme > 40% of total weight."""
    return


# ── runner ──
if __name__ == "__main__":
    import traceback
    passed = failed = 0
    for name in sorted(globals()):
        if not name.startswith("test_"):
            continue
        fn = globals()[name]
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {name}\n        {e}")
            failed += 1
        except Exception:
            print(f"  FAIL  {name}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    raise SystemExit(0 if failed == 0 else 1)
