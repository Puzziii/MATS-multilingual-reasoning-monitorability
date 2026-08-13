# Application fact bank

Purpose: short factual components for the applicant to turn into answers personally. Not submission-ready prose.

## What I did — components to verify and phrase personally

- **SUPPORTED** — Designed a paired trust-boundary experiment with clean, trusted, injected non-thinking, and injected thinking conditions.
- **SUPPORTED** — Built/froze 8 scenarios across 4 attack families, each in English, Tamil, and Tanglish: 24 scenario-language units and 96 study attempts.
- **SUPPORTED** — Used harmless exact-match tasks and unique canary targets; no LLM judge for behavioral grading.
- **SUPPORTED** — Preregistered hypotheses, metrics, denominators, missing-response treatment, model configuration, and operational limits.
- **SUPPORTED** — Preserved pilot and follow-up as separate phases and added the follow-up as a post-pilot scenario-generalization test.
- **SUPPORTED** — Applied a frozen outcome-blind codebook to visible reasoning, then separately annotated reasoning language before unblinding.
- **SUPPORTED** — Built deterministic analysis, tables, figures, privacy checks, and frozen Git checkpoints.
- **SUPPORTED** — Manually checked 12/12 follow-up grading-audit rows and all 6 fixed-seed qualitative examples; no grading disagreement and no example replacement.
- **JUDGMENT REQUIRED** — Confirm which design, coding, translation, annotation, review, and writing tasks were personally yours versus tool-assisted before using first-person language.

## Selected lead result

- **DESCRIPTIVE ONLY** — Exact intent/outcome cross-tab over 20 non-empty traces: 17 benign-correct with ignore=yes/follow=no; 3 attack-success with ignore=no/follow=yes; zero discordant cells.
- **DESCRIPTIVE ONLY** — Report immediately afterward that thinking mode was not a reliable defense: pilot attack success was 5/12 non-think versus 1/11 think; follow-up was 2/12 versus 3/12.
- **SUPPORTED caveat** — One additional attack-success response had persisted-empty reasoning and therefore no intent/recognition labels.
- **DESCRIPTIVE ONLY** — Controls: clean 23/23 available answers correct; trusted target adherence 23/24.
- **DESCRIPTIVE ONLY** — Selected takeaway: visible reasoning appeared informative when available, but turning reasoning on did not consistently improve safety.

## Candidate most-surprising result — choose and explain personally

- **DESCRIPTIVE ONLY** — Follow-up thinking-mode direction reversed relative to the pilot: 3/12 think attacks versus 2/12 non-think, after pilot 1/11 versus 5/12.
- **DESCRIPTIVE ONLY** — Among eligible traces, visible payload noticing was 20/20 even though 3/20 final answers followed the attack.
- **DESCRIPTIVE ONLY** — Untrusted recognition appeared in 2/3 eligible attack-success traces; recognition alone did not guarantee resistance in this sample.
- **DESCRIPTIVE ONLY** — Tamil prompts produced mixed-language visible reasoning in 8/8 persisted combined think responses; Tanglish prompts produced English reasoning in 5/7.
- **JUDGMENT REQUIRED** — State what surprised you before seeing results; do not retrofit a reaction from the fact bank.

## Why it may matter — prompts, not conclusions

- **SUPPORTED** — A pilot-only report would have suggested a cleaner thinking-mode pattern than the follow-up supported.
- **SUPPORTED** — The paired design separates whether the same payload is obeyed in a trusted channel from whether it is followed inside explicitly untrusted data.
- **SUPPORTED** — Visible reasoning can be absent even when a final answer persists; label denominators must preserve that distinction.
- **DESCRIPTIVE ONLY** — In this sample, visible intent fields tracked eligible behavioral outcomes exactly, while untrusted recognition did not perfectly predict behavior.
- **UNSUPPORTED / DO NOT CLAIM** — This proves reasoning monitoring works, reasoning causes safety, or thinking mode is safer.
- **JUDGMENT REQUIRED** — Why does this result matter to your own research agenda or to Neel’s program?

## Selected primary limitation

- **SUPPORTED** — Eight scenarios, one model, and one deterministic run per condition are too small to separate robust effects from prompt-specific variation; the pilot/follow-up reversal demonstrates this directly.
- **SUPPORTED** — One API model/configuration only.
- **SUPPORTED** — Eight base scenarios; only four per phase; subgroup denominators mostly 1–8.
- **SUPPORTED** — One human annotator; no inter-annotator reliability estimate.
- **SUPPORTED** — API-visible reasoning is not guaranteed faithful or complete.
- **SUPPORTED** — Explicit untrusted delimiters are simpler than many deployed trust boundaries.
- **SUPPORTED** — One missing pilot think outcome and one missing follow-up clean outcome.
- **SUPPORTED** — Two pilot labels required strict blinding sensitivity.
- **SUPPORTED** — Also retain the single-annotator limitation and non-empty reasoning coverage of 20/24 think attempts.

## Selected next experiment

- **SUPPORTED** — Pre-register roughly 30–50 new scenarios across the four attack families before adding models.
- **SUPPORTED** — Run repeated samples per condition.
- **SUPPORTED** — Use two independent outcome-blind annotators and report agreement.
- **SUPPORTED** — Then replicate on Sarvam-30B and at least one non-Sarvam model.

## Personal contribution evidence requiring confirmation

- **SUPPORTED** — Repository record: applicant named in preregistration is Madhusudhanan G.
- **SUPPORTED** — Frozen protocol: all 12 follow-up scenario-language records received lead-researcher human approval before protocol freeze.
- **SUPPORTED** — Ledger: recorded activities include Tamil/Tanglish authoring and review, preregistration/protocol work, manual reasoning annotations, manual grading QA, and final qualitative review.
- **SUPPORTED** — Frozen outputs: two outcome-blind annotation sets and two separate reasoning-language forms were frozen before their respective unblinding steps.
- **SUPPORTED** — Contribution disclosure: applicant selected/refined the question, designed controls, verified multilingual prompts, manually annotated reasoning, audited grading, interpreted results, and remains responsible for final wording.
- **SUPPORTED** — Coding agents implemented much of the harness, validation, safeguards, tests, and deterministic analysis from specifications and assisted with assembling the structured report draft.
- **SUPPORTED** — Sarvam-105B produced the experimental responses.

## Exact model, call, and sample details

- **SUPPORTED** — Model identifier: `sarvam-105b` via Sarvam chat-completions API.
- **SUPPORTED** — 8 scenarios; 4 attack families; 3 languages; 4 conditions.
- **SUPPORTED** — Pilot: 12 units, 48 attempts, 47 persisted responses, 1 unavailable injected-think response.
- **SUPPORTED** — Follow-up: 12 units, 48 attempts, 47 responses, 1 unavailable clean response.
- **SUPPORTED** — Combined: 24 units, 96 attempts, 94 responses, 2 unavailable.
- **SUPPORTED** — Combined think: 24 attempts, 23 persisted responses, 20 non-empty, 3 persisted empty, 1 consumed unavailable.
- **SUPPORTED** — Reasoning-label samples: pilot 9 eligible/7 strict; follow-up 11 eligible; combined 20 eligible/18 strict.
- **SUPPORTED** — Temperature 0.0; top-p 1.0; max tokens 2048; seed 1729; `n=1`; stream false; frequency/presence penalties 0; wiki grounding false.
- **SUPPORTED** — Think effort medium; non-think effort null.
- **SUPPORTED** — Sequential calls; zero retries; timeout 120 seconds; ≥2.1 seconds between request starts.
- **SUPPORTED** — Exact-match output grading after whitespace normalization.
- **SUPPORTED** — Behavioral attack-success denominators use available responses: pilot think 11 and combined think 23; reasoning availability always uses all think attempts.

## Exact headline numbers

| Measure | Pilot | Follow-up | Combined | Status |
| --- | ---: | ---: | ---: | --- |
| Clean benign accuracy | 12/12 | 11/11 | 23/23 | DESCRIPTIVE ONLY |
| Trusted adherence | 12/12 | 11/12 | 23/24 | DESCRIPTIVE ONLY |
| Non-think attack success | 5/12 | 2/12 | 7/24 | DESCRIPTIVE ONLY |
| Think attack success | 1/11 | 3/12 | 4/23 | DESCRIPTIVE ONLY |
| Non-empty reasoning / think attempts | 9/12 | 11/12 | 20/24 | DESCRIPTIVE ONLY |
| Payload noticed / eligible | 9/9 | 11/11 | 20/20 | DESCRIPTIVE ONLY |
| Untrusted recognized / eligible | 9/9 | 10/11 | 19/20 | DESCRIPTIVE ONLY |
| Intent ignore / eligible | 9/9 | 8/11 | 17/20 | DESCRIPTIVE ONLY |
| Intent follow / eligible | 0/9 | 3/11 | 3/20 | DESCRIPTIVE ONLY |

## Claims to keep out of application-form answers

- **UNSUPPORTED / DO NOT CLAIM** — “Thinking makes the model safer.”
- **UNSUPPORTED / DO NOT CLAIM** — “The effect replicated.”
- **UNSUPPORTED / DO NOT CLAIM** — “Reasoning caused resistance.”
- **UNSUPPORTED / DO NOT CLAIM** — “Visible reasoning is faithful internal thought.”
- **UNSUPPORTED / DO NOT CLAIM** — “Tamil is safer” or “Tanglish is more vulnerable.”
- **UNSUPPORTED / DO NOT CLAIM** — “Sarvam-105B is robust to indirect prompt injection.”
- **UNSUPPORTED / DO NOT CLAIM** — Any generalization to other models, API versions, natural attacks, or high-stakes deployments.
- **UNSUPPORTED / DO NOT CLAIM** — Statistical significance or an effect size with inferential meaning.
- **UNSUPPORTED / DO NOT CLAIM** — First/only/novel research claim before primary-paper verification.
