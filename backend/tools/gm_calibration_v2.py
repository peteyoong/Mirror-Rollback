"""
GM Calibration v2 — Forensic comparison using Mirror's PRODUCTION engines.
==========================================================================
Runs `calculations.astrology.get_full_natal_chart` and
`calculations.human_design.get_human_design_chart` for each subject and
prints the values that would be displayed in Mirror, alongside the GM
screenshot values, to identify mismatches.

Read-only. No DB writes. No engine modifications.
"""
from __future__ import annotations
import sys, os, json
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

sys.path.insert(0, "/app/backend")

from calculations.astrology import get_full_natal_chart
from calculations.human_design import get_human_design_chart
from calculations.true_sidereal_midpoint_boundaries import (
    midpoint_13_sign_from_tropical_longitude,
)

@dataclass
class Subject:
    name: str
    local_dt: datetime
    tz_offset_h: float
    lat: float
    lon: float
    gm_personality: dict          # GM right-panel values (planet -> "Gate.Line / Sign / House / Deg")
    gm_design: dict               # GM left-panel values

# GM screenshot values transcribed from screenshots.
# Format: planet -> (gate_line, sign, house, deg_in_sign_str)
# Use 'X' for sign if unsure; degrees and gate.line are taken as gospel.
SUBJECTS = [
    Subject(
        name="Pete Y",
        local_dt=datetime(1968, 4, 1, 1, 25),
        tz_offset_h=7.5,
        lat=3.1073, lon=101.607002,
        gm_design={  # LEFT panel  "Astro HD Natal" — note: this is the DESIGN chart per profile convention
            "Sun":     ("5.1",  "?", 7,  "16°27'"),
            "Earth":   ("35.1", "?", 1,  "15°39'"),
            "Moon":    ("41.5", "?", 9,  "11°06'"),
            "NorthNode": ("36.1","?",11, "35°21'R"),
            "SouthNode": ("6.1", "?", 5, "31°45'R"),
            "Mercury": ("5.5",  "?", 8,  "20°16'"),
            "Venus":   ("28.1", "?", 6,  "01°53'"),
            "Mars":    ("61.5", "?", 9,  "00°23'"),
            "Jupiter": ("31.3", "?", 3,  "21°32'R"),
            "Saturn":  ("55.6", "?",10,  "17°24'"),
            "Uranus":  ("29.5", "?", 4,  "06°46'R"),
            "Neptune": ("32.5", "?", 6,  "13°34'"),
            "Pluto":   ("4.4",  "?", 4,  "00°23'R"),
            "Chiron":  ("30.1", "?",10,  "06°48'"),
            "Lilith":  ("21.2", "?",11,  "10°41'"),
            "AC":      ("2.1",  "?", 1,  "24°02'"),
            "MC":      ("19.3", "?", 9,  "14°48'"),
            "DC":      ("1.1",  "?", 7,  "00°20'"),
            "IC":      ("33.3", "?", 3,  "26°28'"),
        },
        gm_personality={  # RIGHT panel "Natal Quantum"
            "Sun":     ("37.5", "?", 3,  "22°13'"),
            "Earth":   ("40.5", "?", 9,  "18°38'"),
            "Moon":    ("21.2", "?", 4,  "11°03'"),
            "NorthNode": ("22.1","?", 4,  "29°49'"),
            "SouthNode": ("47.1","?",10, "26°13'"),
            "Mercury": ("13.6", "?", 4,  "00°46'"),
            "Venus":   ("49.1", "?", 3,  "01°05'"),
            "Mars":    ("25.4", "?", 4,  "01°55'"),
            "Jupiter": ("62.6", "?", 8,  "12°29'R"),
            "Saturn":  ("63.3", "?", 3,  "25°57'"),
            "Uranus":  ("29.2", "?", 9,  "04°47'R"),
            "Neptune": ("32.5", "?",11,  "14°04'"),
            "Pluto":   ("4.2",  "?", 9,  "36°59'R"),
            "Chiron":  ("30.5", "?", 3,  "11°07'"),
            "Lilith":  ("51.6", "?", 5,  "00°38'"),
            "AC":      ("5.5",  "?", 1,  "20°12'"),
            "MC":      ("47.4", "?",10,  "28°41'"),
            "DC":      ("35.5", "?", 6,  "19°23'"),
            "IC":      ("22.4", "?", 4,  "32°16'"),
        },
    ),
    Subject(
        name="Mel",
        local_dt=datetime(1981, 7, 13, 7, 25),
        tz_offset_h=7.5,
        lat=2.1889, lon=102.250999,
        gm_design={
            "Sun":     ("22.5","?",6,"33°28'"),
            "Earth":   ("47.6","?",12,"29°52'"),
            "Moon":    ("52.1","?",9,"08°17'"),
            "NorthNode": ("52.4","?",9,"10°50'"),
            "SouthNode": ("58.4","?",3,"07°36'"),
            "Mercury": ("37.1","?",5,"18°11'"),
            "Venus":   ("36.1","?",6,"34°47'"),
            "Mars":    ("22.3","?",6,"31°18'"),
            "Jupiter": ("59.3","?",11,"10°42'R"),
            "Saturn":  ("59.5","?",11,"12°33'R"),
            "Uranus":  ("50.3","?",1,"17°09'R"),
            "Neptune": ("43.6","?",2,"10°20'R"),
            "Pluto":   ("47.6","?",12,"30°21'R"),
            "Chiron":  ("51.1","?",7,"15°16'"),
            "Lilith":  ("48.2","?",1,"48°58'"),
            "AC":      ("48.1","?",1,"48°58'"),
            "MC":      ("52.3","?",9,"09°50'"),
            "DC":      ("21.1","?",7,"10°06'"),
            "IC":      ("58.3","?",3,"06°37'"),
        },
        gm_personality={
            "Sun":     ("45.3","?",12,"22°54'"),
            "Earth":   ("26.3","?",6,"23°42'"),
            "Moon":    ("28.1","?",5,"01°55'"),
            "NorthNode": ("15.3","?",1,"04°40'R"),
            "SouthNode": ("10.3","?",7,"01°27'R"),
            "Mercury": ("8.5","?",11,"02°28'"),
            "Venus":   ("39.6","?",1,"01°45'"),
            "Mars":    ("8.1","?",11,"35°36'"),
            "Jupiter": ("59.3","?",3,"10°48'"),
            "Saturn":  ("59.4","?",3,"11°32'"),
            "Uranus":  ("32.5","?",4,"13°55'R"),
            "Neptune": ("43.4","?",5,"08°18'R"),
            "Pluto":   ("47.4","?",3,"28°56'R"),
            "Chiron":  ("42.1","?",10,"01°06'"),
            "Lilith":  ("32.1","?",4,"09°29'"),
            "AC":      ("15.2","?",12,"03°19'"),
            "MC":      ("25.6","?",10,"03°00'"),
            "DC":      ("10.2","?",7,"00°05'"),
            "IC":      ("46.6","?",4,"41°24'"),
        },
    ),
    Subject(
        name="Jaan C",
        local_dt=datetime(1973, 12, 9, 21, 15),  # GM screenshot time, NOT db time
        tz_offset_h=7.5,
        lat=3.1478, lon=101.695,
        gm_design={
            "Sun":     ("7.6","?",9,"35°14'"),
            "Earth":   ("13.6","?",3,"00°25'"),
            "Moon":    ("13.1","?",3,"19°06'"),
            "NorthNode": ("34.4","?",12,"08°00'R"),
            "SouthNode": ("20.4","?",6,"07°12'R"),
            "Mercury": ("29.3","?",9,"05°01'"),
            "Venus":   ("6.6","?",10,"36°10'"),
            "Mars":    ("17.5","?",5,"07°55'"),
            "Jupiter": ("10.4","?",1,"02°31'R"),
            "Saturn":  ("20.3","?",6,"06°08'"),
            "Uranus":  ("47.4","?",10,"28°48'"),
            "Neptune": ("28.3","?",11,"03°44'"),
            "Pluto":   ("59.3","?",9,"11°10'"),
            "Chiron":  ("22.3","?",4,"30°57'"),
            "Lilith":  ("34.3","?",12,"06°22'"),
            "AC":      ("9.1","?",1,"10°04'"),
            "MC":      ("40.4","?",10,"16°58'"),
            "DC":      ("16.1","?",7,"09°16'"),
            "IC":      ("37.4","?",4,"20°34'"),
        },
        gm_personality={
            "Sun":     ("1.4","?",5,"03°00'"),
            "Earth":   ("2.4","?",11,"26°41'"),
            "Moon":    ("24.3","?",11,"19°47'"),
            "NorthNode": ("14.4","?",6,"01°52'R"),
            "SouthNode": ("8.4","?",12,"01°04'R"),
            "Mercury": ("50.4","?",5,"18°44'"),
            "Venus":   ("10.3","?",7,"01°02'"),
            "Mars":    ("36.4","?",10,"37°32'"),
            "Jupiter": ("58.6","?",7,"09°38'"),
            "Saturn":  ("20.2","?",12,"04°51'R"),
            "Uranus":  ("6.4","?",4,"33°57'"),
            "Neptune": ("28.5","?",5,"06°25'"),
            "Pluto":   ("59.6","?",3,"14°01'"),
            "Chiron":  ("63.5","?",9,"27°36'R"),
            "Lilith":  ("5.1","?",6,"16°09'"),
            "AC":      ("12.2","?",1,"27°50'"),
            "MC":      ("36.5","?",10,"39°10'"),
            "DC":      ("11.2","?",7,"28°39'"),
            "IC":      ("6.5","?",4,"35°34'"),
        },
    ),
    Subject(
        name="Ana Gayoso",
        local_dt=datetime(1983, 5, 3, 8, 20),
        tz_offset_h=-3.0,
        lat=-34.5433, lon=-58.7122,
        gm_design={},  # Ana's chart provided is a different style; will skip detailed compare
        gm_personality={},
    ),
]


def deg_in_sign_to_float(s: str) -> float:
    s = s.replace("R", "").strip()
    # Format: "DD°MM'" or "DD°MM" 
    s = s.replace("′", "'")
    if "°" not in s:
        return float(s)
    a, b = s.split("°", 1)
    d = float(a.strip())
    b = b.replace("'", "").strip()
    m = float(b) if b else 0.0
    return d + m / 60.0


def fmt_dm(deg: float) -> str:
    if deg < 0:
        deg += 360.0
    d = int(deg)
    m_full = (deg - d) * 60.0
    m = int(round(m_full))
    if m == 60:
        d += 1
        m = 0
    return f"{d:02d}°{m:02d}'"


def compare_subject(s: Subject) -> None:
    utc = (s.local_dt - timedelta(hours=s.tz_offset_h)).replace(tzinfo=timezone.utc)
    print("=" * 90)
    print(f"SUBJECT: {s.name}    local={s.local_dt}  tz=+{s.tz_offset_h:+.2f}h  UTC={utc}")
    print(f"  lat={s.lat}  lon={s.lon}")

    sidereal_settings = {
        "mode": "true_sidereal_user_defined",
        "svp_degrees": 31.2836,
        "reference_year": 2000,
        "yearly_increment": 0.0,
    }
    astro = get_full_natal_chart(
        utc.replace(tzinfo=None), s.lat, s.lon,
        sidereal_settings=sidereal_settings, house_system="Equal",
    )
    hd = get_human_design_chart(
        utc.replace(tzinfo=None), s.lat, s.lon,
        sidereal_settings=sidereal_settings,
    )

    # Map planet -> Mirror computed personality data
    planets = astro.get("planets", {})
    angles  = astro.get("angles", {})

    print(f"\n  HD Personality Sun gate.line (Mirror): {hd.get('personality',{}).get('sun',{}).get('gate')}.{hd.get('personality',{}).get('sun',{}).get('line')}")
    print(f"  HD Design Sun     gate.line (Mirror): {hd.get('design',{}).get('sun',{}).get('gate')}.{hd.get('design',{}).get('sun',{}).get('line')}")
    print(f"  HD Type/Authority/Profile: {hd.get('type')} / {hd.get('authority')} / {hd.get('profile')}")
    print(f"  HD Definition: {hd.get('definition')}")
    print(f"  HD Incarnation Cross: {hd.get('incarnation_cross', {}).get('name')}")
    print(f"  HD Channels (Mirror): {sorted(hd.get('channels', []))}")

    print()
    print(f"  {'Body':<12} | {'Mirror compute':<35} | {'GM Personality':<25} | match")
    for body in ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto","NorthNode","Chiron"]:
        m = planets.get(body, {})
        sign = m.get("sign","-")
        deg  = m.get("degree_in_sign", m.get("degree", 0))
        gm = s.gm_personality.get(body, ("-","-","-","-"))
        mirror_str = f"{sign} {fmt_dm(deg)}"
        match = "OK" if gm[3] != "-" and abs(deg_in_sign_to_float(gm[3]) - deg) < 1.0 else "DIFF"
        print(f"  {body:<12} | {mirror_str:<35} | {gm[0]} / {gm[1]} / H{gm[2]} / {gm[3]:<10} | {match}")

    # Angles
    for ap in ["AC","MC","DC","IC"]:
        a = angles.get(ap.lower(), {}) or angles.get(ap, {})
        sign = a.get("sign","-")
        deg  = a.get("degree_in_sign", a.get("degree", 0))
        gm = s.gm_personality.get(ap, ("-","-","-","-"))
        mirror_str = f"{sign} {fmt_dm(deg)}"
        match = "OK" if gm[3] != "-" and abs(deg_in_sign_to_float(gm[3]) - deg) < 1.0 else "DIFF"
        print(f"  {ap:<12} | {mirror_str:<35} | {gm[0]} / {gm[1]} / H{gm[2]} / {gm[3]:<10} | {match}")


if __name__ == "__main__":
    for s in SUBJECTS:
        compare_subject(s)
