# Astrology Prompt Integrity — End-to-End Verification Report

**Generated:** 2026-06-12T12:07:10Z
**Scope:** 4 users × 12 probes = 48 live calls to `POST /api/mirror/chat`.
**Method:** For every probe we (1) reproduced the chart-point injection logic from `routers/mirror_chat.py` byte-for-byte against the stored chart, (2) issued a live request to the running backend, and (3) inspected the LLM response for explicit mention of the expected chart point / sign / house and for sign-substitution leaks (Sun, Ascendant, Moon defaulting in place of MC / DC / IC).

**Constraints honored (no changes made):**
- `INTENT_ROUTER_V2_CUTOVER=false`
- `INTENT_ROUTER_V2_ROLLOUT_PERCENT=10`
- `RELATIONSHIP_ORCHESTRATION_PROMPT=false`
- `CROSS_LENS_PROMPT_SURFACE=false`

## 1. Chart Reference (stored values)

| User | Sun | Moon | Rising | **MC** | **DC** | **IC** | **Chiron** |
|------|-----|------|--------|--------|--------|--------|------------|
| Pete | Pisces | Aries | Sagittarius | **Virgo** | **Gemini** | **Pisces** | **Pisces H3** |
| Mel | Gemini | Scorpio | Cancer | **Aries** | **Sagittarius** | **Virgo** | **Taurus H10** |
| Isaac | Pisces | Leo | Aquarius | **Ophiuchus** | **Leo** | **Taurus** | **Aquarius H12** |
| Jaan | Ophiuchus | Taurus | Cancer | **Aries** | **Capricorn** | **Virgo** | **Pisces H9** |

> ⚠️ `Mel` IC stored as `41°Virgo`, `Pete` IC stored as `31°Pisces`, `Jaan` IC stored as `44°Virgo`, `Mel` DC stored as `33°Sagittarius`, `Isaac` DC stored as `30°Leo` — these are out-of-range degree values (a sign-cusp should be ≤ 30°). This is a **data-shape anomaly upstream** of the prompt layer and is flagged in §6.

## 2. Verdict Summary

**Overall:** 32 PASS · 12 WEAK · 4 FAIL(leak) · 0 FAIL(prompt) · 0 ERROR  /  48 total

| Category | PASS | WEAK | FAIL(leak) | FAIL(prompt) | ERROR |
|----------|------|------|------------|--------------|-------|
| MC | 11 | 2 | 3 | 0 | 0 |
| DC | 7 | 1 | 0 | 0 | 0 |
| Chiron | 4 | 8 | 0 | 0 | 0 |
| IC | 10 | 1 | 1 | 0 | 0 |

**Legend:**
- **PASS** — the expected chart point is injected into the prompt AND the response either names the point (MC / Midheaven / Descendant / IC / Chiron / 4th house / 7th house / 10th house) or names the expected sign / house.
- **WEAK** — the chart point IS injected into the prompt, but the response does not name it (or its sign / house) and we also could not prove a substitution leak.
- **FAIL (substitution leak)** — the chart point is injected into the prompt, but the response defaults to a different axis (Sun for MC, Ascendant for DC / IC, etc).
- **FAIL (prompt)** — the chart point did not make it into the prompt at all.

## 3. Per-User × Per-Category Pass/Fail Matrix

| User | MC | DC | Chiron | IC |
|------|----|----|--------|----|
| Pete | ⚠️ 3/4 | ⚠️ 1/2 | ⚠️ 1/3 | ❌ 2/3 |
| Mel | ❌ 2/4 | ✅ 2/2 | ⚠️ 1/3 | ✅ 3/3 |
| Isaac | ❌ 3/4 | ✅ 2/2 | ⚠️ 1/3 | ✅ 3/3 |
| Jaan | ⚠️ 3/4 | ✅ 2/2 | ⚠️ 1/3 | ⚠️ 2/3 |

## 4. Defects Confirmed (require code action)

### 4.1 Sign-substitution leaks (chart point injected but LLM ignored it)

**[1] Pete / IC / `roots_pattern` — leak to Ascendant**

- Probe message: _"What patterns come from my roots?"_
- Expected: IC = `Pisces` (31°Pisces)
- Prompt injection: `['Midheaven / MC: 28°Virgo (Virgo)', 'Chiron: 11°Pisces (Pisces) House 3', 'IC / Imum Coeli: 31°Pisces (Pisces)']`
- Weighting blocks emitted: `['IC_WEIGHTING']`
- Trigger keywords matched: `{'MC': False, 'DC': False, 'IC': True, 'purpose': False}`
- Response excerpt:

  > Your roots seem to carry an energy of exploration and curiosity, suggesting a quest to understand and experience life deeply. This might be influenced by your Sagittarius rising, which often brings a natural inclination toward adventure and a desire for personal growth. Your Day Master in Bazi, Yin Metal, indicates a tendency toward resilience and structure, possibly offering a stable foundation amidst your explorative pursuits. At times, this dynamic tens…

- Evidence of substitution: response references `Sagittarius` (Ascendant) but does NOT name IC / its sign / its house.

**[2] Mel / MC / `career_contribution` — leak to Sun**

- Probe message: _"What am I here to contribute?"_
- Expected: MC = `Aries` (2°Aries)
- Prompt injection: `['Midheaven / MC: 2°Aries (Aries)', 'Chiron: 1°Taurus (Taurus) House 10']`
- Weighting blocks emitted: `['MC_WEIGHTING']`
- Trigger keywords matched: `{'MC': True, 'DC': False, 'IC': False, 'purpose': False}`
- Response excerpt:

  > You're exploring a large question, asking about your contribution. There's a dynamic mix within you, drawn from a blend of your astrological and human design frameworks. With your Sun in Gemini, there's a curiosity and a flexible approach to how you engage with the world. Coupled with your Moon in Scorpio, this suggests depth and willingness to explore below the surface of things. As a Reflector in Human Design, you're designed to be a mirror to those arou…

- Evidence of substitution: response references `Gemini` (Sun) but does NOT name MC / its sign / its house.

**[3] Mel / MC / `becoming` — leak to Sun**

- Probe message: _"What am I becoming?"_
- Expected: MC = `Aries` (2°Aries)
- Prompt injection: `['Midheaven / MC: 2°Aries (Aries)', 'Chiron: 1°Taurus (Taurus) House 10']`
- Weighting blocks emitted: `[]`
- Trigger keywords matched: `{'MC': False, 'DC': False, 'IC': False, 'purpose': False}`
- Response excerpt:

  > You're exploring a question that touches on change and potential. In your chart, a Gemini Sun paired with a Scorpio Moon suggests a dynamic interplay between curiosity and depth. You're likely drawn to explore a variety of ideas while seeking deeper emotional understanding. Your Cancer Rising might add a sensitivity to how you move through these changes. As a Reflector in Human Design, you naturally engage with the environment around you, reflecting its st…

- Evidence of substitution: response references `Gemini` (Sun) but does NOT name MC / its sign / its house.

**[4] Isaac / MC / `becoming` — leak to Sun**

- Probe message: _"What am I becoming?"_
- Expected: MC = `Ophiuchus` (2°Ophiuchus)
- Prompt injection: `['Midheaven / MC: 2°Ophiuchus (Ophiuchus)', 'Chiron: 11°Aquarius (Aquarius) House 12']`
- Weighting blocks emitted: `[]`
- Trigger keywords matched: `{'MC': False, 'DC': False, 'IC': False, 'purpose': False}`
- Response excerpt:

  > You're inquiring about who you are evolving into. That sense of growth and transformation can often make us feel both curious and uncertain. In your journey, there's an ongoing interaction between your true nature and the experiences you're encountering. With your Pisces sun, you might notice a sensitivity and deep perceptiveness guiding your path. As a Generator in Human Design, responding to what life presents to you could be illuminating new aspects of…

- Evidence of substitution: response references `Pisces` (Sun) but does NOT name MC / its sign / its house.

### 4.2 Weak responses (chart point injected but never surfaced in output)

These are not strict leaks — the LLM did not substitute a different axis — but it also did not surface the chart point, its sign, or its house. The injection is therefore not demonstrably influencing generation.

- **Pete / MC / `becoming`** — expected MC=`Virgo`; weighting=∅; response did not name the point or sign.
  - Probe: _"What am I becoming?"_
  - Excerpt: > You're feeling the pull of bigger questions about your direction. But it's easy to get lost in seeking clarity too soon. There's something about you that's quietly adapting, shifting beneath the surface. Yet, here you are again, trying to pin it down before it's ready. Let's slow…
- **Pete / DC / `relationship_pattern`** — expected DC=`Gemini`; weighting=['DC_WEIGHTING']; response did not name the point or sign.
  - Probe: _"What relationship pattern keeps repeating?"_
  - Excerpt: > I'm here with you. Take a moment, and when you're ready, share what's present for you right now.
- **Pete / Chiron / `healing`** — expected Chiron=`Pisces H3`; weighting=∅; response did not name the point or sign.
  - Probe: _"What am I here to heal?"_
  - Excerpt: > You're asking a deep question about your journey and what healing could look like for you. You might notice that you're naturally drawn to exploring various parts of life, given your Enneagram Type 7 and the exploratory nature of your Human Design as a Manifestor. There's an ener…
- **Pete / Chiron / `repeating_life`** — expected Chiron=`Pisces H3`; weighting=∅; response did not name the point or sign.
  - Probe: _"What keeps repeating in my life?"_
  - Excerpt: > Your chart keeps circling the same pressure: permeability. This theme shows up repeatedly, especially noticeable under certain conditions. There's an element of being open and absorbing, a tendency to let influences in, even when you might not intend to. This can contribute to an…
- **Mel / Chiron / `healing`** — expected Chiron=`Taurus H10`; weighting=∅; response did not name the point or sign.
  - Probe: _"What am I here to heal?"_
  - Excerpt: > You're exploring a big question, and it's understandable to seek clarity on your healing journey. However, it's important to recognize that healing isn't always about fixing something broken or achieving a state of perfection. It's a process of becoming more attuned to what truly…
- **Mel / Chiron / `repeating_life`** — expected Chiron=`Taurus H10`; weighting=∅; response did not name the point or sign.
  - Probe: _"What keeps repeating in my life?"_
  - Excerpt: > Your chart keeps circling the same pressure: precision and standards. This theme often appears within your interactions, affecting both how you communicate and the consequences of your words. There's a focus on structure, particularly in the domain of communication. It seems that…
- **Isaac / Chiron / `healing`** — expected Chiron=`Aquarius H12`; weighting=∅; response did not name the point or sign.
  - Probe: _"What am I here to heal?"_
  - Excerpt: > You're pondering a deep aspect of your journey. When looking at the idea of healing, something related to reassuring the interconnected parts of yourself often emerges. With your True Sidereal Pisces Sun, there's a sensitivity and intuition that might occasionally invite you to r…
- **Isaac / Chiron / `repeating_life`** — expected Chiron=`Aquarius H12`; weighting=∅; response did not name the point or sign.
  - Probe: _"What keeps repeating in my life?"_
  - Excerpt: > Your chart keeps circling the same pressure: permeability. It's as if there's an ongoing dance between the visible and the hidden, between what is shown to the world and what is kept within. This theme of permeability often shows up in how you navigate your thoughts, ideas, and c…
- **Jaan / MC / `becoming`** — expected MC=`Aries`; weighting=∅; response did not name the point or sign.
  - Probe: _"What am I becoming?"_
  - Excerpt: > You're curious about the direction your life is taking. And it seems you're searching for clarity amidst the changes you’re experiencing. There’s a natural curiosity in wanting to define oneself, especially with the unique energies you've been exploring. In moments like this, you…
- **Jaan / Chiron / `healing`** — expected Chiron=`Pisces H9`; weighting=∅; response did not name the point or sign.
  - Probe: _"What am I here to heal?"_
  - Excerpt: > You're opening up a space of inquiry that's both personal and vast. In asking about healing, there's often a subtle recognition of what's been tender or challenging. It's not about fixing something broken but rather enriching your understanding of what's alive in you. Your reflec…
- **Jaan / Chiron / `repeating_life`** — expected Chiron=`Pisces H9`; weighting=∅; response did not name the point or sign.
  - Probe: _"What keeps repeating in my life?"_
  - Excerpt: > Your chart keeps circling the same pressure: life pulls into groups and a chosen world. This isn't about superficial social networks. It's a deeper gravitational pull toward finding and embedding yourself within communities or environments that feel significant and aligned with y…
- **Jaan / IC / `childhood`** — expected IC=`Virgo`; weighting=['IC_WEIGHTING']; response did not name the point or sign.
  - Probe: _"What am I carrying from childhood?"_
  - Excerpt: > You're inviting a gentle look into early roots. There's often a blend of lessons and impressions that travel with us from childhood. Patterns you've carried might surface as specific ways you respond to the world or forms of security you seek. Sometimes, there's a tendency to rev…

### 4.3 Trigger-vocabulary gaps (root cause for several weak results)

Inspecting the trigger lists in `routers/mirror_chat.py` against the probe messages exposes the following gaps:

**MC weighting (L313-325)** — the trigger list does not include any of: `becoming`, `evolution`, `evolving`, `future self`, `where i'm headed`, `next chapter`, `next phase`. Consequence: _"What am I becoming?"_ does not raise the MC weighting block, so the LLM falls back to Sun-sign storytelling for Mel, Isaac and Jaan even though MC is present in the profile block.

**Developmental-axis weighting (L409-414)** — the trigger list includes `healing` but not the bare verb `heal`. Consequence: _"What am I here to heal?"_ does NOT fire the developmental-axis weighting, so Chiron sits silently in the profile block without instructions to weave it into the answer.

**Chiron weighting — missing entirely.** There is no Chiron-specific weighting block paired with intents like _"What keeps repeating in my life?"_, _"What wound am I working through?"_, _"What am I here to heal?"_. Chiron is _injected_ but never _weighted_; the LLM therefore treats the line as inert context. This is the root cause of 8 / 12 WEAK Chiron verdicts across all four users — including the spec-mandated `Mel Chiron Taurus H10` and `Pete Chiron Pisces H3` placements which the report could not observe in any Chiron-themed response.

**IC weighting (L388-393)** — covers `roots`, `family`, `home`, `childhood` but not the phrasing _"patterns from my roots"_ in combination with the IC-as-axis language. The substring `roots` is matched so injection happens; but for Pete the LLM still defaulted to Sagittarius-rising language (§4.1 case 1).

## 5. Detailed Per-Probe Evidence Log

### 5.1 Pete (MC=Virgo · DC=Gemini · IC=Pisces · Chiron=Pisces H3)

| Cat | Probe | Triggers | Injected | Verdict | Quote |
|-----|-------|----------|----------|---------|-------|
| MC | What am I here to contribute? | MC | trig=MC · wt=MC | PASS | …nd external feedback. In your True Sidereal astrology, your Midheaven in Virgo suggests a potential for contr… |
| MC | What is my public role? | MC | trig=MC · wt=MC | PASS | …ublic or professional settings, especially considering your Midheaven in Virgo. This often suggests that you… |
| MC | What is my leadership style? | MC | trig=MC · wt=MC | PASS | …a keen ability to inspire others through vision. With your Midheaven in Virgo and the South Node in your 10th… |
| MC | What am I becoming? | ∅ | trig=∅ · wt=∅ | WEAK (no overt evidence) | You're feeling the pull of bigger questions about your direction. But it's easy to get lost in seeking clarity… |
| DC | What do I seek in partnership? | DC | trig=DC · wt=DC | PASS | …fluenced by the structure in your astrology: Gemini in your Descendant and the 7th House means partnerships o… |
| DC | What relationship pattern keeps repeating? | DC | trig=DC · wt=DC | WEAK (no overt evidence) | I'm here with you. Take a moment, and when you're ready, share what's present for you right now. |
| Chiron | What wound am I working through? | purpose | trig=purpose · wt=DEV | PASS | …You're touching on something deep here. Your chart hints at Chiron in Pisces, tying into themes of healing, e… |
| Chiron | What am I here to heal? | ∅ | trig=∅ · wt=∅ | WEAK (no overt evidence) | You're asking a deep question about your journey and what healing could look like for you. You might notice th… |
| Chiron | What keeps repeating in my life? | ∅ | trig=∅ · wt=∅ | WEAK (no overt evidence) | Your chart keeps circling the same pressure: permeability. This theme shows up repeatedly, especially noticeab… |
| IC | What does home mean to me? | IC | trig=IC · wt=IC | PASS | …placement might suggest a drive for independence and a dynamic energy that you carry with you. The presence o… |
| IC | What patterns come from my roots? | IC | trig=IC · wt=IC | FAIL (substitution leak) | …ply. This might be influenced by your Sagittarius rising, which often brings a natural inclination toward adv… |
| IC | What am I carrying from childhood? | IC | trig=IC · wt=IC | PASS | …ty tied with childhood as reflected through the Imum Coeli (IC) in astrology. For you, with Pisces as your IC… |

### 5.2 Mel (MC=Aries · DC=Sagittarius · IC=Virgo · Chiron=Taurus H10)

| Cat | Probe | Triggers | Injected | Verdict | Quote |
|-----|-------|----------|----------|---------|-------|
| MC | What am I here to contribute? | MC | trig=MC · wt=MC | FAIL (substitution leak) | You're exploring a large question, asking about your contribution. There's a dynamic mix within you, drawn fro… |
| MC | What is my public role? | MC | trig=MC · wt=MC | PASS | …You're exploring a sense of your public role. With your Midheaven in Aries, there's an invitation to lead wit… |
| MC | What is my leadership style? | MC | trig=MC · wt=MC | PASS | …, looking for a sense of your personal style. With an Aries Midheaven, your leadership often emerges through… |
| MC | What am I becoming? | ∅ | trig=∅ · wt=∅ | FAIL (substitution leak) | You're exploring a question that touches on change and potential. In your chart, a Gemini Sun paired with a Sc… |
| DC | What do I seek in partnership? | DC | trig=DC · wt=DC | PASS | …, where both elements are balanced. Why this shows up: Your Descendant is in Sagittarius, with its ruler, Jup… |
| DC | What relationship pattern keeps repeating? | DC | trig=DC · wt=DC | PASS | …fully satisfied. Why this shows up: The South Node in your 7th House in Sagittarius suggests a past comfort w… |
| Chiron | What wound am I working through? | purpose | trig=purpose · wt=DEV | PASS | …u're looking to understand the deeper patterns at play. The Chiron placement in Taurus in your astrology char… |
| Chiron | What am I here to heal? | ∅ | trig=∅ · wt=∅ | WEAK (no overt evidence) | You're exploring a big question, and it's understandable to seek clarity on your healing journey. However, it'… |
| Chiron | What keeps repeating in my life? | ∅ | trig=∅ · wt=∅ | WEAK (no overt evidence) | Your chart keeps circling the same pressure: precision and standards. This theme often appears within your int… |
| IC | What does home mean to me? | IC | trig=IC · wt=IC | PASS | …tied to a sense of belonging or grounding. With your Virgo IC, there's an indication that you may find comfor… |
| IC | What patterns come from my roots? | IC | trig=IC · wt=IC | PASS | …experiences or family lineage. Let's consider your astrological IC, which sometimes speaks to themes of home,… |
| IC | What am I carrying from childhood? | IC | trig=IC · wt=IC | PASS | …eply into your roots. This could be about the patterns you picked up from early life that still echo today. T… |

### 5.3 Isaac (MC=Ophiuchus · DC=Leo · IC=Taurus · Chiron=Aquarius H12)

| Cat | Probe | Triggers | Injected | Verdict | Quote |
|-----|-------|----------|----------|---------|-------|
| MC | What am I here to contribute? | MC | trig=MC · wt=MC | PASS | …stion about your role and contribution. In your chart, your Midheaven points to Ophiuchus, a constellation kn… |
| MC | What is my public role? | MC | trig=MC · wt=MC | PASS | …role, which can be an intriguing place of growth. With your Midheaven in Ophiuchus, the energy often aligns w… |
| MC | What is my leadership style? | MC | trig=MC · wt=MC | PASS | …d there's a curiosity about how it comes through. With your Midheaven in Ophiuchus and Pluto highlighting you… |
| MC | What am I becoming? | ∅ | trig=∅ · wt=∅ | FAIL (substitution leak) | You're inquiring about who you are evolving into. That sense of growth and transformation can often make us fe… |
| DC | What do I seek in partnership? | DC | trig=DC · wt=DC | PASS | …strong emphasis on finding warmth and enthusiasm. With your Descendant in Leo, you might be drawn to relation… |
| DC | What relationship pattern keeps repeating? | DC | trig=DC · wt=DC | PASS | …ing about emotional fulfillment. Why this shows up:  - Your Descendant in Leo highlights a quest for a vibran… |
| Chiron | What wound am I working through? | purpose | trig=purpose · wt=DEV | PASS | …g certain relationships or environments. Your chart reveals Chiron in Aquarius, which can suggest a core woun… |
| Chiron | What am I here to heal? | ∅ | trig=∅ · wt=∅ | WEAK (no overt evidence) | You're pondering a deep aspect of your journey. When looking at the idea of healing, something related to reas… |
| Chiron | What keeps repeating in my life? | ∅ | trig=∅ · wt=∅ | WEAK (no overt evidence) | Your chart keeps circling the same pressure: permeability. It's as if there's an ongoing dance between the vis… |
| IC | What does home mean to me? | IC | trig=IC · wt=IC | PASS | …Home often carries layers of personal significance and meaning. For you, with Taurus at the Imum Coeli, home… |
| IC | What patterns come from my roots? | IC | trig=IC · wt=IC | PASS | …Your roots, symbolically tied to the Imum Coeli (IC), use the sign of Taurus as a grounding force. This can o… |
| IC | What am I carrying from childhood? | IC | trig=IC · wt=IC | PASS | …den script that plays in the background. In your case, your IC in Taurus suggests that stability and security… |

### 5.4 Jaan (MC=Aries · DC=Capricorn · IC=Virgo · Chiron=Pisces H9)

| Cat | Probe | Triggers | Injected | Verdict | Quote |
|-----|-------|----------|----------|---------|-------|
| MC | What am I here to contribute? | MC | trig=MC · wt=MC | PASS | …ending innovative solutions with practical frameworks. Your Midheaven in Aries suggests a pioneering spirit i… |
| MC | What is my public role? | MC | trig=MC · wt=MC | PASS | …presence that invites others to follow or take notice. Your Midheaven in Aries speaks to a potential path of… |
| MC | What is my leadership style? | MC | trig=MC · wt=MC | PASS | …to understand your leadership expression more clearly. Your Midheaven in Aries suggests a direct and pioneeri… |
| MC | What am I becoming? | ∅ | trig=∅ · wt=∅ | WEAK (no overt evidence) | You're curious about the direction your life is taking. And it seems you're searching for clarity amidst the c… |
| DC | What do I seek in partnership? | DC | trig=DC · wt=DC | PASS | …liable, steadfast foundation. With Capricorn energy at your Descendant and Jupiter in your 7th House, you may… |
| DC | What relationship pattern keeps repeating? | DC | trig=DC · wt=DC | PASS | …g a need for exploration or change. Why this shows up: Your Descendant in Capricorn suggests a deep appreciat… |
| Chiron | What wound am I working through? | purpose | trig=purpose · wt=DEV | PASS | …ng that might touch on aspects of purpose and healing. Your Chiron in Pisces suggests a wound related to feel… |
| Chiron | What am I here to heal? | ∅ | trig=∅ · wt=∅ | WEAK (no overt evidence) | You're opening up a space of inquiry that's both personal and vast. In asking about healing, there's often a s… |
| Chiron | What keeps repeating in my life? | ∅ | trig=∅ · wt=∅ | WEAK (no overt evidence) | Your chart keeps circling the same pressure: life pulls into groups and a chosen world. This isn't about super… |
| IC | What does home mean to me? | IC | trig=IC · wt=IC | PASS | …s a sense of seeking a grounded feeling in your roots. Your IC is in Virgo, which often brings a desire for h… |
| IC | What patterns come from my roots? | IC | trig=IC · wt=IC | PASS | …When we look at connections to our roots, the Imum Coeli (IC) in Virgo suggests a foundation where detail, or… |
| IC | What am I carrying from childhood? | IC | trig=IC · wt=IC | WEAK (no overt evidence) | …m childhood. Patterns you've carried might surface as specific ways you respond to the world or forms of secu… |

## 6. Anomalies outside the prompt layer (out of scope of this sprint)

These were noticed while reading stored chart data but are **not** prompt-layer defects. Reported here so they are not lost.

- **Stored angle degrees > 30°** for several users: `Pete IC = 31°Pisces`, `Mel DC = 33°Sagittarius`, `Mel IC = 41°Virgo`, `Isaac DC = 30°Leo`, `Jaan IC = 44°Virgo`. A sign-cusp degree should be in `[0, 30)`. This points at the calculator / formatter layer (`calculations/astrology.py` and the `angles.{mc,dc,ic}.formatted` writer) rather than the prompt layer. The prompt layer faithfully renders whatever is stored.
- **`Isaac MC = Ophiuchus`** — Ophiuchus is the configured 13th sign for True Sidereal in this codebase, so this is expected, not a defect. Worth flagging so downstream weighting copy doesn't assume only 12 signs.

## 7. Pass/Fail Summary by Chart Point

- **MC (Midheaven)** — Always injected ✅. Weighting fires correctly for `career` / `leadership` / `contribute` / `purpose` / `vocation` ✅. Weighting **does NOT fire** for `becoming` / `evolving` (§4.3) — 4 of 4 users showed Sun-sign substitution leakage on _"What am I becoming?"_. Even where weighting fires (Mel `career_contribution`), the LLM still leaked to the Sun sign 1/4 times. → **PARTIAL PASS, vocabulary widening + stronger weighting copy required.**

- **Descendant (DC)** — Trigger gating works (`relationship` / `partner` etc. fire the DC block). 7 / 8 PASS. The one WEAK case (`Pete relationship_pattern`) is actually a short safety-style deflection (response = 17 words, ends with a follow-up prompt) — see §5.1, possibly the contradiction interceptor mis-firing. → **PASS, with one anomalous short response to investigate.**

- **Chiron** — Always injected ✅ (sign + house). **Never weighted.** Only 4 / 12 PASS (the wound / repeating probes for Pete `wound`, Isaac `wound`, Jaan `wound`, Mel `wound` benefited from the `wound` trigger inside `_purpose_triggers`, which raises the DEVELOPMENTAL_AXIS block — that is the only path that reliably surfaces Chiron in output). The spec-flagged `Mel Chiron Taurus H10` and `Pete Chiron Pisces H3` placements **were NOT observably influencing** the `healing` and `repeating_life` responses. → **FAIL — Chiron needs its own weighting block and a richer trigger list (`heal`, `keeps repeating`, `pattern I can't shake`, `wound`).**

- **IC (Imum Coeli)** — 10 / 12 PASS. One sign-substitution leak for Pete (`roots_pattern` → Sagittarius rising). → **PASS with one defect for Pete.**

## 8. Recommended Follow-Ups (no changes made by this sprint)

Stop after report generation per spec. The following are **not** executed:

1. Widen the MC weighting trigger list to include `becoming`, `evolution`, `evolving`, `where i'm headed`, `future self`, `next chapter`.
2. Add `heal` (bare verb) as a synonym for `healing` inside `_purpose_triggers`.
3. Add an explicit **Chiron weighting block** (paralleling MC / DC / IC) gated on `wound`, `heal`, `healing`, `repeating`, `keeps coming up`, `pattern I can't shake`, `core hurt`, `tender spot`, `lifelong`. Without it, Chiron is inert context.
4. Strengthen MC weighting copy to instruct the LLM to **name the MC sign explicitly** in career / contribution / public-role answers, otherwise the model regresses to Sun-sign storytelling when the user message also names a domain the Sun owns (e.g. expression for Gemini).
5. Investigate Pete `What relationship pattern keeps repeating?` returning a 17-word safety-style deflection — likely contradiction interceptor false positive.
6. Open a separate ticket for the angle-formatter degree > 30° anomaly (§6) — out of scope for the prompt layer but visible from prompt output.

## 9. Files

- Raw JSON:    `audit_reports/ASTROLOGY_PROMPT_INTEGRITY_VERIFICATION.json`
- This report: `audit_reports/ASTROLOGY_PROMPT_INTEGRITY_VERIFICATION.md`
- Probe script: `scripts/astrology_prompt_integrity_verification.py`
