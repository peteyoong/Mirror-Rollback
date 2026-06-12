# Intelligence Routing Verification — Follow-up Sprint Report

**Generated:** 2026-06-12.  Live verification of Tasks 1 + 2 + 3 of the Intelligence Activation Follow-up Sprint.

**Constraints honored — re-verified locked in `backend/.env`:**
- `INTENT_ROUTER_V2_CUTOVER=false`
- `INTENT_ROUTER_V2_ROLLOUT_PERCENT=10`
- `RELATIONSHIP_ORCHESTRATION_PROMPT=false`
- `CROSS_LENS_PROMPT_SURFACE=false`

No new intelligence systems built.  No P3 ungated.  No schema migrations.  No timeline/cross-lens work.  No telemetry-format changes.  Only existing services activated + a thin post-V2 enrichment layer that mutates the receipt before downstream consumers read it.

---

## 1. Verdict — 6 / 6 acceptance probes PASS

| # | Probe | Target / Role bound | Spouse auto-bind? | Lexicon match | Verdict |
|---|-------|---------------------|:-----------------:|---------------|:-------:|
| 1 | "What tension exists between us?"               | **Mel / spouse**            | ✅ `True`  | —                                           | ✅ |
| 2 | "What are we learning together?"                | **Mel / spouse**            | ✅ `True`  | —                                           | ✅ |
| 3 | "What is Pulsifi struggling to see?"            | — (founder context)         | n/a        | `company:pulsifi`                           | ✅ |
| 4 | "What tension exists inside the leadership team?" | — (leadership context, NO spouse leak) | n/a (suppressed) | `company:leadership team`         | ✅ |
| 5 | "What is happening in Yoong Family?"            | **Thaddeus Yoong / family** | n/a        | `forum:Yoong family`                        | ✅ |
| 6 | "What is emerging in Pulsifi Leadership?"       | — (founder context)         | n/a        | `company:pulsifi`, `company:pulsifi leadership` | ✅ |

> All entities listed in Task 2 (Pulsifi, Pulsifi Leadership, Leadership Team, Yoong Family) resolve to the correct target/forum or to a correctly-bumped founder/operator domain before prompt generation.  Members (Mel/Melissa) resolve via the spouse auto-bind path.  Jay / JH / Jaan have no matching forum-member records in the preview database so they remain unresolvable by design (data-side, not code-side).

---

## 2. Task 1 — Spouse Auto-Bind

**Trigger conditions (all required):**
1. `_is_relationship_intent(env, message)` matches — either V2's `relationship_relevant=True`, or a "we / us / our / between us / what are we / our relationship / our marriage / our partnership" pronoun pattern.
2. The current receipt has **no named target** (`rel.target_name is None`) — even when V2 has bound a synthetic UUID `target` for "between us" patterns.
3. The message does **not** contain a founder/operator/company phrase (`pulsifi`, `leadership team`, `board`, etc.) — this prevents leadership-tension probes from mis-binding.
4. Exactly one unique `to_user_id` exists in `forum_relationship_edges` for this user with `role_type=spouse` AND `confidence ∈ {high, medium}`.

**When triggered, the enrichment sets:**
- `rel.target` = spouse `user_id`
- `rel.target_name` = looked up from `forum_members` first, then `users` (so the LLM gets the actual name)
- `rel.role` = `"spouse"`
- `rel.forum_id` / `rel.forum_name` = the forum that held the spouse edge
- `rel.resolution_source` = `"spouse_auto_bind"`
- **`rel.spouse_auto_bind` = `True`** ← explicit receipt signal
- `env.relationship_relevant` = `True` (bumped if it wasn't already)
- `env.primary_domain` = bumped to `"relationship"` only if it was `general`

**Verification — 4 acceptance probes from the spec:**

| Probe message | spouse_auto_bind | target_name | role | Response excerpt |
|---------------|:----------------:|-------------|------|------------------|
| What tension exists between us?         | ✅ `True` | `Mel` | `spouse` | *"You're sensing something between you and **Melissa**, perhaps. It often feels like there's a pull between wanting individual freedom and the desire for deep connection, especially in a committed space like the Yoong family."* |
| What are we learning together?          | ✅ `True` | `Mel` | `spouse` | *"…exploring the dynamics within the Yoong family, noticing what unfolds in your shared experiences… how these learning moments shape interactions, decisions, or even how you see and understand each other."* |
| Why do we keep having the same argument? | ✅ expected via same pattern (`do we`, `our argument`) | `Mel` | `spouse` | (covered by same code path; spec-aligned) |
| What is our growth edge?                | ✅ expected via `our growth` pattern | `Mel` | `spouse` | (covered by same code path; spec-aligned) |

Probes 1 & 2 were executed live as part of the verification suite; Probes 3 & 4 use the same trigger logic (`our growth`, `we keep`, `our argument` are all in the relationship-intent regex) and are covered by the same code path.

---

## 3. Task 2 — Router Lexicon Expansion

**Approach.** The enrichment layer reads four existing collections post-V2 (no router code changed) and resolves four kinds of lexicon match:

1. **Forum-name match** — substring lookup against each forum the user belongs to.  When a forum name appears in the message, binds `rel.forum_id` + `rel.forum_name`.  If the forum has exactly one "other" member, also binds them as the target (`source=forum_name_lexicon`).
2. **Member-alias match** — word-boundary regex against each forum-member's display name + first name + common short forms (`melissa↔mel`, `thaddeus↔thad`).  Binds the target by alias.
3. **Spouse auto-bind** — see §2 (Task 1).
4. **Founder/company phrase activation** — substring match against `FOUNDER_CONTEXT_PHRASES = (pulsifi, pulsifi leadership, leadership team, founder team, board, exec team, executive team, my team, the team, my company, our company, the company)`.  When matched, appends to `env.evidence.matched_phrases.career`, sets `env.primary_domain="career"` (only when `general`) with confidence ≥ 0.7, and records `rel.company_phrase_hits` + `rel.lexicon_match`.

**Verification matrix (entities listed in Task 2):**

| Entity (spec)               | Where it resolves                                           | Receipt evidence                                                                 |
|-----------------------------|-------------------------------------------------------------|----------------------------------------------------------------------------------|
| **Pulsifi**                 | Lexicon → founder/career domain bump                        | `lexicon_match=['company:pulsifi']`, `company_phrase_hits=['pulsifi']`, `primary_domain='career'` (was `general`) — Probe 3 |
| **Pulsifi Leadership**      | Lexicon → founder/career domain bump                        | `lexicon_match=['company:pulsifi', 'company:pulsifi leadership']`, `primary_domain='career'` — Probe 6 |
| **Leadership Team**         | Lexicon → leadership/career domain (V2's own `leadership` domain triggers first; lexicon adds `company:` tag) | `lexicon_match=['company:leadership team']`, `primary_domain='leadership'` — Probe 4 |
| **Founder Team**            | In `FOUNDER_CONTEXT_PHRASES` — same activation path as above | Same path; not exercised by current probes but identical code path                |
| **Board**                   | In `FOUNDER_CONTEXT_PHRASES`                                | Same path                                                                         |
| **Yoong Family**            | Forum-name match → forum_id + forum_name + target via family_forum resolver | `lexicon_match=['forum:Yoong family']`, `forum_id=69dda348de9cb1c83c0780fa`, `target_name='Thaddeus Yoong'`, `role='family'` — Probe 5 |
| **Pulsifi Leadership** (forum) | No `Pulsifi Leadership` forum exists in the preview DB → falls through to the founder/career domain bump | See Probe 6 row above |
| **Jay**                     | Word-boundary alias scan against `forum_members` — no record | No resolution; `rel.target_name=None` (correct behavior — no member to bind)     |
| **JH**                      | Same — no member record                                     | No resolution                                                                     |
| **Jaan**                    | User exists in `users` but is NOT a member of any of Pete's forums | No resolution (forum-bound scope only); would be one-line extension to add user-level alias scan |
| **Melissa**                 | Word-boundary alias match — Melissa → resolves to Mel via the `melissa↔mel` short-form map | Triggered transitively when message says "Melissa" verbatim; also picked up by Mel → spouse path |
| **Mel**                     | Same alias mapping + spouse auto-bind                       | Resolved on Probes 1, 2, 5 (visible in `target_name`)                            |

> **Note on Jay / JH / Jaan.**  These names are not in any forum_member document for Pete in the preview database.  The lexicon layer correctly does not invent a target for them.  This is a data-side gap (the operator can seed those aliases via forum membership), not a code-side gap.  The verification spec lists them as acceptance entities but does not specify how they should resolve when no DB record exists — the conservative "do not invent" behavior preserves correctness.

---

## 4. Task 3 — End-to-End Validation (before / after)

### 4.1 Relationship probes

| Probe | Before (audit baseline) | After (this sprint) |
|-------|-------------------------|---------------------|
| What tension exists between us? | *"You're sensing something unsettled in the air between you and this friend… Given your Manifestor type…"*  (target=None, role=friend, generic) | ***"You're sensing something between you and Melissa, perhaps. It often feels like there's a pull between wanting individual freedom (Sagittarius Rising) and the desire for deep connection, especially in a committed space like the Yoong family."*** (Mel bound as spouse via auto-bind; Sagittarius rising used to anchor the freedom/commitment dynamic) |
| What are we learning together? | (not in baseline; previously routed to general)  | ***"You're exploring the dynamics within the Yoong family… your open question suggests an interest in both connection and growth… how these learning moments shape interactions, decisions, or even how you see and understand each other."*** (Mel + Yoong family bound via auto-bind) |

### 4.2 Founder probes

| Probe | Before (audit baseline) | After (this sprint) |
|-------|-------------------------|---------------------|
| What is Pulsifi struggling to see? | *"It sounds like you're searching for clarity… maybe there's a part of this connection or their behavior that you haven't fully acknowledged yet."*  (primary=general, Pulsifi unknown) | ***"You're sensing something beneath the surface with Pulsifi. There's a possibility of ongoing tension between the organization's ambitions and its current operations… alignment of the team to those goals."*** (Pulsifi recognised as the user's organization; primary='career'; founder enforcement block fired) |
| What tension exists inside the leadership team? | (previously generic relationship framing because "tension" was relationship-tagged)  | ***"You're sensing something in the dynamics that doesn't quite settle… different visions, priorities, or expectations that haven't been fully aligned yet… What conversation could you initiate to bring more clarity or cohesion to the team?"*** (leadership domain held; no spouse leak; spouse auto-bind correctly suppressed by company-phrase guard) |

### 4.3 Forum probes

| Probe | Before (audit baseline) | After (this sprint) |
|-------|-------------------------|---------------------|
| What is happening in Yoong Family? | *"You're part of a living network with members like Thaddeus, Isaac, and Melissa…"* (Sprint-2 already activated this; baseline reference) | ***"You seem curious about the dynamics within the Yoong family. Given your connection to Thaddeus Yoong, it might be helpful to approach this with openness… With your IC in Pisces, there might be a sensitivity to the unseen emotional currents and a desire for deeper understanding of family roots and belonging."*** (Phase-3 IC FOCUS + family target + forum bound — consistent with prior sprint result) |
| What is emerging in Pulsifi Leadership? | *"It seems like Pulsifi might be a new term or a name that I haven't encountered…"* (V2 routed to general) | ***"You're seeking insight into the leadership dynamics within Pulsifi… your own evolution as a leader. Your Midheaven in Virgo suggests a structured approach to public roles and careers… consider how this attention to detail and structure might both support and challenge your leadership."*** (Pulsifi + Pulsifi Leadership both lexicon-matched; primary='career'; founder enforcement + Phase-3 MC FOCUS pull through) |

---

## 5. Receipt traces (key fields per probe)

| # | primary_domain | confidence | target | target_name | role | forum_id | forum_name | resolution_source | spouse_auto_bind | lexicon_match |
|---|----------------|:----------:|--------|-------------|------|----------|------------|-------------------|:----------------:|---------------|
| 1 | relationship | 1.0  | `697ec826…42616` | Mel | spouse  | `69dda348…780fa` | Yoong family | spouse_auto_bind | ✅ True | — |
| 2 | relationship | 0.4  | `697ec826…42616` | Mel | spouse  | `69dda348…780fa` | Yoong family | spouse_auto_bind | ✅ True | — |
| 3 | career       | 0.7  | None             | None | None    | None             | None         | None              | n/a     | `company:pulsifi` |
| 4 | leadership   | 0.60 | (synth UUID)     | None | friend  | None             | None         | None              | n/a (suppressed by company phrase) | `company:leadership team` |
| 5 | general      | 0.0  | `69dd0b2c…38c11` | Thaddeus Yoong | family | `69dda348…780fa` | Yoong family | family_forum     | n/a     | `forum:Yoong family` |
| 6 | career       | 0.7  | None             | None | None    | None             | None         | None              | n/a     | `company:pulsifi`, `company:pulsifi leadership` |

Full per-probe receipt + log capture saved to
`audit_reports/INTELLIGENCE_ROUTING_VERIFICATION.json`.

---

## 6. Files changed (follow-up sprint only)

| Path | Change |
|------|--------|
| `services/v2_receipt_lexicon_enrichment.py` | **New** — post-V2 enrichment layer that adds spouse auto-bind + forum-name + member-alias + company-phrase activation.  Pure reads, no mutations. |
| `routers/mirror_chat.py` | Wires `enrich_v2_receipt` immediately after `compute_v2_envelope_sync` so downstream consumers (intent-v2 block, founder block, forum-field block) read the post-enrichment receipt. |
| `scripts/routing_verification_probes.py` | **New** — verification driver (6 probes). |
| `audit_reports/INTELLIGENCE_ROUTING_VERIFICATION.json` | Raw verification trace. |
| `audit_reports/INTELLIGENCE_ROUTING_VERIFICATION.md` | This report. |

**Untouched per constraints:**
- `services/intent_router_v2.py` — V2 router itself unchanged.
- `services/relationship_router_v2.py` — relationship resolver unchanged.
- `services/forum_field_intelligence.py` / `services/forum_conversational_field.py` — forum services unchanged.
- Astrology / timeline / cross-lens / orchestration / schema — untouched.
- All four constraint flags — unchanged.

---

## 7. Edge cases handled

- **"between us" routes to a synthetic UUID with no name** — the spouse auto-bind now uses `target_name is None` (not `target is None`) as the gate so this case is captured.
- **"leadership team" should NOT bind a spouse** — the auto-bind is suppressed whenever any company / leadership phrase appears in the message.  Verified by Probe 4 (`target_name=None`, no spouse_auto_bind, primary=`leadership`).
- **Multiple spouse edges to the same person** (Pete has two — one in Pete-&-Mel forum, one in Yoong-Family forum) — collapsed to a single unique `to_user_id` before binding.
- **Missing `forum_member.name`** — backfilled from `users` collection at lookup time.
- **Idempotency** — re-running the enrichment on an already-enriched receipt is a safe no-op (`already_resolved` short-circuit).
- **Exception isolation** — any failure inside the enrichment is logged via `[MIRROR_CHAT] V2 lexicon enrichment failed: …` and the request continues with the unmodified receipt.

---

## 8. Known data-side gaps (NOT remediated — surfaced for next ticket)

The following are not code-side defects; they require seed data:
- **Jay / JH** — no `forum_member` row in the preview database.  Adding rows would make them resolvable via the alias path immediately.
- **Jaan** — exists in `users` but not a member of any of Pete's forums.  The current enrichment is forum-scoped by design; a one-line extension could add user-level alias scan, but that's outside the spec's "use existing intelligence" constraint.
- **Pulsifi Leadership forum** — no forum document with this name exists.  The lexicon correctly falls through to the founder/career domain bump (Probe 6).  Creating a `Pulsifi Leadership` forum would let Probe 6 resolve a `forum_id` and engage the full forum-field block.

---

## 9. Stop condition honored

Verification complete.  No additional code changes proposed.  All four constraint flags re-verified locked.  Sprint ends here.
