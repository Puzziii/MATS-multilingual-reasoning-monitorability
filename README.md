# Multilingual Reasoning Monitorability: A Small Study of Sarvam-105B

This repository contains the replication package, execution harness, and analysis pipeline for a case study investigating the intersection of **indirect prompt injection (IPI)** and **visible reasoning monitorability** in multilingual contexts (English, Tamil, and Tanglish) using Sarvam-105B.

This study was conducted as a MATS application project.

## Research Question

When an instruction is embedded inside explicitly untrusted content:
1. Does Sarvam-105B follow or resist it?
2. Does the model explicitly recognize the content as untrusted in its API-visible reasoning?
3. Do observed behavior and visible-reasoning patterns differ across English, Tamil, and Tanglish?

## Key Findings

- **Reasoning Monitorability:** When the model thought out loud and produced non-empty reasoning (20/24 traces), it consistently noticed the payload and frequently stated an intent to ignore it. Intent explicitly stated in the reasoning strongly corresponded with the final outcome (17 benign outcomes aligned with `intent_ignore`, and 3 attack successes aligned with `intent_follow`).
- **Thinking as a Defense (Failed Replication):** The initial pilot suggested that thinking might serve as a strong defense against IPI. However, this effect did not replicate in the follow-up sample. In the follow-up, turning reasoning on actually increased attack success.
- **Multilingual Impact:** The study did not find conclusive evidence of a population-level difference in vulnerability between English, Tamil, and Tanglish. Sample sizes were deliberately kept small for this descriptive study.

## Workflow and Methodology

This project was executed through a structured, multi-phase experimental workflow, driven by a collaboration between a human researcher and autonomous AI coding agents.

### Collaborative Model
- **Human Researcher (Applicant):** Selected the research question, designed the controls, verified all multilingual prompts (English, Tamil, Tanglish), manually annotated the outcome-blind reasoning traces, audited the grading, interpreted the findings, and directed the strict freeze protocol.
- **AI Coding Agents (Claude Opus / Gemini Pro):** Implemented the execution harness, offline schema validations, execution safeguards, `pytest` suites, data pipelines, and deterministic analysis scripts based on the applicant's exact specifications.
- **Experimental Target Model (Sarvam-105B):** The LLM under test, which evaluated the injected and trusted prompts across all conditions to produce the experimental responses and API-visible reasoning.

### Experimental Phases
1. **Phases 1–3 (Preparation & Pilot):** Protocol review, implementation of the guarded pilot runner, and execution of the first 48-call pilot study.
2. **Phase 4 (Pilot Analysis & Blinding):** Implementation of deterministic behavioral grading, exposure audits, outcome-blind reasoning annotation (to prevent bias), and manual verification of pilot results.
3. **Phase 5 (Follow-up Study):** Implementation of the follow-up runner, safe handling of provider API incidents (HTTP 403s), and execution of the 48-call follow-up study to test the replication of the pilot's findings.
4. **Phase 6 (Final Analysis & Reporting):** Outcome-blind annotation of follow-up reasoning, final unblinded joins, deterministic generation of combined figures/tables, and documentation of all findings into the final frozen report.

## Repository Structure

- `docs/`: Preregistration, execution protocols, freezing guidelines, the final report drafts, and qualitative examples.
- `data/`: Frozen synthetic scenarios (`pilot_scenarios.jsonl`, `followup_scenarios.jsonl`).
- `src/monitorability/`: Execution harness, schema smoke checks, grading, and result-generation logic.
- `analysis/`: Generated figures and tabular results.
- `tests/`: Validations and preregistration integrity tests.

## Setup and Installation

The execution harness and analysis scripts require Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Execution and Analysis

To run the preregistration tests and integrity checks:

```bash
pytest -q
```

To run a dry-run preview of the execution pipeline (offline):

```bash
python -m monitorability.runner --dry-run data/pilot_scenarios.jsonl
```

To run the offline schema smoke preview:

```bash
python -m monitorability.schema_smoke
```

To reproduce the analysis CSVs and figures, run:

```bash
python src/monitorability/analyze_final.py
```
