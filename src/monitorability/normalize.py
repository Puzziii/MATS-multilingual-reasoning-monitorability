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
    return NormalizedResponse(
        final_text=normalize_text(final_text),
        visible_reasoning_text=normalize_text(reasoning_text),
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
