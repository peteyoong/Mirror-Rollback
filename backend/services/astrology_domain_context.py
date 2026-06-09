"""Domain-specific astrology retrieval — Mirror Chat v2.
Slice A: relationship fully populated; career/home/spiritual = scaffold.
Build marker: astrology-domain-context-v1
"""
from typing import Any, Dict, List, Optional

BUILD_MARKER = "astrology-domain-context-v1"

_RULERS = {  # traditional rulers — used for 7th-house ruler lookup
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
    "Ophiuchus": "Jupiter",  # forensic placeholder; not in production output
}


def _planets_in_house(planets: Dict[str, Dict], house_num: int) -> List[str]:
    return [name for name, p in (planets or {}).items()
            if isinstance(p, dict) and p.get("house") == house_num]


def _format_placement(p: Optional[Dict]) -> Optional[str]:
    if not p: return None
    sign = p.get("sign") or "?"
    house = p.get("house")
    deg = p.get("degree")
    s = f"{sign}"
    if deg is not None:
        s = f"{sign} {round(deg,1)}°"
    if house is not None:
        s += f" (H{house})"
    return s


def build_relationship_context(chart: Dict) -> Dict[str, Any]:
    """Pulls the partnership architecture from a chart object."""
    astro   = (chart or {}).get("astrology") or chart or {}
    planets = astro.get("planets") or {}
    houses  = astro.get("houses") or {}
    angles  = astro.get("angles") or {}

    # 7th house sign — read from the cusps list when available
    cusps = houses.get("formatted_cusps") or houses.get("cusps") or []
    house_7_sign = None
    if isinstance(cusps, list) and len(cusps) >= 7:
        c7 = cusps[6]
        if isinstance(c7, str):
            # Mirror stores cusps as e.g. "1° Capricorn"
            for sign in _RULERS:
                if sign in c7:
                    house_7_sign = sign; break
        elif isinstance(c7, dict):
            house_7_sign = c7.get("sign")

    # DC sign — directly from angles
    dc = angles.get("dc") or {}
    descendant_sign = dc.get("sign") or house_7_sign

    h7_ruler  = _RULERS.get(house_7_sign) if house_7_sign else None
    h7_ruler_placement = _format_placement(planets.get(h7_ruler)) if h7_ruler else None

    return {
        "descendant_sign":       descendant_sign,
        "house_7_sign":          house_7_sign,
        "house_7_planets":       _planets_in_house(planets, 7),
        "house_7_ruler":         h7_ruler,
        "house_7_ruler_placement": h7_ruler_placement,
        "venus":                 _format_placement(planets.get("Venus")),
        "juno":                  _format_placement(planets.get("Juno")),
        "moon":                  _format_placement(planets.get("Moon")),
        "house_4_planets":       _planets_in_house(planets, 4),
        "house_8_planets":       _planets_in_house(planets, 8),
    }


def build_career_context(chart: Dict) -> Dict[str, Any]:   # scaffold
    astro = (chart or {}).get("astrology") or chart or {}
    planets = astro.get("planets") or {}
    angles  = astro.get("angles") or {}
    return {
        "mc":              (angles.get("mc") or {}).get("sign"),
        "house_10_planets":_planets_in_house(planets, 10),
        "house_6_planets": _planets_in_house(planets, 6),
        "saturn":          _format_placement(planets.get("Saturn")),
        "sun":             _format_placement(planets.get("Sun")),
        "jupiter":         _format_placement(planets.get("Jupiter")),
    }


def build_home_context(chart: Dict) -> Dict[str, Any]:     # scaffold
    astro = (chart or {}).get("astrology") or chart or {}
    planets = astro.get("planets") or {}
    angles  = astro.get("angles") or {}
    return {
        "ic":              (angles.get("ic") or {}).get("sign"),
        "house_4_planets": _planets_in_house(planets, 4),
        "moon":            _format_placement(planets.get("Moon")),
    }


def build_spiritual_context(chart: Dict) -> Dict[str, Any]:  # scaffold
    astro = (chart or {}).get("astrology") or chart or {}
    planets = astro.get("planets") or {}
    return {
        "north_node": _format_placement(planets.get("North Node")),
        "chiron":     _format_placement(planets.get("Chiron")),
        "neptune":    _format_placement(planets.get("Neptune")),
    }


_DOMAIN_BUILDERS = {
    "relationship": build_relationship_context,
    "career":       build_career_context,
    "home":         build_home_context,
    "spiritual":    build_spiritual_context,
}


def build_domain_proof_block(domain: str, chart: Dict, target_name: str = "this person") -> str:
    """Build the strict 'Lead from X' proof block to prepend to the LLM prompt."""
    builder = _DOMAIN_BUILDERS.get(domain)
    if not builder: return ""
    ctx = builder(chart)

    if domain == "relationship":
        lines = [
            "\n=== DOMAIN PROOF BLOCK — RELATIONSHIP / MARRIAGE ===",
            f"Target: {target_name}",
            "",
            "DETERMINISTIC PLACEMENTS (read-only ground truth):",
            f"  • Descendant sign: {ctx.get('descendant_sign')}",
            f"  • 7th House sign: {ctx.get('house_7_sign')}",
            f"  • 7th House ruler: {ctx.get('house_7_ruler')} — {ctx.get('house_7_ruler_placement') or 'not located'}",
            f"  • Planets in 7th: {', '.join(ctx.get('house_7_planets') or []) or '(empty)'}",
            f"  • Venus: {ctx.get('venus')}",
            f"  • Juno:  {ctx.get('juno')}",
            f"  • Moon (emotional needs): {ctx.get('moon')}",
            f"  • Planets in 4th: {', '.join(ctx.get('house_4_planets') or []) or '(empty)'}",
            f"  • Planets in 8th: {', '.join(ctx.get('house_8_planets') or []) or '(empty)'}",
            "",
            "ABSOLUTE RULES (override earlier voice or safety guards):",
            "  1. LEAD with the partnership architecture. Open with what this",
            "     person learns about / seeks in partnership — derive it from",
            "     Descendant, 7th House sign, 7th-ruler placement, Venus, Juno.",
            "  2. The Moon, 4th House, and 8th House are SUPPORTING COLOR only,",
            "     not headline structures.",
            "  3. NEVER open the response with the Sun sign, Human Design type,",
            "     Enneagram type, or Numerology life path. These may appear",
            "     ONLY AFTER the partnership architecture has been explained.",
            "  4. Mirror voice: do NOT say 'Your Descendant is Gemini.' Instead",
            "     write the lived experience first, then add a 'Why this shows",
            "     up' section that names the structures.",
            "  5. The 'Why this is showing up' section must list at minimum:",
            "     Descendant, 7th House (and its sign), 7th ruler placement,",
            "     Venus, Juno.",
            "==================================================\n",
        ]
        return "\n".join(lines)

    # Scaffold for other domains — minimal instruction
    return (
        f"\n=== DOMAIN PROOF BLOCK — {domain.upper()} ===\n"
        f"Target: {target_name}\n"
        f"Context: {ctx}\n"
        "Lead from the structures shown; do not headline Sun/HD/numerology.\n"
        "==================================================\n"
    )
