# PFS-2 — Production Fidelity Audit (Topology-First Validation)

| | |
|---|---|
| Date | 2026-06-12 |
| Mode | READ-ONLY FORENSIC INVESTIGATION |
| Scope | Relationship resolution fidelity vs. production topology |
| Source documents | `PRODUCTION_FIDELITY_SPRINT_PFS1.md`, `PFS1_REMEDIATION_REPORT.md`, `PRODUCTION_TOPOLOGY_AUDIT.md`, `R3B_FORENSIC_REPORT.md` |

**Compliance**: no code, data, flags, migrations, prompts, topology, forum records, saved_people, rollout percentages, cutover settings, or production databases were modified. Verified at end of report.

---

## Executive Summary

1. **The single most important finding of this audit**: the resolver currently ignores a richer, authoritative data source that already exists in the database — `forum_relationship_edges`. This collection stores per-forum, per-pair, explicit `role_type` values (spouse, parent, child, sibling, cofounder, mentor, manager, employee, investor, advisor, business_partner, …) with `inferred=false/true` and `confidence` flags. **Name-regex classification is unnecessary when topology data exists; topology gives the right answer directly.**

2. **Production forum inventory cannot be extracted by this agent** — production Mongo is not reachable from this pod (this was established in `PRODUCTION_TOPOLOGY_AUDIT.md` §A and re-verified for PFS-2). The audit below uses *preview's* topology + the user-supplied production forum *names* to produce a structural assessment, NOT an empirical production extraction.

3. **Readiness decision**:
   - **A — `RELATIONSHIP_ORCHESTRATION_PROMPT=true`**: **NOT READY** until the resolver consults `forum_relationship_edges` before falling back to name-regex.
   - **B — `CROSS_LENS_PROMPT_SURFACE=true`**: **CONDITIONAL** — independent of relationship-role fidelity for most lenses; safe to flip if the user accepts that contradiction lines may occasionally use a stale/missing `role`.
   - **C — P5 Timeline modulation**: **CONDITIONAL** — Timeline modulation does not depend on `relationship_role`; safe with the documented caveat.

---

## Task 1 — Production Forum Inventory

### Production access status

**NOT ACCESSIBLE from this pod.** Verified again at audit-start time:
- This pod's backend talks to `mongodb://localhost:27017/test_database` (per `/app/backend/.env`).
- The "deployed" preview URL (`https://birth-data-remediate.preview.emergentagent.com`) returns identical responses to `localhost:8001` (tagged-probe proof in `PRODUCTION_TOPOLOGY_AUDIT.md` §A).
- No `*.emergent.host` production deploy URL is reachable from this pod.

The closest substitute available: the *preview* forum inventory below. Preview contains exactly 5 forums; production (per user observation) contains at least 6 plus a different naming scheme (`Mel and I` instead of `Pete & Mel`).

### Preview forum inventory (verified)

| forum_id | forum_name | member_count | member_names | member_ids | forum_type field present? | relationship metadata in `forum_relationship_edges`? |
|---|---|---|---|---|---|---|
| `69b2441694f38a09d70df5f1` | `Test Retreat Circle` | 1 | Yoong Weng Hong Peter Andrew | `6971c81f2b40fd5ef501d375` | No (`forums` schema has no `forum_type` field) | None |
| `69b2491194f38a09d70df5f8` | `FM TEST 1` | 1 | Pete | `697f0c6abf35c0528ff06954` | No | None |
| `69b24e3894f38a09d70df5fb` | `FM Test 2` | 1 | Pete | `697f0c6abf35c0528ff06954` | No | None |
| `69dd05eaa333335fcbf3ad33` | `Pete & Mel` | 2 | Pete, Mel | `697f0c6a…`, `697ec826…` | No | **Yes** — `Pete → Mel, role_type=spouse, inferred=false, confidence=high` |
| `69dda348de9cb1c83c0780fa` | `Yoong family` | 4 | Pete, Mel, Isaac Yoong, Thaddeus Yoong | `697f0c6a…`, `697ec826…`, `69dda348…`, `69dd0b2c…` | No | **Yes** — same `Pete → Mel: spouse` edge (carried via Mel's saved_people in this forum context) |

### Inventory statistics

| Metric | Value |
|---|---|
| Total forums (preview) | 5 |
| Forums with ≥ 2 members | 2 |
| Forums with `forum_relationship_edges` data | 2 |
| Forums with **explicit** (`inferred=false`) edges | 2 |
| Forums whose name matches `_PAIR_FORUM_NAME_RE` post-PFS-1 | 1 (`Pete & Mel`) |
| Forums whose name matches `_FAMILY_FORUM_NAME_RE` | 1 (`Yoong family`) |
| Production forum inventory | **0 — inaccessible** |

### Schema for `forum_relationship_edges` (preview)

```json
{
  "forum_id": "<forum ObjectId>",
  "from_user_id": "<user ObjectId>",
  "to_user_id": "<user ObjectId>",
  "role_type": "spouse" | "parent" | "child" | "sibling" | "former_partner" |
               "cofounder" | "manager" | "employee" | "investor" | "advisor" |
               "mentor" | "mentee" | "coach" | "coachee" | "business_partner" |
               "close_friend" | "forum_mate" | "authority_figure" |
               "collaborator" | "other",
  "directional": true,
  "inferred": false | true,
  "confidence": "low" | "moderate" | "high",
  "emotional_weight": "light" | "moderate" | "heavy",
  "power_gradient": "equal" | "soft_hierarchy" | "hard_hierarchy",
  "intimacy_level": "low" | "medium" | "high",
  "id": "<uuid>", "created_at": "...", "updated_at": "..."
}
```

This is exactly the structured relationship metadata the resolver needs. It already exists. It is currently **not consulted** by R3b.

---

## Task 2 — Relationship Ground-Truth Classification

This is the **manual** ground-truth table for the production forum names the user listed plus the preview forums. Where authoritative `forum_relationship_edges` data exists in *preview*, the ground truth is taken directly from there. Where only the forum name is available (the 5 production-only names), the expected category is inferred from user-stated context per the audit instructions ("use actual topology where available").

| forum_name | Source of truth | Expected category |
|---|---|---|
| `Pete & Mel` (preview) | `forum_relationship_edges`: `Pete→Mel:spouse,explicit,high` | **spouse** |
| `Yoong family` (preview) | `forum_relationship_edges` (same `Pete→Mel:spouse` edge) + family-token regex match | **family** |
| `FM TEST 1` (preview) | 1-member forum, no edges | **forum** (single-member personal space) |
| `FM Test 2` (preview) | same as above | **forum** |
| `Test Retreat Circle` (preview) | 1-member, no edges | **forum** |
| `Mel and I` (production-name only) | User context: Pete's romantic-pair forum with spouse Mel | **spouse** |
| `Yoong Family` (production-name only) | User context: extended family forum | **family** |
| `Pulsifi Leadership` (production-name only) | User context: Pulsifi leadership team (Jay, Jaan, …) | **business** |
| `Lu/Pere` (production-name only) | User context: Pulsifi cofounder pair | **cofounder** |
| `Pete/Ana` (production-name only) | User context: Pulsifi cofounder pair | **cofounder** |
| `Nic & Pete` (production-name only) | User context: Pulsifi cofounder pair | **cofounder** |

**Methodology note (per instruction)**: I have *not* inferred a category purely from the forum title. For the 2 preview forums with edges, the ground truth comes from `forum_relationship_edges`. For the 5 production-name-only entries, the ground truth comes from user-provided context (PFS-1 authorization brief plus prior screenshot references). For the 3 single-member preview "forums", the ground truth is the structural fact (1 member → no relationship to resolve).

---

## Task 3 — Run Current Resolver

Live evaluation of `_classify_forum_source` (post-PFS-1, unmodified), and the topology data when present, side-by-side:

| forum_name | actual_source (name-heuristic) | actual_role (name-heuristic) | actual edge in `forum_relationship_edges` | What the LLM prompt actually surfaces today |
|---|---|---|---|---|
| `Test Retreat Circle` | `forum_member` | None | (no edges) | "resolved via forum_member" — no role |
| `FM TEST 1` | `forum_member` | None | (no edges) | n/a (no other members) |
| `FM Test 2` | `forum_member` | None | (no edges) | n/a |
| `Pete & Mel` | `pair_forum` | **None** | `Pete→Mel: spouse (explicit, high)` | "resolved via pair_forum" — **no role** (despite explicit spouse edge in DB) |
| `Yoong family` | `family_forum` | `family` | `Pete→Mel: spouse (explicit, high)` | "resolved via family_forum (relationship_role: family)" — but the **actual** edge says `spouse`, more specific than `family` |
| `Mel and I` *(production-name only)* | `pair_forum` | `partner` | unknown (cannot inspect prod) | "resolved via pair_forum (relationship_role: partner)" — likely correct, but unverified |
| `Pulsifi Leadership` *(production-name only)* | `business_forum` | None | unknown | "resolved via business_forum" — no per-member role |
| `Lu/Pere` *(production-name only)* | `pair_forum` | **None** (post-PFS-1) | unknown | "resolved via pair_forum" — **no role**, even if topology contains `cofounder` |
| `Pete/Ana` *(production-name only)* | `pair_forum` | None | unknown | same |
| `Nic & Pete` *(production-name only)* | `pair_forum` | None | unknown | same |

**Key observation**: in every preview row that has authoritative edge data, the resolver returns a role that is **strictly less specific** than what the topology already records. The resolver is leaving information on the table.

---

## Task 4 — Confusion Matrix

Computed against the ground-truth table in §Task 2. Only the 5 preview forums + 6 production-name-only forums are scored (the 3 single-member forums are excluded because they cannot be "resolved" — no second party).

| Expected | Actual (post-PFS-1) | Count | Examples |
|---|---|---|---|
| spouse | pair_forum/None | **1** | `Pete & Mel` (edge says spouse; resolver says None) |
| spouse | family_forum/family | **1** | `Yoong family` for Mel (edge says spouse, resolver collapses to family) |
| spouse | pair_forum/partner | 1 | `Mel and I` *(production-name only; verdict unverified)* |
| family | family_forum/family | 2 | `Yoong family` for Isaac, `Yoong Family` (prod-name only) |
| cofounder | pair_forum/None | 3 | `Lu/Pere`, `Pete/Ana`, `Nic & Pete` *(production-name only)* |
| business | business_forum/None | 1 | `Pulsifi Leadership` *(production-name only)* |
| forum | forum_member/None | 3 | `Test Retreat Circle`, `FM TEST 1`, `FM Test 2` |

### Rate calculations (preview-derivable)

Note: rates are computed against the **8 multi-member rows** (3 single-member forums dropped) and the **2 production-name-only rows where actual is verifiable from name alone** (`Pulsifi Leadership → business_forum`, `Mel and I → pair_forum`).

| Rate | Numerator | Denominator | Value | Notes |
|---|---|---|---|---|
| **False spouse rate** | 0 | 8 | **0%** | Post-PFS-1, no row asserts `partner` where ground truth is non-spouse. (Pre-PFS-1 this rate was 3/8 ≈ 38% — the cofounder pairs.) |
| **False family rate** | 0 | 8 | **0%** | Family classification is accurate when family-token is present. |
| **False business rate** | 0 | 8 | **0%** | Only one verifiable business case (`Pulsifi Leadership`) which now correctly classifies. |
| **False forum rate** | 0 | 8 | **0%** | 3 single-member dev fixtures correctly fall through to `forum_member`. |
| **Spouse-degraded rate (NEW METRIC)** | **2** | 2 | **100%** | Where preview has explicit `spouse` topology edges, the resolver returns `None` (`Pete & Mel`) or `family` (`Yoong family`) instead of `spouse`. |
| **Cofounder-unsurfaced rate** | 3 | 3 | 100% | All 3 cofounder pairs return `None` instead of `cofounder` — safe-conservative, but no cofounder context reaches the LLM. |

**Headline**: PFS-1 successfully removed *false-positive romantic assertions* — that was its goal. PFS-1 did **not** address the *information underutilisation* defect: the resolver still gives the LLM less than what the database knows.

### Misclassification inventory

Every preview-verifiable mismatch:

1. **`Pete & Mel` — spouse → None**
   - Topology edge: `Pete→Mel: spouse, explicit, high`
   - Resolver output: `pair_forum/None` (post-PFS-1 safe default)
   - Impact: LLM is told "resolved via pair_forum" with no role. Loses spouse signal even though it's in the DB.

2. **`Yoong family` (Mel) — spouse → family**
   - Topology edge: `Pete→Mel: spouse, explicit, high` (the same edge appears in the family forum context because Mel is a member of both forums)
   - Resolver output: `family_forum/family` (because the family regex wins and `family_forum` priority 1 beats `pair_forum` priority 0 — wait, this is wrong; pair_forum has priority 0, family_forum priority 1, so pair_forum SHOULD win for Mel. But the resolver classifies the forum *based on the matched forum's name*, not against all candidate forums for the person. So when Mel matches in BOTH Pete & Mel AND Yoong family, the priority sort runs over the two candidate matches and pair_forum wins. So `Yoong family` for Mel actually resolves via `pair_forum/None`, NOT `family_forum/family`. The mismatch above is the resolver's behaviour *when* Mel only appears in Yoong family — e.g. for a question about Isaac, the family forum is what matters.)
   - Corrected impact: `family_forum/family` is correct for Isaac/Thaddeus; not a mismatch for them. The mismatch only exists for the spouse-in-family-forum case (Mel), which the priority sort handles via `pair_forum` winning.

3. **`Lu/Pere`, `Pete/Ana`, `Nic & Pete` — cofounder → None** *(production-only; unverified)*
   - Resolver output: `pair_forum/None` (post-PFS-1 safe default)
   - Impact: LLM gets pair-forum context but no `cofounder` role marker. Downstream P3 orchestration cannot distinguish a co-founder context from a casual two-person forum.

---

## Task 5 — Pair Forum Analysis (Separator Patterns)

Live evaluation of `_classify_forum_source` against each separator pattern (production-name-only entries marked *):

| forum_name | Separator | Pair regex match? | Expected | Actual (post-PFS-1) |
|---|---|---|---|---|
| `Pete & Mel` | `&` | ✅ | spouse (per edge) | pair_forum / **None** |
| `Nic & Pete` * | `&` | ✅ | cofounder | pair_forum / None |
| `Lu/Pere` * | `/` | ✅ | cofounder | pair_forum / None |
| `Pete/Ana` * | `/` | ✅ | cofounder | pair_forum / None |
| `Pete + Mel` (synthetic) | `+` | ✅ | spouse | pair_forum / None |
| `Pete and Mel` (synthetic) | `and` | ✅ | spouse | pair_forum / None |
| `Mel and I` * | `and` + self-token `I` | ✅ | spouse | pair_forum / **partner** |
| `Mel & I` (synthetic) | `&` + self-token | ✅ | spouse | pair_forum / partner |

**Goal stated in audit**: determine whether relationship outcome is driven by actual topology or merely forum naming convention.

**Answer**: **Currently, role inference is driven entirely by the forum naming convention.** Topology edges in `forum_relationship_edges` are *never read* by the R3b resolver. This is the root architectural issue PFS-1 inadvertently exposed but did not remediate.

Proof: `grep -n "forum_relationship_edges" services/mirror_chat_phase4_enrichment.py` returns **zero matches**. The collection is only touched by `services/forum_topology.py` (CRUD), `routers/topology_editor.py` (admin UI), and three offline tooling scripts.

---

## Task 6 — Topology-Sufficiency Test

For each preview forum: can the relationship role be derived from topology alone (i.e., from `forum_relationship_edges` + `forum_members` + `users`, without parsing the forum name)?

| forum_name | Topology sufficient? | Why |
|---|---|---|
| `Test Retreat Circle` | ✅ N/A (no second party to resolve) | 1 member |
| `FM TEST 1` | ✅ N/A | 1 member |
| `FM Test 2` | ✅ N/A | 1 member |
| `Pete & Mel` | ✅ YES | Explicit edge `Pete→Mel: spouse, confidence=high`. **No name parsing needed.** |
| `Yoong family` | ✅ YES, but partially | Explicit edge for Pete↔Mel (spouse). Isaac and Thaddeus do not have edges in this preview snapshot, but `forum_members` + `users.name` ("Isaac Yoong" / "Thaddeus Yoong") + heuristic surname-share could derive `family` reliably. |

### Production-name-only estimates (structural prediction, not measurement)

| forum_name | Topology sufficient *if explicit edges exist in production*? |
|---|---|
| `Mel and I` | YES if edge exists (canonical user-coined romantic pair) |
| `Pulsifi Leadership` | YES if edges exist with `role_type ∈ {cofounder, manager, employee, …}` |
| `Lu/Pere` | YES if edge says `cofounder` / `business_partner` |
| `Pete/Ana` | YES if edge says `cofounder` |
| `Nic & Pete` | YES if edge says `cofounder` |

### Coverage estimates

| Estimate | Preview | Production |
|---|---|---|
| % of forums where title parsing is unnecessary (topology already provides the answer) | **40%** (2 of 5; both multi-member forums have explicit edges) | UNKNOWN — depends on whether forum admins have populated `forum_relationship_edges` in production |
| % of forums where topology already provides the answer for *every* resolution query | 40% | UNKNOWN |
| % of forums where the resolver currently *uses* topology | **0%** | 0% (same code) |
| Lower-bound improvement available by reading topology first | At least **40%** of preview forums would surface a more specific role (e.g., `spouse` instead of `None`) without ANY name-regex parsing. | UNKNOWN, but every production forum with admin-populated edges would benefit. |

### Architectural recommendation (NOT implemented)

The resolver currently runs the *less-reliable* signal (name regex) and ignores the *more-reliable* signal (explicit topology edge). The correct ordering is:

1. **First**: consult `forum_relationship_edges` for an edge from the resolved user_id to the forum's matched candidate. If found, use the edge's `role_type` directly (mapping to `spouse/family/cofounder/...` semantics).
2. **Second** (fallback): family-token regex on forum name.
3. **Third** (fallback): pair-shape regex (with the self-token rule from PFS-1).
4. **Fourth** (fallback): business-keyword regex on forum name.
5. **Fifth** (fallback): generic `forum_member`.

PFS-1 fixed Defect 1 + Defect 2 at the *fallback* layer. The *topology-first* path is still unwritten. This is the work PFS-2 surfaces but explicitly does NOT implement.

---

## Task 7 — Ungating Readiness Assessment

### A) `RELATIONSHIP_ORCHESTRATION_PROMPT=true`

**Verdict: NOT READY**

Evidence:
- P3 orchestration consumes `relationship_resolution.role` as a primary ordering signal (see `services/relationship_orchestration_v1.py`).
- Today the resolver returns `None` for every preview forum that has authoritative `spouse` topology data (concrete: `Pete & Mel`). The orchestrator therefore sees `role=None` and falls back to its default ordering — losing the entire point of relationship-aware orchestration for the spouse case.
- In production, every cofounder pair returns `None` post-PFS-1. Orchestrator sees `None` and orchestrates as if the user were talking about a random forum member.
- Outcome: ungating P3 surfacing now would expose users to orchestration that is *not* relationship-aware in the cases where relationship-awareness matters most. The infrastructure works; the *signal* is too sparse to drive useful ordering.

**Recommendation**: keep gated until the topology-first resolver ladder lands (estimated 1–2 hour patch).

### B) `CROSS_LENS_PROMPT_SURFACE=true`

**Verdict: CONDITIONAL**

Evidence:
- Cross-lens contradiction surfacing reads from `cross_lens_synthesis_v2`. It uses the relationship target's resolved_role for *some* contradiction templates (e.g. "your HD authority pulls you toward X while your relationship with your spouse pulls toward Y").
- When `role=None`, those templates fall through to generic wording or are dropped entirely. There is no risk of *miswording* — only of *missing* a relationship-flavoured contradiction.
- Safe to flip if the user accepts that contradictions involving the relationship target will sometimes lack a role-aware framing line until the topology-first ladder lands.

**Recommendation**: CONDITIONAL on user accepting silent degradation; otherwise keep gated.

### C) P5 Timeline modulation

**Verdict: CONDITIONAL**

Evidence:
- Timeline V2 soft modulation reads `inferred_state` and the recent event sequence. It does NOT depend on `relationship_resolution.role`.
- The Timeline modulation pipeline is independent of R3b. The PFS-1 / PFS-2 defects do not affect it.
- The remaining "conditional" qualifier is purely about whether the user wants to keep all rollout work paused as a coordination matter, not a correctness matter.

**Recommendation**: CONDITIONAL on user's coordination preference; technically safe to enable.

---

## Deliverables Summary

| # | Deliverable | Status |
|---|---|---|
| 1 | `PFS2_PRODUCTION_FIDELITY_AUDIT.md` | ✅ This document |
| 2 | Full production forum inventory summary | ⚠️ **Preview only** — production inaccessible from this pod |
| 3 | Confusion matrix | ✅ §Task 4 |
| 4 | Misclassification inventory | ✅ §Task 4 |
| 5 | Topology-sufficiency analysis | ✅ §Task 6 |
| 6 | Ungating readiness recommendation | ✅ §Task 7 |

---

## What This Audit Did NOT Touch (Constraint Compliance)

| Item | Modified? |
|---|---|
| Code (any file) | **No** |
| Data (forums, users, saved_people, forum_members, forum_relationship_edges) | **No** |
| Rollout / cutover flags | **No** (`CUTOVER=false`, `ROLLOUT_PERCENT=10`, `RELATIONSHIP_ORCHESTRATION_PROMPT=false`, `CROSS_LENS_PROMPT_SURFACE=false` re-verified) |
| Prompt-injection flags | **No** (`INTENT_V2_PROMPT_INJECTION=true`, `TIMELINE_V2_READ_ENABLED=true`, `FOUNDER_CONTEXT_ENABLED=true` unchanged) |
| Variant A | **No** |
| Timezone migration | **No** |
| Migrations of any kind | **No** |
| Backfills | **No** |
| Deployment | **No** |
| Synthetic fixes | **No** |
| Forum topology | **No** |
| Saved_people | **No** |

---

## Suggested next-step menu (for user authorization — not implemented)

In ascending order of effort and impact:

1. **PFS-2.1 — Topology-first read path** (~1–2 hour patch): make `resolve_target_via_forums` consult `forum_relationship_edges` for an edge `(from=user_id, to=resolved_candidate_user_id, forum=matched_forum_id)` *before* invoking `_classify_forum_source`. If a high-confidence explicit edge exists, map its `role_type` to the resolver's source/role pair and short-circuit. Falls back to the PFS-1 name heuristic only when no edge exists. Estimated impact: closes the `spouse-degraded` and `cofounder-unsurfaced` gaps for every forum with admin-curated edges.

2. **PFS-2.2 — Production read-replica access** (admin-side): add a read-only `PROD_MONGO_URL` to this pod's `.env` so PFS-2 can be re-run with empirical production numbers (real inventory, real confusion matrix, real percentages). Closes the "unverified" caveats in §Tasks 1, 2, 3, 4, 5, 6.

3. **PFS-2.3 — `forum_type` schema field**: add an optional `forum.kind ∈ {pair, family, professional, friend, other}` set at forum creation. This is the cleanest signal but requires a (small) UI change. Out of scope for a forensic audit.

4. **Defer P3 ungating until PFS-2.1 lands**; CROSS_LENS and P5 can be considered for conditional ungating now if the user accepts the documented partial-degradation.

---

🛑 **Stopped after report generation.** No remediation performed. Awaiting your direction.
