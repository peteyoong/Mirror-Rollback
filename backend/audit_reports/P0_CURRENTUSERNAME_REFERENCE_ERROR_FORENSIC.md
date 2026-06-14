# P0 — `currentUserName` ReferenceError — Forensic Report

**Date:** 2026-06-14
**Build:** `v5.0.1-20260514_120951-hotfix`
**Bundle:** `entry-b3cdf036630b6f659f0a728a5bb5b997.js`
**Bundle SHA-256:** `6377fa2cf4028dffc27ee971558997eeb579284896911c8d591f1a6361a98152`
**Status:** **Root cause confirmed.** No patch applied (per directive).

---

## 1. TL;DR

A single, undeclared identifier — `currentUserName` — is referenced inside the
BaZi Evidence Layer V2 renderer in **`/app/frontend/app/forums/mappings.tsx`**
at **line 929**. When the BaZi Evidence Layer V2 block renders, the JavaScript
engine evaluates the reference and throws a `ReferenceError`, which the React
Error Boundary catches and presents as *"Something went wrong / Can't find
variable: currentUserName"*.

The bug exists **only in `forums/mappings.tsx`**. It does **not** exist in
`components/RelationshipInsightV2Card.tsx` (the actual "Relationship Insight
V2" component — verified clean).

User-named surfaces ("Why This Relationship Matters", "What BaZi Sees Here",
"Core Dynamic", "Growth Edge", "Shadow Pattern") all live inside the **same
`renderDetailModal()`** in `forums/mappings.tsx`. Tapping any of them mounts
the modal, which **also** renders the broken Evidence Layer block immediately
beneath those sections — so any tap that opens the modal crashes the screen.
Hence the user's "tap Why This Relationship Matters → crash" observation.

---

## 2. Exact offending location

```
File:  /app/frontend/app/forums/mappings.tsx
Line:  929
Code:  const nameA = currentUserName || 'You';
```

Surrounding context (lines 922–931, the BaZi Evidence Layer V2 renderer block):

```tsx
// eslint-disable-next-line @typescript-eslint/no-var-requires
const EL      = require('../../services/bazi/evidenceLabels');
const cycle   = diag.cycle           || 'unknown';
const elA     = diag.element_a       || '?';
const elB     = diag.element_b       || '?';
const animA   = diag.animal_a        || '';
const animB   = diag.animal_b        || '';
const animRel = diag.animal_relation || 'unknown';
const nameA   = currentUserName      || 'You';      // ← LINE 929 — UNDECLARED
const nameB   = selectedMember?.member_name || 'Them';
```

The reference is to an identifier that is **never declared anywhere in the
file or in any imported module**. In ES-module strict mode (used by Metro for
all `.tsx` output), an unresolvable identifier throws a `ReferenceError` at
evaluation time, not at parse time — which is why the bundle ships with no
build error but crashes the first time the renderer runs.

Search proof (read-only):

```
$ grep -rn "currentUserName" /app/frontend --include="*.tsx" --include="*.ts" \
      | grep -v node_modules
/app/frontend/app/forums/mappings.tsx:929:  const nameA = currentUserName || 'You';
                                ↑
        ONE and only one occurrence in the entire frontend source tree.
        Never declared, never imported, never destructured.
```

Bundle proof:

```
$ grep -oc "currentUserName" entry-b3cdf036630b6f659f0a728a5bb5b997.js
1
@2778191: ...b=currentUserName||'You',w=F?.member_name||'Them',...
```

The bundle carries the identifier verbatim (minified to `b`), confirming the
bug shipped exactly as written in source.

---

## 3. Why the user sees it under "Relationship Insight V2"

The string labels named in the bug report — **Why This Relationship Matters,
What BaZi Sees Here, Core Dynamic, Growth Edge, Shadow Pattern** — are all
declared at one site:

```
/app/frontend/app/forums/mappings.tsx:866  { key: 'core_dynamic',     label: 'Core Dynamic' }
/app/frontend/app/forums/mappings.tsx:867  { key: 'what_strengthens', label: 'What Strengthens This Relationship' }
/app/frontend/app/forums/mappings.tsx:868  { key: 'growth_edge',      label: 'Growth Edge' }
/app/frontend/app/forums/mappings.tsx:869  { key: 'shadow_pattern',   label: 'Shadow Pattern' }
/app/frontend/app/forums/mappings.tsx:870  { key: 'why_matters',      label: 'Why This Relationship Matters' }
/app/frontend/app/forums/mappings.tsx:871  { key: 'what_bazi_sees',   label: 'What BaZi Sees Here' }
```

These six are the "BAZI DYNAMICS" (Wisdom-Mode V3) narrative sections in the
detail modal. **Tapping any of them does not toggle a sub-view** — they are
text rows that are already rendered. The crash is triggered by the *modal
mounting*, because the BaZi Evidence Layer V2 block (lines 902–1056) renders
immediately below those rows, regardless of which row the user thought they
were tapping.

`components/RelationshipInsightV2Card.tsx` (the actual `relationship-insight`
route component) does **not** reference `currentUserName`:

```
$ grep -n "currentUserName" /app/frontend/components/RelationshipInsightV2Card.tsx
(0 results)
```

The V2 card uses `data.you_name || 'You'` for the viewer name (line ~383
in source). It is **NOT** part of this crash.

---

## 4. Render path that triggers the crash

```
User taps "View detail" on Mel in the forum mappings list
    │
    ▼
ForumMappingsScreen.handleMemberPress(mapping)        (mappings.tsx:66)
    │
    ▼  setSelectedMember(mapping)
ForumMappingsScreen re-renders the detail modal
    │
    ▼
renderDetailModal()                                    (mappings.tsx:239)
    │
    │ ── renders Wisdom-Mode V3 narrative sections
    │     (lines 860-898 — "BAZI DYNAMICS" block, 6 rows including
    │      "Why This Relationship Matters", "Core Dynamic", etc.)
    │
    ▼
{/* MARKER: bazi-evidence-layer-v2 */}                (mappings.tsx:901)
    │
    ▼
IIFE at line 902 — "BAZI EVIDENCE LAYER v2" renderer
    │
    │ ── extracts diag from signals.bazi.diagnostics
    │ ── declares cycle, elA, elB, animA, animB, animRel
    │
    ▼
LINE 929:  const nameA = currentUserName || 'You';
    │
    ▼
JS engine: ReferenceError — "Can't find variable: currentUserName"
    │
    ▼
React Error Boundary catches → "Something went wrong"
```

---

## 5. Variable available vs variable expected

The lexical scope at line 929 (inside `renderDetailModal()` inside
`ForumMappingsScreen()`) has access to:

| Identifier in scope     | Source                                  | Suitable as viewer name? |
| ----------------------- | --------------------------------------- | :----------------------: |
| `user`                  | `useAppStore()` at line 29              | ✅ — has `.name?: string`  (definitive) |
| `user?.id`              | derived                                 | ❌ — not a display name              |
| `theme`, `isDark`       | `useTheme()` at line 28                 | ❌                                   |
| `forumId`, `forumName`  | `useLocalSearchParams()` at line 31     | ❌                                   |
| `selectedMember`        | useState at line 36                     | ❌ — this is the **OTHER** person     |
| `mappings`              | useState at line 33                     | ❌                                   |
| `currentUserName`       | **NOT DECLARED**                         | n/a — this is the bug    |

Canonical `User` type (`/app/frontend/store/index.ts:86`):

```ts
interface User {
    id: string;
    name?: string;                // ← viewer display name
    birth_date: string;
    birth_time?: string;
    birth_location: { ... };
    ...
}
```

Existing usage of `user?.name`-style access already appears 4 times in the
same file (lines 40, 43, 46, 295) — i.e. the canonical pattern is well-
established in this file.

---

## 6. Candidate fixes ranked

The user listed five candidates. Each evaluated against the bug context:

| #  | Candidate                         | Available in scope? | Verdict / safety                                                 |
| -- | --------------------------------- | :-----------------: | --------------------------------------------------------------- |
| 1  | `you_name`                        | ❌                  | Not in scope. (V2 endpoint exposes `you_name`, but the
                                                                   forum-mappings endpoint does not include a top-level
                                                                   `you_name` on each mapping row.)                              |
| 2  | `viewer_name`                     | ❌                  | Never declared anywhere in the project.                          |
| 3  | `currentUser?.name`               | ❌                  | `currentUser` is also not in scope here. (Pattern used elsewhere
                                                                   but with a different store binding.)                           |
| 4  | `relationship.you_name`           | ❌                  | No `relationship` variable in `renderDetailModal` scope.         |
| 5  | **`user?.name`**                  | **✅**              | **Already used 4× in this same file** (lines 40, 43, 46, 295).
                                                                   Matches the canonical `User` interface. Defensive against
                                                                   undefined.                                                     |

**Safest fix (RECOMMENDED, not applied):**

```tsx
const nameA = user?.name || 'You';
```

Why this is safe:
1. `user` is already destructured from `useAppStore()` at the top of the
   component (line 29) and is *guaranteed in scope* at line 929.
2. The `?.name` chain is defensive against the brief moment between
   component mount and session restore where `user` could be `null`.
3. The `|| 'You'` fallback exactly matches the original intent
   (the literal string `'You'` was already in the broken expression).
4. The change is a **one-line, one-token** patch with no side effects
   anywhere else in the render tree.
5. No backend change, no API contract change, no flag change, no schema
   change.

A **defence-in-depth secondary option** would be:

```tsx
const nameA = user?.name || user?.first_name || 'You';
```

But `first_name` is not on the canonical `User` interface, so the primary
single-token fix is preferred for minimum risk.

---

## 7. Blast radius if patched

The line 929 change affects **only** the visible label of the first column of
the "Direction of Flow" rows inside the BaZi Evidence Layer V2 block. With
`user?.name` present, the user sees their real name (e.g. "Pete"); with the
fallback, they see `"You"`. Today, the entire modal crashes — so any
non-throwing value is a strict improvement.

Surfaces affected:
- ✅ `/forums/mappings` detail modal (the crash path) — fixed
- ⬜ All other surfaces — unchanged
- ⬜ `RelationshipInsightV2Card` (`/relationship-insight`) — already correct, **not** touched

No backend / schema / FKR / Ophiuchus / Variant-A / Slice-3 prompt-gate
behaviour is affected.

---

## 8. Reproducibility (per the bug report)

| Step                                                       | Source-trace verification                                                                         |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| "Open Mel relationship card"                               | `app/forums/mappings.tsx` is the route screen for `/forums/mappings`.                              |
| "Open Relationship Insight V2"                             | User naming overlaps; the modal that contains the user-listed labels lives in `forums/mappings.tsx`. |
| "Tap 'Why This Relationship Matters'"                      | Label declared at `mappings.tsx:870`. Tap is a no-op for the row itself — the crash is on modal mount. |
| "App crashes consistently"                                 | Yes — the Evidence Layer block runs on every modal mount.                                          |
| "Re-login does not resolve"                                | Correct — login state has no effect on a `ReferenceError` for a missing identifier.                |
| "Reproduced on mobile Chrome"                              | Browser-agnostic — every modern JS engine throws on undeclared identifier in strict mode.          |

---

## 9. Read-only verification log

```
1. Source grep ............ /app/frontend → 1 occurrence at mappings.tsx:929
2. Bundle grep ............ entry-b3cdf036630b6f659f0a728a5bb5b997.js → 1 occurrence
3. Bundle context ......... "...b=currentUserName||'You',w=F?.member_name||'Them'..."
   (b minified from nameA; w minified from nameB)
4. V2 card scan ........... RelationshipInsightV2Card.tsx → 0 occurrences (clean)
5. Type definition ........ User.name is optional string (store/index.ts:86-94)
6. Existing pattern ....... user?.name|null used 4× in same file (40/43/46/295)
```

No code modified. No bundle rebuilt. No deploy.

---

## 10. Awaiting authorisation

This forensic report is the requested deliverable per the directive
*"Do NOT patch immediately. First produce a forensic report... Confirm root
cause before changing code."*

Awaiting explicit go-ahead before applying the one-line fix:

```diff
- const nameA = currentUserName || 'You';
+ const nameA = user?.name || 'You';
```

Followed by `yarn build:deploy` to produce a new bundle, and a quick smoke
of the detail modal to confirm the crash is gone.
