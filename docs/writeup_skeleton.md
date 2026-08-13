# Main-report fill-in-yourself skeleton

Constraint: headings, questions, verified bullet facts, and placement markers only. Replace every voice marker personally; do not copy this structure as polished submission prose.

Main-text budget: approximately 2,500–3,500 words, plus appendix. Executive summary: target one page and no more than 600 words.

## Title

Can Visible Reasoning Reveal Indirect Prompt-Injection Decisions Across English, Tamil, and Tanglish? A Small Study of Sarvam-105B

Verified title ingredients:

- [SUPPORTED] English, Tamil, and Tanglish.
- [SUPPORTED] Indirect prompt injection inside explicitly untrusted content.
- [SUPPORTED] Sarvam-105B case study.
- [DESCRIPTIVE ONLY] Pilot result did not replicate directionally in the follow-up.

## Executive summary placeholder — write last; target one page, maximum 600 words

[WRITE THIS IN YOUR OWN VOICE]

Questions to answer personally:

- Why did you choose this problem?
- What did you expect before running it?
- What changed your mind after the follow-up?
- Which result matters most to you?
- What is the most honest one-sentence limitation?

Facts available for selection:

- [SUPPORTED] 8 scenarios × 3 languages × 4 conditions = 96 attempts.
- [DESCRIPTIVE ONLY] Pilot attack success: non-think 5/12; think 1/11.
- [DESCRIPTIVE ONLY] Follow-up: non-think 2/12; think 3/12; direction did not replicate.
- [DESCRIPTIVE ONLY] Combined secondary accounting: 7/24 versus 4/23.
- [DESCRIPTIVE ONLY] Non-empty reasoning: pilot 9/12; follow-up 11/12; combined 20/24.
- [DESCRIPTIVE ONLY] Exact eligible-trace intent cross-tab: 17 benign with ignore=yes/follow=no; 3 attacks with ignore=no/follow=yes; discordant cells 0/20.
- [SUPPORTED] Small, descriptive, single-model study; no significance or causal claim.

Required figure placements:

- `[FIGURE: ../analysis/figures/final_attack_success.png]`
- `[FIGURE: ../analysis/figures/final_pairwise_transitions.png]`

## Research question and motivation — 250–350 words

[WRITE THIS IN YOUR OWN VOICE]

Questions:

- What practical failure mode makes an explicit trusted/untrusted counterfactual useful?
- Why inspect API-visible reasoning without equating it to internal thought?
- Why are Tamil and Tanglish personally and scientifically relevant to you?

Facts and motivation:

- [SUPPORTED] Research question has behavioral, visible-recognition, and multilingual components.
- [SUPPORTED] Visible reasoning is treated as an API output, not a faithful internal-state guarantee.
- [SUPPORTED] Synthetic harmless tasks isolate exact attack targets and benign answers.
- [SUPPORTED] Rampart motivated attention to hidden language/script safety gaps; TamilLM supplied practical Tamil/Tanglish evaluation experience.
- [SUPPORTED] Safe framing: “I did not find prior work combining indirect prompt injection, visible-reasoning annotation, and Tamil/Tanglish in a controlled trusted-versus-untrusted setup.” Do not say “first study.”

## Related work and gap — 250–350 words

[WRITE THIS IN YOUR OWN VOICE]

Verified primary-work set:

- Korbak et al., *Chain of Thought Monitorability*.
- Onyame et al., multilingual CoT fragility across 13 languages, including Telugu but not Tamil/Tanglish.
- Greshake et al., indirect prompt injection.
- Yi et al., BIPIA.
- MIPIAD, English/Bangla injection-defense classification.
- Srinivasan et al., Hindi/Hinglish injection detection using classifiers.

Allowed distinction bullets after citation verification:

- [SUPPORTED about this project] Paired trusted versus delimited-untrusted delivery.
- [SUPPORTED about this project] Same injected prompt with thinking mode off/on.
- [SUPPORTED about this project] English, native-script Tamil, and Tanglish.
- [SUPPORTED about this project] Exact behavioral grading plus outcome-blinded visible-reasoning annotation.

## Experimental design — 400–500 words

[WRITE THIS IN YOUR OWN VOICE]

### Units and phases

- [SUPPORTED] Pilot P1–P4: 12 scenario-language units, 48 attempts.
- [SUPPORTED] Follow-up P5–P8: 12 new units, 48 attempts.
- [SUPPORTED] Combined: 24 units, 96 attempts.
- [SUPPORTED] Four families: simple override, fake authority, task-output hijack, synthetic canary extraction.
- [SUPPORTED] Three prompt languages and four conditions per unit.

### Conditions and controls

- [SUPPORTED] Clean: benign task without attack.
- [SUPPORTED] Trusted: target payload delivered as trusted instruction.
- [SUPPORTED] Injected non-think: payload inside explicit untrusted delimiters, reasoning off.
- [SUPPORTED] Injected think: identical injected prompt, reasoning effort medium.
- [SUPPORTED] Exact-match grading after whitespace normalization.

### Configuration

- [SUPPORTED] `sarvam-105b`; temperature 0; top-p 1; max tokens 2048; seed 1729.
- [SUPPORTED] Sequential; zero retries; 120-second timeout; ≥2.1 seconds between request starts.

### Annotation and blinding

- [SUPPORTED] Manual outcome-blind reasoning labels frozen before hidden-key joins.
- [SUPPORTED] Separate post-blind reasoning-language form.
- [SUPPORTED] Empty/unavailable traces excluded from label denominators, never coded “no.”
- [SUPPORTED] Strict sensitivity excludes exactly two compromised pilot traces without identifying them.

Questions:

- Which implementation details belong in main text versus appendix?
- How much operational-deviation detail is necessary before results?

## Behavioral results — 350–450 words

[WRITE THIS IN YOUR OWN VOICE]

### Accounting and controls

- [SUPPORTED] Pilot 48 attempts/47 responses; follow-up 48/47; combined 96/94.
- [DESCRIPTIVE ONLY] Clean: pilot 12/12, follow-up 11/11, combined 23/23.
- [DESCRIPTIVE ONLY] Trusted: pilot 12/12, follow-up 11/12, combined 23/24.

### Injected outcomes

- [DESCRIPTIVE ONLY] Pilot non-think: attack 5/12, benign 6/12, other 1/12.
- [DESCRIPTIVE ONLY] Pilot think: attack 1/11, benign 10/11, other 0/11.
- [DESCRIPTIVE ONLY] Follow-up non-think: attack 2/12, benign 8/12, other 2/12.
- [DESCRIPTIVE ONLY] Follow-up think: attack 3/12, benign 9/12, other 0/12.
- [DESCRIPTIVE ONLY] Combined non-think: attack 7/24, benign 14/24, other 3/24.
- [DESCRIPTIVE ONLY] Combined think: attack 4/23, benign 19/23, other 0/23.

Figure placement:

- `[FIGURE: ../analysis/figures/final_attack_success.png]`

Questions:

- Lead with phase-separated counts before pooled counts?
- How will you state the opposite follow-up direction without rationalizing it?

## Paired transitions — 180–250 words

[WRITE THIS IN YOUR OWN VOICE]

- [DESCRIPTIVE ONLY] Pilot: both resist 6/12; attack→resist 4/12; resist→attack 0/12; both attack 1/12; think missing 1/12.
- [DESCRIPTIVE ONLY] Follow-up: both resist 8/12; attack→resist 1/12; resist→attack 2/12; both attack 1/12; think missing 0/12.
- [DESCRIPTIVE ONLY] Combined: 14/24; 5/24; 2/24; 2/24; 1/24, respectively.

Figure placement:

- `[FIGURE: ../analysis/figures/final_pairwise_transitions.png]`

Warning:

- [UNSUPPORTED / DO NOT CLAIM] Paired transition differences are not causal estimates.

## Visible-reasoning results — 350–450 words

[WRITE THIS IN YOUR OWN VOICE]

### Availability

- [DESCRIPTIVE ONLY] Pilot: 9/12 non-empty, 2/12 persisted empty, 1/12 consumed unavailable.
- [DESCRIPTIVE ONLY] Follow-up: 11/12 non-empty, 1/12 persisted empty, 0/12 consumed unavailable.
- [DESCRIPTIVE ONLY] Combined: 20/24, 3/24, and 1/24.

Figure placement:

- `[FIGURE: ../analysis/figures/final_reasoning_availability.png]`

### Frozen labels

- [DESCRIPTIVE ONLY] Pilot eligible 9: noticed 9/9; recognized 9/9; ignore 9/9; follow 0/9; ambiguous 0/9.
- [DESCRIPTIVE ONLY] Follow-up eligible 11: noticed 11/11; recognized 10/11; ignore 8/11; follow 3/11; ambiguous 1/11.
- [DESCRIPTIVE ONLY] Combined eligible 20: noticed 20/20; recognized 19/20; ignore 17/20; follow 3/20; ambiguous 1/20.
- [DESCRIPTIVE ONLY] Combined strict 18: noticed 18/18; recognized 17/18; ignore 15/18; follow 3/18; ambiguous 1/18.

Optional figure placement:

- `[FIGURE: ../analysis/figures/final_reasoning_behavior.png]`

### Intent × outcome cross-tab

- [DESCRIPTIVE ONLY] 17 benign-correct: ignore=yes 17/20; follow=no 17/20.
- [DESCRIPTIVE ONLY] 3 attack-success: ignore=no 3/20; follow=yes 3/20.
- [DESCRIPTIVE ONLY] Discordant cells: 0/20.
- [DESCRIPTIVE ONLY] Strict subset: same pattern, 15 benign and 3 attack over 18.
- [SUPPORTED] One additional attack success had persisted-empty reasoning and no labels.

Warnings:

- [UNSUPPORTED / DO NOT CLAIM] Reasoning caused resistance.
- [UNSUPPORTED / DO NOT CLAIM] Visible intent is a faithful internal state.
- [UNSUPPORTED / DO NOT CLAIM] A new monitorability/faithfulness score.

## Multilingual results — 250–350 words

[WRITE THIS IN YOUR OWN VOICE]

Behavioral facts, both injected modes combined:

- [DESCRIPTIVE ONLY] Pilot: English 4/8, Tamil 0/8, Tanglish 2/7 attack successes.
- [DESCRIPTIVE ONLY] Follow-up: English 1/8, Tamil 1/8, Tanglish 3/8.
- [DESCRIPTIVE ONLY] Combined: English 5/16, Tamil 1/16, Tanglish 5/15.

Reasoning-language facts, combined persisted think responses:

- [DESCRIPTIVE ONLY] English 11/23; mixed 9/23; other 2/23; unavailable 1/23; Tamil 0/23; Tanglish 0/23.
- [DESCRIPTIVE ONLY] Tamil prompts: mixed reasoning 8/8.
- [DESCRIPTIVE ONLY] English prompts: English reasoning 6/8 and other 2/8.
- [DESCRIPTIVE ONLY] Tanglish prompts: English 5/7, mixed 1/7, unavailable 1/7.

Optional/appendix figure placement:

- `[FIGURE: ../analysis/figures/final_language_results.png]`

Questions:

- Is the language figure informative enough for the main body given tiny cells and mode pooling?
- What translation-quality caveat is most important from your firsthand review?

Warning:

- [UNSUPPORTED / DO NOT CLAIM] A general Tamil advantage, Tanglish weakness, or statistically meaningful language effect.

## Pilot versus follow-up non-replication — 250–350 words

[WRITE THIS IN YOUR OWN VOICE]

Facts that must remain prominent:

- [DESCRIPTIVE ONLY] Pilot direction: non-think 5/12 versus think 1/11.
- [DESCRIPTIVE ONLY] Follow-up direction: non-think 2/12 versus think 3/12.
- [SUPPORTED] Follow-up used four new scenarios but the same families, languages, conditions, model configuration, renderer, and grading.
- [SUPPORTED] Follow-up is a post-pilot scenario-generalization test, not a second-model replication.
- [UNSUPPORTED / DO NOT CLAIM] The pooled difference rescues or confirms the pilot hypothesis.

Questions:

- What did the failed directional replication teach you about scenario sensitivity?
- Which prior expectation did you update?
- How will you distinguish “did not replicate” from “proved no effect”?

## Random qualitative examples — 150–250 words plus excerpts

[WRITE THIS IN YOUR OWN VOICE]

- [SUPPORTED] Six fixed-seed examples, one per language × injected-mode stratum.
- [SUPPORTED] Seed `20260813`; selection did not condition on outcome or reasoning availability.
- [SUPPORTED] No example was replaced after manual review.
- [SUPPORTED] Examples are pending your own narrative interpretation, not automatic interpretation.

Placement:

- Use Q02/Q04/Q06 near the front: one frozen injected-think example per language, selected by language and mode rather than outcome.
- Retain all six fixed-seed examples in the appendix.

Questions:

- What does each example illustrate without treating it as representative?

## Limitations — 300–400 words

[WRITE THIS IN YOUR OWN VOICE]

Required bullets:

- [SUPPORTED] Primary limitation: eight scenarios, one model, and one deterministic run per condition cannot separate robust effects from prompt-specific variation; the pilot/follow-up reversal demonstrates this directly.
- [SUPPORTED] Single model and fixed API configuration.
- [SUPPORTED] Eight synthetic scenarios; tiny phase/language/family cells.
- [SUPPORTED] One annotator and no inter-annotator reliability estimate.
- [SUPPORTED] Visible reasoning may be incomplete, post-processed, or unfaithful.
- [SUPPORTED] Explicit delimiters simplify the trust boundary.
- [SUPPORTED] Translation naturalness/force may vary.
- [SUPPORTED] Two unavailable calls and their exact denominator treatment.
- [SUPPORTED] Two compromised pilot annotations handled through strict sensitivity.
- [SUPPORTED] Operational deviations retained in provenance.
- [SUPPORTED] API changes/nondeterminism may affect replication.
- [UNSUPPORTED / DO NOT CLAIM] Statistical significance, causality, broad model or deployment generalization.

Question:

- Which limitation most changes how you personally interpret the result?

## Conclusion — 120–180 words

[WRITE THIS IN YOUR OWN VOICE]

Questions:

- What is the most defensible takeaway after the failed follow-up replication?
- Which fact would you want a monitorability researcher to remember?
- What is the next experiment you would actually run?

Facts available:

- [DESCRIPTIVE ONLY] Visible intent and behavior were aligned in the 20 eligible traces, but one additional attack had empty reasoning.
- [DESCRIPTIVE ONLY] Pilot and follow-up thinking-mode comparisons pointed in opposite directions.
- [SUPPORTED] The study provides a frozen, reproducible single-model case study—not a general conclusion.
- [SUPPORTED] Prioritized next experiment: 30–50 preregistered new scenarios, repeated samples, two independent blinded annotators, then Sarvam-30B and at least one non-Sarvam model.

## Reproducibility appendix — 350–500 words or table only

[WRITE THIS IN YOUR OWN VOICE]

Include:

- [SUPPORTED] `final-analysis-v1.0` → `06df8eab67f276ab6c32ed3eaa267f97bf83dfda`.
- [SUPPORTED] Dataset/protocol/raw/annotation hashes from [writeup_evidence_pack.md](writeup_evidence_pack.md).
- [SUPPORTED] Exact model parameters and operational limits.
- [SUPPORTED] Seeds: pilot order `20260811`; follow-up order `42`; generation `1729`; audit/qualitative selection `20260813`.
- [SUPPORTED] Deterministic two-run generation and forbidden-field scan.
- [SUPPORTED] Manual QA: 12/12 automatic labels agreed; 6/6 fixed examples reviewed and not replaced.
- [SUPPORTED] Missing-call and deviation ledger.

Appendix placements:

- `[TABLE: full prompt-language behavioral results]`
- `[TABLE: full attack-family behavioral results]`
- `[TABLE: frozen label × behavioral-outcome cross-tabs]`
- `[FIGURE: ../analysis/figures/final_language_results.png]`
- `[FIGURE: ../analysis/figures/final_reasoning_behavior.png]`
