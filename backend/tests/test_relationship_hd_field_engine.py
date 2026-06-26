"""Tests for the HD Relationship Field Engine V3
===================================================

Build marker: relationship-hd-field-v3

Coverage (12 categories per spec):
  1. Every Type pairing emits a field_v3 (5×5 = 15 unique frozensets)
  2. Every Authority pairing emits decision_dynamics
  3. Centre conditioning narratives fire for asymmetric centers
  4. Electromagnetic narrative deterministic by count
  5. Compromise narrative deterministic by count
  6. Dominance narrative deterministic by side counts
  7. Repair pathway non-empty for all combinations
  8. Diagnostics completeness
  9. Backward compatibility (returns None gracefully on bad input)
 10. Mirror language compliance — forbidden tokens scan
 11. No forbidden tokens across full 5×5 Type × 6×6 Authority sweep
 12. Snapshot lock for Pete↔Mel / Pete↔Isaac / Pete↔Thaddeus
"""
from __future__ import annotations
import asyncio
import os
import sys
from itertools import product, combinations
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from services.relationship_hd_field_engine import (
    AUTHORITIES, AUTHORITY_PAIR, CENTER_BOTH_DEFINED, CENTER_BOTH_OPEN,
    CENTER_CONDITIONING, CENTER_PRIORITY, ENGINE_VERSION,
    FORBIDDEN_TOKENS, TYPE_PAIR_AURA,
    compute_hd_relationship_field, find_forbidden_language,
    _classify_channels,
)

TYPES = ("Manifestor", "Generator", "Manifesting Generator",
         "Projector", "Reflector")


# ── Fixtures: real Pete / Mel / Isaac / Thaddeus shapes ─────────────
PETE_CHART = {
    "human_design": {
        "type":      "Manifestor",
        "authority": "Emotional",
        "profile":   "5/1",
        "definition": "Split",
        "defined_centers":   ["Solar Plexus", "Throat", "Ego", "Head", "Ajna"],
        "undefined_centers": ["G Center", "Sacral", "Spleen", "Root", "Heart"],
        "active_gates": [37, 40, 35, 36, 5, 63, 4, 25, 51, 21, 1, 8],
        "defined_channels": [
            {"gate1":63,"gate2":4,"centers":["Head","Ajna"]},
            {"gate1":35,"gate2":36,"centers":["Throat","Solar Plexus"]},
            {"gate1":37,"gate2":40,"centers":["Solar Plexus","Ego"]},
        ],
    },
}
MEL_CHART = {
    "human_design": {
        "type":      "Reflector",
        "authority": "Lunar",
        "profile":   "3/5",
        "definition": "None",
        "defined_centers":   [],
        "undefined_centers": ["Head","Ajna","Throat","G Center","Heart","Solar Plexus","Sacral","Spleen","Root"],
        "active_gates": [3, 14, 50, 27, 35, 9, 47],
        "defined_channels": [],
    },
}
ISAAC_CHART = {
    "human_design": {
        "type":      "Generator",
        "authority": "Sacral",
        "profile":   "6/2",
        "definition": "Single",
        "defined_centers":   ["Sacral","Throat","G Center","Spleen","Root"],
        "undefined_centers": ["Head","Ajna","Heart","Solar Plexus"],
        "active_gates": [20, 34, 10, 57, 27, 50, 2, 14],
        "defined_channels": [
            {"gate1":20,"gate2":34,"centers":["Throat","Sacral"]},
            {"gate1":10,"gate2":57,"centers":["G Center","Spleen"]},
            {"gate1":27,"gate2":50,"centers":["Sacral","Spleen"]},
            {"gate1":2,"gate2":14,"centers":["G Center","Sacral"]},
        ],
    },
}
THADDEUS_CHART = {
    "human_design": {
        "type":      "Manifesting Generator",
        "authority": "Sacral",
        "profile":   "4/6",
        "definition": "Single",
        "defined_centers":   ["Sacral","Throat","G Center","Solar Plexus","Heart"],
        "undefined_centers": ["Head","Ajna","Spleen","Root"],
        "active_gates": [1, 8, 2, 14, 6, 59, 36, 35, 51, 25],
        "defined_channels": [
            {"gate1":1,"gate2":8,"centers":["G Center","Throat"]},
            {"gate1":2,"gate2":14,"centers":["G Center","Sacral"]},
            {"gate1":6,"gate2":59,"centers":["Solar Plexus","Sacral"]},
            {"gate1":35,"gate2":36,"centers":["Throat","Solar Plexus"]},
        ],
    },
}


def _make_chart(type_, auth, profile="4/6", definition="Single",
                defined=None, undefined=None, gates=None):
    all_centers = ["Head","Ajna","Throat","G Center","Heart",
                   "Solar Plexus","Sacral","Spleen","Root"]
    defined = defined or ["Sacral","Throat"]
    undefined = undefined or [c for c in all_centers if c not in defined]
    return {"human_design": {
        "type": type_, "authority": auth, "profile": profile,
        "definition": definition,
        "defined_centers": defined, "undefined_centers": undefined,
        "active_gates": gates or [1, 8, 34, 20],
        "defined_channels": [{"gate1":1,"gate2":8,"centers":["G Center","Throat"]},
                             {"gate1":20,"gate2":34,"centers":["Throat","Sacral"]}],
    }}


REQUIRED_FIELD_V3_KEYS = {
    "energy_signature", "field_overview", "aura_dynamics",
    "decision_dynamics", "centre_conditioning", "electromagnetic_gifts",
    "compromise_dynamics", "dominance_dynamics", "friction_patterns",
    "repair_pathway", "growth_edge", "energy_weather",
}
REQUIRED_DIAGNOSTICS_KEYS = {
    "type_pair", "authority_pair", "profile_pair", "definition_pair",
    "electromagnetic_count", "electromagnetic_pairs",
    "compromise_count", "compromise_pairs",
    "dominance_count", "dominance_a_count", "dominance_b_count",
    "companion_count", "channel_count_a", "channel_count_b",
    "defined_centers_a", "defined_centers_b", "center_conditioning",
    "engine_version",
}


# 1. Every Type pairing emits complete field_v3
def test_every_type_pair_emits_complete_field_v3():
    for ta, tb in product(TYPES, repeat=2):
        ca = _make_chart(ta, "Sacral" if ta == "Generator" else "Emotional")
        cb = _make_chart(tb, "Sacral" if tb == "Generator" else "Emotional")
        r = compute_hd_relationship_field(ca, cb, "Alpha", "Bravo")
        assert r is not None, f"{ta}↔{tb} returned None"
        assert set(r["field_v3"].keys()) == REQUIRED_FIELD_V3_KEYS, \
            f"{ta}↔{tb}: missing keys {REQUIRED_FIELD_V3_KEYS - set(r['field_v3'].keys())}"


# 2. Every Authority pairing emits decision_dynamics
def test_every_authority_pair_emits_decision_dynamics():
    common_auths = ("Emotional","Sacral","Splenic","Ego","Self-Projected","Lunar")
    for aa, ab in product(common_auths, repeat=2):
        ca = _make_chart("Generator", aa)
        cb = _make_chart("Generator", ab)
        r = compute_hd_relationship_field(ca, cb, "A", "B")
        assert r is not None
        dd = r["field_v3"]["decision_dynamics"]
        assert isinstance(dd, str) and len(dd) > 20, f"{aa}↔{ab}: weak decision_dynamics"


# 3. Centre conditioning fires for asymmetric centers
def test_centre_conditioning_asymmetric_emits_lines():
    # Pete (G Center open) ↔ Isaac (G Center defined) — Isaac amplifies Pete's G
    r = compute_hd_relationship_field(PETE_CHART, ISAAC_CHART, "Pete", "Isaac")
    lines = r["field_v3"]["centre_conditioning"]
    assert isinstance(lines, list) and 1 <= len(lines) <= 3
    # At least one line mentions an actual center name
    assert any(any(c in l for c in CENTER_PRIORITY) for l in lines)


def test_centre_conditioning_caps_at_three():
    r = compute_hd_relationship_field(PETE_CHART, MEL_CHART, "Pete", "Mel")
    assert len(r["field_v3"]["centre_conditioning"]) <= 3


# 4. Electromagnetic narrative deterministic by count
def test_electromagnetic_narrative_present():
    r = compute_hd_relationship_field(PETE_CHART, ISAAC_CHART, "Pete", "Isaac")
    em = r["field_v3"]["electromagnetic_gifts"]
    assert isinstance(em, str) and len(em) > 30


def test_electromagnetic_classifier_correctness():
    # A has gate 1 only, B has gate 8 only → forms 1-8 electromagnetic
    a = {1}
    b = {8}
    classified = _classify_channels(a, b)
    em = classified["electromagnetic"]
    assert (1, 8) in em or (8, 1) in em


# 5. Compromise narrative
def test_compromise_narrative_present():
    r = compute_hd_relationship_field(PETE_CHART, ISAAC_CHART, "Pete", "Isaac")
    assert isinstance(r["field_v3"]["compromise_dynamics"], str)


# 6. Dominance narrative
def test_dominance_narrative_present():
    r = compute_hd_relationship_field(PETE_CHART, MEL_CHART, "Pete", "Mel")
    # Mel is Reflector (no defined channels) → Pete's channels dominate field
    dom = r["field_v3"]["dominance_dynamics"]
    assert isinstance(dom, str)


def test_dominance_classifier_correctness():
    a = {1, 8}  # Pete has full 1-8 channel
    b = set()   # Mel has neither
    classified = _classify_channels(a, b)
    dom = classified["dominance"]
    assert len(dom) >= 1
    # Tuple last element marks who dominates
    assert any(e[-1] == "a" for e in dom)


# 7. Repair pathway always non-empty
def test_repair_pathway_non_empty_for_all_type_authority_combos():
    common_auths = ("Emotional","Sacral","Splenic","Ego","Lunar")
    for ta in TYPES:
        for aa in common_auths:
            for tb in TYPES:
                for ab in common_auths:
                    ca = _make_chart(ta, aa)
                    cb = _make_chart(tb, ab)
                    r = compute_hd_relationship_field(ca, cb, "A", "B")
                    if r is None: continue
                    repair = r["field_v3"]["repair_pathway"]
                    assert isinstance(repair, list) and len(repair) >= 1, \
                        f"{ta}/{aa}↔{tb}/{ab}: empty repair"


# 8. Diagnostics completeness
def test_diagnostics_complete():
    r = compute_hd_relationship_field(PETE_CHART, MEL_CHART, "Pete", "Mel")
    diag = r["diagnostics"]
    assert set(diag.keys()) == REQUIRED_DIAGNOSTICS_KEYS, \
        f"missing diagnostic keys: {REQUIRED_DIAGNOSTICS_KEYS - set(diag.keys())}"
    assert diag["engine_version"] == ENGINE_VERSION


# 9. Backward compatibility — returns None on bad input
def test_returns_none_when_type_missing():
    assert compute_hd_relationship_field({}, PETE_CHART, "A","B") is None
    assert compute_hd_relationship_field(PETE_CHART, {}, "A","B") is None
    no_auth = {"human_design": {"type":"Generator","authority":""}}
    assert compute_hd_relationship_field(no_auth, PETE_CHART, "A","B") is None


# 10. Mirror-language guard detects every token
def test_forbidden_language_detection():
    for tok in FORBIDDEN_TOKENS:
        assert find_forbidden_language(f"this is {tok} here") == [tok]


# 11. No forbidden tokens across exhaustive sweep
def test_no_forbidden_language_in_full_sweep():
    common_auths = ("Emotional","Sacral","Splenic","Ego","Lunar","Self-Projected")
    for ta, tb in product(TYPES, repeat=2):
        for aa, ab in product(common_auths, repeat=2):
            ca = _make_chart(ta, aa); cb = _make_chart(tb, ab)
            r = compute_hd_relationship_field(ca, cb, "Alpha", "Bravo")
            if r is None: continue
            blob = []
            for v in r["field_v3"].values():
                if isinstance(v, str): blob.append(v)
                elif isinstance(v, list): blob.extend(x for x in v if isinstance(x, str))
            bad = find_forbidden_language(" ".join(blob))
            assert not bad, f"{ta}/{aa}↔{tb}/{ab}: forbidden token {bad}"


# 12. Snapshot lock — three real pairs
def test_snapshot_pete_mel():
    r = compute_hd_relationship_field(PETE_CHART, MEL_CHART, "Pete", "Mel")
    f = r["field_v3"]; d = r["diagnostics"]
    assert "Catalyst" in f["energy_signature"]   # Manifestor primary label
    assert "Sampler"  in f["energy_signature"] or "Reflective" in f["energy_signature"]
    # Manifestor × Reflector — informing/sampling theme present
    assert "inform" in f["aura_dynamics"].lower() or "closed" in f["aura_dynamics"].lower()
    # Reflector should trigger 28-day repair pathway
    assert any("28" in line.lower() or "month" in line.lower() for line in f["repair_pathway"])
    assert d["type_pair"] == "Manifestor × Reflector"


def test_snapshot_pete_isaac():
    r = compute_hd_relationship_field(PETE_CHART, ISAAC_CHART, "Pete", "Isaac")
    f = r["field_v3"]; d = r["diagnostics"]
    assert "Catalyst" in f["energy_signature"]
    assert "Engine"   in f["energy_signature"]
    # Manifestor × Generator — informing + waiting-to-respond theme
    txt = (f["aura_dynamics"] + f["decision_dynamics"]).lower()
    assert "inform" in txt or "respond" in txt
    assert d["type_pair"] == "Manifestor × Generator"


def test_snapshot_pete_thaddeus():
    r = compute_hd_relationship_field(PETE_CHART, THADDEUS_CHART, "Pete", "Thaddeus")
    f = r["field_v3"]; d = r["diagnostics"]
    assert d["type_pair"] == "Manifestor × Manifesting Generator"
    # Both initiate — collision / engine theme
    assert "engine" in f["aura_dynamics"].lower() or "collide" in f["aura_dynamics"].lower() or "informing" in f["aura_dynamics"].lower()


# 13. DB sweep — every valid HD pair emits complete field_v3
def test_db_sweep_field_v3_always_complete():
    from motor.motor_asyncio import AsyncIOMotorClient
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BACKEND, ".env"))

    async def _run():
        c = AsyncIOMotorClient(os.getenv("MONGO_URL"))
        db = c[os.getenv("DB_NAME","test_database")]
        users = await db.users.find({}).to_list(length=None)
        charts = {}
        for u in users:
            ch = await db.charts.find_one({"user_id": str(u["_id"])})
            if not ch: continue
            hd = ch.get("human_design") or {}
            if hd.get("type") and hd.get("authority"):
                charts[str(u["_id"])] = ch
        sample = list(charts.values())[:30]
        pairs = list(combinations(sample, 2))[:200]
        ok = 0; bad: List[str] = []
        for a, b in pairs:
            r = compute_hd_relationship_field(a, b, "A", "B")
            if not r: bad.append("None"); continue
            if set(r["field_v3"].keys()) != REQUIRED_FIELD_V3_KEYS:
                bad.append("keys-mismatch"); continue
            ok += 1
        c.close()
        return ok, len(pairs), bad

    ok, total, bad = asyncio.run(_run())
    assert not bad, f"incomplete on {len(bad)}/{total} pairs.  First few: {bad[:3]}"
    assert ok == total


if __name__ == "__main__":
    import traceback
    p = f = 0
    for name in sorted(globals()):
        if not name.startswith("test_"): continue
        fn = globals()[name]
        try:
            fn(); print(f"  PASS  {name}"); p += 1
        except Exception:
            print(f"  FAIL  {name}"); traceback.print_exc(); f += 1
    print(f"\n{p} passed, {f} failed")
    raise SystemExit(0 if not f else 1)
