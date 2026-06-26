"""hd_channel_narrative.py — per-channel relationship narrative
================================================================
Build marker: hd-channel-narrative-v1

For every completed Human-Design relationship channel, produce a
deterministic narrative triplet:

    {
      "gift":          one sentence — what this channel opens between you
      "tension":       one sentence — the watch-out / shadow if unmanaged
      "practical_use": one sentence — a concrete way to engage it
    }

Strict rules:
  • No mystical fatalism, no "destiny / soulmate / karmic" language.
  • Names are inlined (no `{name_a}` placeholders surfacing).
  • Curated overrides take precedence over template fallback.
  • Output is idempotent and depends only on the (channel_id,
    channel_name, theme, relational, name_a, name_b) tuple.

This module is ADDITIVE.  It does not mutate channel-completion math.
"""
from __future__ import annotations
from typing import Dict, Any

NARRATIVE_VERSION = "hd-channel-narrative-v1"

# ─────────────────────────────────────────────────────────────────────
# Curated per-channel narratives — written in grounded, human voice.
# Keys MUST be the canonical "low-high" channel id used in HD_CHANNELS.
# Templates may use {a} and {b} for names.
# ─────────────────────────────────────────────────────────────────────
CURATED: Dict[str, Dict[str, str]] = {
    "1-8": {
        "gift": "{a} brings the original spark, {b} gives it shape — together you make new work feel inevitable rather than risky.",
        "tension": "If one of you tries to predict the other's voice, the freshness dies; the channel rewards letting each person sound exactly like themselves.",
        "practical_use": "Show the raw idea before polishing it — let the other react in real time, not to a finished version.",
    },
    "2-14": {
        "gift": "Direction tends to find you both when you're together; opportunities surface that wouldn't have surfaced alone.",
        "tension": "Without naming who's responding to what, you can drift — busy but pointed nowhere in particular.",
        "practical_use": "Check in monthly on what each of you is actually being called toward — name it out loud.",
    },
    "3-60": {
        "gift": "You can move through real change together without falling apart — one of you names the limit, the other finds the way through.",
        "tension": "Restlessness can spike before either of you is ready to act; small frustrations can read as crisis.",
        "practical_use": "When the pressure rises, pause for one week before any big move — let the new form arrive on its own timing.",
    },
    "4-63": {
        "gift": "You can think hard things through with each other — doubt becomes a workable question instead of a private spiral.",
        "tension": "Logic loops are easy to get stuck in; one of you may want an answer faster than the actual answer is ready.",
        "practical_use": "Write the question down. Sleep on it. Come back tomorrow — the channel needs a beat between doubt and resolution.",
    },
    "5-15": {
        "gift": "Your natural rhythms align — eating, sleeping, working, resting tend to sync up without much effort.",
        "tension": "When timing diverges, the whole connection can feel off, even when nothing concrete is wrong.",
        "practical_use": "Protect one shared rhythm — a meal, a walk, a weekly check-in — and let other timings flex around it.",
    },
    "6-59": {
        "gift": "Emotional walls drop faster than usual; intimacy here is the real kind, not the performed kind.",
        "tension": "The same channel that opens closeness can also rush it — bond before either of you has chosen the depth.",
        "practical_use": "Name when you feel the pull. Slowness is allowed. Closeness lasts longer when it's chosen, not absorbed.",
    },
    "10-20": {
        "gift": "Together you become more openly yourselves — less filtering, less performance, more truth in the room.",
        "tension": "Raw honesty can land as bluntness; what feels like courage to one can feel like a hit to the other.",
        "practical_use": "Say the true thing — and then ask how it landed before moving on.",
    },
    "13-33": {
        "gift": "One of you speaks while the other deeply absorbs — the listener often sees more than the speaker realises.",
        "tension": "The listening side can quietly start to feel unseen if they never get reflected back.",
        "practical_use": "Trade roles weekly: whoever was held by the other names what they were actually trying to say.",
    },
    "21-45": {
        "gift": "Resources, money, direction — these become a shared project naturally; you can actually build something together.",
        "tension": "If responsibility for the build goes unspoken, one of you ends up carrying more than was agreed.",
        "practical_use": "Make the contract visible while it's still small — who decides what, who owns what, when do you revisit it.",
    },
    "25-51": {
        "gift": "You initiate things together that neither of you would have started alone — the activation in the room is real.",
        "tension": "Initiating before agreement is the failure mode; one of you may move while the other is still considering.",
        "practical_use": "Before any big start, take one breath together. If both are in, go. If not, name what's missing.",
    },
    "27-50": {
        "gift": "You instinctively look out for what matters to each other — care happens before being asked.",
        "tension": "Over-care can shade into managing; the cared-for can start to feel less like an adult and more like a charge.",
        "practical_use": "Ask before you cover for the other — even when you already know what they need.",
    },
    "28-38": {
        "gift": "You challenge each other's sense of purpose — the questioning here builds both of you when it's honest.",
        "tension": "Without ground rules it shades into a fight over whose meaning is real; both can leave drained.",
        "practical_use": "Set a time limit on the heavy conversation. Name what you each want to find, not just what you want to prove.",
    },
    "32-54": {
        "gift": "You push each other toward growth that wouldn't have happened solo — ambition becomes shared ambition.",
        "tension": "Growth-push can read as criticism; what feels like belief to one can feel like pressure to the other.",
        "practical_use": "Name the intention before the push: are you encouraging them, or correcting them?",
    },
    "34-57": {
        "gift": "There's an instinctive, body-level trust here — you read each other without needing the words.",
        "tension": "Wordless trust can skip checking in; assumptions build that later turn out to be wrong.",
        "practical_use": "Once a week, ask the question you assume you already know the answer to.",
    },
    "35-36": {
        "gift": "You pull each other into new emotional territory — boredom doesn't get to settle for long.",
        "tension": "Chasing intensity can outrun what hasn't been digested yet; novelty becomes a way to avoid landing.",
        "practical_use": "Before the next new thing, name what's actually unfinished from the last one.",
    },
    "37-40": {
        "gift": "Loyalty forms fast — there's a sense of 'we're in this' that doesn't have to be argued into being.",
        "tension": "Unspoken contracts get binding without ever being agreed; both sides assume they know the deal.",
        "practical_use": "Say out loud what you've already agreed to silently — name the contract while it's still small.",
    },
    "39-55": {
        "gift": "Emotional range here is wide — depth and joy both have room; you don't have to flatten yourselves.",
        "tension": "Provocation can be unconscious; one of you may stir the other's feelings without meaning to.",
        "practical_use": "Sleep on big emotional decisions. The wave will tell you what's actually true by morning.",
    },
    "12-22": {
        "gift": "What you feel between you can be put into words — emotional expression flows here when the mood is right.",
        "tension": "Mood is the gatekeeper; when the mood is off, the same words land wrong, sometimes badly.",
        "practical_use": "Wait for the right moment, then say the thing. Don't force a difficult truth into a flat hour.",
    },
    "18-58": {
        "gift": "You can give each other honest feedback that actually lands — improvement becomes a shared project, not a fight.",
        "tension": "Correction without joy turns into criticism; the same channel that polishes can also wear the other down.",
        "practical_use": "Pair every piece of feedback with the thing you actually love about what they're doing.",
    },
    "47-64": {
        "gift": "You make sense of confusion together — patterns become visible that neither of you would have spotted alone.",
        "tension": "Both of you can spiral in unresolved thought; the channel can amplify confusion before it resolves.",
        "practical_use": "Write the puzzle down. Walk away. Come back in 24 hours — the answer rarely arrives on demand.",
    },
}


# ─────────────────────────────────────────────────────────────────────
# Template fallback for any channel without a curated entry
# ─────────────────────────────────────────────────────────────────────
def _template_narrative(name_a: str, name_b: str,
                        rel: str, theme: str) -> Dict[str, str]:
    rel = rel or "connection"
    theme = (theme or "").strip()
    return {
        "gift": (
            f"This channel opens {rel} between {name_a} and {name_b} — "
            f"something around {theme} becomes available together that wasn't available alone."
        ),
        "tension": (
            f"The same channel can over-amplify {rel}; under stress it can drown out what each of you "
            f"would have chosen separately."
        ),
        "practical_use": (
            f"Name when {rel} is alive between you, and name when it's running the show. The channel works "
            f"best when you use it on purpose, not when it uses you."
        ),
    }


def compute_channel_narrative(
    channel_id: str,
    channel_name: str,
    theme: str,
    relational: str,
    name_a: str = "You",
    name_b: str = "them",
) -> Dict[str, str]:
    """Return {gift, tension, practical_use} for a single completed channel.

    Curated entry wins; otherwise fall back to a deterministic template.
    Names are inlined; no `{name_a}`-style residue can leak out.
    """
    curated = CURATED.get(channel_id)
    if curated:
        out = {k: v.format(a=name_a, b=name_b) for k, v in curated.items()}
    else:
        out = _template_narrative(name_a, name_b, relational, theme)
    # Defensive: never return empty strings
    for k in ("gift", "tension", "practical_use"):
        if not out.get(k):
            out[k] = _template_narrative(name_a, name_b, relational, theme)[k]
    return out


__all__ = ["compute_channel_narrative", "CURATED", "NARRATIVE_VERSION"]
