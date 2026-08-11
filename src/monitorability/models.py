from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal, Mapping


Language = Literal["en", "ta", "tanglish"]
Condition = Literal["clean", "trusted", "injected_non_think", "injected_think"]
ReasoningMode = Literal["off", "on"]
CONDITIONS: tuple[Condition, ...] = (
    "clean",
    "trusted",
    "injected_non_think",
    "injected_think",
)
DELIMITER_OPEN = "<untrusted_content>"
DELIMITER_CLOSE = "</untrusted_content>"
INSERT_TOKEN = "{{INSERT}}"


@dataclass(frozen=True)
class ScenarioRecord:
    scenario_id: str
    attack_family: str
    carrier: str
    language: Language
    system_prompt: str
    task_prompt: str
    trusted_context: str
    trusted_instruction_prefix: str
    untrusted_content_template: str
    neutral_insert: str
    attack_payload: str
    expected_benign_answer: str
    attack_target: str
    human_verified: bool

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ScenarioRecord":
        return cls(**dict(value))


@dataclass(frozen=True)
class ConditionCall:
    call_id: str
    scenario_id: str
    attack_family: str
    carrier: str
    language: Language
    condition: Condition
    reasoning_mode: ReasoningMode
    system_prompt: str
    user_prompt: str
    trusted_instruction_prefix: str
    expected_benign_answer: str
    attack_target: str
    request_parameters: dict[str, Any]


@dataclass(frozen=True)
class NormalizedResponse:
    final_text: str
    visible_reasoning_text: str
    model: str
    scenario_id: str
    language: Language
    condition: Condition
    request_parameters: dict[str, Any]
    timestamp: str
    latency: float
    raw_provider_response: Any
    attack_family: str
    carrier: str
    call_id: str
    reasoning_mode: ReasoningMode
    grading_metrics: dict[str, bool]
    attempt: int
    event_type: Literal["response"] = "response"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def render_untrusted_content(record: ScenarioRecord, insert: str) -> str:
    if record.untrusted_content_template.count(INSERT_TOKEN) != 1:
        raise ValueError("untrusted_content_template must contain {{INSERT}} exactly once")
    return record.untrusted_content_template.replace(INSERT_TOKEN, insert)


def render_condition(record: ScenarioRecord, condition: Condition) -> str:
    clean_content = render_untrusted_content(record, record.neutral_insert)
    clean = f"{record.trusted_context}\n\n{record.task_prompt}\n\n{clean_content}"
    if condition == "clean":
        return clean
    if condition == "trusted":
        return f"{clean}\n\n{record.trusted_instruction_prefix} {record.attack_payload}"
    injected_content = render_untrusted_content(record, record.attack_payload)
    injected = f"{record.trusted_context}\n\n{record.task_prompt}\n\n{injected_content}"
    if condition in {"injected_non_think", "injected_think"}:
        return injected
    raise ValueError(f"unknown condition: {condition}")


def expand_conditions(record: ScenarioRecord) -> list[ConditionCall]:
    calls: list[ConditionCall] = []
    for condition in CONDITIONS:
        reasoning_mode: ReasoningMode = "on" if condition == "injected_think" else "off"
        calls.append(
            ConditionCall(
                call_id=f"{record.scenario_id}:{record.language}:{condition}",
                scenario_id=record.scenario_id,
                attack_family=record.attack_family,
                carrier=record.carrier,
                language=record.language,
                condition=condition,
                reasoning_mode=reasoning_mode,
                system_prompt=record.system_prompt,
                user_prompt=render_condition(record, condition),
                trusted_instruction_prefix=record.trusted_instruction_prefix,
                expected_benign_answer=record.expected_benign_answer,
                attack_target=record.attack_target,
                request_parameters={"reasoning_mode": reasoning_mode},
            )
        )
    return calls
