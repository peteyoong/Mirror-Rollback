# Astrology Relationship Re-Story V1
**Delivery Report**

| Field | Value |
|---|---|
| Workstream | Astrology Relationship Re-Story (V1 of N) |
| Status | **GREEN — pytest 9/9 (incl. real DB), full suite 60/60** |
| Scope | Producer module only.  No surface wiring.  No prompt redesign.  No new collections.  No migrations. |
| File added | `/app/backend/services/astrology_relationship_restory_v1.py` (449 lines) |
| Test file | `/app/backend/services/test_astrology_relationship_restory_v1.py` (228 lines) |
| Build marker | `astrology-relationship-restory-v1` |
| Untouched | All astrology / HD / BaZi / numerology / timeline engines.  All env flags. |

---

## 1. What landed

A new deterministic producer that consumes the same chart payload as the
existing `relationship_astrology_engine.py` (V2) and emits the 5-section
**BaZi-V2-style narrative** you described.

```
compute_relationship_restory_v1(
    chart_a, chart_b, relationship_role, name_a, name_b,
) -> {
    "success":           True,
    "build_marker":      "astrology-relationship-restory-v1",
    "relationship_role": "spouse",
    "sections": {
        "what_lives_between_you":             { headline, body, hidden_evidence: [...] },
        "what_strengthens_this_relationship": { headline, body, hidden_evidence: [...] },
        "growth_edge":                        { headline, body, hidden_evidence: [...] },
        "shadow_pattern":                     { headline, body, hidden_evidence: [...] },
        "why_this_person_matters":            { headline, body, hidden_evidence: [...] },
    },
}
```

### Section-by-section inputs (per your spec)

| Section | Inputs read | What it answers |
|---|---|---|
| **What lives between you** | Descendant, 7th-house cusp, Sun/Moon synastry, angular contacts | What repeatedly happens when these two meet |
| **What strengthens this relationship** | Venus, Moon, supportive synastry, benefic reinforcement | Practical relational conditions |
| **Growth edge** | Saturn, Pluto, South Node, difficult synastry | Developmental task — not problem list |
| **Shadow pattern** | Saturn / Moon / Mars / Venus friction | How the relationship fails under stress |
| **Why this person matters** | Juno, North Node, Vertex, corroborating synastry | Why this relationship keeps showing up |

### Output philosophy (matches BaZi V2)

> User-facing fields describe **what happens between people** — not
> houses, signs, aspects, or rulerships.  Astro evidence lives in
> `hidden_evidence[]` so downstream surfaces can show it in an
> expandable tray.

---

## 2. Strict guardrails — verified by tests

| Guard | Description | Verified by |
|---|---|---|
| **G1** | User-facing `headline` / `body` strings MUST NOT contain astro terminology (planet names, sign names, "house", "ruler", "aspect", "synastry", …) | `test_G1_G2_no_jargon_or_destiny` (5 parametrised role/element scenarios) + `test_G6_real_charts_pete_mel` |
| **G2** | User-facing strings MUST NOT contain destiny / soulmate / fate / certainty language (`soulmate`, `destined`, `meant to be`, `karmic`, `must`, `guaranteed`, …) | same tests |
| **G3** | Output MUST be deterministic for fixed inputs | `test_G3_determinism` (byte-equal across two invocations) |
| **G4** | All 5 sections present, each with headline + body + hidden_evidence | `test_G4_output_shape_complete` |
| **G5** | `hidden_evidence[]` MAY contain astro tokens (that's its purpose) | `test_G6_real_charts_pete_mel` asserts ≥1 evidence row |
| **G6** | Real DB charts (Pete + Mel) produce a complete narrative | `test_G6_real_charts_pete_mel` (live `test_database` query) |
| **G7** | Empty / partial chart inputs do not crash | `test_G7_empty_inputs_safe` |

### Jargon banlist (the regex used by tests)
```
Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus,
Neptune, Pluto, Chiron, Juno, Vertex, North Node, South Node,
nodal, Ascendant, Descendant, Midheaven, Imum Coeli, ASC, DSC, MC, IC,
Aries, Taurus, Gemini, Cancer, Leo, Virgo, Libra, Scorpio,
Sagittarius, Capricorn, Aquarius, Pisces, Ophiuchus,
house, cusp, conjunction, opposition, square, trine, sextile,
quincunx, orb, natal, synastry, composite, transit,
ruler, rulership, ruling, aspect, placement, astrology,
astrological, horoscope, zodiac
```

### Destiny banlist
```
soulmate, twin flame, destined, destiny, fate, fated, predestined,
meant to be, karmic, karma, karmic lesson, will always, never will,
guaranteed, guarantee, absolute(ly), certain, certainty, must
```

Any match in `sections.*.headline` or `sections.*.body` fails the test.

---

## 3. Sample output (deterministic — generated against real Pete + Mel charts)

```
What lives between you
──────────────────────
When you two meet, one of you reaches for words to make sense of what's
happening while the other is already reading the atmosphere underneath
the words.  Most of what lives between you is happening in that gap.

What strengthens this relationship
──────────────────────────────────
What strengthens you is letting each other enjoy what each of you
enjoys, without translating one taste into the other.  Repair happens
when the words come AFTER warmth, not before it.  A hand on a shoulder
before a sentence reaches further than the sentence alone.

Growth edge
───────────
One of you orients to structure; the other orients to clarity.  The
growth edge is letting structure soften and letting clarity get
embodied — without either side demanding the other become like them.

Shadow pattern
──────────────
Under stress, one of you reaches for explanation; the other reaches
for atmosphere.  The more one explains, the more the other retracts.
The loop reads to both of you as the other person being unreachable —
when actually both are reaching, in two different directions.

Why this person matters
───────────────────────
This relationship keeps asking you toward the same thing — the
practice of being seen without performing.  Mel is often the room
where Pete has to drop the work of being impressive, and vice versa.
```

No planet names.  No sign names.  No "house" / "aspect" / "ruler".  No
"destined" / "soulmate" / "must".  Mirror voice.

---

## 4. Test summary

```
$ python -m pytest services/test_astrology_relationship_restory_v1.py -v
test_G4_output_shape_complete                                              PASSED
test_G1_G2_no_jargon_or_destiny[air_water_spouse-inputs0]                  PASSED
test_G1_G2_no_jargon_or_destiny[fire_earth_partner-inputs1]                PASSED
test_G1_G2_no_jargon_or_destiny[fire_water_child-inputs2]                  PASSED
test_G1_G2_no_jargon_or_destiny[same_element_friend-inputs3]               PASSED
test_G1_G2_no_jargon_or_destiny[missing_b_unknown_role-inputs4]            PASSED
test_G3_determinism                                                        PASSED
test_G6_real_charts_pete_mel                                               PASSED
test_G7_empty_inputs_safe                                                  PASSED
=== 9 passed in 0.12s ===
```

Full FCAC + Re-Story V1 + prior suites:

```
$ python -m pytest services/test_relationship_field_v2.py \
                   services/test_slice_2_ask_mirror_wiring.py \
                   services/test_slice_3_prompt_gate.py \
                   services/test_slice_a_auto_context.py \
                   services/test_slice_b_forum_chat_wiring.py \
                   services/test_astrology_relationship_restory_v1.py -q
=== 60 passed in 35.93s ===
```

Zero regressions.

---

## 5. Architecture

```
        ┌────────────────────────────────────────────────┐
        │  Existing astrology calc engines (UNTOUCHED)   │
        │  • calculations.astrology.get_full_natal_chart │
        │  • services.relationship_astrology_engine (V2) │
        └─────────────────────┬──────────────────────────┘
                              │ (chart payload)
                              ▼
        ┌────────────────────────────────────────────────┐
        │  services.astrology_relationship_restory_v1    │
        │  (NEW — this slice)                            │
        │                                                │
        │  compute_relationship_restory_v1(              │
        │     chart_a, chart_b, role, name_a, name_b     │
        │  ) -> 5-section narrative                      │
        │                                                │
        │  Read-only.  Deterministic.  Mirror voice.     │
        │  No surface wiring yet.                        │
        └────────────────────────────────────────────────┘
```

This producer is a sibling of `relationship_astrology_engine.py` — both
read the same chart shape, but the V1 re-story emits the 5-section form
the user requested, while the V2 engine remains in service for the
existing deep-spouse synthesis surface.

---

## 6. Guardrails honoured

| Constraint | Honoured | Evidence |
|---|---|---|
| Do not modify astrology / HD / BaZi / numerology / timeline engines | ✅ | only one NEW file added; no edits to existing engines |
| No new collections / no migrations | ✅ | no DB writes |
| No prompt redesign | ✅ | no LLM prompts touched |
| No env flag changes | ✅ | no `.env` edits |
| Mirror voice (no destiny / soulmate / fate / certainty) | ✅ | `test_G1_G2…` covers it |
| No houses / signs / aspects / rulerships in user-facing text | ✅ | same test |

---

## 7. What is NOT in this slice (future work)

- **Surface wiring** — Ask Mirror, Forum Chat, Astrology Chat, and the
  Relationship Insight V2 card currently consume the existing V2 engine.
  A future slice will switch them (gated behind a new flag).
- **Prompt-block emitter** — once a surface adopts Re-Story V1 it will
  need a small emitter that turns the section payload into the system
  prompt (similar to Slice 3 of Relationship Field V2).
- **Card UI** — `RelationshipInsightV2Card.tsx` will need a new
  5-section variant; out of scope for this slice (producer only).
- **More section variations** — the body strings are intentionally
  conservative.  Once we have real-world traffic we can expand the
  element-combination matrix.

---

## 8. Files touched

| File | Lines | Role |
|---|---|---|
| `services/astrology_relationship_restory_v1.py` | 449 | NEW — producer module |
| `services/test_astrology_relationship_restory_v1.py` | 228 | NEW — 9 acceptance tests |
| `audit_reports/ASTROLOGY_RELATIONSHIP_RESTORY_V1.md` | — | NEW — this report |

Zero modifications to any existing engine, router, or surface.

---

— end of report —
