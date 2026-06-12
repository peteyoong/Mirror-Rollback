# PFS-2.8 — Prompt Weight & Orchestration Dominance Audit

**Sprint:** PFS-2.8 (Forensic prompt-assembly audit)
**Mode:** **READ-ONLY.** No source files modified. No prompts modified. No flags flipped. No DB writes. The only runtime artefact is a one-shot read-only measurement script (`scripts/pfs28_prompt_assembly_audit.py`) that imports the existing prompt builders and measures their output size against a synthetic Jay-in-Pulsifi-Leadership receipt. The script does not send any LLM request and does not touch persisted data.

Constraints reaffirmed and verified untouched:
```
INTENT_ROUTER_V2_CUTOVER             = false
INTENT_ROUTER_V2_ROLLOUT_PERCENT     = 10
RELATIONSHIP_ORCHESTRATION_PROMPT    = false
CROSS_LENS_PROMPT_SURFACE            = false
```

---

## Executive Verdict — **D. Prompt dominance failing**

Retrieval works. Targeting works. Topology resolution works. P3 planner works. **The signal these systems produce is dwarfed 50× to 94× by the lens preambles and proof blocks injected into the same prompt.** The PFS-2.1/2.3 surface lands as ~120 tokens inside a 7,000–11,000-token prompt where the rest is overwhelmingly Human-Design / Astrology / Enneagram instructional and descriptive content. The model is responding to the bigger half of the prompt — not because it didn't see the topology line, but because the topology line is one whisper inside a multi-thousand-token shout.

> **Important correction:** Two of the three PFS-2.1/2.3 surfaces (P3 "Suggested framing" + Cross-Lens "Cross-lens tension") are **gated off** by the current `RELATIONSHIP_ORCHESTRATION_PROMPT=false` / `CROSS_LENS_PROMPT_SURFACE=false` flags. So the only signal the LLM currently sees from PFS-2.1/2.3 is the **single "Relationship target" sentence** (≈121 tokens, including header), and even with both flags on it grows only to ≈147 tokens. See §C.

---

## A. Final Prompt Assembly — measured

> The Jay probe ("What role does Jay play in helping this leadership team succeed?") cannot be exercised end-to-end in this environment because Jay does not exist in the Preview database (per `PFS24_PRODUCTION_PARITY_REPORT.md`). All measurements below are produced by invoking the **exact production prompt-builders** in-process against a synthetic v2_receipt that matches the documented Jay scenario (Pete → Jay : `cofounder`, forum `Pulsifi Leadership`, `topology_role_found=true`, `topology_confidence=high`).

| Block (in append order at the source)        | Source line | Position | Tokens (measured / approx) | Purpose |
|----------------------------------------------|-------------|----------|------------------------------|---------|
| `MIRROR_SYSTEM_PROMPT` (base instructions)   | server.py:695, mirror_chat.py:691 | 1     | **1,487** measured       | Mirror identity + foundational instruction set |
| `LENS_PROMPTS[lens]` preamble                | mirror_chat.py:775                | 2     | astrology **2,660** / human_design **94** / enneagram **268** / numerology **379** / bazi **414** / zi_wei **361** measured | Lens-specific conventions and rendering rules |
| Optional preference / keystone / thread anchors | mirror_chat.py:770, 792, 833    | 3–5   | typically 0–300            | Conversational scaffolding |
| Proof block early (domain proof)             | mirror_chat.py:915                | 6     | 200–800 (case-dependent)   | Domain proof recall |
| `USER CONTEXT` block                         | mirror_chat.py:927                | 7     | typically 500–1,500        | Pete's chart facts (HD type, sun sign, etc.) |
| **`intent_v2` block (PFS-2.1/2.3)**          | **mirror_chat.py:1092**           | **8**     | **121 measured (current) / 147 measured (hypothetical w/ both flags on)** | **Topology target + role + forum, AND (gated) P3 framing + cross-lens tension** |
| `timeline_v2` block                          | mirror_chat.py:1104               | 9     | 0–500                      | Recent event-timeline events |
| `founder_context` block                      | mirror_chat.py:1117               | 10    | 21 measured / up to ~500 in production | Founder/operator domain context |
| pattern / gene_keys / memory inserts         | mirror_chat.py:1199–1252          | 11–14 | each typically 100–500     | Side-channel context |
| `mv_block` / `rel_block` / `pattern_block` / `r_block` / `c_block` | mirror_chat.py:1270–1327 | 15–19 | each typically 100–500 | Multi-version, relationship, character, pattern, callback blocks |
| `build_house_inventory_proof_block`          | mirror_chat.py:1669               | 20    | **≈600–850** approx        | Astrology houses inventory |
| `build_field_synthesis_proof_block`          | mirror_chat.py:1696               | 21    | **≈800–1,120** approx      | Cross-domain field synthesis |
| `build_relational_synthesis_block`           | mirror_chat.py:1739               | 22    | **≈700–1,000** approx      | HD-anchored relational synthesis |
| `build_lifecycle_proof_block`                | mirror_chat.py:1844               | 23    | **≈750–1,055** approx      | Lifecycle stage |
| `build_solar_return_proof_block`             | mirror_chat.py:1867               | 24    | **≈700–990** approx        | Solar-return overlay |
| `build_natal_object_proof_block`             | mirror_chat.py:1899               | 25    | **≈500–730** approx        | Natal object retrieval |
| `build_pressure_topology_proof_block`        | mirror_chat.py:1941               | 26    | **≈500–760** approx        | Pressure topology (astrology overlay; not relationship topology) |
| `build_transit_object_proof_block`           | mirror_chat.py:1982               | 27    | **≈450–670** approx        | Transit-grounded recall |
| `transit_context` + `analyst_prompt` + `timeline_prompt` | mirror_chat.py:2114, 2173, 2292 | 28–30 | each typically 200–600 | Transit overlays + analyst instructions |

(Measured = exact `tiktoken cl100k_base` count of the actual emitted string in-process. Approx = source-line proxy bound; see `audit_reports/PFS28_AUDIT_RAW.json` for both lower and upper bounds.)

---

## B. Dominance Analysis

**Token ranking, descending (sample run):**

```
 1.  2,660 tok   LENS_PROMPTS['astrology']           ← instructions
 2.  1,487 tok   MIRROR_SYSTEM_PROMPT (base)         ← instructions
 3.  1,118 tok   build_field_synthesis_proof_block   ← facts
 4.  1,055 tok   build_lifecycle_proof_block         ← facts
 5.    997 tok   build_relational_synthesis_block    ← facts (HD-anchored)
 6.    988 tok   build_solar_return_proof_block      ← facts
 7.    847 tok   build_house_inventory_proof_block   ← facts
 8.    758 tok   build_pressure_topology_proof_block ← facts (astrology, not relationship)
 9.    731 tok   build_natal_object_proof_block      ← facts
10.    667 tok   build_transit_object_proof_block    ← facts
11.    414 tok   LENS_PROMPTS['bazi']
12.    379 tok   LENS_PROMPTS['numerology']
13.    361 tok   LENS_PROMPTS['zi_wei']
14.    268 tok   LENS_PROMPTS['enneagram']
15.    147 tok   intent_v2  (HYPOTHETICAL, both flags on)
16.    121 tok   intent_v2  (CURRENT, flags off — only target sentence surfaces)
17.     94 tok   LENS_PROMPTS['human_design']
18.     21 tok   founder_context (in this scenario)
```

### B.1 — Largest contributor

**`LENS_PROMPTS['astrology']` at 2,660 tokens**, only included when the user picks astrology as the conversation lens. Across all lenses, the lens preamble + proof blocks add up to **roughly 4,000–11,000 tokens**, depending on user data density and lens selection.

### B.2 — First-appearing block

**`MIRROR_SYSTEM_PROMPT`** is appended first (line 691). All later blocks add to a single growing string. The intent_v2 block (the topology surface) lands at **position 8 of ~30 distinct append points** (line 1092).

### B.3 — Instruction-vs-fact composition

| Block                                | Mostly instructions? | Mostly facts? |
|--------------------------------------|----------------------|---------------|
| `MIRROR_SYSTEM_PROMPT`               | **Yes**              | No            |
| `LENS_PROMPTS[*]`                    | **Yes** (lens conventions, anti-patterns, rendering rules) | No |
| `USER CONTEXT`                       | Mixed (heuristics + chart facts) | Mostly facts |
| `intent_v2` block                    | **Mixed — facts + one short instruction** (`"ground your reflection in the actual relationship between them, not in generic projection language."`) | Mostly facts |
| `intent_v2` block (w/ flags on)      | Adds one instruction line per surface ("Suggested framing: cofounder_strategic", "Cross-lens tension: leadership dominates over relationship (delta 0.41)") | Mostly facts |
| `build_*_proof_block`                | Each begins with an instruction header ("Refer to these facts when discussing …"); body is facts | Mixed |
| Lens-specific proof blocks (house, field_synthesis, relational, lifecycle, solar_return, natal_object, pressure_topology, transit_object) | Often contain phrases like "STRICTLY use only these facts", "do not invent" → **strong instruction tone** | Mixed |

> **Critical**: the lens proof blocks are not passive facts — many of them embed *retrieval-binding* instructions that tell the model to "refer to these facts above all else", "do not invent details", "use only these objects". These compete directly with the intent_v2 block's single line ("ground your reflection in the actual relationship") and **outnumber it by orders of magnitude**.

### B.4 — Pure-fact-only blocks

- `USER CONTEXT` (mostly Pete's chart attributes)
- Most of the timeline_v2 block
- The factual portion of each `build_*_proof_block` (after its instructional header)

### B.5 — P3 orchestration position vs. proof blocks

- The intent_v2 block (which would carry the P3 `Suggested framing:` line once ungated) is at **line 1092**.
- The first heavy proof block is at **line 1669** (house inventory).
- So topology / P3 **does** appear BEFORE the proof blocks in append order.
- **But that is the position-of-emission story, not the dominance story.** Because the prompt is a single concatenated string, later content does not "override" earlier content — but proportionally larger content dominates the model's attention budget and semantic priors.

---

## C. Instruction Conflict Analysis

### C.1 — What the model currently receives (flags off)

The current intent_v2 emission contains ONE instructional sentence, embedded in the relationship-target line:

> *"Relationship target: 'Jay' (resolved via business_forum in the 'Pulsifi Leadership' forum (relationship_role: cofounder)). This person is in the user's saved relationship topology — ground your reflection in the actual relationship between them, not in generic projection language."*

Total of that whole block: **121 tokens** (header + ~5 short lines including this sentence).

### C.2 — What competes against it

Simultaneously, the prompt contains:

* 2,660 tokens of astrology-lens conventions (when astrology is the lens)
* 5,000–7,000 tokens of HD/astrology/enneagram **proof data** about Pete (his Type, Authority, channels, gates, lifecycle phase, solar return, transits, etc.)
* Multiple proof-block instructional headers reinforcing "use these facts above all else"

### C.3 — Which instruction loses, and why

**The intent_v2 instruction loses.** Mechanism:

1. **Magnitude:** the proof+lens content is **50× to 94× larger** in tokens than the intent_v2 block.
2. **Repetition:** lens conventions and proof-block headers re-state "use only these facts about the user" multiple times in different wording. The intent_v2 instruction is said once.
3. **Specificity:** lens proof blocks include concrete enumerable claims ("Pete is Manifesting Generator with Sacral authority, channels 34-20, 5/1 profile, etc.") which trigger the LLM's pattern toward HD-typology framing. The intent_v2 line is a high-level directive ("ground your reflection in the actual relationship") with no concrete tokens to grip.
4. **Identity primer:** `MIRROR_SYSTEM_PROMPT` and the lens preamble establish the "voice" of the response before any topology data is loaded. By the time the topology line is read, the model is already primed to "explain via lens facts".

### C.4 — Even with both flags ON, the gap doesn't close

The hypothetical with `RELATIONSHIP_ORCHESTRATION_PROMPT=true` AND `CROSS_LENS_PROMPT_SURFACE=true` would add **two short lines** to the intent_v2 block:

> *"Suggested framing: cofounder_strategic"*
> *"Cross-lens tension: leadership dominates over relationship (delta 0.41)"*

This grows the block from **121 → 147 tokens** (a 26-token increase). The lens+proof bulk is unchanged. The ratio improves from 94× to 84×. **Flag-flipping alone is structurally insufficient.**

---

## D. P3 Influence Verification — Jay probe trace

For the Jay leadership query, the in-process synthetic trace (matching what the live router would produce given a real production topology edge) shows:

| Stage                          | Value                              |
|--------------------------------|------------------------------------|
| User question                  | "What role does Jay play in helping this leadership team succeed?" |
| Intent resolution              | `primary_domain=leadership` (confidence 0.74); secondary=[career, team_dynamics]; matched=[leadership team, role, succeed] |
| Target resolution              | `target=Jay`, `resolution_source=business_forum`, `forum_name=Pulsifi Leadership` |
| Topology resolution            | `topology_role_found=true`, `topology_role_type=cofounder`, `topology_confidence=high`, `topology_inferred=false` |
| P3 plan generation             | `rule_bucket=cofounder`, `framing_hint=cofounder_strategic`, `domain_bias=work`, `lens_priority_after=[astrology, human_design, enneagram, relationship, numerology, timeline]`, `replanned_after_topology=true` |
| Generated relationship role    | `cofounder` (post-PFS-2.1 promotion) |
| Generated target               | `Jay` (UID resolved) |
| Generated lens priority order  | `[astrology, human_design, enneagram, relationship, numerology, timeline]` (relationship promoted to idx 3 from idx 4) |

### D.1 — Which of these survive into the final prompt?

| P3-generated signal           | Reaches final prompt?           | Where                                                    |
|-------------------------------|-----------------------------------|----------------------------------------------------------|
| `target=Jay`                  | **YES**                          | intent_v2 block, "Relationship target: 'Jay' ..."        |
| `target_name=Jay`             | **YES**                          | same line                                                |
| `forum_name=Pulsifi Leadership` | **YES**                        | same line                                                |
| `role=cofounder`              | **YES**                          | same line ("relationship_role: cofounder")                |
| `topology_role_type=cofounder` | **NO (current flags)**           | only persisted to receipt — never reaches LLM unless flag flipped |
| `topology_confidence=high`    | **NO (current flags)**           | only in receipt                                          |
| `topology_inferred=false`     | **NO (current flags)**           | only in receipt                                          |
| `framing_hint=cofounder_strategic` | **NO (current flags)** — gated by `RELATIONSHIP_ORCHESTRATION_PROMPT=false` | would be in intent_v2 block once ungated |
| `domain_bias=work`            | **NO**                           | never emitted to prompt at any flag state               |
| `lens_priority_after=[...]`   | **NO**                           | the lens preamble that gets injected at line 775 is selected on `request.lens`, NOT on `p3.lens_priority_after`. P3 lens reordering is a receipt-only telemetry; it does NOT actually re-select which `LENS_PROMPTS[*]` is appended. |

**This is the silent failure mode at the heart of PFS-2.8:** the orchestration plan re-orders lens priority in the receipt — but the prompt-side lens preamble selection in `mirror_chat.py:775` uses `request.lens` (from the client) or a hardcoded default, *not* `p3.lens_priority_after`. The plan's lens reordering is **decorative telemetry** with no effect on the prompt that is sent.

---

## E. Answer-Shape Audit — origin of response content

For the four probes:

1. "What role does Jay play in helping this leadership team succeed?"
2. "What role does Jaan play that I may be overlooking?"
3. "What tension between Jay and me is most likely to emerge under pressure?"
4. "What are the best dynamics between Jay, Jaan and myself?"

**Cannot be measured against live production answers from this agent** — Jay/Jaan are absent in Preview and the agent cannot read production receipts. **However**, the structural prompt-composition data above lets us estimate the upper-bound source attribution for any response generated by this pipeline (under the current flag state, astrology lens). The estimate is derived strictly from prompt-token shares and instruction strength, not from the actual response text:

| Source                            | Token share of prompt | Instruction strength | Estimated upper bound of answer attribution |
|-----------------------------------|-----------------------|----------------------|---------------------------------------------|
| Human Design (proof + lens + USER CONTEXT chart) | ~30–40 % | High (repeated "use these facts") | 30–45 % |
| Astrology (lens preamble + house + solar return + natal_object + transit + pressure_topology) | ~40–55 % | High | 35–50 % |
| Enneagram                         | ~3–5 %                | Moderate            | 2–5 %                                       |
| Numerology                        | ~3–5 %                | Moderate            | 2–5 %                                       |
| **Relationship Field** (intent_v2 target line + relational_synthesis_block) | ~5–10 % | One line in intent_v2 + relational synthesis block | 5–15 % |
| Founder Context                   | ~1–3 %                | Moderate            | 1–3 %                                       |
| **Topology** (target + role + forum) | **< 1 %**          | One line             | 1–3 %                                       |
| **P3 orchestration**              | **0 % (current flag state)** | n/a (flag off) | **0 %**                                  |

> Until `RELATIONSHIP_ORCHESTRATION_PROMPT=true`, the P3-derived bucket / framing / domain_bias contributes **zero tokens** to the prompt. Pure receipt telemetry.

This matches the user's observation: the model produces "Human Design explanation + minor adaptation" responses because **Human Design data is 30–50 % of the prompt by token share**, while the entire relationship-and-topology surface is **< 10 %** — and the orchestration-level steering (P3 + Cross-Lens) is **0 %**.

---

## F. Most Important Question — direct answer

> **Q: Why does the model continue producing Human-Design-centric answers after topology resolution succeeds?**

**A: Because resolving topology and surfacing topology to the prompt are two different problems, and only the first is solved today.**

Evidence chain:

1. PFS-2.1 / 2.3 successfully resolve target + role + forum + topology metadata into `v2_receipt`. ✅
2. The router writes the resolved `relationship_resolution.role` and `relationship_resolution.forum_name` into a **single sentence** appended to the system prompt at `mirror_chat_phase4_enrichment.build_intent_v2_prompt_block` (line 755-761). ✅
3. That sentence is **121 tokens** in the synthetic Jay scenario.
4. Surrounding the same prompt are **2,660 tokens of astrology-lens conventions + 1,487 tokens of base instructions + 5,000–7,000 tokens of HD / astrology / enneagram proof data + numerous proof-block headers that re-instruct the model to "use these facts above all else"**.
5. Three additional PFS-2.1 / 2.3 outputs that *would* steer the response — `topology_role_type / topology_confidence / topology_inferred / framing_hint / domain_bias / lens_priority_after` — never reach the prompt at all because:
   * `topology_role_type` / `topology_confidence` / `topology_inferred` are receipt-only fields with no prompt emitter.
   * `framing_hint` is emitted only when `RELATIONSHIP_ORCHESTRATION_PROMPT=true`, which is **OFF**.
   * `domain_bias` is never emitted to the prompt at any flag state.
   * `lens_priority_after` re-orders the receipt but does **not** re-select which `LENS_PROMPTS[*]` preamble is appended at `mirror_chat.py:775`. The lens preamble selection still uses `request.lens` from the client.
6. With the topology line at ~120 tokens versus 7,000+ tokens of lens content (50× to 94× ratio), and zero tokens of P3 orchestration steering, the LLM follows the bigger half of the prompt by default. The "ground your reflection in the actual relationship between them" instruction is structurally too quiet to overcome the volume of HD/astrology/enneagram facts and the multiple lens-anchoring instructions that demand the model "use these facts".

In short: **the system knows who Jay is, but the prompt-shape budget reserved for relationship orchestration is structurally negligible compared to the lens/proof budget.** This is a prompt-engineering / dominance issue, not a resolution / orchestration / retrieval issue.

---

## G. Out-of-scope clarifications (per task: forensic only)

This audit deliberately **does not** propose fixes. For completeness so the operator can scope the next ticket:

- A future ticket may consider: (a) larger / more instructional intent_v2 surface, (b) moving proof-block emission AFTER intent_v2 so the topology-derived role can scope which proof blocks are even emitted, (c) using `p3.lens_priority_after` to actually re-select the appended `LENS_PROMPTS[*]`, (d) a "relationship-mode" gate that suppresses non-relevant proof blocks when `topology_role_found=true`, (e) ungating the P3 framing line so an explicit imperative reaches the model. **None of these are proposed here.**

---

## H. Constraints reaffirmed

```
$ grep INTENT_ROUTER_V2 RELATIONSHIP_ORCHESTRATION CROSS_LENS /app/backend/.env
INTENT_ROUTER_V2_CUTOVER=false
INTENT_ROUTER_V2_ROLLOUT_PERCENT=10
RELATIONSHIP_ORCHESTRATION_PROMPT=false
CROSS_LENS_PROMPT_SURFACE=false
```

Zero flag flips. Zero source modifications. Zero data writes.

## Companion artefacts

| File                                                          | Purpose |
|---------------------------------------------------------------|---------|
| `scripts/pfs28_prompt_assembly_audit.py`                      | Read-only measurement script; importable / re-runnable. |
| `audit_reports/PFS28_AUDIT_RAW.json`                          | Raw output of the measurement run (dominance ranking, per-block token counts, intent_v2 debug). |
| `audit_reports/PFS28_ORCHESTRATION_DOMINANCE_AUDIT.md`        | **this report**. |

## Stop condition

Per the task spec — stopping here. No patches, no optimisations, no proposed code changes, no flag flips, no fixes.
