"""Guarded offline-first runner for the frozen 48-call Phase 5 follow-up."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import subprocess
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import pilot_run
from .models import CONDITIONS, ConditionCall, ScenarioRecord, expand_conditions
from .providers.sarvam import SARVAM_MODEL, SarvamProvider, build_request_body
from .runner import load_records
from .validation import ValidationError, validate_records

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FOLLOWUP_DATA_PATH = PROJECT_ROOT / "data" / "followup_scenarios.jsonl"
FOLLOWUP_PROTOCOL_PATH = PROJECT_ROOT / "docs" / "followup_protocol_v1.0.md"
FOLLOWUP_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "followup_results.jsonl"
PILOT_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "pilot_results.jsonl"
FOLLOWUP_PREREGISTRATION_TAG = "followup-prereg-v1.0"
FOLLOWUP_PREREGISTRATION_COMMIT = "832e427e4b2f3cc21db619e27ae51cb61d3f3c96"
FOLLOWUP_DATA_SHA256 = "5e36606a6919d67ea837af3a2402ad289e151d7d018d320af440ec3b94849e19"
FOLLOWUP_PROTOCOL_SHA256 = "1bd7ad09f1fcfefe470dc1b5545d188c6142b484f187390767def930f15a9082"
PILOT_RAW_SHA256 = "43bd3b7fffdc6944a3ac23cf5350613b2b32f1e25832ddc025c2a1f2723c3a14"
EXECUTION_ORDER_SEED = 42
TIMEOUT_SECONDS = pilot_run.TIMEOUT_SECONDS
MINIMUM_START_INTERVAL_SECONDS = pilot_run.MINIMUM_START_INTERVAL_SECONDS
MAX_RETRIES = 0
MAXIMUM_NETWORK_ATTEMPTS = 48
EXPECTED_UNIT_ORDER = (
    "P7:ta", "P6:tanglish", "P5:tanglish", "P7:tanglish", "P8:en", "P7:en",
    "P8:tanglish", "P6:en", "P6:ta", "P5:en", "P5:ta", "P8:ta",
)
FIXED_PROVIDER_CONFIGURATION = dict(pilot_run.FIXED_PROVIDER_CONFIGURATION)
PreflightError = pilot_run.PreflightError
FollowupRunError = pilot_run.PilotRunError
FollowupExecutionHalted = pilot_run.PilotExecutionHalted
Runtime = pilot_run.Runtime


@dataclass(frozen=True)
class FollowupPlan:
    records: tuple[ScenarioRecord, ...]
    calls: tuple[ConditionCall, ...]
    hashes: dict[str, str]

    @property
    def call_ids(self) -> tuple[str, ...]:
        return tuple(call.call_id for call in self.calls)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_output(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=PROJECT_ROOT, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise PreflightError("local Git checkpoint inspection failed")
    return result.stdout.strip()


def _actual_hashes() -> dict[str, str]:
    return {"followup_data_sha256": _sha256(FOLLOWUP_DATA_PATH),
            "followup_protocol_sha256": _sha256(FOLLOWUP_PROTOCOL_PATH),
            "pilot_raw_sha256": _sha256(PILOT_OUTPUT_PATH)}


def _assert_pinned_inputs(*, hashes: Mapping[str, str], require_clean_worktree: bool) -> None:
    expected = {"followup_data_sha256": FOLLOWUP_DATA_SHA256,
                "followup_protocol_sha256": FOLLOWUP_PROTOCOL_SHA256,
                "pilot_raw_sha256": PILOT_RAW_SHA256}
    if dict(hashes) != expected:
        raise PreflightError("follow-up frozen input hashes do not match")
    if _git_output("rev-parse", f"{FOLLOWUP_PREREGISTRATION_TAG}^{{commit}}") != FOLLOWUP_PREREGISTRATION_COMMIT:
        raise PreflightError("follow-up preregistration tag does not point to the frozen commit")
    if subprocess.run(["git", "merge-base", "--is-ancestor", FOLLOWUP_PREREGISTRATION_TAG, "HEAD"],
                      cwd=PROJECT_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode:
        raise PreflightError("follow-up preregistration tag is not an ancestor of HEAD")
    if require_clean_worktree and _git_output("status", "--porcelain", "--untracked-files=all"):
        raise PreflightError("live follow-up execution requires a clean Git worktree")
    if TIMEOUT_SECONDS != 120.0 or MINIMUM_START_INTERVAL_SECONDS != 2.1 or MAX_RETRIES != 0 or MAXIMUM_NETWORK_ATTEMPTS != 48:
        raise PreflightError("follow-up operational configuration differs from frozen protocol")
    if FIXED_PROVIDER_CONFIGURATION != pilot_run.FIXED_PROVIDER_CONFIGURATION:
        raise PreflightError("provider configuration differs from frozen original-pilot configuration")


def _ordered_records(records: list[ScenarioRecord]) -> tuple[ScenarioRecord, ...]:
    ordered = list(records)
    random.Random(EXECUTION_ORDER_SEED).shuffle(ordered)
    if tuple(f"{record.scenario_id}:{record.language}" for record in ordered) != EXPECTED_UNIT_ORDER:
        raise PreflightError("deterministic unit order does not match frozen protocol")
    return tuple(ordered)


def _assert_request_pairing(calls: tuple[ConditionCall, ...]) -> None:
    by_id = {call.call_id: call for call in calls}
    for unit in EXPECTED_UNIT_ORDER:
        nonthink, think = by_id.get(f"{unit}:injected_non_think"), by_id.get(f"{unit}:injected_think")
        if nonthink is None or think is None or nonthink.user_prompt.encode() != think.user_prompt.encode():
            raise PreflightError("missing or non-identical injected think/non-think pair")
        nonthink_body, think_body = build_request_body(nonthink), build_request_body(think)
        if nonthink_body.get("model") != SARVAM_MODEL or think_body.get("model") != SARVAM_MODEL:
            raise PreflightError("request model differs from frozen configuration")
        if {k: v for k, v in nonthink_body.items() if k != "reasoning_effort"} != {k: v for k, v in think_body.items() if k != "reasoning_effort"}:
            raise PreflightError("paired request bodies differ beyond reasoning_effort")
        if nonthink_body["reasoning_effort"] is not None or think_body["reasoning_effort"] != "medium":
            raise PreflightError("paired reasoning effort differs from frozen protocol")


def build_plan(*, require_clean_worktree: bool, hashes: Mapping[str, str] | None = None) -> FollowupPlan:
    resolved_hashes = dict(hashes) if hashes is not None else _actual_hashes()
    _assert_pinned_inputs(hashes=resolved_hashes, require_clean_worktree=require_clean_worktree)
    try:
        records = validate_records(load_records(FOLLOWUP_DATA_PATH))
    except (ValidationError, ValueError) as exc:
        raise PreflightError("follow-up data is malformed or not fully human-verified") from exc
    if len(records) != 12:
        raise PreflightError("follow-up must contain exactly 12 verified units")
    ordered = _ordered_records(records)
    calls = tuple(call for record in ordered for call in expand_conditions(record))
    if len(calls) != MAXIMUM_NETWORK_ATTEMPTS or len(set(call.call_id for call in calls)) != MAXIMUM_NETWORK_ATTEMPTS:
        raise PreflightError("follow-up must contain exactly 48 unique calls")
    for start in range(0, len(calls), len(CONDITIONS)):
        if tuple(call.condition for call in calls[start:start + len(CONDITIONS)]) != CONDITIONS:
            raise PreflightError("condition order differs from frozen protocol")
    _assert_request_pairing(calls)
    return FollowupPlan(ordered, calls, resolved_hashes)


def manifest_event(plan: FollowupPlan, *, run_id: str) -> dict[str, Any]:
    return {"event_type": "manifest", "run_id": run_id,
            "frozen_followup_preregistration_tag": FOLLOWUP_PREREGISTRATION_TAG,
            "frozen_followup_preregistration_commit": FOLLOWUP_PREREGISTRATION_COMMIT,
            "hashes": dict(plan.hashes), "provider": "sarvam",
            "provider_configuration": dict(FIXED_PROVIDER_CONFIGURATION),
            "execution_order_seed": EXECUTION_ORDER_SEED, "ordered_call_ids": list(plan.call_ids),
            "planned_unique_calls": MAXIMUM_NETWORK_ATTEMPTS, "maximum_network_attempts": MAXIMUM_NETWORK_ATTEMPTS,
            "timeout_seconds": TIMEOUT_SECONDS, "minimum_request_start_interval_seconds": MINIMUM_START_INTERVAL_SECONDS,
            "max_retries": MAX_RETRIES, "sequential": True}


def _require_live_credential() -> None:
    """Presence-only credential preflight; the value is not logged or retained."""
    api_key = os.environ.get("SARVAM_API_KEY")
    if not isinstance(api_key, str) or not api_key.strip():
        raise PreflightError("live follow-up execution requires a configured credential")


def run_fresh(plan: FollowupPlan, *, runtime: Runtime, output_path: Path = FOLLOWUP_OUTPUT_PATH,
              run_id_factory: Callable[[], str] = lambda: uuid.uuid4().hex) -> int:
    """Execute once append-only. The frozen follow-up protocol authorizes no resume."""
    _require_live_credential()
    if output_path.exists():
        raise FollowupRunError("fresh follow-up run refuses an existing output artifact")
    run_id = run_id_factory()
    pilot_run._append_event(output_path, manifest_event(plan, run_id=run_id))
    reusable_plan = pilot_run.PilotPlan(plan.records, plan.calls, plan.hashes)
    return pilot_run._execute_remaining(reusable_plan, plan.calls, output_path=output_path, run_id=run_id, runtime=runtime)


def offline_preview(plan: FollowupPlan) -> str:
    return "\n".join(("follow-up runner: offline preview (no network calls)",
                      f"followup_preregistration_tag={FOLLOWUP_PREREGISTRATION_TAG}", f"planned_units={len(plan.records)}",
                      f"planned_unique_calls={len(plan.calls)}", f"maximum_network_attempts={MAXIMUM_NETWORK_ATTEMPTS}",
                      f"execution_order_seed={EXECUTION_ORDER_SEED}",
                      f"ordered_units={json.dumps([f'{r.scenario_id}:{r.language}' for r in plan.records])}",
                      f"condition_order={json.dumps(list(CONDITIONS))}", "sequential=true", "execution=READY", "network calls: 0"))


def main(argv: list[str] | None = None, *, provider_factory: Callable[..., SarvamProvider] = SarvamProvider) -> int:
    parser = argparse.ArgumentParser(description="Run the fixed guarded Phase 5 follow-up")
    parser.add_argument("--execute-live-followup", action="store_true")
    args = parser.parse_args(argv)
    try:
        plan = build_plan(require_clean_worktree=args.execute_live_followup)
        if not args.execute_live_followup:
            print(offline_preview(plan)); return 0
        _require_live_credential()
        completed = run_fresh(plan, runtime=Runtime(transport=provider_factory(allow_network=True, timeout=TIMEOUT_SECONDS).generate))
    except (FollowupRunError, PreflightError):
        print("guarded follow-up execution blocked; no further calls will be made"); return 2
    print(f"guarded follow-up completed_calls={completed}"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
