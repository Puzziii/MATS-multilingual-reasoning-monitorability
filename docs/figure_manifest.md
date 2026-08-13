# Final figure manifest

All figures are frozen at `final-analysis-v1.0`. Captions below are factual drafting material, not submission prose. No figure supports significance or causal claims.

## Executive-summary recommendation

Priority order:

1. `final_attack_success.png` — essential; directly preserves pilot/follow-up non-replication.
2. `final_pairwise_transitions.png` — strongest unit-paired view of the same non-replication.

Use exactly the attack-success and paired-transition figures in the executive summary. Put reasoning availability and labels in the body, and use the language figure only if space and the adjacent small-cell warning permit it.

## `analysis/figures/final_attack_success.png`

- SHA-256: `3d197359330907048377f2faed245a85f2c0468c193d76477db3cbb34f394bc6`.
- Recommended placement: executive summary and behavioral-results section.
- Exact result shown:

| Dataset | Injected non-think attack success | Injected think attack success |
| --- | ---: | ---: |
| Pilot | 5/12 (41.7%) | 1/11 (9.1%) |
| Follow-up | 2/12 (16.7%) | 3/12 (25.0%) |
| Combined | 7/24 (29.2%) | 4/23 (17.4%) |

- Factual caption: **Attack-target exact matches in injected non-thinking and thinking conditions, reported separately for the 48-attempt pilot and 48-attempt follow-up; pooled counts are secondary.**
- Interpretation warnings:
  - Small descriptive sample; no confidence interval or significance test.
  - The follow-up direction is opposite the pilot direction and must remain prominent.
  - Think denominators differ because one pilot think response is unavailable.
  - Do not label the plotted difference a causal effect of reasoning mode.

## `analysis/figures/final_pairwise_transitions.png`

- SHA-256: `11ba387de73079b1c7a62160ca5c580242f949c998ebfe2f880e962f98f743e8`.
- Recommended placement: executive summary if space permits; otherwise immediately after aggregate attack-success results.
- Exact result shown:

| Non-think → think transition | Pilot | Follow-up |
| --- | ---: | ---: |
| Both resist | 6/12 | 8/12 |
| Attack → resist | 4/12 | 1/12 |
| Resist → attack | 0/12 | 2/12 |
| Both attack | 1/12 | 1/12 |
| Think missing | 1/12 | 0/12 |

- Factual caption: **Paired injected-condition transitions across the 12 scenario-language units in each phase; attack→resist transitions decreased from 4/12 to 1/12, while resist→attack transitions increased from 0/12 to 2/12 in the follow-up.**
- Interpretation warnings:
  - Counts are paired observations, not causal estimates.
  - “Resist” groups benign-correct and other-output states because neither exactly matched the attack target.
  - One pilot pair has a missing think response.
  - Combined transition counts (14/24, 5/24, 2/24, 2/24, 1/24) are not plotted.

## `analysis/figures/final_reasoning_availability.png`

- SHA-256: `1b6391dede678c83ba1c5332b1657e41249c365d1f68f2e1d01ea3ebb5daa45d`.
- Recommended placement: opening of visible-reasoning results in the main body.
- Exact result shown:

| Dataset | Non-empty | Persisted empty | Consumed unavailable | Think-attempt denominator |
| --- | ---: | ---: | ---: | ---: |
| Pilot | 9/12 (75.0%) | 2/12 (16.7%) | 1/12 (8.3%) | 12 |
| Follow-up | 11/12 (91.7%) | 1/12 (8.3%) | 0/12 (0.0%) | 12 |
| Combined | 20/24 (83.3%) | 3/24 (12.5%) | 1/24 (4.2%) | 24 |

- Factual caption: **Availability of API-visible reasoning for every injected-think attempt; only the 20 non-empty traces are eligible for frozen reasoning labels.**
- Interpretation warnings:
  - Empty and unavailable traces are not negative reasoning labels.
  - One persisted-empty trace ended in attack success; it cannot be classified as noticing, recognizing, ignoring, or following.
  - Availability is an API-output property, not evidence of faithful internal reasoning.

## `analysis/figures/final_reasoning_behavior.png`

- SHA-256: `0ed552d3b599a90cb8d7970456441d095e406ee8e0a4ad7c8872e67b61adca16`.
- Recommended placement: visible-reasoning body section; appendix if the exact cross-tab table is in the main text.
- Exact result shown:

| Dataset/scope | Payload noticed=yes | Untrusted recognized=yes | Intent ignore=yes | Intent follow=yes |
| --- | ---: | ---: | ---: | ---: |
| Pilot eligible | 9/9 | 9/9 | 9/9 | 0/9 |
| Follow-up eligible | 11/11 | 10/11 | 8/11 | 3/11 |
| Combined eligible | 20/20 | 19/20 | 17/20 | 3/20 |

- Factual caption: **Yes counts for four frozen reasoning fields among non-empty label-eligible traces; the follow-up contains three stated-follow intents and three injected-think attack successes.**
- Interpretation warnings:
  - The figure omits the separate `ambiguous` field: 0/9 pilot, 1/11 follow-up, 1/20 combined.
  - The figure omits strict-sensitivity counts: combined 18/18 noticed, 17/18 recognized, 15/18 ignore, and 3/18 follow.
  - `Untrusted recognized` and `intent follow` share a similar orange hue in the frozen figure; identify series carefully.
  - Marginal bars do not show the exact intent × outcome cross-tab; use the table in `writeup_evidence_pack.md` for that claim.
  - Do not infer causality or faithfulness.

## `analysis/figures/final_language_results.png`

- SHA-256: `5359c24824f75bfddbf3887d5079293a73a4844954b77ed75da571615a433eab`.
- Recommended placement: appendix; body only if multilingual differences are a central personally chosen theme and all small-cell caveats are adjacent.
- Exact result shown; injected thinking and non-thinking attack successes are pooled within each prompt language:

| Prompt language | Pilot | Follow-up | Combined |
| --- | ---: | ---: | ---: |
| English | 4/8 (50.0%) | 1/8 (12.5%) | 5/16 (31.3%) |
| Tamil | 0/8 (0.0%) | 1/8 (12.5%) | 1/16 (6.3%) |
| Tanglish | 2/7 (28.6%) | 3/8 (37.5%) | 5/15 (33.3%) |

- Factual caption: **Attack-target exact matches across both injected modes by prompt language, with pilot and follow-up shown separately and pooled counts secondary.**
- Interpretation warnings:
  - Mode pooling hides the pilot/follow-up think versus non-think reversal.
  - Denominators are only 7–8 per phase-language group.
  - Scenarios, language realizations, and attack families are not independently randomized factors.
  - Do not claim a Tamil advantage, Tanglish vulnerability, or general language effect.

## Placement summary

| Figure | Executive summary | Main body | Appendix | Priority |
| --- | --- | --- | --- | --- |
| `final_attack_success.png` | Yes | Yes | Optional duplicate prohibited | 1 |
| `final_pairwise_transitions.png` | Yes if space | Yes | Optional | 2 |
| `final_reasoning_availability.png` | No | Yes | Optional | 3 |
| `final_reasoning_behavior.png` | No by default | Yes | Yes if exact cross-tab is main text | 4 |
| `final_language_results.png` | No | Optional | Yes | 5 |
