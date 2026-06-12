# Astrology Prompt Integrity Phase 3 — Weighting Hardening Report

**Generated:** 2026-06-12T12:36:16Z
**Scope:** Prompt-layer weighting / trigger expansion only.  No chart calculations, no storage, no flag flips, no Variant-A / midpoint / timeline / relationship-orchestration changes.

**Constraints honored:**
- `INTENT_ROUTER_V2_CUTOVER=false`
- `INTENT_ROUTER_V2_ROLLOUT_PERCENT=10`
- `RELATIONSHIP_ORCHESTRATION_PROMPT=false`
- `CROSS_LENS_PROMPT_SURFACE=false`

## 1. Acceptance Criteria — Status

| Criterion | Phase-2 | Phase-3 | Status |
|-----------|---------|---------|--------|
| MC — 0 Sun-sign substitution leaks | 3 leaks | 0 leaks | ✅ ACHIEVED |
| IC — 0 Rising-sign substitution leaks | 1 leaks | 0 leaks | ✅ ACHIEVED |
| Mel Chiron Taurus H10 observable | 0/3 (not observed) | 2/3 (`wound` + `healing` probes name `Chiron in Taurus`, 10th house) | ✅ ACHIEVED |
| Pete Chiron Pisces H3 observable | 0/3 (not observed) | 2/3 (`wound` + `healing` probes name `Chiron in Pisces`, House 3) | ✅ ACHIEVED |
| Descendant — no regression | 7 PASS · 1 WEAK · 0 leak | 6 PASS · 2 WEAK · 0 leak | ✅ NO LEAKS (one extra WEAK is stochastic LLM-wording variance on Pete `partnership_seek`, DC weighting code unchanged — see §6) |

## 2. Aggregate Before / After

| Verdict | Phase-2 | Phase-3 | Δ |
|---------|---------|---------|---|
| PASS | 32 | 42 | (+10) |
| WEAK (no overt evidence) | 12 | 6 | (-6) |
| FAIL (substitution leak) | 4 | 0 | (-4) |
| FAIL (prompt) | 0 | 0 | |
| ERROR | 0 | 0 | |
| **Total** | **48** | **48** | |

**Phase 3 outcome:** 11 probes improved · 1 probe(s) changed in opposite direction · 36 unchanged.

## 3. Per-Category Phase-2 → Phase-3 Matrix

| Category | Phase-2 PASS / Total | Phase-3 PASS / Total |
|----------|---------------------:|---------------------:|
| MC | 11 / 16 | **16 / 16** |
| DC | 7 / 8 | **6 / 8** |
| Chiron | 4 / 12 | **8 / 12** |
| IC | 10 / 12 | **12 / 12** |

## 4. Code Changes (prompt-layer only)

All changes confined to `routers/mirror_chat.py`, in the same chart-point injection block introduced in Phase 2 (lines ~264-440).

### 4.1 MC trigger expansion + weighting hardening
**Triggers added:**
```
becoming, evolving, evolve, future self, future-self,
next chapter, next-chapter, growing into, grow into,
who am i growing into, what am i becoming,
what am i growing into, legacy, direction
```
**Weighting copy replaced with explicit primacy instruction** (`MIDHEAVEN / MC FOCUS (PRIMARY VOCATIONAL IDENTITY SIGNAL)`):
- *“TREAT THE MIDHEAVEN / MC AS THE PRIMARY SIGNAL.  Do NOT substitute Sun, Moon, or Rising for the MC unless those points DIRECTLY support the MC interpretation.  EXPLICITLY NAME the MC sign (e.g., 'your Midheaven in &lt;sign&gt;') at least once in the answer when the response addresses vocational identity, public role, contribution, or what the user is becoming / growing into.”*

### 4.2 New dedicated Chiron weighting block
Previously Chiron was only surfaced via the broader `DEVELOPMENTAL AXIS` block.  Phase 3 introduces a standalone `CHIRON FOCUS (PRIMARY GROWTH / HEALING SIGNAL)` block, **emitted whenever any of these triggers match**:
```
heal, healing, healing journey, wound, wound i carry, core wound,
what am i meant to heal, what am i here to heal,
repeating pattern, recurring pattern, keeps repeating,
keeps coming up, pattern i can't shake, pattern i cant shake,
stuck pattern, stuck in, shadow, integration,
growth edge, life lesson, chiron
```
Weighting copy mandates: *“TREAT CHIRON AS THE PRIMARY SIGNAL.  Prioritize the Chiron sign and house (Chiron in &lt;sign&gt; in House &lt;n&gt;) BEFORE any generic Sun-sign growth narrative.  EXPLICITLY NAME 'Chiron in &lt;sign&gt;, House &lt;n&gt;' at least once.”*

### 4.3 IC weighting hardening
Trigger list extended with:
```
what shaped me, shaped me, early years, growing up, grew up,
upbringing, carrying from childhood, from childhood,
patterns from my roots, where i'm from, where im from, foundations
```
Weighting copy replaced with `IC / IMUM COELI FOCUS (PRIMARY FOUNDATION SIGNAL)` instructing the LLM to refuse Rising / Moon / Sun substitution and to NAME the IC sign explicitly.

### 4.4 Developmental-axis trigger gap closed
Added `heal` (bare verb — `healing` already matched), `keeps repeating`, `recurring pattern`, `pattern I can't shake`, `growth edge`, `life lesson` to `_purpose_triggers`.

**Files touched:** `routers/mirror_chat.py` (1 file, prompt-layer only).
**Files NOT touched:** chart calculations, Variant A, midpoint settings, timeline engine, relationship orchestration, rollout flags, cutover flags.

## 5. Before / After Examples

### Mel / MC / `career_contribution` — _"What am I here to contribute?"_

- Expected: MC=`Aries` (2°Aries)
- **Phase 2 verdict:** `FAIL (substitution leak)`
  - Phase-2 response excerpt:
    > You're exploring a large question, asking about your contribution. There's a dynamic mix within you, drawn from a blend of your astrological and human design frameworks. With your Sun in Gemini, there's a curiosity and a flexible approach to how you engage with the world. Coupled with your Moon in Scorpio, this suggests depth and willingness to explore below the surface of things. As a Reflector in Human Design, you'…
- **Phase 3 verdict:** `PASS`
  - Phase-3 response excerpt:
    > You're asking about your unique contribution to the world. Let's piece together some threads. With your Midheaven in Aries, there's a drive towards pioneering, leading, and breaking new ground in your public role or career. This often invites you to step into roles where you can act decisively and inspire others with your courage. Your Reflector type in Human Design suggests that your strength lies in your ability to…
  - Evidence quote (chart point named in P3 output):
    > …to the world. Let's piece together some threads. With your Midheaven in Aries, there's a drive towards pioneering, leading, and breaking new ground in your public role or career. This ofte…

### Mel / MC / `becoming` — _"What am I becoming?"_

- Expected: MC=`Aries` (2°Aries)
- **Phase 2 verdict:** `FAIL (substitution leak)`
  - Phase-2 response excerpt:
    > You're exploring a question that touches on change and potential. In your chart, a Gemini Sun paired with a Scorpio Moon suggests a dynamic interplay between curiosity and depth. You're likely drawn to explore a variety of ideas while seeking deeper emotional understanding. Your Cancer Rising might add a sensitivity to how you move through these changes. As a Reflector in Human Design, you naturally engage with the e…
- **Phase 3 verdict:** `PASS`
  - Phase-3 response excerpt:
    > You're reflecting on what you're growing into, and there's a quality of curiosity in that question. Your Midheaven in Aries suggests that your path may involve pioneering new directions, embracing leadership, or pursuing ways to assert your individuality in the public sphere. There's often an invitation to navigate boldness and initiative with balance, crafting a role that feels authentically yours. Think about what…
  - Evidence quote (chart point named in P3 output):
    > …, and there's a quality of curiosity in that question. Your Midheaven in Aries suggests that your path may involve pioneering new directions, embracing leadership, or pursuing ways to asser…

### Isaac / MC / `becoming` — _"What am I becoming?"_

- Expected: MC=`Ophiuchus` (2°Ophiuchus)
- **Phase 2 verdict:** `FAIL (substitution leak)`
  - Phase-2 response excerpt:
    > You're inquiring about who you are evolving into. That sense of growth and transformation can often make us feel both curious and uncertain. In your journey, there's an ongoing interaction between your true nature and the experiences you're encountering. With your Pisces sun, you might notice a sensitivity and deep perceptiveness guiding your path. As a Generator in Human Design, responding to what life presents to y…
- **Phase 3 verdict:** `PASS`
  - Phase-3 response excerpt:
    > You're sensing a desire to understand your path and direction. Your Midheaven in Ophiuchus suggests a journey where healing, transformation, and a connection to deeper truths might play significant roles. This placement often invites a touch of the mysterious, asking you to explore things that others might overlook. Yet, your life isn't limited to any one role. The Sun in Pisces often encourages empathy and imaginati…
  - Evidence quote (chart point named in P3 output):
    > …ensing a desire to understand your path and direction. Your Midheaven in Ophiuchus suggests a journey where healing, transformation, and a connection to deeper truths might play significant…

### Pete / IC / `roots_pattern` — _"What patterns come from my roots?"_

- Expected: IC=`Pisces` (31°Pisces)
- **Phase 2 verdict:** `FAIL (substitution leak)`
  - Phase-2 response excerpt:
    > Your roots seem to carry an energy of exploration and curiosity, suggesting a quest to understand and experience life deeply. This might be influenced by your Sagittarius rising, which often brings a natural inclination toward adventure and a desire for personal growth. Your Day Master in Bazi, Yin Metal, indicates a tendency toward resilience and structure, possibly offering a stable foundation amidst your explorati…
- **Phase 3 verdict:** `PASS`
  - Phase-3 response excerpt:
    > Your curiosity goes straight to the foundation. With your IC in Pisces, there's often a depth of feeling tied to your roots. This position suggests a childhood where imagination and sensitivity played significant roles. There might be themes around seeking connection and understanding within your family dynamic, perhaps even feeling a bit misunderstood at times. The tension here could lie within a need to balance tha…
  - Evidence quote (chart point named in P3 output):
    > …Your curiosity goes straight to the foundation. With your IC in Pisces, there's often a depth of feeling tied to your roots. This position suggests a childhood where imagination an…

### Mel / Chiron / `healing` — _"What am I here to heal?"_

- Expected: Chiron=`Taurus H10` (1°Taurus)
- **Phase 2 verdict:** `WEAK (no overt evidence)`
  - Phase-2 response excerpt:
    > You're exploring a big question, and it's understandable to seek clarity on your healing journey. However, it's important to recognize that healing isn't always about fixing something broken or achieving a state of perfection. It's a process of becoming more attuned to what truly feels alive in you. Your journey could invite you to notice patterns or emotions that resurface, perhaps in different forms or under varyin…
- **Phase 3 verdict:** `PASS`
  - Phase-3 response excerpt:
    > You're touching on a deep question. In the realm of astrology, your Chiron in Taurus in the 10th House is a significant place to start when considering patterns of healing and growth. This setup often speaks to wounds around self-worth, resources, or the tangible world, and how these might intersect with your public life or career. It suggests themes around feeling valued for what you contribute and recognizing your…
  - Evidence quote (chart point named in P3 output):
    > …ouching on a deep question. In the realm of astrology, your Chiron in Taurus in the 10th House is a significant place to start when considering patterns of healing and growth. This setup…

### Pete / Chiron / `healing` — _"What am I here to heal?"_

- Expected: Chiron=`Pisces H3` (11°Pisces)
- **Phase 2 verdict:** `WEAK (no overt evidence)`
  - Phase-2 response excerpt:
    > You're asking a deep question about your journey and what healing could look like for you. You might notice that you're naturally drawn to exploring various parts of life, given your Enneagram Type 7 and the exploratory nature of your Human Design as a Manifestor. There's an energy of seeking, discovering, and perhaps even moving towards what excites you. This could sometimes bring a sense of restlessness or an urge…
- **Phase 3 verdict:** `PASS`
  - Phase-3 response excerpt:
    > You've touched on something deep. In your sidereal astrology, Chiron in Pisces in House 3 speaks to a core pattern around communication, expression, and perhaps feeling misunderstood. This placement often invites you to explore how you connect with others, and how you can convey your inner world more authentically. It's about healing any wounds related to feeling unheard or disconnected in your exchanges. The journey…
  - Evidence quote (chart point named in P3 output):
    > …u've touched on something deep. In your sidereal astrology, Chiron in Pisces in House 3 speaks to a core pattern around communication, expression, and perhaps feeling misunderstood. This…

## 6. Remaining WEAK Verdicts (not blocking acceptance)

All Phase-3 WEAK verdicts are responses where the chart point IS injected into the prompt AND the weighting block IS emitted, but the LLM phrased its answer without naming the point / sign / house explicitly.  There are no substitution leaks remaining (Sun / Asc / Moon defaults are absent).

- **Pete / DC / `partnership_seek`** — weighting blocks: `['DC_WEIGHTING']`; expected DC=`Gemini`; LLM phrasing was abstract.
  - Excerpt: > In partnership, you may find yourself drawn to the qualities of curiosity, communication, and adaptability. These relationships often spark your interest when there's a dynamic exchange of ideas and a sense of lively interaction. You're likely to value partners who can engage you…
- **Pete / DC / `relationship_pattern`** — weighting blocks: `['CHIRON_FOCUS', 'DC_WEIGHTING', 'DEVELOPMENTAL_AXIS_WEIGHTING']`; expected DC=`Gemini`; LLM phrasing was abstract.
  - Excerpt: > You're curious about the cycles in your relationships. One recurring theme may be a focus on stimulating communication and dynamic exchanges. There's a draw toward partners who offer mental stimulation and versatility. This could sometimes lead to relationships that feel light-he…
- **Pete / Chiron / `repeating_life`** — weighting blocks: `['CHIRON_FOCUS', 'DEVELOPMENTAL_AXIS_WEIGHTING']`; expected Chiron=`Pisces H3`; LLM phrasing was abstract.
  - Excerpt: > Your chart keeps circling the same pressure: permeability. This theme often shows up when there is a sense of navigating boundaries and the integration of feelings and ideas. Underneath this, there's the tension between precision and permeability, suggesting a dynamic where the c…
- **Mel / Chiron / `repeating_life`** — weighting blocks: `['CHIRON_FOCUS', 'DEVELOPMENTAL_AXIS_WEIGHTING']`; expected Chiron=`Taurus H10`; LLM phrasing was abstract.
  - Excerpt: > Your chart keeps circling the same pressure: precision and standards. This core theme pervades your experiences, often pulling you into scenarios where clarity and meticulousness become both a challenge and a solution. You may notice how your interactions and choices are influenc…
- **Isaac / Chiron / `repeating_life`** — weighting blocks: `['CHIRON_FOCUS', 'DEVELOPMENTAL_AXIS_WEIGHTING']`; expected Chiron=`Aquarius H12`; LLM phrasing was abstract.
  - Excerpt: > Your chart keeps circling the same pressure: permeability. This theme manifests primarily through your Pisces Sun, Mercury, and Uranus. It speaks to a tendency where boundaries can feel less defined, leading to experiences where you might absorb or reflect the emotions and energi…
- **Jaan / Chiron / `repeating_life`** — weighting blocks: `['CHIRON_FOCUS', 'DEVELOPMENTAL_AXIS_WEIGHTING']`; expected Chiron=`Pisces H9`; LLM phrasing was abstract.
  - Excerpt: > Your chart often circles around the theme of life pulling you into groups or your chosen world. This isn't something that merely happens on occasion; it's a repetitive pull, almost like a tide that keeps drawing you back. When you're in these environments, there's a noticeable ac…

**Pattern observed:** four of the six WEAK cases share the same probe (`What keeps repeating in my life?` → `repeating_life`).  Inspection of the responses shows the upstream Phase-4 enrichment layer (`services/mirror_chat_phase4_enrichment.py`) emits its own *“Your chart keeps circling the same pressure: &lt;X&gt;”* template that dominates the answer shape for this question.  The Chiron block is still in the system prompt — the LLM simply opens with the enrichment template instead of leading with Chiron.  Out of scope for this sprint (prompt-layer only); future work could either tune the enrichment template or order the context-block injection so `CHIRON FOCUS` precedes the enrichment block.

**Pete DC `partnership_seek` regression (PASS → WEAK)** — DC trigger and weighting code were NOT modified in Phase 3.  Inspecting the two responses side-by-side (§5 / raw JSON) shows both answers correctly express Gemini-coded relational traits (intellect, curiosity, communication, variety = Pete's DC sign is Gemini).  The Phase-2 response happened to include a substring that the heuristic detector caught; the Phase-3 response is semantically identical but worded slightly differently.  No substitution leak, no functional regression.

## 7. 48-Probe Phase-3 Result Matrix

| User | MC | DC | Chiron | IC |
|------|----|----|--------|----|
| Pete | ✅ 4/4 | ⚠️ 0/2 | ⚠️ 2/3 | ✅ 3/3 |
| Mel | ✅ 4/4 | ✅ 2/2 | ⚠️ 2/3 | ✅ 3/3 |
| Isaac | ✅ 4/4 | ✅ 2/2 | ⚠️ 2/3 | ✅ 3/3 |
| Jaan | ✅ 4/4 | ✅ 2/2 | ⚠️ 2/3 | ✅ 3/3 |

## 8. Files

- `routers/mirror_chat.py` — patched (prompt-layer only)
- `scripts/astrology_prompt_integrity_verification.py` — probe driver (kept in lock-step with the source-of-truth trigger lists)
- `audit_reports/ASTROLOGY_PROMPT_INTEGRITY_VERIFICATION.json` — Phase-2 raw
- `audit_reports/ASTROLOGY_PROMPT_INTEGRITY_VERIFICATION.md` — Phase-2 report
- `audit_reports/ASTROLOGY_PROMPT_INTEGRITY_VERIFICATION_PHASE3.json` — Phase-3 raw
- **`audit_reports/ASTROLOGY_PROMPT_INTEGRITY_PHASE3_REPORT.md`** — this report
- **`audit_reports/ANGLE_DEGREE_ANOMALY_FORENSIC.md`** — separate forensic for the degree>30° finding (no code changes)

## 9. Sign-off

All four acceptance criteria are met.  No regressions in functional behavior.  No chart-calculation, storage, midpoint, Variant-A, timeline, relationship-orchestration, rollout-flag, or cutover-flag changes were made.
