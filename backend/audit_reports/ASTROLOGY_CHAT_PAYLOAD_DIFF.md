# Astrology Chat Payload Diff — Ask Mirror vs Astrology Chat

**Build marker:** `astrology-chat-parity-audit-v1`
**Date:** 2026-02
**Companion document:** `ASTROLOGY_CHAT_PARITY_AUDIT.md`
**Mode:** READ-ONLY. No code modified. Live retrieval against `test_database`.

This document captures **exact, byte-level differences** in what each chat path injects into the LLM for the four reference users (Pete, Mel, Isaac, Thaddeus), against the three questions in the failure scenario.

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✓ | Block is injected into LLM system prompt |
| ✗ | Block is NOT injected |
| 🟢 | Contains literal "Ophiuchus" — engine-grounded ground truth available |
| 🟡 | Block present but does not contain Ophiuchus |
| 🔴 | Block absent (no deterministic grounding) |

---

## A — Per-user injection matrix

### A.1  Question: `"What is Thaddeus's Ascendant?"`  (asked by Pete, baseline working scenario)

| Block | Ask Mirror (`lens=None`) | Astrology Chat (`lens="astrology"`) |
|-------|--------------------------|-------------------------------------|
| `MIRROR_SYSTEM_PROMPT` | ✓ | ✓ |
| V1 preference insert | ✓ | ✓ |
| `LENS_PROMPTS["astrology"]` | ✗ | ✓ (contains "I don't have reliable data" template) |
| USER CONTEXT — Pete's chart | ✓ | ✓ |
| Lens-conversation memory + CHART SIGNALS (Pete) | ✗ | ✓ |
| Engine routing — proof block (V7 Ask Mirror engine path) | ✓ if any intent matches (none here) | ✓ if any intent matches (none here) |
| **FKR EVIDENCE block** | ✓ 🟢 — `FACT_LOOKUP`, **5072 chars**, contains literal `"Ascendant: 2°Ophiuchus"` (Thaddeus) | Same — FKR fires regardless of lens. ✓ 🟢 |

**Outcome:** Both paths receive the Ophiuchus fact in the FKR block. Ask Mirror has fewer suppression rules → answers correctly. Astrology Chat receives the same fact but ALSO receives the lens prompt's "use ONLY CHART SIGNALS" rule, which the LLM may interpret as "the FKR-evidence Thaddeus data is not in MY CHART SIGNALS" — but in practice for entity-named queries the FKR block is authoritative enough.

---

### A.2  Question: `"Do I have Ophiuchus in my chart?"`  (asked self-referentially, failing scenario)

| User | Path | `LENS_PROMPTS["astrology"]` | USER CONTEXT contains Ophiuchus? | CHART SIGNALS contains Ophiuchus? | FKR block? | Astrology-chat-router intent? |
|------|------|------------------------------|----------------------------------|------------------------------------|------------|--------------------------------|
| Pete     | Ask Mirror      | ✗ | ✗ (no body in Ophi)              | ✗ (block not injected for lens=None) | 🔴 `block_emitted=False`, modes=[] | None |
| Pete     | Astrology Chat  | ✓ | ✗ (USER CONTEXT only shows H12 cusp via implicit `--- ASTROLOGY ---` block — Ophi not shown unless triggered) | 🟢 `- House 12: cusp Ophiuchus` | 🔴 same — `block_emitted=False`, modes=[] | None |
| **Mel**  | Ask Mirror      | ✗ | ✓ (planet block has `Neptune: 8°Ophiuchus`) | ✗ | 🔴 `block_emitted=False`, modes=[] | None |
| **Mel**  | Astrology Chat  | ✓ | ✓ | 🟢 `- Neptune · Ophiuchus · House 5 · 8.3°` | 🔴 same — `block_emitted=False`, modes=[] | None |
| **Isaac** | Ask Mirror      | ✗ | ✓ (USER CONTEXT MC injection: `Midheaven / MC: 0°Ophiuchus (Ophiuchus)`) | ✗ | 🔴 `block_emitted=False`, modes=[] | None |
| **Isaac** | Astrology Chat  | ✓ | ✓ | 🟢 `- Midheaven · Ophiuchus · House 10 · 0.2°` + `- House 10: cusp Ophiuchus [tenants: Pluto]` | 🔴 same — `block_emitted=False`, modes=[] | None |
| **Thaddeus** | Ask Mirror   | ✗ | ✓ (USER CONTEXT Rising injection: `Rising: 2°Ophiuchus (Ophiuchus)`) | ✗ | 🔴 `block_emitted=False`, modes=[] | None |
| **Thaddeus** | Astrology Chat | ✓ | ✓ | 🟢 `- Ascendant · Ophiuchus · House 1 · 2.5°` + `- House 1: cusp Ophiuchus [tenants: Pluto]` | 🔴 same — `block_emitted=False`, modes=[] | None |

**Critical observation:** For all four users, on the failing question, `classify_query` returns `[]` (FKR emits no block) and `classify_astrology_intent` returns `None` (engine emits no block). The deterministic layers go silent on Ophiuchus-shaped queries — **for both paths equally**.

The asymmetry is therefore **NOT in retrieval** — both paths get the same null retrieval. The asymmetry is in:
1. **The LENS_PROMPT** — only Astrology Chat receives it. It contains the "I don't have reliable data" instruction template.
2. **USER CONTEXT detail level** — Astrology Chat (lens="astrology") additionally injects Mercury..Pluto with full sign/house/degree, while Ask Mirror keeps it to Sun/Moon/Rising + intent-gated extras. So Astrology Chat ironically has MORE Ophiuchus data in its USER CONTEXT block than Ask Mirror does, but is the one that denies Ophiuchus.

---

### A.3  Question: `"What placements in my chart are in Ophiuchus?"`  (failing inventory query)

Same matrix as A.2 — `classify_query` returns `[]`, `classify_astrology_intent` returns `None`, deterministic layers silent for all four users on both paths. Only the CHART SIGNALS / USER CONTEXT blocks carry Ophiuchus facts (when present), and only LENS_PROMPTS["astrology"] applies its refusal instruction.

---

### A.4  Question: `"What is my Ascendant?"`  vs  `"What sign is my Neptune in?"`  (self-referential entity-named)

Live verification with `classify_query`:

| User | Question | FKR `classify_query` result | FKR block_chars | Contains Ophi? |
|------|----------|-------------------------------|------------------|----------------|
| Pete     | `"What is my Ascendant?"`          | `["FACT_LOOKUP"]` | **3790** | No (Pete ASC=Sagittarius) |
| Mel      | `"What sign is my Neptune in?"`    | `[]`              | **0**    | n/a — phrase "what sign is" doesn't match the `_FACT_LOOKUP_PATTERNS[0]` regex which requires `\bwhat is\b` (not `\bwhat sign is\b`) |
| Isaac    | `"What sign is my Midheaven?"`     | `[]`              | **0**    | Same issue as Mel — phrasing mismatch |
| Thaddeus | `"What is my Ascendant?"`          | `["FACT_LOOKUP"]` | **2361** | **YES** (Thaddeus ASC=Ophiuchus, FKR injects `"Ascendant: 2°Ophiuchus"`) |

**This is a secondary FKR coverage gap** documented for the record: even self-referential entity queries fail FKR when the natural language uses `"what sign is my X"` instead of `"what is my X"`. The FACT_LOOKUP regex (`forum_chat_knowledge_retrieval.py:51-58`) anchors on `\bwhat is\b`, so any sign-form phrasing is missed.

---

## B — Exact prompt fragment that produces the failure

`server.py` line **1019-1023** (inside `LENS_PROMPTS["astrology"]`):

```text
The "CHART SIGNALS" block lists every placement we actually have for
this user (True Sidereal, with houses).

- Use ONLY placements that appear in CHART SIGNALS.
- Never invent a degree, sign, house, or aspect.
- If the user asks about a placement that is not in CHART SIGNALS, say:
    "I don't have reliable data for that placement in your chart."
  Do not paper over the gap by reaching for a different placement.
```

When the user types `"Do I have Ophiuchus in my chart?"`:
- The LLM scans CHART SIGNALS for an entry named `"Ophiuchus"`.
- It finds none (Ophiuchus is a SIGN, not a placement key).
- It applies the rule above and emits the verbatim failure phrase.

The prompt does NOT include any clause like "if the user asks whether a SIGN is present, list every placement whose sign equals that name".

---

## C — Conversation-memory layer — does it know about Ophiuchus?

Both YES (data layer) and NO (instruction layer):

| Component | File | Knows about Ophiuchus? |
|-----------|------|-------------------------|
| `SIGN_NAMES` | `services/astrology_conversation.py:85-88` | ✓ Includes `"Ophiuchus"` |
| `SIGN_ALIASES` | `:93-99` | ✓ Includes `"ophi"`, `"serpent bearer"`, `"serpent-bearer"`, `"serpentbearer"` |
| `_parse_cusp_entry` | `:151-180` | ✓ Validates `raw_sign in SIGN_NAMES` — accepts Ophiuchus |
| `build_chart_entity_index` | `:187-325` | ✓ Indexes planets/angles/houses with `sign="Ophiuchus"` correctly |
| `format_chart_signals_block` | `:591-641` | ✓ Emits "Ophiuchus" verbatim in output |
| `extract_entities_from_text` | `:362-391` | ⚠ Tags Ophiuchus mentions as `Sign:Ophiuchus` (with `Sign:` prefix), which `current_real` filter at `:424` STRIPS OUT (`[e for e in current_entities if not e.startswith("Sign:")]`) — so the user typing "Ophiuchus" never becomes an ACTIVE ENTITY |
| `resolve_active_entity` | `:398-490` | ⚠ Because Sign-tagged entities are filtered, a question about Ophiuchus has NO active entity (`source="none"`) — the LLM is left with a stateless prompt |
| `LENS_PROMPTS["astrology"]` | `server.py:980-1198` | ✗ No mention of Ophiuchus, 13-sign, Variant A, or canonical engine. Tells LLM to refuse. |

So the underlying CHART SIGNALS data is correct. The ACTIVE ENTITY mechanism deliberately filters out signs as conversational subjects (which is correct for most flows — "Pisces" alone shouldn't anchor a question — but means an Ophiuchus-shaped query gets no anchor and the LLM has no scaffold to compose an answer from).

---

## D — What both paths share (so we can rule them out)

These layers are **identical** between Ask Mirror and Astrology Chat — they cannot be the source of the divergence:

| Layer | File / line | Behaviour for Ophiuchus |
|-------|-------------|--------------------------|
| Stored chart write path (W2) | `calculations/astrology.py:444-1074` | Correctly stamps `sign="Ophiuchus"` for any body / angle in Ophiuchus band |
| `db.charts.find_one` retrieval | `routers/mirror_chat.py:262` | Returns the same doc to both paths |
| USER CONTEXT block builder | `routers/mirror_chat.py:280-822` | Same logic for both — Ophiuchus passes through verbatim wherever stored |
| `MIRROR_SYSTEM_PROMPT` | `server.py:695-980` | No Ophiuchus mention — neither positive nor negative |
| `MIDHEAVEN integrity guardrail` (`mirror_chat.py:321-329`) | Same for both | Says "Do NOT state a person's Midheaven / MC sign unless it is explicitly present in this ASTROLOGY PROFILE block" — works correctly when MC=Ophiuchus |
| FKR `build_fkr_evidence_block` | `services/forum_chat_knowledge_retrieval.py:481-507` | When triggered, includes Ophiuchus verbatim — same for both paths |
| V2 receipt shadow router | `routers/mirror_chat.py:138-247` | Lens-aware but does not filter Ophiuchus |

---

## E — Summary

**The divergence is NOT in retrieval.** Both paths retrieve the same chart, USER CONTEXT, and (for entity-named queries) the same FKR evidence block. Both paths' deterministic layers fall silent on generic Ophiuchus questions.

**The divergence IS in the instruction layer:**
1. Astrology Chat alone receives `LENS_PROMPTS["astrology"]` (`server.py:980-1198`) which contains the literal "I don't have reliable data" template (line 1022).
2. Neither path's prompt contains a positive Ophiuchus disclosure ("Mirror canonically uses 13-sign Variant A; Ophiuchus is a real sign for this user").

Ask Mirror escapes the failure because:
- It does not apply the LENS_PROMPT refusal rule.
- For entity-named queries about other users (e.g., "What is Thaddeus's Ascendant?"), FKR fires and injects the Ophiuchus fact deterministically — the LLM has no room to deny it.

Astrology Chat hits the failure because:
- It applies the LENS_PROMPT refusal rule.
- For generic Ophiuchus questions, deterministic retrieval is silent → only CHART SIGNALS + USER CONTEXT carry the facts, and the refusal rule overrides them.

End of payload diff.
