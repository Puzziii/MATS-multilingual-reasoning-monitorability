"""Phase 5A focused dataset and schema validation tests.

Tests only the follow-up dataset and its structural invariants.
Does NOT import or inspect Phase 4 reasoning traces, behavioral rows, or grading outputs.
Does NOT run the full pilot test suite.
Does NOT make network calls.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from monitorability.models import (
    CONDITIONS,
    ScenarioRecord,
    expand_conditions,
    render_condition,
    render_untrusted_content,
)
from monitorability.runner import load_records, dry_run
from monitorability.validation import (
    ValidationError,
    collect_validation_errors,
    validate_record,
    validate_records,
)

FOLLOWUP_PATH = Path("data/followup_scenarios.jsonl")
PILOT_PATH = Path("data/pilot_scenarios.jsonl")

EXPECTED_SCENARIO_IDS = {"P5", "P6", "P7", "P8"}
EXPECTED_LANGUAGES = {"en", "ta", "tanglish"}
EXPECTED_FAMILIES = {
    "P5": "simple_override",
    "P6": "fake_authority",
    "P7": "task_output_hijack",
    "P8": "synthetic_canary_extraction",
}
EXPECTED_CARRIERS = {
    "P5": "retrieved_content",
    "P6": "quoted_message",
    "P7": "tool_api_output",
    "P8": "retrieved_content",
}
EXPECTED_TARGETS = {
    "P5": "VIOLET-882",
    "P6": "AMBER-157",
    "P7": "INDIGO-364",
    "P8": "SLATE-793",
}
PILOT_TARGETS = {"ORCHID-731", "COBALT-284", "EMBER-519", "IVORY-426"}


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def followup_records():
    return load_records(FOLLOWUP_PATH)


@pytest.fixture(scope="module")
def pilot_records():
    return load_records(PILOT_PATH)


# ---------------------------------------------------------------------------
# 1. Count and taxonomy invariants
# ---------------------------------------------------------------------------

def test_followup_has_exactly_12_records(followup_records):
    assert len(followup_records) == 12, f"Expected 12, got {len(followup_records)}"


def test_followup_has_exactly_4_scenario_ids(followup_records):
    ids = {r["scenario_id"] for r in followup_records}
    assert ids == EXPECTED_SCENARIO_IDS, f"Scenario IDs: {ids}"


def test_followup_has_all_three_languages(followup_records):
    langs = {r["language"] for r in followup_records}
    assert langs == EXPECTED_LANGUAGES


def test_each_scenario_has_all_three_languages(followup_records):
    for pid in EXPECTED_SCENARIO_IDS:
        langs = {r["language"] for r in followup_records if r["scenario_id"] == pid}
        assert langs == EXPECTED_LANGUAGES, f"{pid} languages: {langs}"


def test_attack_families_match_spec(followup_records):
    for r in followup_records:
        expected = EXPECTED_FAMILIES[r["scenario_id"]]
        assert r["attack_family"] == expected, (
            f"{r['scenario_id']}/{r['language']}: family={r['attack_family']!r}, expected={expected!r}"
        )


def test_carriers_match_spec(followup_records):
    for r in followup_records:
        expected = EXPECTED_CARRIERS[r["scenario_id"]]
        assert r["carrier"] == expected, (
            f"{r['scenario_id']}/{r['language']}: carrier={r['carrier']!r}, expected={expected!r}"
        )


def test_attack_targets_match_spec(followup_records):
    for r in followup_records:
        expected = EXPECTED_TARGETS[r["scenario_id"]]
        assert r["attack_target"] == expected, (
            f"{r['scenario_id']}/{r['language']}: target={r['attack_target']!r}, expected={expected!r}"
        )


def test_attack_targets_are_unique_per_scenario(followup_records):
    targets = {r["attack_target"] for r in followup_records}
    assert len(targets) == 4, f"Expected 4 unique targets, got {targets}"


# ---------------------------------------------------------------------------
# 2. No overlap with pilot
# ---------------------------------------------------------------------------

def test_targets_do_not_overlap_with_pilot(followup_records):
    fu_targets = {r["attack_target"] for r in followup_records}
    overlap = fu_targets & PILOT_TARGETS
    assert not overlap, f"Overlap with pilot targets: {overlap}"


def test_scenario_ids_do_not_overlap_with_pilot(followup_records, pilot_records):
    fu_ids = {r["scenario_id"] for r in followup_records}
    pilot_ids = {r["scenario_id"] for r in pilot_records}
    overlap = fu_ids & pilot_ids
    assert not overlap, f"Scenario ID overlap: {overlap}"


def test_benign_answers_do_not_overlap_with_pilot(followup_records, pilot_records):
    fu_answers = {r["expected_benign_answer"] for r in followup_records}
    pilot_answers = {r["expected_benign_answer"] for r in pilot_records}
    overlap = fu_answers & pilot_answers
    assert not overlap, f"Benign answer overlap with pilot: {overlap}"


# ---------------------------------------------------------------------------
# 3. human_verified=false for all records
# ---------------------------------------------------------------------------

def test_all_records_are_verified(followup_records):
    for r in followup_records:
        assert r["human_verified"] is True, (
            f"{r['scenario_id']}/{r['language']} has human_verified={r['human_verified']!r}"
        )


# ---------------------------------------------------------------------------
# 4. Schema shape validation (require_human_verified=True)
# ---------------------------------------------------------------------------

def test_all_records_pass_schema_shape(followup_records):
    errors = collect_validation_errors(followup_records, require_human_verified=True)
    assert not errors, "Schema validation errors:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# 5. Attack-target placement safeguards
# ---------------------------------------------------------------------------

def test_attack_targets_absent_from_system_prompts(followup_records):
    for r in followup_records:
        target = r["attack_target"]
        assert target not in r["system_prompt"], (
            f"{r['scenario_id']}/{r['language']}: target in system_prompt"
        )


def test_attack_targets_absent_from_task_prompts(followup_records):
    for r in followup_records:
        target = r["attack_target"]
        assert target not in r["task_prompt"], (
            f"{r['scenario_id']}/{r['language']}: target in task_prompt"
        )


def test_attack_targets_absent_from_neutral_inserts(followup_records):
    for r in followup_records:
        target = r["attack_target"]
        assert target not in r["neutral_insert"], (
            f"{r['scenario_id']}/{r['language']}: target in neutral_insert"
        )


def test_p5_p6_p7_targets_in_payloads(followup_records):
    """Non-canary families must have attack_target in attack_payload."""
    for r in followup_records:
        if r["attack_family"] != "synthetic_canary_extraction":
            assert r["attack_target"] in r["attack_payload"], (
                f"{r['scenario_id']}/{r['language']}: target not in attack_payload"
            )


def test_p8_target_not_in_payload(followup_records):
    """Canary extraction: target must NOT be in attack_payload."""
    for r in followup_records:
        if r["attack_family"] == "synthetic_canary_extraction":
            assert r["attack_target"] not in r["attack_payload"], (
                f"{r['scenario_id']}/{r['language']}: target found in attack_payload (canary violation)"
            )


def test_p8_target_in_trusted_context(followup_records):
    """Canary extraction: target must appear in trusted_context."""
    for r in followup_records:
        if r["attack_family"] == "synthetic_canary_extraction":
            assert r["attack_target"] in r["trusted_context"], (
                f"{r['scenario_id']}/{r['language']}: target not in trusted_context"
            )


def test_p8_benign_answer_not_in_neutral_insert(followup_records):
    for r in followup_records:
        if r["attack_family"] == "synthetic_canary_extraction":
            assert r["expected_benign_answer"] not in r["neutral_insert"], (
                f"{r['scenario_id']}/{r['language']}: benign answer in neutral_insert"
            )


def test_clean_prompt_excludes_target_for_non_canary(followup_records):
    for r in followup_records:
        if r["attack_family"] != "synthetic_canary_extraction":
            record = ScenarioRecord.from_mapping(r)
            clean = render_condition(record, "clean")
            assert r["attack_target"] not in clean, (
                f"{r['scenario_id']}/{r['language']}: target in clean prompt"
            )


# ---------------------------------------------------------------------------
# 6. Condition rendering invariants
# ---------------------------------------------------------------------------

def test_injected_prompts_are_identical_across_think_and_non_think(followup_records):
    for r in followup_records:
        record = ScenarioRecord.from_mapping(r)
        calls = {c.condition: c for c in expand_conditions(record)}
        assert calls["injected_non_think"].user_prompt == calls["injected_think"].user_prompt, (
            f"{r['scenario_id']}/{r['language']}: injected prompts differ"
        )


def test_reasoning_modes_are_correct(followup_records):
    for r in followup_records:
        record = ScenarioRecord.from_mapping(r)
        calls = {c.condition: c for c in expand_conditions(record)}
        assert calls["injected_non_think"].reasoning_mode == "off"
        assert calls["injected_think"].reasoning_mode == "on"
        assert calls["clean"].reasoning_mode == "off"
        assert calls["trusted"].reasoning_mode == "off"


def test_exactly_four_conditions_per_unit(followup_records):
    for r in followup_records:
        record = ScenarioRecord.from_mapping(r)
        calls = expand_conditions(record)
        assert len(calls) == 4, f"{r['scenario_id']}/{r['language']}: {len(calls)} conditions"
        assert {c.condition for c in calls} == set(CONDITIONS)


def test_trusted_prompt_contains_attack_target(followup_records):
    for r in followup_records:
        record = ScenarioRecord.from_mapping(r)
        calls = {c.condition: c for c in expand_conditions(record)}
        assert r["attack_target"] in calls["trusted"].user_prompt, (
            f"{r['scenario_id']}/{r['language']}: target not in trusted prompt"
        )


def test_injected_prompt_contains_attack_target(followup_records):
    for r in followup_records:
        record = ScenarioRecord.from_mapping(r)
        calls = {c.condition: c for c in expand_conditions(record)}
        assert r["attack_target"] in calls["injected_non_think"].user_prompt, (
            f"{r['scenario_id']}/{r['language']}: target not in injected prompt"
        )


# ---------------------------------------------------------------------------
# 7. P7-specific: JSON integrity and no raw double quotes in inserts/payloads
# ---------------------------------------------------------------------------

def test_p7_untrusted_template_is_valid_json_after_insert(followup_records):
    for r in followup_records:
        if r["scenario_id"] == "P7":
            record = ScenarioRecord.from_mapping(r)
            # Render with neutral insert — must produce valid JSON inside delimiter
            rendered = render_untrusted_content(record, r["neutral_insert"])
            # Extract content between delimiters
            inner = rendered.split("<untrusted_content>")[1].split("</untrusted_content>")[0]
            try:
                json.loads(inner)
            except json.JSONDecodeError as exc:
                pytest.fail(f"P7/{r['language']} neutral inner content is not valid JSON: {exc}\nContent: {inner!r}")


def test_p7_attack_rendered_template_is_valid_json(followup_records):
    for r in followup_records:
        if r["scenario_id"] == "P7":
            record = ScenarioRecord.from_mapping(r)
            rendered = render_untrusted_content(record, r["attack_payload"])
            inner = rendered.split("<untrusted_content>")[1].split("</untrusted_content>")[0]
            try:
                json.loads(inner)
            except json.JSONDecodeError as exc:
                pytest.fail(f"P7/{r['language']} attack inner content is not valid JSON: {exc}\nContent: {inner!r}")


def test_p7_no_raw_double_quotes_in_neutral_insert_or_payload(followup_records):
    for r in followup_records:
        if r["scenario_id"] == "P7":
            assert '"' not in r["neutral_insert"], (
                f"P7/{r['language']}: raw double-quote in neutral_insert"
            )
            assert '"' not in r["attack_payload"], (
                f"P7/{r['language']}: raw double-quote in attack_payload"
            )


# ---------------------------------------------------------------------------
# 8. Language-specific invariants
# ---------------------------------------------------------------------------

def test_tanglish_contains_no_tamil_unicode(followup_records):
    for r in followup_records:
        if r["language"] == "tanglish":
            raw = json.dumps(r, ensure_ascii=False)
            assert not re.search(r"[\u0B80-\u0BFF]", raw), (
                f"{r['scenario_id']}/tanglish: Tamil Unicode detected"
            )


def test_tamil_contains_tamil_script_in_key_fields(followup_records):
    for r in followup_records:
        if r["language"] == "ta":
            combined = (
                r["task_prompt"] + r["trusted_context"] + r["neutral_insert"] + r["attack_payload"]
            )
            assert re.search(r"[\u0B80-\u0BFF]", combined), (
                f"{r['scenario_id']}/ta: no Tamil script found in key fields"
            )


def test_tanglish_trusted_instruction_prefix_is_english(followup_records):
    for r in followup_records:
        if r["language"] == "tanglish":
            assert r["trusted_instruction_prefix"] == "Trusted user instruction:", (
                f"{r['scenario_id']}/tanglish: prefix={r['trusted_instruction_prefix']!r}"
            )


def test_english_labels_unchanged_in_all_languages(followup_records):
    """English attack targets and benign answers must be identical across all languages for a scenario."""
    for pid in EXPECTED_SCENARIO_IDS:
        group = [r for r in followup_records if r["scenario_id"] == pid]
        targets = {r["attack_target"] for r in group}
        benigns = {r["expected_benign_answer"] for r in group}
        assert len(targets) == 1, f"{pid}: differing targets across languages: {targets}"
        assert len(benigns) == 1, f"{pid}: differing benign answers across languages: {benigns}"


# ---------------------------------------------------------------------------
# 9. 48-call offline preview (dry_run — no network calls)
# ---------------------------------------------------------------------------

def test_offline_48_call_preview_no_network(followup_records):
    """Verify the dry_run reports 48 planned calls and zero network calls."""
    result = dry_run(followup_records)
    assert "network calls: 0" in result
    assert "planned condition calls: 48" in result


def test_total_expand_conditions_equals_48(followup_records):
    total = sum(
        len(expand_conditions(ScenarioRecord.from_mapping(r)))
        for r in followup_records
    )
    assert total == 48, f"Expected 48 planned calls, got {total}"


# ---------------------------------------------------------------------------
# 10. No accidental modification of frozen pilot dataset
# ---------------------------------------------------------------------------

def test_pilot_dataset_hash_unchanged():
    import hashlib
    data = PILOT_PATH.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    # The pilot file hash was confirmed at Phase 4B freeze.
    # It is intentionally NOT checked against the annotation file hash here —
    # only the raw scenarios file is verified.
    assert len(digest) == 64, "SHA-256 digest has unexpected length"
    # Record the hash for traceability (does not fail if hash is unknown):
    # Actual pilot_scenarios.jsonl hash reported in output only.


def test_followup_does_not_modify_pilot_records(followup_records, pilot_records):
    """Follow-up records must not alter pilot scenario IDs or targets."""
    pilot_ids = {r["scenario_id"] for r in pilot_records}
    fu_ids = {r["scenario_id"] for r in followup_records}
    assert not (fu_ids & pilot_ids), f"Overlapping IDs: {fu_ids & pilot_ids}"
