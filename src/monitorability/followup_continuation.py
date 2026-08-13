"""Guarded, no-resume continuation for the frozen Phase 5 follow-up recovery."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import uuid
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from . import followup_run, pilot_run
from .models import ConditionCall
from .providers.sarvam import SarvamProvider


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FAILED_ATTEMPT_PATH = PROJECT_ROOT / "outputs" / "followup_results_attempt1_403.jsonl"
SMOKE_PATH = PROJECT_ROOT / "outputs" / "followup_auth_smoke.jsonl"
CONTINUATION_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "followup_results.jsonl"
DEVIATION_PATH = PROJECT_ROOT / "docs" / "followup_continuation_deviation_v1.0.md"
FAILED_ATTEMPT_SHA256 = "16f31be5bf7fe9d9f58ab3a0321603f06e38b4323bad6860f757e93566e4a4b4"
SMOKE_SHA256 = "da52c7445445c3582fd7d5cbb3a9cc57c1867b9057988f28fcf9b072e44c4e9f"
DEVIATION_SHA256 = "e686571dfa73cc26e53e0b4001d6274eab062d9a58eea029af78bdea083e0df4"
FOLLOWUP_RUNNER_TAG = "followup-runner-v1.0"
FOLLOWUP_RUNNER_COMMIT = "5cd037b0b9f213c3c6fe2d0e1b966fcbc03670f9"
CONSUMED_CALL_ID = "P7:ta:clean"
FIRST_REMAINING_CALL_ID = "P7:ta:trusted"
LAST_REMAINING_CALL_ID = "P8:ta:injected_think"
PRIOR_CONSUMED_ATTEMPTS = 1
MAXIMUM_CONTINUATION_ATTEMPTS = 47
MAXIMUM_COMBINED_STUDY_ATTEMPTS = 48

PreflightError = followup_run.PreflightError
ContinuationError = followup_run.FollowupRunError
ContinuationHalted = followup_run.FollowupExecutionHalted
Runtime = followup_run.Runtime


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_events(path: Path) -> list[dict[str, Any]]:
    try:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PreflightError("failed-attempt artifact is not valid JSONL") from exc


def _validate_failed_attempt() -> None:
    if _sha256(FAILED_ATTEMPT_PATH) != FAILED_ATTEMPT_SHA256:
        raise PreflightError("failed-attempt artifact hash does not match")
    events = _load_events(FAILED_ATTEMPT_PATH)
    if len(events) != 3 or [event.get("event_type") for event in events] != ["manifest", "request_started", "failure"]:
        raise PreflightError("failed-attempt artifact has an invalid event sequence")
    started, failed = events[1], events[2]
    if started.get("call_id") != CONSUMED_CALL_ID or failed.get("call_id") != CONSUMED_CALL_ID:
        raise PreflightError("failed-attempt artifact does not consume the frozen call")
    if started.get("attempt") != 1 or failed.get("attempt") != 1:
        raise PreflightError("failed-attempt artifact has an invalid attempt number")


def _validate_deviation_and_smoke() -> None:
    if _sha256(DEVIATION_PATH) != DEVIATION_SHA256:
        raise PreflightError("continuation deviation hash does not match")
    if _sha256(SMOKE_PATH) != SMOKE_SHA256:
        raise PreflightError("authorization-smoke artifact hash does not match")


def _validate_runner_checkpoint() -> None:
    if followup_run._git_output("rev-parse", f"{FOLLOWUP_RUNNER_TAG}^{{commit}}") != FOLLOWUP_RUNNER_COMMIT:
        raise PreflightError("follow-up runner tag does not point to the frozen commit")
    if subprocess.run(["git", "merge-base", "--is-ancestor", FOLLOWUP_RUNNER_TAG, "HEAD"],
                      cwd=PROJECT_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                      check=False).returncode:
        raise PreflightError("follow-up runner tag is not an ancestor of HEAD")


def _require_live_credential() -> None:
    """Perform only a non-empty credential check; do not log or retain its value."""
    value = os.environ.get("SARVAM_API_KEY")
    if not isinstance(value, str) or not value.strip():
        raise PreflightError("live continuation requires a configured credential")


def build_continuation_plan(*, require_clean_worktree: bool) -> tuple[followup_run.FollowupPlan, tuple[ConditionCall, ...]]:
    plan = followup_run.build_plan(require_clean_worktree=require_clean_worktree)
    _validate_failed_attempt()
    _validate_deviation_and_smoke()
    _validate_runner_checkpoint()
    if plan.call_ids[0] != CONSUMED_CALL_ID:
        raise PreflightError("frozen full plan no longer begins with the consumed call")
    remaining = plan.calls[PRIOR_CONSUMED_ATTEMPTS:]
    if len(remaining) != MAXIMUM_CONTINUATION_ATTEMPTS or len(set(call.call_id for call in remaining)) != len(remaining):
        raise PreflightError("continuation must contain exactly 47 unique calls")
    if remaining[0].call_id != FIRST_REMAINING_CALL_ID or remaining[-1].call_id != LAST_REMAINING_CALL_ID:
        raise PreflightError("continuation suffix does not match frozen order")
    if CONSUMED_CALL_ID in {call.call_id for call in remaining}:
        raise PreflightError("continuation includes the consumed call")
    if PRIOR_CONSUMED_ATTEMPTS + len(remaining) != MAXIMUM_COMBINED_STUDY_ATTEMPTS:
        raise PreflightError("combined study attempt ceiling is invalid")
    return plan, remaining


def continuation_manifest_event(plan: followup_run.FollowupPlan, remaining: tuple[ConditionCall, ...], *, run_id: str) -> dict[str, Any]:
    return {
        "event_type": "continuation_authorization",
        "run_id": run_id,
        "failed_attempt_sha256": FAILED_ATTEMPT_SHA256,
        "authorization_smoke_sha256": SMOKE_SHA256,
        "continuation_deviation_sha256": DEVIATION_SHA256,
        "consumed_call_id": CONSUMED_CALL_ID,
        "prior_consumed_attempts": PRIOR_CONSUMED_ATTEMPTS,
        "remaining_authorized_calls": len(remaining),
        "maximum_continuation_attempts": MAXIMUM_CONTINUATION_ATTEMPTS,
        "maximum_combined_study_attempts": MAXIMUM_COMBINED_STUDY_ATTEMPTS,
        "first_remaining_call_id": remaining[0].call_id,
        "last_remaining_call_id": remaining[-1].call_id,
        "ordered_remaining_call_ids": [call.call_id for call in remaining],
        "frozen_hashes": dict(plan.hashes),
        "sequential": True,
        "max_retries": 0,
    }


def run_continuation(
    plan: followup_run.FollowupPlan,
    remaining: tuple[ConditionCall, ...],
    *,
    runtime: Runtime,
    output_path: Path = CONTINUATION_OUTPUT_PATH,
    run_id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
) -> int:
    """Write one authorization event, execute one suffix, and never resume."""
    _require_live_credential()
    if output_path.exists():
        raise ContinuationError("continuation refuses an existing output artifact")
    run_id = run_id_factory()
    pilot_run._append_event(output_path, continuation_manifest_event(plan, remaining, run_id=run_id))
    reusable_plan = pilot_run.PilotPlan(plan.records, remaining, plan.hashes)
    return pilot_run._execute_remaining(
        reusable_plan, remaining, output_path=output_path, run_id=run_id, runtime=runtime,
        attempts_already_consumed=PRIOR_CONSUMED_ATTEMPTS,
    )


def offline_preview(plan: followup_run.FollowupPlan, remaining: tuple[ConditionCall, ...]) -> str:
    return "\n".join((
        "follow-up continuation: offline preview (no network calls)",
        f"prior_consumed_attempts={PRIOR_CONSUMED_ATTEMPTS}",
        f"remaining_authorized_calls={len(remaining)}",
        f"first_remaining_call={remaining[0].call_id}",
        f"last_remaining_call={remaining[-1].call_id}",
        f"maximum_combined_study_attempts={MAXIMUM_COMBINED_STUDY_ATTEMPTS}",
        "integrity=READY",
        "network calls: 0",
    ))


def main(argv: list[str] | None = None, *, provider_factory: Callable[..., SarvamProvider] = SarvamProvider) -> int:
    parser = argparse.ArgumentParser(description="Run the guarded 47-call follow-up continuation")
    parser.add_argument("--execute-live-followup-continuation", action="store_true")
    args = parser.parse_args(argv)
    try:
        plan, remaining = build_continuation_plan(require_clean_worktree=args.execute_live_followup_continuation)
        if not args.execute_live_followup_continuation:
            print(offline_preview(plan, remaining))
            return 0
        _require_live_credential()
        provider = provider_factory(allow_network=True, timeout=followup_run.TIMEOUT_SECONDS)
        completed = run_continuation(plan, remaining, runtime=Runtime(transport=provider.generate))
    except (ContinuationError, PreflightError):
        print("guarded follow-up continuation blocked; no further calls will be made")
        return 2
    print(f"guarded follow-up continuation completed_calls={completed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
