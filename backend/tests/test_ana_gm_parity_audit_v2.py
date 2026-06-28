"""Ana GM Parity Audit V2 — corrected comparison.

GM uses "Zodiac 13" (13-sign sidereal) with Sharatan-2° ayanamsa.
Mirror also uses 13-sign sidereal (Variant-A) with SVP=31.2836.
Both frames use the SAME label set. Compare directly.

We additionally derive Sharatan's tropical longitude analytically (its
fixed-star ephemeris file is absent locally) and report the ayanamsa
delta between GM and Mirror.
"""
import os
import json
import math
from datetime import datetime, timezone

import pytest
import swisseph as swe

from calculations.astrology import (
    get_full_natal_chart,
    SVP_DEGREES,
    ZODIAC_SIGNS_13,
    normalize_degrees,
)
from calculations.sign_attribution import attribute_sign

# Birth data
BIRTH_UTC = datetime(1983, 5, 3, 11, 20, tzinfo=timezone.utc)
LAT = -34.5538
LON = -58.7030

# GM REFERENCE — already in 13-sign sidereal frame at Sharatan-2° ayanamsa.
GM = {
    "ASC":     {"sign": "Taurus",      "degree": 0.683,  "house": None},
    "MC":      {"sign": "Aquarius",    "degree": 4.083,  "house": None},
    "DC":      {"sign": "Scorpio",     "degree": 9.100,  "house": None},
    "IC":      {"sign": "Leo",         "degree": 15.750, "house": None},
    "Sun":     {"sign": "Aries",       "degree": 11.400, "house": 12},
    "Moon":    {"sign": "Sagittarius", "degree": 27.333, "house": 8},
    "Mercury": {"sign": "Taurus",      "degree": 4.633,  "house": 1},
    "Venus":   {"sign": "Taurus",      "degree": 2.433,  "house": 2},
    "Mars":    {"sign": "Aries",       "degree": 19.350, "house": 12},
    "Jupiter": {"sign": "Scorpio",     "degree": 7.700,  "house": 7},
    "Saturn":  {"sign": "Libra",       "degree": 7.583,  "house": 6},
    "Uranus":  {"sign": "Scorpio",     "degree": 6.867,  "house": 7},
    "Neptune": {"sign": "Sagittarius", "degree": 2.117,  "house": 8},
    "Pluto":   {"sign": "Libra",       "degree": 5.067,  "house": 5},
}


def _label_13(longitude_sidereal: float):
    """Reproduce Mirror's Variant-A 13-sign labeling for a sidereal longitude.

    Mirror's attribute_sign() operates on TROPICAL longitude, so we add SVP
    back to convert sidereal→tropical, then label.
    """
    trop = normalize_degrees(longitude_sidereal + SVP_DEGREES)
    r = attribute_sign(trop)
    return r["sign"], r["degree_within_sign"]


@pytest.fixture(scope="module")
def chart_equal():
    return get_full_natal_chart(BIRTH_UTC, LAT, LON, house_system="Equal")


@pytest.fixture(scope="module")
def chart_placidus():
    return get_full_natal_chart(BIRTH_UTC, LAT, LON, house_system="Placidus")


class TestParityDirect13Sign:
    """Direct 13-sign label comparison (both Mirror and GM live in 13-sign)."""

    def test_print_and_check(self, chart_equal, chart_placidus):
        ce, cp = chart_equal, chart_placidus

        sign_misses = []
        deg_misses = []   # > 0.5° within-sign delta even when sign matches
        house_misses = []

        print("\n=== Ana 13-sign parity (Mirror Variant-A vs GM Zodiac-13) ===")
        print(f"{'Body':<9} {'GM sign':<13} {'GM°':>7}  {'Mirror sign':<13} {'M°':>7}  {'Δ°':>7}  GMhs Mhs(Eq) Mhs(Pl)")

        # Angles
        for ang in ("ASC", "MC", "DC", "IC"):
            sid = ce["angles"][ang.lower()]["longitude"]
            m_sign, m_deg = _label_13(sid)
            gm = GM[ang]
            delta = (m_deg - gm["degree"] + 540) % 360 - 180 if m_sign == gm["sign"] else None
            sign_ok = m_sign == gm["sign"]
            print(
                f"{ang:<9} {gm['sign']:<13} {gm['degree']:7.3f}  "
                f"{m_sign:<13} {m_deg:7.3f}  "
                f"{(delta if delta is not None else float('nan')):+7.3f}  "
                f"   —     —     —"
            )
            if not sign_ok:
                sign_misses.append((ang, m_sign, gm["sign"]))
            elif delta is not None and abs(delta) > 0.5:
                deg_misses.append((ang, m_deg, gm["degree"], delta))

        # Planets
        for body in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter",
                     "Saturn", "Uranus", "Neptune", "Pluto"):
            p_e = ce["planets"][body]
            p_p = cp["planets"][body]
            sid = p_e["longitude"]
            # Mirror already stores the Variant-A 13-sign sign on p_e — use it.
            m_sign = p_e["sign"]
            m_deg = p_e["degree"]
            gm = GM[body]
            delta = (m_deg - gm["degree"] + 540) % 360 - 180 if m_sign == gm["sign"] else None
            print(
                f"{body:<9} {gm['sign']:<13} {gm['degree']:7.3f}  "
                f"{m_sign:<13} {m_deg:7.3f}  "
                f"{(delta if delta is not None else float('nan')):+7.3f}  "
                f"  h{gm['house']:<2}  h{p_e['house']:<2}    h{p_p['house']:<2}"
            )
            if m_sign != gm["sign"]:
                sign_misses.append((body, m_sign, gm["sign"]))
            elif delta is not None and abs(delta) > 0.5:
                deg_misses.append((body, m_deg, gm["degree"], delta))

            if p_e["house"] != gm["house"]:
                house_misses.append((body, p_e["house"], gm["house"], "Equal"))
            # Also track Placidus
            if p_p["house"] != gm["house"]:
                house_misses.append((body, p_p["house"], gm["house"], "Placidus"))

        print(f"\nSign misses (Mirror-Equal vs GM): {len(sign_misses)}")
        for b, m, g in sign_misses:
            print(f"  {b}: Mirror={m}  GM={g}")
        print(f"Within-sign Δ > 0.5°: {len(deg_misses)}")
        for b, m, g, d in deg_misses:
            print(f"  {b}: Mirror={m:.3f}°  GM={g:.3f}°  Δ={d:+.3f}°")
        print(f"House misses (Mirror vs GM): {len(house_misses)}")
        for b, m, g, sys_ in house_misses:
            print(f"  {b} [{sys_}]: Mirror=h{m}  GM=h{g}")

        # House shifts Equal vs Placidus
        print("\nHouse shifts (Equal → Placidus):")
        for body in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter",
                     "Saturn", "Uranus", "Neptune", "Pluto"):
            he = ce["planets"][body]["house"]
            hp = cp["planets"][body]["house"]
            if he != hp:
                print(f"  {body}: Equal h{he} → Placidus h{hp}")

        # Persist
        os.makedirs("/app/test_reports", exist_ok=True)
        out = {
            "sign_misses_equal_vs_gm": [
                {"body": b, "mirror": m, "gm": g} for b, m, g in sign_misses
            ],
            "within_sign_delta_over_0p5": [
                {"body": b, "mirror_deg": m, "gm_deg": g, "delta": d}
                for b, m, g, d in deg_misses
            ],
            "house_misses": [
                {"body": b, "mirror": m, "gm": g, "system": s}
                for b, m, g, s in house_misses
            ],
        }
        with open("/app/test_reports/iteration_20_parity.json", "w") as f:
            json.dump(out, f, indent=2)


class TestSharatanAyanamsa:
    """Compute Sharatan β Arietis tropical λ for 1983-05-03 analytically.

    Swiss Ephemeris fixed-star file (sefstars.txt) is not present locally,
    so we use the published ICRS J2000 catalogue position and apply
    Newcomb precession in ecliptic longitude (≈ 50.3″/yr).

    β Arietis (Sheratan):
        ICRS J2000 RA  =  28.66027°
        ICRS J2000 Dec = +20.80831°
    Ecliptic obliquity J2000 ε = 23.4392911°.

    λ_J2000 = atan2( sin(α)cos(ε)+tan(δ)sin(ε), cos(α) )
    """

    def test_sharatan_ayanamsa_and_delta(self):
        # Catalogue position J2000
        ra_deg = 28.66027
        dec_deg = 20.80831
        eps_j2000 = 23.4392911

        ra = math.radians(ra_deg)
        dec = math.radians(dec_deg)
        eps = math.radians(eps_j2000)

        # Transform equatorial → ecliptic
        x = math.sin(ra) * math.cos(eps) + math.tan(dec) * math.sin(eps)
        y = math.cos(ra)
        lam_j2000 = math.degrees(math.atan2(x, y)) % 360.0

        # Apply general precession in ecliptic longitude.
        # From J2000.0 to 1983-05-03 is approximately -16.66 Julian years.
        # General precession p ≈ 50.290966″/yr ≈ 0.013969701°/yr.
        years = (swe.julday(1983, 5, 3, 11.333) - 2451545.0) / 365.25
        p_per_year_deg = 50.290966 / 3600.0
        lam_1983_tropical = (lam_j2000 + years * p_per_year_deg) % 360.0

        print(f"\nSharatan (β Arietis) tropical longitude:")
        print(f"  J2000        = {lam_j2000:.4f}°")
        print(f"  1983-05-03   = {lam_1983_tropical:.4f}°  ({years:+.3f} years from J2000)")

        # GM's "Sharatan = 2° Aries" sidereal claim implies
        # ayanamsa = tropical_lon - sidereal_lon = lam_1983 - 2.0
        gm_ayanamsa = lam_1983_tropical - 2.0
        # Wrap to plausible 0..360 (real ayanamsa, ~24-32° this epoch)
        gm_ayanamsa = gm_ayanamsa % 360.0

        print(f"  GM Sharatan-2° ayanamsa for 1983-05-03 ≈ {gm_ayanamsa:.4f}°")
        print(f"  Mirror SVP (fixed)                     = {SVP_DEGREES:.4f}°")
        delta = gm_ayanamsa - SVP_DEGREES
        print(f"  Δ (GM − Mirror)                        = {delta:+.4f}°")

        # Persist
        os.makedirs("/app/test_reports", exist_ok=True)
        with open("/app/test_reports/iteration_20_ayanamsa.json", "w") as f:
            json.dump({
                "sharatan_tropical_lon_j2000_deg": lam_j2000,
                "sharatan_tropical_lon_1983_deg": lam_1983_tropical,
                "years_from_j2000_to_1983": years,
                "precession_rate_deg_per_year": p_per_year_deg,
                "gm_sharatan_ayanamsa_1983": gm_ayanamsa,
                "mirror_svp_degrees": SVP_DEGREES,
                "ayanamsa_delta_gm_minus_mirror_deg": delta,
            }, f, indent=2)


class TestSignCrossingsUnderTwoAyanamsas:
    """At each planet, recompute the 13-sign label under Mirror's SVP vs GM's
    Sharatan-2° ayanamsa, and report which (if any) cross sign boundaries.
    """

    def test_sign_crossings(self):
        # Replay Sharatan calc
        ra = math.radians(28.66027)
        dec = math.radians(20.80831)
        eps = math.radians(23.4392911)
        lam_j2000 = math.degrees(math.atan2(
            math.sin(ra)*math.cos(eps) + math.tan(dec)*math.sin(eps),
            math.cos(ra)
        )) % 360.0
        years = (swe.julday(1983, 5, 3, 11.333) - 2451545.0) / 365.25
        sh = (lam_j2000 + years * (50.290966 / 3600.0)) % 360.0
        gm_ay = (sh - 2.0) % 360.0

        # Compute tropical for each planet at Ana's birth.
        jd = swe.julday(1983, 5, 3, 11.0 + 20.0 / 60.0)
        crossings = []
        print("\n[Per-planet 13-sign label: Mirror-SVP vs GM-Sharatan]")
        for body in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter",
                     "Saturn", "Uranus", "Neptune", "Pluto"):
            pid = getattr(swe, body.upper())
            xx, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH)
            trop = xx[0] % 360.0

            # Mirror labeling: attribute_sign on TROPICAL longitude (its
            # boundaries already bake in SVP).
            r_mirror = attribute_sign(trop)
            s_mirror = r_mirror["sign"]
            d_mirror = r_mirror["degree_within_sign"]

            # GM labeling: shift the tropical longitude by (Mirror_SVP −
            # GM_ayanamsa) before calling attribute_sign so the same
            # boundary tables produce the GM result.
            shift = SVP_DEGREES - gm_ay
            trop_shifted = (trop + shift) % 360.0
            r_gm = attribute_sign(trop_shifted)
            s_gm = r_gm["sign"]
            d_gm = r_gm["degree_within_sign"]

            tag = "" if s_mirror == s_gm else "  <-- SIGN CROSSING"
            print(
                f"  {body:<8} trop={trop:7.3f}  "
                f"Mirror={s_mirror:<12s} {d_mirror:6.3f}°  "
                f"GM={s_gm:<12s} {d_gm:6.3f}°{tag}"
            )
            if s_mirror != s_gm:
                crossings.append((body, s_mirror, s_gm))

        print(f"\nTotal sign crossings: {len(crossings)}")
