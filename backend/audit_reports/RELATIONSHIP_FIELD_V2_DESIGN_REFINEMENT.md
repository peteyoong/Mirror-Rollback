# RELATIONSHIP FIELD V2 — Design Refinement (Read-Only)

**Date:** 2026-06-14
**Status:** Design draft. Awaiting approval before any implementation.
**Supersedes Section 7 of:**
  `audit_reports/RELATIONSHIP_FIELD_V2_ORCHESTRATION_AUDIT.md`
**Scope additions per user directive:**
  Add `relationship_stance` as a first-class field. Define the schema,
  the taxonomy, and worked example outputs for Mel, Thaddeus, Isaac,
  a forum_member, and an unknown person.
**Mandate:** Zero code. Zero DB writes. Zero migrations. Zero flag
changes. Zero deploys.

---

## 0. Why `relationship_stance` exists

The audit (Section 1) showed that today's machinery identifies **who**
the target is (role = spouse, child, parent, ...) but never encodes
**how that person exists in relation to the user**. A "role" is a
structural label; a "stance" is a semantic posture that downstream
surfaces can read to pick voice, lens emphasis, and framing.

Two real-data examples make the gap visible:

```
role  = "child"           role  = "parent"
                               vs
stance = "steward_guardian" stance = "lineage_source"
   ↓                            ↓
user is responsible-for      user is descended-from
voice = caretaking            voice = inheritance
lens emphasis: Moon, 4th      lens emphasis: IC, Saturn,
                              South-Node
```

Role + stance together let Mirror answer "Tell me about Thaddeus"
*differently* from "Tell me about my mother" — even though both edges
exist in `forum_relationship_edges` with `role_type` ∈ {child, parent}.

---

## 1. Relationship Field — Canonical Schema

### 1.1 Shape (pseudo-schema, language-agnostic)

```
RelationshipField {
  # ── Identity ────────────────────────────────────────────────
  self_user_id           : str           # always the viewer
  target_user_id         : str | null    # canonical FK to users
  target_name            : str | null    # display name
  target_aliases         : list[str]     # all known aliases (lex hits)

  # ── Frame & topology ────────────────────────────────────────
  active_frame           : enum {SELF, MEMBER, FORUM, RELATIONAL}
  forum_id               : str | null
  forum_name             : str | null
  forum_topology         : {
      members            : list[{id, name, role?}]
      active_member_id   : str | null
      member_count       : int
      is_private         : bool
  } | null

  # ── Role + stance (the new layer) ───────────────────────────
  relationship_role      : enum (see §2.1 — structural label)
  relationship_stance    : enum (see §2.2 — semantic posture)
  closeness              : enum {HIGH, MEDIUM, LOW}
  emotional_weight       : enum {HIGH, MEDIUM, LOW}
  directionality         : enum {SYMMETRIC,
                                 USER_AS_GIVER,
                                 USER_AS_RECEIVER}

  # ── Provenance / debuggability ──────────────────────────────
  resolution_source      : enum {
      forum_relationship_edges,        # 1st-class canonical
      explicit_map,                    # /api/admin/map-relationship
      saved_people,                    # user-saved circle
      forum_inference,                 # 2-member private forum etc.
      member_alias_lexicon,            # lex name match (weakest)
      pronoun_memory,                  # last-target threading
      proposed_unresolved,             # name-fallback only
      none                             # nothing matched
  }
  resolution_path        : list[str]   # ordered audit trail
  confidence             : float in [0,1]
  conflicts              : list[str]   # e.g. "edge=spouse vs sp=friend"
  missing_data           : list[str]
  router_version         : str

  # ── Downstream hints (computed once, consumed by all surfaces) ─
  framing_hint           : enum (see §2.3)
  domain_bias            : enum (see §2.4)
  lens_priority          : list[str]   # ordered lens stack
  prior_relational_memory_keys : list[str]  # pointers to past mappings
}
```

### 1.2 Single Resolver Contract

```
resolve_relationship_field(
    self_user_id     : str,
    message          : str,
    hints            : {
        about_person_id  : str | null,
        forum_topology   : {...} | null,
        life_domain      : str | null,
        last_target_id   : str | null,    # ← NEW: pronoun threading
    },
    db
) → RelationshipField
```

All five live surfaces (Ask Mirror generalist, Ask Mirror lens, Forum
Chat, How They Map To Me, Relationship Insight V2) call this **once
per request** and read from the returned envelope.

### 1.3 Resolution Precedence

The single canonical priority ladder that replaces today's three-tree
race:

```
  1. forum_relationship_edges (role_type explicit)   ← canonical
  2. relationship_mappings    (user-defined)
  3. saved_people             (user-saved circle)
  4. forum_members            (role_type at membership row)
  5. forum_inference          (2-member private etc.)
  6. member_alias_lexicon     (text scan)
  7. pronoun_memory           (last_target_id)
  8. proposed_unresolved      (proper-name fallback, receipt-only)
```

Whichever step resolves first AND yields a `role_type` populates the
field. **Lower-precedence sources only fire if higher ones are absent**
— this fixes the audit's #2 critical bug (lexicon racing edges).

---

## 2. Taxonomies

### 2.1 Role Vocabulary (structural — already exists)

Sourced from `services/forum_topology.py` and
`services/relationship_orchestration_v1.py`. No change to the existing
role lexicon — `relationship_stance` is layered ON TOP, not replacing.

```
FAMILY:        spouse · former_partner · child · parent · sibling
PROFESSIONAL:  cofounder · business_partner · manager · employee ·
               investor · advisor · mentor · mentee · coach · coachee
SOCIAL:        close_friend · forum_mate · authority_figure ·
               collaborator · other
SELF:          self (no target)
```

### 2.2 Stance Vocabulary (semantic — NEW)

#### 2.2.1 Core mapping (user-approved, frozen)

| `relationship_role`   | `relationship_stance`   | One-line semantic                                   |
| --------------------- | ----------------------- | --------------------------------------------------- |
| `spouse`              | `covenant_partner`      | Mutual binding commitment; symmetric weight         |
| `child`               | `steward_guardian`      | User is responsible-for; protective directionality  |
| `parent`              | `lineage_source`        | User is descended-from; inheritance directionality  |
| `sibling`             | `shared_origin`         | Lateral; same generational soil                     |
| `close_friend`        | `chosen_ally`           | Selected (not biological); voluntary closeness      |
| `mentor`              | `guide`                 | Asymmetric upward; user receives                    |
| `forum_member`        | `peer`                  | Lateral; situational; bounded by forum context      |
| *(unresolved)*        | `neutral`               | Stance unknown; no relational scaffolding asserted  |

#### 2.2.2 Proposed extensions (for completeness; **flag for review**)

Each is derivable from existing role tokens already in the system
(`relationship_orchestration_v1.LENS_MODULATIONS`). Marked
"PROPOSED" so we can either lock them or trim before implementation.

| `relationship_role`         | proposed `relationship_stance` | Semantic                                                              |
| --------------------------- | ------------------------------ | --------------------------------------------------------------------- |
| `former_partner` / `ex`     | `severed_covenant`             | Was covenant_partner; binding is dissolved but echo remains           |
| `mentee`                    | `apprentice`                   | Inverse of guide; user gives developmental energy                     |
| `coach`                     | `accountable_guide`            | Like mentor, but transactional / structured                           |
| `coachee` / `client`        | `accountable_apprentice`       | Inverse of accountable_guide                                          |
| `cofounder` / `business_partner` | `co_architect`            | Symmetric work-covenant; shared structural authorship                 |
| `advisor`                   | `counsel`                      | Periodic asymmetric guide on specific axis                            |
| `investor`                  | `stakeholder`                  | Asymmetric power; user is accountable-to                              |
| `manager` / `boss`          | `authority_above`              | User is accountable-to within hierarchy                               |
| `employee` / `direct_report` | `authority_below`             | User holds responsibility-for within hierarchy                        |
| `authority_figure`          | `power_holder`                 | External authority not tied to org chart                              |
| `collaborator`              | `peer_in_motion`               | Project-scoped lateral working partnership                            |
| `forum_mate` / `other`      | `peer`                         | Same as core forum_member                                             |
| `self`                      | `self_subject`                 | No target; user is reflecting on themselves                           |

#### 2.2.3 Stance attributes (consumed by downstream surfaces)

Each stance carries a constant attribute bundle. These attributes are
the **interface** the downstream surfaces read — not the stance string
itself.

```
StanceAttributes {
  voice           : enum {covenant, protective, inherited,
                          lateral, voluntary, deferential,
                          coaching, accountable, mutual,
                          dissolving, peer, self}
  directionality  : enum {SYMMETRIC, USER_AS_GIVER, USER_AS_RECEIVER}
  intensity_cap   : enum {HIGH, MEDIUM, LOW}    # caps response intensity
  primary_axis    : enum {DC_7th, IC_4th, MC_10th,
                          North_Node, South_Node, Saturn,
                          Venus, Moon, Sun, Mars, none}
  forbidden_voice : list[str]   # e.g. covenant_partner must NOT
                                # speak as if Mel were a stranger
}
```

Lookup table (subset shown — full table sized to match §2.2):

| stance              | voice          | direction        | intensity | primary axis  | forbidden                                  |
| ------------------- | -------------- | ---------------- | --------- | ------------- | ------------------------------------------ |
| `covenant_partner`  | covenant       | SYMMETRIC        | HIGH      | DC_7th, Venus | strangers’ voice; generic Sun-sign         |
| `steward_guardian`  | protective     | USER_AS_GIVER    | HIGH      | Moon, IC_4th  | peer voice; intellectual detachment        |
| `lineage_source`    | inherited      | USER_AS_RECEIVER | HIGH      | IC_4th, Saturn, S-Node | mentor framing; coaching tone     |
| `shared_origin`     | lateral        | SYMMETRIC        | MEDIUM    | Moon, IC_4th  | hierarchical voice                         |
| `chosen_ally`       | voluntary      | SYMMETRIC        | MEDIUM    | Venus, Mars   | covenant voice; family framing             |
| `guide`             | deferential    | USER_AS_RECEIVER | MEDIUM    | Jupiter, MC   | peer voice; co-equal framing               |
| `peer`              | peer           | SYMMETRIC        | MEDIUM    | Mercury, Mars | covenant voice; family voice               |
| `neutral`           | self           | n/a              | LOW       | none          | asserting any specific relational frame    |
| `severed_covenant`  | dissolving     | SYMMETRIC        | HIGH      | DC_7th, Pluto | active-covenant voice                      |
| `co_architect`      | mutual         | SYMMETRIC        | HIGH      | MC, Saturn    | romantic voice; family voice               |
| `authority_above`   | accountable    | USER_AS_GIVER    | MEDIUM    | Saturn, MC    | peer voice; family voice                   |
| `authority_below`   | coaching       | USER_AS_RECEIVER | MEDIUM    | Saturn, MC    | peer voice; family voice                   |
| `self_subject`     | self           | n/a              | LOW       | none          | asserting a target where none exists       |

### 2.3 Framing Hint (unchanged from `relationship_orchestration_v1`)

Stance is the upstream signal. Framing hint is the downstream sentence
the prompt builder can use. Today's `FRAMING_HINT` map is preserved —
stance just makes the choice deterministic instead of bucket-only.

### 2.4 Domain Bias (unchanged)

Per-stance default for the `domain_bias` field already used by the
dashboard. Inherited from
`relationship_orchestration_v1.DOMAIN_BIAS`; the stance taxonomy
provides a finer-grained source of truth.

---

## 3. Worked Examples — Real Pete Data

All examples use the live `test_database` edge graph from the audit:

```
Pete (697f0c6abf35c0528ff06954)
  → Mel (697ec826) spouse high  [Pete & Mel · Yoong family]
  → Thaddeus (69dd0b2c) child high  [Yoong family]
  → Isaac (69dda348) child high  [Yoong family]
```

For each example, the resolver call is identical:

```
resolve_relationship_field(
    self_user_id = "697f0c6abf35c0528ff06954",
    message      = <see each example>,
    hints        = {about_person_id: null,
                    forum_topology: null,
                    life_domain:    null,
                    last_target_id: null},
    db           = ...
) → RelationshipField
```

What changes between examples is the message and (consequently) the
target the resolver binds.

### 3.1 Example A — Spouse: Mel

**Message:** "Tell me about Mel."

```jsonc
{
  // Identity
  "self_user_id":   "697f0c6abf35c0528ff06954",
  "target_user_id": "697ec826ad4b18f75bf42616",
  "target_name":    "Mel",
  "target_aliases": ["Mel", "Melissa", "Melissa Mars"],

  // Frame
  "active_frame":   "MEMBER",        // promoted post-resolution
  "forum_id":       "69dd05ea…",     // Pete & Mel (private, 2-member)
  "forum_name":     "Pete & Mel",
  "forum_topology": {
    "members": [
      {"id": "697f0c6a…", "name": "Pete", "role": "spouse"},
      {"id": "697ec826…", "name": "Mel",  "role": "spouse"}
    ],
    "active_member_id": "697ec826…",
    "member_count":     2,
    "is_private":       true
  },

  // Role + stance
  "relationship_role":   "spouse",
  "relationship_stance": "covenant_partner",
  "closeness":           "HIGH",
  "emotional_weight":    "HIGH",
  "directionality":      "SYMMETRIC",

  // Provenance
  "resolution_source": "forum_relationship_edges",
  "resolution_path":   [
    "edges:from=Pete,to=Mel,role=spouse,conf=high",
    "edges:scope_pair_forum=Pete & Mel",
    "stance_lookup:spouse->covenant_partner"
  ],
  "confidence":     0.97,
  "conflicts":      [],
  "missing_data":   [],
  "router_version": "relationship_field_v2.0.0",

  // Downstream
  "framing_hint":  "couple_dynamic",
  "domain_bias":   "relationship",
  "lens_priority": ["astrology_relationship_layer", "relationship_field",
                    "human_design_relationship", "bazi_relationship",
                    "enneagram_attachment", "numerology"],
  "prior_relational_memory_keys": [
    "forum_mappings:pete<>mel:2026-06-14",
    "rel_insight_v2:pete<>mel:2026-06-14"
  ]
}
```

#### How each surface would consume it

| Surface                  | What it does differently from today                                                                                              |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| Ask Mirror (generalist)  | Replaces today's soft "bound (role: forum_peer)" line with a RESOLVED FIELD mandate block using `stance=covenant_partner`. Forbids stranger / Sun-sign voice. Anchors in DC/Venus axis. |
| Ask Mirror (astrology)   | Activates the **layered relationship block** (Descendant / 7th / Venus / Juno) — today this only fires from Forum Chat.          |
| Forum Chat               | Same field, no rebuild. The `forum_id` is now redundant because it's already on the field.                                       |
| How They Map To Me       | Card stays unchanged for Mel, but the `prior_relational_memory_keys` mean Mirror Chat can cite "yesterday's mapping said…".       |
| Relationship Insight V2  | Validates URL `context=spouse` against `relationship_role=spouse` — flags mismatch in `conflicts`. Today blindly trusts the URL. |

### 3.2 Example B — Child: Thaddeus

**Message:** "What's coming up for Thaddeus this week?"

```jsonc
{
  "self_user_id":   "697f0c6abf35c0528ff06954",
  "target_user_id": "69dd0b2cc92ba973f8838c11",
  "target_name":    "Thaddeus Yoong",
  "target_aliases": ["Thaddeus", "Thaddeus Yoong"],

  "active_frame":   "MEMBER",
  "forum_id":       "69dda348…",        // Yoong family
  "forum_name":     "Yoong family",
  "forum_topology": {
    "members": [
      {"id": "697f0c6a…", "name": "Pete",     "role": "parent"},
      {"id": "697ec826…", "name": "Mel",      "role": "parent"},
      {"id": "69dd0b2c…", "name": "Thaddeus", "role": "child"},
      {"id": "69dda348…", "name": "Isaac",    "role": "child"}
    ],
    "active_member_id": "69dd0b2c…",
    "member_count":     4,
    "is_private":       true
  },

  "relationship_role":   "child",
  "relationship_stance": "steward_guardian",
  "closeness":           "HIGH",
  "emotional_weight":    "HIGH",
  "directionality":      "USER_AS_GIVER",     // Pete → Thaddeus

  "resolution_source": "forum_relationship_edges",
  "resolution_path":   [
    "edges:from=Pete,to=Thaddeus,role=child,conf=high",
    "edges:scope_family_forum=Yoong family",
    "stance_lookup:child->steward_guardian"
  ],
  "confidence":     0.96,
  "conflicts":      [],
  "missing_data":   [],
  "router_version": "relationship_field_v2.0.0",

  "framing_hint":  "parenting",
  "domain_bias":   "relationship",
  "lens_priority": ["astrology_home_layer", "human_design_family_pattern",
                    "relationship_field", "enneagram_attachment",
                    "numerology"],
  "prior_relational_memory_keys": [
    "forum_mappings:pete<>thaddeus:…"
  ]
}
```

#### How surfaces shift from today's behaviour

- **Ask Mirror**: Today, "What's coming up for Thaddeus this week?"
  fails the `life_domain=relationship` regex (no spouse/marriage/etc.
  tokens) → the parenting frame never activates. **With the field**:
  `stance=steward_guardian` directly activates parenting frame
  regardless of message phrasing. Voice: protective. Primary axis:
  Moon / 4th house. Forbidden: peer / intellectual-detachment voice.
- **Astrology Chat**: Layered relationship block re-purposed as
  *layered parenting block* — leads with Moon / IC / 4th / 5th house
  before Sun. Today this block only knows how to talk about partners.

### 3.3 Example C — Child: Isaac (same structure, different person)

**Message:** "Mirror, what does Isaac need from me right now?"

```jsonc
{
  "self_user_id":   "697f0c6abf35c0528ff06954",
  "target_user_id": "69dda348de9cb1c83c0780f8",
  "target_name":    "Isaac Yoong",
  "target_aliases": ["Isaac", "Isaac Yoong"],

  "active_frame":   "MEMBER",
  "forum_id":       "69dda348…",
  "forum_name":     "Yoong family",
  "forum_topology": { /* same shape as 3.2 */ },

  "relationship_role":   "child",
  "relationship_stance": "steward_guardian",
  "closeness":           "HIGH",
  "emotional_weight":    "HIGH",
  "directionality":      "USER_AS_GIVER",

  "resolution_source": "forum_relationship_edges",
  "resolution_path":   [
    "edges:from=Pete,to=Isaac,role=child,conf=high",
    "edges:scope_family_forum=Yoong family",
    "stance_lookup:child->steward_guardian"
  ],
  "confidence":     0.96,
  "conflicts":      [],
  "missing_data":   [],
  "router_version": "relationship_field_v2.0.0",

  "framing_hint":  "parenting",
  "domain_bias":   "relationship",
  "lens_priority": ["astrology_home_layer", "human_design_family_pattern",
                    "relationship_field", "enneagram_attachment",
                    "numerology"],
  "prior_relational_memory_keys": [
    "forum_mappings:pete<>isaac:…"
  ]
}
```

**Why this is a useful regression case:**
Thaddeus and Isaac have **identical stance + lens stack**, but the
question phrasing differs sharply ("what's coming up for X" vs "what
does X need from me"). With the field-based resolver, the prompt
output should be parenting-voiced in *both* turns. Today, Thaddeus's
question would fall through to a generic forecast voice; Isaac's
question (which contains "need from me") might accidentally trigger
the relationship regex via "from me" pattern matching and surface a
spouse-flavoured response. The stance lock prevents the
mis-classification.

### 3.4 Example D — Forum Member (non-family, no role edge)

**Setup:** Imagine Pete is in a **professional** forum named
"Pulsifi Leadership" with members including a colleague "Bee".
No `forum_relationship_edges.role_type` is set for Pete↔Bee
(role-less edge or no edge yet — the membership exists but the role
is unannotated).
**Message:** "How does Bee land for me in this forum?"

```jsonc
{
  "self_user_id":   "697f0c6abf35c0528ff06954",
  "target_user_id": "<bee_user_id>",
  "target_name":    "Bee",
  "target_aliases": ["Bee"],

  "active_frame":   "FORUM",          // forum context drives frame
  "forum_id":       "<pulsifi_leadership_forum_id>",
  "forum_name":     "Pulsifi Leadership",
  "forum_topology": {
    "members":          [/* the forum's actual members */],
    "active_member_id": "<bee_user_id>",
    "member_count":     6,
    "is_private":       false
  },

  "relationship_role":   "forum_member",
  "relationship_stance": "peer",
  "closeness":           "MEDIUM",
  "emotional_weight":    "MEDIUM",
  "directionality":      "SYMMETRIC",

  "resolution_source": "forum_members",       // edge had no role_type
  "resolution_path":   [
    "edges:from=Pete,to=Bee:role_type_missing",
    "fallback:forum_members:role=forum_member",
    "stance_lookup:forum_member->peer"
  ],
  "confidence":     0.72,
  "conflicts":      [],
  "missing_data":   ["explicit_role_on_edge"],   // dashboard signal
  "router_version": "relationship_field_v2.0.0",

  "framing_hint":  "forum_member_dynamic",
  "domain_bias":   "forum",
  "lens_priority": ["relationship_field", "human_design_relationship",
                    "astrology_relationship_layer",
                    "enneagram_attachment", "numerology"],
  "prior_relational_memory_keys": []
}
```

#### Surface behaviour

- **Ask Mirror**: Today, "How does Bee land for me" only resolves Bee
  if she's in the user's `saved_people` (rarely true for colleagues).
  **With the field**: forum-member lexicon match against the forum
  member list resolves Bee; `stance=peer` activates professional
  voice; forbidden: covenant / family voice. Lens lead: Mercury /
  Mars / 11th house (peer dynamics).
- **Missing-data telemetry**: `missing_data=["explicit_role_on_edge"]`
  surfaces in the dashboard so an operator can promote Bee to a
  specific role (advisor / collaborator / etc.) — improving every
  future query for Pete↔Bee.

### 3.5 Example E — Unknown Person

**Message:** "What does Mirror think about Patricia?"
(Patricia is not in `saved_people`, not in any of Pete's forums,
not in any edge.)

```jsonc
{
  "self_user_id":   "697f0c6abf35c0528ff06954",
  "target_user_id": null,
  "target_name":    null,
  "target_aliases": ["Patricia"],     // unresolved candidate

  "active_frame":   "SELF",
  "forum_id":       null,
  "forum_name":     null,
  "forum_topology": null,

  "relationship_role":   null,
  "relationship_stance": "neutral",
  "closeness":           "LOW",
  "emotional_weight":    "LOW",
  "directionality":      null,

  "resolution_source": "proposed_unresolved",
  "resolution_path":   [
    "edges:no_match",
    "saved_people:no_match",
    "forum_members:no_match",
    "lexicon:no_match",
    "proper_name_fallback:Patricia",
    "stance_lookup:unknown->neutral"
  ],
  "confidence":     0.55,
  "conflicts":      [],
  "missing_data":   ["target_unresolved"],
  "router_version": "relationship_field_v2.0.0",

  "framing_hint":  "self_inquiry",
  "domain_bias":   "self",
  "lens_priority": [],
  "prior_relational_memory_keys": [],

  "proposed_action": {
    "type":           "add_to_circle",
    "suggested_name": "Patricia",
    "reason":         "name 'Patricia' appears in message but is not in user's saved_people OR any of their forums",
    "source_text":    "What does Mirror think about Patricia?",
    "confidence":     0.55
  }
}
```

#### Surface behaviour

- **Ask Mirror**: Today's prompt already has the right copy
  ("Acknowledge this rather than guessing who they are. Ask the user
  who 'Patricia' is."). With the field, this stays — but the
  `proposed_action` is no longer dead-lettered: any frontend can read
  `field.proposed_action` and render an "Add Patricia to your
  circle?" CTA underneath the response.
- **Stance lock**: `stance=neutral` explicitly forbids the LLM from
  asserting any specific relational frame ("she sounds like a
  romantic interest"). Today the LLM is free to project — the
  neutral stance closes that exit.

---

## 4. Backwards-Compatibility Notes

The Field is **additive on top of today's signals**:

- `relationship_role` is preserved verbatim; existing readers continue
  to work.
- `relationship_stance` is a new field on the
  `relationship_resolution` block.
- The `relationship_orchestration_v1` plan continues to compute as
  today; the Field just becomes its input source-of-truth instead of
  three competing layers.
- The flag `RELATIONSHIP_ORCHESTRATION_PROMPT` remains the gate for
  whether `framing_hint` is injected into the prompt. The Field
  itself is **non-flag-gated** — it's a data refinement, not a
  prompt behaviour change.
- Stance attributes (voice / directionality / intensity / axis /
  forbidden_voice) live in a separate lookup module and can be edited
  without touching the resolver.

---

## 5. Resolution Walkthrough — Pete's 4 Cases In One Pass

How the single resolver call dispatches each example:

```
                              ┌───────────────────────┐
                              │ resolve_relationship_ │
                              │      field(...)       │
                              └───────────┬───────────┘
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            │                             │                             │
            ▼                             ▼                             ▼
  message="Tell me about Mel"   message="...Thaddeus..."    message="...Bee..."
            │                             │                             │
       edges scan                    edges scan                    edges scan
       Pete→Mel spouse              Pete→Thad child              Pete→Bee no role
            │                             │                             │
            ▼                             ▼                             ▼
  role=spouse                       role=child                   role=null
  stance=covenant_partner           stance=steward_guardian      forum_members fallback
  forum_id=Pete & Mel               forum_id=Yoong family        role=forum_member
                                                                stance=peer
                                                                missing=explicit_role

  message="...Patricia..."
            │
       edges scan: miss
       saved_people: miss
       forum_members: miss
       lexicon: miss
            ▼
  proper_name_fallback
  stance=neutral
  proposed_action.type=add_to_circle
```

---

## 6. Open Questions (need user disposition before coding)

1. **Stance extensions (§2.2.2):** Lock as-proposed, edit, or drop
   the entire extension set and ship only the 8 user-approved core
   stances? (Coding plan changes materially.)
2. **Directionality field:** Worth surfacing as its own first-class
   attribute, or fold it into stance attributes only?
   (Recommendation: first-class — it unlocks "who-gives-to-whom"
   queries downstream without re-deriving from stance.)
3. **`prior_relational_memory_keys`:** Keep as pointer-only (read on
   demand by Mirror Chat) or eager-load top-N entries into the
   Field at resolve time? (Pointer-only = leaner; eager-load =
   single retrieval pass.)
4. **`conflicts` enforcement:** When Relationship Insight V2's URL
   `context=stranger` contradicts `edges.role_type=spouse`, do we
   (a) override the URL silently, (b) raise a 409, or (c) record in
   `conflicts` and let the renderer choose? (Recommendation: c.)
5. **Stance for `self`:** Is `self_subject` the right token, or
   should `relationship_stance` be `null` when no target exists?
   (Recommendation: `self_subject` — gives downstream surfaces a
   single non-null token to switch on.)
6. **Lexicon-only matches:** Currently demoted to confidence ≤ 0.7
   so they don't trip the high-confidence mandate block. Confirm
   this threshold is right.

---

## 7. Hold Point

This document is read-only design. No file outside `audit_reports/`
has been touched. No service code changed. No DB writes. No flag
flips. Atlas access remains blocked pending IP whitelist.

**Awaiting user approval on:**
- The schema in §1
- The stance taxonomy in §2 (core mapping + extension set)
- The example envelopes in §3 (especially the resolution_source for
  edge-less forum members)
- The six open questions in §6

Once approved, the implementation sequence proposed in the audit
(`resolve_relationship_field()` service + FE payload normalisation +
prompt-block consolidation) can begin. No coding until then.
