"""Guarded, fixed-configuration runner for the frozen 48-call pilot."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import random
import subprocess
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .grading import grade
from .models import CONDITIONS, ConditionCall, ScenarioRecord, expand_conditions
from .normalize import normalize_response
from .providers.base import redact_for_log, sanitize_error
from .providers.sarvam import (
    SARVAM_CHAT_COMPLETIONS_URL,
    SARVAM_MODEL,
    SarvamProvider,
    SarvamResponseError,
    build_request_body,
    parse_chat_completion,
)
from .runner import load_records
from .validation import ValidationError, validate_records


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PILOT_DATA_PATH = PROJECT_ROOT / "data" / "pilot_scenarios.jsonl"
PREREGISTRATION_PATH = PROJECT_ROOT / "docs" / "preregistration_v0.1.md"
EXECUTION_PROTOCOL_PATH = PROJECT_ROOT / "docs" / "execution_protocol_v1.0.md"
RESUME_DEVIATION_PATH = PROJECT_ROOT / "docs" / "pilot_attempt_2_resume_deviation.md"
PILOT_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "pilot_results.jsonl"

PREREGISTRATION_TAG = "prereg-v1.0"
PREREGISTRATION_COMMIT = "196f5bcb3ba9589490b1429ca7558085e5682d14"
EXECUTION_PROTOCOL_TAG = "execution-protocol-v1.0"
EXECUTION_PROTOCOL_COMMIT = "94f985bf45760d318073ed73bbd4c7892a7a5cff"
RESUME_DEVIATION_TAG = "pilot-resume-deviation-v1.0"
RESUME_DEVIATION_COMMIT = "d2236f3ecd6521f546e666adeef155be080e9f35"

PREREGISTRATION_SHA256 = "5d9c9fd877e391fe9f6c38bccc8eed9cc829e19e2f05c83bb04c95c548555f77"
PILOT_DATA_SHA256 = "1782cdfdcc0c27cbf48b579809d64cf4fc14b4a8f4d03820ce75baa9dddbac4a"
EXECUTION_PROTOCOL_SHA256 = "904b6c93f61ad4797369f25d3075f66c25f48d0b1d38003c5b2cf49a938f7739"
RESUME_DEVIATION_SHA256 = "edd2e382cc5569517c3231ed99460ee3c0be07a12d129b00778797fdb86145d2"
PRE_RESUME_ARTIFACT_SHA256 = "43268dfcfdd4761aa64718a69b77f17db9bce344f7daef14eba7d770d1c5a64c"
CONSUMED_CALL_ID = "P3:tanglish:injected_think"
CONSUMED_FAILURE_ERROR_TYPE = "SarvamResponseError"
CONSUMED_FAILURE_ERROR_MESSAGE = "Sarvam think response requires non-empty reasoning_content"
PRE_RESUME_ATTEMPTS = 12
PRE_RESUME_SUCCESSES = 11

EXECUTION_ORDER_SEED = 20260811
TIMEOUT_SECONDS = 120.0
MINIMUM_START_INTERVAL_SECONDS = 2.1
MAX_RETRIES = 0
MAXIMUM_NETWORK_ATTEMPTS = 48
EXPECTED_UNIT_ORDER = (
    "P3:ta",
    "P4:ta",
    "P3:tanglish",
    "P4:en",
    "P4:tanglish",
    "P1:tanglish",
    "P2:tanglish",
    "P1:ta",
    "P3:en",
    "P2:ta",
    "P2:en",
    "P1:en",
)

FIXED_PROVIDER_CONFIGURATION: dict[str, Any] = {
    "endpoint": SARVAM_CHAT_COMPLETIONS_URL,
    "model": SARVAM_MODEL,
    "temperature": 0.0,
    "top_p": 1.0,
    "max_tokens": 2048,
    "seed": 1729,
    "n": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "wiki_grounding": False,
    "think_reasoning_effort": "medium",
    "non_think_reasoning_effort": None,
}


class PilotRunError(RuntimeError):
    """Raised when a fixed pilot run cannot proceed safely."""


class PreflightError(PilotRunError):
    """Raised when frozen inputs or repository state do not match."""


class ResumeError(PilotRunError):
    """Raised when an append-only artifact cannot be resumed safely."""


class PilotExecutionHalted(PilotRunError):
    """Raised after a terminal provider failure is durably recorded."""


@dataclass(frozen=True)
class ResumeState:
    run_id: str
    pending_calls: tuple[ConditionCall, ...]
    last_start_epoch: float | None
    prior_attempts: int
    prior_successes: int
    total_attempts: int
    authorization_present: bool


@dataclass(frozen=True)
class GitState:
    preregistration_tag_target: str
    execution_protocol_tag_target: str
    execution_protocol_is_ancestor_of_head: bool
    clean_worktree: bool


@dataclass(frozen=True)
class PilotPlan:
    records: tuple[ScenarioRecord, ...]
    calls: tuple[ConditionCall, ...]
    hashes: dict[str, str]

    @property
    def call_ids(self) -> tuple[str, ...]:
        return tuple(call.call_id for call in self.calls)


@dataclass
class Runtime:
    """Injectable clock, sleeper, and provider transport for deterministic tests."""

    transport: Callable[[ConditionCall], Mapping[str, Any]]
    monotonic: Callable[[], float] = time.monotonic
    epoch_seconds: Callable[[], float] = time.time
    sleep: Callable[[float], None] = time.sleep
    timestamp: Callable[[], str] = lambda: datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise PreflightError(f"git {' '.join(args)} failed")
    return result.stdout.strip()


def inspect_git_state() -> GitState:
    """Collect only local Git state; this function never contacts a remote."""
    preregistration_target = _git_output("rev-parse", f"{PREREGISTRATION_TAG}^{{commit}}")
    protocol_target = _git_output("rev-parse", f"{EXECUTION_PROTOCOL_TAG}^{{commit}}")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", EXECUTION_PROTOCOL_TAG, "HEAD"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0
    clean = not _git_output("status", "--porcelain", "--untracked-files=all")
    return GitState(
        preregistration_tag_target=preregistration_target,
        execution_protocol_tag_target=protocol_target,
        execution_protocol_is_ancestor_of_head=ancestor,
        clean_worktree=clean,
    )


def _actual_hashes() -> dict[str, str]:
    return {
        "preregistration_sha256": _sha256(PREREGISTRATION_PATH),
        "execution_protocol_sha256": _sha256(EXECUTION_PROTOCOL_PATH),
        "pilot_data_sha256": _sha256(PILOT_DATA_PATH),
    }


def _assert_pinned_inputs(
    *,
    hashes: Mapping[str, str],
    git_state: GitState,
    require_clean_worktree: bool,
) -> None:
    expected_hashes = {
        "preregistration_sha256": PREREGISTRATION_SHA256,
        "execution_protocol_sha256": EXECUTION_PROTOCOL_SHA256,
        "pilot_data_sha256": PILOT_DATA_SHA256,
    }
    for name, expected in expected_hashes.items():
        if hashes.get(name) != expected:
            raise PreflightError(f"pinned {name} does not match")
    if git_state.preregistration_tag_target != PREREGISTRATION_COMMIT:
        raise PreflightError("preregistration tag does not point to the frozen commit")
    if git_state.execution_protocol_tag_target != EXECUTION_PROTOCOL_COMMIT:
        raise PreflightError("execution-protocol tag does not point to the frozen commit")
    if not git_state.execution_protocol_is_ancestor_of_head:
        raise PreflightError("execution-protocol tag is not an ancestor of HEAD")
    if require_clean_worktree and not git_state.clean_worktree:
        raise PreflightError("live pilot execution requires a clean Git worktree")


def _assert_fixed_operational_configuration() -> None:
    if TIMEOUT_SECONDS != 120.0:
        raise PreflightError("request timeout differs from execution protocol v1.0")
    if MINIMUM_START_INTERVAL_SECONDS != 2.1:
        raise PreflightError("request-start interval differs from execution protocol v1.0")
    if MAX_RETRIES != 0:
        raise PreflightError("max_retries differs from execution protocol v1.0")
    if MAXIMUM_NETWORK_ATTEMPTS != 48:
        raise PreflightError("maximum network attempts differs from execution protocol v1.0")


def _ordered_records(records: list[ScenarioRecord]) -> tuple[ScenarioRecord, ...]:
    ordered = list(records)
    random.Random(EXECUTION_ORDER_SEED).shuffle(ordered)
    actual = tuple(f"{record.scenario_id}:{record.language}" for record in ordered)
    if actual != EXPECTED_UNIT_ORDER:
        raise PreflightError("deterministic unit order does not match execution protocol v1.0")
    return tuple(ordered)


def _assert_fixed_request_configuration(calls: tuple[ConditionCall, ...]) -> None:
    request_parameter_keys = (
        "temperature",
        "top_p",
        "max_tokens",
        "seed",
        "n",
        "stream",
        "frequency_penalty",
        "presence_penalty",
        "wiki_grounding",
    )
    calls_by_id = {call.call_id: call for call in calls}
    for call in calls:
        body = build_request_body(call)
        if body.get("model") != SARVAM_MODEL:
            raise PreflightError("Sarvam request model differs from the frozen configuration")
        if set(body) != {"model", "messages", "reasoning_effort", *request_parameter_keys}:
            raise PreflightError("Sarvam request body fields differ from the frozen configuration")
        for key in request_parameter_keys:
            if body.get(key) != FIXED_PROVIDER_CONFIGURATION[key]:
                raise PreflightError(f"Sarvam request parameter {key} differs from the frozen configuration")
        if not isinstance(body.get("messages"), list) or len(body["messages"]) != 2:
            raise PreflightError("Sarvam request messages differ from the fixed provider contract")
        expected_reasoning = "medium" if call.reasoning_mode == "on" else None
        if body.get("reasoning_effort") != expected_reasoning:
            raise PreflightError("Sarvam reasoning_effort differs from the frozen configuration")

    for record_key in EXPECTED_UNIT_ORDER:
        nonthink = calls_by_id.get(f"{record_key}:injected_non_think")
        think = calls_by_id.get(f"{record_key}:injected_think")
        if nonthink is None or think is None:
            raise PreflightError("missing paired injected condition call")
        if nonthink.user_prompt.encode("utf-8") != think.user_prompt.encode("utf-8"):
            raise PreflightError("injected think and non-think prompts are not byte-identical")
        nonthink_body = build_request_body(nonthink)
        think_body = build_request_body(think)
        if {
            key: value for key, value in nonthink_body.items() if key != "reasoning_effort"
        } != {
            key: value for key, value in think_body.items() if key != "reasoning_effort"
        }:
            raise PreflightError("paired injected request bodies differ beyond reasoning_effort")
        if nonthink_body["reasoning_effort"] is not None or think_body["reasoning_effort"] != "medium":
            raise PreflightError("paired injected reasoning_effort values do not match the protocol")


def build_plan(
    *,
    require_clean_worktree: bool,
    hashes: Mapping[str, str] | None = None,
    git_state: GitState | None = None,
) -> PilotPlan:
    """Validate the fixed pilot inputs and construct its only permitted call plan."""
    resolved_hashes = dict(hashes) if hashes is not None else _actual_hashes()
    resolved_git_state = git_state if git_state is not None else inspect_git_state()
    _assert_pinned_inputs(
        hashes=resolved_hashes,
        git_state=resolved_git_state,
        require_clean_worktree=require_clean_worktree,
    )
    _assert_fixed_operational_configuration()
    try:
        validated = validate_records(load_records(PILOT_DATA_PATH))
    except (ValidationError, ValueError) as exc:
        raise PreflightError("pilot data is malformed or not fully human-verified") from exc
    if len(validated) != 12:
        raise PreflightError("pilot must contain exactly 12 verified scenario-language units")
    ordered_records = _ordered_records(validated)
    calls = tuple(call for record in ordered_records for call in expand_conditions(record))
    if len(calls) != MAXIMUM_NETWORK_ATTEMPTS or len(set(call.call_id for call in calls)) != MAXIMUM_NETWORK_ATTEMPTS:
        raise PreflightError("pilot must contain exactly 48 unique condition calls")
    for offset in range(0, len(calls), len(CONDITIONS)):
        if tuple(call.condition for call in calls[offset : offset + len(CONDITIONS)]) != CONDITIONS:
            raise PreflightError("within-unit condition order does not match the execution protocol")
    _assert_fixed_request_configuration(calls)
    return PilotPlan(records=ordered_records, calls=calls, hashes=resolved_hashes)


def manifest_event(plan: PilotPlan, *, run_id: str) -> dict[str, Any]:
    return {
        "event_type": "manifest",
        "run_id": run_id,
        "frozen_preregistration_tag": PREREGISTRATION_TAG,
        "frozen_preregistration_commit": PREREGISTRATION_COMMIT,
        "execution_protocol_tag": EXECUTION_PROTOCOL_TAG,
        "execution_protocol_commit": EXECUTION_PROTOCOL_COMMIT,
        "hashes": dict(plan.hashes),
        "provider": "sarvam",
        "provider_configuration": dict(FIXED_PROVIDER_CONFIGURATION),
        "execution_order_seed": EXECUTION_ORDER_SEED,
        "ordered_call_ids": list(plan.call_ids),
        "planned_unique_calls": MAXIMUM_NETWORK_ATTEMPTS,
        "maximum_network_attempts": MAXIMUM_NETWORK_ATTEMPTS,
        "timeout_seconds": TIMEOUT_SECONDS,
        "minimum_request_start_interval_seconds": MINIMUM_START_INTERVAL_SECONDS,
        "max_retries": MAX_RETRIES,
        "sequential": True,
    }


def _append_event(path: Path, event: Mapping[str, Any]) -> None:
    """Append and fsync a sanitized JSONL event before returning."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sanitized = redact_for_log(dict(event))
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(sanitized, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _validate_provider_response(
    response: Mapping[str, Any], call: ConditionCall
) -> dict[str, Any]:
    raw = response.get("raw_provider_response")
    if not isinstance(raw, Mapping):
        raise SarvamResponseError("provider response must retain the raw provider response")
    parsed = parse_chat_completion(raw, reasoning_mode=call.reasoning_mode)
    if parsed["model"] != SARVAM_MODEL:
        raise SarvamResponseError("Sarvam response model differs from the frozen configuration")
    return parsed


def _response_event(
    response: Mapping[str, Any],
    call: ConditionCall,
    *,
    run_id: str,
    timestamp: str,
    latency: float,
) -> dict[str, Any]:
    parsed = _validate_provider_response(response, call)
    normalized = normalize_response(
        parsed,
        call,
        timestamp=timestamp,
        latency=latency,
        grading_metrics=grade(
            parsed["final_text"],
            expected_benign_answer=call.expected_benign_answer,
            attack_target=call.attack_target,
            condition=call.condition,
        ),
        attempt=1,
    ).to_dict()
    normalized["run_id"] = run_id
    normalized["provider"] = "sarvam"
    normalized["usage"] = redact_for_log(parsed["usage"])
    normalized["finish_reason"] = parsed["finish_reason"]
    normalized["raw_provider_response"] = redact_for_log(parsed["raw_provider_response"])
    return normalized


def _is_uncertain(exc: BaseException) -> bool:
    uncertain_types = (TimeoutError, OSError, http.client.HTTPException)
    current: BaseException | None = exc
    while current is not None:
        if isinstance(current, uncertain_types):
            return True
        next_exception = current.__cause__
        current = next_exception if isinstance(next_exception, BaseException) else None
    return False


def _failure_event(
    call: ConditionCall,
    *,
    run_id: str,
    timestamp: str,
    exc: BaseException,
) -> dict[str, Any]:
    return {
        "event_type": "uncertain" if _is_uncertain(exc) else "failure",
        "run_id": run_id,
        "call_id": call.call_id,
        "scenario_id": call.scenario_id,
        "language": call.language,
        "condition": call.condition,
        "provider": "sarvam",
        "attempt": 1,
        "timestamp": timestamp,
        **sanitize_error(exc),
    }


def _wait_for_request_start(last_start_epoch: float | None, runtime: Runtime) -> float:
    if last_start_epoch is not None:
        remaining = MINIMUM_START_INTERVAL_SECONDS - (runtime.epoch_seconds() - last_start_epoch)
        if remaining > 0:
            runtime.sleep(remaining)
    return runtime.epoch_seconds()


def _execute_remaining(
    plan: PilotPlan,
    pending_calls: tuple[ConditionCall, ...],
    *,
    output_path: Path,
    run_id: str,
    runtime: Runtime,
    attempts_already_consumed: int = 0,
    last_start_epoch: float | None = None,
) -> int:
    """Execute a planned suffix sequentially, stopping permanently on any error."""
    if attempts_already_consumed < 0 or attempts_already_consumed + len(pending_calls) > MAXIMUM_NETWORK_ATTEMPTS:
        raise PilotRunError("planned execution exceeds the frozen maximum")
    completed = 0
    for call in pending_calls:
        request_start_epoch = _wait_for_request_start(last_start_epoch, runtime)
        started_at = runtime.monotonic()
        _append_event(
            output_path,
            {
                "event_type": "request_started",
                "run_id": run_id,
                "call_id": call.call_id,
                "scenario_id": call.scenario_id,
                "language": call.language,
                "condition": call.condition,
                "provider": "sarvam",
                "attempt": 1,
                "timestamp": runtime.timestamp(),
                "request_start_epoch": request_start_epoch,
            },
        )
        try:
            provider_response = runtime.transport(call)
            response_event = _response_event(
                provider_response,
                call,
                run_id=run_id,
                timestamp=runtime.timestamp(),
                latency=runtime.monotonic() - started_at,
            )
        except Exception as exc:
            _append_event(
                output_path,
                _failure_event(call, run_id=run_id, timestamp=runtime.timestamp(), exc=exc),
            )
            raise PilotExecutionHalted("provider failure was recorded; manual review is required") from exc
        _append_event(output_path, response_event)
        last_start_epoch = request_start_epoch
        completed += 1
    return completed


def run_fresh(
    plan: PilotPlan,
    *,
    runtime: Runtime,
    output_path: Path = PILOT_OUTPUT_PATH,
    run_id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
) -> int:
    """Write the first manifest and execute the complete fixed plan exactly once."""
    _require_live_credential()
    if output_path.exists():
        raise PilotRunError("fresh pilot run refuses to use an existing output artifact")
    run_id = run_id_factory()
    _append_event(output_path, manifest_event(plan, run_id=run_id))
    return _execute_remaining(
        plan,
        plan.calls,
        output_path=output_path,
        run_id=run_id,
        runtime=runtime,
    )


def _load_jsonl_artifact(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ResumeError("resume requires the original output artifact")
    events: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for number, line in enumerate(handle, start=1):
                if not line.strip():
                    raise ResumeError(f"artifact contains an empty line at {number}")
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ResumeError(f"artifact event {number} is not an object")
                events.append(value)
    except json.JSONDecodeError as exc:
        raise ResumeError("artifact contains malformed JSONL") from exc
    if not events:
        raise ResumeError("artifact is empty")
    return events


def _pre_resume_artifact_sha256(path: Path) -> str:
    """Hash exactly the preserved pre-resume prefix, excluding authorization/events."""
    if not path.exists():
        raise ResumeError("resume requires the original output artifact")
    prefix = bytearray()
    try:
        for number, line in enumerate(path.read_bytes().splitlines(keepends=True), start=1):
            value = json.loads(line.decode("utf-8"))
            if not isinstance(value, dict):
                raise ResumeError(f"artifact event {number} is not an object")
            if value.get("event_type") == "resume_authorization":
                break
            prefix.extend(line)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResumeError("artifact contains malformed JSONL") from exc
    return hashlib.sha256(bytes(prefix)).hexdigest()


def _verify_resume_deviation() -> None:
    target = _git_output("rev-parse", f"{RESUME_DEVIATION_TAG}^{{commit}}")
    if target != RESUME_DEVIATION_COMMIT:
        raise ResumeError("resume-deviation tag does not point to the frozen commit")
    if _sha256(RESUME_DEVIATION_PATH) != RESUME_DEVIATION_SHA256:
        raise ResumeError("resume-deviation document hash does not match")


def _validate_manifest(manifest: Mapping[str, Any], plan: PilotPlan) -> str:
    if manifest.get("event_type") != "manifest":
        raise ResumeError("first artifact event must be a manifest")
    run_id = manifest.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ResumeError("manifest is missing a run_id")
    expected = manifest_event(plan, run_id=run_id)
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ResumeError(f"manifest field does not match fixed protocol: {key}")
    return run_id


def _validate_completed_response(
    event: Mapping[str, Any], call: ConditionCall, *, require_instrumentation: bool
) -> None:
    required = {
        "call_id": call.call_id,
        "scenario_id": call.scenario_id,
        "language": call.language,
        "condition": call.condition,
        "model": SARVAM_MODEL,
        "attempt": 1,
    }
    for key, value in required.items():
        if event.get(key) != value:
            raise ResumeError(f"completed response has invalid {key}")
    if event.get("finish_reason") is not None and not isinstance(event.get("finish_reason"), str):
        raise ResumeError("completed response has invalid finish_reason")
    if not isinstance(event.get("final_text"), str):
        raise ResumeError("completed response is missing final_text")
    if not isinstance(event.get("visible_reasoning_text"), str):
        raise ResumeError("completed response is missing visible_reasoning_text")
    if not isinstance(event.get("usage"), Mapping):
        raise ResumeError("completed response is missing usage")
    if not isinstance(event.get("raw_provider_response"), Mapping):
        raise ResumeError("completed response is missing raw_provider_response")
    if not isinstance(event.get("grading_metrics"), Mapping):
        raise ResumeError("completed response is missing grading_metrics")
    if require_instrumentation:
        if not isinstance(event.get("final_text_available"), bool):
            raise ResumeError("completed response is missing final_text_available")
        if not isinstance(event.get("reasoning_available"), bool):
            raise ResumeError("completed response is missing reasoning_available")
        if not isinstance(event.get("reasoning_character_count"), int):
            raise ResumeError("completed response is missing reasoning_character_count")
        if not isinstance(event.get("reasoning_mode_mismatch"), bool):
            raise ResumeError("completed response is missing reasoning_mode_mismatch")


def _validate_consumed_failure(event: Mapping[str, Any], call: ConditionCall, run_id: str) -> None:
    expected_keys = {
        "event_type",
        "run_id",
        "call_id",
        "scenario_id",
        "language",
        "condition",
        "provider",
        "attempt",
        "timestamp",
        "error_type",
        "error_message",
    }
    if set(event) != expected_keys:
        raise ResumeError("consumed failure does not exactly match the documented event")
    expected = {
        "event_type": "failure",
        "run_id": run_id,
        "call_id": CONSUMED_CALL_ID,
        "scenario_id": call.scenario_id,
        "language": call.language,
        "condition": call.condition,
        "provider": "sarvam",
        "attempt": 1,
        "error_type": CONSUMED_FAILURE_ERROR_TYPE,
        "error_message": CONSUMED_FAILURE_ERROR_MESSAGE,
    }
    for key, value in expected.items():
        if event.get(key) != value:
            raise ResumeError("failure does not match the documented consumed empty-reasoning event")
    if not isinstance(event.get("timestamp"), str) or not event["timestamp"]:
        raise ResumeError("consumed failure is missing timestamp")


def resume_authorization_event(plan: PilotPlan, *, run_id: str) -> dict[str, Any]:
    return {
        "event_type": "resume_authorization",
        "run_id": run_id,
        "deviation_tag": RESUME_DEVIATION_TAG,
        "deviation_commit": RESUME_DEVIATION_COMMIT,
        "deviation_sha256": RESUME_DEVIATION_SHA256,
        "pre_resume_artifact_sha256": PRE_RESUME_ARTIFACT_SHA256,
        "consumed_call_id": CONSUMED_CALL_ID,
        "prior_attempts": PRE_RESUME_ATTEMPTS,
        "prior_successes": PRE_RESUME_SUCCESSES,
        "remaining_authorized_calls": MAXIMUM_NETWORK_ATTEMPTS - PRE_RESUME_ATTEMPTS,
        "next_call_id": "P4:en:clean",
        "maximum_total_attempts": MAXIMUM_NETWORK_ATTEMPTS,
    }


def _validate_resume_authorization(event: Mapping[str, Any], plan: PilotPlan, run_id: str) -> None:
    expected = resume_authorization_event(plan, run_id=run_id)
    if event != expected:
        raise ResumeError("resume_authorization event does not match the frozen deviation")


def _resume_state(plan: PilotPlan, events: list[dict[str, Any]]) -> ResumeState:
    run_id = _validate_manifest(events[0], plan)
    index = 1
    call_index = 0
    pre_attempts = 0
    pre_successes = 0
    consumed = False
    authorization_present = False
    last_start_epoch: float | None = None

    while index < len(events):
        event = events[index]
        if event.get("event_type") == "resume_authorization":
            if authorization_present or call_index != PRE_RESUME_ATTEMPTS:
                raise ResumeError("resume_authorization is out of order")
            if pre_attempts != PRE_RESUME_ATTEMPTS or pre_successes != PRE_RESUME_SUCCESSES or not consumed:
                raise ResumeError("resume_authorization has invalid pre-resume state")
            _validate_resume_authorization(event, plan, run_id)
            authorization_present = True
            index += 1
            continue
        if event.get("event_type") != "request_started":
            raise ResumeError("artifact contains an unknown or out-of-order event")
        if call_index >= len(plan.calls):
            raise ResumeError("artifact exceeds the frozen 48-call limit")
        if call_index >= PRE_RESUME_ATTEMPTS and not authorization_present:
            raise ResumeError("resumed request is missing resume_authorization")
        call = plan.calls[call_index]
        if event.get("call_id") != call.call_id:
            raise ResumeError("artifact request order does not match the fixed call order")
        if event.get("run_id") != run_id or event.get("attempt") != 1:
            raise ResumeError("request_started event is malformed")
        value = event.get("request_start_epoch")
        if not isinstance(value, (int, float)):
            raise ResumeError("request_started event is missing request_start_epoch")
        last_start_epoch = float(value)
        if not authorization_present:
            pre_attempts += 1
        index += 1
        if index == len(events):
            raise ResumeError("request_started event has no terminal event; manual review is required")
        terminal = events[index]
        if terminal.get("run_id") != run_id or terminal.get("call_id") != call.call_id:
            raise ResumeError("terminal event does not match request_started event")
        if terminal.get("event_type") == "response":
            _validate_completed_response(terminal, call, require_instrumentation=authorization_present)
            if not authorization_present:
                pre_successes += 1
        elif terminal.get("event_type") == "failure":
            if authorization_present or call.call_id != CONSUMED_CALL_ID or consumed:
                raise ResumeError("failure event is not the documented consumed call")
            _validate_consumed_failure(terminal, call, run_id)
            consumed = True
        else:
            raise ResumeError("artifact contains an uncertain or unknown terminal event")
        index += 1
        call_index += 1

    if pre_attempts != PRE_RESUME_ATTEMPTS or pre_successes != PRE_RESUME_SUCCESSES or not consumed:
        raise ResumeError("artifact does not match the documented pre-resume attempt")
    if call_index < PRE_RESUME_ATTEMPTS:
        raise ResumeError("artifact does not contain the full documented pre-resume attempt")
    return ResumeState(
        run_id=run_id,
        pending_calls=plan.calls[call_index:],
        last_start_epoch=last_start_epoch,
        prior_attempts=pre_attempts,
        prior_successes=pre_successes,
        total_attempts=call_index,
        authorization_present=authorization_present,
    )


def inspect_resume(plan: PilotPlan, *, output_path: Path = PILOT_OUTPUT_PATH) -> ResumeState:
    """Verify the only authorized consumed failure without mutating the artifact."""
    _verify_resume_deviation()
    if _pre_resume_artifact_sha256(output_path) != PRE_RESUME_ARTIFACT_SHA256:
        raise ResumeError("pre-resume artifact hash does not match the frozen deviation")
    return _resume_state(plan, _load_jsonl_artifact(output_path))


def _ensure_resume_authorization(plan: PilotPlan, output_path: Path, state: ResumeState) -> bool:
    if state.authorization_present:
        return False
    _append_event(output_path, resume_authorization_event(plan, run_id=state.run_id))
    return True


def run_resume(
    plan: PilotPlan,
    *,
    runtime: Runtime,
    output_path: Path = PILOT_OUTPUT_PATH,
) -> int:
    """Resume only the deviation-authorized suffix without repeating a call."""
    _require_live_credential()
    state = inspect_resume(plan, output_path=output_path)
    _ensure_resume_authorization(plan, output_path, state)
    return _execute_remaining(
        plan,
        state.pending_calls,
        output_path=output_path,
        run_id=state.run_id,
        runtime=runtime,
        attempts_already_consumed=state.total_attempts,
        last_start_epoch=state.last_start_epoch,
    )


def offline_preview(plan: PilotPlan) -> str:
    """Return a complete fixed-plan preview without constructing a provider."""
    return "\n".join(
        (
            "pilot runner: offline preview (no network calls)",
            f"frozen_preregistration_tag={PREREGISTRATION_TAG}",
            f"execution_protocol_tag={EXECUTION_PROTOCOL_TAG}",
            f"planned_unique_calls={len(plan.calls)}",
            f"maximum_network_attempts={MAXIMUM_NETWORK_ATTEMPTS}",
            f"timeout_seconds={TIMEOUT_SECONDS}",
            f"minimum_request_start_interval_seconds={MINIMUM_START_INTERVAL_SECONDS}",
            f"max_retries={MAX_RETRIES}",
            "sequential=true",
            f"ordered_call_ids={json.dumps(list(plan.call_ids), ensure_ascii=False)}",
            "network calls: 0",
        )
    )


def resume_preview(plan: PilotPlan, *, output_path: Path = PILOT_OUTPUT_PATH) -> str:
    """Preview the only authorized resume state without credentials or transport."""
    state = inspect_resume(plan, output_path=output_path)
    next_call = state.pending_calls[0].call_id if state.pending_calls else "none"
    return "\n".join(
        (
            "pilot runner: resume preview (no network calls)",
            f"prior_attempts={state.prior_attempts}",
            f"prior_successes={state.prior_successes}",
            "consumed_failures=1",
            f"remaining_calls={len(state.pending_calls)}",
            f"next_call={next_call}",
            f"maximum_total_attempts={MAXIMUM_NETWORK_ATTEMPTS}",
            "resume_integrity=READY",
            "network calls=0",
        )
    )


def _require_live_credential() -> None:
    """Fail before any live artifact or provider action when the key is unusable."""
    api_key = os.environ.get("SARVAM_API_KEY")
    if not isinstance(api_key, str) or not api_key.strip():
        raise PreflightError("live pilot execution requires a configured credential")


def main(
    argv: list[str] | None = None,
    *,
    provider_factory: Callable[..., SarvamProvider] = SarvamProvider,
) -> int:
    parser = argparse.ArgumentParser(description="Run the fixed guarded 48-call MATS pilot")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--execute-live-pilot", action="store_true")
    modes.add_argument("--resume-live-pilot", action="store_true")
    modes.add_argument("--resume-preview", action="store_true")
    args = parser.parse_args(argv)

    live = args.execute_live_pilot or args.resume_live_pilot
    try:
        plan = build_plan(require_clean_worktree=live)
        if args.resume_preview:
            print(resume_preview(plan))
            return 0
        if not live:
            print(offline_preview(plan))
            return 0
        _require_live_credential()
        # SarvamProvider retains its own credential check immediately before
        # HTTPS transport as defence in depth.
        provider = provider_factory(allow_network=True, timeout=TIMEOUT_SECONDS)
        runtime = Runtime(transport=provider.generate)
        completed = (
            run_resume(plan, runtime=runtime)
            if args.resume_live_pilot
            else run_fresh(plan, runtime=runtime)
        )
    except (PilotRunError, PreflightError, ResumeError):
        print("guarded pilot execution blocked; no further calls will be made")
        return 2
    print(f"guarded pilot completed_calls={completed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
