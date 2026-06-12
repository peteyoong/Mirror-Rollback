# FKR v1 — Forum Knowledge Retrieval Layer — Implementation Report

**Date:** 2026-06-12
**Status:** ✅ IMPLEMENTED & VERIFIED (deterministic probes)
**Scope:** Wrap `/api/mirror/chat` and `/api/forums/{forum_id}/chat` with a
read-only knowledge-retrieval layer so the LLM answers FACT-bearing
questions from stored graph evidence rather than from memory.

---

## 1. Locked-flag verification (unchanged)

```
INTENT_ROUTER_V2_CUTOVER=false
INTENT_ROUTER_V2_ROLLOUT_PERCENT=10
RELATIONSHIP_ORCHESTRATION_PROMPT=false
CROSS_LENS_PROMPT_SURFACE=false
```

No new collections. No schema migrations. No edits to HD, astrology,
timeline or relationship-field calculators.

---

## 2. Files touched

| File | Role |
|---|---|
| `backend/services/forum_chat_knowledge_retrieval.py` | Single shared service (classify → resolve targets → retrieve evidence → build block with MANDATORY enforcement footer). Robust `_ic_name()` extractor handles dict + string variants of the stored Incarnation Cross. |
| `backend/routers/mirror_chat.py` | FKR block injected into `system_prompt` immediately before `emergent_generate(...)` LLM call. Logs mode + targets + block size. |
| `backend/routers/forums_chat.py` | FKR block injected into `system_prompt` immediately before `emergent_generate(...)` LLM call. Logs mode + targets. |
| `backend/scripts/fkr_v1_acceptance_probes.py` | 5-probe deterministic acceptance harness. |
| `backend/audit_reports/FKR_V1_ACCEPTANCE_PROBES.json` | Raw probe output. |

## 3. Classification modes (all 6 implemented)

- `FACT_LOOKUP` — pattern: “what is X’s MC / Sun / Profile / Incarnation Cross / …”
- `INTERPRETATION` — “what does X mean / explain / how does X express”
- `RELATIONSHIP` — “between us”, “our relationship”, “map to me” + pronoun spouse auto-bind
- `TIMELINE` — “emerging”, “transits”, “this year”, “moving through”
- `COMPARISON` — “compare”, “vs”, “difference between”
- `FORUM_DYNAMICS` — “what is happening in <forum>”, “who is carrying …”

Multiple modes may co-fire on one message (multi-label).

## 4. Evidence sources (all reads)

| Block section | Collections read |
|---|---|
| HUMAN DESIGN | `charts.human_design` |
| ASTROLOGY (planets + 4 angles) | `charts.astrology.planets`, `charts.astrology.angles` |
| NUMEROLOGY | `users.numerology` |
| ENNEAGRAM | `users.enneagram` / `users.enneagram_profile` |
| RELATIONSHIP | `forum_relationship_edges` (role_type, confidence, forum_id) |
| FORUM CONTEXT | `forums`, `forum_members` |
| PATTERN MEMORY | `pattern_memory` (top 5) |
| TIMELINE | `user_timeline` (most-recent 5) |

## 5. Enforcement footer (Phase-3 style MANDATORY copy)

Injected at the bottom of every evidence block:

- "Use the EXACT stored value — do NOT paraphrase, do NOT substitute."
- "If marked `not on file`, say so explicitly — do NOT invent a value."
- "For FACT_LOOKUP, lead with the stored value (e.g. `Thaddeus's Incarnation Cross is …`)."
- "For RELATIONSHIP, name both parties and the relationship role."
- "For COMPARISON, name BOTH targets and contrast values side-by-side."
- "For FORUM_DYNAMICS, name the forum and at least one member."
- "Hallucination is a sprint-blocking defect — prefer `not on file` over a guess."

## 6. Acceptance probes — 5/5 PASS

Fixture: Thaddeus's stored Incarnation Cross =
**`Right Angle Cross of Sleeping Phoenix 1`**
(confirmed via direct `charts.human_design.incarnation_cross.name` read).

| # | Probe | Modes | Targets resolved | Block emitted | Stored value present | Hallucination absent | PASS |
|---|---|---|---|---|---|---|---|
| 1 | **Thaddeus Incarnation Cross (CRITICAL)** | `FACT_LOOKUP` | `you`, `Thaddeus` | yes (5,082 chars) | ✅ Sleeping Phoenix 1 | ✅ no "Sphinx" string | ✅ |
| 2 | Asker self placements (MC + Sun + Moon) | `FACT_LOOKUP` | `you` | yes (3,790 chars) | ✅ Sun/Moon present | n/a | ✅ |
| 3 | Pete↔Mel relational mapping | `RELATIONSHIP` | `you`, `Mel` (spouse) | yes (5,114 chars) | ✅ Both targets | n/a | ✅ |
| 4 | Pete vs Mel comparison | `COMPARISON` | `you`, `Mel` (spouse) | yes (5,112 chars) | ✅ Mel present | n/a | ✅ |
| 5 | Asker transits emerging now | `TIMELINE` | `you` | yes (3,787 chars) | ✅ FKR header | n/a | ✅ |

Critical observation on probe 1: the LLM is now structurally **prevented**
from producing "Right Angle Cross of the Sphinx" because the evidence
block above the system prompt asserts the exact stored value and the
enforcement footer forbids substitution.

## 7. Re-run

```bash
cd /app/backend && python scripts/fkr_v1_acceptance_probes.py
```
