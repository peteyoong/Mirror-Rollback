"""
ASC Forensic — Multi-Chart Comparison Matrix
=============================================
Build marker: asc-house-forensic-fix-v1

For each user in the cohort, compute Sun/Moon/ASC/MC under 5 different
sign-attribution systems:

  1. MIRROR_CURRENT      — uniform 30° signs, ayanamsa=31.2836°
  2. IAU_13_CONSTELLATION— pure IAU constellation boundaries (incl. Ophiuchus)
  3. IAU_12_MERGED       — IAU constellation boundaries with Ophiuchus
                           merged into Scorpius (likely Athen Chimenti)
  4. LAHIRI_30           — uniform 30° signs, ayanamsa=23.85° (Lahiri J2000)
  5. FAGAN_BRADLEY_30    — uniform 30° signs, ayanamsa=24.97° (Fagan/Athen-canonical)

Output is intended for cross-verification against Genetic Matrix
"True Sidereal-M (Midpoint)" readings the user maintains externally.

Run:
    cd /app/backend && python -m tests.asc_comparison_matrix
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import swisseph as swe

# path bootstrap
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.iau_constellations import IAU_ECLIPTIC_BOUNDARIES, lookup_constellation  # noqa: E402

EPHE_PATH = str(ROOT / "ephe")
swe.set_ephe_path(EPHE_PATH)

# Cohort — varied DOBs + timezones from real Mirror users
COHORT: List[Dict[str, Any]] = [
    {"uid": "697ec826ad4b18f75bf42616", "label": "Mel",       "date": "1981-07-13", "time": "07:25", "tz": "Asia/Kuala_Lumpur", "lat": 2.1896,    "lon": 102.2501},
    {"uid": "6971c81f2b40fd5ef501d375", "label": "Peter-KL",  "date": "1968-04-01", "time": "01:25", "tz": "Asia/Kuala_Lumpur", "lat": 3.2083304, "lon": 101.304146},
    {"uid": "697f74791a7a96aa35e283a0", "label": "TestNYC",   "date": "1990-05-15", "time": "14:30", "tz": "+00:00",            "lat": 40.7127,   "lon": -74.0060},
    {"uid": "697f751b1a7a96aa35e283a1", "label": "TestLA",    "date": "1985-03-21", "time": "09:30", "tz": "+00:00",            "lat": 34.0537,   "lon": -118.2428},
    {"uid": "697f78e11a7a96aa35e283a2", "label": "TestChicago","date":"1992-07-15", "time": "10:45", "tz": "+00:00",            "lat": 41.8756,   "lon": -87.6244},
    {"uid": "697f795f1a7a96aa35e283a3", "label": "TestSeattle","date":"1988-12-01", "time": "15:30", "tz": "+00:00",            "lat": 47.6038,   "lon": -122.3301},
    {"uid": "697f79961a7a96aa35e283a4", "label": "TestBoston","date":"1995-06-20", "time": "08:00", "tz": "+00:00",            "lat": 42.3588,   "lon": -71.0578},
    {"uid": "697f79d31a7a96aa35e283a6", "label": "TestMiami", "date": "1990-03-15", "time": "12:00", "tz": "+00:00",            "lat": 25.7742,   "lon": -80.1936},
]

SIGNS_12 = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def to_utc_jd(date: str, time: str, tz: str) -> float:
    naive = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    if tz.startswith("+") or tz.startswith("-"):
        sign = 1 if tz.startswith("+") else -1
        hh, mm = tz.lstrip("+-").split(":") if ":" in tz else (tz.lstrip("+-"), "00")
        from datetime import timedelta, timezone as _t
        aware = naive.replace(tzinfo=_t(sign * timedelta(hours=int(hh), minutes=int(mm))))
    else:
        from zoneinfo import ZoneInfo
        aware = naive.replace(tzinfo=ZoneInfo(tz))
    from datetime import timezone as _tz
    utc = aware.astimezone(_tz.utc)
    return swe.julday(
        utc.year, utc.month, utc.day,
        utc.hour + utc.minute / 60.0 + utc.second / 3600.0,
    )


def uniform_30(longitude: float, ayanamsa: float) -> Tuple[str, float]:
    """Attribution under uniform 30° signs with given ayanamsa."""
    sid = (longitude - ayanamsa) % 360
    idx = int(sid // 30)
    return SIGNS_12[idx], sid % 30


# Build a 12-sign view by merging Ophiuchus into Scorpius
IAU_12_RANGES: List[Tuple[str, float, float]] = []
for name, start, end in IAU_ECLIPTIC_BOUNDARIES:
    if name == "Ophiuchus":
        continue
    IAU_12_RANGES.append((name, start, end))
# Extend Scorpius to swallow Ophiuchus
_extended: List[Tuple[str, float, float]] = []
for name, start, end in IAU_12_RANGES:
    if name == "Scorpius":
        _extended.append((name, start, 266.62))  # Ophiuchus's original end
    else:
        _extended.append((name, start, end))
IAU_12_RANGES = _extended


def iau_13_attribution(tropical_long: float) -> Tuple[str, float]:
    n = tropical_long % 360
    name = lookup_constellation(n)
    # find degree-in-constellation
    for cn, start, end in IAU_ECLIPTIC_BOUNDARIES:
        if cn == name:
            if start > end:  # Pisces wrap
                width = 360 - start + end
                if n >= start:
                    deg = n - start
                else:
                    deg = (360 - start) + n
                return cn, deg
            return cn, n - start
    return name, 0.0


def iau_12_merged_attribution(tropical_long: float) -> Tuple[str, float]:
    n = tropical_long % 360
    # Pisces wrap
    if n >= 351.57 or n < 28.69:
        deg = (n - 351.57) % 360
        return "Pisces", deg
    for cn, start, end in IAU_12_RANGES:
        if cn == "Pisces":
            continue
        if start <= n < end:
            return cn, n - start
    return "Pisces", 0.0


def calc_chart(date: str, time: str, tz: str, lat: float, lon: float) -> Dict[str, float]:
    jd = to_utc_jd(date, time, tz)
    houses_p, ascmc_t = swe.houses(jd, lat, lon, b"P")
    sun_t, _ = swe.calc_ut(jd, swe.SUN)
    moon_t, _ = swe.calc_ut(jd, swe.MOON)
    return {
        "jd": jd,
        "Sun_trop": sun_t[0] % 360,
        "Moon_trop": moon_t[0] % 360,
        "ASC_trop": ascmc_t[0] % 360,
        "MC_trop": ascmc_t[1] % 360,
    }


def fmt_sign_deg(name: str, deg: float) -> str:
    d = int(deg)
    m = int((deg - d) * 60)
    return f"{d}°{m:02d}' {name}"


def evaluate_user(u: Dict[str, Any]) -> Dict[str, Any]:
    chart = calc_chart(u["date"], u["time"], u["tz"], u["lat"], u["lon"])
    out = {"user": u["label"], "uid": u["uid"], "chart": chart, "systems": {}}
    AYAN_MIRROR = 31.2836
    AYAN_LAHIRI = 23.85
    AYAN_FAGAN = 24.97
    for body in ("Sun", "Moon", "ASC", "MC"):
        trop = chart[f"{body}_trop"]
        m_name, m_deg = uniform_30(trop, AYAN_MIRROR)
        l_name, l_deg = uniform_30(trop, AYAN_LAHIRI)
        f_name, f_deg = uniform_30(trop, AYAN_FAGAN)
        iau13_name, iau13_deg = iau_13_attribution(trop)
        iau12_name, iau12_deg = iau_12_merged_attribution(trop)
        out["systems"].setdefault("mirror_current", {})[body]      = fmt_sign_deg(m_name, m_deg)
        out["systems"].setdefault("iau_13", {})[body]              = fmt_sign_deg(iau13_name, iau13_deg)
        out["systems"].setdefault("iau_12_merged", {})[body]       = fmt_sign_deg(iau12_name, iau12_deg)
        out["systems"].setdefault("lahiri_30", {})[body]           = fmt_sign_deg(l_name, l_deg)
        out["systems"].setdefault("fagan_30", {})[body]            = fmt_sign_deg(f_name, f_deg)
    return out


def render(results: List[Dict[str, Any]]) -> str:
    out: List[str] = []
    out.append("# ASC Comparison Matrix — Multi-Chart Audit")
    out.append("")
    out.append("**Build marker:** `asc-house-forensic-fix-v1`")
    out.append("")
    out.append("Five sign-attribution systems compared across 8 charts.")
    out.append("Cross-verify each `iau_12_merged` row against the user's Genetic Matrix reading.")
    out.append("That column is the leading hypothesis for what Athen Chimenti's True Sidereal-M actually is.")
    out.append("")
    headers = ["body", "mirror_current\n(ay=31.28)", "iau_13\n(13 IAU)", "iau_12_merged\n(Athen?)", "lahiri_30\n(ay=23.85)", "fagan_30\n(ay=24.97)"]
    for r in results:
        out.append(f"\n## {r['user']}  (uid={r['uid']})")
        out.append("")
        out.append(f"_Tropical: Sun {r['chart']['Sun_trop']:.2f}° · Moon {r['chart']['Moon_trop']:.2f}° · ASC {r['chart']['ASC_trop']:.2f}° · MC {r['chart']['MC_trop']:.2f}°_")
        out.append("")
        out.append("| body | mirror_current | iau_13 | **iau_12_merged** | lahiri_30 | fagan_30 |")
        out.append("|------|----------------|--------|-------------------|-----------|----------|")
        for body in ("Sun", "Moon", "ASC", "MC"):
            row = [body]
            for k in ("mirror_current", "iau_13", "iau_12_merged", "lahiri_30", "fagan_30"):
                row.append(r["systems"][k][body])
            out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def main():
    results = [evaluate_user(u) for u in COHORT]
    md = render(results)
    md_path = ROOT / "tests" / "ASC_COMPARISON_MATRIX.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md)

    # Also emit a focused summary on the divergent column
    print(f"[asc-comparison] wrote {md_path}")
    print()
    print("=== KEY ASC DIVERGENCE TABLE ===")
    print(f"{'User':<14s}  {'mirror_current':<22s}  {'iau_13':<22s}  {'iau_12_merged':<22s}")
    for r in results:
        print(f"{r['user']:<14s}  "
              f"{r['systems']['mirror_current']['ASC']:<22s}  "
              f"{r['systems']['iau_13']['ASC']:<22s}  "
              f"{r['systems']['iau_12_merged']['ASC']:<22s}")
    print()
    print("=== SUN / MOON SANITY (should agree across iau_13 / iau_12_merged) ===")
    print(f"{'User':<14s}  {'Sun (mirror)':<18s}  {'Sun (iau_12)':<18s}  {'Moon (mirror)':<18s}  {'Moon (iau_12)':<18s}")
    for r in results:
        print(f"{r['user']:<14s}  "
              f"{r['systems']['mirror_current']['Sun']:<18s}  "
              f"{r['systems']['iau_12_merged']['Sun']:<18s}  "
              f"{r['systems']['mirror_current']['Moon']:<18s}  "
              f"{r['systems']['iau_12_merged']['Moon']:<18s}")


if __name__ == "__main__":
    main()
