# B3.1 — Lens-Term Compound Handling · Implementation Report
**Build marker:** intent-router-v2 / B3.1-lens-term-compound
**Date:** 2026-06-12 (re-validation pass)
**Status:** ✅ IMPLEMENTED · ✅ VALIDATED

---

## 1. Goal

Resolve the "lens-jargon override" failure class:

* Bare educational queries like `Tell me about my 7th house` were
  collapsing into `relationship` (because the 7th-house lexicon entry
  has a relationship weight). The intended target is `identity` — the
  user is asking about a chart concept, not their marriage.
* `Tell me about my Saturn return` was caught the same way — but the
  user actually wants `life_direction` (compound-lane).

The fix:

1. Detect a **lens term** (planet, house, transit, HD type, enneagram
   token, …).
2. Detect the **absence of a contextual cue** (relational, career,
   financial, temporal, conflict, named person).
3. When both hold, apply an `EDUCATIONAL_MODE_BONUS` to `identity` and
   a balancing `EDUCATIONAL_MODE_NATURAL_PENALTY` against the
   lens-collapse natural domains (relationship/career/family/money).
4. **Compound-lane exception:** if a compound-lane domain
   (`life_direction` / `growth`) has a strong-enough signal
   (`>= EDUCATIONAL_MODE_COMPOUND_SUPPRESS_FLOOR = 0.85`), suppress the
   educational-mode override so the compound lane wins.

## 2. What landed in code

File: `backend/services/intent_router_v2.py` (lines 94-165, 395-440).

### 2.1 Lens-term detector

```python
_EDU_LENS_TERM_RE = re.compile(
    r"\b("
    r"saturn|venus|mars|jupiter|pluto|mercury|sun|moon|uranus|neptune|"
    r"chiron|north\s+node|south\s+node|nodes?|"
    r"\d+(st|nd|rd|th)\s+house|"
    r"natal|transit|return|ascendant|midheaven|descendant|ic\b|"
    r"manifestor|generator|projector|reflector|sacral|splenic|"
    r"emotional\s+authority|gate\s+\d+|channel\s+\d+|profile\s+\d|"
    r"\d/\d\s*profile|defined\s+\w+\s+center|undefined\s+\w+\s+center|"
    r"my\s+(sun|moon|rising|ascendant|mercury|venus|mars|jupiter|"
    r"saturn|uranus|neptune|pluto|chiron|midheaven|big\s+three|"
    r"chart|natal\s+chart|birth\s+chart|astrology|human\s+design|"
    r"hd\s+type|type|profile|authority|strategy|incarnation\s+cross|"
    r"enneagram|tritype|wing|life\s+path|expression|destiny\s+number|"
    r"soul\s+urge|bazi|day\s+master|gene\s+keys)"
    r")\b",
    re.I)
```

### 2.2 Contextual-cue suppressor

A broad regex that — if present — suppresses educational-mode entirely
(see `B3_2_FOUNDER_OPERATOR_IMPLEMENTATION.md` §2.2 for the full set).
Covers: relational vocabulary, career / leadership / founder
vocabulary, financial, temporal, conflict, health.

### 2.3 Tunable constants

```python
EDUCATIONAL_MODE_BONUS                   = 0.50
EDUCATIONAL_MODE_NATURAL_PENALTY         = 1.2
EDUCATIONAL_MODE_NATURAL_DOMAINS         = ("relationship", "career",
                                            "family", "money")
EDUCATIONAL_MODE_COMPOUND_SUPPRESS_FLOOR = 0.85
EDUCATIONAL_MODE_COMPOUND_DOMAINS        = ("life_direction", "growth")
```

### 2.4 Decision flow (in `classify_intent_v2`)

```python
# 5c. B3.1 — educational-mode disambiguation.
if _EDU_LENS_TERM_RE.search(message) \
        and not _EDU_CONTEXTUAL_CUE_RE.search(message):
    # Compound-lane suppression check
    compound_signal = max(
        raw_scores.get(d, 0.0) for d in EDUCATIONAL_MODE_COMPOUND_DOMAINS
    )
    if compound_signal < EDUCATIONAL_MODE_COMPOUND_SUPPRESS_FLOOR:
        raw_scores["identity"] += EDUCATIONAL_MODE_BONUS
        for d in EDUCATIONAL_MODE_NATURAL_DOMAINS:
            raw_scores[d] = max(0.0, raw_scores[d] - EDUCATIONAL_MODE_NATURAL_PENALTY)
        educational_mode_applied = True
```

## 3. Validation

### 3.1 Targeted golden sets

```
golden_set_lens_jargon              n=25  top1=100.0%  top2=100.0%  routing_pass=100.0%
golden_set_educational_astrology    n=10  top1=100.0%  top2=100.0%  routing_pass=100.0%
```

### 3.2 Worked examples (from the rerun)

| Message | Predicted | Expected | Pass? |
|---|---|---|---|
| `Tell me about my 7th house` | `identity` | `identity` | ✓ |
| `Tell me about my Saturn return` | `life_direction` | `life_direction` | ✓ (compound-lane override) |
| `What does my 4th house say?` | `identity` | `identity` | ✓ |
| `How does my 7th house affect my marriage?` | `relationship` | `relationship` | ✓ (contextual cue suppresses educational mode) |
| `My Saturn return is hitting my career` | `career` | `career` | ✓ (contextual cue wins) |

### 3.3 No false positives in baseline `golden_set`

All 15 cases of the baseline still pass top-1 — the override does not
flip true positives.

## 4. Files Touched (cumulative — landed in prior agent pass, re-verified now)

```
M backend/services/intent_router_v2.py    (94-165 detector, 395-440 decision)
A backend/tests/intent_router_v2/golden_set_lens_jargon.yaml          (25 cases)
A backend/tests/intent_router_v2/golden_set_educational_astrology.yaml (10 cases)
```

## 5. Caveats / Known Limits

* Educational mode is intentionally **conservative**: it only fires
  when *no* contextual cue is present. This means a message like
  `What's my 7th house about right now?` might still route to
  `relationship` if `right now` is the only temporal cue (it is —
  see the cue regex). Tuning this beyond the current behaviour is a
  candidate for a future iteration.
* The lens-term regex is regex-based, not lemma-aware. Misspellings
  (`pluto's transitting my…`) will not match — also a B4 candidate.
