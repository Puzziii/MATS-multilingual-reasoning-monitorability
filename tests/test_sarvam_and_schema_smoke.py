from __future__ import annotations

import json
from pathlib import Path

import pytest

from monitorability.models import ScenarioRecord, expand_conditions
from monitorability.providers.base import redact_for_log, sanitize_error
from monitorability.providers.sarvam import (
    SARVAM_CHAT_COMPLETIONS_URL,
    SARVAM_MODEL,
    LiveTransportDisabledError,
    SarvamProvider,
    SarvamResponseError,
    build_request_body,
    parse_chat_completion,
)
from monitorability.runner import main as runner_main
from monitorability.schema_smoke import (
    SMOKE_SYSTEM_PROMPT,
    SMOKE_USER_PROMPT,
    build_smoke_call,
    execute_one_live_smoke,
    main as smoke_main,
)


def _calls(valid_record):
    record = ScenarioRecord.from_mapping(dict(valid_record, human_verified=True))
    return {call.condition: call for call in expand_conditions(record)}


def _api_response(*, reasoning: str | None = "reasoning", content: str = "379", model: str = SARVAM_MODEL):
    message = {"content": content}
    if reasoning is not None:
        message["reasoning_content"] = reasoning
    return {
        "model": model,
        "choices": [{"message": message, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


class FakeHTTPResponse:
    def __init__(self, payload, status: int = 200):
        self.status = status
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


class FakeConnection:
    def __init__(self, response: FakeHTTPResponse):
        self.response = response
        self.requests = []
        self.closed = False

    def request(self, method, url, *, body, headers):
        self.requests.append({"method": method, "url": url, "body": body, "headers": headers})

    def getresponse(self):
        return self.response

    def close(self):
        self.closed = True


class ConnectionFactory:
    def __init__(self, connection):
        self.connection = connection
        self.calls = []

    def __call__(self, host, *, port, timeout):
        self.calls.append({"host": host, "port": port, "timeout": timeout})
        return self.connection


def test_exact_think_and_nonthink_bodies_differ_only_by_reasoning_effort(valid_record):
    calls = _calls(valid_record)
    think = build_request_body(calls["injected_think"])
    nonthink = build_request_body(calls["injected_non_think"])
    expected_common = {
        "model": "sarvam-105b",
        "messages": [
            {"role": "system", "content": calls["injected_think"].system_prompt},
            {"role": "user", "content": calls["injected_think"].user_prompt},
        ],
        "temperature": 0.0,
        "top_p": 1.0,
        "max_tokens": 2048,
        "seed": 1729,
        "n": 1,
        "stream": False,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "wiki_grounding": False,
    }
    assert {key: value for key, value in think.items() if key != "reasoning_effort"} == expected_common
    assert {key: value for key, value in nonthink.items() if key != "reasoning_effort"} == expected_common
    assert think["reasoning_effort"] == "medium"
    assert nonthink["reasoning_effort"] is None
    assert {key for key in think if think[key] != nonthink[key]} == {"reasoning_effort"}


def test_transport_uses_exact_endpoint_and_safe_headers(monkeypatch, valid_record):
    calls = _calls(valid_record)
    connection = FakeConnection(FakeHTTPResponse(_api_response()))
    factory = ConnectionFactory(connection)
    monkeypatch.setenv("SARVAM_API_KEY", "test-only-credential")
    result = SarvamProvider(allow_network=True, connection_factory=factory).generate(calls["injected_think"])
    assert SARVAM_CHAT_COMPLETIONS_URL == "https://api.sarvam.ai/v1/chat/completions"
    assert factory.calls == [{"host": "api.sarvam.ai", "port": 443, "timeout": 30.0}]
    request = connection.requests[0]
    assert request["method"] == "POST"
    assert request["url"] == "/v1/chat/completions"
    assert request["headers"] == {
        "Content-Type": "application/json",
        "api-subscription-key": "test-only-credential",
    }
    assert "Authorization" not in request["headers"]
    assert json.loads(request["body"]) == build_request_body(calls["injected_think"])
    assert result["final_text"] == "379"
    assert result["visible_reasoning_text"] == "reasoning"
    assert result["usage"]["total_tokens"] == 15
    assert connection.closed is True


@pytest.mark.parametrize("reasoning", [None, "   "])
def test_think_response_rejects_missing_or_empty_reasoning(reasoning):
    with pytest.raises(SarvamResponseError, match="reasoning_content"):
        parse_chat_completion(_api_response(reasoning=reasoning), reasoning_mode="on")


def test_nonthink_response_rejects_unexpected_reasoning():
    with pytest.raises(SarvamResponseError, match="must not contain reasoning_content"):
        parse_chat_completion(_api_response(reasoning="unexpected"), reasoning_mode="off")


@pytest.mark.parametrize("payload", [{}, {"choices": []}, {"choices": [{}, {}]}])
def test_malformed_responses_fail_closed(payload):
    with pytest.raises(SarvamResponseError):
        parse_chat_completion(payload, reasoning_mode="on")


def test_missing_api_key_blocks_before_transport(monkeypatch, valid_record):
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)
    connection = FakeConnection(FakeHTTPResponse(_api_response()))
    factory = ConnectionFactory(connection)
    with pytest.raises(RuntimeError, match="SARVAM_API_KEY"):
        SarvamProvider(allow_network=True, connection_factory=factory).generate(_calls(valid_record)["injected_think"])
    assert factory.calls == []


def test_transport_is_disabled_by_default_even_with_a_key(monkeypatch, valid_record):
    monkeypatch.setenv("SARVAM_API_KEY", "test-only-credential")
    factory = ConnectionFactory(FakeConnection(FakeHTTPResponse(_api_response())))
    with pytest.raises(LiveTransportDisabledError):
        SarvamProvider(connection_factory=factory).generate(_calls(valid_record)["injected_think"])
    assert factory.calls == []


def test_response_raw_payload_and_logging_redact_credentials(monkeypatch, valid_record):
    credential = "test-only-credential"
    response = _api_response()
    response["metadata"] = {"api-subscription-key": credential, "echo": f"value={credential}", credential: "echoed key"}
    connection = FakeConnection(FakeHTTPResponse(response))
    monkeypatch.setenv("SARVAM_API_KEY", credential)
    result = SarvamProvider(allow_network=True, connection_factory=ConnectionFactory(connection)).generate(
        _calls(valid_record)["injected_think"]
    )
    rendered = json.dumps(result)
    assert credential not in rendered
    assert "[REDACTED]" in rendered
    assert redact_for_log({"api-subscription-key": credential}) == {"api-subscription-key": "[REDACTED]"}
    assert credential not in sanitize_error(RuntimeError(f"api-subscription-key={credential}"))["error_message"]


class CountingSmokeProvider:
    name = "counting-smoke"

    def __init__(self):
        self.calls = 0

    def generate(self, call):
        self.calls += 1
        assert call.system_prompt == SMOKE_SYSTEM_PROMPT
        assert call.user_prompt == SMOKE_USER_PROMPT
        assert call.reasoning_mode == "on"
        parsed = parse_chat_completion(_api_response(), reasoning_mode="on")
        return parsed


def test_smoke_invokes_provider_once_and_appends_raw_response(tmp_path):
    output_path = tmp_path / "schema-smoke.jsonl"
    output_path.write_text('{"event_type":"previous"}\n', encoding="utf-8")
    provider = CountingSmokeProvider()
    event = execute_one_live_smoke(provider, output_path)
    assert provider.calls == 1
    lines = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 2
    assert lines[-1] == event
    assert event["planned_calls"] == event["completed_calls"] == 1
    assert event["final_text"] == "379"
    assert event["raw_provider_response"]["usage"]["total_tokens"] == 15


def test_smoke_preview_is_offline_and_contains_only_fixed_prompt(monkeypatch, capsys):
    def forbidden_init(*args, **kwargs):
        raise AssertionError("offline preview must not instantiate a provider")

    monkeypatch.setattr(SarvamProvider, "__init__", forbidden_init)
    assert smoke_main([]) == 0
    output = capsys.readouterr().out
    assert "planned_calls=1" in output
    assert "no network calls" in output
    assert SMOKE_SYSTEM_PROMPT in output
    assert SMOKE_USER_PROMPT in output
    assert "P1" not in output and "pilot_scenarios" not in output


def test_normal_runner_sarvam_option_fails_closed_without_transport(monkeypatch, tmp_path):
    def forbidden_provider(*args, **kwargs):
        raise AssertionError("normal runner must not instantiate Sarvam transport")

    monkeypatch.setattr("monitorability.providers.sarvam.SarvamProvider", forbidden_provider)
    output_path = tmp_path / "pilot.jsonl"
    assert runner_main(["--provider", "sarvam", "--output", str(output_path), "data/pilot_scenarios.jsonl"]) == 2
    assert not output_path.exists()


def test_smoke_call_is_fixed_nonstudy_think_request():
    call = build_smoke_call()
    assert call.scenario_id == "schema-smoke"
    assert call.system_prompt == SMOKE_SYSTEM_PROMPT
    assert call.user_prompt == SMOKE_USER_PROMPT
    assert call.reasoning_mode == "on"
