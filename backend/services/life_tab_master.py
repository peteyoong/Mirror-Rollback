"""
Life Tab Master Voice
=====================

Build marker: life-tab-master-voice-v1

This is Mirror's *integrative reflective intelligence* for the Life Tab
chats (Relationships / Work / Self).  Where lens chats sound like
"Astrology says X, HD says Y, BaZi says Z", the Life Tab should sound
like ONE coherent voice that has internalised all of those signals and
speaks BEHAVIOURALLY about the user's lived experience.

NB: this module DOES NOT replace the memory / compression / intensity /
relational / pattern / anti-locking layers.  Those still run.  The only
thing this module replaces is the *single-lens voice* — with a
multi-lens synthesis voice.

Public API:
    compose_master_voice_blocks(
        user_context,
        domain,
        user_message,
        history,
        max_history_turns=6,
    ) -> (system_block_text: str, debug_payload: dict)

The returned debug_payload includes:
    - marker:                "life-tab-master-voice-v1"
    - domain:                "relationships" | "work" | "self"
    - contributing_frameworks: [str]      # e.g. ["astrology", "enneagram"]
    - dominant_signal:       {framework, signal, why}  | None
    - depth_mode:            "LIGHT" | "NORMAL" | "DEEP"
    - intensity_mode:        "SOFT" | "OBSERVATIONAL" | "DIRECT" | "CONFRONTING"
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from services.lens_conversation import (
    detect_depth_mode,
    detect_intensity_mode,
    format_compression_block,
    format_history_block,
    format_intensity_block,
)


# ---------------------------------------------------------------------------
# 1.  Behavioural signal extractors per framework.
#     Translate framework-native data into PLAIN-LANGUAGE behavioural cues.
#     No "Saturn", "Gate 43", "Life Path", "Enneagram 5", "Day Master Wood"
#     in the output.  Only "tends to over-function under pressure",
#     "comes alive when things are open-ended", etc.
# ---------------------------------------------------------------------------


# Enneagram → behavioural read per type.  Compact: ONE line per axis.
# Keys are leading digit; "4w5" / "7w8" notation tolerated via [0] slice.
_ENN_BEHAVIOUR: Dict[str, Dict[str, str]] = {
    "1": {
        "self":          "lives with a strict inner standard that runs even when no one is watching",
        "relationships": "expresses love through correction and being reliable, sometimes more than through warmth",
        "work":          "carries responsibility heavily, struggles to leave imperfect work alone",
    },
    "2": {
        "self":          "finds identity through being needed; rest can feel uncomfortable",
        "relationships": "leans in fast, attuned to others, sometimes loses own needs in the process",
        "work":          "over-extends helping; says yes before checking own bandwidth",
    },
    "3": {
        "self":          "self-worth bound to performance; struggles to feel real outside of output",
        "relationships": "shapes presentation to win the room; intimacy lands when the polish drops",
        "work":          "highly capable; runs on visibility, achievement, momentum",
    },
    "4": {
        "self":          "locates identity in depth, longing, what's missing; suspicious of generic experience",
        "relationships": "pulled toward intensity, hard to feel ordinary contentment as enough",
        "work":          "needs meaning to engage; struggles when work feels soulless",
    },
    "5": {
        "self":          "conserves inner resources, knowing replaces touching, slow to take up space",
        "relationships": "loves through clarity and reliability; emotional demand is the costliest expense",
        "work":          "deep in a niche, anti-spectacle, can starve presence of energy",
    },
    "6": {
        "self":          "vigilance and trust testing are the operating system; safety is earned",
        "relationships": "loyal once trust is real; until then, scans for the catch",
        "work":          "anticipates risk, can confuse anxiety-in-service with anxiety-as-problem",
    },
    "7": {
        "self":          "moves toward possibility and pain-reframe; the depth is real but tends to keep moving",
        "relationships": "energising, hard to pin; intimacy is the harder track",
        "work":          "generates ideas faster than finishes them; resists constraint",
    },
    "8": {
        "self":          "agency-protective, big presence, tenderness lives underneath and is well-guarded",
        "relationships": "direct, protective; vulnerability is the rare currency",
        "work":          "decisive, occupies space, can flatten quieter voices without meaning to",
    },
    "9": {
        "self":          "organised around inner peace; own preferences often surface last",
        "relationships": "blends, accommodates, can disappear from own life inside relationships",
        "work":          "steady and underrated; struggles when forced to choose",
    },
}


# Numerology → behavioural read per life-path digit.
_LP_BEHAVIOUR: Dict[str, Dict[str, str]] = {
    "1": {
        "self":          "drives toward originality and being first; uncomfortable when imitating",
        "relationships": "leads, sets direction; struggles to let someone else carry the wheel",
        "work":          "needs autonomy; thrives when allowed to build the new thing",
    },
    "2": {
        "self":          "attuned to others, peace-keeping, can collapse own preference to keep harmony",
        "relationships": "wired for partnership; reads the room more than the self",
        "work":          "thrives in cooperative settings; less suited to lone-wolf roles",
    },
    "3": {
        "self":          "expressive, creative, plays with ideas and form; flat structures feel airless",
        "relationships": "communicative, performative; depth shows up when the audience disappears",
        "work":          "needs creative latitude; languages and ideas are the medium",
    },
    "4": {
        "self":          "builds the structure others lean on; rest competes with the to-do list",
        "relationships": "loyal and reliable; can prioritise the system over the soft moment",
        "work":          "operationally strong; deep capacity for follow-through",
    },
    "5": {
        "self":          "moves toward freedom and variety; constraints rapidly chafe",
        "relationships": "needs room; intimacy works when the door stays unlocked",
        "work":          "thrives in change; can lose interest when the work calcifies",
    },
    "6": {
        "self":          "organised around care and responsibility; rest can read as neglect to self",
        "relationships": "the caretaker; absorbs others' load, sometimes invisibly",
        "work":          "service-oriented; pulled toward people-work and meaning",
    },
    "7": {
        "self":          "inward, reflective, suspicious of surface; comfort in solitude",
        "relationships": "real connection beats lots of connection; small circle, deep reads",
        "work":          "depth before breadth; thrives in research, analysis, craft",
    },
    "8": {
        "self":          "power-aware; thinks in terms of leverage, resource, scale",
        "relationships": "respects honest negotiation; struggles with passivity in others",
        "work":          "executive instincts; comfortable holding consequence",
    },
    "9": {
        "self":          "carries a bigger arc than the immediate one; restless inside small frames",
        "relationships": "loves widely; sometimes the global concern overrides the local one",
        "work":          "thrives when the work has meaning beyond the individual unit",
    },
    "11": {
        "self":          "highly sensitive antenna; intuition arrives before reasoning catches up",
        "relationships": "reads people fast; can absorb others' field before sorting from own",
        "work":          "visionary instinct; flat operational work drains quickly",
    },
    "22": {
        "self":          "build-it-large impulse; structural imagination paired with practical hands",
        "relationships": "loyal to the long arc; can be slow to articulate the soft side",
        "work":          "thrives at scale; builds institutions, not just artefacts",
    },
    "33": {
        "self":          "service orientation paired with high self-expectation; gives more than asks",
        "relationships": "cares deeply; can over-give to the point of self-erasure",
        "work":          "pulled toward meaning-work; struggles when work feels purely transactional",
    },
}


# Astrology → behavioural read per Sun sign.  Compact, behaviour-first.
_SUN_BEHAVIOUR: Dict[str, Dict[str, str]] = {
    "Aries":       {"self": "moves first, asks later; identity tied to action",
                    "relationships": "direct, initiating; can collide with slower rhythms",
                    "work": "thrives starting things; less interested in maintenance"},
    "Taurus":      {"self": "steady, embodied, slow to change; needs the body fed and seated",
                    "relationships": "reliable, sensuous; slow to enter and slow to leave",
                    "work": "marathoner, not sprinter; resists pressure to rush"},
    "Gemini":      {"self": "lives in language and connection; idea-rich, attention-divided",
                    "relationships": "talkative, curious; intimacy shows up in the third hour, not the first",
                    "work": "thrives juggling; struggles with deep single-track work"},
    "Cancer":      {"self": "feeling-organised; protects the inner field; takes a while to come out",
                    "relationships": "nurturing, loyal; needs emotional safety before opening",
                    "work": "carries the team's emotional climate, sometimes invisibly"},
    "Leo":         {"self": "needs presence and recognition; alive when seen, withdraws when overlooked",
                    "relationships": "warm, generous; conflict often about being unwitnessed",
                    "work": "performs best with visibility; thrives on creative leadership"},
    "Virgo":       {"self": "service-and-discernment wired; struggles to leave imperfect things alone",
                    "relationships": "shows love through care, attention to detail; harder with messiness",
                    "work": "highly capable; can over-function and burn quietly"},
    "Libra":       {"self": "weighs constantly; identity stabilises in relationship",
                    "relationships": "wired for partnership; can collapse own preference to keep harmony",
                    "work": "diplomatic, collaborative; struggles with unilateral decision-making"},
    "Scorpio":     {"self": "intense, private; doesn't trust surface, prefers what's beneath",
                    "relationships": "loyal, deep; reveals slowly, then completely",
                    "work": "investigative, thorough; uncomfortable in performative roles"},
    "Sagittarius": {"self": "horizon-seeking; restless inside small frames; meaning-hungry",
                    "relationships": "freedom-loving; intimacy works when the door stays open",
                    "work": "thrives with autonomy and bigger purpose; chafes under fine constraint"},
    "Capricorn":   {"self": "structure-organised; carries weight early, ages well",
                    "relationships": "loyal, slow-warming; expresses care through reliability",
                    "work": "executive instincts; comfortable with long horizons and consequence"},
    "Aquarius":    {"self": "lives slightly outside the system; tribe-oriented, slightly distant in 1:1",
                    "relationships": "loyal but spacious; intimacy without merging",
                    "work": "thrives in mission-work; struggles with hierarchy without meaning"},
    "Pisces":      {"self": "porous, intuitive, feels everything; needs solitude to digest",
                    "relationships": "deeply compassionate; can lose self inside other",
                    "work": "thrives in creative or healing fields; struggles in hard-edge environments"},
}


# Human Design → behavioural read per type.
_HD_BEHAVIOUR: Dict[str, Dict[str, str]] = {
    "Generator":         {"self": "energy responds to what's in front; building when truly lit, frustrated when forcing",
                          "relationships": "shows up consistently; struggles to say no when the body says yes",
                          "work": "sustained energy when the work matches; depleted when chasing"},
    "Manifesting Generator": {"self": "non-linear, multi-track, sees shortcuts; can skip steps that mattered",
                              "relationships": "fast-moving, intense bursts of attention; can leave gaps",
                              "work": "thrives juggling several projects; bored by single-focus"},
    "Projector":         {"self": "designed to see systems and others; needs invitation to land deeply",
                          "relationships": "perceptive, attuned; can feel invisible when not invited in",
                          "work": "thrives advising and guiding; burns out trying to do it all themselves"},
    "Manifestor":        {"self": "initiating energy; needs to inform others before acting to avoid friction",
                          "relationships": "independent; the friction is usually about consultation, not love",
                          "work": "thrives starting and leaving; less suited to maintenance"},
    "Reflector":         {"self": "highly sensitive to environment; identity shifts with the field",
                          "relationships": "barometer for the relational climate; takes time to know own truth",
                          "work": "needs the right environment more than most; toxic teams cost more"},
}


# BaZi → behavioural read per Day Master element (strategic stance).
_BAZI_BEHAVIOUR: Dict[str, Dict[str, str]] = {
    "Wood":  {"self": "growth-oriented, expansive; struggles when boxed in",
              "relationships": "generative, supportive; can over-extend nurturing others",
              "work": "good at building; struggles with cutting things"},
    "Fire":  {"self": "expressive, visible; identity tied to being seen and warming the room",
              "relationships": "passionate, demonstrative; cools fast when withdrawn from",
              "work": "thrives in front-of-room work; less suited to silent labour"},
    "Earth": {"self": "stabilising, gathering, holds the centre; can over-absorb others' weight",
              "relationships": "the one people lean on; struggles to ask for the same in return",
              "work": "operationally trustworthy; can carry too much load before naming it"},
    "Metal": {"self": "refining, clarifying, cuts away what's not essential; can be too pruning",
              "relationships": "precise care; affection shows up as honesty more than effusion",
              "work": "thrives with structure and standards; struggles with sloppy systems"},
    "Water": {"self": "fluid, deep, adaptive; needs flow more than form",
              "relationships": "attuned, intuitive; can mirror others until own shape is hard to find",
              "work": "thrives in roles that require reading the field; struggles in rigid structures"},
}


# ---------------------------------------------------------------------------
# 2.  Public extractor — pull all behavioural signals available for the user.
# ---------------------------------------------------------------------------


def extract_behavioral_signals(
    user_context: Dict[str, Any],
    domain: str,
) -> List[Dict[str, str]]:
    """
    Returns a ranked list of behavioural signal dicts:
        [{framework, signal, why}, ...]

    Higher = stronger / more confident.  Used by the master voice to lead
    with ONE dominant signal and (optionally) reach for one supporting
    signal.  No framework names appear in `signal`; framework name is
    tracked only in the debug provenance.
    """
    dom = (domain or "self").strip().lower()
    if dom not in ("relationships", "work", "self"):
        dom = "self"

    signals: List[Dict[str, str]] = []

    user = user_context.get("user") or {}
    chart = user_context.get("chart") or {}
    enneagram_results = user_context.get("enneagram_results") or {}
    bazi_chart = user_context.get("bazi_chart") or {}

    # --- Enneagram (highest-confidence behavioural signal when present) ----
    enn_type: Optional[str] = None
    try:
        # Prefer explicit `core_type` from results, fall back to user doc.
        et = (
            (enneagram_results or {}).get("core_type")
            or (user.get("enneagram") or {}).get("type")
            or user.get("enneagram_type")
        )
        if et is not None:
            enn_type = str(et).strip()
    except Exception:
        enn_type = None
    if enn_type:
        digit = enn_type[0] if enn_type[0].isdigit() else None
        if digit and digit in _ENN_BEHAVIOUR:
            signals.append({
                "framework": "enneagram",
                "signal": _ENN_BEHAVIOUR[digit][dom],
                "why": f"core type {digit}",
            })

    # --- Numerology life path -----------------------------------------------
    lp: Optional[str] = None
    try:
        n = (user.get("numerology") or {})
        lp_raw = n.get("life_path") or n.get("life_path_number")
        if lp_raw is not None:
            lp = str(lp_raw).strip()
    except Exception:
        lp = None
    if lp and lp in _LP_BEHAVIOUR:
        signals.append({
            "framework": "numerology",
            "signal": _LP_BEHAVIOUR[lp][dom],
            "why": f"life-path {lp}",
        })

    # --- Astrology Sun sign --------------------------------------------------
    sun_sign: Optional[str] = None
    try:
        astro = (chart or {}).get("astrology") or {}
        sun = (astro.get("planets") or {}).get("Sun") or astro.get("sun") or {}
        sun_sign = (sun.get("sign") or "").strip().capitalize() or None
        if not sun_sign:
            # Some charts store sun_sign at the top.
            sun_sign = (astro.get("sun_sign") or "").strip().capitalize() or None
    except Exception:
        sun_sign = None
    if sun_sign and sun_sign in _SUN_BEHAVIOUR:
        signals.append({
            "framework": "astrology",
            "signal": _SUN_BEHAVIOUR[sun_sign][dom],
            "why": f"Sun in {sun_sign}",
        })

    # --- Human Design type --------------------------------------------------
    hd_type: Optional[str] = None
    try:
        hd = (chart or {}).get("human_design") or {}
        t = hd.get("type") or hd.get("energy_type") or (user.get("human_design") or {}).get("type")
        if t:
            hd_type = str(t).strip().title()
            if hd_type.startswith("Manifesting Gen"):
                hd_type = "Manifesting Generator"
    except Exception:
        hd_type = None
    if hd_type and hd_type in _HD_BEHAVIOUR:
        signals.append({
            "framework": "human_design",
            "signal": _HD_BEHAVIOUR[hd_type][dom],
            "why": f"{hd_type} type",
        })

    # --- BaZi Day Master element --------------------------------------------
    day_master: Optional[str] = None
    try:
        bz = bazi_chart or (chart or {}).get("bazi") or {}
        dm = bz.get("day_master") or {}
        if isinstance(dm, dict):
            day_master = (dm.get("element") or "").strip().title()
        elif isinstance(dm, str):
            day_master = dm.strip().title()
    except Exception:
        day_master = None
    if day_master and day_master in _BAZI_BEHAVIOUR:
        signals.append({
            "framework": "bazi",
            "signal": _BAZI_BEHAVIOUR[day_master][dom],
            "why": f"Day Master {day_master}",
        })

    # --- Zi Wei / Purple Star structural anchor ----------------------------
    # Pulls a single behavioural recognition per domain from the user's
    # Zi Wei profile (Career / Marriage / Life palace anchors).  Lazy
    # compute is safe because the interpreter is stable per birth data.
    try:
        from services.zi_wei_interpreter import get_or_compute_profile as _zw_profile
        zw = _zw_profile(user_context)
        if zw and zw.get("available"):
            anchor_palace = {
                "self":          "Life",
                "relationships": "Marriage",
                "work":          "Career",
            }.get(dom, "Life")
            anchor = next(
                (p for p in zw.get("palaces", []) if p.get("palace") == anchor_palace),
                None,
            )
            if anchor and anchor.get("behavioural_signal"):
                signals.append({
                    "framework": "zi_wei",
                    "signal": anchor["behavioural_signal"],
                    "why": f"{anchor_palace} palace structural anchor",
                })
    except Exception:
        # Zi Wei is optional — never block master voice on failure.
        pass

    return signals


# ---------------------------------------------------------------------------
# 3.  Domain-aware master-voice stance prompts.
# ---------------------------------------------------------------------------


_MASTER_VOICE_PREAMBLE = """\
--- LIFE TAB MASTER VOICE (life-tab-master-voice-v1) ---

You are NOT speaking from a single interpretive system.  You are speaking
as Mirror's integrative reflective intelligence — one voice that has
quietly internalised what astrology, Human Design, numerology, BaZi and
the Enneagram each show about this person, and now speaks BEHAVIOURALLY.

Default voice rules (apply at EVERY turn unless the user explicitly
overrides them):

  1. PLAIN LANGUAGE BY DEFAULT.
     Do NOT name "Saturn", "Gate 43", "Life Path 7", "Enneagram 5",
     "Day Master Wood", "Mercury retrograde", or any framework jargon.
     Speak about the user's PATTERN OF BEHAVIOUR, not its symbolic source.

  2. SYNTHESIS, NOT STACKING.
     The signals below are inputs that have already been resolved into
     behavioural recognitions.  Do NOT say "astrology says X and HD
     says Y".  Speak as one voice that has weighed and integrated them.

  3. ONE DOMINANT SIGNAL.
     Lead with the strongest behavioural pattern.  You may reach for
     ONE supporting signal — only if it sharpens the answer.  Never
     more than two threads in a single reply.

  4. RECOGNITIONAL, NOT DECLARATIVE.
     "This pattern tends to show up when…", "There is a familiar
     shape to this…", "Something in you organises around…".  Avoid
     "you are an X person".  Speak about patterns, conditions, and
     what is currently alive — not about identity.

  5. REVEAL FRAMEWORKS ONLY WHEN ASKED.
     If the user asks "why is this showing up?", "what part of my
     chart is this?", "is this astrology or HD?", "what's the
     evidence?" — only then is it appropriate to name the underlying
     framework.  Even then: name lightly, then keep going.

  6. LIVED EXPERIENCE > SYMBOLIC MECHANICS.
     The user should leave feeling "this understands my situation",
     not "this gave me a reading".

  7. PRESERVE AMBIGUITY.
     Recognition, not verdict.  Stay probabilistic, contextual,
     field-aware.  People are not internally consistent — hold both
     sides of the contradiction when needed.
"""


_DOMAIN_STANCE: Dict[str, str] = {
    "relationships": """\
DOMAIN: RELATIONSHIPS
Focus areas: attachment, reciprocity, emotional distance, projection,
conflict patterns, relational loops.

Stance:
  - Speak to the FIELD between people, not just the user's chart.
  - Honour both sides of a dynamic; never recruit the user against
    another person.
  - When a pattern repeats across relationships, name it as a pattern
    of the user's relational nervous system — not as a fixed identity.
  - Vulnerability, withdrawal, over-functioning, attachment anxiety,
    intimacy block, distance, control — these are the operating
    vocabulary.  Never "your 7th house" or "your defined Heart".
""",
    "work": """\
DOMAIN: WORK
Focus areas: pressure, ambition, visibility, exhaustion, leadership,
authority dynamics, meaning vs responsibility, capacity.

Stance:
  - Speak to STRUCTURE and PRESSURE.  How does this person hold
    pressure?  What kind of work environment does their nervous
    system actually run on?
  - Notice when ambition is healthy vs. when it's a defence.  Notice
    when exhaustion is from over-functioning vs. from misalignment.
  - Authority dynamics matter: boss / direct reports / cofounders /
    clients each land differently on this person.
  - The user should feel SEEN as a worker, not as a chart.  Never
    "your Saturn return" or "your 10th house".
""",
    "self": """\
DOMAIN: SELF
Focus areas: identity, emotional regulation, internal contradiction,
growth edge, recurring self-patterns, what is alive right now.

Stance:
  - Speak to the INNER WEATHER.  What is the user organising around
    inside themselves?  What pattern keeps surfacing?
  - Make room for contradiction — humans aren't internally consistent.
    Hold both sides without trying to collapse them.
  - Growth edge over pathology.  Where is the user already changing,
    even slightly, and how can that be reflected back gently?
  - Identity is dynamic.  Avoid "you are X" framings.  Prefer
    "something in you is organising around X right now".
""",
}


def _format_signals_block(signals: List[Dict[str, str]]) -> str:
    """
    Render the behavioural-signal block.  Framework names are ALLOWED
    here because this is the LLM's internal context, not the user-facing
    output.  The voice prompt instructs the LLM to translate these
    signals into plain language for the user.
    """
    if not signals:
        return (
            "--- BEHAVIOURAL SIGNALS (life-tab-master-voice-v1) ---\n"
            "No framework signals are currently computed for this user.\n"
            "Speak honestly: lean on what the user shares about their\n"
            "lived experience.  Do NOT invent signals.  Do NOT default to\n"
            "generic coaching language."
        )
    lines = ["--- BEHAVIOURAL SIGNALS (life-tab-master-voice-v1) ---"]
    lines.append("Internal context.  Use these as recognitions to weigh;")
    lines.append("do NOT name the framework in your reply unless the user")
    lines.append("explicitly asks where the read is coming from.")
    lines.append("")
    for i, s in enumerate(signals[:5]):
        marker = "DOMINANT" if i == 0 else "supporting"
        lines.append(
            f"  - [{marker}] {s.get('signal','').strip()}"
            f"   (provenance: {s.get('framework','?')} — {s.get('why','')})"
        )
    lines.append("")
    lines.append("Lead with the DOMINANT signal.  Pull in ONE supporting")
    lines.append("signal only if it sharpens THIS answer.  Never stack.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 4.  Public composer
# ---------------------------------------------------------------------------


def compose_master_voice_blocks(
    user_context: Dict[str, Any],
    domain: str,
    user_message: str,
    history: List[Dict[str, str]],
    max_history_turns: int = 6,
) -> Tuple[str, Dict[str, Any]]:
    """
    Build the Life Tab master-voice system block + debug payload.

    Reuses lens_conversation's depth + intensity helpers (lens-agnostic)
    so the compression and emotional-timing axes stay coherent across all
    surfaces.  Intensity is computed with lens_name="life_master" so the
    universal ceilings still apply (per lens_conversation defaults
    DIRECT — i.e. life-tab will NOT reach CONFRONTING unless the user
    explicitly invites and the ceiling logic permits).
    """
    dom = (domain or "self").strip().lower()
    if dom not in ("relationships", "work", "self"):
        dom = "self"

    signals = extract_behavioral_signals(user_context, dom)

    # Reuse lens_conversation helpers — they're framework-agnostic.
    depth_mode = detect_depth_mode(user_message, history)
    intensity_mode = detect_intensity_mode(user_message, history, lens_name="life_master")

    blocks: List[str] = []
    blocks.append(_MASTER_VOICE_PREAMBLE.rstrip())
    blocks.append(_DOMAIN_STANCE.get(dom, _DOMAIN_STANCE["self"]).rstrip())
    blocks.append(_format_signals_block(signals))
    history_block = format_history_block(history, max_turns=max_history_turns)
    if history_block:
        blocks.append(history_block)
    blocks.append(format_compression_block(depth_mode))
    blocks.append(format_intensity_block(intensity_mode, lens_name="life_master"))

    system_block = "\n\n".join(b for b in blocks if b)

    contributing = []
    seen = set()
    for s in signals:
        f = s.get("framework")
        if f and f not in seen:
            seen.add(f)
            contributing.append(f)

    debug: Dict[str, Any] = {
        "marker": "life-tab-master-voice-v1",
        "domain": dom,
        "contributing_frameworks": contributing,
        "signals_count": len(signals),
        "dominant_signal": (
            {
                "framework": signals[0].get("framework"),
                "signal":    signals[0].get("signal"),
                "why":       signals[0].get("why"),
            } if signals else None
        ),
        "depth_mode": depth_mode,
        "intensity_mode": intensity_mode,
        # narrative-flexibility-v1 / relational-awareness-v1 layers are
        # still applied by the dispatcher on top of this block.
    }
    return system_block, debug
