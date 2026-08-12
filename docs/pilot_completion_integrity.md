# Multilingual Monitorability Pilot Completion Integrity

This document records the exact integrity metadata for the completed raw multilingual pilot artifact (`outputs/pilot_results.jsonl`).

- **resume exit status**: 0
- **manifest events**: 1
- **resume authorization events**: 1
- **request_started events**: 48
- **response events**: 47
- **documented consumed failure calls**: 1
- **total planned call IDs consumed**: 48
- **uncertain events**: 0
- **total actual network attempts**: 48
- **duplicate successes**: 0
- **unmatched starts**: 0
- **malformed events**: 0
- **next unattempted call**: none
- **think attempts**: 12
- **persisted think responses**: 11
- **think reasoning non-empty**: 9
- **think reasoning empty/unavailable**: 2
- **non-think reasoning unexpectedly present**: 0
- **empty final text**: 0
- **finish reasons**: stop=47
- **aggregate usage**:
  - prompt tokens: 9163
  - completion tokens: 5195
  - total tokens: 14358
- **preregistered reasoning gate**: PASS at exactly 9/12
- **artifact credential audit**: false
- **integrity status**: PASS
- **raw artifact SHA-256**: 43bd3b7fffdc6944a3ac23cf5350613b2b32f1e25832ddc025c2a1f2723c3a14

## Clarifications
- “48 consumed calls” means all 48 planned call IDs reached a terminal state.
- It does not mean 48 successful response events.
- There are 47 persisted responses and one documented consumed failure.
- The consumed P3:tanglish:injected_think call has no recoverable behavioral output or usage.
- No behavioral or reasoning-content analysis was performed during this integrity audit.
