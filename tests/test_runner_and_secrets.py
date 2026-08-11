from __future__ import annotations

import json
import logging

import pytest
from pathlib import Path

from monitorability.providers.base import RetryableProviderError, redact_for_log, safe_log, sanitize_error
from monitorability.providers.mock import MockProvider
from monitorability.providers.sarvam import SarvamProvider
from monitorability.runner import dry_run, execute, load_records
from monitorability.validation import ValidationError


class FailOnceProvider:
    name = "fail-once"

    def __init__(self):
        self.calls = 0
        self.delegate = MockProvider()

    def generate(self, call):
        self.calls += 1
        if self.calls == 1:
            raise RetryableProviderError("transport status=503")
        return self.delegate.generate(call)


def test_dry_run_reports_ready_when_all_records_verified():
    output = dry_run(load_records(Path("data/pilot_scenarios.jsonl")))
    assert "planned scenario-language units: 12" in output
    assert "planned condition calls: 48" in output
    assert "completed" not in output
    assert "real execution: READY" in output
    assert "validation reasons" not in output
    assert "network calls: 0" in output


def test_retry_error_and_response_events_are_append_only(complete_records, tmp_path):
    output_path = tmp_path / "responses.jsonl"
    provider = FailOnceProvider()
    executable_records = [dict(record, human_verified=True) for record in complete_records]
    assert execute(executable_records, provider, output_path, max_retries=1) == 12
    events = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert len(events) == 13
    assert events[0]["event_type"] == "error"
    assert events[0]["call_id"] == "TEST-1:en:clean"
    assert events[0]["attempt"] == 1
    assert events[0]["retryable_status"] is True
    assert events[0]["error_type"] == "RetryableProviderError"
    first_response = events[1]
    assert first_response["event_type"] == "response"
    assert first_response["attempt"] == 2
    assert first_response["attack_family"] == "simple_override"
    assert first_response["carrier"] == "retrieved_content"
    assert first_response["grading_metrics"]["benign_exact"] is True
    assert first_response["raw_provider_response"]["provider"] == "mock"
    assert all(event["event_type"] == "response" for event in events[1:])


def test_execute_rejects_unverified_records_without_creating_output(complete_records, tmp_path):
    output_path = tmp_path / "blocked.jsonl"
    with pytest.raises(ValidationError, match="not human-verified"):
        execute(complete_records, MockProvider(), output_path)
    assert not output_path.exists()


def test_secret_safe_logging(monkeypatch, caplog):
    secret = "unit-test-value-not-a-credential"
    monkeypatch.setenv("SARVAM_API_KEY", secret)
    provider = SarvamProvider()
    with caplog.at_level(logging.INFO):
        safe_log(logging.getLogger("test-secret"), "provider_configured", api_key=secret)
    assert secret not in caplog.text
    assert secret not in repr(provider)
    assert redact_for_log({"authorization": secret}) == {"authorization": "[REDACTED]"}


def test_error_sanitization_uses_redacted_text_without_control_a():
    secret = "unit-test-api-key-value"
    sanitized = sanitize_error(RuntimeError(f"api_key={secret}"))
    assert secret not in sanitized["error_message"]
    assert "[REDACTED]" in sanitized["error_message"]
    assert "\x01" not in sanitized["error_message"]
