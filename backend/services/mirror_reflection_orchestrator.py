"""mirror_reflection_orchestrator.py — Progressive-revelation synthesizer V1
=============================================================================

Build marker:  mirror-reflection-orchestrator-v1

Turns Knowledge Graph clusters into a single relationship-synthesis
story.  Every emitted line is traceable to one or more clusters; every
cluster is traceable to its source signals (and through them, back to
the lens engine output).
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

ORCHESTRATOR_VERSION = "mirror-reflection-orchestrator-v1.5"

# ─────────────────────────────────────────────────────────────────────
# V1.5.1 — Humanization + dedup / diversification layer
# Strips raw HD/astrology jargon from the *top-story* layer. Technical
# terms still appear in evidence_ladder.technical_refs (drill-down).
# ─────────────────────────────────────────────────────────────────────
import re as _re

_TECH_TERMS_PATTERN = _re.compile(
    r"\b("
    r"defined\s+Ajna|open\s+Ajna|Ajna(?!\w)|"
    r"defined\s+Sacral|open\s+Sacral|Sacral(?!\w)|"
    r"defined\s+Solar\s+Plexus|open\s+Solar\s+Plexus|Solar\s+Plexus|"
    r"defined\s+G[\s-]?Center|open\s+G[\s-]?Center|G[\s-]?Center|"
    r"defined\s+Throat|open\s+Throat|Throat(?!\w)|"
    r"defined\s+Spleen|open\s+Spleen|Spleen|"
    r"defined\s+Ego|open\s+Ego|Heart\s+Center|"
    r"defined\s+Root|open\s+Root|Root\s+Center|"
    r"defined\s+Head|open\s+Head|Head\s+Center|"
    r"defined\s+center|open\s+center|defined\s+centers|open\s+centers|"
    r"defined-?\s*(?:Ajna|Sacral|Solar\s+Plexus|Spleen|Throat|Root|Head|G[\s-]?Center|Heart|Ego)\b|"
    r"open-?\s*(?:Ajna|Sacral|Solar\s+Plexus|Spleen|Throat|Root|Head|G[\s-]?Center|Heart|Ego)\b|"
    r"Gate\s+\d{1,2}(?:\.\d)?|Channel\s+\d{1,2}-\d{1,2}|"
    r"Ten\s+God|lunar-?authority|splenic\s+authority|"
    r"\b\d{1,2}-\d{1,2}\b"
    r")\b",
    _re.IGNORECASE,
)

# Sentence-level rewrites — when the WHOLE sentence matches one of these
# patterns, the sentence is REPLACED by the clean text. The pattern
# matches optional possessive prefix (e.g. "Pete's") and end punctuation.
# Each tuple is (full_sentence_regex, clean_replacement).
_SENTENCE_REWRITES = [
    (_re.compile(
        r"^\s*(?P<who>[A-Z][\w'’]*?)?'?s?\s*defined\s+Ajna\s+amplifies\s+certainty[^.?!]*[.?!]?\s*$",
        _re.IGNORECASE),
     "One of you can become certain fast — that certainty starts pulling the room into shape before the other has decided anything."),
    (_re.compile(
        r"^\s*(?P<who>[A-Z][\w'’]*?)?'?s?\s*defined\s+Solar\s+Plexus[^.?!]*[.?!]?\s*$",
        _re.IGNORECASE),
     "One of you carries the emotional weather for both."),
    (_re.compile(
        r"^\s*(?P<who>[A-Z][\w'’]*?)?'?s?\s*open\s+Solar\s+Plexus[^.?!]*[.?!]?\s*$",
        _re.IGNORECASE),
     "One of you may absorb the other's emotional weather before knowing what's theirs."),
    (_re.compile(
        r"^\s*(?P<who>[A-Z][\w'’]*?)?'?s?\s*defined\s+Sacral[^.?!]*[.?!]?\s*$",
        _re.IGNORECASE),
     "One of you brings a steady body-yes the other can lean into."),
    (_re.compile(
        r"^\s*(?P<who>[A-Z][\w'’]*?)?'?s?\s*open\s+Sacral[^.?!]*[.?!]?\s*$",
        _re.IGNORECASE),
     "One of you may take on the other's energy and over-give before noticing."),
    (_re.compile(
        r"^\s*(?P<who>[A-Z][\w'’]*?)?'?s?\s*defined\s+(?:throat|G[\s-]?Center)[^.?!]*[.?!]?\s*$",
        _re.IGNORECASE),
     "One of you tends to set the direction the room moves toward."),
    (_re.compile(
        r".*\blunar-?authority\b[^.?!]*[.?!]?\s*",
        _re.IGNORECASE),
     "Give the side that needs time before deciding the time it actually needs."),
    (_re.compile(
        r".*\bsplenic\s+(authority|signals?)[^.?!]*[.?!]?\s*",
        _re.IGNORECASE),
     "Quiet, in-the-moment knowing doesn't repeat itself — listen the first time."),
    (_re.compile(
        r"^\s*Manifestor\s*[x×]\s*Reflector\s*[^.?!]*[.?!]?\s*$",
        _re.IGNORECASE),
     "One of you initiates; the other samples and reflects the field over time."),
    (_re.compile(
        r"^\s*Generator\s*[x×]\s*Projector\s*[^.?!]*[.?!]?\s*$",
        _re.IGNORECASE),
     "One of you responds with steady body-knowing; the other reads and guides."),
    # Catch any sentence that still has hyphenated "defined-Xxx" or
    # "open-Xxx" residue followed by "side's conclusions" — drop it.
    (_re.compile(
        r"^\s*[^.?!]*\b(?:open|defined)-?\s*[A-Z][a-z]+\b[^.?!]*?\bside'?s?\b[^.?!]*[.?!]?\s*$",
        _re.IGNORECASE),
     "One side's conclusions may carry more weight than the other's; check whose read is leading."),
]


# Phrase-level humanization mappings (run AFTER sentence rewrites for
# residual cleanup). Each tuple is (regex, replacement).
_HUMANIZE_PHRASES = [
    (_re.compile(r"centre\s+conditioning|center\s+conditioning", _re.IGNORECASE),
     "the way you each shape the atmosphere around the other"),
    # Backward-compatibility tail-end catch for sentences that escaped
    # the sentence-level rewrite (defensive only).
    (_re.compile(r"\b(?:open|defined)-the\s+field\s+between\s+you\b", _re.IGNORECASE),
     "the field between you"),
    (_re.compile(r"\bone\s+of\s+you\s+can\s+become\s+certain\s+so\s+fast[^.]*",
                 _re.IGNORECASE),
     "one of you can become certain fast"),
]


def _split_sentences(text: str):
    """Crude but safe sentence splitter that preserves trailing
    punctuation. Splits on '.', '!', '?' followed by whitespace or EOS."""
    parts = _re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p]


def _humanize(text: str) -> str:
    """Strip / soften raw HD jargon for top-story rendering. Idempotent.

    Strategy:
      1. Split into sentences.
      2. For each sentence that matches a known broken pattern,
         REPLACE the whole sentence with a clean rewrite.
      3. For each remaining sentence, run residual phrase replacements.
      4. As a last resort, drop sentences that STILL contain a
         technical token (no replacement could rescue them).
    """
    if not isinstance(text, str) or not text:
        return text

    out_sentences = []
    for sent in _split_sentences(text):
        rewritten = None
        # Try full-sentence rewrites first
        for pat, repl in _SENTENCE_REWRITES:
            if pat.search(sent):
                rewritten = repl
                break
        if rewritten is None:
            tmp = sent
            for pat, repl in _HUMANIZE_PHRASES:
                tmp = pat.sub(repl, tmp)
            # If technical token STILL leaks in this sentence, drop it.
            if _TECH_TERMS_PATTERN.search(tmp):
                # As a final resort, try a softer in-place strip — but
                # only when the resulting sentence still reads cleanly
                # (no compound residue like "defined-the field").
                tmp2 = _TECH_TERMS_PATTERN.sub("the field between you", tmp)
                tmp2 = _re.sub(r"(open|defined)-?\s*the\s+field\s+between\s+you",
                                "the field between you", tmp2, flags=_re.IGNORECASE)
                tmp2 = _re.sub(r"\b(\w+)'s\s+the\s+field\s+between\s+you",
                                r"the field between \1", tmp2, flags=_re.IGNORECASE)
                if _TECH_TERMS_PATTERN.search(tmp2):
                    # Still leaking — drop entirely.
                    continue
                rewritten = tmp2
            else:
                rewritten = tmp
        # Strip leading "<Name>'s " possessive that now precedes a clean
        # rewrite starting with "One of you..." or similar; turns
        # "Pete's One of you..." into "One of you...".
        rewritten = _re.sub(r"^[A-Z][\w'’]+'s\s+(?=One\s+of\s+you|The\s+other|Both\s+of\s+you|Give\s+|Quiet,)",
                            "", rewritten)
        out_sentences.append(rewritten.strip())

    # Reassemble with single spaces and tidy.
    out = " ".join(s for s in out_sentences if s).strip()
    out = _re.sub(r"\s+", " ", out)
    out = _re.sub(r"\s+([.;,!?])", r"\1", out)
    # Collapse repeated "the field between you" / duplicate phrases.
    out = _re.sub(r"(the field between you)(\s+\1)+", r"\1", out)
    # Also strip residual "Type pair: X × Y" diagnostic-only summaries
    out = _re.sub(r"^\s*Type\s+pair\s*:\s*[^.]+\.?\s*$",
                  "Two different mechanics meeting — the rhythm between you is its own thing.",
                  out, flags=_re.IGNORECASE)
    return out


def _normalize_for_dedupe(text: str) -> str:
    """Lowercased, punctuation-stripped, whitespace-collapsed dedupe key."""
    if not isinstance(text, str): return ""
    s = _re.sub(r"[^\w\s]", " ", text.lower())
    return _re.sub(r"\s+", " ", s).strip()


def _diversified_pick(clusters: List[Dict[str, Any]],
                       used_signal_ids: set,
                       used_text_keys: set,
                       polarity: Optional[str] = None,
                       theme: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Pick a cluster whose top signal is NOT already used. Falls back
    to any-cluster if needed."""
    candidates = list(clusters)
    if polarity:
        candidates = [c for c in clusters
                      if (c.get("polarity_tally") or {}).get(polarity)] or candidates
    if theme:
        candidates = [c for c in candidates if c.get("theme") == theme] or candidates
    for c in candidates:
        sigs_sorted = sorted(c.get("signals", []),
                              key=lambda s: -(s.get("strength", 0.5) * s.get("confidence", 0.5)))
        for s in sigs_sorted:
            sid = s.get("id")
            txt_key = _normalize_for_dedupe(s.get("summary", ""))
            if sid in used_signal_ids or (txt_key and txt_key in used_text_keys):
                continue
            used_signal_ids.add(sid)
            if txt_key:
                used_text_keys.add(txt_key)
            # Return a synthetic "cluster-like" pick keyed by chosen signal
            return {**c, "_chosen_signal": s}
    return None


FORBIDDEN = ("destiny", "destined", "soulmate", "meant to be",
             "karmic partner", "guaranteed compatibility",
             "prediction", "fortune telling", "fortune-telling")


def _find_forbidden(text: str) -> List[str]:
    if not isinstance(text, str) or not text: return []
    lower = text.lower()
    return [t for t in FORBIDDEN if t in lower]


def _pick_cluster_by_polarity(clusters: List[Dict[str, Any]],
                              polarity: str) -> Optional[Dict[str, Any]]:
    """Return the highest-agreement cluster where the requested polarity
    is the dominant tally."""
    best = None
    best_score = -1
    for c in clusters:
        tally = c.get("polarity_tally") or {}
        if not tally.get(polarity): continue
        score = c["agreement_score"] + 0.05 * c["lens_count"] + 0.02 * tally[polarity]
        if score > best_score:
            best_score = score; best = c
    return best


def _first_summary(cluster: Dict[str, Any]) -> str:
    if not cluster: return ""
    # Pick the signal in the cluster with the highest strength × confidence.
    sigs = sorted(cluster["signals"],
                  key=lambda s: -(s.get("strength", 0.5) * s.get("confidence", 0.5)))
    return (sigs[0]["summary"] if sigs else "").strip()


def _collect_repair_lines(clusters: List[Dict[str, Any]],
                          max_lines: int = 3) -> List[str]:
    seen: set = set()
    out: List[str] = []
    for c in clusters:
        if c["theme"] != "repair" and "repair" not in (c.get("polarity_tally") or {}):
            continue
        for s in sorted(c["signals"],
                        key=lambda x: -(x.get("strength", 0.5) * x.get("confidence", 0.5))):
            if s.get("polarity") != "repair": continue
            line = s.get("summary", "").strip()
            if line and line not in seen:
                seen.add(line); out.append(line)
                if len(out) >= max_lines: return out
    return out


def _confidence_score(clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not clusters:
        return {"level": "emerging", "score": 0, "reason": "No clusters produced."}
    top = clusters[0]
    high_conv = sum(1 for c in clusters if c["lens_count"] >= 3)
    mid_conv  = sum(1 for c in clusters if c["lens_count"] == 2)
    base = int(round(top["agreement_score"] * 60 + high_conv * 10 + mid_conv * 5))
    score = max(5, min(100, base))
    if high_conv >= 1 or top["lens_count"] >= 3:
        level = "high"
        reason = f"{high_conv or 1} theme(s) supported by 3+ lenses."
    elif mid_conv >= 1 or top["lens_count"] == 2:
        level = "medium"
        reason = f"{mid_conv} theme(s) supported by 2 lenses."
    else:
        level = "emerging"
        reason = "Single-lens insight; awaiting cross-lens confirmation."
    return {"level": level, "score": score, "reason": reason}


def _headline(clusters: List[Dict[str, Any]], name_a: str, name_b: str) -> str:
    if not clusters:
        return f"{name_a} and {name_b}: insufficient evidence to synthesize."
    top = clusters[0]
    theme = top["theme"].replace("_", " ").title()
    lc = top["lens_count"]
    lens_str = " + ".join(top["supporting_lenses"])
    if lc >= 3:
        return f"{theme} is the strongest signal between {name_a} and {name_b} ({lens_str} converge)."
    if lc == 2:
        return f"{theme} is the leading theme between {name_a} and {name_b} ({lens_str})."
    return f"{theme} is an emerging theme for {name_a} and {name_b} ({lens_str} only)."


def _question(top_cluster: Optional[Dict[str, Any]]) -> str:
    if not top_cluster: return ""
    theme = top_cluster.get("theme", "growth")
    Q = {
        "communication":     "Where are you each translating instead of speaking directly?",
        "pressure":          "Where does pressure get held silently instead of named?",
        "repair":            "When repair happens, who moves first — and is that sustainable?",
        "commitment":        "What have you committed to that no longer has the heart behind it?",
        "growth":            "What does this relationship ask each of you to grow into?",
        "identity":          "Whose sense of self is leading the room right now?",
        "timing":            "Whose rhythm is setting the pace — and is that intentional?",
        "emotional_clarity": "What decisions are being made before the emotional wave has settled?",
        "responsibility":    "What responsibility is being carried unevenly?",
        "belonging":         "Where do each of you feel most seen by the other?",
        "movement":          "What's moving between you that wasn't moving before?",
        "grounding":         "What needs to slow down before it can land?",
    }
    return Q.get(theme, "What does this connection make possible that nothing else does?")


ORCHESTRATOR_VERSION_OLD = "mirror-reflection-orchestrator-v1"
ORCHESTRATOR_VERSION_V15 = "mirror-reflection-orchestrator-v1.5"


def _build_evidence_ladder(story, clusters):
    """V1.5 — every story claim traces back to supporting signals,
    lens contributions, technical refs, and a provenance status rollup.
    No claim is invented; each line maps to an existing cluster's
    polarity-targeted pick or top signals.
    """
    ladder = []

    def _entry(claim_label, claim_text, cluster):
        if not cluster or not claim_text:
            return None
        sigs = cluster.get("signals") or []
        supporting = [{"signal_id": s.get("id"),
                        "lens": s.get("lens"),
                        "summary": s.get("summary"),
                        "polarity": s.get("polarity"),
                        "strength": s.get("strength"),
                        "confidence": s.get("confidence"),
                        "layer": s.get("layer"),
                        "mechanic": s.get("mechanic"),
                        "evidence_type": s.get("evidence_type"),
                        "provenance_status": (s.get("provenance") or {}).get("status")}
                      for s in sigs[:6]]
        lens_contrib = {}
        for s in sigs:
            lens_contrib[s.get("lens", "unknown")] = lens_contrib.get(s.get("lens", "unknown"), 0) + 1
        tech_refs = [{"signal_id": s.get("id"),
                      "lens": s.get("lens"),
                      "source_path": s.get("source_path"),
                      "data": s.get("technical")}
                     for s in sigs if s.get("technical")][:6]
        prov_rollup = cluster.get("provenance_status") or "unknown"
        return {
            "claim_label":         claim_label,
            "claim":               _humanize(claim_text),
            "claim_raw":           claim_text,
            "cluster_theme":       cluster.get("theme"),
            "supporting_signals":  supporting,
            "lens_contributions":  lens_contrib,
            "technical_refs":      tech_refs,
            "provenance_status":   ("verified" if prov_rollup == "verified"
                                    else ("suspect" if prov_rollup in ("suspect","stale","missing")
                                          else "mixed")),
            "agreement_score":     cluster.get("agreement_score"),
            "confidence_score":    cluster.get("confidence_score"),
            "drilldown_level":     "technical",
        }

    # Map each story slot to its origin cluster (re-derive cheaply).
    top              = clusters[0] if clusters else None
    movement_cluster = _pick_cluster_by_polarity(clusters, "movement") or top
    growth_cluster   = _pick_cluster_by_polarity(clusters, "growth") or top
    shadow_cluster   = (_pick_cluster_by_polarity(clusters, "shadow")
                        or _pick_cluster_by_polarity(clusters, "friction"))

    for label, claim, c in (
        ("headline",         story.get("headline"),         top),
        ("summary",          story.get("summary"),          top),
        ("current_movement", story.get("current_movement"), movement_cluster),
        ("growth_edge",      story.get("growth_edge"),      growth_cluster),
        ("shadow_pattern",   story.get("shadow_pattern"),   shadow_cluster),
        ("question_to_ask",  story.get("question_to_ask"),  top),
    ):
        entry = _entry(label, claim, c)
        if entry:
            ladder.append(entry)

    # Repair pathway entries (each line traces to its source cluster)
    for line in (story.get("repair_pathway") or []):
        # Find best cluster matching this line's text (deterministic).
        match = next((c for c in clusters
                      if any((s.get("summary") or "") == line
                             for s in c.get("signals") or [])), None) or top
        e = _entry("repair_pathway", line, match)
        if e: ladder.append(e)
    return ladder


def synthesize_relationship(
    signals: List[Dict[str, Any]],
    graph:   Dict[str, Any],
    name_a:  str = "You",
    name_b:  str = "them",
) -> Dict[str, Any]:
    clusters = graph.get("clusters") or []

    # Story slots — each derived from a polarity-targeted cluster pick.
    top                 = clusters[0] if clusters else None
    movement_cluster    = _pick_cluster_by_polarity(clusters, "movement") or top
    growth_cluster      = _pick_cluster_by_polarity(clusters, "growth") or top
    shadow_cluster      = _pick_cluster_by_polarity(clusters, "shadow")
    if not shadow_cluster:
        shadow_cluster = _pick_cluster_by_polarity(clusters, "friction")

    headline  = _headline(clusters, name_a, name_b)
    summary   = _first_summary(top) if top else ""

    # V1.5.1 — diversified picks: each story slot draws from a DISTINCT
    # signal whose text hasn't already been used. This prevents a single
    # high-strength signal from dominating headline/movement/shadow.
    _used_sids: set = set()
    _used_keys: set = set()
    head_pick = _diversified_pick(clusters, _used_sids, _used_keys)  # any-strongest
    movement_pick = _diversified_pick(clusters, _used_sids, _used_keys, polarity="movement")
    growth_pick = _diversified_pick(clusters, _used_sids, _used_keys, polarity="growth")
    shadow_pick = _diversified_pick(clusters, _used_sids, _used_keys, polarity="shadow") \
                   or _diversified_pick(clusters, _used_sids, _used_keys, polarity="friction")

    def _picked_summary(pick: Optional[Dict[str, Any]]) -> str:
        if not pick: return ""
        chosen = pick.get("_chosen_signal") or {}
        return (chosen.get("summary") or "").strip()

    story = {
        "headline":          _humanize(headline),
        "summary":           _humanize(summary),
        "current_movement":  _humanize(_picked_summary(movement_pick) or _first_summary(movement_cluster)),
        "growth_edge":       _humanize(_picked_summary(growth_pick)   or _first_summary(growth_cluster)),
        "shadow_pattern":    _humanize(_picked_summary(shadow_pick)   or (_first_summary(shadow_cluster) if shadow_cluster else "")),
        "repair_pathway":    [_humanize(line) for line in _collect_repair_lines(clusters, 3)],
        "question_to_ask":   _humanize(_question(top)),
    }

    # Final guard: dedupe across ALL story slots after humanization.
    _seen_keys: set = set()
    for slot in ("headline", "summary", "current_movement", "growth_edge", "shadow_pattern"):
        text = story.get(slot, "")
        if not text:
            continue
        key = _normalize_for_dedupe(text)
        if key in _seen_keys:
            story[slot] = ""  # blank duplicate slot rather than repeating
        else:
            _seen_keys.add(key)
    # Repair pathway dedupe
    seen_rp: set = set()
    rp_out: List[str] = []
    for line in story.get("repair_pathway", []) or []:
        k = _normalize_for_dedupe(line)
        if k and k not in seen_rp and k not in _seen_keys:
            seen_rp.add(k); rp_out.append(line)
    story["repair_pathway"] = rp_out

    # Evidence tray
    evidence_lines: List[str] = []
    lens_contributions: Dict[str, int] = {}
    technical_refs:  List[Dict[str, Any]] = []
    for c in clusters[:5]:
        for s in sorted(c["signals"],
                        key=lambda x: -(x.get("strength", 0.5) * x.get("confidence", 0.5)))[:2]:
            evidence_lines.append({
                "line":        s.get("summary"),
                "lens":        s.get("lens"),
                "source_path": s.get("source_path"),
                "signal_id":   s.get("id"),
                "theme":       s.get("theme"),
                "polarity":    s.get("polarity"),
                "strength":    s.get("strength"),
                "confidence":  s.get("confidence"),
            })
            lens_contributions[s.get("lens", "unknown")] = (
                lens_contributions.get(s.get("lens", "unknown"), 0) + 1
            )
            if s.get("technical"):
                technical_refs.append({
                    "signal_id": s.get("id"),
                    "lens":      s.get("lens"),
                    "data":      s.get("technical"),
                })

    # Forbidden language guard — defensive, since all upstream prose
    # already passes this check.  If anything slips through, surface it.
    flagged: List[str] = []
    for v in story.values():
        if isinstance(v, str):
            flagged.extend(_find_forbidden(v))
        elif isinstance(v, list):
            for item in v: flagged.extend(_find_forbidden(item))

    confidence = _confidence_score(clusters)

    # V1.5 — every story claim traces to supporting signals.
    evidence_ladder = _build_evidence_ladder(story, clusters)

    # V1.5.1 — `undertone_for_today` is a SHORT, deterministic, KG-derived
    # line that the frontend may render as a subtle subtitle underneath the
    # transit-based "Between You Today" hero. It is NOT a replacement for
    # transits/weather — strictly an architectural undertone.
    undertone = ""
    _LOW_VALUE_PREFIXES = (
        "type pair:", "authority pair:", "profile pair:", "definition pair:",
        "no electromagnetic", "no companion", "no compromise", "no dominance",
        "the field between you",
    )

    def _pick_undertone_from(cluster):
        if not cluster or not cluster.get("signals"):
            return ""
        for s in sorted(cluster["signals"], key=lambda x: -(x.get("strength", 0.5) * x.get("confidence", 0.5))):
            cand = _humanize((s.get("summary") or "").strip())
            if not cand or len(cand) < 18 or len(cand) >= 200:
                continue
            cand_l = cand.lower()
            if any(cand_l.startswith(p) for p in _LOW_VALUE_PREFIXES):
                continue
            if _normalize_for_dedupe(cand) in _seen_keys:
                continue
            # First letter must be a word char (avoid orphan punctuation residue)
            if not cand[0].isalpha():
                continue
            return cand
    # Walk top cluster first, then any subsequent clusters
    for c in clusters[:6]:
        candidate = _pick_undertone_from(c)
        if candidate:
            undertone = "Underneath today: " + candidate.rstrip(".") + "."
            break

    return {
        "story":      story,
        "undertone_for_today": undertone,
        "evidence": {
            "why_mirror_sees_this": evidence_lines,
            "lens_contributions":   lens_contributions,
            "technical_refs":       technical_refs,
        },
        "evidence_ladder": evidence_ladder,
        "confidence": confidence,
        "diagnostics": {
            "strongest_cluster": (top or {}).get("theme"),
            "clusters_used":     [c["theme"] for c in clusters[:5]],
            "signal_count":      len(signals),
            "lenses_present":    (graph.get("diagnostics") or {}).get("lenses_present", []),
            "forbidden_flagged": flagged,
            "engine_version":    ORCHESTRATOR_VERSION,
            "provenance_rollup": [{"theme": c.get("theme"),
                                   "status": c.get("provenance_status"),
                                   "penalty": c.get("provenance_penalty")}
                                  for c in clusters[:8]],
        },
    }
