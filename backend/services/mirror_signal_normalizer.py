"""mirror_signal_normalizer.py — Mirror Signal Normalization Layer V1
=====================================================================

Build marker:  mirror-signal-normalizer-v1

Converts deterministic lens outputs (Astrology, HD Field V3, BaZi V2,
Numerology V2-lite, Enneagram) into a shared evidence-signal format
that downstream graph + orchestrator services can consume.

This is purely a READ layer.  No lens engine is modified.  Output is
ephemeral per-request.  No DB writes.
"""
from __future__ import annotations
import hashlib
import re
from typing import Any, Dict, List, Optional

NORMALIZER_VERSION = "mirror-signal-normalizer-v1.5"

# ─────────────────────────────────────────────────────────────────────
# V1.5 — Evidence Ontology defaults
# ─────────────────────────────────────────────────────────────────────
# Per-lens defaults. Section overrides applied below.
_LENS_DEFAULT_ONTOLOGY: Dict[str, Dict[str, str]] = {
    "human_design": {"layer": "foundation", "mechanic": "conditioning", "evidence_type": "center", "drilldown_level": "lens"},
    "bazi":         {"layer": "season",     "mechanic": "timing",       "evidence_type": "bridge_element", "drilldown_level": "lens"},
    "numerology":   {"layer": "foundation", "mechanic": "identity",     "evidence_type": "life_path", "drilldown_level": "lens"},
    "astrology":    {"layer": "weather",    "mechanic": "timing",       "evidence_type": "natal", "drilldown_level": "lens"},
    "enneagram":    {"layer": "foundation", "mechanic": "conditioning", "evidence_type": "enneagram_type", "drilldown_level": "lens"},
}

# Section/keyword overrides — refine ontology based on signal content.
_MECHANIC_OVERRIDES: List[tuple] = [
    ("repair",       "repair"),
    ("communicat",   "communication"),
    ("listen",       "communication"),
    ("speak",        "communication"),
    ("control",      "control"),
    ("project",      "projection"),
    ("conditioning", "conditioning"),
    ("friction",     "friction"),
    ("amplif",       "amplification"),
    ("flow",         "flow"),
    ("rhythm",       "timing"),
    ("season",       "timing"),
    ("pace",         "timing"),
    ("identity",     "identity"),
]

_LAYER_OVERRIDES: List[tuple] = [
    ("season",        "season"),
    ("weather",       "weather"),
    ("today",         "weather"),
    ("current",       "weather"),
    ("opportunity",   "opportunity"),
    ("repair_pathway","opportunity"),
    ("memory",        "memory"),
    ("history",       "memory"),
]


def _infer_evidence_ontology(lens: str, section: str, summary: str) -> Dict[str, str]:
    """Deterministic ontology classifier. Backward-compatible: defaults
    fall back to per-lens defaults when no keyword match."""
    base = dict(_LENS_DEFAULT_ONTOLOGY.get(lens, {
        "layer": "foundation", "mechanic": "identity",
        "evidence_type": "natal", "drilldown_level": "lens",
    }))
    haystack = f"{section} {summary}".lower()
    for needle, mech in _MECHANIC_OVERRIDES:
        if needle in haystack:
            base["mechanic"] = mech
            break
    for needle, layer in _LAYER_OVERRIDES:
        if needle in haystack:
            base["layer"] = layer
            break
    return base


def _provenance_default(status: str = "unknown",
                        engine_version: Optional[str] = None,
                        source_input_status: str = "unknown") -> Dict[str, Any]:
    """V1.5 provenance carrier. NOT yet enforced; orchestrator + KG
    consume it to compute confidence penalties only."""
    return {
        "status":              status,
        "hash":                None,
        "engine_version":      engine_version,
        "computed_at":         None,
        "source_input_status": source_input_status,
        "confidence_penalty":  0.0,
    }

# Canonical theme vocabulary — every normalized signal must map to one.
CANONICAL_THEMES = (
    "communication", "pressure", "repair", "commitment", "growth",
    "identity", "timing", "emotional_clarity", "responsibility",
    "belonging", "movement", "grounding",
)

# Substring → theme mapping (longest-match wins).  Deterministic.
_THEME_HEURISTICS: List[tuple] = [
    ("emotional wave", "emotional_clarity"),
    ("emotional",       "emotional_clarity"),
    ("repair",          "repair"),
    ("28-day",          "timing"),
    ("wave",            "emotional_clarity"),
    ("commit",          "commitment"),
    ("responsibilit",   "responsibility"),
    ("officer",         "responsibility"),
    ("ground",          "grounding"),
    ("listen",          "communication"),
    ("speak",           "communication"),
    ("speech",          "communication"),
    ("voice",           "communication"),
    ("inform",          "communication"),
    ("translation",     "communication"),
    ("identity",        "identity"),
    ("belong",          "belonging"),
    ("pressure",        "pressure"),
    ("control",         "pressure"),
    ("movement",        "movement"),
    ("momentum",        "movement"),
    ("initiate",        "movement"),
    ("response",        "movement"),
    ("growth",          "growth"),
    ("learn",           "growth"),
    ("expand",          "growth"),
    ("structure",       "grounding"),
    ("steady",          "grounding"),
    ("clarity",         "emotional_clarity"),
    ("season",          "timing"),
    ("year",            "timing"),
    ("rhythm",          "timing"),
    ("pace",            "timing"),
    ("waiting",         "timing"),
]


def _classify_theme(text: str, fallback: str = "growth") -> str:
    if not isinstance(text, str): return fallback
    lower = text.lower()
    for needle, theme in _THEME_HEURISTICS:
        if needle in lower: return theme
    return fallback


def _sid(lens: str, lens_section: str, summary: str) -> str:
    """Deterministic short signal id."""
    h = hashlib.sha1(f"{lens}|{lens_section}|{summary}".encode("utf-8")).hexdigest()
    return f"{lens[:3]}_{h[:10]}"


def _clip(text: Any, n: int = 240) -> str:
    if not isinstance(text, str): return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= n else text[:n - 1].rsplit(" ", 1)[0] + "…"


def _signal(*, lens: str, section: str, summary: str,
            polarity: str, theme: str = None, strength: float = 0.7,
            confidence: float = 0.7, time_scope: str = "lifelong",
            domain: str = "relationship", subject_id: str = "a",
            object_id: Optional[str] = "b",
            technical: Optional[Dict[str, Any]] = None,
            provenance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    summary = _clip(summary)
    th = theme or _classify_theme(summary)
    ont = _infer_evidence_ontology(lens, section, summary)
    prov = provenance or _provenance_default(
        status="unknown", engine_version=NORMALIZER_VERSION,
        source_input_status="unknown",
    )
    return {
        "id":           _sid(lens, section, summary),
        "lens":         lens,
        "domain":       domain,
        "subject_id":   subject_id,
        "object_id":    object_id,
        "theme":        th,
        "polarity":     polarity,
        "time_scope":   time_scope,
        "strength":     round(max(0.0, min(1.0, strength)), 3),
        "confidence":   round(max(0.0, min(1.0, confidence)), 3),
        "source_path":  f"signals.{lens}.{section}",
        "summary":      summary,
        "technical":    technical or {},
        # ── V1.5 additive fields ──
        "layer":            ont["layer"],
        "mechanic":         ont["mechanic"],
        "evidence_type":    ont["evidence_type"],
        "drilldown_level":  ont["drilldown_level"],
        "provenance":       prov,
    }


# ─────────────────────────────────────────────────────────────────────
# HD Field V3 normalization
# ─────────────────────────────────────────────────────────────────────
def normalize_hd_field(hdf: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(hdf, dict): return []
    f = hdf.get("field_v3") or {}
    d = hdf.get("diagnostics") or {}
    out: List[Dict[str, Any]] = []
    LENS = "human_design"

    if f.get("energy_weather"):
        out.append(_signal(lens=LENS, section="energy_weather",
            summary=f["energy_weather"], polarity="evidence",
            theme=None, time_scope="lifelong", strength=0.7))
    if f.get("decision_dynamics"):
        out.append(_signal(lens=LENS, section="decision_dynamics",
            summary=f["decision_dynamics"], polarity="evidence",
            theme="emotional_clarity", strength=0.85, confidence=0.85,
            technical={"authority_pair": d.get("authority_pair")}))
    for line in (f.get("centre_conditioning") or [])[:3]:
        out.append(_signal(lens=LENS, section="centre_conditioning",
            summary=line, polarity="shadow",
            theme=_classify_theme(line, "pressure"),
            strength=0.75, confidence=0.8))
    for line in (f.get("repair_pathway") or [])[:5]:
        out.append(_signal(lens=LENS, section="repair_pathway",
            summary=line, polarity="repair",
            theme="repair", strength=0.85, confidence=0.85))
    for line in (f.get("friction_patterns") or [])[:4]:
        out.append(_signal(lens=LENS, section="friction_patterns",
            summary=line, polarity="friction",
            theme=_classify_theme(line, "pressure"),
            strength=0.7, confidence=0.75))
    if d.get("type_pair"):
        out.append(_signal(lens=LENS, section="diagnostics.type_pair",
            summary=f"Type pair: {d['type_pair']}", polarity="evidence",
            theme="identity", strength=0.95, confidence=0.95,
            technical={"type_pair": d["type_pair"]}))
    return out


# ─────────────────────────────────────────────────────────────────────
# BaZi V2 normalization
# ─────────────────────────────────────────────────────────────────────
def normalize_bazi(bazi_sigs: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(bazi_sigs, dict): return []
    card = bazi_sigs.get("v2_card") or {}
    diag = bazi_sigs.get("diagnostics") or {}
    out: List[Dict[str, Any]] = []
    LENS = "bazi"

    field_polarities = {
        "current_movement":              ("movement", "movement", "season"),
        "natural_strength":              ("support",  "growth",   "lifelong"),
        "shadow_pattern":                ("shadow",   "pressure", "lifelong"),
        "repair_pathway":                ("repair",   "repair",   "lifelong"),
        "how_they_help_each_other":      ("support",  "identity", "lifelong"),
        "how_they_challenge_each_other": ("friction", "pressure", "lifelong"),
        "growth_edge":                   ("growth",   "growth",   "lifelong"),
        "current_relationship_season":   ("evidence", "timing",   "season"),
    }
    for field, (polarity, theme, scope) in field_polarities.items():
        v = card.get(field)
        if isinstance(v, str) and v:
            out.append(_signal(lens=LENS, section=f"v2_card.{field}",
                summary=v, polarity=polarity, theme=theme,
                time_scope=scope, strength=0.8, confidence=0.85,
                technical={k: diag.get(k) for k in ("bridge_element",
                    "ten_gods_a_sees_b", "ten_gods_b_sees_a",
                    "day_master_relation") if k in diag}))
    # Diagnostic role-casting as its own signal
    if diag.get("ten_gods_a_sees_b") and diag.get("ten_gods_b_sees_a"):
        out.append(_signal(lens=LENS, section="diagnostics.ten_gods",
            summary=f"Role-casting: a→b={diag['ten_gods_a_sees_b']}, b→a={diag['ten_gods_b_sees_a']}",
            polarity="evidence", theme="identity", strength=0.85, confidence=0.9,
            technical={k: diag.get(k) for k in ("ten_gods_a_sees_b","ten_gods_b_sees_a")}))
    return out


# ─────────────────────────────────────────────────────────────────────
# Numerology V2-lite normalization
# ─────────────────────────────────────────────────────────────────────
def normalize_numerology(num_sigs: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(num_sigs, dict): return []
    card = num_sigs.get("v2_card") or {}
    diag = num_sigs.get("diagnostics") or {}
    out: List[Dict[str, Any]] = []
    LENS = "numerology"
    for theme_line in (num_sigs.get("themes") or [])[:3]:
        out.append(_signal(lens=LENS, section="themes",
            summary=theme_line, polarity="evidence", strength=0.7))
    field_polarities = {
        "core_dynamic":     ("evidence", "identity"),
        "natural_strength": ("support",  "growth"),
        "growth_edge":      ("growth",   "growth"),
        "shadow_pattern":   ("shadow",   "pressure"),
        "repair_pathway":   ("repair",   "repair"),
    }
    for field, (polarity, theme) in field_polarities.items():
        v = card.get(field)
        if isinstance(v, str) and v:
            out.append(_signal(lens=LENS, section=f"v2_card.{field}",
                summary=v, polarity=polarity, theme=theme,
                strength=0.75, confidence=0.8,
                technical={"pair_type": diag.get("pair_type")}))
    return out


# ─────────────────────────────────────────────────────────────────────
# Astrology normalization (best-effort; surfaces what's there)
# ─────────────────────────────────────────────────────────────────────
def normalize_astrology(astro_sigs: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(astro_sigs, dict): return []
    out: List[Dict[str, Any]] = []
    LENS = "astrology"
    card = (astro_sigs.get("v2_card") or astro_sigs.get("astrology_card") or {})
    candidate_keys = ("current_movement", "growth_edge", "shadow_pattern",
                      "repair_pathway", "core_dynamic", "natural_strength")
    polarity_map = {
        "current_movement": ("movement",  "movement"),
        "growth_edge":      ("growth",    "growth"),
        "shadow_pattern":   ("shadow",    "pressure"),
        "repair_pathway":   ("repair",    "repair"),
        "core_dynamic":     ("evidence",  "identity"),
        "natural_strength": ("support",   "growth"),
    }
    for k in candidate_keys:
        v = card.get(k)
        if isinstance(v, str) and v:
            pol, th = polarity_map[k]
            out.append(_signal(lens=LENS, section=f"v2_card.{k}",
                summary=v, polarity=pol, theme=th,
                strength=0.78, confidence=0.85))
    # Top-level evidence arrays
    for bucket, polarity in (("attraction","support"), ("tension","friction"), ("growth","growth")):
        for item in (astro_sigs.get(bucket) or [])[:3]:
            if isinstance(item, str) and item:
                out.append(_signal(lens=LENS, section=bucket,
                    summary=item, polarity=polarity, strength=0.6))
    return out


# ─────────────────────────────────────────────────────────────────────
# Enneagram normalization (assessment-dependent)
# ─────────────────────────────────────────────────────────────────────
def normalize_enneagram(enn_sigs: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(enn_sigs, dict): return []
    out: List[Dict[str, Any]] = []
    LENS = "enneagram"
    polarity_map = {
        "how_you_help_them":  ("support",  "growth"),
        "how_they_help_you":  ("support",  "growth"),
        "friction_pattern":   ("friction", "pressure"),
        "growth_edge":        ("growth",   "growth"),
    }
    for field, (pol, th) in polarity_map.items():
        v = enn_sigs.get(field)
        if isinstance(v, str) and v:
            out.append(_signal(lens=LENS, section=field, summary=v,
                polarity=pol, theme=th, strength=0.7, confidence=0.75))
        elif isinstance(v, (list, int)):
            for item in (v if isinstance(v, list) else [str(v)]):
                if isinstance(item, str) and item:
                    out.append(_signal(lens=LENS, section=field,
                        summary=item, polarity=pol, theme=th,
                        strength=0.6, confidence=0.7))
    return out


# ─────────────────────────────────────────────────────────────────────
# Public entry — full normalize from a mapping's signals block
# ─────────────────────────────────────────────────────────────────────
def normalize_signals(signals: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert a forum `mapping['signals']` dict into a flat list of
    normalized signals.  Safe on partial / missing inputs."""
    if not isinstance(signals, dict): return []
    out: List[Dict[str, Any]] = []
    out.extend(normalize_hd_field(signals.get("human_design_field") or {}))
    out.extend(normalize_bazi(signals.get("bazi") or {}))
    out.extend(normalize_numerology(signals.get("numerology") or {}))
    out.extend(normalize_astrology(signals.get("astrology") or {}))
    out.extend(normalize_enneagram(signals.get("enneagram") or {}))
    return out


def normalize_signals_v15(signals: Dict[str, Any],
                          provenance_by_lens: Optional[Dict[str, Dict[str, Any]]] = None
                          ) -> List[Dict[str, Any]]:
    """V1.5 wrapper. Calls `normalize_signals` and overlays per-lens
    provenance metadata onto each emitted signal. Backward-compatible:
    if `provenance_by_lens` is None, signals carry default provenance
    (status='unknown') already populated by `_signal`.

    `provenance_by_lens` shape:
        {
          "astrology":   { "status": "verified", "hash": "...", "engine_version": "...",
                           "computed_at": "...", "source_input_status": "valid",
                           "confidence_penalty": 0.0 },
          "human_design": {...},
          ...
        }
    """
    out = normalize_signals(signals)
    if not provenance_by_lens:
        return out
    for s in out:
        p = provenance_by_lens.get(s.get("lens"))
        if not p:
            continue
        s["provenance"] = {**(s.get("provenance") or {}), **p}
        # Optional confidence penalty applied here (carry-through; KG
        # also independently penalizes).
        pen = float(p.get("confidence_penalty") or 0.0)
        if pen > 0:
            s["confidence"] = round(max(0.0, s["confidence"] - pen), 3)
    return out
