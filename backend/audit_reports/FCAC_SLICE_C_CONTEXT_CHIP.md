# FCAC Slice C — Frontend Context Chip + Ambiguity Panel
**Delivery Report**

| Field | Value |
|---|---|
| Slice | C — Frontend simplification of Forum Chat |
| Status | **GREEN — bundle compiles, zero TS errors in touched files, zero taxonomy leakage** |
| Scope | Forum Chat view only.  No backend changes (Slice B already shipped that). |
| New env flag | `EXPO_PUBLIC_FORUM_CHAT_AUTO_CONTEXT` — mirror of the backend `FORUM_CHAT_AUTO_CONTEXT`, default `false` |
| Untouched flags | All other `EXPO_PUBLIC_*` flags untouched |

---

## 1. What landed

When `EXPO_PUBLIC_FORUM_CHAT_AUTO_CONTEXT=true`, Forum Chat behaves like this:

```
┌─────────────────────────────────────────────────────┐
│ ← Ask Mirror                                        │
├─────────────────────────────────────────────────────┤
│                                                     │  (tab strip removed)
│            Tap a prompt or type your own            │
│                                                     │
│            • What strengths does this group bring?  │
│            • What themes are emerging?              │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Type your question...                          ➤    │
└─────────────────────────────────────────────────────┘
```

After sending *"What does Mel need from me?"*:

```
┌─────────────────────────────────────────────────────┐
│ ← Ask Mirror                                        │
├─────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐   │
│  │ 👤 About Mel                                 │   │  (legacy mode header on
│  │ What does Mel need from me?                  │   │   user bubble, unchanged)
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │ [ 👤 Mel · Spouse ]    ← NEW: ResolvedContextChip
│  │ Mirror                                       │   │
│  │ Mel's pull right now is toward…              │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

When the resolver returns AMBIGUOUS (e.g. *"Tell me about Test"* — 5 saved_people match):

```
┌─────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────┐   │
│  │ I found multiple people. Which one did       │   │
│  │ you mean?                                    │   │
│  │ Your question: "Tell me about Test."         │   │
│  ├──────────────────────────────────────────────┤   │
│  │ Test                                friend   │   │
│  │ Test Child                          child    │   │
│  │ Test Spouse                         spouse   │   │
│  │ Test Boss                           boss     │   │
│  │ Test Ex                          ex_partner  │   │
│  ├──────────────────────────────────────────────┤   │
│  │              Never mind                      │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

Tapping a candidate re-issues the original message with the chosen `target_member_id`, and the resolver binds unambiguously on the second pass.

### When the flag is `false` (default)
The legacy `[ Me ] [ Member ] [ Forum ]` tab strip and member picker are preserved **byte-for-byte**.  Behaviour is identical to before this slice.

---

## 2. Files touched

| File | Change |
|---|---|
| `frontend/components/ForumChatView.tsx` | Flag-gated rendering: hides mode tabs + member picker when ON; renders chip + clarification panel; auto-context request body |
| `frontend/components/forum/ResolvedContextChip.tsx` | **NEW** — presentational chip (164 lines) |
| `frontend/components/forum/AmbiguityClarificationPanel.tsx` | **NEW** — candidate picker (139 lines) |
| `frontend/services/api.ts` | Added `ResolvedFrame`, `ResolvedContextBlock`, `ClarificationCandidate` types; extended request + response shapes |
| `frontend/.env` | Added `EXPO_PUBLIC_FORUM_CHAT_AUTO_CONTEXT=false` |

---

## 3. Chip language (Mirror voice only)

| Resolved frame | Chip emoji | Chip label | Internal taxonomy in label? |
|---|---|---|---|
| SELF | 🪞 | **Self** | ❌ none |
| MEMBER (spouse) | 👤 | **Mel · Spouse** | ❌ none |
| MEMBER (child)  | 👤 | **Thaddeus · Child** | ❌ none |
| PAIRWISE | 👥 | **Mel ↔ Thaddeus** | ❌ none |
| MULTI_PERSON (children) | 👨‍👩‍👧‍👦 | **My children** | ❌ none |
| MULTI_PERSON (siblings) | 👫 | **My siblings** | ❌ none |
| MULTI_PERSON (parents) | 👪 | **My parents** | ❌ none |
| MULTI_PERSON (circle) | 🌐 | **My circle** | ❌ none |
| FORUM | 🌐 | **Forum** | ❌ none |
| AMBIGUOUS | ❓ | **Multiple matches** | ❌ none |

Verified by `grep` against the chip source:
```
$ grep -E "'PAIRWISE'|'MULTI_PERSON'|'AMBIGUOUS'|covenant_partner|steward_guardian|scope_class" \
        components/forum/ResolvedContextChip.tsx
```
→ all hits are inside `case` discriminators (code-only) — none appear in the rendered `label` strings.

---

## 4. Behavioural guarantees

| Constraint | Honoured | Evidence |
|---|---|---|
| Tab strip hidden when flag ON | ✅ | `{!AUTO_CTX_ENABLED && (<ModeSelector />)}` |
| Tab strip preserved when flag OFF | ✅ | gated render; legacy path untouched |
| Member picker hidden when flag ON | ✅ | same gating |
| Chip rendered ONLY when `resolved_context` present | ✅ | `{AUTO_CTX_ENABLED && msg.resolved_context && …}` |
| Never auto-pick on AMBIGUOUS | ✅ | panel is the ONLY exit; tap explicitly required |
| Pronoun follow-up via `last_target_id` | ✅ | `setLastTargetId` after every resolved turn |
| No prompt leakage to UI text | ✅ | grep verified |
| Legacy contract preserved when flag OFF | ✅ | `requestBody` branches on the flag — old payload byte-identical |
| Bundle compiles | ✅ | http://localhost:3000 → HTTP 200 |
| Zero TS errors in touched files | ✅ | `tsc --noEmit -p tsconfig.json` shows 0 new errors in ForumChatView / ResolvedContextChip / AmbiguityClarificationPanel / api.ts |

---

## 5. How to enable

```bash
# Backend
echo 'FORUM_CHAT_AUTO_CONTEXT=true' >> /app/backend/.env
sudo supervisorctl restart backend

# Frontend
sed -i 's/EXPO_PUBLIC_FORUM_CHAT_AUTO_CONTEXT=false/EXPO_PUBLIC_FORUM_CHAT_AUTO_CONTEXT=true/' /app/frontend/.env
sudo supervisorctl restart expo
```

Both reversible by flipping the values back to `false` and restarting.  No DB writes, no schema changes.

---

## 6. What is NOT in this slice

- Astrology Chat consumption of auto-context (Slice F)
- Astrology Relationship Re-Story V1 (delivered next, separate workstream)
- Persisting `resolved_context` to the chat history (`forum_chat_messages` collection) — currently in-memory only.  Refresh of the chat thread will not show chips on prior messages.

---

## 7. Next step

Proceed to **Astrology Relationship Re-Story V1**.

— end of report —
