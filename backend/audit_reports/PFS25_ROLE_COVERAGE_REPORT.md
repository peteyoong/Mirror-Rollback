# PFS-2.5 — Role Coverage Report

**Source:** `scripts/pfs25_graph_audit.py` against Preview (`test_database`).
**Production:** **not measurable from this agent** — see
`PFS24_PRODUCTION_PARITY_REPORT.md` for the environmental caveat.

## 1. Coverage matrix (Preview)

| `role_type`        | Edges in Preview | Resolves to bucket | Framing                  | Domain bias    | Production parity |
|--------------------|------------------|--------------------|---------------------------|----------------|--------------------|
| spouse             | 2                | `spouse`           | couple_dynamic            | relationship   | UNKNOWN |
| former_partner     | 0                | `former_partner`   | closure_dynamic           | relationship   | UNKNOWN |
| child              | 0                | `child`            | parenting                 | relationship   | UNKNOWN |
| parent             | 0                | `parent`           | lineage                   | relationship   | UNKNOWN |
| sibling            | 0                | `sibling`          | family_dynamic            | relationship   | UNKNOWN |
| cofounder          | 0                | `cofounder`        | cofounder_strategic       | work           | UNKNOWN |
| business_partner   | 0                | `cofounder`        | cofounder_strategic       | work           | UNKNOWN |
| advisor            | 0                | `advisor`          | guidance                  | work           | UNKNOWN |
| investor           | 0                | `investor`         | influence                 | work           | UNKNOWN |
| manager            | 0                | `manager`          | authority                 | work           | UNKNOWN |
| employee           | 0                | `employee`         | responsibility            | work           | UNKNOWN |
| collaborator       | 0                | `collaborator`     | partnership               | work           | UNKNOWN |
| mentor             | 0                | `mentor`           | development_giving        | work_self      | UNKNOWN |
| mentee             | 0                | `mentee`           | development_receiving     | self           | UNKNOWN |
| coach              | 0                | `coach`            | growth_giving             | self_work      | UNKNOWN |
| coachee            | 0                | `coachee`          | growth_receiving          | self           | UNKNOWN |
| authority_figure   | 0                | `authority_figure` | power_dynamics            | self_work      | UNKNOWN |
| close_friend       | 0                | `close_friend`     | closeness                 | relationship   | UNKNOWN |
| forum_mate         | 0                | `forum_member`     | forum_member_dynamic      | forum          | UNKNOWN |
| other              | 0                | `forum_member`     | forum_member_dynamic      | forum          | UNKNOWN |

**Lexicon coverage at the code layer is 20 / 20.** Data coverage at
the Preview layer is 1 / 20 — only `spouse` is observable in real edges.

## 2. Per-edge resolved-bucket distribution (Preview)

```
spouse : 2     → bucket=spouse, framing=couple_dynamic, domain_bias=relationship
```

Production distribution: **unknown.**

## 3. Confidence + inference posture (Preview)

```
confidence: high  : 2
confidence: moderate: 0
confidence: low   : 0
inferred: false   : 2   (explicit)
inferred: true    : 0   (none inferred)
```

All Preview edges are high-confidence explicit — the cleanest possible
state. Production may show different ratios; this is the diagnostic to
run first when production data becomes available.

## 4. Special-focus rollup

| Required for PFS-2.4 observation | Preview coverage |
|-----------------------------------|------------------|
| spouse                            | ✅ 2 edges       |
| child                             | ❌ 0 edges       |
| cofounder                         | ❌ 0 edges       |
| advisor                           | ❌ 0 edges       |
| mentor                            | ❌ 0 edges       |
| investor                          | ❌ 0 edges       |
| forum_member / forum_mate         | ❌ 0 edges       |
| close_friend                      | ❌ 0 edges       |

**1 / 8 special-focus categories have observable Preview coverage.**
