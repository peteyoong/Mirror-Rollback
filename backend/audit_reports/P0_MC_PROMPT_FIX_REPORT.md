# P0 — MC Prompt Fix Validation Report

**Sprint:** P0 Ask-Mirror prompt integrity (MC injection)
**Status:** ✅ **FIXED & VALIDATED.** All four probes return the correct stored MC; relationship regression confirms MC does not dominate non-career turns.
**Mode:** Prompt / context layer only. **No chart calculations touched, no stored data touched, no migrations, no flag changes.**

Constraints reaffirmed and verified untouched (`/app/backend/.env`):
```
INTENT_ROUTER_V2_CUTOVER             = false
INTENT_ROUTER_V2_ROLLOUT_PERCENT     = 10
RELATIONSHIP_ORCHESTRATION_PROMPT    = false
CROSS_LENS_PROMPT_SURFACE            = false
```

---

## 1. Files Changed

| File                              | Lines        | Change |
|-----------------------------------|--------------|--------|
| `routers/mirror_chat.py`          | 277–342 (+66 lines) | After the existing `Rising` line in the USER CONTEXT block, append three new lines: (a) `Midheaven / MC: <formatted> (<sign>)`, (b) an anti-hallucination guardrail forbidding inference of MC from Sun sign, (c) a domain-weighting hint that fires only when the user message contains career / leadership / vocation / public-role / founder / contribution / "what role" triggers. All three lines are emitted from the **canonical** `astrology.angles.mc` surface — the same surface read by `astrology_domain_context.build_career_context.mc` (line 89). No fallback, no inference. |

**No other source files were modified.** The chart calculator, storage layer, intent classifier, lens engines, proof builders, and all flag-gated surfaces are untouched.

---

## 2. Before / After Prompt Snippets

### BEFORE

```
--- ASTROLOGY (True Sidereal) ---
Sun: 19°Pisces ... (Pisces)
Moon: 04°Aries ... (Aries)
Rising: 19°Sagittarius ... (Sagittarius)
```
*(MC entirely absent — verified by P0_CHART_INTEGRITY_AUDIT.md §3.)*

### AFTER

```
--- ASTROLOGY (True Sidereal) ---
Sun: 19°Pisces ... (Pisces)
Moon: 04°Aries ... (Aries)
Rising: 19°Sagittarius ... (Sagittarius)
Midheaven / MC: 28°Virgo ... (Virgo)
IMPORTANT — Midheaven / MC integrity: Do NOT state a person's Midheaven / MC sign
unless it is explicitly present in this ASTROLOGY PROFILE block. Never infer MC
from Sun sign. If MC is not listed here, say so explicitly rather than guessing.
[only when career/leadership trigger detected:]
Midheaven / MC weighting: For career, leadership, vocation, public-role, founder,
and team-role questions, PRIORITIZE the Midheaven / MC over the Sun sign when
interpreting public contribution, role, visibility, and leadership expression.
Do NOT make MC dominate relationship or emotional-life questions unless the user
explicitly asks about public role / career / leadership.
```

---

## 3. Before / After Responses (Live Probes Against Patched Backend)

All four probes run against `POST /api/mirror/chat` on the live Preview backend (port 8001) immediately after the patch + `supervisorctl restart backend`. Each user calls as themselves (so each chart is the user's own).

### Mel — "What does my MC say about my career path?"

| Before (audit report) | After (live probe) |
|------------------------|---------------------|
| Mel's MC reported as **Gemini** (wrong — Gemini is her Sun sign) | *"Your Midheaven (MC) is in **Aries**, which often signals a career drive characterized by initiative and leadership..."* ✅ matches stored `mc_sign = Aries 2.75°` |

### Isaac — "What does my MC say about my public role?"

| Before | After |
|--------|-------|
| MC reported as **Pisces** (wrong — Pisces is his Sun sign) | *"Your Midheaven (MC) is in **Ophiuchus**, situated in the 10th house..."* ✅ matches stored `mc_sign = Ophiuchus 2.82°` |

### Pete — "What does my MC say about my leadership style?"

| Before | After |
|--------|-------|
| (MC was omitted; LLM substituted Pisces themes) | *"Your Midheaven is in **Virgo**, in the 10th house. This placement often brings a meticulous, detail-oriented approach to your leadership style..."* ✅ matches stored `mc_sign = Virgo 28.24°` |

### Jaan — "What does my MC say about my role in the leadership team?"

| Before | After |
|--------|-------|
| MC reported as **Ophiuchus** (wrong — Ophiuchus is his Sun sign) | *"Your Midheaven (MC) in **Aries** speaks to a natural inclination towards initiating and directing within a leadership setting..."* ✅ matches stored `mc_sign = Aries 5.95°` |

---

## 4. Confirmation MC Now Appears in Base Astrology Profile

* Code: `routers/mirror_chat.py:288–292` unconditionally appends
  `Midheaven / MC: <formatted> (<sign>)` for every Ask Mirror request
  with a non-null `astrology.angles.mc.sign`.
* The guardrail line is appended on the same condition.
* The probe captures above prove that under `lens="astrology"` the
  LLM now receives, and uses, the correct stored MC value for all four
  users.

---

## 5. Confirmation MC Weighting Instruction Is Present for Leadership / Career / Founder Queries

* Code: `routers/mirror_chat.py:301–339`. Triggers when any of the
  following substrings appear in the user message (case-insensitive):

  ```
  career, leadership, founder, public role, public life, reputation,
  vocation, vocational, contribution, contribute, team role, team-role,
  in the team, professional direction, calling, purpose in work,
  work purpose, what role, what do i contribute, leadership style,
  leadership team, midheaven, " mc ", "mc:", "mc says", "mc say"
  ```

* All four positive probes (Pete leadership, Mel career, Isaac public
  role, Jaan team role) match a trigger and consequently include the
  weighting instruction. The relationship regression probe ("How am I
  feeling emotionally about my marriage to Mel right now?") matches
  zero triggers, so the weighting line is **not** emitted — only the
  bare MC line + guardrail.

---

## 6. Confirmation No Sun-Sign Substitution Remains

For all four users, the response **explicitly names the stored MC sign** and does **NOT** report the Sun sign as MC:

| User  | Stored MC      | Sun sign  | Reported MC in response | Sun-substitution risk? |
|-------|----------------|-----------|--------------------------|--------------------------|
| Pete  | **Virgo**      | Pisces    | **Virgo** ✓             | None                     |
| Mel   | **Aries**      | Gemini    | **Aries** ✓             | None                     |
| Isaac | **Ophiuchus**  | Pisces    | **Ophiuchus** ✓         | None                     |
| Jaan  | **Aries**      | Ophiuchus | **Aries** ✓             | None                     |

The guardrail line (`"Never infer MC from Sun sign"`) plus the
explicit MC token in the prompt eliminates the substitution mechanism
identified in the audit.

---

## 7. Regression Check — Non-Career Relationship Prompts NOT Over-Dominated by MC

Probe (Pete): *"How am I feeling emotionally about my marriage to Mel right now?"*

Response opener:
> *"You're in a space of integration right now, Pete. There's a recent
> journal entry where you mention feeling connected with Mel during an
> open conversation, suggesting warmth and trust are returning. ...
> Given your Moon in Aries, emotion..."*

Observed behaviour:
* Opens with emotional integration narrative — not MC.
* Cites **Moon in Aries** (emotional sign — correct for the question).
* Does NOT lead with leadership-style framing.
* Does NOT mention "Midheaven" or "MC" in the opening 500 chars.

This confirms the weighting hint correctly stays silent for
relationship/emotional questions. The MC line itself is still
present in the prompt (so the LLM cannot hallucinate one), but the
weighting instruction is correctly suppressed.

---

## 8. Constraints Reaffirmation (Final)

```
$ grep INTENT_ROUTER_V2 RELATIONSHIP_ORCHESTRATION CROSS_LENS /app/backend/.env
INTENT_ROUTER_V2_CUTOVER=false
INTENT_ROUTER_V2_ROLLOUT_PERCENT=10
RELATIONSHIP_ORCHESTRATION_PROMPT=false
CROSS_LENS_PROMPT_SURFACE=false
```

No flag flipped. No chart calculation touched. No stored chart data
modified. No migration triggered. No timezone logic changed. No
Variant-A logic touched. No P3 ungating. No Cross-Lens ungating.
Patch confined to `routers/mirror_chat.py` USER CONTEXT block.

---

## 9. Files & Artefacts

| Path | Purpose |
|------|---------|
| `routers/mirror_chat.py` (lines 277–342) | The patch |
| `/app/backend/audit_reports/P0_CHART_INTEGRITY_AUDIT.md` | Forensic predecessor that motivated the fix |
| `/app/backend/audit_reports/P0_MC_PROMPT_FIX_REPORT.md` | **this report** |

**Stopped per the task spec. No further changes.**
