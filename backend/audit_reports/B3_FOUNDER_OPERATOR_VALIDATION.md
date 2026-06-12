# B3 — Founder/Operator/Spouse/Forum Validation Suite

_Generated: 2026-06-12T03:32:51.821727+00:00_

Re-run of the original June 14 30-prompt suite **after** B3.2 lexicon
expansion, B3.1 educational-mode disambiguation, and P4 forum-topology
plumbing.

## Aggregate accuracy

| Category | Current wiring | P4 wired (`active_member_id` supplied) | Domain mix (current) |
|----------|----------------|-----------------------------------------|----------------------|
| founder  | 100.0% (10/10) | 100.0% (10/10) | {'leadership': 7, 'identity': 1, 'career': 2} |
| spouse   | 100.0% (10/10) | 100.0% (10/10) | {'relationship': 10} |
| forum    |   0.0% (0/10) | 100.0% (10/10) | {'relationship': 10} |

**Overall pass-rate** — current wiring: 66.7%, P4-wired: 100.0%.

## Per-prompt detail (current wiring)

| # | Category | Prompt | Expected ∈ | Actual | Target | Pass |
|---|----------|--------|------------|--------|--------|------|
|  1 | founder  | Should I restructure my leadership team? | {leadership,career,identity} | leadership | — | ✅ |
|  2 | founder  | My cofounder and I disagree about product direction. | {leadership,career,identity} | leadership | — | ✅ |
|  3 | founder  | Should I let this executive go? | {leadership,career,identity} | leadership | — | ✅ |
|  4 | founder  | How do I think about downsizing? | {leadership,career,identity} | leadership | — | ✅ |
|  5 | founder  | Which relationship is creating friction in the company? | {leadership,career,identity} | leadership | — | ✅ |
|  6 | founder  | What is the blind spot in my leadership right now? | {leadership,career,identity} | leadership | — | ✅ |
|  7 | founder  | Am I avoiding a decision? | {leadership,career,identity} | identity | — | ✅ |
|  8 | founder  | Should I prioritize fundraising or profitability? | {leadership,career,identity} | career | — | ✅ |
|  9 | founder  | What dynamic exists between me and my management team? | {leadership,career,identity} | leadership | — | ✅ |
| 10 | founder  | What is the next growth constraint in the business? | {leadership,career,identity} | career | — | ✅ |
| 11 | spouse   | How does Mel map to me right now? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 12 | spouse   | What is happening between me and my spouse? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 13 | spouse   | What tension are we carrying? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 14 | spouse   | What does Mel most need from me? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 15 | spouse   | How do I show up in this relationship? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 16 | spouse   | What relationship pattern keeps repeating? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 17 | spouse   | What should I understand about my partner? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 18 | spouse   | Where are we aligned? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 19 | spouse   | What dynamic is asking for attention? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 20 | spouse   | What is the growth edge in this relationship? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 21 | forum    | Tell me about this forum member. | {relationship,growth} | relationship | — | ❌ |
| 22 | forum    | How does this person map to me? | {relationship,growth} | relationship | — | ❌ |
| 23 | forum    | What role do they play in the group? | {relationship,growth} | relationship | — | ❌ |
| 24 | forum    | What tension exists between us? | {relationship,growth} | relationship | — | ❌ |
| 25 | forum    | What should I understand about this member? | {relationship,growth} | relationship | — | ❌ |
| 26 | forum    | How do I work with them effectively? | {relationship,growth} | relationship | — | ❌ |
| 27 | forum    | What contribution do they bring? | {relationship,growth} | relationship | — | ❌ |
| 28 | forum    | How are they experienced by the forum? | {relationship,growth} | relationship | — | ❌ |
| 29 | forum    | What relationship pattern exists here? | {relationship,growth} | relationship | — | ❌ |
| 30 | forum    | What dynamic is emerging in the forum? | {relationship,growth} | relationship | — | ❌ |

## Per-prompt detail (P4 wired)

| # | Category | Prompt | Expected ∈ | Actual | Target | Pass |
|---|----------|--------|------------|--------|--------|------|
|  1 | founder  | Should I restructure my leadership team? | {leadership,career,identity} | leadership | — | ✅ |
|  2 | founder  | My cofounder and I disagree about product direction. | {leadership,career,identity} | leadership | — | ✅ |
|  3 | founder  | Should I let this executive go? | {leadership,career,identity} | leadership | — | ✅ |
|  4 | founder  | How do I think about downsizing? | {leadership,career,identity} | leadership | — | ✅ |
|  5 | founder  | Which relationship is creating friction in the company? | {leadership,career,identity} | leadership | — | ✅ |
|  6 | founder  | What is the blind spot in my leadership right now? | {leadership,career,identity} | leadership | — | ✅ |
|  7 | founder  | Am I avoiding a decision? | {leadership,career,identity} | identity | — | ✅ |
|  8 | founder  | Should I prioritize fundraising or profitability? | {leadership,career,identity} | career | — | ✅ |
|  9 | founder  | What dynamic exists between me and my management team? | {leadership,career,identity} | leadership | — | ✅ |
| 10 | founder  | What is the next growth constraint in the business? | {leadership,career,identity} | career | — | ✅ |
| 11 | spouse   | How does Mel map to me right now? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 12 | spouse   | What is happening between me and my spouse? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 13 | spouse   | What tension are we carrying? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 14 | spouse   | What does Mel most need from me? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 15 | spouse   | How do I show up in this relationship? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 16 | spouse   | What relationship pattern keeps repeating? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 17 | spouse   | What should I understand about my partner? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 18 | spouse   | Where are we aligned? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 19 | spouse   | What dynamic is asking for attention? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 20 | spouse   | What is the growth edge in this relationship? | {relationship,family,growth} | relationship | mel-001 | ✅ |
| 21 | forum    | Tell me about this forum member. | {relationship,growth} | relationship | kara-001 | ✅ |
| 22 | forum    | How does this person map to me? | {relationship,growth} | relationship | kara-001 | ✅ |
| 23 | forum    | What role do they play in the group? | {relationship,growth} | relationship | kara-001 | ✅ |
| 24 | forum    | What tension exists between us? | {relationship,growth} | relationship | kara-001 | ✅ |
| 25 | forum    | What should I understand about this member? | {relationship,growth} | relationship | kara-001 | ✅ |
| 26 | forum    | How do I work with them effectively? | {relationship,growth} | relationship | kara-001 | ✅ |
| 27 | forum    | What contribution do they bring? | {relationship,growth} | relationship | kara-001 | ✅ |
| 28 | forum    | How are they experienced by the forum? | {relationship,growth} | relationship | kara-001 | ✅ |
| 29 | forum    | What relationship pattern exists here? | {relationship,growth} | relationship | kara-001 | ✅ |
| 30 | forum    | What dynamic is emerging in the forum? | {relationship,growth} | relationship | kara-001 | ✅ |