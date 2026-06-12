# PFS-2.4 — Role / Bucket / Telemetry Distribution

**Source:** raw scan output captured to
`/app/backend/audit_reports/PFS24_OBSERVATION_SCAN.txt`.
**Receipts scanned:** 101 (pre + post PFS-2.3).
**Post-PFS-2.3 (`v1.1.0`) receipts:** 8.

---

## 1. `rule_bucket` distribution (all 101 receipts)

```
self        : 30
(missing)   : 71   ← pre-PFS-2.1/2.3 receipts; no orchestration block written
```

Of the 30 with a populated bucket:
* **2** → `spouse`     (the 2 Mel traces, both v1.1.0)
* **28** → `self`      (mix of v1.0.0 and v1.1.0; details below)

## 2. `framing_hint` distribution

```
self_inquiry : 30
(missing)    : 71
```

Will be `couple_dynamic / parenting / cofounder_strategic / …` only
when the corresponding topology edge exists. In Preview that's only
`couple_dynamic` (spouse).

## 3. `domain_bias` distribution (PFS-2.3 new field)

```
relationship : 2   ← both Mel traces
self         : 6   ← v1.1.0 receipts with no target / unknown_role_token
(missing)    : 93  ← pre-PFS-2.3 receipts; the field didn't exist yet
```

## 4. `topology_role_type` distribution (PFS-2.1 new field)

```
spouse : 2
```

**Only `spouse` is observable in this environment.** This matches the
`forum_relationship_edges` content exactly (2 spouse edges).

## 5. `topology_role_found` distribution

```
true   :  2
false  :  1   ← Isaac receipt
None   : 98  ← receipts pre-PFS-2.1 OR receipts where the resolver
                returned no target (legitimate `null` state)
```

## 6. `replanned_after_topology` distribution (PFS-2.3 plumbing fix)

```
true   :  3   ← 2 Mel + 1 Isaac fallback (re-plan ran, landed on self)
None   : 98  ← either pre-PFS-2.3 or no target resolved
```

The `replanned_after_topology=true` count (3) > `topology_role_found=true`
count (2) by exactly one — that's the Isaac case where the resolver
found a target via PFS-1 fallback (no topology) and the re-plan still
fired to keep the receipt deterministic. **Expected behaviour.**

## 7. `resolution_source` distribution

```
pair_forum    :  5   ← 2 fresh Mel traces + 3 earlier R3b-only Mel traces
family_forum  :  3   ← 1 fresh Isaac + 2 earlier R3b-only Isaac/Thaddeus
(missing)     : 93
```

## 8. Most-frequent `target_name` observations

```
Mel             : 5
Isaac Yoong     : 2
Thaddeus Yoong  : 1
```

No other names ever resolved in Preview. (Synthetic probes for
"Lu" / "Sandra" / cofounder / advisor all returned `target=None`.)

## 9. `unknown_role_token` events

```
self:unknown_role_token:family   ×1   (Isaac trace)
```

This is the *only* token that falls outside the PFS-2.3 lexicon in
Preview. It is documented and expected behaviour — `family` is a
PFS-1 heuristic forum-level aggregate, not a topology `role_type`.

## 10. Self-fallback with bound target (potential lexicon gaps)

9 receipts have `bucket=self` AND a bound `target`. Of these:
* 1 is the documented Isaac case (PFS-1 `family` token).
* The other 8 are pre-PFS-2.1 receipts that pre-date the topology code
  entirely — their `relationship_resolution.target` was set via the V2
  router's saved_people path, and the orchestration block (where it
  exists at all) is v1.0.0 with no topology awareness.

No new lexicon gaps were introduced by PFS-2.3.

## 11. `forum_relationship_edges` health (Preview)

```
edges_total            : 2
high_confidence_edges  : 2
explicit_edges (inferred=false) : 2
distinct_role_types    : ["spouse"]
```

This is the proximate cause of the entire observation gap. Without
edges for `child`, `cofounder`, `mentor`, `advisor`, `investor`,
etc. there is nothing in Preview to exercise those buckets.

## Conclusion

Distribution data is consistent with environmental expectations.
PFS-2.3 telemetry is faithfully written. The *content* of the
distribution is dominated by Preview's data sparsity — not by any
defect in the resolver or the orchestrator.
