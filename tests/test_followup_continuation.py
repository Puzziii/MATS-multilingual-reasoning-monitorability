"""Focused mocked checks for the one authorized 47-call follow-up suffix."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from monitorability import followup_continuation as continuation


@pytest.fixture
def prepared():
    return continuation.build_continuation_plan(require_clean_worktree=False)


def _runtime(transport):
    return continuation.Runtime(
        transport=transport, monotonic=lambda: 1.0, epoch_seconds=lambda: 2.1,
        sleep=lambda _: None, timestamp=lambda: "2026-08-13T00:00:00+00:00",
    )


def test_exact_47_call_suffix_and_combined_ceiling(prepared):
    plan, remaining = prepared
    assert len(plan.calls) == 48
    assert len(remaining) == len({call.call_id for call in remaining}) == 47
    assert remaining[0].call_id == continuation.FIRST_REMAINING_CALL_ID
    assert remaining[-1].call_id == continuation.LAST_REMAINING_CALL_ID
    assert continuation.CONSUMED_CALL_ID not in {call.call_id for call in remaining}
    assert continuation.PRIOR_CONSUMED_ATTEMPTS + len(remaining) == continuation.MAXIMUM_COMBINED_STUDY_ATTEMPTS


def test_hash_tag_and_failed_incident_integrity(prepared, monkeypatch):
    plan, remaining = prepared
    assert plan.hashes["followup_data_sha256"] == continuation.followup_run.FOLLOWUP_DATA_SHA256
    assert len(remaining) == 47
    monkeypatch.setattr(continuation, "FAILED_ATTEMPT_SHA256", "0" * 64)
    with pytest.raises(continuation.PreflightError, match="failed-attempt artifact hash"):
        continuation.build_continuation_plan(require_clean_worktree=False)


def test_runner_tag_checkpoint_is_pinned(prepared, monkeypatch):
    monkeypatch.setattr(continuation, "FOLLOWUP_RUNNER_COMMIT", "0" * 40)
    with pytest.raises(continuation.PreflightError, match="runner tag"):
        continuation.build_continuation_plan(require_clean_worktree=False)


def test_missing_credential_precedes_artifact_and_transport(prepared, tmp_path, monkeypatch):
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)
    plan, remaining = prepared
    output, calls = tmp_path / "followup_results.jsonl", []
    with pytest.raises(continuation.PreflightError):
        continuation.run_continuation(plan, remaining, runtime=_runtime(lambda call: calls.append(call)), output_path=output)
    assert calls == []
    assert not output.exists()


def test_existing_output_refusal_and_no_second_continuation(prepared, tmp_path, monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "configured")
    plan, remaining = prepared
    output, calls = tmp_path / "followup_results.jsonl", []
    output.write_text("prior continuation data\n", encoding="utf-8")
    with pytest.raises(continuation.ContinuationError):
        continuation.run_continuation(plan, remaining, runtime=_runtime(lambda call: calls.append(call)), output_path=output)
    assert calls == []


def test_failure_is_sanitized_not_retried_and_halts(prepared, tmp_path, monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "configured")
    plan, remaining = prepared
    output, calls = tmp_path / "followup_results.jsonl", []
    def fail(call):
        calls.append(call.call_id)
        raise RuntimeError("Authorization=private-value")
    with pytest.raises(continuation.ContinuationHalted):
        continuation.run_continuation(plan, remaining, runtime=_runtime(fail), output_path=output, run_id_factory=lambda: "run")
    assert calls == [continuation.FIRST_REMAINING_CALL_ID]
    events = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert [event["event_type"] for event in events] == ["continuation_authorization", "request_started", "failure"]
    assert "private-value" not in output.read_text(encoding="utf-8")
    with pytest.raises(continuation.ContinuationError):
        continuation.run_continuation(plan, remaining, runtime=_runtime(fail), output_path=output)
    assert calls == [continuation.FIRST_REMAINING_CALL_ID]


def test_preview_is_zero_network_and_frozen_files_unchanged(prepared):
    plan, remaining = prepared
    pilot_before = hashlib.sha256(continuation.followup_run.PILOT_OUTPUT_PATH.read_bytes()).hexdigest()
    data_before = hashlib.sha256(continuation.followup_run.FOLLOWUP_DATA_PATH.read_bytes()).hexdigest()
    protocol_before = hashlib.sha256(continuation.followup_run.FOLLOWUP_PROTOCOL_PATH.read_bytes()).hexdigest()
    preview = continuation.offline_preview(plan, remaining)
    for expected in ("prior_consumed_attempts=1", "remaining_authorized_calls=47",
                     "first_remaining_call=P7:ta:trusted", "last_remaining_call=P8:ta:injected_think",
                     "maximum_combined_study_attempts=48", "integrity=READY", "network calls: 0"):
        assert expected in preview
    assert hashlib.sha256(continuation.followup_run.PILOT_OUTPUT_PATH.read_bytes()).hexdigest() == pilot_before
    assert hashlib.sha256(continuation.followup_run.FOLLOWUP_DATA_PATH.read_bytes()).hexdigest() == data_before
    assert hashlib.sha256(continuation.followup_run.FOLLOWUP_PROTOCOL_PATH.read_bytes()).hexdigest() == protocol_before
