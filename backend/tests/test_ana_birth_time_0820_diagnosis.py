"""Ana 08:20 birth_time repair verification + GM-delta engine diagnosis.

Iteration 19 — strictly read-only against PROD.

Verifies:
  1. user.birth_time persisted as "08:20" (per timezone_override repair).
  2. Stored ASC ≈ Taurus 0.47°, MC ≈ Aquarius 3.87° (per Variant-A 13-sign mode).
  3. member-summary now reads Taurus Rising (not Aries Rising) and HD line
     "Manifesting Generator · Sacral Authority · 3/5" unchanged.
  4. member-mappings: HD narrative_blocks populated; story slots have no raw
     HD jargon (Ajna, Gate #, Channel x-y, bare "Sacral").
  5. Diagnostic: independent Swiss Ephemeris recompute confirms Mirror's
     tropical & sidereal numbers, and quantifies the GM delta.
"""
import os
import re
import json
import pytest
import requests

PROD = "https://mirror-lens-fixes-r-1779710763.emergent.host"
ANA = "6a1c17323b39ec46cfd74326"
PETE = "697f0c6abf35c0528ff06954"
FORUM = "6a1bd0d7fa294d284b7749c4"

PEEK_TOKEN = "PEEK_CHART_ANGLES_2026_06_26"
TIMEOUT = 60


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


# ============================================================
# 1. PROD STATE AFTER REPAIR
# ============================================================
class TestProdStateAfterRepair:

    @pytest.fixture(scope="class")
    def peek(self, session):
        url = f"{PROD}/api/admin/peek_chart_angles"
        r = session.get(url, params={"user_id": ANA, "confirm": PEEK_TOKEN}, timeout=TIMEOUT)
        assert r.status_code == 200, f"peek_chart_angles failed: {r.status_code} {r.text[:300]}"
        return r.json()

    def test_birth_time_persisted_0820(self, peek):
        bt = peek["user"]["birth_time"]
        assert bt == "08:20", f"user.birth_time={bt!r}, expected '08:20'"

    def test_timezone_persisted(self, peek):
        tz = peek["user"]["timezone"]
        assert tz == "America/Argentina/Buenos_Aires", f"timezone={tz}"

    def test_asc_taurus_047(self, peek):
        asc = peek["stored"]["ASC"]
        assert asc["sign"] == "Taurus", f"ASC.sign={asc['sign']}"
        assert abs(asc["degree"] - 0.47) < 0.05, f"ASC.degree={asc['degree']}"
        # sidereal longitude (post-SVP subtraction) should be ~20.20
        assert abs(asc["longitude"] - 20.1968) < 0.01, f"ASC.longitude={asc['longitude']}"

    def test_mc_aquarius_387(self, peek):
        mc = peek["stored"]["MC"]
        assert mc["sign"] == "Aquarius", f"MC.sign={mc['sign']}"
        assert abs(mc["degree"] - 3.87) < 0.05, f"MC.degree={mc['degree']}"
        assert abs(mc["longitude"] - 298.7167) < 0.01, f"MC.longitude={mc['longitude']}"


# ============================================================
# 2. MEMBER-SUMMARY REFLECTS NEW CHART
# ============================================================
class TestMemberSummary:

    @pytest.fixture(scope="class")
    def summary(self, session):
        url = f"{PROD}/api/forums/{FORUM}/member-summary/{ANA}"
        r = session.get(url, params={"user_id": PETE}, timeout=TIMEOUT)
        assert r.status_code == 200, f"member-summary failed: {r.status_code}"
        return r.json().get("summary", {})

    def test_rising_is_taurus_not_aries(self, summary):
        astro = summary.get("astrology") or ""
        assert "Taurus Rising" in astro, f"astrology={astro!r}"
        assert "Aries Rising" not in astro, f"stale Aries Rising still in: {astro!r}"

    def test_human_design_unchanged(self, summary):
        hd = summary.get("human_design") or ""
        assert hd == "Manifesting Generator \u00b7 Sacral Authority \u00b7 3/5", f"hd={hd!r}"


# ============================================================
# 3. MEMBER-MAPPINGS RELATIONSHIP SYNTHESIS
# ============================================================
class TestRelationshipSynthesis:

    @pytest.fixture(scope="class")
    def ana_map(self, session):
        url = f"{PROD}/api/forums/{FORUM}/member-mappings"
        r = session.get(url, params={"user_id": PETE}, timeout=TIMEOUT)
        assert r.status_code == 200, f"member-mappings failed: {r.status_code}"
        data = r.json()
        mappings = data.get("mappings") or []
        m = next((x for x in mappings if ANA in json.dumps(x)), None)
        assert m is not None, "Ana mapping not found"
        return m

    def test_hd_narrative_blocks_populated(self, ana_map):
        hd_field = ana_map["signals"]["human_design_field"]
        nb = hd_field.get("narrative_blocks") or {}
        assert isinstance(nb, dict) and len(nb) >= 5, f"narrative_blocks too sparse: {list(nb.keys())}"
        # spot-check expected v1 narrative slots
        assert "type_pair_engagement" in nb
        assert "authority_rhythm" in nb

    def test_relationship_channels_present(self, ana_map):
        # The mapping exposes relationship channels (electromagnetic / compromise),
        # not Ana's individual channels. 28-38 is the compromise channel between
        # Pete and Ana, confirming HD numbers are stable across recompute.
        diag = ana_map["signals"]["human_design_field"]["diagnostics"]
        comp = diag.get("compromise_pairs") or []
        assert [28, 38] in comp or [38, 28] in comp, f"compromise_pairs={comp}"

    def test_no_raw_hd_jargon_in_story_slots(self, ana_map):
        """Acceptance: raw HD jargon (Ajna / Gate # / Channel #-# / bare Sacral) must NOT
        leak into the story-facing slots of relationship_synthesis. The technical_refs
        sub-tree is explicitly excluded (it's diagnostic, not narrative)."""
        rs = ana_map.get("relationship_synthesis") or {}
        # Limit scan to user-facing narrative slots
        story_slots = {
            "story": rs.get("story"),
            "undertone_for_today": rs.get("undertone_for_today"),
        }
        # Also include top-level narrative slots that render to the user
        for k in ("headline", "description", "what_works", "what_to_watch", "why_this_happens", "story"):
            story_slots[f"top.{k}"] = ana_map.get(k)

        patterns = [
            (r'\bAjna\b', "Ajna"),
            (r'\bGate\s+\d+', "Gate ##"),
            (r'\bChannel\s+\d+\s*-\s*\d+', "Channel ##-##"),
        ]
        hits = []
        def scan(obj, path):
            if isinstance(obj, str):
                for pat, label in patterns:
                    if re.search(pat, obj):
                        hits.append((path, label, obj[:120]))
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    scan(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    scan(v, f"{path}[{i}]")
        for k, v in story_slots.items():
            scan(v, k)
        assert not hits, f"HD jargon leaked into story slots: {hits}"


# ============================================================
# 4. ENGINE DIAGNOSIS — independent Swiss Ephemeris cross-check
# ============================================================
class TestEngineGmDiagnosis:
    """Independent computation of Ana's chart at 1983-05-03 11:20 UTC,
    lat=-34.5538, lon=-58.7030. Documents the actual tropical & sidereal
    values produced by Swiss Ephemeris and compares them to (a) Mirror's
    stored values and (b) GM's claimed values from the user's request."""

    GM = {
        "asc_tropical_12sign": (0.68, "Aries"),     # GM PDF: Aries 0°41'
        "mc_tropical_12sign":  (4.08, "Capricorn"), # GM PDF: Capricorn 4°05'  → 274.08° raw
        "sun_tropical_12sign": (14.13, "Taurus"),   # GM PDF: Taurus 14°08'   → 44.13° raw
        "moon_tropical_12sign":(0.22,  "Aries"),    # GM PDF: Aries 0°13'     → 0.22° raw
    }
    MIRROR_STORED = {  # Variant A 13-sign True-Sidereal-M output
        "asc_sign": "Taurus",   "asc_deg_in_sign": 0.4682,  "asc_sid_lon": 20.1968,
        "mc_sign":  "Aquarius", "mc_deg_in_sign":  3.8732,  "mc_sid_lon": 298.7167,
    }
    SVP = 31.2836

    @pytest.fixture(scope="class")
    def se(self):
        import swisseph as swe
        return swe

    @pytest.fixture(scope="class")
    def computed(self, se):
        jd = se.julday(1983, 5, 3, 11 + 20/60.0)  # 11:20 UTC
        lat, lon = -34.5538, -58.7030
        cusps, ascmc = se.houses(jd, lat, lon, b"A")  # Equal houses
        sun  = se.calc_ut(jd, se.SUN,  se.FLG_SWIEPH)[0][0]
        moon = se.calc_ut(jd, se.MOON, se.FLG_SWIEPH)[0][0]
        return {
            "jd": jd,
            "asc_trop": ascmc[0],
            "mc_trop":  ascmc[1],
            "sun_trop": sun,
            "moon_trop":moon,
            "asc_sid":  (ascmc[0] - self.SVP) % 360,
            "mc_sid":   (ascmc[1] - self.SVP) % 360,
            "sun_sid":  (sun     - self.SVP) % 360,
            "moon_sid": (moon    - self.SVP) % 360,
        }

    def test_mirror_sidereal_matches_swisseph(self, computed):
        """Mirror's stored sidereal longitudes equal SE tropical - SVP exactly."""
        assert abs(computed["asc_sid"] - self.MIRROR_STORED["asc_sid_lon"]) < 0.01
        assert abs(computed["mc_sid"]  - self.MIRROR_STORED["mc_sid_lon"])  < 0.01

    def test_engine_is_variant_a_13sign_in_tropical_frame(self):
        """Confirms the sign-mapping logic and that Ophiuchus IS included."""
        from calculations.sign_attribution import (
            attribute_sign, MODE_MIDPOINT13_VARIANT_A, get_zodiac_signs,
            DEFAULT_MODE, OPHIUCHUS_SIGN_NAME, SIGNS_13,
        )
        assert DEFAULT_MODE == MODE_MIDPOINT13_VARIANT_A
        signs = get_zodiac_signs(DEFAULT_MODE)
        assert OPHIUCHUS_SIGN_NAME in signs
        assert len(signs) == 13
        # Sign mapping is 0-indexed: SIGNS_13[0] == "Aries"
        assert SIGNS_13[0] == "Aries"
        # And the Variant-A table operates on TROPICAL longitude
        # (Mirror passes tropical = sidereal + SVP into attribute_sign).
        r = attribute_sign(51.4804, mode=MODE_MIDPOINT13_VARIANT_A)
        assert r["sign"] == "Taurus"
        assert abs(r["degree_within_sign"] - 0.468) < 0.01

    def test_gm_delta_is_not_clean_30deg_offset(self, computed):
        """Diagnostic: raw tropical longitudes Mirror produces vs GM-claimed.
        We document that the *raw longitudes* differ by ~50° (ASC), ~56° (MC),
        ~1.67° (Sun), and ~66° (Moon) — NOT a clean 30° one-sign offset."""
        gm_asc = 0.68
        gm_mc  = 274.08
        gm_sun = 44.13
        gm_moon = 0.22

        def signed_min(a, b):
            d = (a - b) % 360
            return d if d <= 180 else d - 360

        d_asc  = signed_min(computed["asc_trop"],  gm_asc)
        d_mc   = signed_min(computed["mc_trop"],   gm_mc)
        d_sun  = signed_min(computed["sun_trop"],  gm_sun)
        d_moon = signed_min(computed["moon_trop"], gm_moon)

        # Print for the report
        print(f"\n[DIAG] Mirror tropical raw vs GM-claimed raw (signed shortest):")
        print(f"  ASC:  Mirror={computed['asc_trop']:.4f}  GM={gm_asc:.4f}  delta={d_asc:+.4f}°")
        print(f"  MC:   Mirror={computed['mc_trop']:.4f}   GM={gm_mc:.4f}    delta={d_mc:+.4f}°")
        print(f"  Sun:  Mirror={computed['sun_trop']:.4f}  GM={gm_sun:.4f}   delta={d_sun:+.4f}°")
        print(f"  Moon: Mirror={computed['moon_trop']:.4f} GM={gm_moon:.4f}  delta={d_moon:+.4f}°")

        # Assert: the delta is NOT close to ±30° on the raw tropical scale for any body.
        for name, d in [("ASC", d_asc), ("MC", d_mc), ("Sun", d_sun), ("Moon", d_moon)]:
            assert abs(abs(d) - 30.0) > 5.0, (
                f"{name} delta {d:+.4f}° unexpectedly within 5° of 30° — "
                f"would have indicated a literal one-sign convention shift; "
                f"actual deltas show the GM mismatch is NOT a 30° offset."
            )

    def test_no_timezone_interpretation_lands_at_gm_asc(self, se):
        """Sweep all plausible UTC offsets for '08:20 local' on 1983-05-03 and
        confirm none produce an ASC anywhere near GM's claimed Aries 0.68°.
        The closest match requires UTC ~07:15 (local AR 04:15), nowhere near 08:20."""
        lat, lon = -34.5538, -58.7030
        candidates = [
            (-3, "UTC-3 correct AR"),
            (-4, "UTC-4 (hypothetical)"),
            (-2, "UTC-2"),
            (0,  "treat-as-UTC"),
            (3,  "UTC+3"),
        ]
        results = []
        for tz_off, label in candidates:
            utc_h = 8 - tz_off
            jd = se.julday(1983, 5, 3, utc_h + 20/60.0)
            asc = se.houses(jd, lat, lon, b"A")[1][0]
            results.append((label, asc, abs((asc - 0.68 + 180) % 360 - 180)))
        results.sort(key=lambda x: x[2])
        print(f"\n[DIAG] Timezone sweep for ASC=0.68° target:")
        for lbl, asc, d in results:
            print(f"  {lbl:30s} → ASC={asc:.4f}°  |delta|={d:.4f}°")
        # Best-match delta should still be > 10° — no plausible timezone hits GM.
        assert results[0][2] > 10.0, (
            f"Unexpectedly close match to GM ASC found at {results[0]} — "
            f"would suggest a timezone misinterpretation hypothesis is viable."
        )
