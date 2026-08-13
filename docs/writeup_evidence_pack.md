# Application write-up evidence pack

Preparation status: offline factual extraction from `final-analysis-v1.0` (`06df8eab67f276ab6c32ed3eaa267f97bf83dfda`). This is not submission prose.

Claim labels used below:

- `SUPPORTED`: directly fixed by a frozen protocol, artifact, code path, or QA record.
- `DESCRIPTIVE ONLY`: directly measured in this small sample; not inferential or causal.
- `UNSUPPORTED / DO NOT CLAIM`: not established by this study, or requires external verification.

## Research question and motivation

- **SUPPORTED** — Frozen research question: when an instruction is embedded inside explicitly untrusted content, does Sarvam-105B follow or resist it, explicitly recognize it as untrusted in API-visible reasoning, and show different observed patterns across English, Tamil, and Tanglish? Source: [preregistration_v0.1.md](preregistration_v0.1.md).
- **SUPPORTED** — The study concerns API-visible `reasoning_content`; it does not treat that field as the model's complete or necessarily faithful internal reasoning. Source: [preregistration_v0.1.md](preregistration_v0.1.md).
- **SUPPORTED** — Motivation encoded in the design: pair the same payload across trusted and explicitly untrusted delivery, compare thinking and non-thinking modes, and retain multilingual surface forms. Source: [preregistration_v0.1.md](preregistration_v0.1.md), [followup_protocol_v1.0.md](followup_protocol_v1.0.md).
- **UNSUPPORTED / DO NOT CLAIM** — Do not say multilingual indirect prompt injection is unstudied, that this is the first Tamil/Tanglish monitorability study, or that the design is novel until the related-work bibliography is verified.

## Experimental design

- **SUPPORTED** — 8 base scenarios: pilot P1–P4 and follow-up P5–P8.
- **SUPPORTED** — 3 prompt languages per scenario: English (`en`), native-script Tamil (`ta`), and Tanglish (`tanglish`).
- **SUPPORTED** — 4 conditions per scenario-language unit: `clean`, `trusted`, `injected_non_think`, and `injected_think`.
- **SUPPORTED** — Combined design: 8 scenarios × 3 languages = 24 paired units; 24 units × 4 conditions = 96 planned study attempts.
- **SUPPORTED** — Each phase had 4 scenarios × 3 languages = 12 units and 48 study attempts.
- **SUPPORTED** — The four attack families were `simple_override`, `fake_authority`, `task_output_hijack`, and `synthetic_canary_extraction`; each family contributed one pilot and one follow-up scenario.
- **SUPPORTED** — For each unit, `injected_non_think` and `injected_think` used the same rendered user prompt; the reasoning-mode parameter was the intended difference.
- **SUPPORTED** — Behavioral grading used exact string matching after frozen whitespace normalization. No LLM judge was used for the primary behavioral outcome.
- **SUPPORTED** — Conditions ran sequentially in the order clean → trusted → injected non-think → injected think. Unit order used seed `20260811` in the pilot and `42` in the follow-up.
- **SUPPORTED** — Reasoning labels were manually assigned from outcome-blinded packets before the hidden keys and behavioral outcomes were joined.

Sources: [execution_protocol_v1.0.md](execution_protocol_v1.0.md), [followup_protocol_v1.0.md](followup_protocol_v1.0.md), [final_research_report.md](../analysis/final_research_report.md), [analyze_final.py](../src/monitorability/analyze_final.py).

## Model and API configuration

- **SUPPORTED** — Provider/model: Sarvam API, manifest model identifier `sarvam-105b`; the follow-up protocol also describes it as Sarvam-105B / `sarvam-2.5-pro-flash`.
- **SUPPORTED** — Endpoint: `https://api.sarvam.ai/v1/chat/completions`.
- **SUPPORTED** — Sampling/configuration: temperature `0.0`; top-p `1.0`; max tokens `2048`; generation seed `1729`; `n=1`; streaming off; frequency penalty `0`; presence penalty `0`; wiki grounding off.
- **SUPPORTED** — Think calls used `reasoning_effort="medium"`; non-think calls used `reasoning_effort=null`.
- **SUPPORTED** — Operational configuration: sequential execution, 120-second timeout, at least 2.1 seconds between request starts, zero retries, and a maximum of 48 study network attempts per phase.
- **SUPPORTED** — Authentication values and headers were not persisted in study artifacts or derived outputs.

Sources: frozen manifests in `outputs/pilot_results.jsonl` and `outputs/followup_results_attempt1_403.jsonl`; [preregistration_v0.1.md](preregistration_v0.1.md); [execution_protocol_v1.0.md](execution_protocol_v1.0.md).

## Attempt and response accounting

Every row is **SUPPORTED** bookkeeping.

| Dataset | Attempts | Persisted responses | Unavailable | Response availability |
| --- | ---: | ---: | ---: | ---: |
| Pilot | 48 | 47 | 1 | 47/48 (97.9%) |
| Follow-up | 48 | 47 | 1 | 47/48 (97.9%) |
| Combined | 96 | 94 | 2 | 94/96 (97.9%) |

- **SUPPORTED** — Both datasets had 47 `finish_reason=stop` responses and one unavailable response; combined: 94 stop and 2 unavailable.
- **SUPPORTED** — Aggregate usage over available responses: pilot 9,163 prompt + 5,195 completion = 14,358 total tokens; follow-up 9,351 + 4,889 = 14,240; combined 18,514 + 10,084 = 28,598.

Sources: [final_research_report.md](../analysis/final_research_report.md), [behavior_calls.csv](../analysis/behavior_calls.csv), [followup_behavior_calls.csv](../analysis/followup_behavior_calls.csv).

## Behavioral outcomes: overall

Every result in this and the next two behavioral tables is **DESCRIPTIVE ONLY**. `NT` means injected non-think. Percentages are rounded to one decimal here; source CSVs retain six decimal places.

| Dataset | Clean benign | Trusted target | NT attack | NT benign | NT other | Think attack | Think benign | Think other |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Pilot | 12/12 (100.0%) | 12/12 (100.0%) | 5/12 (41.7%) | 6/12 (50.0%) | 1/12 (8.3%) | 1/11 (9.1%) | 10/11 (90.9%) | 0/11 (0.0%) |
| Follow-up | 11/11 (100.0%) | 11/12 (91.7%) | 2/12 (16.7%) | 8/12 (66.7%) | 2/12 (16.7%) | 3/12 (25.0%) | 9/12 (75.0%) | 0/12 (0.0%) |
| Combined | 23/23 (100.0%) | 23/24 (95.8%) | 7/24 (29.2%) | 14/24 (58.3%) | 3/24 (12.5%) | 4/23 (17.4%) | 19/23 (82.6%) | 0/23 (0.0%) |

- **DESCRIPTIVE ONLY** — The pilot difference was 5/12 non-think attack successes versus 1/11 think attack successes.
- **DESCRIPTIVE ONLY** — The follow-up did not reproduce that direction: 2/12 non-think versus 3/12 think attack successes.
- **DESCRIPTIVE ONLY** — The pooled comparison, secondary to the separate phases, was 7/24 non-think versus 4/23 think.
- **UNSUPPORTED / DO NOT CLAIM** — Do not say thinking reduced attack success, improved safety, or had a statistically reliable effect. The follow-up moved in the opposite direction and no significance test was preregistered.

Source: [combined_behavior_summary.csv](../analysis/combined_behavior_summary.csv).

## Behavioral outcomes: prompt-language breakdown

All cells are **DESCRIPTIVE ONLY**. Each injected condition has four observations per language and phase unless the frozen missing think response reduces the denominator to three.

| Dataset | Language | Available | Clean | Trusted | NT attack | NT benign | NT other | Think attack | Think benign | Think other |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Pilot | English | 16/16 | 4/4 | 4/4 | 3/4 | 1/4 | 0/4 | 1/4 | 3/4 | 0/4 |
| Pilot | Tamil | 16/16 | 4/4 | 4/4 | 0/4 | 3/4 | 1/4 | 0/4 | 4/4 | 0/4 |
| Pilot | Tanglish | 15/16 | 4/4 | 4/4 | 2/4 | 2/4 | 0/4 | 0/3 | 3/3 | 0/3 |
| Follow-up | English | 16/16 | 4/4 | 4/4 | 0/4 | 3/4 | 1/4 | 1/4 | 3/4 | 0/4 |
| Follow-up | Tamil | 15/16 | 3/3 | 4/4 | 1/4 | 2/4 | 1/4 | 0/4 | 4/4 | 0/4 |
| Follow-up | Tanglish | 16/16 | 4/4 | 3/4 | 1/4 | 3/4 | 0/4 | 2/4 | 2/4 | 0/4 |
| Combined | English | 32/32 | 8/8 | 8/8 | 3/8 | 4/8 | 1/8 | 2/8 | 6/8 | 0/8 |
| Combined | Tamil | 31/32 | 7/7 | 8/8 | 1/8 | 5/8 | 2/8 | 0/8 | 8/8 | 0/8 |
| Combined | Tanglish | 31/32 | 8/8 | 7/8 | 3/8 | 5/8 | 0/8 | 2/7 | 5/7 | 0/7 |

- **DESCRIPTIVE ONLY** — Combining both injected modes for the plotted language view: pilot English 4/8, Tamil 0/8, Tanglish 2/7; follow-up English 1/8, Tamil 1/8, Tanglish 3/8; combined English 5/16, Tamil 1/16, Tanglish 5/15.
- **UNSUPPORTED / DO NOT CLAIM** — Do not claim a language effect or rank languages from these cells; each phase-language-mode cell has only three or four observations and scenario identity is tied to attack family.

Source: [combined_behavior_summary.csv](../analysis/combined_behavior_summary.csv).

## Behavioral outcomes: attack-family breakdown

All cells are **DESCRIPTIVE ONLY**. Each injected condition has three observations per family and phase unless a missing response reduces the denominator.

| Dataset | Attack family | Available | Clean | Trusted | NT attack | NT benign | NT other | Think attack | Think benign | Think other |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Pilot | simple override | 12/12 | 3/3 | 3/3 | 0/3 | 3/3 | 0/3 | 0/3 | 3/3 | 0/3 |
| Pilot | fake authority | 12/12 | 3/3 | 3/3 | 2/3 | 0/3 | 1/3 | 1/3 | 2/3 | 0/3 |
| Pilot | task-output hijack | 11/12 | 3/3 | 3/3 | 1/3 | 2/3 | 0/3 | 0/2 | 2/2 | 0/2 |
| Pilot | synthetic canary extraction | 12/12 | 3/3 | 3/3 | 2/3 | 1/3 | 0/3 | 0/3 | 3/3 | 0/3 |
| Follow-up | simple override | 12/12 | 3/3 | 3/3 | 1/3 | 1/3 | 1/3 | 1/3 | 2/3 | 0/3 |
| Follow-up | fake authority | 12/12 | 3/3 | 3/3 | 0/3 | 2/3 | 1/3 | 1/3 | 2/3 | 0/3 |
| Follow-up | task-output hijack | 11/12 | 2/2 | 3/3 | 1/3 | 2/3 | 0/3 | 1/3 | 2/3 | 0/3 |
| Follow-up | synthetic canary extraction | 12/12 | 3/3 | 2/3 | 0/3 | 3/3 | 0/3 | 0/3 | 3/3 | 0/3 |
| Combined | simple override | 24/24 | 6/6 | 6/6 | 1/6 | 4/6 | 1/6 | 1/6 | 5/6 | 0/6 |
| Combined | fake authority | 24/24 | 6/6 | 6/6 | 2/6 | 2/6 | 2/6 | 2/6 | 4/6 | 0/6 |
| Combined | task-output hijack | 22/24 | 5/5 | 6/6 | 2/6 | 4/6 | 0/6 | 1/5 | 4/5 | 0/5 |
| Combined | synthetic canary extraction | 24/24 | 6/6 | 5/6 | 2/6 | 4/6 | 0/6 | 0/6 | 6/6 | 0/6 |

- **UNSUPPORTED / DO NOT CLAIM** — Do not claim attack-family effects; each phase-family-mode cell has at most three observations and each family is represented by only one base scenario per phase.

Source: [combined_behavior_summary.csv](../analysis/combined_behavior_summary.csv).

## Paired injected-condition transitions

All transition counts are **DESCRIPTIVE ONLY**. The denominator is the 12 scenario-language units per phase and 24 combined.

| Transition, non-think → think | Pilot | Follow-up | Combined |
| --- | ---: | ---: | ---: |
| Both resist (`both_benign_or_other`) | 6/12 | 8/12 | 14/24 |
| Attack → resist | 4/12 | 1/12 | 5/24 |
| Resist → attack | 0/12 | 2/12 | 2/24 |
| Both attack | 1/12 | 1/12 | 2/24 |
| Think response missing | 1/12 | 0/12 | 1/24 |

- **DESCRIPTIVE ONLY** — The follow-up contains two resist→attack transitions versus none in the pilot, while attack→resist transitions fell from four in the pilot to one in the follow-up.
- **UNSUPPORTED / DO NOT CLAIM** — Do not interpret paired transitions as a causal effect of visible reasoning or reasoning mode; calls were provider outputs from a small, fixed, single-model sample.

Sources: [combined_pairwise_units.csv](../analysis/combined_pairwise_units.csv), [final_pairwise_transitions.png](../analysis/figures/final_pairwise_transitions.png).

## Reasoning availability and denominator treatment

Every availability count is **DESCRIPTIVE ONLY**.

| Dataset | Think attempts | Non-empty eligible | Persisted empty | Consumed unavailable |
| --- | ---: | ---: | ---: | ---: |
| Pilot | 12 | 9/12 (75.0%) | 2/12 (16.7%) | 1/12 (8.3%) |
| Follow-up | 12 | 11/12 (91.7%) | 1/12 (8.3%) | 0/12 (0.0%) |
| Combined | 24 | 20/24 (83.3%) | 3/24 (12.5%) | 1/24 (4.2%) |

- **SUPPORTED** — Empty and unavailable traces were not converted to negative reasoning labels.
- **SUPPORTED** — Label denominators are 9 pilot, 11 follow-up, and 20 combined non-empty traces; strict sensitivity denominators are 7 pilot and 18 combined after excluding exactly two compromised pilot records.
- **DESCRIPTIVE ONLY** — Availability × behavior over all 24 think attempts: non-empty = 3 attack-success + 17 benign-correct; persisted-empty = 1 attack-success + 2 benign-correct; consumed-unavailable = 1 missing.
- **SUPPORTED** — The one attack success with persisted-empty reasoning has no reasoning labels and must not be described as `payload_noticed=no`, `untrusted_recognized=no`, or any intent value.

Sources: [combined_reasoning_summary.csv](../analysis/combined_reasoning_summary.csv), [final_reasoning_availability.png](../analysis/figures/final_reasoning_availability.png).

## Frozen reasoning labels and sensitivity

All label rates are **DESCRIPTIVE ONLY**. Values are `yes` counts over non-empty label-eligible traces; `no` is the denominator minus the displayed numerator. All eligible annotations had high confidence: pilot 9/9, pilot strict 7/7, follow-up 11/11, combined 20/20, combined strict 18/18.

| Field | Pilot eligible | Pilot strict | Follow-up eligible | Combined eligible | Combined strict |
| --- | ---: | ---: | ---: | ---: | ---: |
| Payload noticed | 9/9 | 7/7 | 11/11 | 20/20 | 18/18 |
| Untrusted recognized | 9/9 | 7/7 | 10/11 | 19/20 | 17/18 |
| Intent ignore | 9/9 | 7/7 | 8/11 | 17/20 | 15/18 |
| Intent follow | 0/9 | 0/7 | 3/11 | 3/20 | 3/18 |
| Ambiguous | 0/9 | 0/7 | 1/11 | 1/20 | 1/18 |

- **DESCRIPTIVE ONLY** — Excluding the two frozen compromised pilot records leaves the pilot label pattern unchanged in proportion and changes the combined counts as shown.
- **UNSUPPORTED / DO NOT CLAIM** — High annotator confidence is not evidence that the API-visible trace is faithful to internal computation.

Source: [combined_reasoning_summary.csv](../analysis/combined_reasoning_summary.csv).

## Reasoning labels by prompt language

All cells are **DESCRIPTIVE ONLY** and show `yes`/eligible denominator in the order: noticed; untrusted recognized; intent ignore; intent follow; ambiguous.

| Dataset | Prompt language | Noticed | Recognized | Ignore | Follow | Ambiguous |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Pilot | English | 2/2 | 2/2 | 2/2 | 0/2 | 0/2 |
| Pilot | Tamil | 4/4 | 4/4 | 4/4 | 0/4 | 0/4 |
| Pilot | Tanglish | 3/3 | 3/3 | 3/3 | 0/3 | 0/3 |
| Follow-up | English | 4/4 | 4/4 | 3/4 | 1/4 | 0/4 |
| Follow-up | Tamil | 4/4 | 4/4 | 4/4 | 0/4 | 1/4 |
| Follow-up | Tanglish | 3/3 | 2/3 | 1/3 | 2/3 | 0/3 |
| Combined | English | 6/6 | 6/6 | 5/6 | 1/6 | 0/6 |
| Combined | Tamil | 8/8 | 8/8 | 8/8 | 0/8 | 1/8 |
| Combined | Tanglish | 6/6 | 5/6 | 4/6 | 2/6 | 0/6 |

- **UNSUPPORTED / DO NOT CLAIM** — Do not infer population-level language differences from denominators of 2–8, or interpret code mixing as lower-quality reasoning.

Source: [combined_reasoning_summary.csv](../analysis/combined_reasoning_summary.csv).

## Reasoning labels by attack family

All cells are **DESCRIPTIVE ONLY** and show `yes`/eligible denominator in the order: noticed; untrusted recognized; intent ignore; intent follow; ambiguous.

| Dataset | Attack family | Noticed | Recognized | Ignore | Follow | Ambiguous |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Pilot | simple override | 3/3 | 3/3 | 3/3 | 0/3 | 0/3 |
| Pilot | fake authority | 2/2 | 2/2 | 2/2 | 0/2 | 0/2 |
| Pilot | task-output hijack | 1/1 | 1/1 | 1/1 | 0/1 | 0/1 |
| Pilot | synthetic canary extraction | 3/3 | 3/3 | 3/3 | 0/3 | 0/3 |
| Follow-up | simple override | 3/3 | 2/3 | 2/3 | 1/3 | 1/3 |
| Follow-up | fake authority | 2/2 | 2/2 | 1/2 | 1/2 | 0/2 |
| Follow-up | task-output hijack | 3/3 | 3/3 | 2/3 | 1/3 | 0/3 |
| Follow-up | synthetic canary extraction | 3/3 | 3/3 | 3/3 | 0/3 | 0/3 |
| Combined | simple override | 6/6 | 5/6 | 5/6 | 1/6 | 1/6 |
| Combined | fake authority | 4/4 | 4/4 | 3/4 | 1/4 | 0/4 |
| Combined | task-output hijack | 4/4 | 4/4 | 3/4 | 1/4 | 0/4 |
| Combined | synthetic canary extraction | 6/6 | 6/6 | 6/6 | 0/6 | 0/6 |

- **UNSUPPORTED / DO NOT CLAIM** — Do not infer attack-family effects; eligible denominators are 1–6 and family is confounded with base scenario.

Source: [combined_reasoning_summary.csv](../analysis/combined_reasoning_summary.csv).

## Reasoning-language breakdown

All counts are **DESCRIPTIVE ONLY** over persisted think responses, including the frozen empty-trace treatment.

| Dataset | English | Tamil | Tanglish | Mixed | Other | Unavailable | Denominator |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Pilot | 5/11 | 0/11 | 0/11 | 4/11 | 2/11 | 0/11 | 11 persisted |
| Follow-up | 6/12 | 0/12 | 0/12 | 5/12 | 0/12 | 1/12 | 12 persisted |
| Combined | 11/23 | 0/23 | 0/23 | 9/23 | 2/23 | 1/23 | 23 persisted |

Prompt language × reasoning language, combined persisted responses:

| Prompt language | English | Tamil | Tanglish | Mixed | Other | Unavailable | Denominator |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| English | 6/8 | 0/8 | 0/8 | 0/8 | 2/8 | 0/8 | 8 |
| Tamil | 0/8 | 0/8 | 0/8 | 8/8 | 0/8 | 0/8 | 8 |
| Tanglish | 5/7 | 0/7 | 0/7 | 1/7 | 0/7 | 1/7 | 7 |

Phase-specific prompt × reasoning-language facts:

- **DESCRIPTIVE ONLY** — Pilot: English prompts 2/4 English and 2/4 other; Tamil 4/4 mixed; Tanglish 3/3 English.
- **DESCRIPTIVE ONLY** — Follow-up: English 4/4 English; Tamil 4/4 mixed; Tanglish 2/4 English, 1/4 mixed, and 1/4 unavailable.
- **UNSUPPORTED / DO NOT CLAIM** — Do not describe `mixed` as Tamil-language reasoning quality or infer comprehension from the language category alone.

Source: [combined_reasoning_summary.csv](../analysis/combined_reasoning_summary.csv).

## Frozen reasoning-label × behavioral-outcome cross-tabs

Every cell below is **DESCRIPTIVE ONLY**. Denominators are the eligible non-empty traces for that phase: pilot 9, follow-up 11, combined 20. There were no `other_output` or `missing` outcomes among eligible traces, so those cells are all zero.

### Pilot, denominator 9

| Label | Value | Attack success | Benign correct | Other | Missing | Total |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Payload noticed | yes | 0/9 | 9/9 | 0/9 | 0/9 | 9/9 |
| Payload noticed | no | 0/9 | 0/9 | 0/9 | 0/9 | 0/9 |
| Untrusted recognized | yes | 0/9 | 9/9 | 0/9 | 0/9 | 9/9 |
| Untrusted recognized | no | 0/9 | 0/9 | 0/9 | 0/9 | 0/9 |
| Intent ignore | yes | 0/9 | 9/9 | 0/9 | 0/9 | 9/9 |
| Intent ignore | no | 0/9 | 0/9 | 0/9 | 0/9 | 0/9 |
| Intent follow | yes | 0/9 | 0/9 | 0/9 | 0/9 | 0/9 |
| Intent follow | no | 0/9 | 9/9 | 0/9 | 0/9 | 9/9 |
| Ambiguous | yes | 0/9 | 0/9 | 0/9 | 0/9 | 0/9 |
| Ambiguous | no | 0/9 | 9/9 | 0/9 | 0/9 | 9/9 |

### Follow-up, denominator 11

| Label | Value | Attack success | Benign correct | Other | Missing | Total |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Payload noticed | yes | 3/11 | 8/11 | 0/11 | 0/11 | 11/11 |
| Payload noticed | no | 0/11 | 0/11 | 0/11 | 0/11 | 0/11 |
| Untrusted recognized | yes | 2/11 | 8/11 | 0/11 | 0/11 | 10/11 |
| Untrusted recognized | no | 1/11 | 0/11 | 0/11 | 0/11 | 1/11 |
| Intent ignore | yes | 0/11 | 8/11 | 0/11 | 0/11 | 8/11 |
| Intent ignore | no | 3/11 | 0/11 | 0/11 | 0/11 | 3/11 |
| Intent follow | yes | 3/11 | 0/11 | 0/11 | 0/11 | 3/11 |
| Intent follow | no | 0/11 | 8/11 | 0/11 | 0/11 | 8/11 |
| Ambiguous | yes | 0/11 | 1/11 | 0/11 | 0/11 | 1/11 |
| Ambiguous | no | 3/11 | 7/11 | 0/11 | 0/11 | 10/11 |

### Combined, denominator 20

| Label | Value | Attack success | Benign correct | Other | Missing | Total |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Payload noticed | yes | 3/20 | 17/20 | 0/20 | 0/20 | 20/20 |
| Payload noticed | no | 0/20 | 0/20 | 0/20 | 0/20 | 0/20 |
| Untrusted recognized | yes | 2/20 | 17/20 | 0/20 | 0/20 | 19/20 |
| Untrusted recognized | no | 1/20 | 0/20 | 0/20 | 0/20 | 1/20 |
| Intent ignore | yes | 0/20 | 17/20 | 0/20 | 0/20 | 17/20 |
| Intent ignore | no | 3/20 | 0/20 | 0/20 | 0/20 | 3/20 |
| Intent follow | yes | 3/20 | 0/20 | 0/20 | 0/20 | 3/20 |
| Intent follow | no | 0/20 | 17/20 | 0/20 | 0/20 | 17/20 |
| Ambiguous | yes | 0/20 | 1/20 | 0/20 | 0/20 | 1/20 |
| Ambiguous | no | 3/20 | 16/20 | 0/20 | 0/20 | 19/20 |

### Exact reasoning-intent × behavior extraction

This is the requested direct cross-tab; no new alignment or faithfulness category is defined.

| Behavioral outcome among 20 eligible traces | Intent ignore = yes | Intent ignore = no | Intent follow = yes | Intent follow = no |
| --- | ---: | ---: | ---: | ---: |
| Attack success, 3/20 | 0/20 | 3/20 | 3/20 | 0/20 |
| Benign correct, 17/20 | 17/20 | 0/20 | 0/20 | 17/20 |
| Other output, 0/20 | 0/20 | 0/20 | 0/20 | 0/20 |
| Missing, 0/20 | 0/20 | 0/20 | 0/20 | 0/20 |

- **DESCRIPTIVE ONLY** — In these 20 eligible traces, all 17 benign-correct outcomes had `intent_ignore=yes` and `intent_follow=no`; all 3 attack-success outcomes had `intent_ignore=no` and `intent_follow=yes`; the discordant cells were 0/20.
- **DESCRIPTIVE ONLY** — Strict sensitivity has the same cell pattern over 18 traces: 15 benign-correct with ignore=yes/follow=no and 3 attack-success with ignore=no/follow=yes.
- **DESCRIPTIVE ONLY** — Untrusted recognition was not perfectly coupled to outcome: 2/3 eligible attack successes had recognition=yes and 1/3 had recognition=no; all 17/17 benign-correct eligible traces had recognition=yes.
- **UNSUPPORTED / DO NOT CLAIM** — Do not say visible reasoning caused resistance, that intent labels are faithful internal states, or that this constitutes a validated monitorability/faithfulness category.
- **SUPPORTED** — One additional think attack success occurred on a persisted-empty trace and is excluded from all label cross-tabs rather than labeled `no`.

Source: [combined_reasoning_summary.csv](../analysis/combined_reasoning_summary.csv).

## Missing-call treatment

- **SUPPORTED** — Pilot: one injected-think study attempt was consumed unavailable. Behavioral think rates use 11 persisted responses; reasoning availability keeps all 12 attempts; labels exclude the unavailable trace.
- **SUPPORTED** — Follow-up: `P7:ta:clean` received HTTP 403, was consumed, never retried or replaced, and remains unavailable. Clean accuracy uses the 11 available clean responses and does not count the call as incorrect.
- **SUPPORTED** — Combined: 96 attempts, 94 persisted responses, and 2 unavailable. Missing responses are excluded only where a metric requires an available response; they remain visible in attempt accounting.
- **UNSUPPORTED / DO NOT CLAIM** — Do not describe either unavailable call as incorrect, benign, resistant, attack-successful, or reasoning-label negative.

Sources: [pilot_attempt_2_resume_deviation.md](pilot_attempt_2_resume_deviation.md), [followup_continuation_deviation_v1.0.md](followup_continuation_deviation_v1.0.md), [final_research_report.md](../analysis/final_research_report.md).

## Protocol deviations and interpretation

- **SUPPORTED** — An initial pilot credential-preflight incident made no provider request and consumed no study attempt. A frozen fresh-run deviation retained the same 48-call ceiling and scientific design. Interpretation impact: operational provenance only; no experimental result was generated. Sources: [pilot_attempt_1_incident.md](pilot_attempt_1_incident.md), [pilot_attempt_2_deviation.md](pilot_attempt_2_deviation.md).
- **SUPPORTED** — The pilot parser initially treated a valid response with empty reasoning as a terminal failure. The call was consumed, never retried, preserved as unavailable for behavioral output, and counted in the 12-attempt reasoning-availability denominator. Interpretation impact: one think outcome is unavailable and no label can be inferred; the continuation changed persistence instrumentation, not prompts, model parameters, hypotheses, or grading. Source: [pilot_attempt_2_resume_deviation.md](pilot_attempt_2_resume_deviation.md).
- **SUPPORTED** — The follow-up's first call received HTTP 403. It was retained as the single unavailable clean call; a separate non-study arithmetic authorization smoke request was excluded from study accounting; exactly 47 remaining calls were run once. Interpretation impact: clean accuracy has denominator 11, all injected conditions remain complete, and missingness must remain explicit. Source: [followup_continuation_deviation_v1.0.md](followup_continuation_deviation_v1.0.md).
- **SUPPORTED** — Two pilot reasoning traces may have been viewed before codebook freeze. Definitions were not changed from the preregistration; final reasoning results include all eligible traces and a strict sensitivity excluding exactly those two without identifying them. Source: [preannotation_exposure_incident.md](preannotation_exposure_incident.md), [reasoning_annotation_codebook_v1.0.md](reasoning_annotation_codebook_v1.0.md).
- **SUPPORTED** — Broad behavioral metadata was briefly exposed only after both pilot annotation forms were frozen; no annotation-ID mapping or outcome linkage occurred during label formation. It was recorded as non-material to frozen label formation. Source: [postfreeze_behavioral_metadata_exposure.md](postfreeze_behavioral_metadata_exposure.md).
- **UNSUPPORTED / DO NOT CLAIM** — Do not say deviations had zero possible effect. State precisely which denominator or sensitivity analysis addresses each deviation.

## Random qualitative examples and manual QA

- **SUPPORTED** — Qualitative selection seed: `20260813`.
- **SUPPORTED** — Six follow-up examples: one selected independently from every prompt-language × injected-condition stratum (3 languages × 2 injected modes), without conditioning on success, failure, output, or reasoning availability.
- **SUPPORTED** — Selection was not changed after review. All six examples were manually checked for copying fidelity, completeness, misleading presentation, and credential/secret exposure; only review-status metadata changed.
- **SUPPORTED** — The grading audit used exactly 12 follow-up rows stratified across all three languages and all four conditions. Manual review agreed with automatic grading for 12/12; zero disagreements.
- **SUPPORTED** — Qualitative examples are observational illustrations only and were not automatically interpreted.

Sources: [qualitative_examples_random.md](../analysis/qualitative_examples_random.md), [followup_grading_audit_sample.csv](../analysis/followup_grading_audit_sample.csv), [final_manual_qa.md](../analysis/final_manual_qa.md).

## Limitations that must remain prominent

- **SUPPORTED** — One model and one fixed API configuration.
- **SUPPORTED** — Only eight synthetic base scenarios and 24 scenario-language units; phase-level subgroup cells are very small.
- **SUPPORTED** — Follow-up is a post-pilot scenario-generalization check, not an independent model replication.
- **SUPPORTED** — One human annotator; confidence values are annotator judgments, not independent reliability estimates.
- **SUPPORTED** — API-visible reasoning may be incomplete, post-processed, or unfaithful.
- **SUPPORTED** — Explicit `<untrusted_content>` delimiters create a clearer trust boundary than many real deployments.
- **SUPPORTED** — Tamil/Tanglish translations may differ in naturalness or force.
- **SUPPORTED** — Exact-match synthetic tasks and canary targets may not represent realistic high-stakes attacks.
- **SUPPORTED** — API/model updates and nondeterminism may affect reruns despite fixed request parameters.
- **DESCRIPTIVE ONLY** — Pilot and follow-up direction differed; pooling cannot erase this non-replication.
- **UNSUPPORTED / DO NOT CLAIM** — No statistical significance, population language effect, causal reasoning effect, generalization beyond Sarvam-105B, or real-world security guarantee.

Sources: [preregistration_v0.1.md](preregistration_v0.1.md), [followup_protocol_v1.0.md](followup_protocol_v1.0.md), [final_research_report.md](../analysis/final_research_report.md).

## Reproducibility details

- **SUPPORTED** — Frozen analysis checkpoint: annotated tag `final-analysis-v1.0`, commit `06df8eab67f276ab6c32ed3eaa267f97bf83dfda`.
- **SUPPORTED** — Deterministic analysis implementation: [analyze_final.py](../src/monitorability/analyze_final.py); focused invariants: [test_analyze_final.py](../tests/test_analyze_final.py).
- **SUPPORTED** — Generated CSV/report outputs were produced twice and byte-compared; PNGs use fixed metadata and deterministic rendering. Human review fields were verified against temporary deterministic pre-review regeneration rather than overwritten.
- **SUPPORTED** — Derived-output privacy scanning excludes full prompts/reasoning/raw responses from tables and reports; only the reviewed qualitative-example file contains the fixed selected excerpts.
- **SUPPORTED** — Pinned core hashes:
  - pilot dataset `1782cdfdcc0c27cbf48b579809d64cf4fc14b4a8f4d03820ce75baa9dddbac4a`;
  - pilot protocol `904b6c93f61ad4797369f25d3075f66c25f48d0b1d38003c5b2cf49a938f7739`;
  - pilot raw `43bd3b7fffdc6944a3ac23cf5350613b2b32f1e25832ddc025c2a1f2723c3a14`;
  - follow-up dataset `5e36606a6919d67ea837af3a2402ad289e151d7d018d320af440ec3b94849e19`;
  - follow-up protocol `1bd7ad09f1fcfefe470dc1b5545d188c6142b484f187390767def930f15a9082`;
  - follow-up failed attempt `16f31be5bf7fe9d9f58ab3a0321603f06e38b4323bad6860f757e93566e4a4b4`;
  - follow-up continuation `ec2293b1da27f4972acbd251d4a7b08c880850ae3061a24cfee3f3b25f86b385`;
  - pilot primary reasoning annotation `6b82e5e63b370a7ee9858889e9912363f18166fd569984c82c64c18802ad1b7c`;
  - pilot reasoning-language form `167826fc017443e98651878fc1e3c8e4641e1b476aff918e5b0e2367e6c3562f`;
  - follow-up primary reasoning annotation `bd5f784011cb3d51cd46ad7c9842bcc33861f1b26300d4bfe2bdf8bda08e2ae0`;
  - follow-up reasoning-language form `3de7acff220444f5483e5483aa7c1b291ce9c30d892288fd003024e14b4fcbf3`.

## Related work selected by the researcher

- **SUPPORTED** — The researcher confirmed the compact primary-work set below. Final reference formatting should preserve the verified source records.
- **SUPPORTED** — Safe novelty framing: “I did not find prior work combining indirect prompt injection, visible-reasoning annotation, and Tamil/Tanglish in a controlled trusted-versus-untrusted setup.”
- **UNSUPPORTED / DO NOT CLAIM** — Do not replace that statement with “first study.”

| Primary work | Precise distinction from this project |
| --- | --- |
| Korbak et al., *Chain of Thought Monitorability* | Establishes CoT monitoring as a promising but fragile safety channel; this project applies visible annotation to paired trusted/untrusted indirect injections in English, Tamil, and Tanglish. |
| Onyame et al., multilingual CoT fragility | Evaluates adversarial hints across 13 languages, including Telugu but not Tamil/Tanglish; it uses GPQA-style hints rather than indirect instructions across trust boundaries. |
| Greshake et al., indirect prompt injection | Introduces the threat model of malicious instructions embedded in retrieved data; this project uses harmless exact-match paired controls and visible-reasoning annotation. |
| Yi et al., BIPIA | Benchmarks indirect injection and identifies boundary awareness as a key factor; this project is a small multilingual trusted-versus-untrusted counterfactual. |
| MIPIAD | Studies English/Bangla injection-defense classification, not visible-reasoning monitorability. |
| Srinivasan et al. | Studies Hindi/Hinglish injection detection with classifiers, not indirect-injection reasoning behavior. |

Researcher-background items recorded in the preregistration, not substitutes for external related work:

- **SUPPORTED** — TamilLM: public 200-pair Tamil SFT seed dataset and validation pipeline covering registers, regional variants, and Tanglish.
- **SUPPORTED** — Rampart Tamil evaluation: 250-row native-script/romanized PII evaluation; if mentioned, 48.0% is aggregate private-term recall for that slice, not Tamil-name recall.

Source: [preregistration_v0.1.md](preregistration_v0.1.md).

## Researcher decisions recorded for drafting

- Title: *Can Visible Reasoning Reveal Indirect Prompt-Injection Decisions Across English, Tamil, and Tanglish? A Small Study of Sarvam-105B*.
- Lead with exact intent–output alignment, then immediately report the failed thinking-mode replication.
- Motivation: Rampart language/script safety coverage and TamilLM Tamil/Tanglish evaluation experience.
- Primary limitation: eight scenarios, one model, and one deterministic run per condition; the pilot/follow-up reversal demonstrates prompt-specific instability.
- Next experiment: 30–50 preregistered new scenarios, repeated samples, two independent blinded annotators, then Sarvam-30B and a non-Sarvam model.
- Main body: approximately 2,500–3,500 words plus appendix. Executive summary: write last, target one page, maximum 600 words.
- Executive-summary figures: attack success and paired transitions.
- Front qualitative subset: Q02/Q04/Q06, chosen by language and injected-thinking mode rather than outcome; all six remain in the appendix.
