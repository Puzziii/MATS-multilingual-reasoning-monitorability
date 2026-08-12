from __future__ import annotations

import hashlib
import json
import shutil

import pytest

from monitorability import pilot_run
from monitorability.providers.sarvam import SARVAM_MODEL, parse_chat_completion


class FakeClock:
    def __init__(self, value: float) -> None:
        self.value = value
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.value

    def epoch_seconds(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.value += seconds

    def timestamp(self) -> str:
        return "2026-08-12T06:30:00+00:00"


class RecordingProvider:
    def __init__(self, artifact_path, fsync_calls: list[int]) -> None:
        self.artifact_path = artifact_path
        self.fsync_calls = fsync_calls
        self.calls = []
        self.lines_before_first_call: int | None = None
        self.fsync_before_first_call: int | None = None

    def __call__(self, call):
        if not self.calls:
            self.lines_before_first_call = len(self.artifact_path.read_text(encoding="utf-8").splitlines())
            self.fsync_before_first_call = len(self.fsync_calls)
        self.calls.append(call)
        message = {"content": call.attack_target if call.condition == "trusted" else call.expected_benign_answer}
        if call.reasoning_mode == "on":
            message["reasoning_content"] = "synthetic visible reasoning"
        raw = {
            "model": SARVAM_MODEL,
            "choices": [{"message": message, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        return parse_chat_completion(raw, reasoning_mode=call.reasoning_mode)


@pytest.fixture(autouse=True)
def fake_live_credential(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "fake-test-credential")


@pytest.fixture
def plan():
    return pilot_run.build_plan(require_clean_worktree=False)


def _copy_partial_artifact(tmp_path):
    output_path = tmp_path / "pilot_results.jsonl"
    shutil.copyfile(pilot_run.PILOT_OUTPUT_PATH, output_path)
    return output_path


def _runtime(provider, state):
    clock = FakeClock((state.last_start_epoch or 0.0) + pilot_run.MINIMUM_START_INTERVAL_SECONDS + 0.01)
    return pilot_run.Runtime(
        transport=provider,
        monotonic=clock.monotonic,
        epoch_seconds=clock.epoch_seconds,
        sleep=clock.sleep,
        timestamp=clock.timestamp,
    ), clock


def _events(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_documented_partial_artifact_permits_only_the_frozen_offline_resume_plan(plan):
    state = pilot_run.inspect_resume(plan)

    assert state.prior_attempts == 12
    assert state.prior_successes == 11
    assert state.total_attempts == 12
    assert state.authorization_present is False
    assert len(state.pending_calls) == 36
    assert state.pending_calls[0].call_id == "P4:en:clean"
    assert pilot_run.CONSUMED_CALL_ID not in {call.call_id for call in state.pending_calls}

    preview = pilot_run.resume_preview(plan)
    assert "prior_attempts=12" in preview
    assert "prior_successes=11" in preview
    assert "consumed_failures=1" in preview
    assert "remaining_calls=36" in preview
    assert "next_call=P4:en:clean" in preview
    assert "maximum_total_attempts=48" in preview
    assert "resume_integrity=READY" in preview
    assert "network calls=0" in preview


def test_any_failure_other_than_the_documented_consumed_event_blocks_resume(plan, tmp_path, monkeypatch):
    output_path = _copy_partial_artifact(tmp_path)
    events = _events(output_path)
    failure = next(event for event in events if event["event_type"] == "failure")
    failure["error_type"] = "RuntimeError"
    output_path.write_text("".join(json.dumps(event, sort_keys=True) + "\n" for event in events), encoding="utf-8")
    monkeypatch.setattr(pilot_run, "PRE_RESUME_ARTIFACT_SHA256", hashlib.sha256(output_path.read_bytes()).hexdigest())

    with pytest.raises(pilot_run.ResumeError, match="documented consumed"):
        pilot_run.inspect_resume(plan, output_path=output_path)


def test_resume_authorization_is_fsynced_before_transport_and_then_idempotent(plan, tmp_path, monkeypatch):
    output_path = _copy_partial_artifact(tmp_path)
    state = pilot_run.inspect_resume(plan, output_path=output_path)
    fsync_calls: list[int] = []
    monkeypatch.setattr(pilot_run.os, "fsync", lambda descriptor: fsync_calls.append(descriptor))
    provider = RecordingProvider(output_path, fsync_calls)
    runtime, clock = _runtime(provider, state)

    assert pilot_run.run_resume(plan, runtime=runtime, output_path=output_path) == 36
    assert len(provider.calls) == 36
    assert len({call.call_id for call in provider.calls}) == 36
    assert provider.calls[0].call_id == "P4:en:clean"
    assert pilot_run.CONSUMED_CALL_ID not in {call.call_id for call in provider.calls}
    assert provider.lines_before_first_call == 27
    assert provider.fsync_before_first_call == 2
    assert len(fsync_calls) == 73
    assert len(clock.sleeps) == 35

    completed_state = pilot_run.inspect_resume(plan, output_path=output_path)
    assert completed_state.authorization_present is True
    assert completed_state.pending_calls == ()
    assert pilot_run.run_resume(plan, runtime=runtime, output_path=output_path) == 0
    events = _events(output_path)
    assert sum(event["event_type"] == "resume_authorization" for event in events) == 1
    assert sum(event["event_type"] == "request_started" for event in events) == 48
    assert sum(event["event_type"] == "response" for event in events) == 47
    assert sum(event["event_type"] == "failure" for event in events) == 1
    assert len({event["call_id"] for event in events if event["event_type"] == "response"}) == 47


def test_resume_attempt_ceiling_includes_the_consumed_call(plan, tmp_path):
    output_path = _copy_partial_artifact(tmp_path)
    state = pilot_run.inspect_resume(plan, output_path=output_path)
    provider = RecordingProvider(output_path, [])
    runtime, _ = _runtime(provider, state)

    with pytest.raises(pilot_run.PilotRunError, match="frozen maximum"):
        pilot_run._execute_remaining(
            plan,
            state.pending_calls + (state.pending_calls[0],),
            output_path=output_path,
            run_id=state.run_id,
            runtime=runtime,
            attempts_already_consumed=state.total_attempts,
            last_start_epoch=state.last_start_epoch,
        )
    assert provider.calls == []


def test_resume_authorization_helper_does_not_append_twice(plan, tmp_path):
    output_path = _copy_partial_artifact(tmp_path)
    initial = pilot_run.inspect_resume(plan, output_path=output_path)

    assert pilot_run._ensure_resume_authorization(plan, output_path, initial) is True
    authorized = pilot_run.inspect_resume(plan, output_path=output_path)
    assert pilot_run._ensure_resume_authorization(plan, output_path, authorized) is False
    assert sum(event["event_type"] == "resume_authorization" for event in _events(output_path)) == 1
