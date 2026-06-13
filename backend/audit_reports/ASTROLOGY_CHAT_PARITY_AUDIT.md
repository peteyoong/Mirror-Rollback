# P0 — Astrology Chat Parity Audit (Ask Mirror vs Astrology Chat)

**Build marker:** `astrology-chat-parity-audit-v1`
**Date:** 2026-02
**Scope:** Forensic audit — read-only. No fixes applied. No calculator/birth/chart/migration/prompt/flag mutations.
**Result:** Root cause proven. Three converging defects identified, ranked, and located by file + line.

---

## TL;DR

| Layer | Ask Mirror (working) | Astrology Chat (failing) | Divergence point |
|-------|----------------------|---------------------------|------------------|
| Same endpoint? | **Yes** — both call `POST /api/mirror/chat` | Same code path | n/a |
| `lens` param | `None` | `"astrology"` | `request.lens` |
| Intent classifier | `services/forum_chat_knowledge_retrieval.classify_query` → routes "What is Thaddeus's Ascendant?" → `FACT_LOOKUP` → FKR fires with 5072-char evidence block containing literal `"Ascendant: 2°Ophiuchus"` | Same FKR fires, **but** `classify_query("Do I have Ophiuchus in my chart?")` returns `[]` (no mode matches → no FKR evidence injected). Engine-router `classify_astrology_intent` ALSO returns `None` (no body/aspect/positional anchor). | **`services/forum_chat_knowledge_retrieval.py::classify_query` has no "Ophiuchus" intent**, AND `services/astrology_chat_router.py::classify_astrology_intent` has no Ophiuchus intent either. |
| Chart payload | USER CONTEXT block + (no LENS_PROMPT) + FKR evidence (deterministic Ophiuchus facts) | USER CONTEXT block + **LENS_PROMPTS["astrology"]** + CHART SIGNALS block (deterministic Ophiuchus facts present) — **but no FKR evidence and no Ophiuchus-aware instruction** | `LENS_PROMPTS["astrology"]` (`server.py:980-1198`) adds a "use ONLY placements in CHART SIGNALS — else say 'I don't have reliable data'" rule with **no Ophiuchus exception clause**, while the FKR evidence path is silent. |
| Result for Mel (Neptune in Ophiuchus) | Would answer correctly if asked specifically (FKR fires on "What is Mel's Neptune?") | Denies Ophiuchus even though `Neptune · Ophiuchus · House 5 · 8.3°` is present in CHART SIGNALS block | LLM is told to refuse "data not in CHART SIGNALS" but isn't told Ophiuchus IS a valid sign here. |
| Result for Pete (no Ophiuchus placements) | Correctly says "no Ophiuchus" | Says "I don't have reliable data on Ophiuchus" — a non-truth that suggests Ophiuchus might exist if only we had data | Both paths technically correct re: Pete, but Astrology Chat's wording invents a data gap that doesn't exist. |

**Root cause (proven, ranked):**
1. **Retrieval-router blindspot (HIGH).** Neither `classify_query` (FKR) nor `classify_astrology_intent` (engine router) has any Ophiuchus-shaped intent. Generic Ophiuchus questions ("Do I have Ophiuchus", "What's in Ophiuchus") match NO regex → both deterministic systems return empty → the LLM is left answering free-form, which falls back to its 12-sign RLHF prior.
2. **Lens-prompt asymmetry (HIGH).** `LENS_PROMPTS["astrology"]` (which fires only for Astrology Chat) instructs the LLM to refuse anything not in CHART SIGNALS and to use the exact phrase "I don't have reliable data for that placement in your chart" — which is the EXACT failure phrase reported. Ask Mirror does not apply this lens prompt.
3. **No 13-sign canonical disclosure to the LLM (HIGH).** Nowhere in the live mirror_chat prompt assembly is the LLM told "Mirror uses 13-sign Variant A (`midpoint13_variant_a_v1`); Ophiuchus is a first-class sign in this user's stored chart; do not deny it." The lone 13-sign disclosure (`ASTROLOGY_DEEP_DIVE_PROMPT` line 2001) is actually a **12-sign assertion** ("This is a 12-sign sidereal system, not … the 13-sign Ophiuchus system") that contradicts the canonical engine — but this prompt only fires for the Astrology Deep Dive endpoint, not the chat. The chat path has no Ophiuchus instruction at all.

---

## 1. Architecture trace — same endpoint, two paths

Both Ask Mirror and Astrology Chat are served by **`POST /api/mirror/chat`** (`routers/mirror_chat.py:105`). The branching point is `request.lens`.

```
                          POST /api/mirror/chat
                          MirrorChatRequest{user_id, message, lens, history, ...}
                                         │
                                         ▼
                              ┌────────────────────┐
                              │  Slice B1: Intent  │   v2_receipt computed
                              │  Router V2 shadow  │   (shadow telemetry only)
                              │  (mirror_chat.py   │
                              │   :138-247)        │
                              └────────────────────┘
                                         │
                                         ▼
                       db.users.find_one + db.charts.find_one      ◄── identical for both
                                         │
                                         ▼
                              build USER CONTEXT block             ◄── identical for both
                              (mirror_chat.py :280-822)               (Sun, Moon, Rising, MC,
                              context_parts = [...]                  Chiron, DC, IC + planets
                                                                     for lens="astrology")
                                         │
                                         ▼
                       system_prompt = MIRROR_SYSTEM_PROMPT          ◄── identical for both
                       (mirror_chat.py :1009)
                                         │
                                         ▼
                       V1 preference insert (tone/depth/support)     ◄── identical for both
                       (mirror_chat.py :1011-1089)
                                         │
                                         ▼
                       ┌─────────────────────────────────────────────────────┐
                       │   if request.lens and request.lens in LENS_PROMPTS: │   ★ DIVERGENCE
                       │       system_prompt += "\n" + LENS_PROMPTS[lens]    │   POINT #1
                       │   (mirror_chat.py :1092-1093)                       │
                       └─────────────────────────────────────────────────────┘
                                         │
                       ┌─────────────────┴─────────────────┐
              lens=None                                    lens="astrology"
              (Ask Mirror)                                 (Astrology Chat)
                       │                                           │
                       │                                           ▼
                       │                              LENS_PROMPTS["astrology"]
                       │                              (server.py :980-1198)
                       │                              Says: "Use ONLY placements
                       │                              in CHART SIGNALS. If user
                       │                              asks about a placement not
                       │                              in CHART SIGNALS, say:
                       │                              'I don't have reliable
                       │                              data for that placement
                       │                              in your chart.'"
                       │                                           │
                       │  ┌────────────────────────────────────────┘
                       │  │
                       ▼  ▼
              Lens-conversation memory + history     (mirror_chat.py :1759-1771)
              services.mirror_chat_pipeline._build_lens_context
                       │
                       │  When lens="astrology":
                       │    registry = AstrologyRegistry
                       │    index = build_chart_entity_index(chart)
                       │      ─→ correctly indexes Ophiuchus planets
                       │      ─→ correctly indexes Ophiuchus cusps
                       │    grounding_block = format_chart_signals_block(index)
                       │      ─→ correctly emits "Neptune · Ophiuchus · House 5"
                       │  When lens=None: block skipped (early return).
                       │
                       ▼
              Mode detection (timeline / analyst / deep_dive)  (mirror_chat.py :2563-2595)
                       │
                       ▼
              ┌──────────────────────────────────────────────────────────────┐
              │  Engine routing: classify_astrology_intent                    │   ★ DIVERGENCE
              │  (mirror_chat.py :1897-2147)                                  │   POINT #2
              │                                                               │
              │  Fires for BOTH paths (lens=None gets V7 Ask-Mirror delegation;│
              │  lens="astrology" gets normal flow).                          │
              │                                                               │
              │  classify_astrology_intent returns a {data_mode, object}      │
              │  envelope when ANY of these intents match:                    │
              │      lifecycle | house_inventory | natal_object |             │
              │      solar_return | transit_to_natal | transit_object |       │
              │      timeline_summary | pressure_topology                     │
              │                                                               │
              │  NEITHER "Do I have Ophiuchus" NOR "What's in Ophiuchus"      │
              │  matches any of these regexes — RETURNS None.                 │
              │  No engine fires → no proof block injected.                   │
              └──────────────────────────────────────────────────────────────┘
                       │
                       ▼
              FKR — Forum Knowledge Retrieval                  (mirror_chat.py :2814-2900)
                       │
                       │   FKR fires for BOTH paths (lens-agnostic).
                       │   build_fkr_evidence_block routes via classify_query
                       │   (forum_chat_knowledge_retrieval.py :141)
                       │
              ┌────────┴───────────────────────────────────────────────────────────┐
              │ Q="What is Thaddeus's Ascendant?"   → classify_query → FACT_LOOKUP │
              │   → 5072-char EVIDENCE block injected,                              │
              │     contains literal "Ascendant: 2°Ophiuchus"                       │
              │                                                                     │
              │ Q="Do I have Ophiuchus in my chart?" → classify_query → []          │   ★ DIVERGENCE
              │   → NO EVIDENCE block injected (block_emitted=False)                │   POINT #3
              │   → empty deterministic context                                     │
              └─────────────────────────────────────────────────────────────────────┘
                       │
                       ▼
              LLM call (mirror_chat.py :2920-2960)
              system_prompt + history + user.message
              + Ask Mirror: NO lens-specific suppression rule, FKR evidence
                            present for entity-named questions → answers correctly
              + Astrology Chat: lens prompt with "refuse outside CHART SIGNALS"
                                rule, NO Ophiuchus instruction, NO FKR for
                                generic Ophiuchus queries → falls back to
                                "I don't have reliable data" / "Traditional
                                astrology does not recognize Ophiuchus"
```

---

## 2. Source-of-truth map

### 2.1 Stored chart layer (identical for both paths)

```
db.charts.find_one({user_id})
  └─ astrology.angles.{asc, dc, mc, ic}.{sign, longitude, degree, formatted}
  └─ astrology.planets.{Sun, Moon, ..., Pluto, Chiron}.{sign, house, degree, ...}
  └─ astrology.houses.{cusps[12], formatted_cusps[12], ascendant, mc, ...}
  └─ astrology_engine_version = "midpoint13_variant_a_v1"
  └─ migration_marker = "variant-a-13-sign-migration-v1"

For Mel (697ec826ad4b18f75bf42616):  planets.Neptune.sign = "Ophiuchus"
For Isaac (69dda348de9cb1c83c0780f8): angles.mc.sign     = "Ophiuchus"
For Thaddeus (69dd0b2cc92ba973f8838c11): angles.asc.sign = "Ophiuchus"
For Pete (697f0c6abf35c0528ff06954):  houses.formatted_cusps[11].sign = "Ophiuchus"
                                       (12th-house cusp only — no body in Ophiuchus)
```

### 2.2 Ask Mirror retrieval (lens=None)

```
USER CONTEXT (always)                                      ◄ mirror_chat.py :280-822
  Sun, Moon, Rising, MC (always-on injection)                  Variant A signs flow through
  Chiron, DC, IC (intent-gated)                                untouched. Ophiuchus appears
                                                               literally where present.

LENS_PROMPTS[lens]                                         ◄ SKIPPED (lens is None)

Lens-conversation memory                                   ◄ SKIPPED (lens is None)

Engine routing (astrology_chat_router)                     ◄ FIRES with V7 Ask Mirror
  - classify_astrology_intent(message)                        delegation when intent
  - V7 target resolution + relationship resolution            classifier triggers; injects
                                                               deterministic proof block.

FKR (forum_chat_knowledge_retrieval)                       ◄ FIRES — emits FACT_LOOKUP
  - classify_query(message) returns modes if matched          / RELATIONSHIP / COMPARISON
  - build_fkr_evidence_block returns 5K-char ground truth     blocks. CONTAINS Ophiuchus
                                                              when stored chart has it.

→ LLM
```

### 2.3 Astrology Chat retrieval (lens="astrology")

```
USER CONTEXT (always)                                      ◄ mirror_chat.py :280-822
  Sun, Moon, Rising, MC (always-on injection)                  Identical Variant A facts.
  Chiron, DC, IC (intent-gated)                                Ophiuchus present where stored.
  PLUS Mercury..Pluto (because lens="astrology")               (lines 598-660)

LENS_PROMPTS["astrology"]                                  ◄ server.py :980-1198  ★ KEY
  - Says: "Use ONLY placements that appear in CHART
    SIGNALS"
  - Says: "If the user asks about a placement that is
    not in CHART SIGNALS, say: 'I don't have reliable
    data for that placement in your chart.'"
  - Has FORBIDDEN HEDGES list (lines 1117-1137) — does
    NOT include the Ophiuchus-denial phrases
  - Has NO mention of Ophiuchus, 13-sign, Variant A,
    midpoint13_variant_a_v1, or canonical engine name.

Lens-conversation memory + CHART SIGNALS                   ◄ mirror_chat.py :1759-1771
  - format_chart_signals_block(index)                         ✓ Ophiuchus survives indexing:
    (astrology_conversation.py :591-641)                       SIGN_NAMES contains
                                                                "Ophiuchus" at line 87.
                                                              ✓ Cusp parser accepts it:
                                                                _parse_cusp_entry validates
                                                                raw_sign in SIGN_NAMES.
                                                              ✓ Block output verified live:
                                                                "Neptune · Ophiuchus · H5"

Engine routing (astrology_chat_router)                     ◄ classify_astrology_intent
  - Fires intent classifier                                    returns None for generic
                                                                Ophiuchus questions ("Do I
                                                                have Ophiuchus?"). NO body,
                                                                NO aspect, NO positional,
                                                                NO house, NO lifecycle —
                                                                NO mode triggers. No engine
                                                                fires, no proof block.

FKR (forum_chat_knowledge_retrieval)                       ◄ Fires identically, but:
  - classify_query("Do I have Ophiuchus...?") = []            classify_query has no
  - build_fkr_evidence_block returns block_emitted=False      "Ophiuchus" mode pattern
                                                              → empty block.

→ LLM
```

### 2.4 First file/function where Ophiuchus disappears

The **stored data is correct end-to-end**.  Ophiuchus disappears at the **prompt-assembly layer**, in three places, in this order:

1. **`services/forum_chat_knowledge_retrieval.py::classify_query` (line 141)** — Has no `OPHIUCHUS` / `OPHI` mode pattern. For "Do I have Ophiuchus", returns `[]` → no FKR evidence block emitted (verified live: `block_chars=0`).
2. **`services/astrology_chat_router.py::classify_astrology_intent` (line 309)** — Has no Ophiuchus intent. The body regex `_BODY_PATTERNS` (line 36-49) covers planets / angles / asteroids but NOT signs. Returns `None` → no deterministic engine fires.
3. **`server.py:980-1198` `LENS_PROMPTS["astrology"]`** — Tells the LLM to refuse anything "not in CHART SIGNALS" using the exact reported failure phrase. Has no Ophiuchus disclosure. This is the prompt the LLM is following when it says "I don't have reliable data on Ophiuchus placements".

For the **specific** "Mel has Neptune in Ophiuchus" question: even though `Neptune · Ophiuchus · House 5 · 8.3°` IS in the CHART SIGNALS block, the LLM still denies it because (a) no Ophiuchus-aware instruction in the prompt counters its 12-sign RLHF prior, and (b) the prompt's "refuse outside CHART SIGNALS" rule is being misapplied to a sign-name query.

---

## 3. Q&A — explicit answers

### Q1: Does Astrology Chat receive the same chart payload as Ask Mirror?

**NO — close but materially different.**  Both paths load the same `db.charts.find_one({user_id})` document and build the same USER CONTEXT block.  Differences:

| Block | Ask Mirror (`lens=None`) | Astrology Chat (`lens="astrology"`) |
|-------|---------------------------|-------------------------------------|
| `MIRROR_SYSTEM_PROMPT` | ✓ | ✓ |
| `V1 preference insert` | ✓ | ✓ |
| `LENS_PROMPTS["astrology"]` | ✗ | ✓ ★ (the suppression rule lives here) |
| USER CONTEXT — Sun/Moon/Rising/MC | ✓ | ✓ |
| USER CONTEXT — Mercury..Pluto detail | ✗ (only on lens="astrology" branch, mirror_chat.py:598) | ✓ |
| Lens-conversation memory + CHART SIGNALS block | ✗ | ✓ |
| Engine routing (`classify_astrology_intent`) — proof blocks | ✓ (V7 Ask Mirror engine path) | ✓ |
| FKR evidence block | ✓ when query matches FKR modes | ✓ when query matches FKR modes — but for generic Ophiuchus queries, NEITHER path gets a block because `classify_query` rejects them too. |

So Ask Mirror has FEWER blocks but they're permissive; Astrology Chat has MORE blocks but they include the **restrictive `LENS_PROMPTS["astrology"]` clause that triggers the failure**.

### Q2: Does Astrology Chat receive ASC, MC, IC, DC with sign labels?

**YES — verified live.**

For Pete (697f0c6abf35c0528ff06954) the USER CONTEXT block contains:
```
Rising: 19°Sagittarius (Sagittarius)
Midheaven / MC: 11°Virgo (Virgo)
IC: 11°Pisces (Pisces)            (only when ic_triggers fire)
Descendant / DC: 19°Gemini (Gemini) (only when dc_triggers fire)
```

For Thaddeus the CHART SIGNALS block (lens-conversation layer) contains:
```
- Ascendant · Ophiuchus · House 1 · 2.5°
- House 1: cusp Ophiuchus [tenants: Pluto]
```

For Isaac:
```
- Midheaven · Ophiuchus · House 10 · 0.2°
- House 10: cusp Ophiuchus [tenants: Pluto]
```

ASC and MC are unconditionally injected by USER CONTEXT (mirror_chat.py:300, :313-319). IC and DC are intent-gated (must hit `_ic_triggers` / `_dc_triggers` lists). When intent-gated for a generic Ophiuchus question, IC and DC may be absent — but the CHART SIGNALS block from the lens-conversation layer always has all four.

**Source:** `mirror_chat.py:298-554` (USER CONTEXT) + `services/astrology_conversation.py:264-297` (CHART SIGNALS angles section).

### Q3: Does Astrology Chat receive Ophiuchus placements at all?

**YES — verified live.**

Live `format_chart_signals_block` output for the four target users:

```
Pete:     "House 12: cusp Ophiuchus"
Mel:      "Neptune · Ophiuchus · House 5 · 8.3°"
Isaac:    "Midheaven · Ophiuchus · House 10 · 0.2°"
          "House 10: cusp Ophiuchus [tenants: Pluto]"
Thaddeus: "Ascendant · Ophiuchus · House 1 · 2.5°"
          "House 1: cusp Ophiuchus [tenants: Pluto]"
```

Ophiuchus is **not filtered** at any retrieval layer.  It survives:
- The W2 canonical writer (`calculations/astrology.py::get_full_natal_chart`)
- The stored chart doc
- The USER CONTEXT block
- The CHART SIGNALS block (`format_chart_signals_block`)
- The cusp parser (`_parse_cusp_entry`)

It **only disappears** at:
- `forum_chat_knowledge_retrieval.classify_query` — has no Ophiuchus mode pattern → for Ophiuchus-shaped questions, returns `[]` → no FKR EVIDENCE block emitted.
- `astrology_chat_router.classify_astrology_intent` — has no Ophiuchus intent → returns `None` → no deterministic engine block emitted.
- The LLM's own output — because `LENS_PROMPTS["astrology"]` tells it to refuse anything not in CHART SIGNALS, while not telling it that Ophiuchus IS a valid sign for THIS user.

### Q4: Is there any instruction, prompt fragment, memory layer, or fallback text containing phrases such as "traditional astrology" / "12-sign zodiac" / "Ophiuchus not recognized" / "Ophiuchus unsupported"?

**YES — located.**

| Phrase | File | Line | Status in live chat |
|--------|------|------|----------------------|
| `"This is a 12-sign sidereal system, not tropical and not the 13-sign Ophiuchus system"` | `server.py` | **2001** | Embedded in `ASTROLOGY_DEEP_DIVE_PROMPT`. **Does NOT fire in Astrology Chat** (used only by `/api/astrology/deep-dive/{user_id}` endpoint, lines 15695-15707). However, it is canonical evidence that **the codebase has 12-sign self-identification baked in elsewhere** that would block Ophiuchus if it ever leaks into the chat prompt path. |
| `"Do NOT say 'in most astrology we use the 12-sign zodiac' or 'I use the 12-sign zodiac'"` | `server.py` | **2001** (same line, continuation) | Same. Defensively forbids LLM from disowning 12-sign — but in the same breath asserts "Mirror is a 12-sign sidereal system". Internally contradictory. |
| `"This does NOT replace the 12-sign zodiac; it's a sky-view"` | `server.py` | **14915** | Inside the `/api/astrology/iau-constellation-overlay` endpoint response. Surfaced to frontend, not to chat LLM directly. |
| `"Additive only — does NOT replace the 12-sign True Sidereal zodiac"` | `server.py` | **14941** | Same endpoint. |
| `"Not a 13-sign zodiac. Sky-observation overlay only."` | `server.py` | **14995** | Inside the IAU overlay response payload. |
| `"layer. The 12-sign True Sidereal zodiac remains the …"` | `server.py` | **15014** | Same. |
| `"I don't have reliable data for that placement in your chart"` | `server.py` | **1022** | **★ THIS IS THE EXACT REPORTED FAILURE PHRASE.** Lives in `LENS_PROMPTS["astrology"]`, fires on every Astrology Chat turn. The LLM is being TOLD to produce this phrase whenever it perceives a placement not in CHART SIGNALS — which it does for generic "Ophiuchus" queries. |
| `"I don't have your … data to specify …"` | `server.py` | **1118** | Listed in `LENS_PROMPTS["astrology"]` as a **forbidden** opener. But the LLM blends this template with the line-1022 instruction → output: "I don't have reliable data on Ophiuchus placements" — which the prompt simultaneously commands and forbids. |
| `"Traditional astrology does not recognize Ophiuchus"` | NOT in codebase | n/a | This phrasing comes from the **LLM's RLHF prior**, not the prompt. The prompt does not include it. Because the lens prompt fails to assert "Mirror canonically uses 13-sign Variant A", the LLM falls back to its RLHF-trained default that Ophiuchus is non-standard. |

**Critical gap:** No file in `services/` or `routers/` or the chat-path of `server.py` contains the text "13-sign", "Variant A", "midpoint13", or "Ophiuchus is a valid sign" as an LLM-facing instruction.

The only positive Ophiuchus-as-real text exists outside the chat path:
- `services/pressure_topology_engine.py:60-61` — content table ("integration under pressure").
- `services/iau_constellations.py:2-14` — IAU overlay narrative.
- `services/ophiuchus_metadata.py` — ruler/element/modality patch.

These never reach the chat LLM via the prompt assembly.

### Q5: Can Astrology Chat answer "What placements in my chart are in Ophiuchus?" using currently available context?

**YES — the data is present and complete; only the LLM's instruction layer prevents it.**

Proof:
- `services/astrology_conversation.py::build_chart_entity_index(chart)` produces a complete entity index that includes every placement with `sign="Ophiuchus"`.
- `format_chart_signals_block(index)` writes those placements into the CHART SIGNALS block with literal sign label `Ophiuchus`.
- This block IS injected into `system_prompt` on every Astrology Chat turn (mirror_chat.py:1770-1771).

A correct deterministic answer is therefore one regex / one filter away.  Pseudocode:
```python
ophi_placements = [
    e for e in index.values()
    if e.get("sign") == "Ophiuchus" and e.get("kind") in ("planet", "node", "angle")
]
```
For Mel this yields `[{"name": "Neptune", "sign": "Ophiuchus", "house": 5, ...}]` deterministically — without any LLM involvement.

The chat does not do this filter today because:
- No intent matches the query → no deterministic engine fires.
- The LLM is bound by `LENS_PROMPTS["astrology"]` to refuse, and has no Ophiuchus-positive counter-instruction.

So: **technically YES**, with the existing CHART SIGNALS block as input. **Practically NO**, because every layer that converts that block into a user-visible answer either (a) doesn't fire (FKR / engine router) or (b) is currently instructed to refuse (lens prompt).

### Q6: Is the problem A) Retrieval failure / B) Context assembly failure / C) Prompt suppression / D) LLM fallback / E) Multiple?

**E) Multiple causes — three converging defects.**

Confidence scores (qualitative — based on live verification):

| Defect class | Defect | Confidence | Evidence |
|--------------|--------|------------|----------|
| **A) Retrieval-router blindspot** | `classify_query` (FKR) has no Ophiuchus mode | **HIGH (95%)** | Live `classify_query("Do I have Ophiuchus in my chart?")` returns `[]`. Block emitted: 0 chars. Verified for both Pete (no Ophiuchus) and Mel (Neptune in Ophiuchus). |
| **A) Retrieval-router blindspot** | `classify_astrology_intent` has no Ophiuchus intent | **HIGH (95%)** | `_BODY_PATTERNS` (astrology_chat_router.py:36-49) lists 25+ patterns; none match "Ophiuchus". No code path returns `data_mode="ophiuchus_inventory"` or similar. |
| **C) Prompt suppression** | `LENS_PROMPTS["astrology"]` instructs the LLM to refuse and produces the exact failure phrase | **HIGH (98%)** | The failing user-visible string `"I don't have reliable data on Ophiuchus placements"` is a verbatim composition of two instruction lines in `server.py:1022` and `:1118`. |
| **D) LLM fallback** | LLM's 12-sign RLHF prior overwhelms data when prompt is silent on Ophiuchus | **HIGH (85%)** | Even when CHART SIGNALS contains "Neptune · Ophiuchus", the LLM hedges because nothing in the prompt confirms Ophiuchus is canonical for this user. |
| **B) Context assembly failure** | CHART SIGNALS block does not contain Ophiuchus | **REJECTED (5%)** | Live verification proves it DOES contain Ophiuchus for Mel/Isaac/Thaddeus. |

Ranking by impact:
1. **C+D (prompt + LLM) combined** — even for users WITH Ophiuchus placements, the LLM hedges or denies.
2. **A (retrieval router)** — for users WITHOUT Ophiuchus placements, FKR not firing means the LLM can't answer "no, you don't" with engine-grounded confidence; it falls back to the chart-signals block + lens prompt, which produces the hedge phrase.

---

## 4. Divergence point — first file/function

**File:** `/app/backend/services/forum_chat_knowledge_retrieval.py`
**Function:** `classify_query` (line 141)

**Evidence:**
```
Q="What is Thaddeus Ascendant?"          classify_query → ["FACT_LOOKUP"]   block_chars=5072 ✓ Ophiuchus
Q="What is Isaac MC?"                    classify_query → ["FACT_LOOKUP"]   block_chars=5176 ✓ Ophiuchus
Q="Do I have Ophiuchus in my chart?"     classify_query → []                block_chars=0    ✗
Q="What placements in my chart are in Ophiuchus?"
                                         classify_query → []                block_chars=0    ✗
```

This is the **first** point at which the two paths diverge in OUTCOME (not in code flow). Both questions hit the same `classify_query` function; one resolves to a deterministic mode, the other does not.

A second divergence happens at **`services/astrology_chat_router.py::classify_astrology_intent` (line 309)** — same function, identical "no Ophiuchus mode" defect, redundant safety net.

A third divergence happens at **`server.py:980` (`LENS_PROMPTS["astrology"]`)** — only fires for lens="astrology", contains the refusal instruction, **not** symmetric with Ask Mirror's lens=None branch.

---

## 5. Root cause ranking

| Rank | Cause | Class | Where | Independently sufficient to reproduce the failure? |
|------|-------|-------|-------|----------------------------------------------------|
| 1 | `LENS_PROMPTS["astrology"]` refuses placements not in CHART SIGNALS + has no Ophiuchus disclosure | Prompt suppression | `server.py:1019-1023, :1117-1137` | **Yes.** Even when data is in CHART SIGNALS, the prompt's structure tells the LLM to refuse if the user's query-shape is unfamiliar. |
| 2 | `classify_query` has no Ophiuchus mode → FKR emits no evidence | Retrieval failure | `services/forum_chat_knowledge_retrieval.py:141` | **Partial.** Removes the deterministic "Yes, you have Neptune in Ophiuchus at H5" engine-grounded block from the prompt, leaving only the LLM with CHART SIGNALS. |
| 3 | `classify_astrology_intent` has no Ophiuchus intent → no engine fires | Retrieval failure | `services/astrology_chat_router.py:309` | **Partial.** Same effect as #2 — strips deterministic backing. |
| 4 | No "Mirror is 13-sign Variant A canonical; Ophiuchus is first-class" instruction anywhere in the chat prompt path | Prompt omission | All of `mirror_chat.py:1009-2920` system_prompt construction | **Yes when combined with LLM prior.** Without this instruction, the LLM falls back to its training-time bias that Ophiuchus is non-canonical, overriding the chart-signals block. |
| 5 | `ASTROLOGY_DEEP_DIVE_PROMPT` line 2001 explicitly asserts Mirror is 12-sign | Stale prompt contradicting engine | `server.py:2001` | **Does not fire for Astrology Chat.** But if it ever did (e.g. via the deep-dive endpoint, which IS user-visible), it would deny Ophiuchus directly. |

---

## 6. What would the safest remediation look like (read-only — not implemented)

See `ASTROLOGY_CHAT_PARITY_AUDIT.md::§7` of the audit dossier and the companion document `ASTROLOGY_CHAT_PAYLOAD_DIFF.md` for full per-user payload diffs.  Three ranked options:

### Option A — Minimal fix (lowest blast radius)

Patch only the **prompt-suppression layer**:

1. Add an Ophiuchus disclosure paragraph to `LENS_PROMPTS["astrology"]` (`server.py:980-1198`) BEFORE the existing CHART SIGNALS rule:
   ```
   ZODIAC CANONICALITY: Mirror operates on a 13-sign canonical engine
   (midpoint13_variant_a_v1, "Variant A").  Ophiuchus is a first-class
   sign in this system.  When Ophiuchus appears in CHART SIGNALS for
   this user, treat it exactly as you would Pisces or Leo — answer
   without hedging, without disclaimers about "traditional astrology",
   and without "I don't have reliable data".  When Ophiuchus does NOT
   appear in CHART SIGNALS, you may state plainly that this user has
   no placements in Ophiuchus.
   ```
2. Add `"Traditional astrology does not recognize Ophiuchus"` and similar phrases to the existing FORBIDDEN HEDGES list (line 1117-1137).

**Blast radius:** Touches one constant in `server.py`. No DB changes, no calculator changes, no schema changes, no engine routing changes. Other lenses unaffected.
**Risk:** LLM may still hedge if RLHF prior is strong; relies on prompt obedience.
**Effort:** ~30 lines of text.

### Option B — Preferred fix (moderate blast radius, structurally correct)

Do A, **plus** add a deterministic Ophiuchus intent to BOTH classifiers:

1. `services/astrology_chat_router.py::classify_astrology_intent` — add new mode `"ophiuchus_inventory"` matched on regex `\bophiuchus|ophi|serpent.?bearer\b`.
2. `services/forum_chat_knowledge_retrieval.py::classify_query` — add new mode `OPHIUCHUS_INVENTORY` with the same regex.
3. Build a tiny `build_ophiuchus_inventory_block(chart)` proof-block helper that iterates `astro.angles + astro.planets` and lists every placement with `sign=="Ophiuchus"` (or explicitly states "no placements in Ophiuchus" when the list is empty).
4. Wire the new mode into `routers/mirror_chat.py:2147+` exactly like `house_inventory` already does.

**Blast radius:** Three files, one new tiny service helper. No DB / calculator / migration changes. Other lenses unaffected.
**Risk:** Low. Engine-grounded answer is now deterministic and cannot be denied by the LLM.
**Effort:** ~80 lines of code + tests for the four reference users.

### Option C — Full convergence onto FKR (highest blast radius)

Refactor so the chat-prompt layer drops the lens-specific "refuse outside CHART SIGNALS" suppression entirely and relies on FKR's `EVIDENCE` block as the single source of truth for ALL chart queries on every lens.

1. Move the CHART SIGNALS block out of the lens-conversation layer; merge it into FKR's evidence-block builder so every chart-shaped question gets a unified deterministic block.
2. Strip the "refuse outside CHART SIGNALS" rule from `LENS_PROMPTS["astrology"]` (the FKR evidence block becomes the authoritative grounding instead).
3. Add the Ophiuchus mode + builder from Option B.
4. Add lens-agnostic Ophiuchus disclosure to `MIRROR_SYSTEM_PROMPT` (one place, affects all lenses uniformly).
5. Audit and remove `ASTROLOGY_DEEP_DIVE_PROMPT:2001` 12-sign assertion (stale; contradicts canonical engine).

**Blast radius:** ~6 files, including a structural shift in how lens prompts ground themselves. Other lenses must be regression-tested.
**Risk:** Higher — touches the lens-conversation flow that all 6 lenses share. But this is the architecturally cleanest endpoint.
**Effort:** ~300 lines of code + full regression test of all 6 lens chats for all 4 reference users.

---

## 7. Constraints respected (read-only audit)

| Constraint | Status |
|------------|--------|
| Do not modify calculator math | ✅ Untouched |
| Do not modify stored charts | ✅ Untouched (DB reads only) |
| Do not modify migrations | ✅ Untouched |
| Do not modify birth data | ✅ Untouched |
| Do not modify prompts | ✅ All findings are read-only inspections of existing prompt strings. No prompt edits applied. |
| Do not modify rollout flags | ✅ Verified `.env`: `INTENT_ROUTER_V2_CUTOVER=false`, `INTENT_ROUTER_V2_ROLLOUT_PERCENT=10`, `RELATIONSHIP_ORCHESTRATION_PROMPT=false`, `CROSS_LENS_PROMPT_SURFACE=false` |
| Do not implement fixes | ✅ No code changes. |

---

## 8. Success criteria check

| Criterion | Answer |
|-----------|--------|
| 1. Why Ask Mirror knows Ophiuchus exists. | FKR `classify_query` resolves entity-named questions (e.g. "What is Thaddeus's Ascendant?") to `FACT_LOOKUP`, which emits a 5K-char EVIDENCE block containing the literal Ophiuchus placement from the stored chart. Ask Mirror has no lens-specific suppression rule, so the LLM answers from the block verbatim. |
| 2. Why Astrology Chat says Ophiuchus does not exist. | Three converging defects: (a) `classify_query` has no Ophiuchus mode → for generic Ophiuchus questions, FKR emits nothing; (b) `classify_astrology_intent` has no Ophiuchus mode → no engine fires; (c) `LENS_PROMPTS["astrology"]` instructs the LLM to refuse anything not in CHART SIGNALS using the exact phrase "I don't have reliable data" — AND has no Ophiuchus disclosure to counter the LLM's RLHF 12-sign prior. |
| 3. First file/function where divergence occurs. | `services/forum_chat_knowledge_retrieval.py::classify_query` (line 141) — first point at which the OUTCOME for Ophiuchus-shaped queries diverges from the OUTCOME for entity-named queries. Same function processes both, but only the entity-named one matches a mode. |
| 4. Safest remediation path. | Option B in §6 — minimal prompt patch + deterministic Ophiuchus intent in both classifiers + tiny ground-truth proof builder. ~80 lines, isolated to 3 files, no DB / calculator / migration / lens-cross-cutting changes. |

End of report.
