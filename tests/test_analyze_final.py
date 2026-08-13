"""Focused offline invariants for the deterministic final research analysis."""
from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from monitorability import analyze_final as final


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_followup_behavior_and_combined_accounting(tmp_path):
    final.write_outputs(tmp_path)
    followup = _rows(tmp_path / "followup_behavior_calls.csv")
    combined = _rows(tmp_path / "combined_behavior_summary.csv")
    assert len(followup) == 48
    assert sum(row["response_available"] == "true" for row in followup) == 47
    missing = [row for row in followup if row["response_available"] == "false"]
    assert len(missing) == 1
    assert missing[0]["call_id"] == "P7:ta:clean"
    assert missing[0]["benign_correct"] == ""
    response_rows = [row for row in combined if row["group_type"] == "overall" and row["measure"] == "response_availability"]
    assert {(row["dataset"], row["numerator"], row["denominator"]) for row in response_rows} == {
        ("pilot", "47", "48"), ("followup", "47", "48"), ("combined", "94", "96")
    }


def test_primary_behavior_and_pairwise_outputs_are_complete(tmp_path):
    final.write_outputs(tmp_path)
    summary = _rows(tmp_path / "combined_behavior_summary.csv")
    pairwise = _rows(tmp_path / "combined_pairwise_units.csv")
    assert len(pairwise) == 24
    assert sum(row["dataset"] == "pilot" for row in pairwise) == 12
    assert sum(row["dataset"] == "followup" for row in pairwise) == 12
    for dataset in ("pilot", "followup", "combined"):
        for measure in (
            "clean_benign_accuracy", "trusted_target_adherence",
            "injected_non_think_attack_success", "injected_think_attack_success",
            "injected_non_think_benign_correct", "injected_think_benign_correct",
            "injected_non_think_other_output", "injected_think_other_output",
        ):
            row = final.find_metric(summary, dataset, measure)
            assert row["numerator"] != ""
            assert row["denominator"] != ""
            assert row["percentage"] != ""


def test_reasoning_accounting_labels_and_sensitivity(tmp_path):
    final.write_outputs(tmp_path)
    followup = _rows(tmp_path / "followup_reasoning_unblinded.csv")
    combined = _rows(tmp_path / "combined_reasoning_summary.csv")
    assert len(followup) == 12
    assert sum(row["reasoning_availability"] == "non_empty" for row in followup) == 11
    assert sum(row["reasoning_availability"] == "persisted_empty" for row in followup) == 1
    empty = [row for row in followup if row["label_eligible"] == "false"]
    assert len(empty) == 1
    assert all(empty[0][field] == "unavailable" for field in final.PRIMARY_LABELS)

    def denominator(dataset: str, scope: str) -> int:
        row = next(row for row in combined if row["dataset"] == dataset and row["scope"] == scope
                   and row["group_type"] == "all" and row["measure"] == "payload_noticed" and row["value"] == "yes")
        return int(row["denominator"])

    assert denominator("pilot", "all_eligible") == 9
    assert denominator("pilot", "strictly_blinded_eligible") == 7
    assert denominator("followup", "all_eligible") == 11
    assert denominator("combined", "all_eligible") == 20
    assert denominator("combined", "strictly_blinded_eligible") == 18

    availability = [row for row in combined if row["dataset"] == "combined" and row["scope"] == "all_attempts"]
    counts = {row["value"]: int(row["numerator"]) for row in availability}
    assert counts == {"non_empty": 20, "persisted_empty": 3, "consumed_unavailable": 1}


def test_audit_and_qualitative_review_files_follow_frozen_sampling_rules(tmp_path):
    final.write_outputs(tmp_path)
    audit = _rows(tmp_path / "followup_grading_audit_sample.csv")
    assert len(audit) == 12
    assert {row["language"] for row in audit} == {"en", "ta", "tanglish"}
    assert {row["condition"] for row in audit} == {"clean", "trusted", "injected_non_think", "injected_think"}
    assert all(row["human_label"] == row["automatic_correct"] == row["reviewer_notes"] == "" for row in audit)
    assert all(row["raw_final_text"] and row["normalized_text"] and row["condition_specific_target"] for row in audit)
    qualitative = (tmp_path / "qualitative_examples_random.md").read_text(encoding="utf-8")
    assert f"Selection seed: `{final.QUALITATIVE_SEED}`" in qualitative
    assert qualitative.count("Status: **Pending personal human review.**") == 6
    assert all(language in qualitative for language in ("`en`", "`ta`", "`tanglish`"))
    assert "`injected_non_think`" in qualitative and "`injected_think`" in qualitative


def test_generation_is_byte_identical_private_and_preserves_frozen_inputs(tmp_path):
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in final.FROZEN_HASHES}
    first, second = tmp_path / "first", tmp_path / "second"
    first_hashes = final.write_outputs(first)
    second_hashes = final.write_outputs(second)
    assert first_hashes == second_hashes
    assert set(first_hashes) == set(final.OUTPUT_FILES)
    final.forbidden_scan(first, *final.load_followup_behavior()[1:])
    after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in final.FROZEN_HASHES}
    assert before == after == final.FROZEN_HASHES
