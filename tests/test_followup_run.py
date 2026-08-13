"""Focused mocked tests for the guarded Phase 5 follow-up runner only."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from monitorability import followup_run


@pytest.fixture
def plan():
    return followup_run.build_plan(require_clean_worktree=False)


def _runtime(transport):
    return followup_run.Runtime(
        transport=transport, monotonic=lambda: 1.0, epoch_seconds=lambda: 2.1,
        sleep=lambda _: None, timestamp=lambda: "2026-08-13T00:00:00+00:00",
    )


def test_exact_48_call_plan_order_and_pairing(plan):
    assert len(plan.records) == 12
    assert tuple(f"{r.scenario_id}:{r.language}" for r in plan.records) == followup_run.EXPECTED_UNIT_ORDER
    assert len(plan.calls) == len(set(plan.call_ids)) == 48
    for offset in range(0, 48, 4):
        assert tuple(call.condition for call in plan.calls[offset:offset + 4]) == followup_run.CONDITIONS
    by_id = {call.call_id: call for call in plan.calls}
    for unit in followup_run.EXPECTED_UNIT_ORDER:
        assert by_id[f"{unit}:injected_non_think"].user_prompt == by_id[f"{unit}:injected_think"].user_prompt
        assert by_id[f"{unit}:injected_non_think"].reasoning_mode == "off"
        assert by_id[f"{unit}:injected_think"].reasoning_mode == "on"


def test_hash_tag_preflight_and_preview_are_offline(plan):
    assert plan.hashes == {"followup_data_sha256": followup_run.FOLLOWUP_DATA_SHA256,
                           "followup_protocol_sha256": followup_run.FOLLOWUP_PROTOCOL_SHA256,
                           "pilot_raw_sha256": followup_run.PILOT_RAW_SHA256}
    preview = followup_run.offline_preview(plan)
    for expected in ("planned_units=12", "planned_unique_calls=48", "maximum_network_attempts=48", "execution=READY", "network calls: 0"):
        assert expected in preview
    with pytest.raises(followup_run.PreflightError):
        followup_run.build_plan(require_clean_worktree=False, hashes={})


def test_missing_key_stops_before_artifact_or_transport(plan, tmp_path, monkeypatch):
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)
    output, calls = tmp_path / "followup_results.jsonl", []
    with pytest.raises(followup_run.PreflightError):
        followup_run.run_fresh(plan, runtime=_runtime(lambda call: calls.append(call)), output_path=output)
    assert calls == []
    assert not output.exists()


def test_existing_artifact_refusal_precedes_transport(plan, tmp_path, monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "configured")
    output, calls = tmp_path / "followup_results.jsonl", []
    output.write_text("already exists\n", encoding="utf-8")
    with pytest.raises(followup_run.FollowupRunError):
        followup_run.run_fresh(plan, runtime=_runtime(lambda call: calls.append(call)), output_path=output)
    assert calls == []


def test_no_retry_sanitized_failure_and_attempt_ceiling(plan, tmp_path, monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "configured")
    output, calls = tmp_path / "followup_results.jsonl", []
    def fail(call):
        calls.append(call.call_id)
        raise RuntimeError("Authorization=private-value")
    with pytest.raises(followup_run.FollowupExecutionHalted):
        followup_run.run_fresh(plan, runtime=_runtime(fail), output_path=output, run_id_factory=lambda: "run")
    assert len(calls) == 1
    events = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert [event["event_type"] for event in events] == ["manifest", "request_started", "failure"]
    assert "private-value" not in output.read_text(encoding="utf-8")
    reusable_plan = followup_run.pilot_run.PilotPlan(plan.records, plan.calls, plan.hashes)
    with pytest.raises(followup_run.FollowupRunError):
        followup_run.pilot_run._execute_remaining(reusable_plan, plan.calls + (plan.calls[0],),
            output_path=tmp_path / "ceiling.jsonl", run_id="run", runtime=_runtime(fail))
    assert len(calls) == 1


def test_offline_work_does_not_modify_pilot_artifact(plan):
    before = hashlib.sha256(followup_run.PILOT_OUTPUT_PATH.read_bytes()).hexdigest()
    followup_run.offline_preview(plan)
    after = hashlib.sha256(followup_run.PILOT_OUTPUT_PATH.read_bytes()).hexdigest()
    assert before == after == followup_run.PILOT_RAW_SHA256
