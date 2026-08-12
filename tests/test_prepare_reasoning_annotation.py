"""Offline invariants for the Phase 4B outcome-blinded annotation materials."""
from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path

from monitorability import prepare_reasoning_annotation as preparation

_REPO = Path(__file__).parent.parent
ARTIFACT = _REPO / "outputs" / "pilot_results.jsonl"
REQUIRED_RAW_SHA256 = "43bd3b7fffdc6944a3ac23cf5350613b2b32f1e25832ddc025c2a1f2723c3a14"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _generate(tmp_path: Path) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    preparation.run(ARTIFACT, tmp_path)
    return (
        _read_rows(tmp_path / "reasoning_annotation_blinded.csv"),
        _read_rows(tmp_path / "reasoning_annotation_key.csv"),
        _read_rows(tmp_path / "reasoning_language_postblind.csv"),
    )


def test_frozen_primary_fields_and_no_planned_action():
    assert preparation.BLINDED_COLUMNS == [
        "annotation_id", "system_prompt", "rendered_user_prompt",
        "visible_reasoning_text", "trace_status", "payload_noticed",
        "untrusted_recognized", "intent_ignore", "intent_follow", "ambiguous",
        "annotation_confidence", "evidence_excerpt", "reviewer_notes",
        "human_review_complete",
    ]
    assert "planned_action" not in preparation.BLINDED_COLUMNS
    assert "attack_noticed" not in preparation.BLINDED_COLUMNS
    assert "untrusted_boundary_recognized" not in preparation.BLINDED_COLUMNS


def test_generation_is_silent_and_preserves_raw_hash(tmp_path, capsys):
    before = hashlib.sha256(ARTIFACT.read_bytes()).hexdigest()
    preparation.run(ARTIFACT, tmp_path)
    captured = capsys.readouterr()
    after = hashlib.sha256(ARTIFACT.read_bytes()).hexdigest()
    assert captured.out == ""
    assert captured.err == ""
    assert before == REQUIRED_RAW_SHA256
    assert after == REQUIRED_RAW_SHA256


def test_packet_counts_status_and_blank_primary_annotations(tmp_path):
    blinded, _, _ = _generate(tmp_path)
    available = [row for row in blinded if row["trace_status"] == "available"]
    unavailable = [row for row in blinded if row["trace_status"] == "unavailable"]
    assert len(blinded) == 12
    assert len(available) == 11
    assert len(unavailable) == 1
    primary_fields = [
        "payload_noticed", "untrusted_recognized", "intent_ignore", "intent_follow", "ambiguous",
    ]
    for row in available:
        assert all(row[field] == "" for field in primary_fields)
        assert row["annotation_confidence"] == ""
        assert row["evidence_excerpt"] == ""
        assert row["reviewer_notes"] == ""
        assert row["human_review_complete"] == "false"
    unavailable_row = unavailable[0]
    assert unavailable_row["visible_reasoning_text"] == ""
    assert all(unavailable_row[field] == "" for field in primary_fields)
    assert unavailable_row["annotation_confidence"] == "unavailable"
    assert unavailable_row["reviewer_notes"] == "Reasoning unavailable"
    assert unavailable_row["human_review_complete"] == "false"


def test_annotation_ids_are_opaque_unique_and_key_is_one_to_one(tmp_path):
    blinded, key, _ = _generate(tmp_path)
    blinded_ids = [row["annotation_id"] for row in blinded]
    key_ids = [row["annotation_id"] for row in key]
    assert len(blinded_ids) == len(set(blinded_ids)) == 12
    assert all(re.fullmatch(r"ann-[0-9a-f]{16}", value) for value in blinded_ids)
    assert set(blinded_ids) == set(key_ids)
    assert list(key[0]) == preparation.KEY_COLUMNS
    assert sum(row["blinding_compromised"] == "true" for row in key) == 2
    assert sum(row["source_response_available"] == "true" for row in key) == 11


def test_no_outcome_or_compromise_leakage_in_blinded_packet(tmp_path):
    blinded, _, _ = _generate(tmp_path)
    headers = set(blinded[0])
    prohibited = {
        "call_id", "scenario_id", "language", "prompt_language", "reasoning_language",
        "final_text", "expected_benign_answer", "attack_target", "grading_metrics",
        "attack_success", "benign_correct", "other_output", "usage", "finish_reason",
        "blinding_compromised", "planned_action", "unclear",
    }
    assert not headers & prohibited


def test_postblind_language_form_is_unpopulated_and_unlinked(tmp_path):
    blinded, key, language_rows = _generate(tmp_path)
    assert list(language_rows[0]) == preparation.POSTBLIND_LANGUAGE_COLUMNS
    assert set(row["annotation_id"] for row in language_rows) == set(row["annotation_id"] for row in blinded)
    assert all("call_id" not in row and "prompt_language" not in row for row in language_rows)
    assert sum(row["reasoning_language"] == "" for row in language_rows) == 11
    assert sum(row["reasoning_language"] == "unavailable" for row in language_rows) == 1
    assert all(row["language_review_complete"] == "false" for row in language_rows)
    assert len(key) == 12


def test_only_blinded_packet_has_reasoning_column(tmp_path):
    blinded, key, language_rows = _generate(tmp_path)
    assert "visible_reasoning_text" in blinded[0]
    assert "visible_reasoning_text" not in key[0]
    assert "visible_reasoning_text" not in language_rows[0]


def test_generation_is_byte_identical(tmp_path):
    output_one = tmp_path / "one"
    output_two = tmp_path / "two"
    preparation.run(ARTIFACT, output_one)
    preparation.run(ARTIFACT, output_two)
    for filename in (
        "reasoning_annotation_blinded.csv",
        "reasoning_annotation_key.csv",
        "reasoning_language_postblind.csv",
    ):
        assert hashlib.sha256((output_one / filename).read_bytes()).hexdigest() == hashlib.sha256(
            (output_two / filename).read_bytes()
        ).hexdigest()
