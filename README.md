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
