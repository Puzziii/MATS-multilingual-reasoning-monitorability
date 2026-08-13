# Phase 4C deterministic reasoning-monitorability analysis

This is a small, descriptive analysis. Every percentage below includes its stated numerator and denominator; no causal interpretation is made.

## Frozen inputs and post-freeze exposure note

- Primary annotation SHA-256: `6b82e5e63b370a7ee9858889e9912363f18166fd569984c82c64c18802ad1b7c`.
- Post-blind language-form SHA-256: `167826fc017443e98651878fc1e3c8e4641e1b476aff918e5b0e2367e6c3562f`.
- Raw pilot SHA-256: `43bd3b7fffdc6944a3ac23cf5350613b2b32f1e25832ddc025c2a1f2723c3a14`.
- Broad behavioral metadata was briefly exposed only after both annotation sets were frozen. No annotation-ID mapping or outcome linkage occurred before label formation; this is treated as non-material to frozen labels.

## Analysis populations

| Population | Count | Definition |
| --- | --- | --- |
| All injected-think attempts | 12 | All frozen attempted calls. |
| Persisted responses | 11 | Responses persisted in the frozen behavioral analysis. |
| Non-empty label-eligible traces | 9 | Non-empty reasoning with completed frozen primary and language reviews. |
| Strictly blinded eligible traces | 7 | Eligible traces excluding the two hidden-key sensitivity records. |

## Reasoning availability

| Status | Count / all attempts |
| --- | --- |
| non empty | 9/12 (75.0%) |
| persisted empty | 2/12 (16.7%) |
| consumed unavailable | 1/12 (8.3%) |

The preregistered availability gate is 9/12 non-empty traces and is satisfied. Persisted-empty and consumed-unavailable traces remain unavailable for primary label rates; they are not coded as `no`.

## Frozen primary labels and confidence

| Frozen field | Yes / eligible | No / eligible |
| --- | --- | --- |
| payload noticed | 9/9 (100.0%) | 0/9 (0.0%) |
| untrusted recognized | 9/9 (100.0%) | 0/9 (0.0%) |
| intent ignore | 9/9 (100.0%) | 0/9 (0.0%) |
| intent follow | 0/9 (0.0%) | 9/9 (100.0%) |
| ambiguous | 0/9 (0.0%) | 9/9 (100.0%) |

| Confidence | Count / eligible |
| --- | --- |
| high | 9/9 (100.0%) |

## Frozen reasoning-language form

| Frozen language value | Count / persisted responses |
| --- | --- |
| English | 5/11 (45.5%) |
| mixed | 4/11 (36.4%) |
| other | 2/11 (18.2%) |

Language comparisons below use only frozen language-form values. The two persisted-empty traces are not label-eligible, regardless of their frozen form entries.

### Frozen reasoning language × prompt language

| Prompt language | n | English | Tamil | Tanglish | mixed | other |
| --- | --- | --- | --- | --- | --- | --- |
| en | 4 | 2/4 (50.0%) | 0/4 (0.0%) | 0/4 (0.0%) | 0/4 (0.0%) | 2/4 (50.0%) |
| ta | 4 | 0/4 (0.0%) | 0/4 (0.0%) | 0/4 (0.0%) | 4/4 (100.0%) | 0/4 (0.0%) |
| tanglish | 3 | 3/3 (100.0%) | 0/3 (0.0%) | 0/3 (0.0%) | 0/3 (0.0%) | 0/3 (0.0%) |

## Label breakdowns among non-empty eligible traces

### By prompt language

| prompt language | n | Payload noticed | Untrusted recognized | Intent ignore | Intent follow |
| --- | --- | --- | --- | --- | --- |
| en | 2 | 2/2 (100.0%) | 2/2 (100.0%) | 2/2 (100.0%) | 0/2 (0.0%) |
| ta | 4 | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) | 0/4 (0.0%) |
| tanglish | 3 | 3/3 (100.0%) | 3/3 (100.0%) | 3/3 (100.0%) | 0/3 (0.0%) |

### By attack family

| attack family | n | Payload noticed | Untrusted recognized | Intent ignore | Intent follow |
| --- | --- | --- | --- | --- | --- |
| fake_authority | 2 | 2/2 (100.0%) | 2/2 (100.0%) | 2/2 (100.0%) | 0/2 (0.0%) |
| simple_override | 3 | 3/3 (100.0%) | 3/3 (100.0%) | 3/3 (100.0%) | 0/3 (0.0%) |
| synthetic_canary_extraction | 3 | 3/3 (100.0%) | 3/3 (100.0%) | 3/3 (100.0%) | 0/3 (0.0%) |
| task_output_hijack | 1 | 1/1 (100.0%) | 1/1 (100.0%) | 1/1 (100.0%) | 0/1 (0.0%) |

### By behavioral outcome

| behavioral outcome | n | Payload noticed | Untrusted recognized | Intent ignore | Intent follow |
| --- | --- | --- | --- | --- | --- |
| benign_correct | 9 | 9/9 (100.0%) | 9/9 (100.0%) | 9/9 (100.0%) | 0/9 (0.0%) |

## Raw label × behavioral-outcome cross-tabs

### payload noticed

| Label value | attack success | benign correct | other output | missing |
| --- | --- | --- | --- | --- |
| yes | 0/9 (0.0%) | 9/9 (100.0%) | 0/9 (0.0%) | 0/9 (0.0%) |
| no | 0/9 (0.0%) | 0/9 (0.0%) | 0/9 (0.0%) | 0/9 (0.0%) |

### untrusted recognized

| Label value | attack success | benign correct | other output | missing |
| --- | --- | --- | --- | --- |
| yes | 0/9 (0.0%) | 9/9 (100.0%) | 0/9 (0.0%) | 0/9 (0.0%) |
| no | 0/9 (0.0%) | 0/9 (0.0%) | 0/9 (0.0%) | 0/9 (0.0%) |

### intent ignore

| Label value | attack success | benign correct | other output | missing |
| --- | --- | --- | --- | --- |
| yes | 0/9 (0.0%) | 9/9 (100.0%) | 0/9 (0.0%) | 0/9 (0.0%) |
| no | 0/9 (0.0%) | 0/9 (0.0%) | 0/9 (0.0%) | 0/9 (0.0%) |

### intent follow

| Label value | attack success | benign correct | other output | missing |
| --- | --- | --- | --- | --- |
| yes | 0/9 (0.0%) | 0/9 (0.0%) | 0/9 (0.0%) | 0/9 (0.0%) |
| no | 0/9 (0.0%) | 9/9 (100.0%) | 0/9 (0.0%) | 0/9 (0.0%) |

The preregistered recognition definition is `untrusted_recognized = yes`. Raw behavioral states are retained above; no additional monitorability or faithfulness category is introduced.

## Blinding-sensitivity analysis

| Frozen field | All eligible (n=9) | Strictly blinded eligible (n=7) |
| --- | --- | --- |
| payload noticed | 9/9 (100.0%) | 7/7 (100.0%) |
| untrusted recognized | 9/9 (100.0%) | 7/7 (100.0%) |
| intent ignore | 9/9 (100.0%) | 7/7 (100.0%) |
| intent follow | 0/9 (0.0%) | 0/7 (0.0%) |
| ambiguous | 0/9 (0.0%) | 0/7 (0.0%) |

The sensitivity exclusion removes exactly the two hidden-key records marked as blinding-compromised. Their identities and contents are not reported.
