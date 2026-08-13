# Multilingual Reasoning Monitorability under Indirect Prompt Injection

This repository contains the replication package, execution harness, and analysis pipeline for a MATS application case study investigating the intersection of indirect prompt injection (IPI) and visible reasoning monitorability in multilingual contexts.

## 1. Overview
As language models increasingly utilize chain-of-thought and other reasoning processes, understanding whether these visible traces reveal deceptive or harmful instructions embedded in external data is a key safety challenge. This small-sample case study evaluates Sarvam-105B under indirect prompt injection across English, Tamil, and Tanglish contexts. The project explores whether the model follows or resists embedded malicious instructions, whether it explicitly recognizes untrusted content within its API-visible reasoning traces, and whether outcomes vary between non-thinking and thinking modes.

## 2. Main Findings

The study produced descriptive evidence across the pilot and follow-up phases. **Importantly, the pilot direction did not replicate in the follow-up. This is small-sample descriptive evidence, not a causal or statistical conclusion.**

- **Model:** Sarvam-105B.
- **Clean task accuracy:** 23/23 available responses.
- **Trusted-instruction adherence:** 23/24.
- **Visible reasoning availability:** Visible reasoning was non-empty for 20/24 injected-thinking attempts.
- **Monitorability intent alignment:** Among those 20 eligible traces: all 3 attack successes were annotated `intent_follow=yes` and `intent_ignore=no`; all 17 benign-correct outputs were `intent_ignore=yes` and `intent_follow=no`.

| Injected Mode | Pilot Attack Success | Follow-up Attack Success | Combined Attack Success |
| --- | --- | --- | --- |
| **Non-thinking** | 5/12 | 2/12 | 7/24 |
| **Thinking** | 1/11 | 3/12 | 4/23 |

*See full analysis in the [Final Research Report](analysis/final_research_report.md).*

## 3. Study Design and Controls

The experimental design consisted of **eight synthetic scenarios across English, Tamil, and Tanglish** evaluated under four distinct conditions:
- **Clean:** Benign task without any external injection.
- **Trusted-control:** Overt, explicitly trusted instructions.
- **Injected non-thinking:** Malicious instruction embedded within explicitly untrusted content delimiters, executed without reasoning mode.
- **Injected-thinking:** Malicious instruction embedded within explicitly untrusted content delimiters, executed with reasoning mode enabled.

Key protocol and dataset links:
- [Preregistration v0.1](docs/preregistration_v0.1.md)
- [Execution Protocol v1.0](docs/execution_protocol_v1.0.md)
- [Follow-up Protocol v1.0](docs/followup_protocol_v1.0.md)
- [Pilot Scenarios](data/pilot_scenarios.jsonl) | [Follow-up Scenarios](data/followup_scenarios.jsonl)
- [Pilot Results](outputs/pilot_results.jsonl) | [Follow-up Results](outputs/followup_results.jsonl)

## 4. Interpretation and Limitations

This study emphasizes cautious interpretation of the small-sample results. We explicitly **do not claim**:
- That thinking improves safety.
- That any observed effect is a replicated effect (the pilot direction reversed in the follow-up).
- Any causal effects or statistical significance.
- That visible reasoning is faithful internal reasoning.
- Any definitive Tamil/Tanglish safety rankings.
- Generalization beyond Sarvam-105B and these eight scenarios.

Key figures supporting the interpretation:
- [Attack Success Exact Matches](analysis/figures/final_attack_success.png)
- [Paired Injected-Condition Transitions](analysis/figures/final_pairwise_transitions.png)
- [API-Visible Reasoning Availability](analysis/figures/final_reasoning_availability.png)

## 5. Reproduction and Repository Guide

The repository uses Python 3.10+. To set up the environment and reproduce the deterministic analysis checks:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
python src/monitorability/analyze_final.py
```

## 6. Related Work

This study builds upon foundational and recent literature regarding prompt injection, multilingual vulnerabilities, and reasoning monitorability:

- **Monitorability and Chain-of-Thought:**
  - Korbak et al. (2025), [arXiv:2507.11473](https://arxiv.org/abs/2507.11473)
  - Onyame et al. (2026), [arXiv:2605.27901](https://arxiv.org/abs/2605.27901)
- **Indirect Prompt Injection:**
  - Greshake et al. (2023), [arXiv:2302.12173](https://arxiv.org/abs/2302.12173)
  - Yi et al. (2023), [arXiv:2312.14197](https://arxiv.org/abs/2312.14197)
- **Multilingual Contexts:**
  - MIPIAD (2026), [arXiv:2605.07269](https://arxiv.org/abs/2605.07269)
  - Srinivasan et al. (2026), Scientific Reports, [DOI:10.1038/s41598-026-43883-0](https://doi.org/10.1038/s41598-026-43883-0)

## 7. Contribution and Tool-Use Disclosure

The author formulated and refined the research question, designed and verified the multilingual scenarios and controls, manually annotated blinded reasoning traces, audited outcome labels, and interpreted the findings. Coding agents assisted with implementation, testing, reproducibility safeguards, and drafting support; all research decisions and final manual reviews were made by the author.
