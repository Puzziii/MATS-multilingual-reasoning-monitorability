from __future__ import annotations

import unicodedata
from collections.abc import Mapping
from typing import Any

from .models import ConditionCall, NormalizedResponse


def normalize_text(value: str) -> str:
    """Apply only preregistered Unicode normalization and outer trimming."""
    return unicodedata.normalize("NFC", value).strip()


def normalize_response(
    provider_response: Mapping[str, Any],
    call: ConditionCall,
    *,
    timestamp: str,
    latency: float,
    grading_metrics: dict[str, bool],
    attempt: int,
) -> NormalizedResponse:
    """Convert an adapter response into the provider-neutral stored shape."""
    final_text = provider_response.get("final_text", "")
    reasoning_text = provider_response.get("visible_reasoning_text", "")
    if not isinstance(final_text, str) or not isinstance(reasoning_text, str):
        raise TypeError("provider response text fields must be strings")
    final_text_available = provider_response.get("final_text_available", bool(normalize_text(final_text)))
    reasoning_available = provider_response.get("reasoning_available", bool(normalize_text(reasoning_text)))
    reasoning_character_count = provider_response.get(
        "reasoning_character_count", len(reasoning_text) if reasoning_available else 0
    )
    reasoning_mode_mismatch = provider_response.get("reasoning_mode_mismatch", False)
    if not isinstance(final_text_available, bool) or not isinstance(reasoning_available, bool):
        raise TypeError("provider response availability fields must be booleans")
    if not isinstance(reasoning_character_count, int) or reasoning_character_count < 0:
        raise TypeError("provider response reasoning_character_count must be a non-negative integer")
    if not isinstance(reasoning_mode_mismatch, bool):
        raise TypeError("provider response reasoning_mode_mismatch must be a boolean")
    return NormalizedResponse(
        final_text=normalize_text(final_text),
        final_text_available=final_text_available,
        visible_reasoning_text=normalize_text(reasoning_text),
        reasoning_available=reasoning_available,
        reasoning_character_count=reasoning_character_count,
        reasoning_mode_mismatch=reasoning_mode_mismatch,
        model=str(provider_response.get("model", "unknown")),
        scenario_id=call.scenario_id,
        language=call.language,
        condition=call.condition,
        request_parameters=dict(call.request_parameters),
        timestamp=timestamp,
        latency=float(latency),
        raw_provider_response=provider_response.get("raw_provider_response", dict(provider_response)),
        attack_family=call.attack_family,
        carrier=call.carrier,
        call_id=call.call_id,
        reasoning_mode=call.reasoning_mode,
        grading_metrics=dict(grading_metrics),
        attempt=attempt,
    )
