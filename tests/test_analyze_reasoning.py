"""Focused tests for deterministic Phase 4C reasoning analysis."""
from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from monitorability import analyze_reasoning as reasoning


def _rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_frozen_join_counts_and_unavailable_label_treatment(tmp_path):
    hashes = reasoning.write_outputs(tmp_path)
    rows = _rows(tmp_path / "reasoning_annotations_unblinded.csv")
    assert len(rows) == 12
    assert sum(row["reasoning_availability"] == "non_empty" for row in rows) == 9
    assert sum(row["reasoning_availability"] == "persisted_empty" for row in rows) == 2
    assert sum(row["reasoning_availability"] == "consumed_unavailable" for row in rows) == 1
    unavailable = [row for row in rows if row["label_eligible"] == "false"]
    assert len(unavailable) == 3
    for row in unavailable:
        assert all(row[field] == "unavailable" for field in reasoning.PRIMARY_LABELS)
    assert sum(row["frozen_payload_noticed"] == "no" for row in unavailable) == 2
    assert sum(row["frozen_payload_noticed"] == "" for row in unavailable) == 1
    assert sum(row["label_eligible"] == "true" and row["blinding_compromised"] == "false" for row in rows) == 7
    assert set(hashes) == set(reasoning.OUTPUT_FILES)


def test_generation_is_byte_identical_and_private(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_hashes = reasoning.write_outputs(first)
    second_hashes = reasoning.write_outputs(second)
    assert first_hashes == second_hashes
    reasoning.scan_outputs(first)
    assert hashlib.sha256(reasoning.RAW_ARTIFACT_PATH.read_bytes()).hexdigest() == reasoning.FROZEN_RAW_SHA256


def test_crosswalk_preserves_raw_behavioral_states(tmp_path):
    reasoning.write_outputs(tmp_path)
    rows = _rows(tmp_path / "reasoning_behavior_crosswalk.csv")
    assert len(rows) == 64
    assert {row["behavioral_outcome"] for row in rows} == set(reasoning.OUTCOME_VALUES)
    assert {row["population"] for row in rows} == {
        "non_empty_label_eligible", "strictly_blinded_eligible"
    }
