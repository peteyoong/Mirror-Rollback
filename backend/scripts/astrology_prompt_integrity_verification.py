#!/usr/bin/env python3
"""
Astrology Prompt Integrity — End-to-End Verification Sprint
============================================================

Verifies that the recent prompt-layer fixes (MC, Descendant, Chiron, IC)
are *actually* affecting live responses, not just appearing in
telemetry. Read-only — no DB writes, no code changes.

For each of the 4 reference users (Pete, Mel, Isaac, Jaan) and each
verification category (MC / Descendant / Chiron / IC) the script:

  1. Reads the stored chart and extracts MC / DC / IC / Chiron values.
  2. Re-runs the prompt-builder snippet *byte-for-byte from
     routers/mirror_chat.py* (lines 264-437) against the stored chart
     to deterministically reproduce the chart-points injected into the
     system prompt.
  3. Makes a live HTTP POST to /api/mirror/chat with a probe message.
  4. Captures the response and looks for:
     - direct mention of the expected sign / house
     - sign-substitution leakage (Sun sign showing up where MC should
       have dominated, Ascendant where Descendant should, etc.)
  5. Emits a pass/fail matrix + before/after evidence into
     /app/backend/audit_reports/ASTROLOGY_PROMPT_INTEGRITY_VERIFICATION.md
"""
import asyncio
import json
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = "http://localhost:8001"
ENDPOINT = f"{BACKEND_URL}/api/mirror/chat"

USERS: Dict[str, str] = {
    "Pete":  "697f0c6abf35c0528ff06954",
    "Mel":   "697ec826ad4b18f75bf42616",
    "Isaac": "69dda348de9cb1c83c0780f8",
    "Jaan":  "69894cc932380843ba87d121",
}

# Probe matrix — each row: (category, intent_key, message)
PROBES: List[Tuple[str, str, str]] = [
    # MC — career / leadership / public role / vocation
    ("MC", "career_contribution", "What am I here to contribute?"),
    ("MC", "public_role",         "What is my public role?"),
    ("MC", "leadership_style",    "What is my leadership style?"),
    ("MC", "becoming",            "What am I becoming?"),
    # Descendant — relationship axis
    ("DC", "partnership_seek",    "What do I seek in partnership?"),
    ("DC", "relationship_pattern","What relationship pattern keeps repeating?"),
    # Chiron — healing / wound / repeating
    ("Chiron", "wound",           "What wound am I working through?"),
    ("Chiron", "healing",         "What am I here to heal?"),
    ("Chiron", "repeating_life",  "What keeps repeating in my life?"),
    # IC — home / family / roots
    ("IC", "home_meaning",        "What does home mean to me?"),
    ("IC", "roots_pattern",       "What patterns come from my roots?"),
    ("IC", "childhood",           "What am I carrying from childhood?"),
]

SIGN_TOKENS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius",
    "Pisces", "Ophiuchus",
]


# ──────────────────────────────────────────────────────────────────
# (1) Mirror of the prompt-builder logic in routers/mirror_chat.py
#     L264-L437 — kept byte-equivalent so we know exactly what the
#     server would inject for the chart points we care about.
# ──────────────────────────────────────────────────────────────────

def build_chart_point_injection(chart: Dict[str, Any], message: str) -> Dict[str, Any]:
    """Return a dict with `injected_points` (list[str]) + `triggers_seen`
    + `weighting_blocks` for the 4 chart-point fixes (MC, DC, IC, Chiron)
    + the developmental-axis weighting. Mirrors mirror_chat.py exactly."""
    out = {
        "injected_points": [],
        "weighting_blocks": [],
        "triggers_seen": {"MC": False, "DC": False, "IC": False, "purpose": False},
        "stored_values": {},
    }
    if not chart:
        return out

    astro = chart.get("astrology") or {}
    if not astro:
        return out

    planets = astro.get("planets") or {}
    angles_doc = astro.get("angles") or {}
    msg_lc = (message or "").lower()
    msg_lc_p2 = msg_lc  # same string in router

    # MC — unconditional injection
    mc_doc = angles_doc.get("mc") or angles_doc.get("midheaven") or {}
    mc_sign_val = mc_doc.get("sign")
    if mc_sign_val:
        mc_formatted = mc_doc.get("formatted") or f"{mc_doc.get('degree', 0):.2f}°{mc_sign_val}"
        out["injected_points"].append(f"Midheaven / MC: {mc_formatted} ({mc_sign_val})")
        out["stored_values"]["MC"] = {"sign": mc_sign_val, "formatted": mc_formatted}

        mc_triggers = (
            "career", "leadership", "founder",
            "public role", "public life", "reputation",
            "vocation", "vocational",
            "contribution", "contribute",
            "team role", "team-role", "in the team",
            "professional direction", "calling",
            "purpose in work", "work purpose",
            "what role", "what do i contribute",
            "leadership style", "leadership team",
            "midheaven", "\u00a0mc\u00a0", " mc ", "mc:",
            "mc says", "mc say",
        )
        if any(t.strip() in msg_lc for t in mc_triggers):
            out["triggers_seen"]["MC"] = True
            out["weighting_blocks"].append("MC_WEIGHTING")

    # Chiron — unconditional injection
    chiron_doc = planets.get("Chiron") or {}
    if chiron_doc.get("sign"):
        c_house = chiron_doc.get("house")
        out["injected_points"].append(
            f"Chiron: {chiron_doc.get('formatted') or chiron_doc.get('sign')} "
            f"({chiron_doc.get('sign')})" + (f" House {c_house}" if c_house else "")
        )
        out["stored_values"]["Chiron"] = {
            "sign": chiron_doc.get("sign"),
            "house": c_house,
            "formatted": chiron_doc.get("formatted"),
        }

    # Descendant — relationship-gated
    dc_doc = angles_doc.get("dc") or angles_doc.get("descendant") or {}
    if dc_doc.get("sign"):
        dc_triggers = (
            "relationship", "marriage", "spouse", "partner",
            "wife", "husband", "girlfriend", "boyfriend",
            "between us", "between you", "forum",
            "team dynamics", "dynamic with", "dynamic between",
            "we work", "how we work", "couple",
        )
        out["stored_values"]["DC"] = {
            "sign": dc_doc.get("sign"),
            "formatted": dc_doc.get("formatted"),
        }
        if any(t in msg_lc_p2 for t in dc_triggers):
            out["triggers_seen"]["DC"] = True
            out["injected_points"].append(
                f"Descendant / DC: {dc_doc.get('formatted') or dc_doc.get('sign')} "
                f"({dc_doc.get('sign')})"
            )
            out["weighting_blocks"].append("DC_WEIGHTING")

    # IC — family/home/childhood/roots/safety gated
    ic_doc = angles_doc.get("ic") or {}
    if ic_doc.get("sign"):
        ic_triggers = (
            "family", "home", "childhood", "roots",
            "belonging", "safety", "parents", "mother",
            "father", "lineage", "ancestry", "inherited",
            "where i come from", "my origins",
        )
        out["stored_values"]["IC"] = {
            "sign": ic_doc.get("sign"),
            "formatted": ic_doc.get("formatted"),
        }
        if any(t in msg_lc_p2 for t in ic_triggers):
            out["triggers_seen"]["IC"] = True
            out["injected_points"].append(
                f"IC / Imum Coeli: {ic_doc.get('formatted') or ic_doc.get('sign')} "
                f"({ic_doc.get('sign')})"
            )
            out["weighting_blocks"].append("IC_WEIGHTING")

    # Developmental axis (purpose/growth/healing/etc.)
    purpose_triggers = (
        "purpose", "growth", "life direction",
        "life-direction", "healing", "spirituality",
        "shadow", "integration", "wound", "calling",
        "my soul", "soul's", "evolution",
    )
    if any(t in msg_lc_p2 for t in purpose_triggers):
        out["triggers_seen"]["purpose"] = True
        out["weighting_blocks"].append("DEVELOPMENTAL_AXIS_WEIGHTING")

    return out


# ──────────────────────────────────────────────────────────────────
# (2) Response evidence detector
# ──────────────────────────────────────────────────────────────────

def detect_evidence(
    category: str,
    response: str,
    chart_points: Dict[str, Any],
    sun_sign: Optional[str],
    asc_sign: Optional[str],
    moon_sign: Optional[str],
) -> Dict[str, Any]:
    """Heuristic detection of whether the response was actually
    influenced by the expected chart point vs. defaulting to a
    sun-sign / ascendant / moon substitution."""
    resp = response or ""
    resp_lc = resp.lower()
    out: Dict[str, Any] = {
        "mentions_expected_point": False,
        "mentions_expected_sign": False,
        "mentions_expected_house": False,
        "leak_sun_substitution": False,
        "leak_asc_substitution": False,
        "leak_moon_substitution": False,
        "evidence_quotes": [],
    }

    if category == "MC":
        target = chart_points.get("MC") or {}
        sign = target.get("sign")
        out["mentions_expected_point"] = bool(
            re.search(r"\b(mc|midheaven|10th\s*house|tenth\s*house|career\s*axis)\b", resp_lc)
        )
        if sign:
            out["mentions_expected_sign"] = sign.lower() in resp_lc
        # Sun-sign substitution leak: response talks about career/contribution
        # but only references sun sign
        if sun_sign and not out["mentions_expected_point"]:
            # If MC sign != Sun sign but response only names the sun sign
            if sign and sun_sign != sign and sun_sign.lower() in resp_lc:
                out["leak_sun_substitution"] = True

    elif category == "DC":
        target = chart_points.get("DC") or {}
        sign = target.get("sign")
        out["mentions_expected_point"] = bool(
            re.search(r"\b(dc|descendant|7th\s*house|seventh\s*house|partnership\s*axis|relational\s*axis)\b", resp_lc)
        )
        if sign:
            out["mentions_expected_sign"] = sign.lower() in resp_lc
        if asc_sign and sign and asc_sign != sign and asc_sign.lower() in resp_lc and not out["mentions_expected_point"]:
            out["leak_asc_substitution"] = True

    elif category == "Chiron":
        target = chart_points.get("Chiron") or {}
        sign = target.get("sign")
        house = target.get("house")
        out["mentions_expected_point"] = "chiron" in resp_lc
        if sign:
            out["mentions_expected_sign"] = sign.lower() in resp_lc
        if house:
            out["mentions_expected_house"] = bool(
                re.search(rf"\b(house\s*{house}|{house}(st|nd|rd|th)\s*house)\b", resp_lc)
            )

    elif category == "IC":
        target = chart_points.get("IC") or {}
        sign = target.get("sign")
        out["mentions_expected_point"] = bool(
            re.search(r"\b(ic|imum coeli|4th\s*house|fourth\s*house|nadir|home\s*axis)\b", resp_lc)
        )
        if sign:
            out["mentions_expected_sign"] = sign.lower() in resp_lc
        if asc_sign and sign and asc_sign != sign and asc_sign.lower() in resp_lc and not out["mentions_expected_point"]:
            out["leak_asc_substitution"] = True
        if moon_sign and sign and moon_sign != sign and moon_sign.lower() in resp_lc and not out["mentions_expected_point"]:
            out["leak_moon_substitution"] = True

    # Collect 1-2 evidence quotes around any expected-sign / point match
    interesting_terms = []
    if category == "MC":
        interesting_terms = ["MC", "Midheaven", "10th house", "tenth house"]
    elif category == "DC":
        interesting_terms = ["DC", "Descendant", "7th house", "seventh house"]
    elif category == "Chiron":
        interesting_terms = ["Chiron"]
    elif category == "IC":
        interesting_terms = ["IC", "Imum Coeli", "4th house", "fourth house", "nadir"]

    quotes: List[str] = []
    for term in interesting_terms:
        for m in re.finditer(re.escape(term), resp, flags=re.IGNORECASE):
            start = max(0, m.start() - 60)
            end = min(len(resp), m.end() + 120)
            snippet = resp[start:end].replace("\n", " ")
            quotes.append(f"…{snippet.strip()}…")
            if len(quotes) >= 2:
                break
        if len(quotes) >= 2:
            break

    if not quotes and out["mentions_expected_sign"]:
        target_sign = None
        if category == "MC":
            target_sign = (chart_points.get("MC") or {}).get("sign")
        elif category == "DC":
            target_sign = (chart_points.get("DC") or {}).get("sign")
        elif category == "Chiron":
            target_sign = (chart_points.get("Chiron") or {}).get("sign")
        elif category == "IC":
            target_sign = (chart_points.get("IC") or {}).get("sign")
        if target_sign:
            for m in re.finditer(re.escape(target_sign), resp, flags=re.IGNORECASE):
                start = max(0, m.start() - 60)
                end = min(len(resp), m.end() + 120)
                snippet = resp[start:end].replace("\n", " ")
                quotes.append(f"…{snippet.strip()}…")
                if len(quotes) >= 2:
                    break

    out["evidence_quotes"] = quotes
    return out


async def run_probe(
    client: httpx.AsyncClient,
    user_id: str,
    message: str,
) -> Dict[str, Any]:
    payload = {
        "user_id": user_id,
        "message": message,
        "include_journal": False,
        "include_history": False,
    }
    t0 = time.time()
    try:
        r = await client.post(ENDPOINT, json=payload, timeout=120.0)
        elapsed = time.time() - t0
        if r.status_code != 200:
            return {
                "ok": False,
                "status": r.status_code,
                "error": r.text[:500],
                "elapsed_s": elapsed,
            }
        body = r.json()
        return {
            "ok": True,
            "status": 200,
            "response": body.get("response", ""),
            "session_id": body.get("session_id"),
            "elapsed_s": elapsed,
        }
    except Exception as e:
        return {
            "ok": False,
            "status": None,
            "error": f"{type(e).__name__}: {e}",
            "elapsed_s": time.time() - t0,
        }


async def fetch_charts(user_ids: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"]]
    out: Dict[str, Dict[str, Any]] = {}
    for name, uid in user_ids.items():
        ch = await db.charts.find_one({"user_id": uid})
        out[name] = ch or {}
    return out


def summarise_user_chart(name: str, chart: Dict[str, Any]) -> Dict[str, Any]:
    astro = chart.get("astrology") or {}
    planets = astro.get("planets") or {}
    angles = astro.get("angles") or {}
    houses = astro.get("houses") or {}
    rising = houses.get("formatted_cusps", [{}])[0] if houses.get("formatted_cusps") else {}
    return {
        "name": name,
        "Sun":     (planets.get("Sun")    or {}).get("sign"),
        "Moon":    (planets.get("Moon")   or {}).get("sign"),
        "Rising":  rising.get("sign"),
        "MC":      ((angles.get("mc") or angles.get("midheaven")) or {}).get("sign"),
        "DC":      ((angles.get("dc") or angles.get("descendant")) or {}).get("sign"),
        "IC":      (angles.get("ic") or {}).get("sign"),
        "Chiron":  (planets.get("Chiron") or {}).get("sign"),
        "ChironHouse": (planets.get("Chiron") or {}).get("house"),
        "MC_formatted":     ((angles.get("mc") or angles.get("midheaven")) or {}).get("formatted"),
        "DC_formatted":     ((angles.get("dc") or angles.get("descendant")) or {}).get("formatted"),
        "IC_formatted":     (angles.get("ic") or {}).get("formatted"),
        "Chiron_formatted": (planets.get("Chiron") or {}).get("formatted"),
    }


async def main() -> int:
    print("[verify] Fetching charts...", flush=True)
    charts = await fetch_charts(USERS)

    chart_summaries: Dict[str, Dict[str, Any]] = {}
    for name in USERS:
        chart_summaries[name] = summarise_user_chart(name, charts.get(name) or {})

    results: List[Dict[str, Any]] = []

    async with httpx.AsyncClient() as client:
        for name, uid in USERS.items():
            chart = charts.get(name) or {}
            cs = chart_summaries[name]
            print(f"\n[verify] === {name} ({uid}) ===", flush=True)
            for category, intent_key, message in PROBES:
                print(f"  [{category:6}] {intent_key:<22} -> {message!r}", flush=True)

                # Step 1: simulate prompt injection
                injection = build_chart_point_injection(chart, message)

                # Step 2: live call
                live = await run_probe(client, uid, message)

                # Step 3: evidence
                chart_points = {
                    "MC":     injection["stored_values"].get("MC"),
                    "DC":     injection["stored_values"].get("DC"),
                    "IC":     injection["stored_values"].get("IC"),
                    "Chiron": injection["stored_values"].get("Chiron"),
                }
                response_text = live.get("response", "") if live.get("ok") else ""
                evidence = detect_evidence(
                    category=category,
                    response=response_text,
                    chart_points=chart_points,
                    sun_sign=cs.get("Sun"),
                    asc_sign=cs.get("Rising"),
                    moon_sign=cs.get("Moon"),
                )

                # Step 4: pass/fail
                # PASS requires:
                #   - Chart point IS injected into the prompt (or weighting block applied)
                #   - Response shows evidence (mentions point OR sign) — OR for MC, at minimum no sun-sign leak
                #   - No detected sign-substitution leak
                prompt_has_point = False
                if category == "MC":
                    prompt_has_point = any("Midheaven / MC" in p for p in injection["injected_points"])
                elif category == "DC":
                    prompt_has_point = any("Descendant / DC" in p for p in injection["injected_points"])
                elif category == "IC":
                    prompt_has_point = any("IC / Imum Coeli" in p for p in injection["injected_points"])
                elif category == "Chiron":
                    prompt_has_point = any(p.startswith("Chiron:") for p in injection["injected_points"])

                response_evidence_strong = (
                    evidence["mentions_expected_point"]
                    or evidence["mentions_expected_sign"]
                    or evidence["mentions_expected_house"]
                )
                leak = (
                    evidence["leak_sun_substitution"]
                    or evidence["leak_asc_substitution"]
                    or evidence["leak_moon_substitution"]
                )

                # Verdict: 3-tier
                if not live.get("ok"):
                    verdict = "ERROR"
                elif not prompt_has_point:
                    verdict = "FAIL (prompt)"
                elif leak:
                    verdict = "FAIL (substitution leak)"
                elif response_evidence_strong:
                    verdict = "PASS"
                else:
                    verdict = "WEAK (no overt evidence)"

                results.append({
                    "user": name,
                    "user_id": uid,
                    "category": category,
                    "intent_key": intent_key,
                    "message": message,
                    "verdict": verdict,
                    "prompt_has_point": prompt_has_point,
                    "injection": injection,
                    "live": live,
                    "evidence": evidence,
                    "chart_points": chart_points,
                })
                # Tiny pacing to avoid bursts
                await asyncio.sleep(0.4)

    # Persist raw JSON
    out_dir = "/app/backend/audit_reports"
    os.makedirs(out_dir, exist_ok=True)
    raw_path = os.path.join(out_dir, "ASTROLOGY_PROMPT_INTEGRITY_VERIFICATION.json")
    with open(raw_path, "w") as f:
        json.dump({
            "generated_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "chart_summaries": chart_summaries,
            "results": results,
        }, f, indent=2, default=str)
    print(f"\n[verify] wrote {raw_path}", flush=True)
    print(f"[verify] total probes: {len(results)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
