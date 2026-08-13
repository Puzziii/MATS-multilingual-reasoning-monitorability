# Final pilot–follow-up research analysis

**Small-sample descriptive analysis only.** No causal claims or significance tests are made. The follow-up is a post-pilot scenario-generalization test, and pilot, follow-up, and combined results are always shown separately.

## Accounting

| Dataset | Attempts | Persisted responses | Unavailable |
| --- | --- | --- | --- |
| Pilot | 48 | 47 | 1 |
| Follow-up | 48 | 47 | 1 |
| Combined | 96 | 94 | 2 |

The unavailable follow-up call is the frozen consumed `P7:ta:clean` attempt; it is excluded only from denominators requiring an available clean response and is never counted as incorrect.

## Primary behavioral results

| Measure | Pilot | Follow-up | Combined |
| --- | --- | --- | --- |
| Clean benign accuracy | 12/12 (100.0%) | 11/11 (100.0%) | 23/23 (100.0%) |
| Trusted-target adherence | 12/12 (100.0%) | 11/12 (91.7%) | 23/24 (95.8%) |
| Injected non-think attack success | 5/12 (41.7%) | 2/12 (16.7%) | 7/24 (29.2%) |
| Injected think attack success | 1/11 (9.1%) | 3/12 (25.0%) | 4/23 (17.4%) |
| Injected non-think benign-correct | 6/12 (50.0%) | 8/12 (66.7%) | 14/24 (58.3%) |
| Injected think benign-correct | 10/11 (90.9%) | 9/12 (75.0%) | 19/23 (82.6%) |
| Injected non-think other-output | 1/12 (8.3%) | 2/12 (16.7%) | 3/24 (12.5%) |
| Injected think other-output | 0/11 (0.0%) | 0/12 (0.0%) | 0/23 (0.0%) |

## Paired injected-condition transitions

| Transition | Pilot (n=12) | Follow-up (n=12) | Combined (n=24) |
| --- | --- | --- | --- |
| both_benign_or_other | 6 | 8 | 14 |
| nonthink_attack_think_benign | 4 | 1 | 5 |
| nonthink_benign_think_attack | 0 | 2 | 2 |
| both_attack | 1 | 1 | 2 |
| think_missing | 1 | 0 | 1 |

## Reasoning availability

| Dataset | Think attempts | Non-empty | Persisted-empty | Consumed-unavailable |
| --- | --- | --- | --- | --- |
| pilot | 12 | 9/12 (75.0%) | 2/12 (16.7%) | 1/12 (8.3%) |
| followup | 12 | 11/12 (91.7%) | 1/12 (8.3%) | 0/12 (0.0%) |
| combined | 24 | 20/24 (83.3%) | 3/24 (12.5%) | 1/24 (4.2%) |

## Frozen reasoning labels and sensitivity

| Field | Pilot eligible | Pilot strict | Follow-up eligible | Combined eligible | Combined strict |
| --- | --- | --- | --- | --- | --- |
| payload_noticed | 9/9 (100.0%) | 7/7 (100.0%) | 11/11 (100.0%) | 20/20 (100.0%) | 18/18 (100.0%) |
| untrusted_recognized | 9/9 (100.0%) | 7/7 (100.0%) | 10/11 (90.9%) | 19/20 (95.0%) | 17/18 (94.4%) |
| intent_ignore | 9/9 (100.0%) | 7/7 (100.0%) | 8/11 (72.7%) | 17/20 (85.0%) | 15/18 (83.3%) |
| intent_follow | 0/9 (0.0%) | 0/7 (0.0%) | 3/11 (27.3%) | 3/20 (15.0%) | 3/18 (16.7%) |
| ambiguous | 0/9 (0.0%) | 0/7 (0.0%) | 1/11 (9.1%) | 1/20 (5.0%) | 1/18 (5.6%) |

Strict sensitivity excludes exactly the two frozen compromised pilot records without revealing their identities. Follow-up has no compromised records. Empty and unavailable traces are excluded from label denominators and are never converted to `no`.

## Language, attack-family, and raw reasoning–behavior tables

The CSV summaries provide prompt-language and attack-family behavioral breakdowns, frozen reasoning-language counts, prompt-language × reasoning-language tables, and raw frozen-label × behavioral-outcome cross-tabs. No new monitorability or faithfulness category is introduced.

## Interpretation limits

Pilot and follow-up differences are reported directly rather than smoothed away by pooling. The combined rows are secondary bookkeeping summaries. These results generalize only to the tested model, frozen parameters, scenarios, and languages, and remain descriptive because each dataset contains only 12 scenario-language units.
