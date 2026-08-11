from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .grading import grade
from .models import CONDITIONS, ConditionCall, ScenarioRecord, expand_conditions
from .normalize import normalize_response
from .providers.base import Provider, RetryableProviderError, safe_log, sanitize_error
from .providers.mock import MockProvider
from .validation import ValidationError, collect_validation_errors, validate_records


LOGGER = logging.getLogger("monitorability.runner")


def load_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"line {line_number} must contain a JSON object")
            records.append(value)
    return records


def all_condition_calls(records: list[ScenarioRecord]) -> list[ConditionCall]:
    calls: list[ConditionCall] = []
    for record in records:
        calls.extend(expand_conditions(record))
    return calls


def dry_run(records: list[dict[str, Any]]) -> str:
    errors = collect_validation_errors(records)
    lines = [
        "dry_run: no network calls",
        f"planned scenario-language units: {len(records)}",
        f"planned condition calls: {len(records) * len(CONDITIONS)}",
        f"real execution: {'READY' if not errors else 'BLOCKED'}",
    ]
    if errors:
        lines.append("validation reasons:")
        lines.extend(f"- {error}" for error in errors)
    lines.append("network calls: 0")
    return "\n".join(lines)


def _append_jsonl(handle: Any, event: dict[str, Any]) -> None:
    handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    handle.flush()


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def execute(
    records: list[dict[str, Any]],
    provider: Provider,
    output_path: Path,
    *,
    max_retries: int = 2,
) -> int:
    """Execute validated calls and append response/error events to JSONL."""
    if max_retries < 0:
        raise ValueError("max_retries must be non-negative")
    validated = validate_records(records)
    calls = all_condition_calls(validated)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    provider_name = getattr(provider, "name", "unknown")
    completed = 0
    with output_path.open("a", encoding="utf-8") as handle:
        for call in calls:
            attempt = 1
            while True:
                started = time.perf_counter()
                try:
                    provider_response = provider.generate(call)
                    break
                except RetryableProviderError as exc:
                    _append_jsonl(
                        handle,
                        {
                            "event_type": "error",
                            "call_id": call.call_id,
                            "attempt": attempt,
                            "timestamp": _timestamp(),
                            "provider": provider_name,
                            "retryable_status": True,
                            **sanitize_error(exc),
                        },
                    )
                    if attempt > max_retries:
                        raise
                    attempt += 1
            response = normalize_response(
                provider_response,
                call,
                timestamp=_timestamp(),
                latency=time.perf_counter() - started,
                grading_metrics=grade(
                    provider_response.get("final_text", ""),
                    expected_benign_answer=call.expected_benign_answer,
                    attack_target=call.attack_target,
                    condition=call.condition,
                ),
                attempt=attempt,
            )
            _append_jsonl(handle, response.to_dict())
            completed += 1
            safe_log(
                LOGGER,
                "call_complete",
                provider=provider_name,
                call_id=call.call_id,
                scenario_id=call.scenario_id,
                language=call.language,
                condition=call.condition,
                attempt=attempt,
                model=response.model,
            )
    return completed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run or dry-run the MATS pilot scaffold")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--provider", choices=("mock", "sarvam"), default="mock")
    parser.add_argument("--output", type=Path, default=Path("outputs/responses.jsonl"))
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("data", type=Path, default=Path("data/pilot_scenarios.jsonl"), nargs="?")
    args = parser.parse_args(argv)
    records = load_records(args.data)
    if args.dry_run:
        print(dry_run(records))
        return 0
    if args.provider == "sarvam":
        print("Sarvam pilot transport is disabled; only schema-smoke accepts an explicit live-call flag")
        return 2
    try:
        completed = execute(records, MockProvider(), args.output, max_retries=args.max_retries)
    except ValidationError as exc:
        print(f"real execution blocked by validation:\n{exc}")
        return 2
    print(f"completed calls: {completed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
