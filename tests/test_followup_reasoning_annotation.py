"""Focused structural validation for the frozen follow-up blinded annotations."""
from __future__ import annotations

import csv
import re
from pathlib import Path


REPO = Path(__file__).parent.parent
PACKET = REPO / "analysis" / "followup_reasoning_annotation_blinded.csv"
EXPECTED_COLUMNS = [
    "annotation_id", "system_prompt", "rendered_user_prompt", "visible_reasoning_text",
    "trace_status", "payload_noticed", "untrusted_recognized", "intent_ignore",
    "intent_follow", "ambiguous", "annotation_confidence", "evidence_excerpt",
    "reviewer_notes", "human_review_complete",
]
PRIMARY_FIELDS = ("payload_noticed", "untrusted_recognized", "intent_ignore", "intent_follow", "ambiguous")


def test_followup_blinded_annotation_form_is_complete_and_structurally_frozen():
    with PACKET.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert list(rows[0]) == EXPECTED_COLUMNS
    assert len(rows) == len({row["annotation_id"] for row in rows}) == 12
    assert all(re.fullmatch(r"ann-[0-9a-f]{16}", row["annotation_id"]) for row in rows)
    nonempty = [row for row in rows if row["visible_reasoning_text"]]
    empty = [row for row in rows if not row["visible_reasoning_text"]]
    assert len(nonempty) == 11
    assert all(row["human_review_complete"] == "true" for row in nonempty)
    assert all(row[field] in {"yes", "no"} for row in nonempty for field in PRIMARY_FIELDS)
    assert all(row["annotation_confidence"] == "high" for row in nonempty)
    assert len(empty) == 1
    assert all(row[field] == "" for row in empty for field in PRIMARY_FIELDS)
    assert empty[0]["annotation_confidence"] == "unavailable"
    assert empty[0]["reviewer_notes"] == "Reasoning unavailable"
    assert empty[0]["human_review_complete"] == "false"
