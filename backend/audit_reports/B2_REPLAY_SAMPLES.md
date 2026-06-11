# B2 Replay Samples

_Companion to `B2_READINESS_REPORT.md`._

## Representative success cases (REAL)

- `real` / `chat_history` / frame=`self`
  - **msg**: Tell me about my Saturn return
  - predicted=`identity`  conf=1.0  signal=1.0  margin=1.0
  - routing=`PASS`  retrieval=`PASS`  target=`NOT_APPLICABLE`
- `real` / `forum_chat_messages` / frame=`self`
  - **msg**: how am I showing up?
  - predicted=`identity`  conf=0.7  signal=0.7  margin=1.0
  - routing=`PASS`  retrieval=`PASS`  target=`NOT_APPLICABLE`
- `real` / `forum_chat_messages` / frame=`self`
  - **msg**: how am I showing up?
  - predicted=`identity`  conf=0.7  signal=0.7  margin=1.0
  - routing=`PASS`  retrieval=`PASS`  target=`NOT_APPLICABLE`
- `real` / `forum_chat_messages` / frame=`self`
  - **msg**: Tell me about Mel’s 4th house
  - predicted=`relationship`  conf=0.6905  signal=1.0  margin=0.381
  - routing=`PASS`  retrieval=`PASS`  target=`UNRESOLVED_NAMED`  - proposed_action: `{'type': 'add_to_circle', 'suggested_name': 'Mel', 'reason': "name 'Mel' appears in message but is not in user's saved_people", 'source_text': 'Tell me about Mel’s 4th house', 'confidence': 0.55}`
- `real` / `forum_chat_messages` / frame=`self`
  - **msg**: Tell me about Mel’s 4th house
  - predicted=`relationship`  conf=0.6905  signal=1.0  margin=0.381
  - routing=`PASS`  retrieval=`PASS`  target=`UNRESOLVED_NAMED`  - proposed_action: `{'type': 'add_to_circle', 'suggested_name': 'Mel', 'reason': "name 'Mel' appears in message but is not in user's saved_people", 'source_text': 'Tell me about Mel’s 4th house', 'confidence': 0.55}`
- `real` / `forum_chat_messages` / frame=`self`
  - **msg**: Can you tell me about Mel’s 4th house please?
  - predicted=`relationship`  conf=0.6905  signal=1.0  margin=0.381
  - routing=`PASS`  retrieval=`PASS`  target=`UNRESOLVED_NAMED`  - proposed_action: `{'type': 'add_to_circle', 'suggested_name': 'Mel', 'reason': "name 'Mel' appears in message but is not in user's saved_people", 'source_text': 'Can you tell me about Mel’s 4th house please?', 'confidence': 0.55}`
- `real` / `forum_chat_messages` / frame=`self`
  - **msg**: Tell me about Mel's 4th house and how does that map to me?
  - predicted=`relationship`  conf=0.7797  signal=1.0  margin=0.5593
  - routing=`PASS`  retrieval=`PASS`  target=`UNRESOLVED_NAMED`  - proposed_action: `{'type': 'add_to_circle', 'suggested_name': 'Mel', 'reason': "name 'Mel' appears in message but is not in user's saved_people", 'source_text': "Tell me about Mel's 4th house and how does that map to me?", 'confidence': 0.55}`
- `real` / `forum_chat_messages` / frame=`self`
  - **msg**: Tell me about Mel's 4th house and how does that map to me?
  - predicted=`relationship`  conf=0.7797  signal=1.0  margin=0.5593
  - routing=`PASS`  retrieval=`PASS`  target=`UNRESOLVED_NAMED`  - proposed_action: `{'type': 'add_to_circle', 'suggested_name': 'Mel', 'reason': "name 'Mel' appears in message but is not in user's saved_people", 'source_text': "Tell me about Mel's 4th house and how does that map to me?", 'confidence': 0.55}`


## Representative failure cases (REAL)

- `real` / `forum_chat_messages` / frame=`self`
  - **msg**: How do I naturally show up in group settings?
  - predicted=`general`  conf=0.0  signal=0.0  margin=0.0
  - routing=`WARNING`  retrieval=`PASS`  target=`NOT_APPLICABLE`
- `real` / `forum_chat_messages` / frame=`self`
  - **msg**: How might my lenses influence how I show up in this forum?
  - predicted=`general`  conf=0.0  signal=0.0  margin=0.0
  - routing=`WARNING`  retrieval=`PASS`  target=`NOT_APPLICABLE`
- `real` / `forum_chat_messages` / frame=`self`
  - **msg**: again
  - predicted=`general`  conf=0.0  signal=0.0  margin=0.0
  - routing=`WARNING`  retrieval=`PASS`  target=`NOT_APPLICABLE`
- `real` / `forum_chat_messages` / frame=`self`
  - **msg**: Reflection test (self).
  - predicted=`general`  conf=0.0  signal=0.0  margin=0.0
  - routing=`WARNING`  retrieval=`PASS`  target=`NOT_APPLICABLE`
- `real` / `forum_chat_messages` / frame=`self`
  - **msg**: Reflection test (self).
  - predicted=`general`  conf=0.0  signal=0.0  margin=0.0
  - routing=`WARNING`  retrieval=`PASS`  target=`NOT_APPLICABLE`
- `real` / `forum_chat_messages` / frame=`self`
  - **msg**: Why do Mel and I fight sometimes?
  - predicted=`general`  conf=0.0  signal=0.0  margin=0.0
  - routing=`WARNING`  retrieval=`PASS`  target=`UNRESOLVED_NAMED`  - proposed_action: `{'type': 'add_to_circle', 'suggested_name': 'Mel', 'reason': "name 'Mel' appears in message but is not in user's saved_people", 'source_text': 'Why do Mel and I fight sometimes?', 'confidence': 0.55}`


## False-positive relationship routing samples

- `real` / `forum_chat_messages` / frame=`forum`
  - **msg**: What strengths does this group composition bring?
  - predicted=`relationship`  conf=0.3682  signal=0.45  margin=0.6364
  - routing=`PASS`  retrieval=`PASS`  target=`UNRESOLVED_NO_NAME`
- `real` / `forum_chat_messages` / frame=`forum`
  - **msg**: What's the energy of this forum?
  - predicted=`relationship`  conf=0.2382  signal=0.45  margin=0.0588
  - routing=`WARNING`  retrieval=`PASS`  target=`UNRESOLVED_NO_NAME`
- `real` / `forum_chat_messages` / frame=`forum`
  - **msg**: What's the energy of this forum?
  - predicted=`relationship`  conf=0.2382  signal=0.45  margin=0.0588
  - routing=`WARNING`  retrieval=`PASS`  target=`UNRESOLVED_NO_NAME`
- `real` / `forum_chat_messages` / frame=`forum`
  - **msg**: Reflection test (forum).
  - predicted=`relationship`  conf=0.3682  signal=0.45  margin=0.6364
  - routing=`PASS`  retrieval=`PASS`  target=`UNRESOLVED_NO_NAME`
- `real` / `forum_chat_messages` / frame=`forum`
  - **msg**: RL probe 1.
  - predicted=`relationship`  conf=0.3682  signal=0.45  margin=0.6364
  - routing=`PASS`  retrieval=`PASS`  target=`UNRESOLVED_NO_NAME`


## Unresolved-named-target samples (with proposed_action)

- `real` / `forum_chat_messages` / frame=`self`
  - **msg**: Tell me about Mel’s 4th house
  - predicted=`relationship`  conf=0.6905  signal=1.0  margin=0.381
  - routing=`PASS`  retrieval=`PASS`  target=`UNRESOLVED_NAMED`  - proposed_action: `{'type': 'add_to_circle', 'suggested_name': 'Mel', 'reason': "name 'Mel' appears in message but is not in user's saved_people", 'source_text': 'Tell me about Mel’s 4th house', 'confidence': 0.55}`
- `real` / `forum_chat_messages` / frame=`self`
  - **msg**: Tell me about Mel’s 4th house
  - predicted=`relationship`  conf=0.6905  signal=1.0  margin=0.381
  - routing=`PASS`  retrieval=`PASS`  target=`UNRESOLVED_NAMED`  - proposed_action: `{'type': 'add_to_circle', 'suggested_name': 'Mel', 'reason': "name 'Mel' appears in message but is not in user's saved_people", 'source_text': 'Tell me about Mel’s 4th house', 'confidence': 0.55}`
- `real` / `forum_chat_messages` / frame=`self`
  - **msg**: Can you tell me about Mel’s 4th house please?
  - predicted=`relationship`  conf=0.6905  signal=1.0  margin=0.381
  - routing=`PASS`  retrieval=`PASS`  target=`UNRESOLVED_NAMED`  - proposed_action: `{'type': 'add_to_circle', 'suggested_name': 'Mel', 'reason': "name 'Mel' appears in message but is not in user's saved_people", 'source_text': 'Can you tell me about Mel’s 4th house please?', 'confidence': 0.55}`
- `real` / `forum_chat_messages` / frame=`self`
  - **msg**: Tell me about Mel's 4th house and how does that map to me?
  - predicted=`relationship`  conf=0.7797  signal=1.0  margin=0.5593
  - routing=`PASS`  retrieval=`PASS`  target=`UNRESOLVED_NAMED`  - proposed_action: `{'type': 'add_to_circle', 'suggested_name': 'Mel', 'reason': "name 'Mel' appears in message but is not in user's saved_people", 'source_text': "Tell me about Mel's 4th house and how does that map to me?", 'confidence': 0.55}`
- `real` / `forum_chat_messages` / frame=`self`
  - **msg**: Tell me about Mel's 4th house and how does that map to me?
  - predicted=`relationship`  conf=0.7797  signal=1.0  margin=0.5593
  - routing=`PASS`  retrieval=`PASS`  target=`UNRESOLVED_NAMED`  - proposed_action: `{'type': 'add_to_circle', 'suggested_name': 'Mel', 'reason': "name 'Mel' appears in message but is not in user's saved_people", 'source_text': "Tell me about Mel's 4th house and how does that map to me?", 'confidence': 0.55}`