# R3b Forum-Topology Fallback — Forensic Validation Report

_Generated: 2026-06-12T07:12:00.272417+00:00_

_Scope: Phase 4 / R3b only.  No rollout/cutover flags were touched.  No P3 surfacing or P5 work executed.  No DB mutations._

## 1. Resolution Source Inventory

| Source | Priority | Role Inference | Defined In |
|---|---|---|---|
| `saved_people` | 0 | explicit (saved_people.relationship_type) | services/relationship_router_v2.py (step 2: name in message → saved_people match) |
| `pair_forum` | 1 | partner (forum name matches _PAIR_FORUM_NAME_RE) | services/mirror_chat_phase4_enrichment.py → resolve_target_via_forums → _classify_forum_source (regex) |
| `family_forum` | 2 | family (forum name contains 'family' / 'fam') | services/mirror_chat_phase4_enrichment.py → resolve_target_via_forums → _classify_forum_source (regex) |
| `forum_member` | 3 | None (no role inferred; left to LLM context). | services/mirror_chat_phase4_enrichment.py → resolve_target_via_forums (fallthrough) |
| `alias_spouse_via_pair_forum` | 1 | partner (deterministic) | services/mirror_chat_phase4_enrichment.py → resolve_target_via_forums (role-noun path) |
| `alias_spouse_via_single_other_member` | 2 | partner (deterministic) | services/mirror_chat_phase4_enrichment.py → resolve_target_via_forums (role-noun path) |
| `unresolved` | 99 | None.  Surfaces 'target_unresolved_name' to the LLM with explicit 'ask the user' framing. | services/mirror_chat_phase4_enrichment.py → resolve_target_via_forums (fallback) |

**Notes**:
- `saved_people` — Authoritative.  Wins over any forum-derived source.
- `pair_forum` — Two-person forum named 'X & Y' / 'X and Y' / 'X+Y'.
- `family_forum` — Multi-member forum with 'family' keyword.
- `forum_member` — Any other shared forum (no pair/family heuristic).
- `alias_spouse_via_pair_forum` — Triggered by 'wife','husband','spouse', etc. Resolves to the single non-self member of a named pair forum.
- `alias_spouse_via_single_other_member` — Triggered by spouse aliases when forum name doesn't match pair regex but forum has exactly one other member.
- `unresolved` — Graceful failure mode for unknown names.

## 3. Final Precedence Ladder

| Order | Step | Module |
|---|---|---|
| 0a | explicit_target_id | `relationship_router_v2.py` or `mirror_chat_phase4_enrichment.py` |
| 0b | saved_people (name match) | `relationship_router_v2.py` or `mirror_chat_phase4_enrichment.py` |
| 0c | pronoun_memory + last_target_id | `relationship_router_v2.py` or `mirror_chat_phase4_enrichment.py` |
| 0d | forum_active_member (forum frame) | `relationship_router_v2.py` or `mirror_chat_phase4_enrichment.py` |
| 1 | pair_forum | `relationship_router_v2.py` or `mirror_chat_phase4_enrichment.py` |
| 1 | alias_spouse_via_pair_forum | `relationship_router_v2.py` or `mirror_chat_phase4_enrichment.py` |
| 2 | family_forum | `relationship_router_v2.py` or `mirror_chat_phase4_enrichment.py` |
| 2 | alias_spouse_via_single_other_member | `relationship_router_v2.py` or `mirror_chat_phase4_enrichment.py` |
| 3 | forum_member | `relationship_router_v2.py` or `mirror_chat_phase4_enrichment.py` |
| 99 | unresolved → target_unresolved_name | `relationship_router_v2.py` or `mirror_chat_phase4_enrichment.py` |

_Implementation_: see `_src_priority` in `resolve_target_via_forums` (`pair_forum=0`, `family_forum=1`, `forum_member=2`) and the resolution-ladder ordering in `resolve_relationship_context`.

## 2. Side-by-Side Resolution Trace for Mel (`Tell me about Mel`)

| Source | Candidate found? | Confidence | Role | Priority | Accepted/Rejected | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| saved_people | No | n/a | n/a | 0 | Skipped | Mel not in Pete's saved_people |
| pair_forum | Yes ('Pete & Mel') | high | partner | 1 | ACCEPTED | Forum name matches X & Y pattern → partner |
| family_forum | Yes ('Yoong family') | moderate | family | 2 | Rejected (pair_forum has higher precedence (1 < 2)) | pair_forum has higher precedence (1 < 2) |
| forum_member | No | n/a | n/a | 3 | Skipped | No other (non-pair, non-family) shared forum |
| alias_mapping | n/a (message uses 'Mel' directly) | n/a | n/a | 1/2 | Not triggered | Spouse-alias path only fires when message contains 'wife','husband','spouse', etc. |

## 4. Forensic Traces — Core 4 Probes

#### Message: `How does Mel map to me?`

- **Winner**: `pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b matched in 2 forums; sorted by priority (pair_forum=0 > family_forum=1 > forum_member=2). Winner: pair_forum ('Pete & Mel'). Defeated: family_forum ('Yoong family').

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "pair_forum",
  "pair_forum_match": true,
  "family_forum_match": true,
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ]
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Mel",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Mel",
    "reason": "name 'Mel' appears in message but is not in user's saved_people",
    "source_text": "How does Mel map to me?",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": "Mel",
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "pair_forum",
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ],
  "user_forum_count": 4,
  "alias_used": "mel\u2192email:melissa.mars"
}
```
</details>

#### Message: `Tell me about Mel`

- **Winner**: `pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b matched in 2 forums; sorted by priority (pair_forum=0 > family_forum=1 > forum_member=2). Winner: pair_forum ('Pete & Mel'). Defeated: family_forum ('Yoong family').

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "pair_forum",
  "pair_forum_match": true,
  "family_forum_match": true,
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ]
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Mel",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Mel",
    "reason": "name 'Mel' appears in message but is not in user's saved_people",
    "source_text": "Tell me about Mel",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": "Mel",
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "pair_forum",
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ],
  "user_forum_count": 4,
  "alias_used": "mel\u2192email:melissa.mars"
}
```
</details>

#### Message: `What is happening between me and Mel?`

- **Winner**: `pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b matched in 2 forums; sorted by priority (pair_forum=0 > family_forum=1 > forum_member=2). Winner: pair_forum ('Pete & Mel'). Defeated: family_forum ('Yoong family').

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "pair_forum",
  "pair_forum_match": true,
  "family_forum_match": true,
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ]
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Mel",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Mel",
    "reason": "name 'Mel' appears in message but is not in user's saved_people",
    "source_text": "What is happening between me and Mel?",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": "Mel",
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "pair_forum",
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ],
  "user_forum_count": 4,
  "alias_used": "mel\u2192email:melissa.mars"
}
```
</details>

#### Message: `How does my wife map to me?`

- **Winner**: `alias_spouse_via_pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b single-forum match: alias_spouse_via_pair_forum ('Pete & Mel'). No precedence contest needed.

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "alias_spouse_via_pair_forum",
  "pair_forum_match": false,
  "family_forum_match": false,
  "all_forums_with_match": []
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": null,
  "missing_data": [],
  "conflicts": [],
  "proposed_action": null
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": null,
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "alias_spouse_via_pair_forum",
  "all_forums_with_match": [],
  "user_forum_count": 4,
  "alias_used": "my wife"
}
```
</details>

## 6. Pair-Forum vs Family-Forum Precedence Verification

- `pair_forum_match`: **True** (forum: `Pete & Mel`)
- `family_forum_match`: **True** (forum: `Yoong family`)
- `target_resolution_source` (winner): **`pair_forum`**
- **Pair-forum precedence held**: **YES ✅**

## 7. saved_people Precedence Promotion Check

If Mel is later added to Pete's `saved_people`, the resolver must prefer `saved_people` over any forum source.

- **Before (no saved_people row)**: source=`pair_forum`, id=`697ec826ad4b18f75bf42616`, role=`partner`
- **After (synthetic saved_people row added)**: source=`saved_people`, id=`697ec826ad4b18f75bf42616`, role=`spouse`
- **saved_people wins**: **YES ✅**

## 5. Identity-Resolution Stress Tests

### Mel Case

#### Message: `Tell me about Mel`

- **Winner**: `pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b matched in 2 forums; sorted by priority (pair_forum=0 > family_forum=1 > forum_member=2). Winner: pair_forum ('Pete & Mel'). Defeated: family_forum ('Yoong family').

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "pair_forum",
  "pair_forum_match": true,
  "family_forum_match": true,
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ]
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Mel",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Mel",
    "reason": "name 'Mel' appears in message but is not in user's saved_people",
    "source_text": "Tell me about Mel",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": "Mel",
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "pair_forum",
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ],
  "user_forum_count": 4,
  "alias_used": "mel\u2192email:melissa.mars"
}
```
</details>

#### Message: `How does Mel map to me?`

- **Winner**: `pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b matched in 2 forums; sorted by priority (pair_forum=0 > family_forum=1 > forum_member=2). Winner: pair_forum ('Pete & Mel'). Defeated: family_forum ('Yoong family').

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "pair_forum",
  "pair_forum_match": true,
  "family_forum_match": true,
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ]
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Mel",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Mel",
    "reason": "name 'Mel' appears in message but is not in user's saved_people",
    "source_text": "How does Mel map to me?",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": "Mel",
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "pair_forum",
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ],
  "user_forum_count": 4,
  "alias_used": "mel\u2192email:melissa.mars"
}
```
</details>

#### Message: `What is happening between me and Mel?`

- **Winner**: `pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b matched in 2 forums; sorted by priority (pair_forum=0 > family_forum=1 > forum_member=2). Winner: pair_forum ('Pete & Mel'). Defeated: family_forum ('Yoong family').

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "pair_forum",
  "pair_forum_match": true,
  "family_forum_match": true,
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ]
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Mel",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Mel",
    "reason": "name 'Mel' appears in message but is not in user's saved_people",
    "source_text": "What is happening between me and Mel?",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": "Mel",
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "pair_forum",
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ],
  "user_forum_count": 4,
  "alias_used": "mel\u2192email:melissa.mars"
}
```
</details>

#### Message: `Tell me about my wife`

- **Winner**: `alias_spouse_via_pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b single-forum match: alias_spouse_via_pair_forum ('Pete & Mel'). No precedence contest needed.

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "alias_spouse_via_pair_forum",
  "pair_forum_match": false,
  "family_forum_match": false,
  "all_forums_with_match": []
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": null,
  "missing_data": [],
  "conflicts": [],
  "proposed_action": null
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": null,
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "alias_spouse_via_pair_forum",
  "all_forums_with_match": [],
  "user_forum_count": 4,
  "alias_used": "my wife"
}
```
</details>

#### Message: `How does my spouse map to me?`

- **Winner**: `alias_spouse_via_pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b single-forum match: alias_spouse_via_pair_forum ('Pete & Mel'). No precedence contest needed.

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "alias_spouse_via_pair_forum",
  "pair_forum_match": false,
  "family_forum_match": false,
  "all_forums_with_match": []
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": null,
  "missing_data": [],
  "conflicts": [],
  "proposed_action": null
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": null,
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "alias_spouse_via_pair_forum",
  "all_forums_with_match": [],
  "user_forum_count": 4,
  "alias_used": "my spouse"
}
```
</details>

#### Message: `What should I understand about Melissa?`

- **Winner**: `pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b matched in 2 forums; sorted by priority (pair_forum=0 > family_forum=1 > forum_member=2). Winner: pair_forum ('Pete & Mel'). Defeated: family_forum ('Yoong family').

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "pair_forum",
  "pair_forum_match": true,
  "family_forum_match": true,
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ]
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Melissa",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Melissa",
    "reason": "name 'Melissa' appears in message but is not in user's saved_people",
    "source_text": "What should I understand about Melissa?",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": "Melissa",
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "pair_forum",
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ],
  "user_forum_count": 4,
  "alias_used": "melissa\u2192email:melissa.mars"
}
```
</details>

### Forum Precedence (frame variations)

_Frame=self_
#### Message: `Tell me about Mel`

- **Winner**: `pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b matched in 2 forums; sorted by priority (pair_forum=0 > family_forum=1 > forum_member=2). Winner: pair_forum ('Pete & Mel'). Defeated: family_forum ('Yoong family').

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "pair_forum",
  "pair_forum_match": true,
  "family_forum_match": true,
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ]
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Mel",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Mel",
    "reason": "name 'Mel' appears in message but is not in user's saved_people",
    "source_text": "Tell me about Mel",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": "Mel",
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "pair_forum",
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ],
  "user_forum_count": 4,
  "alias_used": "mel\u2192email:melissa.mars"
}
```
</details>

_Frame=forum_
#### Message: `Tell me about Mel`
_active_frame_: `forum`

- **Winner**: `pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b matched in 2 forums; sorted by priority (pair_forum=0 > family_forum=1 > forum_member=2). Winner: pair_forum ('Pete & Mel'). Defeated: family_forum ('Yoong family').

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "pair_forum",
  "pair_forum_match": true,
  "family_forum_match": true,
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ]
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Mel",
  "missing_data": [
    "forum_target_unresolved",
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Mel",
    "reason": "name 'Mel' appears in message but is not in user's saved_people",
    "source_text": "Tell me about Mel",
    "confidence": 0.65
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": "Mel",
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "pair_forum",
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ],
  "user_forum_count": 4,
  "alias_used": "mel\u2192email:melissa.mars"
}
```
</details>

_Frame=member_
#### Message: `Tell me about Mel`
_active_frame_: `member`

- **Winner**: `pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b matched in 2 forums; sorted by priority (pair_forum=0 > family_forum=1 > forum_member=2). Winner: pair_forum ('Pete & Mel'). Defeated: family_forum ('Yoong family').

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "pair_forum",
  "pair_forum_match": true,
  "family_forum_match": true,
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ]
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Mel",
  "missing_data": [
    "forum_target_unresolved",
    "target_unresolved"
  ],
  "conflicts": [
    "frame=member_but_no_target"
  ],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Mel",
    "reason": "name 'Mel' appears in message but is not in user's saved_people",
    "source_text": "Tell me about Mel",
    "confidence": 0.65
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": "Mel",
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "pair_forum",
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ],
  "user_forum_count": 4,
  "alias_used": "mel\u2192email:melissa.mars"
}
```
</details>

### Cofounder Case (expected: mostly unresolved — no Pulsifi forum exists for Pete)

#### Message: `Tell me about Jay`

- **Winner**: `unresolved` → id=`None`, role=`None`
- **Why**: UNRESOLVED — name not in saved_people, not in any of the user's forums, and no spouse-alias matched a pair-forum.

**Telemetry**:
```json
{
  "target_resolved": false,
  "resolved_target_id": null,
  "relationship_role": null,
  "target_resolution_source": "unresolved",
  "pair_forum_match": false,
  "family_forum_match": false,
  "all_forums_with_match": []
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Jay",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Jay",
    "reason": "name 'Jay' appears in message but is not in user's saved_people",
    "source_text": "Tell me about Jay",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": false,
  "candidate_name": "Jay",
  "resolved_user_id": null,
  "resolved_name": null,
  "resolved_role": null,
  "forum_id": null,
  "forum_name": null,
  "resolution_source": "unresolved",
  "all_forums_with_match": [],
  "user_forum_count": 4,
  "alias_used": null
}
```
</details>

#### Message: `Tell me about Jaan`

- **Winner**: `unresolved` → id=`None`, role=`None`
- **Why**: UNRESOLVED — name not in saved_people, not in any of the user's forums, and no spouse-alias matched a pair-forum.

**Telemetry**:
```json
{
  "target_resolved": false,
  "resolved_target_id": null,
  "relationship_role": null,
  "target_resolution_source": "unresolved",
  "pair_forum_match": false,
  "family_forum_match": false,
  "all_forums_with_match": []
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Jaan",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Jaan",
    "reason": "name 'Jaan' appears in message but is not in user's saved_people",
    "source_text": "Tell me about Jaan",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": false,
  "candidate_name": "Jaan",
  "resolved_user_id": null,
  "resolved_name": null,
  "resolved_role": null,
  "forum_id": null,
  "forum_name": null,
  "resolution_source": "unresolved",
  "all_forums_with_match": [],
  "user_forum_count": 4,
  "alias_used": null
}
```
</details>

#### Message: `What am I not seeing about JH?`

- **Winner**: `unresolved` → id=`None`, role=`None`
- **Why**: UNRESOLVED — name not in saved_people, not in any of the user's forums, and no spouse-alias matched a pair-forum.

**Telemetry**:
```json
{
  "target_resolved": false,
  "resolved_target_id": null,
  "relationship_role": null,
  "target_resolution_source": "unresolved",
  "pair_forum_match": false,
  "family_forum_match": false,
  "all_forums_with_match": []
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": null,
  "missing_data": [],
  "conflicts": [],
  "proposed_action": null
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": false,
  "candidate_name": null,
  "resolved_user_id": null,
  "resolved_name": null,
  "resolved_role": null,
  "forum_id": null,
  "forum_name": null,
  "resolution_source": "unresolved",
  "all_forums_with_match": [],
  "user_forum_count": 4,
  "alias_used": null
}
```
</details>

#### Message: `What is happening in Pulsifi leadership?`

- **Winner**: `unresolved` → id=`None`, role=`None`
- **Why**: UNRESOLVED — name not in saved_people, not in any of the user's forums, and no spouse-alias matched a pair-forum.

**Telemetry**:
```json
{
  "target_resolved": false,
  "resolved_target_id": null,
  "relationship_role": null,
  "target_resolution_source": "unresolved",
  "pair_forum_match": false,
  "family_forum_match": false,
  "all_forums_with_match": []
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Pulsifi",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Pulsifi",
    "reason": "name 'Pulsifi' appears in message but is not in user's saved_people",
    "source_text": "What is happening in Pulsifi leadership?",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": false,
  "candidate_name": "Pulsifi",
  "resolved_user_id": null,
  "resolved_name": null,
  "resolved_role": null,
  "forum_id": null,
  "forum_name": null,
  "resolution_source": "unresolved",
  "all_forums_with_match": [],
  "user_forum_count": 4,
  "alias_used": null
}
```
</details>

### Child Case

#### Message: `Tell me about Isaac`

- **Winner**: `family_forum` → id=`69dda348de9cb1c83c0780f8`, role=`family`
- **Why**: R3b single-forum match: family_forum ('Yoong family'). No precedence contest needed.

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "69dda348de9cb1c83c0780f8",
  "relationship_role": "family",
  "target_resolution_source": "family_forum",
  "pair_forum_match": false,
  "family_forum_match": true,
  "all_forums_with_match": [
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ]
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Isaac",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Isaac",
    "reason": "name 'Isaac' appears in message but is not in user's saved_people",
    "source_text": "Tell me about Isaac",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": "Isaac",
  "resolved_user_id": "69dda348de9cb1c83c0780f8",
  "resolved_name": "Isaac Yoong",
  "resolved_role": "family",
  "forum_id": "69dda348de9cb1c83c0780fa",
  "forum_name": "Yoong family",
  "resolution_source": "family_forum",
  "all_forums_with_match": [
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ],
  "user_forum_count": 4,
  "alias_used": "isaac\u2192isaac yoong"
}
```
</details>

#### Message: `Tell me about Thaddeus`

- **Winner**: `family_forum` → id=`69dd0b2cc92ba973f8838c11`, role=`family`
- **Why**: R3b single-forum match: family_forum ('Yoong family'). No precedence contest needed.

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "69dd0b2cc92ba973f8838c11",
  "relationship_role": "family",
  "target_resolution_source": "family_forum",
  "pair_forum_match": false,
  "family_forum_match": true,
  "all_forums_with_match": [
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ]
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Thaddeus",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Thaddeus",
    "reason": "name 'Thaddeus' appears in message but is not in user's saved_people",
    "source_text": "Tell me about Thaddeus",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": "Thaddeus",
  "resolved_user_id": "69dd0b2cc92ba973f8838c11",
  "resolved_name": "Thaddeus Yoong",
  "resolved_role": "family",
  "forum_id": "69dda348de9cb1c83c0780fa",
  "forum_name": "Yoong family",
  "resolution_source": "family_forum",
  "all_forums_with_match": [
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ],
  "user_forum_count": 4,
  "alias_used": "thaddeus\u2192thaddeus yoong"
}
```
</details>

#### Message: `What does Thaddeus need from me right now?`

- **Winner**: `family_forum` → id=`69dd0b2cc92ba973f8838c11`, role=`family`
- **Why**: R3b single-forum match: family_forum ('Yoong family'). No precedence contest needed.

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "69dd0b2cc92ba973f8838c11",
  "relationship_role": "family",
  "target_resolution_source": "family_forum",
  "pair_forum_match": false,
  "family_forum_match": true,
  "all_forums_with_match": [
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ]
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Thaddeus",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Thaddeus",
    "reason": "name 'Thaddeus' appears in message but is not in user's saved_people",
    "source_text": "What does Thaddeus need from me right now?",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": "Thaddeus",
  "resolved_user_id": "69dd0b2cc92ba973f8838c11",
  "resolved_name": "Thaddeus Yoong",
  "resolved_role": "family",
  "forum_id": "69dda348de9cb1c83c0780fa",
  "forum_name": "Yoong family",
  "resolution_source": "family_forum",
  "all_forums_with_match": [
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ],
  "user_forum_count": 4,
  "alias_used": "thaddeus\u2192thaddeus yoong"
}
```
</details>

### Ambiguous Name Cases

#### Message: `Mel`

- **Winner**: `pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b matched in 2 forums; sorted by priority (pair_forum=0 > family_forum=1 > forum_member=2). Winner: pair_forum ('Pete & Mel'). Defeated: family_forum ('Yoong family').

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "pair_forum",
  "pair_forum_match": true,
  "family_forum_match": true,
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ]
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Mel",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Mel",
    "reason": "name 'Mel' appears in message but is not in user's saved_people",
    "source_text": "Mel",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": "Mel",
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "pair_forum",
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ],
  "user_forum_count": 4,
  "alias_used": "mel\u2192email:melissa.mars"
}
```
</details>

#### Message: `Melissa`

- **Winner**: `pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b matched in 2 forums; sorted by priority (pair_forum=0 > family_forum=1 > forum_member=2). Winner: pair_forum ('Pete & Mel'). Defeated: family_forum ('Yoong family').

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "pair_forum",
  "pair_forum_match": true,
  "family_forum_match": true,
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ]
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Melissa",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Melissa",
    "reason": "name 'Melissa' appears in message but is not in user's saved_people",
    "source_text": "Melissa",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": "Melissa",
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "pair_forum",
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ],
  "user_forum_count": 4,
  "alias_used": "melissa\u2192email:melissa.mars"
}
```
</details>

#### Message: `wife`

- **Winner**: `alias_spouse_via_pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b single-forum match: alias_spouse_via_pair_forum ('Pete & Mel'). No precedence contest needed.

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "alias_spouse_via_pair_forum",
  "pair_forum_match": false,
  "family_forum_match": false,
  "all_forums_with_match": []
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": null,
  "missing_data": [],
  "conflicts": [],
  "proposed_action": null
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": null,
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "alias_spouse_via_pair_forum",
  "all_forums_with_match": [],
  "user_forum_count": 4,
  "alias_used": "wife"
}
```
</details>

#### Message: `spouse`

- **Winner**: `alias_spouse_via_pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b single-forum match: alias_spouse_via_pair_forum ('Pete & Mel'). No precedence contest needed.

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "alias_spouse_via_pair_forum",
  "pair_forum_match": false,
  "family_forum_match": false,
  "all_forums_with_match": []
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": null,
  "missing_data": [],
  "conflicts": [],
  "proposed_action": null
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": null,
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "alias_spouse_via_pair_forum",
  "all_forums_with_match": [],
  "user_forum_count": 4,
  "alias_used": "spouse"
}
```
</details>

#### Message: `partner`

- **Winner**: `alias_spouse_via_pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b single-forum match: alias_spouse_via_pair_forum ('Pete & Mel'). No precedence contest needed.

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "alias_spouse_via_pair_forum",
  "pair_forum_match": false,
  "family_forum_match": false,
  "all_forums_with_match": []
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": null,
  "missing_data": [],
  "conflicts": [],
  "proposed_action": null
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": null,
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "alias_spouse_via_pair_forum",
  "all_forums_with_match": [],
  "user_forum_count": 4,
  "alias_used": "partner"
}
```
</details>

### Failure Tests

#### Message: `Tell me about Zephyrina`

- **Winner**: `unresolved` → id=`None`, role=`None`
- **Why**: UNRESOLVED — name not in saved_people, not in any of the user's forums, and no spouse-alias matched a pair-forum.

**Telemetry**:
```json
{
  "target_resolved": false,
  "resolved_target_id": null,
  "relationship_role": null,
  "target_resolution_source": "unresolved",
  "pair_forum_match": false,
  "family_forum_match": false,
  "all_forums_with_match": []
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Zephyrina",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Zephyrina",
    "reason": "name 'Zephyrina' appears in message but is not in user's saved_people",
    "source_text": "Tell me about Zephyrina",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": false,
  "candidate_name": "Zephyrina",
  "resolved_user_id": null,
  "resolved_name": null,
  "resolved_role": null,
  "forum_id": null,
  "forum_name": null,
  "resolution_source": "unresolved",
  "all_forums_with_match": [],
  "user_forum_count": 4,
  "alias_used": null
}
```
</details>

#### Message: `Tell me about Pet`

- **Winner**: `unresolved` → id=`None`, role=`None`
- **Why**: UNRESOLVED — name not in saved_people, not in any of the user's forums, and no spouse-alias matched a pair-forum.

**Telemetry**:
```json
{
  "target_resolved": false,
  "resolved_target_id": null,
  "relationship_role": null,
  "target_resolution_source": "unresolved",
  "pair_forum_match": false,
  "family_forum_match": false,
  "all_forums_with_match": []
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Pet",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Pet",
    "reason": "name 'Pet' appears in message but is not in user's saved_people",
    "source_text": "Tell me about Pet",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": false,
  "candidate_name": "Pet",
  "resolved_user_id": null,
  "resolved_name": null,
  "resolved_role": null,
  "forum_id": null,
  "forum_name": null,
  "resolution_source": "unresolved",
  "all_forums_with_match": [],
  "user_forum_count": 4,
  "alias_used": null
}
```
</details>

#### Message: `Mel or Melissa?`

- **Winner**: `pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b matched in 2 forums; sorted by priority (pair_forum=0 > family_forum=1 > forum_member=2). Winner: pair_forum ('Pete & Mel'). Defeated: family_forum ('Yoong family').

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "pair_forum",
  "pair_forum_match": true,
  "family_forum_match": true,
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ]
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Mel",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Mel",
    "reason": "name 'Mel' appears in message but is not in user's saved_people",
    "source_text": "Mel or Melissa?",
    "confidence": 0.45
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": "Mel",
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "pair_forum",
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ],
  "user_forum_count": 4,
  "alias_used": "mel\u2192email:melissa.mars"
}
```
</details>

## 8. Precedence Validation — Examples of Each Tier

### Tier 0 — saved_people wins

#### Message: `Tell me about Mel`

- **Winner**: `saved_people` → id=`697ec826ad4b18f75bf42616`, role=`spouse`
- **Why**: saved_people MATCH (priority 0) — name found in user's explicit saved_people list; role=spouse; resolution_path=['mentioned_name'].

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "spouse",
  "target_resolution_source": "saved_people",
  "pair_forum_match": false,
  "family_forum_match": false,
  "all_forums_with_match": []
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": "697ec826ad4b18f75bf42616",
  "role": "spouse",
  "resolution_path": [
    "mentioned_name"
  ],
  "target_unresolved_name": null,
  "missing_data": [],
  "conflicts": [],
  "proposed_action": null
}
```
</details>

### Tier 1 — pair_forum wins

#### Message: `Tell me about Mel`

- **Winner**: `pair_forum` → id=`697ec826ad4b18f75bf42616`, role=`partner`
- **Why**: R3b matched in 2 forums; sorted by priority (pair_forum=0 > family_forum=1 > forum_member=2). Winner: pair_forum ('Pete & Mel'). Defeated: family_forum ('Yoong family').

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "697ec826ad4b18f75bf42616",
  "relationship_role": "partner",
  "target_resolution_source": "pair_forum",
  "pair_forum_match": true,
  "family_forum_match": true,
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ]
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Mel",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Mel",
    "reason": "name 'Mel' appears in message but is not in user's saved_people",
    "source_text": "Tell me about Mel",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": "Mel",
  "resolved_user_id": "697ec826ad4b18f75bf42616",
  "resolved_name": "Mel",
  "resolved_role": "partner",
  "forum_id": "69dd05eaa333335fcbf3ad33",
  "forum_name": "Pete & Mel",
  "resolution_source": "pair_forum",
  "all_forums_with_match": [
    {
      "forum_id": "69dd05eaa333335fcbf3ad33",
      "forum_name": "Pete & Mel",
      "source": "pair_forum",
      "role": "partner"
    },
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ],
  "user_forum_count": 4,
  "alias_used": "mel\u2192email:melissa.mars"
}
```
</details>

### Tier 2 — family_forum wins

#### Message: `Tell me about Isaac`

- **Winner**: `family_forum` → id=`69dda348de9cb1c83c0780f8`, role=`family`
- **Why**: R3b single-forum match: family_forum ('Yoong family'). No precedence contest needed.

**Telemetry**:
```json
{
  "target_resolved": true,
  "resolved_target_id": "69dda348de9cb1c83c0780f8",
  "relationship_role": "family",
  "target_resolution_source": "family_forum",
  "pair_forum_match": false,
  "family_forum_match": true,
  "all_forums_with_match": [
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ]
}
```

<details><summary>V2 router trace</summary>

```json
{
  "target": null,
  "role": null,
  "resolution_path": [
    "none"
  ],
  "target_unresolved_name": "Isaac",
  "missing_data": [
    "target_unresolved"
  ],
  "conflicts": [],
  "proposed_action": {
    "type": "add_to_circle",
    "suggested_name": "Isaac",
    "reason": "name 'Isaac' appears in message but is not in user's saved_people",
    "source_text": "Tell me about Isaac",
    "confidence": 0.55
  }
}
```
</details>

<details><summary>R3b forum fallback trace</summary>

```json
{
  "found": true,
  "candidate_name": "Isaac",
  "resolved_user_id": "69dda348de9cb1c83c0780f8",
  "resolved_name": "Isaac Yoong",
  "resolved_role": "family",
  "forum_id": "69dda348de9cb1c83c0780fa",
  "forum_name": "Yoong family",
  "resolution_source": "family_forum",
  "all_forums_with_match": [
    {
      "forum_id": "69dda348de9cb1c83c0780fa",
      "forum_name": "Yoong family",
      "source": "family_forum",
      "role": "family"
    }
  ],
  "user_forum_count": 4,
  "alias_used": "isaac\u2192isaac yoong"
}
```
</details>

## 9. Constraint Compliance

| Flag | Required | Actual |
|---|---|---|
| `INTENT_ROUTER_V2_CUTOVER`         | `false` | `false` |
| `INTENT_ROUTER_V2_ROLLOUT_PERCENT` | `10`    | `10` |
| `RELATIONSHIP_ORCHESTRATION_PROMPT`| `false` | `false` |
| `CROSS_LENS_PROMPT_SURFACE`        | `false` | `false` |
| `INTENT_V2_PROMPT_INJECTION`       | `true`  | `true` |
| `TIMELINE_V2_READ_ENABLED`         | `true`  | `true` |
| `FOUNDER_CONTEXT_ENABLED`          | `true`  | `true` |

## 10. Live Persistence Verification — `mirror_chat_retrieval_receipts`

_During validation, a telemetry gap was discovered: the V2 receipt was being persisted **before** R3b enrichment ran, so `target_resolution_source` and `forum_fallback_resolution` were dropped from the persisted record. The persistence call was moved to **after** the Phase 4 enrichment block in `routers/mirror_chat.py`. Below are the two most-recent receipts for Pete to demonstrate the fix._

### Receipt 1 (most recent)

- `request_id`: `mc-77ea5231-bdad-4e40-97c8-9b610d74c5de`
- `computed_at`: `2026-06-12T07:11:37.686074+00:00`
- `target_resolution_source`: **`family_forum`**
- `forum_fallback_resolution.found`: `True`
- `forum_fallback_resolution.resolution_source`: `family_forum`
- `forum_fallback_resolution.resolved_name`: `Isaac Yoong`
- `forum_fallback_resolution.resolved_role`: `family`
- `forum_fallback_resolution.forum_name`: `Yoong family`
- `relationship_resolution.target`: `69dda348de9cb1c83c0780f8`
- `relationship_resolution.target_name`: `Isaac Yoong`
- `relationship_resolution.role`: `family`
- `relationship_resolution.resolution_source`: `family_forum`

  - `all_forums_with_match`:
```json
[
  {
    "forum_id": "69dda348de9cb1c83c0780fa",
    "forum_name": "Yoong family",
    "source": "family_forum",
    "role": "family"
  }
]
```

### Receipt 2 (#2)

- `request_id`: `mc-99453607-4823-4486-9e0e-28035d2f3a90`
- `computed_at`: `2026-06-12T07:11:33.678210+00:00`
- `target_resolution_source`: **`pair_forum`**
- `forum_fallback_resolution.found`: `True`
- `forum_fallback_resolution.resolution_source`: `pair_forum`
- `forum_fallback_resolution.resolved_name`: `Mel`
- `forum_fallback_resolution.resolved_role`: `partner`
- `forum_fallback_resolution.forum_name`: `Pete & Mel`
- `relationship_resolution.target`: `697ec826ad4b18f75bf42616`
- `relationship_resolution.target_name`: `Mel`
- `relationship_resolution.role`: `partner`
- `relationship_resolution.resolution_source`: `pair_forum`

  - `all_forums_with_match`:
```json
[
  {
    "forum_id": "69dd05eaa333335fcbf3ad33",
    "forum_name": "Pete & Mel",
    "source": "pair_forum",
    "role": "partner"
  },
  {
    "forum_id": "69dda348de9cb1c83c0780fa",
    "forum_name": "Yoong family",
    "source": "family_forum",
    "role": "family"
  }
]
```
