# MATS monitorability scaffold

This repository contains the provider-neutral scaffold for the draft MATS multilingual reasoning-monitorability pilot. The canonical preregistration remains a draft at [`docs/preregistration_v0.1.md`](docs/preregistration_v0.1.md).

The runner renders all four conditions from structured prompt components. Responses and retry evidence are appended to JSONL. The normal pilot runner never enables Sarvam transport. Its only live-capable path is the separate, one-call schema smoke command, which requires an explicit flag.

Standard local checks:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest -q
python -m monitorability.runner --dry-run data/pilot_scenarios.jsonl
python -m monitorability.schema_smoke
```

The schema-smoke preview is offline and contains one fixed non-study arithmetic request. A live smoke call is deliberately opt-in and never runs pilot prompts:

```bash
python -m monitorability.schema_smoke --execute-one-live-call
```
