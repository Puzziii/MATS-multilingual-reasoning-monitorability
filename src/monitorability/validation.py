from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from .models import (
    DELIMITER_CLOSE,
    DELIMITER_OPEN,
    INSERT_TOKEN,
    ScenarioRecord,
    render_condition,
)
from .normalize import normalize_text


REQUIRED_FIELDS = (
    "scenario_id",
    "attack_family",
    "carrier",
    "language",
    "system_prompt",
    "task_prompt",
    "trusted_context",
    "trusted_instruction_prefix",
    "untrusted_content_template",
    "neutral_insert",
    "attack_payload",
    "expected_benign_answer",
    "attack_target",
    "human_verified",
)
ALLOWED_FIELDS = frozenset(REQUIRED_FIELDS)
ATTACK_FAMILIES = frozenset(
    {"simple_override", "fake_authority", "task_output_hijack", "synthetic_canary_extraction"}
)
CARRIERS = frozenset({"retrieved_content", "quoted_message", "tool_api_output"})
LANGUAGES = frozenset({"en", "ta", "tanglish"})
PROTECTED_FIELDS = (
    "task_prompt",
    "trusted_context",
    "trusted_instruction_prefix",
    "neutral_insert",
    "attack_payload",
    "expected_benign_answer",
    "attack_target",
)
_PLACEHOLDER_RE = re.compile(
    r"(\[\[.*?\]\]|<\s*(?:todo|placeholder|tbd|translate|review)[^>]*>|"
    r"\b(?:placeholder|todo|tbd|replace[_ -]?me|human review required|machine-translate)\b)",
    re.IGNORECASE | re.DOTALL,
)


class ValidationError(ValueError):
    """Raised when records cannot be executed safely."""


def contains_placeholder(value: str) -> bool:
    return bool(_PLACEHOLDER_RE.search(value))


def _delimiter_sequence_errors(value: str, field: str, *, require_insert: bool) -> list[str]:
    errors: list[str] = []
    if value.count(DELIMITER_OPEN) != 1:
        errors.append(f"{field} must contain exactly one {DELIMITER_OPEN}")
    if value.count(DELIMITER_CLOSE) != 1:
        errors.append(f"{field} must contain exactly one {DELIMITER_CLOSE}")
    if require_insert and value.count(INSERT_TOKEN) != 1:
        errors.append(f"{field} must contain exactly one {INSERT_TOKEN}")
    if not require_insert and INSERT_TOKEN in value:
        errors.append(f"{field} must not contain {INSERT_TOKEN}")
    open_index = value.find(DELIMITER_OPEN)
    close_index = value.find(DELIMITER_CLOSE)
    if require_insert:
        insert_index = value.find(INSERT_TOKEN)
        if open_index >= 0 and insert_index >= 0 and close_index >= 0 and not (open_index < insert_index < close_index):
            errors.append(f"{field} delimiters and {INSERT_TOKEN} must occur in opening/insert/closing order")
    elif open_index >= 0 and close_index >= 0 and open_index >= close_index:
        errors.append(f"{field} delimiters must occur in opening/closing order")
    return errors


def _validate_record_shape(value: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    unknown = sorted(set(value) - ALLOWED_FIELDS)
    if unknown:
        errors.append(f"unknown fields: {', '.join(unknown)}")
    missing = [field for field in REQUIRED_FIELDS if field not in value]
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
        return errors
    for field in REQUIRED_FIELDS:
        field_value = value[field]
        if field == "human_verified":
            if not isinstance(field_value, bool):
                errors.append("human_verified must be a boolean")
        elif not isinstance(field_value, str) or not field_value.strip():
            errors.append(f"{field} must be a non-empty string")
    if isinstance(value.get("attack_family"), str) and value["attack_family"] not in ATTACK_FAMILIES:
        errors.append(f"invalid attack_family: {value['attack_family']}")
    if isinstance(value.get("carrier"), str) and value["carrier"] not in CARRIERS:
        errors.append(f"invalid carrier: {value['carrier']}")
    if isinstance(value.get("language"), str) and value["language"] not in LANGUAGES:
        errors.append(f"invalid language: {value['language']}")
    for field, field_value in value.items():
        if isinstance(field_value, str) and contains_placeholder(field_value):
            errors.append(f"placeholder remains in {field}")
    template = value.get("untrusted_content_template")
    if isinstance(template, str):
        errors.extend(_delimiter_sequence_errors(template, "untrusted_content_template", require_insert=True))
    system = value.get("system_prompt")
    if isinstance(system, str):
        errors.extend(_delimiter_sequence_errors(system, "system_prompt", require_insert=False))
    for field in PROTECTED_FIELDS:
        field_value = value.get(field)
        if isinstance(field_value, str):
            for token in (DELIMITER_OPEN, DELIMITER_CLOSE, INSERT_TOKEN):
                if token in field_value:
                    errors.append(f"{field} must not contain delimiter token {token}")
    return errors


def validate_record(value: Mapping[str, Any], *, require_human_verified: bool = True) -> None:
    errors = _validate_record_shape(value)
    if require_human_verified and value.get("human_verified") is not True:
        errors.append("record is not human-verified")
    if errors:
        raise ValidationError("; ".join(errors))

    record = ScenarioRecord.from_mapping(value)
    clean = normalize_text(render_condition(record, "clean"))
    trusted = normalize_text(render_condition(record, "trusted"))
    injected = normalize_text(render_condition(record, "injected_non_think"))
    injected_think = normalize_text(render_condition(record, "injected_think"))
    target = normalize_text(record.attack_target)
    expected_benign_answer = normalize_text(record.expected_benign_answer)
    if target == expected_benign_answer:
        errors.append("expected_benign_answer and attack_target must differ after normalization")
    if target in normalize_text(record.system_prompt):
        errors.append("attack_target must not occur in system_prompt")
    if target in normalize_text(record.neutral_insert):
        errors.append("attack_target must not occur in neutral_insert")
    if target not in trusted:
        errors.append("trusted prompt does not contain attack_target")
    if target not in injected:
        errors.append("injected prompt does not contain attack_target")
    if injected != injected_think:
        errors.append("injected non-think and think prompts must be identical")
    errors.extend(_delimiter_sequence_errors(clean, "rendered clean prompt", require_insert=False))
    errors.extend(_delimiter_sequence_errors(injected, "rendered injected prompt", require_insert=False))
    if record.attack_family == "synthetic_canary_extraction":
        if target in normalize_text(record.attack_payload):
            errors.append("attack_target must not occur in attack_payload")
        if target not in normalize_text(record.trusted_context):
            errors.append("synthetic canary attack_target must appear in trusted_context")
        if target not in clean:
            errors.append("synthetic canary attack_target must appear in rendered clean prompt")
        if target in normalize_text(record.task_prompt) or target in normalize_text(record.untrusted_content_template):
            errors.append("synthetic canary attack_target may occur in clean only through trusted_context")
    else:
        if target not in normalize_text(record.attack_payload):
            errors.append("attack_target must occur in attack_payload")
        if target in clean:
            errors.append("rendered clean prompt contains attack_target")
    if errors:
        raise ValidationError("; ".join(errors))


def collect_validation_errors(
    values: Iterable[Mapping[str, Any]], *, require_human_verified: bool = True
) -> list[str]:
    records = list(values)
    errors: list[str] = []
    seen_pairs: set[tuple[str, str]] = set()
    target_owner: dict[str, str] = {}
    target_by_scenario: dict[str, str] = {}
    metadata_by_scenario: dict[str, tuple[str, str, str]] = {}
    languages_by_scenario: dict[str, set[str]] = {}

    for index, value in enumerate(records, start=1):
        try:
            validate_record(value, require_human_verified=require_human_verified)
        except ValidationError as exc:
            errors.append(f"record {index}: {exc}")

        scenario_id = value.get("scenario_id")
        language = value.get("language")
        target = value.get("attack_target")
        family = value.get("attack_family")
        carrier = value.get("carrier")
        expected = value.get("expected_benign_answer")
        if isinstance(scenario_id, str) and isinstance(language, str):
            pair = (scenario_id, language)
            if pair in seen_pairs:
                errors.append(f"record {index}: duplicate scenario/language pair: {scenario_id}/{language}")
            seen_pairs.add(pair)
            languages_by_scenario.setdefault(scenario_id, set()).add(language)
            metadata = (str(family), str(carrier), str(expected))
            previous_metadata = metadata_by_scenario.setdefault(scenario_id, metadata)
            if previous_metadata != metadata:
                errors.append(f"record {index}: attack-family, carrier, or expected-answer changed across languages for {scenario_id}")
            if isinstance(target, str):
                previous_target = target_by_scenario.setdefault(scenario_id, target)
                if previous_target != target:
                    errors.append(f"record {index}: attack_target changed across languages for {scenario_id}")
                previous_owner = target_owner.setdefault(target, scenario_id)
                if previous_owner != scenario_id:
                    errors.append(f"record {index}: attack_target reused by different scenarios: {target}")

    for scenario_id, languages in sorted(languages_by_scenario.items()):
        missing_languages = LANGUAGES - languages
        if missing_languages:
            errors.append(
                f"scenario {scenario_id} missing languages: {', '.join(sorted(missing_languages))}"
            )
    return errors


def validate_records(
    values: Iterable[Mapping[str, Any]], *, require_human_verified: bool = True
) -> list[ScenarioRecord]:
    records = list(values)
    errors = collect_validation_errors(records, require_human_verified=require_human_verified)
    if errors:
        raise ValidationError("\n".join(errors))
    return [ScenarioRecord.from_mapping(value) for value in records]
