from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import ConditionCall
from .normalize import normalize_text
from .providers.base import redact_for_log
from .providers.sarvam import SARVAM_MODEL, SarvamProvider

SMOKE_SYSTEM_PROMPT = "Follow the user instruction and give only the requested final answer."
SMOKE_USER_PROMPT = "Compute 17 * 24 - 29. Reply with the integer only."


def build_smoke_call() -> ConditionCall:
    """Return the fixed non-study, thinking-mode schema-smoke request."""
    return ConditionCall(
        call_id="schema-smoke:en:injected_think",
        scenario_id="schema-smoke",
        attack_family="schema_smoke",
        carrier="non_study",
        language="en",
        condition="injected_think",
        reasoning_mode="on",
        system_prompt=SMOKE_SYSTEM_PROMPT,
        user_prompt=SMOKE_USER_PROMPT,
        trusted_instruction_prefix="",
        expected_benign_answer="379",
        attack_target="not-applicable",
        request_parameters={"reasoning_mode": "on"},
    )


def smoke_preview() -> str:
    body = SarvamProvider.build_request_body(build_smoke_call())
    return "\n".join(
        (
            "schema smoke: offline preview (no network calls)",
            "planned_calls=1",
            f"sanitized_request_body={json.dumps(redact_for_log(body), ensure_ascii=False, sort_keys=True)}",
        )
    )


def validate_smoke_response(response: Mapping[str, Any]) -> None:
    raw = response.get("raw_provider_response")
    choices = raw.get("choices") if isinstance(raw, Mapping) else None
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("schema smoke requires exactly one response choice")
    if response.get("model") != SARVAM_MODEL:
        raise ValueError("schema smoke requires model sarvam-105b")
    if response.get("finish_reason") != "stop":
        raise ValueError("schema smoke requires finish_reason=stop")
    if normalize_text(str(response.get("final_text", ""))) != "379":
        raise ValueError("schema smoke requires final content 379")
    reasoning = response.get("visible_reasoning_text")
    if not isinstance(reasoning, str) or not normalize_text(reasoning):
        raise ValueError("schema smoke requires non-empty reasoning_content")
    usage = response.get("usage")
    if not isinstance(usage, Mapping) or not usage:
        raise ValueError("schema smoke requires captured usage fields")


def _append_jsonl(path: Path, event: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(event), ensure_ascii=False, sort_keys=True) + "\n")


def execute_one_live_smoke(provider: SarvamProvider, output_path: Path) -> dict[str, Any]:
    """Make exactly one provider call, with no retries, and append a safe event."""
    response = provider.generate(build_smoke_call())
    validate_smoke_response(response)
    event = {
        "event_type": "schema_smoke_response",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "planned_calls": 1,
        "completed_calls": 1,
        "model": response["model"],
        "finish_reason": response["finish_reason"],
        "final_text": normalize_text(response["final_text"]),
        "visible_reasoning_text": response["visible_reasoning_text"],
        "usage": redact_for_log(response["usage"]),
        "raw_provider_response": redact_for_log(response["raw_provider_response"]),
    }
    _append_jsonl(output_path, event)
    return event


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preview or explicitly run one Sarvam schema smoke request")
    parser.add_argument("--execute-one-live-call", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("outputs/schema_smoke.jsonl"))
    args = parser.parse_args(argv)
    if not args.execute_one_live_call:
        print(smoke_preview())
        return 0
    try:
        event = execute_one_live_smoke(SarvamProvider(allow_network=True), args.output)
    except Exception as exc:  # Never print provider response text or credentials.
        print(f"schema smoke failed closed: {type(exc).__name__}")
        return 2
    print(f"schema smoke completed_calls={event['completed_calls']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
