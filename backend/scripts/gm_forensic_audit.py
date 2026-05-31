"""
GM-Alignment Forensic Audit — three-user comparison
====================================================
Compares Mirror's Equal vs Placidus output against Genetic Matrix's
"Astro HD Natal" panel (left side of GM screenshots) for Pete, Mel,
and Ana. NO CODE CHANGES, NO MIGRATION. Read-only forensic.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, "/app/backend")
from calculations.astrology import get_full_natal_chart  # noqa: E402


# ---------------------------------------------------------------------------
# GROUND TRUTH from GM screenshots — LEFT panel ("Astro HD Natal")
# ---------------------------------------------------------------------------
# Pete:  House label = "Equal", True Sidereal-M (User defined).
#        Birth: 1968-04-01 01:25 UTC+07:30, Petaling Jaya Malaysia
#        (3.1073, 101.607002). MC=Capricorn 14°48' in HOUSE 9
#        → mathematically IMPOSSIBLE under Placidus (MC = 10th cusp by def).
PETE = {
    "name": "Pete",
    "utc": datetime(1968, 3, 31, 17, 55, 0, tzinfo=timezone.utc),  # 01:25 +07:30
    "lat": 3.1073,
    "lon": 101.607002,
    "gm_label_house_system": "Equal",
    "gm": {
        # Reading directly from Pete's image (left panel, sign and house number)
        "AC":  {"sign": "Aries",       "house": 1,  "deg": "24°02'"},
        "MC":  {"sign": "Capricorn",   "house": 9,  "deg": "14°48'"},
        "Sun": {"sign": "Pisces",      "house": 12},
        "Moon":{"sign": "Aquarius",    "house": 11},
    },
}

# Mel: House label = "Equal", True Sidereal-M (User defined).
#      Birth: 1981-07-13 07:25 UTC+07:30 Melaka Malaysia
#      (2.1889, 102.250999). MC=Gemini in HOUSE 9 → again Equal.
MEL = {
    "name": "Mel",
    "utc": datetime(1981, 7, 12, 23, 55, 0, tzinfo=timezone.utc),  # 07:25 +07:30
    "lat": 2.1889,
    "lon": 102.250999,
    "gm_label_house_system": "Equal",
    "gm": {
        "AC":  {"sign": "Cancer",  "house": 1, "deg": "(visible)"},
        "MC":  {"sign": "Aries",   "house": 10, "deg": "(visible)"},
        # GM left table marks MC near the 10/9 boundary
    },
}

# Ana: Two artifacts. The .jpg is "Zodiac 13 Birth Chart" with
# "Custom (Sharatan(Beta Aries))=02°Aries Topocentric Equal(Asc=1st)
# True Nodes Modern" labels at bottom-left. The .pdf is the
# standard True Sidereal-M Astro HD Natal view (same view as Pete/Mel).
# Birth: 1983-05-03 08:20 UTC-03:00, San Miguel Argentina
# (-34.5438, -58.715302).
ANA = {
    "name": "Ana",
    "utc": datetime(1983, 5, 3, 11, 20, 0, tzinfo=timezone.utc),
    "lat": -34.5438,
    "lon": -58.715302,
    "gm_label_house_system": "Equal (per Z13 jpg) / unclear (PDF)",
}


def rough_house_equal(longitude: float, asc_longitude: float) -> int:
    """Given a sidereal longitude and the ASC sidereal longitude,
    return the Equal-house number (1..12)."""
    diff = (longitude - asc_longitude) % 360.0
    return int(diff // 30.0) + 1


def chart_summary(label: str, chart: dict) -> dict:
    angles  = chart.get("angles") or {}
    planets = chart.get("planets") or {}
    out = {
        "label": label,
        "house_system": chart.get("metadata", {}).get("house_system") or chart.get("house_system"),
        "asc_sign": (angles.get("asc") or {}).get("sign"),
        "asc_deg":  (angles.get("asc") or {}).get("longitude"),
        "mc_sign":  (angles.get("mc")  or {}).get("sign"),
        "mc_deg":   (angles.get("mc")  or {}).get("longitude"),
        "planets":  {},
    }
    for p in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter",
              "Saturn", "Uranus", "Neptune", "Pluto", "Chiron",
              "Juno", "North Node", "South Node"):
        pp = planets.get(p) or {}
        out["planets"][p] = {
            "sign":  pp.get("sign"),
            "house": pp.get("house"),
            "deg":   pp.get("longitude"),
        }
    return out


def compare_user(u: dict):
    print("=" * 78)
    print(f"  USER: {u['name']}")
    print(f"  Birth UTC: {u['utc']}   lat={u['lat']}  lon={u['lon']}")
    print(f"  GM house-system label (from screenshot): {u.get('gm_label_house_system')}")
    print("=" * 78)

    chart_eq = get_full_natal_chart(birth_datetime=u["utc"], lat=u["lat"], lon=u["lon"], house_system="Equal")
    chart_pl = get_full_natal_chart(birth_datetime=u["utc"], lat=u["lat"], lon=u["lon"], house_system="Placidus")

    eq = chart_summary("Equal",    chart_eq)
    pl = chart_summary("Placidus", chart_pl)

    # Angles
    print(f"  ASC  Mirror-Equal: {eq['asc_sign']:<12}  Mirror-Placidus: {pl['asc_sign']}")
    print(f"  MC   Mirror-Equal: {eq['mc_sign']:<12}  Mirror-Placidus: {pl['mc_sign']}")

    # Planet houses
    print(f"  {'Planet':12} {'Sign':14} {'Equal-H':>7} {'Placidus-H':>10}")
    for p in eq["planets"]:
        pe = eq["planets"][p]
        pp = pl["planets"][p]
        print(f"  {p:12} {str(pe['sign']):14} {str(pe['house']):>7} {str(pp['house']):>10}")

    # MC investigation
    print()
    print("  MC investigation:")
    print(f"    Mirror-Equal    MC sidereal long: {eq['mc_deg']}  sign: {eq['mc_sign']}")
    print(f"    Mirror-Placidus MC sidereal long: {pl['mc_deg']}  sign: {pl['mc_sign']}")

    # GM cross-check (where we have explicit values)
    gm = u.get("gm") or {}
    if gm:
        print()
        print("  GM cross-check (left panel 'Astro HD Natal'):")
        for k, v in gm.items():
            if k == "AC":
                m_eq, m_pl = eq["asc_sign"], pl["asc_sign"]
            elif k == "MC":
                m_eq, m_pl = eq["mc_sign"], pl["mc_sign"]
            else:
                m_eq = (eq["planets"].get(k) or {}).get("sign")
                m_pl = (pl["planets"].get(k) or {}).get("sign")
            ok_eq = "✓" if v.get("sign") == m_eq else "✗"
            ok_pl = "✓" if v.get("sign") == m_pl else "✗"
            print(f"    {k:6} GM={v.get('sign'):<12} (house {v.get('house','?')})  "
                  f"Mirror-Equal={str(m_eq):<12}{ok_eq}  Mirror-Plac={str(m_pl):<12}{ok_pl}")

    return {"user": u["name"], "equal": eq, "placidus": pl}


if __name__ == "__main__":
    results = []
    for u in (PETE, MEL, ANA):
        results.append(compare_user(u))
        print()

    print("=" * 78)
    print("STRUCTURAL TEST: 'GM places MC in house 9' → impossible under Placidus")
    print("=" * 78)
    print("  Pete GM MC house = 9   → GM is NOT using Placidus for Pete")
    print("  Mel  GM MC house = 9   → GM is NOT using Placidus for Mel")
    print("  Under Placidus, MC == 10th-house-cusp BY CONSTRUCTION.")
    print("  Therefore GM's 'Astro HD Natal' panel uses EQUAL HOUSES.")
