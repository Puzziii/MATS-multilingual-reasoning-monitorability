"""Focused invariants for the completed outcome-blinded language form."""
from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path


REPO = Path(__file__).parent.parent
FORM = REPO / "analysis" / "reasoning_language_postblind.csv"
PRIMARY = REPO / "analysis" / "reasoning_annotation_blinded.csv"
FROZEN_PRIMARY_SHA256 = "6b82e5e63b370a7ee9858889e9912363f18166fd569984c82c64c18802ad1b7c"
ALLOWED_AVAILABLE_VALUES = {"English", "Tamil", "Tanglish", "mixed", "other"}


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_completed_language_form_is_structurally_blinded():
    form_rows = _rows(FORM)
    primary_rows = _rows(PRIMARY)

    assert hashlib.sha256(PRIMARY.read_bytes()).hexdigest() == FROZEN_PRIMARY_SHA256
    assert list(form_rows[0]) == [
        "annotation_id",
        "reasoning_language",
        "language_review_complete",
        "language_reviewer_notes",
    ]
    assert len(form_rows) == len({row["annotation_id"] for row in form_rows}) == 12
    assert all(re.fullmatch(r"ann-[0-9a-f]{16}", row["annotation_id"]) for row in form_rows)

    primary_status = {row["annotation_id"]: row["trace_status"] for row in primary_rows}
    assert {row["annotation_id"] for row in form_rows} == set(primary_status)
    available = [row for row in form_rows if primary_status[row["annotation_id"]] == "available"]
    unavailable = [row for row in form_rows if primary_status[row["annotation_id"]] == "unavailable"]

    assert len(available) == 11
    assert all(row["reasoning_language"] in ALLOWED_AVAILABLE_VALUES for row in available)
    assert all(row["language_review_complete"] == "true" for row in available)
    assert len(unavailable) == 1
    assert unavailable[0]["reasoning_language"] == "unavailable"
    assert unavailable[0]["language_review_complete"] == "false"
    assert unavailable[0]["language_reviewer_notes"] == ""
