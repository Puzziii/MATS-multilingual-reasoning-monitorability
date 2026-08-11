from __future__ import annotations

from typing import Any

from ..models import ConditionCall


class MockProvider:
    """Deterministic local provider; it never opens a network connection."""

    name = "mock"

    def generate(self, call: ConditionCall) -> dict[str, Any]:
        if call.condition == "trusted":
            final_text = call.attack_target
        else:
            final_text = call.expected_benign_answer
        reasoning = "Mock provider reasoning is visible only for injected_think." if call.condition == "injected_think" else ""
        raw = {
            "provider": self.name,
            "call_id": call.call_id,
            "condition": call.condition,
            "final_text": final_text,
            "visible_reasoning_text": reasoning,
            "model": "mock-model",
        }
        return {
            "final_text": final_text,
            "visible_reasoning_text": reasoning,
            "model": "mock-model",
            "raw_provider_response": raw,
        }
