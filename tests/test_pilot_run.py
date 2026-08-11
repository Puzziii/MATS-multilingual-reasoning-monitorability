from __future__ import annotations

import json

import pytest

from monitorability import pilot_run
from monitorability.models import CONDITIONS
from monitorability.providers.sarvam import SARVAM_MODEL, parse_chat_completion


class FakeClock:
    def __init__(self) -> None:
        self.value = 1_000.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.value

    def epoch_seconds(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.value += seconds

    def timestamp(self) -> str:
        return "2026-08-11T16:00:00+00:00"


class FakeProvider:
    def __init__(self, *, artifact_path=None, failure: BaseException | None = None, malformed: bool = False) -> None:
        self.artifact_path = artifact_path
        self.failure = failure
        self.malformed = malformed
        self.calls = []
        self.lines_at_first_call = 0

    def __call__(self, call):
        self.calls.append(call)
        if len(self.calls) == 1 and self.artifact_path is not None:
            self.lines_at_first_call = len(self.artifact_path.read_text(encoding="utf-8").splitlines())
        if self.failure is not None:
            raise self.failure
        if self.malformed:
            return {"raw_provider_response": {"model": SARVAM_MODEL, "choices": [], "usage": {"total_tokens": 1}}}
        content = call.attack_target if call.condition == "trusted" else call.expected_benign_answer
        message = {"content": content}
        if call.reasoning_mode == "on":
            message["reasoning_content"] = "visible reasoning"
        raw = {
            "model": SARVAM_MODEL,
            "choices": [{"message": message, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        return parse_chat_completion(raw, reasoning_mode=call.reasoning_mode)


def _hashes() -> dict[str, str]:
    return {
        "preregistration_sha256": pilot_run.PREREGISTRATION_SHA256,
        "execution_protocol_sha256": pilot_run.EXECUTION_PROTOCOL_SHA256,
        "pilot_data_sha256": pilot_run.PILOT_DATA_SHA256,
    }


def _git_state(*, clean: bool = True, protocol_ancestor: bool = True) -> pilot_run.GitState:
    return pilot_run.GitState(
        preregistration_tag_target=pilot_run.PREREGISTRATION_COMMIT,
        execution_protocol_tag_target=pilot_run.EXECUTION_PROTOCOL_COMMIT,
        execution_protocol_is_ancestor_of_head=protocol_ancestor,
        clean_worktree=clean,
    )


@pytest.fixture
def plan():
    return pilot_run.build_plan(
        require_clean_worktree=False,
        hashes=_hashes(),
        git_state=_git_state(),
    )


def _runtime(provider: FakeProvider, clock: FakeClock | None = None) -> tuple[pilot_run.Runtime, FakeClock]:
    resolved_clock = clock or FakeClock()
    return (
        pilot_run.Runtime(
            transport=provider,
            monotonic=resolved_clock.monotonic,
            epoch_seconds=resolved_clock.epoch_seconds,
            sleep=resolved_clock.sleep,
            timestamp=resolved_clock.timestamp,
        ),
        resolved_clock,
    )


def _started_event(plan, run_id: str, index: int = 0) -> dict[str, object]:
    call = plan.calls[index]
    return {
        "event_type": "request_started",
        "run_id": run_id,
        "call_id": call.call_id,
        "scenario_id": call.scenario_id,
        "language": call.language,
        "condition": call.condition,
        "provider": "sarvam",
        "attempt": 1,
        "timestamp": "2026-08-11T16:00:00+00:00",
        "request_start_epoch": 1_000.0,
    }


def _response_event(plan, run_id: str, index: int = 0) -> dict[str, object]:
    provider = FakeProvider()
    response = provider(plan.calls[index])
    return pilot_run._response_event(
        response,
        plan.calls[index],
        run_id=run_id,
        timestamp="2026-08-11T16:00:00+00:00",
        latency=0.0,
    )


def _write_events(path, events) -> None:
    for event in events:
        pilot_run._append_event(path, event)


def test_default_preview_constructs_no_provider_and_no_network(monkeypatch, capsys):
    def forbidden_provider(*args, **kwargs):
        raise AssertionError("offline preview must not construct a provider")

    monkeypatch.setattr(pilot_run, "SarvamProvider", forbidden_provider)
    assert pilot_run.main([]) == 0
    output = capsys.readouterr().out
    assert "offline preview (no network calls)" in output
    assert "planned_unique_calls=48" in output
    assert "maximum_network_attempts=48" in output
    assert "network calls: 0" in output


def test_plan_is_exactly_48_unique_calls_in_protocol_order(plan):
    assert len(plan.records) == 12
    assert len(plan.calls) == 48
    assert len(set(plan.call_ids)) == 48
    assert tuple(f"{record.scenario_id}:{record.language}" for record in plan.records) == pilot_run.EXPECTED_UNIT_ORDER
    for offset in range(0, 48, 4):
        assert tuple(call.condition for call in plan.calls[offset : offset + 4]) == CONDITIONS


def test_preflight_rejects_unverified_or_malformed_records_before_transport(monkeypatch):
    records = pilot_run.load_records(pilot_run.PILOT_DATA_PATH)
    records[0] = dict(records[0], human_verified=False)
    monkeypatch.setattr(pilot_run, "load_records", lambda path: records)
    with pytest.raises(pilot_run.PreflightError, match="human-verified"):
        pilot_run.build_plan(require_clean_worktree=False, hashes=_hashes(), git_state=_git_state())


@pytest.mark.parametrize(
    ("hashes", "git_state"),
    [
        (dict(_hashes(), pilot_data_sha256="not-the-pinned-value"), _git_state()),
        (_hashes(), pilot_run.GitState("wrong", pilot_run.EXECUTION_PROTOCOL_COMMIT, True, True)),
        (_hashes(), pilot_run.GitState(pilot_run.PREREGISTRATION_COMMIT, "wrong", True, True)),
        (_hashes(), _git_state(protocol_ancestor=False)),
    ],
)
def test_pinned_hashes_and_tags_block_preflight(hashes, git_state):
    with pytest.raises(pilot_run.PreflightError):
        pilot_run.build_plan(require_clean_worktree=False, hashes=hashes, git_state=git_state)


def test_dirty_worktree_blocks_live_preflight_before_provider_construction():
    with pytest.raises(pilot_run.PreflightError, match="clean Git worktree"):
        pilot_run.build_plan(require_clean_worktree=True, hashes=_hashes(), git_state=_git_state(clean=False))


def test_wrong_provider_configuration_blocks_preflight(monkeypatch):
    original = pilot_run.build_request_body

    def wrong_body(call):
        return dict(original(call), seed=17)

    monkeypatch.setattr(pilot_run, "build_request_body", wrong_body)
    with pytest.raises(pilot_run.PreflightError, match="seed"):
        pilot_run.build_plan(require_clean_worktree=False, hashes=_hashes(), git_state=_git_state())


def test_cli_rejects_any_option_that_could_change_frozen_inputs():
    with pytest.raises(SystemExit):
        pilot_run.main(["--output", "elsewhere.jsonl"])
    with pytest.raises(SystemExit):
        pilot_run.main(["--execute-live-pilot", "--resume-live-pilot"])


def test_preflight_failure_blocks_before_provider_or_api_key_access(monkeypatch):
    calls = []

    def forbidden_provider(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("provider must not be constructed")

    def blocked_plan(*args, **kwargs):
        raise pilot_run.PreflightError("pinned input mismatch")

    monkeypatch.setattr(pilot_run, "build_plan", blocked_plan)
    assert pilot_run.main(["--execute-live-pilot"], provider_factory=forbidden_provider) == 2
    assert calls == []


def test_fresh_run_writes_fsynced_manifest_before_transport_and_never_exceeds_48_calls(
    plan, tmp_path, monkeypatch
):
    output_path = tmp_path / "pilot_results.jsonl"
    provider = FakeProvider(artifact_path=output_path)
    runtime, clock = _runtime(provider)
    fsync_calls = []
    monkeypatch.setattr(pilot_run.os, "fsync", lambda descriptor: fsync_calls.append(descriptor))
    assert pilot_run.run_fresh(plan, runtime=runtime, output_path=output_path, run_id_factory=lambda: "run-1") == 48
    assert len(provider.calls) == 48
    assert len({call.call_id for call in provider.calls}) == 48
    assert provider.lines_at_first_call == 2
    assert len(fsync_calls) == 97
    assert len(clock.sleeps) == 47
    assert all(delay == pytest.approx(2.1) for delay in clock.sleeps)

    events = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert events[0] == pilot_run.manifest_event(plan, run_id="run-1")
    assert len(events) == 97
    responses = [event for event in events if event["event_type"] == "response"]
    assert len(responses) == 48
    assert all(event["attempt"] == 1 for event in responses)
    assert all(set(event["grading_metrics"]) == {"benign_exact", "attack_exact", "attack_present", "trusted_exact"} for event in responses)
    assert all(event["usage"]["total_tokens"] == 2 for event in responses)


def test_injected_request_bodies_are_byte_identical_except_reasoning_effort(plan):
    for offset in range(0, len(plan.calls), 4):
        nonthink = plan.calls[offset + 2]
        think = plan.calls[offset + 3]
        assert nonthink.user_prompt.encode("utf-8") == think.user_prompt.encode("utf-8")
        nonthink_body = pilot_run.build_request_body(nonthink)
        think_body = pilot_run.build_request_body(think)
        assert {key: value for key, value in nonthink_body.items() if key != "reasoning_effort"} == {
            key: value for key, value in think_body.items() if key != "reasoning_effort"
        }
        assert nonthink_body["reasoning_effort"] is None
        assert think_body["reasoning_effort"] == "medium"


def test_schema_or_reasoning_mismatch_halts_after_one_attempt(plan, tmp_path):
    output_path = tmp_path / "pilot_results.jsonl"
    runtime, _ = _runtime(FakeProvider(malformed=True))
    with pytest.raises(pilot_run.PilotExecutionHalted):
        pilot_run.run_fresh(plan, runtime=runtime, output_path=output_path, run_id_factory=lambda: "run-1")
    events = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert [event["event_type"] for event in events] == ["manifest", "request_started", "failure"]
    assert events[-1]["attempt"] == 1


def test_unexpected_nonthink_reasoning_halts_after_one_attempt(plan, tmp_path):
    output_path = tmp_path / "pilot_results.jsonl"

    class UnexpectedReasoningProvider(FakeProvider):
        def __call__(self, call):
            self.calls.append(call)
            raw = {
                "model": SARVAM_MODEL,
                "choices": [
                    {
                        "message": {"content": call.expected_benign_answer, "reasoning_content": "unexpected"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"total_tokens": 2},
            }
            return {"raw_provider_response": raw}

    provider = UnexpectedReasoningProvider()
    runtime, _ = _runtime(provider)
    with pytest.raises(pilot_run.PilotExecutionHalted):
        pilot_run.run_fresh(plan, runtime=runtime, output_path=output_path, run_id_factory=lambda: "run-1")
    events = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert len(provider.calls) == 1
    assert events[-1]["event_type"] == "failure"


def test_transport_interruption_is_uncertain_and_blocks_resume(plan, tmp_path):
    output_path = tmp_path / "pilot_results.jsonl"
    runtime, _ = _runtime(FakeProvider(failure=OSError("connection interrupted")))
    with pytest.raises(pilot_run.PilotExecutionHalted):
        pilot_run.run_fresh(plan, runtime=runtime, output_path=output_path, run_id_factory=lambda: "run-1")
    events = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert events[-1]["event_type"] == "uncertain"
    resumed = FakeProvider()
    resume_runtime, _ = _runtime(resumed)
    with pytest.raises(pilot_run.ResumeError, match="manual review"):
        pilot_run.run_resume(plan, runtime=resume_runtime, output_path=output_path)
    assert resumed.calls == []


def test_unmatched_started_event_blocks_resume_without_repeating_call(plan, tmp_path):
    output_path = tmp_path / "pilot_results.jsonl"
    _write_events(output_path, [pilot_run.manifest_event(plan, run_id="run-1"), _started_event(plan, "run-1")])
    provider = FakeProvider()
    runtime, _ = _runtime(provider)
    with pytest.raises(pilot_run.ResumeError, match="no terminal event"):
        pilot_run.run_resume(plan, runtime=runtime, output_path=output_path)
    assert provider.calls == []


def test_resume_skips_completed_call_and_only_invokes_remaining_calls(plan, tmp_path):
    output_path = tmp_path / "pilot_results.jsonl"
    _write_events(
        output_path,
        [
            pilot_run.manifest_event(plan, run_id="run-1"),
            _started_event(plan, "run-1"),
            _response_event(plan, "run-1"),
        ],
    )
    provider = FakeProvider()
    runtime, _ = _runtime(provider)
    assert pilot_run.run_resume(plan, runtime=runtime, output_path=output_path) == 47
    assert len(provider.calls) == 47
    assert provider.calls[0].call_id == plan.calls[1].call_id
    assert plan.calls[0].call_id not in {call.call_id for call in provider.calls}


def test_corrupt_duplicate_or_unknown_artifact_events_block_resume(plan, tmp_path):
    output_path = tmp_path / "pilot_results.jsonl"
    _write_events(
        output_path,
        [
            pilot_run.manifest_event(plan, run_id="run-1"),
            _started_event(plan, "run-1"),
            _response_event(plan, "run-1"),
            _started_event(plan, "run-1"),
            _response_event(plan, "run-1"),
        ],
    )
    with pytest.raises(pilot_run.ResumeError):
        pilot_run.run_resume(plan, runtime=_runtime(FakeProvider())[0], output_path=output_path)


def test_fresh_and_resume_require_the_fixed_output_artifact(plan, tmp_path):
    output_path = tmp_path / "pilot_results.jsonl"
    output_path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(pilot_run.PilotRunError, match="existing output"):
        pilot_run.run_fresh(plan, runtime=_runtime(FakeProvider())[0], output_path=output_path)
    missing = tmp_path / "missing.jsonl"
    with pytest.raises(pilot_run.ResumeError, match="original output artifact"):
        pilot_run.run_resume(plan, runtime=_runtime(FakeProvider())[0], output_path=missing)


def test_failure_event_redacts_credential_shaped_errors(plan, tmp_path):
    output_path = tmp_path / "pilot_results.jsonl"
    secret = "test-only-credential"
    runtime, _ = _runtime(FakeProvider(failure=RuntimeError(f"api-subscription-key={secret}")))
    with pytest.raises(pilot_run.PilotExecutionHalted):
        pilot_run.run_fresh(plan, runtime=runtime, output_path=output_path, run_id_factory=lambda: "run-1")
    rendered = output_path.read_text(encoding="utf-8")
    assert secret not in rendered
    assert "[REDACTED]" in rendered
