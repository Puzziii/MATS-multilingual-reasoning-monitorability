from __future__ import annotations

import http.client
import json
import os
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import urlsplit

from ..models import ConditionCall
from .base import RetryableProviderError, redact_for_log, redact_secret_value


SARVAM_CHAT_COMPLETIONS_URL = "https://api.sarvam.ai/v1/chat/completions"
SARVAM_MODEL = "sarvam-105b"
_REQUEST_PARAMETERS = {
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


class LiveTransportDisabledError(RuntimeError):
    """Raised unless a caller explicitly enables one live transport path."""


class SarvamResponseError(RuntimeError):
    """Raised when a response does not match the required chat-completion schema."""


def build_request_body(call: ConditionCall) -> dict[str, Any]:
    """Build the exact Sarvam request body from already-rendered messages."""
    return {
        "model": SARVAM_MODEL,
        "messages": [
            {"role": "system", "content": call.system_prompt},
            {"role": "user", "content": call.user_prompt},
        ],
        "reasoning_effort": "medium" if call.reasoning_mode == "on" else None,
        **_REQUEST_PARAMETERS,
    }


def parse_chat_completion(payload: Mapping[str, Any], *, reasoning_mode: str) -> dict[str, Any]:
    """Parse a structurally valid completion without discarding unavailable text."""
    choices = payload.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise SarvamResponseError("Sarvam response must contain exactly one choice")
    choice = choices[0]
    if not isinstance(choice, Mapping):
        raise SarvamResponseError("Sarvam response choice must be an object")
    message = choice.get("message")
    if not isinstance(message, Mapping):
        raise SarvamResponseError("Sarvam response choice message must be an object")

    content_value = message.get("content")
    if content_value is not None and not isinstance(content_value, str):
        raise SarvamResponseError("Sarvam response content must be a string or null")
    final_text_available = isinstance(content_value, str) and bool(content_value.strip())
    final_text = content_value if final_text_available else ""

    reasoning_value = message.get("reasoning_content")
    if reasoning_value is not None and not isinstance(reasoning_value, str):
        raise SarvamResponseError("Sarvam reasoning_content must be a string or null")
    reasoning_available = isinstance(reasoning_value, str) and bool(reasoning_value.strip())
    visible_reasoning_text = reasoning_value if reasoning_available else ""
    reasoning_character_count = len(reasoning_value) if reasoning_available else 0
    reasoning_mode_mismatch = (reasoning_mode == "on" and not reasoning_available) or (
        reasoning_mode == "off" and reasoning_available
    )

    finish_reason = choice.get("finish_reason")
    if finish_reason is not None and not isinstance(finish_reason, str):
        raise SarvamResponseError("Sarvam response finish_reason must be a string or null")
    model = payload.get("model")
    if not isinstance(model, str) or not model:
        raise SarvamResponseError("Sarvam response model must be a non-empty string")
    usage_value = payload.get("usage")
    if usage_value is None:
        usage: dict[str, Any] = {}
    elif isinstance(usage_value, Mapping):
        usage = dict(usage_value)
    else:
        raise SarvamResponseError("Sarvam response usage must be an object or null")
    return {
        "final_text": final_text,
        "final_text_available": final_text_available,
        "visible_reasoning_text": visible_reasoning_text,
        "reasoning_available": reasoning_available,
        "reasoning_character_count": reasoning_character_count,
        "reasoning_mode_mismatch": reasoning_mode_mismatch,
        "model": model,
        "finish_reason": finish_reason,
        "usage": usage,
        "raw_provider_response": dict(payload),
    }


class SarvamProvider:
    """Fail-closed standard-library transport for Sarvam chat completions.

    The provider never reads or stores SARVAM_API_KEY unless a caller explicitly
    enables transport. The normal pilot runner leaves transport disabled.
    """

    name = "sarvam"
    endpoint = SARVAM_CHAT_COMPLETIONS_URL
    model = SARVAM_MODEL

    def __init__(
        self,
        *,
        allow_network: bool = False,
        timeout: float = 30.0,
        connection_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._allow_network = allow_network
        self._timeout = timeout
        self._connection_factory = connection_factory or http.client.HTTPSConnection

    def __repr__(self) -> str:
        state = "enabled" if self._allow_network else "disabled"
        return f"SarvamProvider(model={self.model!r}, transport={state!r})"

    @staticmethod
    def build_request_body(call: ConditionCall) -> dict[str, Any]:
        return build_request_body(call)

    @staticmethod
    def _headers(api_key: str) -> dict[str, str]:
        return {"Content-Type": "application/json", "api-subscription-key": api_key}

    def generate(self, call: ConditionCall) -> dict[str, Any]:
        body = self.build_request_body(call)
        if not self._allow_network:
            raise LiveTransportDisabledError(
                "Sarvam transport is disabled; use only the explicit schema-smoke live flag"
            )
        return self._post_json(body, reasoning_mode=call.reasoning_mode)

    def _post_json(self, body: Mapping[str, Any], *, reasoning_mode: str) -> dict[str, Any]:
        serialized = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        # The credential is deliberately read only after transport is explicitly
        # enabled and immediately before constructing the live HTTPS request.
        api_key = os.environ.get("SARVAM_API_KEY")
        if not api_key:
            raise RuntimeError("SARVAM_API_KEY is required for live Sarvam transport")
        headers = self._headers(api_key)
        parsed = urlsplit(self.endpoint)
        connection: Any | None = None
        try:
            connection = self._connection_factory(
                parsed.hostname,
                port=parsed.port or 443,
                timeout=self._timeout,
            )
            connection.request("POST", parsed.path, body=serialized, headers=headers)
            response = connection.getresponse()
            status = int(response.status)
            response_bytes = response.read()
        except (OSError, TimeoutError, http.client.HTTPException) as exc:
            raise RetryableProviderError(f"Sarvam transport failure: {type(exc).__name__}") from exc
        finally:
            if connection is not None:
                connection.close()
        if status == 429 or status >= 500:
            raise RetryableProviderError(f"Sarvam HTTP status {status}")
        if not 200 <= status < 300:
            raise SarvamResponseError(f"Sarvam HTTP status {status}")
        try:
            decoded = json.loads(response_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SarvamResponseError("Sarvam response was not valid JSON") from exc
        if not isinstance(decoded, Mapping):
            raise SarvamResponseError("Sarvam response root must be an object")
        sanitized = redact_for_log(redact_secret_value(decoded, api_key))
        return parse_chat_completion(sanitized, reasoning_mode=reasoning_mode)
