"""
Forum Knowledge Retrieval Layer (FKR v1)
=========================================

Read-only retrieval layer wired into BOTH chat surfaces:
  * POST /api/mirror/chat            (Ask Mirror generalist)
  * POST /api/forums/{forum_id}/chat (in-forum chat)

Pipeline executed BEFORE the LLM call:

    User Question
       ↓
    classify_query()        — multi-label: FACT_LOOKUP / INTERPRETATION /
                              RELATIONSHIP / TIMELINE / COMPARISON /
                              FORUM_DYNAMICS
       ↓
    resolve_targets()       — extracts named people, "us/we" → spouse,
                              forum names, and the asking user
       ↓
    retrieve_evidence()     — pulls per-target facts from:
                              charts.astrology / charts.human_design
                              users.numerology / users.enneagram
                              forum_relationship_edges, forum_members,
                              forums, pattern_memory, user_timeline
       ↓
    build_evidence_block()  — emits a strict EVIDENCE block + a Phase-3
                              style MANDATORY enforcement footer.
       ↓
    LLM Response

Constraints honoured:
  * Pure reads.  No mutations, no new collections, no schema changes.
  * Does not modify the HD / astrology / timeline / relationship-field
    calculators.  Only consumes their stored outputs.
  * All four router/cutover/orchestration flags untouched.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from bson import ObjectId

log = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────
# Query classification
# ────────────────────────────────────────────────────────────

_FACT_LOOKUP_PATTERNS = [
    r"\bwhat is\b.*\b(mc|midheaven|ic|imum coeli|ascendant|asc|rising|"
    r"descendant|dc|sun|moon|chiron|north node|south node|venus|mars|"
    r"mercury|jupiter|saturn|uranus|neptune|pluto|profile|type|authority|"
    r"strategy|definition|incarnation cross|cross|centers?|channels?|"
    r"gates?|life path|expression|soul urge|birthday|destiny|"
    r"environment|variables?|enneagram|wing|instinct|"
    r"bazi|element|day master)\b",
    r"\bwhich (centers?|channels?|gates?|houses?|signs?)\b",
    r"\bwho is\b",
]
_INTERPRET_PATTERNS = [
    r"\bwhat does .* mean\b",
    r"\bexplain\b",
    r"\bhow does .* express\b",
    r"\binterpret\b",
    # P1 expansion — relational "need from me" reads as interpretation
    # AND relationship (multi-label).
    r"\bwhat does .+ need from (me|us)\b",
]
_RELATIONSHIP_PATTERNS = [
    r"\bhow does .* (affect|impact|map to|relate to) (me|us)\b",
    r"\btension between\b",
    r"\bbetween us\b",
    r"\bour (relationship|partnership|marriage|growth|argument|dynamic)\b",
    r"\bwhat are we\b",
    r"\bwe keep\b",
    r"\bus together\b",
    r"\bmap to me\b",
    r"\bdynamic with\b",
    # P1 expansion — natural-language relationship phrasings:
    r"\b\w+ and i\b",                       # "Mel and I", "Isaac and I"
    r"\b\w+ and me\b",                      # "Mel and me"
    r"\bwhat does \w+ need from (me|us)\b",
    r"\bhow is \w+ different from (me|us)\b",
    r"\bwhat keeps happening between\b",    # "between us / them"
    r"\bwhat (do|are) we (struggle|fight|argue|repeat)\b",
    r"\bwhat are we repeating\b",
    r"\bwhat are we working through\b",
]
_TIMELINE_PATTERNS = [
    r"\b(emerging|upcoming|next|future|moving through|going through|"
    r"transit|transits?|this year|right now)\b",
    r"\bwhat (is|are) .* going through\b",
]
_COMPARISON_PATTERNS = [
    r"\bcompare\b",
    r"\bdifference between\b",
    r"\bhow are .* (and|vs|versus|different)\b",
    r"\b(vs\.?|versus)\b",
    # P1 expansion — natural comparison phrasings without "compare/vs":
    r"\bhow is \w+ different from\b",
    r"\bhow do .* differ\b",                # "How do the boys differ", "how do my kids differ"
    r"\bwhich (one|child|kid|boy|girl|of \w+) is more\b",
    r"\bwhich (one|child|kid|boy|girl|of \w+) (does|is|has)\b",
    r"\bmore like (me|you|us)\b",
    r"\bwhich (\w+) (challenges|tests|stretches) me\b",
    r"\bstrengths complement\b",
]
_FORUM_DYNAMICS_PATTERNS = [
    r"\bwhat is happening in\b",
    r"\bwho is carrying\b",
    r"\bin the (family|team|forum|group)\b",
    r"\bforum dynamics?\b",
    # P1 expansion — natural forum-dynamic phrasings:
    r"\bwho (balances|complements|grounds|steadies|tensions?)\b",
    r"\bwho creates (the )?(most )?tension\b",
    r"\bwhat is (this|the|our) (group|family|team|forum)'?s? blind ?spot\b",
    r"\bblind ?spot\b",
    r"\bthis group\b",
    r"\bthis forum\b",
    r"\bthis (family|team)\b",
    r"\bwhat role does \w+ play\b",
    # P1B expansion — pre-ungating validation gap fixes:
    r"\bwhere (is|are) (the|our|my) (family|home|household|kids|boys|children)\b",
    r"\bwhere (is|are) (we|us|our) (growing|growing together|evolving)\b",
    r"\b(the|our|my) family (is|are|keeps|tends|moves|drifts|grows|shifts)\b",
    r"\btension (at home|in (the|our|my) (home|house|household|family))\b",
    r"\bat home\b.*\b(tension|conflict|dynamic|pattern|shift|grow|growing|emerging)\b",
    r"\b(tension|conflict|growth|growing edge|blind ?spot|pattern) (at home|in (the|our|my) (home|house|family))\b",
    # Loosened "at home" pattern — matches when "tension/conflict/growth"
    # appears anywhere in a sentence that ends with "at home" (real
    # phrasing: "What tension needs attention at home?").
    r"\b(tension|conflict|pattern|blind ?spot|growth|growing edge|need(s)?|happening|emerging)\b[^.?!]{0,60}\bat home\b",
    r"\bat home\b[^.?!]{0,60}\b(tension|conflict|pattern|growth|growing edge|emerging)\b",
    r"\bwhat (is|are) (we|the family|our family|our home) (going through|working on)\b",
    r"\bhow (is|are) (the|our) family (doing|moving|growing)\b",
]


def classify_query(message: str) -> List[str]:
    msg = (message or "").lower()
    modes: List[str] = []
    def _match(patterns: List[str]) -> bool:
        return any(re.search(p, msg, flags=re.I) for p in patterns)
    if _match(_FACT_LOOKUP_PATTERNS):     modes.append("FACT_LOOKUP")
    if _match(_INTERPRET_PATTERNS):       modes.append("INTERPRETATION")
    if _match(_RELATIONSHIP_PATTERNS):    modes.append("RELATIONSHIP")
    if _match(_TIMELINE_PATTERNS):        modes.append("TIMELINE")
    if _match(_COMPARISON_PATTERNS):      modes.append("COMPARISON")
    if _match(_FORUM_DYNAMICS_PATTERNS):  modes.append("FORUM_DYNAMICS")
    if not modes:
        # Default: any question with a possessive ("X's MC", "X's profile")
        # implies fact lookup; otherwise leave empty (the spec only requires
        # retrieval when classifiable).
        if re.search(r"\b\w+'s\b", msg):
            modes.append("FACT_LOOKUP")
    return modes


# ────────────────────────────────────────────────────────────
# Target resolution
# ────────────────────────────────────────────────────────────

def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()


async def _load_known_people(db, asker_id: str, scope_forum_id: Optional[str]
                             ) -> List[Dict[str, Any]]:
    """All forum-members across forums the asker belongs to (plus an
    optional scope forum override for in-forum chat)."""
    forum_ids: List[str] = []
    if scope_forum_id:
        forum_ids.append(scope_forum_id)
    async for m in db.forum_members.find({"user_id": asker_id}):
        fid = m.get("forum_id")
        if fid and fid not in forum_ids:
            forum_ids.append(fid)
    if not forum_ids:
        return []
    people: List[Dict[str, Any]] = []
    seen: set = set()
    async for m in db.forum_members.find({"forum_id": {"$in": forum_ids}}):
        uid = m.get("user_id")
        if not uid or uid == asker_id or uid in seen:
            continue
        seen.add(uid)
        people.append({
            "user_id": uid,
            "name": m.get("name") or m.get("display_name"),
            "forum_id": m.get("forum_id"),
        })
    # Resolve missing names from users.
    missing = [p["user_id"] for p in people if not p["name"]]
    if missing:
        try:
            objs = []
            for u in missing:
                try:
                    objs.append(ObjectId(u))
                except Exception:
                    objs.append(u)
            async for u in db.users.find({"_id": {"$in": objs}}):
                name = u.get("name") or u.get("first_name") or ""
                uid = str(u.get("_id"))
                for p in people:
                    if p["user_id"] == uid and not p["name"]:
                        p["name"] = name
        except Exception:
            pass
    return people


async def resolve_targets(*, db, user_id: str, message: str,
                          forum_id: Optional[str] = None
                          ) -> List[Dict[str, Any]]:
    """Returns list of {user_id, name, role, forum_id, source}.
    First entry is the asker themselves (always included)."""
    msg = (message or "").lower()
    asker: Dict[str, Any] = {
        "user_id": user_id, "name": "you", "role": "self",
        "forum_id": forum_id, "source": "asker",
    }
    targets: List[Dict[str, Any]] = [asker]

    people = await _load_known_people(db, user_id, forum_id)

    # Alias map for short forms.
    _short = {"melissa": "mel", "mel": "melissa",
              "thaddeus": "thad", "jaan": "jaan"}

    matched_uids: set = set()
    for p in people:
        if not p.get("name"):
            continue
        first = p["name"].split()[0].lower() if p["name"] else ""
        full  = p["name"].lower()
        aliases = {first, full}
        if first in _short:
            aliases.add(_short[first])
        for a in aliases:
            if not a:
                continue
            if re.search(rf"\b{re.escape(a)}\b", msg):
                if p["user_id"] in matched_uids:
                    continue
                matched_uids.add(p["user_id"])
                # Look up edge role.
                role = None
                try:
                    e = await db.forum_relationship_edges.find_one({
                        "from_user_id": user_id,
                        "to_user_id":   p["user_id"],
                    })
                    if e:
                        role = e.get("role_type")
                except Exception:
                    pass
                targets.append({
                    "user_id":  p["user_id"],
                    "name":     p["name"],
                    "role":     role or "forum_peer",
                    "forum_id": p.get("forum_id"),
                    "source":   "alias_match",
                })
                break

    # ── P1 group / plural resolution ────────────────────────────
    # Resolve common kinship plurals into the underlying set of
    # forum_relationship_edges.role_type-typed people.  Only fires when
    # the alias loop hasn't already resolved the same individuals.
    GROUP_PATTERNS = {
        "children": re.compile(
            r"\b("
            r"the boys|my boys|both boys|"
            r"the kids|my kids|both kids|"
            r"the children|my children|the babies|my babies|"
            r"both children|both of them|my offspring|"
            # "which child / which kid / which one of the kids / which of my children"
            r"which child|which kid|which boy|which girl|"
            r"which one of (the|my) (kids|children|boys|girls)|"
            r"which of (the|my) (kids|children|boys|girls)"
            r")\b",
            re.IGNORECASE,
        ),
        "family": re.compile(
            r"\b("
            r"our family|the family|my family|"
            r"at home|our home|our household|"
            r"in (the|our|my) (home|household|house)|"
            r"home (dynamic|life|environment|patterns?)"
            r")\b",
            re.IGNORECASE,
        ),
    }

    async def _expand_group(role_filter: List[str]) -> List[Dict[str, Any]]:
        """Pull from forum_relationship_edges where asker→to_user has a
        role_type in role_filter; return target dicts with names resolved."""
        found: List[Dict[str, Any]] = []
        try:
            cur = db.forum_relationship_edges.find({
                "from_user_id": user_id,
                "role_type":    {"$in": role_filter},
            })
            seen_uids: set = set()
            async for e in cur:
                tu = e.get("to_user_id")
                if not tu or tu in seen_uids or tu in matched_uids:
                    continue
                seen_uids.add(tu)
                # Resolve name from known_people first, then users.
                name = None
                fid  = e.get("forum_id")
                for p in people:
                    if p["user_id"] == tu:
                        name = p["name"]; fid = fid or p.get("forum_id")
                        break
                if not name:
                    try:
                        uobj = ObjectId(tu) if _looks_objectid(tu) else tu
                        u = await db.users.find_one({"_id": uobj})
                        if u:
                            name = u.get("name") or u.get("first_name")
                    except Exception:
                        pass
                found.append({
                    "user_id":  tu,
                    "name":     name or "(unknown)",
                    "role":     e.get("role_type") or "forum_peer",
                    "forum_id": fid,
                    "source":   "group_expansion",
                })
        except Exception:
            pass
        return found

    # children-group plurals
    if GROUP_PATTERNS["children"].search(msg):
        children = await _expand_group(["child"])
        for c in children:
            if c["user_id"] not in matched_uids:
                matched_uids.add(c["user_id"])
                targets.append(c)

    # family-group plural — include spouse + children (and any other
    # explicit kinship edges) only.  We deliberately do NOT pull
    # every forum_member because "the family" implies kin, not
    # acquaintance.
    if GROUP_PATTERNS["family"].search(msg):
        family = await _expand_group(["spouse", "child", "parent", "sibling"])
        for c in family:
            if c["user_id"] not in matched_uids:
                matched_uids.add(c["user_id"])
                targets.append(c)

    pronoun_match = bool(re.search(
        r"\b(between us|we keep|what are we|our relationship|our marriage|"
        r"our growth|our argument|us together|the two of us)\b", msg))
    spouse_bound = any(t.get("role") == "spouse" for t in targets)
    if pronoun_match and not spouse_bound:
        try:
            cur = db.forum_relationship_edges.find({
                "from_user_id": user_id,
                "role_type":    "spouse",
                "confidence":   {"$in": ["high", "medium"]},
            })
            unique_to: List[str] = []
            sample_forum: Optional[str] = None
            async for e in cur:
                t = e.get("to_user_id")
                if t and t not in unique_to:
                    unique_to.append(t)
                    sample_forum = sample_forum or e.get("forum_id")
            if len(unique_to) == 1:
                tu = unique_to[0]
                # Resolve name.
                name = None
                for p in people:
                    if p["user_id"] == tu:
                        name = p["name"]; break
                if not name:
                    try:
                        uobj = ObjectId(tu) if _looks_objectid(tu) else tu
                        u = await db.users.find_one({"_id": uobj})
                        if u:
                            name = u.get("name") or u.get("first_name")
                    except Exception:
                        pass
                if tu not in matched_uids:
                    targets.append({
                        "user_id":  tu, "name": name or "(spouse)",
                        "role":     "spouse",
                        "forum_id": sample_forum,
                        "source":   "spouse_auto_bind",
                    })
        except Exception:
            pass

    return targets


def _looks_objectid(s: Any) -> bool:
    return isinstance(s, str) and bool(re.fullmatch(r"[0-9a-fA-F]{24}", s))


# ────────────────────────────────────────────────────────────
# Evidence retrieval (per target)
# ────────────────────────────────────────────────────────────

async def retrieve_for_target(db, t: Dict[str, Any]) -> Dict[str, Any]:
    """All graph facts for one target.  Each missing source returns
    None — the LLM is instructed to say 'not on file' for None facts."""
    uid = t.get("user_id")
    ev: Dict[str, Any] = {"target": t, "person": None, "hd": None,
                          "astro": None, "numerology": None,
                          "enneagram": None, "forum": None,
                          "pattern": None, "timeline": None}
    if not uid:
        return ev
    # Person profile.
    try:
        uobj = ObjectId(uid) if _looks_objectid(uid) else uid
        u = await db.users.find_one({"_id": uobj})
        if u:
            ev["person"] = {
                "name":  u.get("name") or u.get("first_name"),
                "email": u.get("email"),
                "dob":   u.get("birth_date") or u.get("dob"),
                "tob":   u.get("birth_time") or u.get("tob"),
                "place": u.get("birth_place") or u.get("location"),
            }
            ev["numerology"] = u.get("numerology") or None
            ev["enneagram"] = u.get("enneagram") or u.get("enneagram_profile")
    except Exception:
        pass
    # Chart (HD + astrology).
    try:
        ch = await db.charts.find_one({"user_id": uid})
        if ch:
            hd = ch.get("human_design") or {}
            astro = ch.get("astrology") or {}

            def _ic_name(hd_doc: Dict[str, Any]) -> Optional[str]:
                """Extract the canonical Incarnation Cross display name from
                whichever schema variant the chart was stored under.  Returns
                a plain string ('Right Angle Cross of Sleeping Phoenix 1')
                or None if no name is present.  NEVER guesses."""
                if not isinstance(hd_doc, dict):
                    return None
                for k in ("incarnation_cross", "cross",
                          "incarnation_cross_details"):
                    v = hd_doc.get(k)
                    if isinstance(v, str) and v.strip():
                        return v.strip()
                    if isinstance(v, dict):
                        for nk in ("name", "cross_name", "display_name"):
                            nv = v.get(nk)
                            if isinstance(nv, str) and nv.strip():
                                return nv.strip()
                return None

            ev["hd"] = {
                "type":              hd.get("type"),
                "strategy":          hd.get("strategy"),
                "authority":         hd.get("authority"),
                "profile":           hd.get("profile"),
                "definition":        hd.get("definition"),
                "incarnation_cross": _ic_name(hd),
                "defined_centers":   hd.get("defined_centers")
                                       or hd.get("centers"),
                "undefined_centers": hd.get("undefined_centers"),
                "channels":          hd.get("channels"),
                "active_gates":      (hd.get("active_gates")
                                      or hd.get("gates")),
                "environment":       hd.get("environment"),
                "motivation":        hd.get("motivation"),
                "variables":         hd.get("variables"),
            }
            planets = astro.get("planets") or {}
            angles  = astro.get("angles") or {}
            def _fmt(p): return (p or {}).get("formatted") \
                                  or (p or {}).get("sign")
            ev["astro"] = {
                "sun":         _fmt(planets.get("Sun")),
                "moon":        _fmt(planets.get("Moon")),
                "mercury":     _fmt(planets.get("Mercury")),
                "venus":       _fmt(planets.get("Venus")),
                "mars":        _fmt(planets.get("Mars")),
                "jupiter":     _fmt(planets.get("Jupiter")),
                "saturn":      _fmt(planets.get("Saturn")),
                "uranus":      _fmt(planets.get("Uranus")),
                "neptune":     _fmt(planets.get("Neptune")),
                "pluto":       _fmt(planets.get("Pluto")),
                "chiron":      _fmt(planets.get("Chiron")),
                "north_node":  _fmt(planets.get("North Node")
                                    or planets.get("NorthNode")),
                "south_node":  _fmt(planets.get("South Node")
                                    or planets.get("SouthNode")),
                "ascendant":   _fmt(angles.get("asc")
                                    or angles.get("ascendant")),
                "midheaven":   _fmt(angles.get("mc")
                                    or angles.get("midheaven")),
                "descendant":  _fmt(angles.get("dc")
                                    or angles.get("descendant")),
                "ic":          _fmt(angles.get("ic")),
            }
    except Exception as e:
        log.warning(f"[fkr] chart load failed for {uid}: {e!r}")
    # Pattern memory.
    try:
        patterns = []
        async for p in db.pattern_memory.find({"user_id": uid}).limit(5):
            patterns.append({
                "pattern":   p.get("pattern"),
                "intensity": p.get("intensity"),
                "summary":   p.get("summary"),
            })
        if patterns:
            ev["pattern"] = patterns
    except Exception:
        pass
    # Timeline (last few events).
    try:
        tl = []
        async for ev_tl in db.user_timeline.find({"user_id": uid})\
                            .sort("timestamp", -1).limit(5):
            tl.append({
                "type":      ev_tl.get("event_type"),
                "state":     ev_tl.get("inferred_state"),
                "summary":   ev_tl.get("summary"),
                "tags":      ev_tl.get("tags"),
                "timestamp": ev_tl.get("timestamp"),
            })
        if tl:
            ev["timeline"] = tl
    except Exception:
        pass
    return ev


async def retrieve_forum_evidence(db, forum_id: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {"forum_id": forum_id, "name": None,
                           "members": []}
    if not forum_id:
        return out
    try:
        try:
            fobj = ObjectId(forum_id)
        except Exception:
            fobj = forum_id
        f = await db.forums.find_one({"_id": fobj})
        if f:
            out["name"] = f.get("name")
            out["forum_type"] = f.get("forum_type")
        async for m in db.forum_members.find({"forum_id": forum_id}):
            out["members"].append({
                "user_id": m.get("user_id"),
                "name": m.get("name") or m.get("display_name"),
                "role": m.get("role"),
            })
        # Resolve missing names.
        missing = [m["user_id"] for m in out["members"] if not m["name"]]
        if missing:
            objs = []
            for u in missing:
                try:
                    objs.append(ObjectId(u))
                except Exception:
                    objs.append(u)
            async for u in db.users.find({"_id": {"$in": objs}}):
                nm = u.get("name") or u.get("first_name") or ""
                uid_s = str(u.get("_id"))
                for m in out["members"]:
                    if m["user_id"] == uid_s and not m["name"]:
                        m["name"] = nm
    except Exception:
        pass
    return out


# ────────────────────────────────────────────────────────────
# Evidence block builder
# ────────────────────────────────────────────────────────────

def _label(target: Dict[str, Any]) -> str:
    n = target.get("name") or "(target)"
    role = target.get("role")
    return f"{n}" + (f" ({role})" if role and role != "self" else "")


def _astro_lines(astro: Optional[Dict[str, Any]]) -> List[str]:
    if not astro:
        return ["  Astrology: not on file"]
    lines: List[str] = []
    for k, label in [
        ("sun", "Sun"), ("moon", "Moon"), ("ascendant", "Ascendant"),
        ("midheaven", "Midheaven / MC"), ("ic", "IC"),
        ("descendant", "Descendant / DC"),
        ("mercury", "Mercury"), ("venus", "Venus"), ("mars", "Mars"),
        ("jupiter", "Jupiter"), ("saturn", "Saturn"),
        ("uranus", "Uranus"), ("neptune", "Neptune"), ("pluto", "Pluto"),
        ("chiron", "Chiron"),
        ("north_node", "North Node"), ("south_node", "South Node"),
    ]:
        v = astro.get(k)
        if v:
            lines.append(f"    {label}: {v}")
    return lines or ["  Astrology: stored but no resolvable planets"]


def _hd_lines(hd: Optional[Dict[str, Any]]) -> List[str]:
    if not hd:
        return ["  Human Design: not on file"]
    lines = []
    for k, label in [
        ("type", "Type"), ("strategy", "Strategy"),
        ("authority", "Authority"), ("profile", "Profile"),
        ("definition", "Definition"),
        ("incarnation_cross", "Incarnation Cross"),
        ("environment", "Environment"),
        ("motivation", "Motivation"),
    ]:
        v = hd.get(k)
        if v:
            lines.append(f"    {label}: {v}")
    def_c = hd.get("defined_centers")
    if def_c and isinstance(def_c, (list, tuple)):
        lines.append("    Defined centers: " + ", ".join(map(str, def_c)))
    elif isinstance(def_c, dict):
        defs = [k for k, v in def_c.items() if v]
        if defs:
            lines.append("    Defined centers: " + ", ".join(defs))
    und_c = hd.get("undefined_centers")
    if und_c and isinstance(und_c, (list, tuple)):
        lines.append("    Undefined centers: " + ", ".join(map(str, und_c)))
    ch = hd.get("channels")
    if ch and isinstance(ch, (list, tuple)):
        lines.append(f"    Channels: {', '.join(str(c) for c in ch[:8])}"
                     + (f" (+{len(ch)-8} more)" if len(ch) > 8 else ""))
    return lines or ["  Human Design: stored but no resolvable fields"]


def build_evidence_block(modes: List[str],
                         targets: List[Dict[str, Any]],
                         evidence: List[Dict[str, Any]],
                         forum: Optional[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append("=" * 60)
    lines.append("FKR v1 — KNOWLEDGE RETRIEVAL EVIDENCE")
    lines.append("Query modes: " + ", ".join(modes) if modes else
                 "Query modes: (no specific mode classified)")
    lines.append("=" * 60)

    for t, ev in zip(targets, evidence):
        if t.get("source") == "asker":
            header = f"\nASKER ({_label(t)})"
        else:
            header = f"\nTARGET: {_label(t)} — source={t.get('source')}"
        lines.append(header)
        person = ev.get("person")
        if person:
            lines.append(f"  Name: {person.get('name')}")
            if person.get("dob"):
                lines.append(f"  Birth date: {person.get('dob')}")
            if person.get("place"):
                lines.append(f"  Birth place: {person.get('place')}")
        lines.append("  -- HUMAN DESIGN --")
        lines.extend(_hd_lines(ev.get("hd")))
        lines.append("  -- ASTROLOGY --")
        lines.extend(_astro_lines(ev.get("astro")))
        num = ev.get("numerology")
        if num:
            lines.append("  -- NUMEROLOGY --")
            for k, v in (num.items() if isinstance(num, dict) else []):
                if v:
                    lines.append(f"    {k}: {v}")
        enn = ev.get("enneagram")
        if enn:
            lines.append("  -- ENNEAGRAM --")
            if isinstance(enn, dict):
                for k, v in enn.items():
                    if v:
                        lines.append(f"    {k}: {v}")
            else:
                lines.append(f"    {enn}")
        if t.get("source") != "asker" and t.get("role"):
            lines.append("  -- RELATIONSHIP --")
            lines.append(f"    Role: {t.get('role')}")
            if t.get("forum_id"):
                lines.append(f"    Forum id: {t.get('forum_id')}")
        patt = ev.get("pattern")
        if patt:
            lines.append("  -- PATTERN MEMORY --")
            for p in patt[:3]:
                lines.append(f"    • {p.get('pattern')} "
                             f"(intensity={p.get('intensity')}): "
                             f"{(p.get('summary') or '')[:160]}")
        tl = ev.get("timeline")
        if tl:
            lines.append("  -- TIMELINE (recent) --")
            for e in tl[:3]:
                lines.append(f"    • [{e.get('state')}] "
                             f"{e.get('type')}: "
                             f"{(e.get('summary') or '')[:160]}")

    if forum and forum.get("forum_id"):
        lines.append(f"\nFORUM CONTEXT: {forum.get('name') or '(unnamed)'}")
        lines.append(f"  forum_id: {forum.get('forum_id')}")
        if forum.get("members"):
            names = ", ".join(m.get("name") or "(?)"
                              for m in forum["members"][:8])
            lines.append(f"  Members ({len(forum['members'])}): {names}")

    # Phase-3 style enforcement footer.
    lines.append("")
    lines.append("=" * 60)
    lines.append("MANDATORY (FKR v1 enforcement):")
    lines.append("  • Answer FROM the EVIDENCE block above, not from memory.")
    lines.append("  • If a fact is listed above, USE THE EXACT STORED VALUE — "
                 "do NOT paraphrase, do NOT substitute a similar one.")
    lines.append("  • If a fact is marked 'not on file', say so explicitly — "
                 "do NOT invent a value.")
    lines.append("  • For FACT_LOOKUP queries, lead the answer with the "
                 "exact stored value (e.g. 'Isaac's Midheaven is …', "
                 "'Thaddeus's Incarnation Cross is …').")
    lines.append("  • For RELATIONSHIP queries, name both parties and the "
                 "relationship role explicitly.")
    lines.append("  • For COMPARISON queries, name BOTH targets and contrast "
                 "their stored values side-by-side.")
    lines.append("  • For FORUM_DYNAMICS queries, name the forum and at "
                 "least one member by name.")
    lines.append("  • For TIMELINE queries, lean on the TIMELINE recent "
                 "entries above; do not invent transit dates.")
    lines.append("  • Hallucination is a sprint-blocking defect — if "
                 "uncertain, prefer 'not on file' over a guess.")
    lines.append("=" * 60)
    return "\n".join(lines)


# ────────────────────────────────────────────────────────────
# Top-level orchestration
# ────────────────────────────────────────────────────────────

async def build_fkr_evidence_block(
    *, db, user_id: str, message: str,
    forum_id: Optional[str] = None,
) -> Tuple[Optional[str], Dict[str, Any]]:
    """Returns (evidence_block_string_or_None, debug_payload)."""
    debug: Dict[str, Any] = {"emitted": False, "modes": [],
                             "targets": [], "errors": []}
    try:
        modes = classify_query(message)
        debug["modes"] = modes
        targets = await resolve_targets(
            db=db, user_id=user_id, message=message, forum_id=forum_id,
        )
        debug["targets"] = [
            {"name": t.get("name"), "role": t.get("role"),
             "source": t.get("source")} for t in targets
        ]
        # Skip if only the asker resolved AND no forum scope.
        if len(targets) == 1 and not forum_id and \
           not any(m in modes for m in
                   ("FORUM_DYNAMICS", "TIMELINE", "RELATIONSHIP",
                    "FACT_LOOKUP", "INTERPRETATION")):
            return None, debug
        evidence = []
        for t in targets:
            ev = await retrieve_for_target(db, t)
            evidence.append(ev)
        forum_ev = None
        if forum_id:
            forum_ev = await retrieve_forum_evidence(db, forum_id)
        block = build_evidence_block(modes, targets, evidence, forum_ev)
        debug["emitted"] = True
        debug["block_chars"] = len(block)
        return block, debug
    except Exception as e:
        log.warning(f"[fkr] build failed: {type(e).__name__}: {e!r}")
        debug["errors"].append(f"{type(e).__name__}: {e!r}")
        return None, debug
