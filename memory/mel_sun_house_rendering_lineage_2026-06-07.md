# Forensic — Mel's Sun House: data-lineage trace
**Date:** 2026-06-07  ·  **Subject:** Pete asking about Mel ("Member" tab in Ask Mirror)
**Reported defect:** Mirror says *"Mel's Sun in Gemini is positioned in the **11th house**"*
**Mode:** Read-only — NO code modified, NO migration, NO recompute.

> **TL;DR:** Every deterministic data stage in Mirror returns **House 12** for Mel's Sun.  The "11" appears for the first time at the **LLM generation step**.  It is a **Sun↔Mercury conflation hallucination** — both Sun and Mercury sit in Gemini for Mel, Mercury is in house 11, and the LLM is binding Sun's sign to Mercury's house number.  A second contributing factor is that the **lens grounding block silently crashes** for every Mirror chart (schema mismatch in `astrology_conversation.build_chart_entity_index`) — so the deterministic *"Sun · Gemini · House 12"* line never reaches the LLM's prompt.

---

## STAGE 1 — Stored astrology document (Mel)
*Source: `db.charts` where `user_id = 697ec826ad4b18f75bf42616`.*

```
sun.longitude         = 79.48916°   (sidereal)
sun.tropical_longitude= 110.51085°
sun.sign              = "Gemini"
sun.degree            = 22.35°
sun.formatted         = "22°Gemini"
sun.house             = 12          ← ground truth
sun.retrograde        = False
metadata.engine_marker= (None — set by sidereal-config not chart)
metadata.house_system = "Equal"
```

Adjacent planet for context:
```
mercury.sign  = "Gemini"
mercury.house = 11
mercury.degree= 1.93°
```

Both **Sun** and **Mercury** are in Gemini.  Sun in House 12, Mercury in House 11.

## STAGE 2 — Lens chart-entity index
*Function:* `services/astrology_conversation.py::build_chart_entity_index(chart)`
*Called from:* `lens_registries/astrology._AstrologyRegistry.build_index`
*Reads:* `astro["planets"]["Sun"]["house"]` ⇒ `12` (line 164: `"house": p.get("house")`)

**🚨 SCHEMA-MISMATCH CRASH detected at line 241:**
```python
sign_on_cusp = (cusp or {}).get("sign")
                            ^^^^^^^^^^^
AttributeError: 'str' object has no attribute 'get'
```
The function expects `houses.formatted_cusps` to be a `List[Dict]` (e.g. `{"sign": "Cancer", "degree": 4.09, ...}`) but Mel's stored chart has `formatted_cusps` as a `List[str]` — e.g. `["4°Cancer", "8°Leo", ...]`.

**Effect:** the function raises before it completes, so the lens grounding block **never gets built**.  The chat layer's outer try/except (`mirror_chat_pipeline.build_lens_context`) silently swallows it and returns `(None, None)` — the LLM gets NO deterministic *"Sun · Gemini · House 12"* line.

(Same crash happens for every Mirror chart because every chart's cusps are strings — confirmed live: running the function on Mel raises `AttributeError`.)

## STAGE 3 — Lens grounding block injected into prompt
*Function:* `services/astrology_conversation.py::format_chart_signals_block(index)`

Because Stage 2 raised, this stage is **never reached**.  The grounding block that *would have* been added is:
```
--- CHART SIGNALS (grounded source of truth) ---
  - Sun · Gemini · House 12 · 22.4°
  - Moon · Scorpio · House 5 · 1.5°
  - Mercury · Gemini · House 11 · 1.9°
  ...
```
Note that the `Sun · House 12` and `Mercury · House 11` lines are adjacent and both carry `Gemini`.

## STAGE 4 — Natal-object proof block (if it fires)
*Function:* `services/natal_object_engine.py::build_natal_object_proof_block(env)`
*Trigger:* would inject "Mel's Sun ⇒ Gemini · House 12 · 22°21′05″" into the system prompt — but ONLY if the chat router's `_NATAL_OBJECT_TRIGGER_RE` regex matches.

Looking at the user's question pattern: *"Reflection test (member)."* or "tell me about Mel" — these do **not** match the natal_object trigger (which expects shapes like *"my Sun"* / *"what house is X in"* / *"tell me about my Lilith"*).  So this strict proof block was **NOT injected**.

## STAGE 5 — Final prompt sent to LLM
What actually reaches the LLM about Mel:

a) **Member-resolver context** (relationship_role, target_name, target_chart pointer — but not formatted as sign/house strings).
b) **Relational synthesis block** (role + closeness + emotional_weight; no chart placements).
c) **Multi-lens memory block — EMPTY for the asker's chart** (Stage-2 crash) → no `Sun · Gemini · House 12` line.
d) **Mel's chart object** is passed through context, but the LLM must extract values itself; without a strict proof block instructing it, it is free to confabulate.
e) **History** of prior turns — sometimes contains `"Mercury in Gemini in her 11th house"` (verified in `forum_chat_messages` for Mel).

The LLM ends up with:
- knowledge that Mel's **Sun is in Gemini** (correct)
- knowledge that *something* of Mel's is in **house 11** (Mercury, in earlier turns)
- both planets sharing the same sign (Gemini)
- no hard rule that locks Sun's house to 12

It **infers / completes** "Sun in Gemini is positioned in the 11th house" — pulling the house number from Mercury and bonding it to Sun.

## STAGE 6 — Where 12 → 11 transitions

| Stage | Sun house value | Source confidence |
|------:|:---|---|
| 1. DB document | **12** | deterministic |
| 2. Lens chart-entity index | (crashes — no value emitted) | broken |
| 3. Lens grounding block | (empty due to Stage-2 crash) | broken |
| 4. Natal-object proof block | (not invoked — trigger regex didn't match the user question) | inactive |
| 5. Final LLM system prompt | (lacks any explicit `Sun · House 12` line) | unprotected |
| 6. LLM generation | **11** | **HALLUCINATED — Sun↔Mercury conflation** |

The number changes from 12 → 11 **only at Stage 6**, in the LLM generation pass.  No engine, database row, or proof-block builder ever stores or emits `11` for Mel's Sun.

---

## Root cause classification

| Root cause | Evidence | Severity |
|---|---|---|
| **A. LLM hallucination via Sun↔Mercury sign conflation** | Both planets in Gemini; Mercury.house = 11; LLM binds Sun's sign to Mercury's house | **PRIMARY** |
| **B. Lens grounding block crashes on every Mirror chart** | `build_chart_entity_index` raises `AttributeError` on `formatted_cusps` (str vs dict) | **CONTRIBUTING** |
| **C. Natal-object proof block didn't fire** | The user's question pattern doesn't match `_NATAL_OBJECT_TRIGGER_RE` ("tell me about Mel" / "reflection test") | **CONTRIBUTING** |
| **D. Member-target routing has no strict natal-data lockdown** | Member chart is passed as object, not as a fenced proof block with hard rules | **CONTRIBUTING** |
| E. Stored data wrong | — sun.house is 12 in DB | **NOT a cause** |
| F. Engine recompute mismatch | — engine identifies Sun.house = 12 correctly | **NOT a cause** |

## What is NOT broken
- ✅ Engine math: Sun assigned to House 12 correctly (sidereal Sun 79.49° in Equal cusps anchored at sidereal ASC 89.10°).
- ✅ Stored data: `sun.house = 12` ✓
- ✅ Natal-object engine: returns Sun house = 12 when invoked.
- ✅ GM agrees: GM also lists Mel's Sun in House 12.
- ✅ House-system / ayanamsa / SVP unchanged since GM-V2 freeze.

---

## Recommended fixes (NOT applied — per instruction)

If/when you authorize a fix, three small surgical changes would close this hallucination corridor:

1. **(highest leverage)** Patch `astrology_conversation.build_chart_entity_index` to tolerate `formatted_cusps` being either a list of dicts OR a list of strings (parse `"4°Cancer"` → `{sign: "Cancer", degree: 4.0}`).  Two lines.  Restores the deterministic `Sun · Gemini · House 12` grounding line to every Mirror chat.

2. **(secondary)** When `_astro_target_user_id` is set (Member tab), build a fenced **TARGET PROOF BLOCK** for the target's chart — minimum: Sun, Moon, ASC, MC sign + house + degree — and inject it with a hard rule:
   ```
   ABSOLUTE RULE: The placements above are the ONLY chart values you may
   cite for {target_name}.  Do not infer, swap, or interpolate.
   ```
   Same pattern as the lifecycle proof block from astrology-lifecycle-v1.

3. **(tertiary)** Add a "same-sign sibling" defence to the natal-object proof block: when two planets share a sign, the block must explicitly call out *"Sun is in House 12 — NOT to be confused with Mercury (also Gemini, House 11)"*. Reduces LLM conflation under any future grounding-block change.

None of these touch chart math, ayanamsa, house system, or migration.

---

**Report saved to** `/app/memory/mel_sun_house_rendering_lineage_2026-06-07.md`.

Status:  No code, math, ayanamsa, house system, chart, DB record, or cache modified by this audit.
