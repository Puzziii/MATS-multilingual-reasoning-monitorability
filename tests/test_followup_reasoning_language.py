"""Focused structural validation for frozen follow-up reasoning-language labels."""
from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path


REPO = Path(__file__).parent.parent
PRIMARY = REPO / "analysis" / "followup_reasoning_annotation_blinded.csv"
FORM = REPO / "analysis" / "followup_reasoning_language_postblind.csv"
FROZEN_PRIMARY_SHA256 = "bd5f784011cb3d51cd46ad7c9842bcc33861f1b26300d4bfe2bdf8bda08e2ae0"
ALLOWED = {"English", "Tamil", "Tanglish", "mixed", "other"}


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_followup_language_form_is_complete_and_unlinked():
    assert hashlib.sha256(PRIMARY.read_bytes()).hexdigest() == FROZEN_PRIMARY_SHA256
    primary, form = _rows(PRIMARY), _rows(FORM)
    assert list(form[0]) == [
        "annotation_id", "reasoning_language", "language_review_complete", "language_reviewer_notes"
    ]
    assert len(form) == len({row["annotation_id"] for row in form}) == 12
    assert all(re.fullmatch(r"ann-[0-9a-f]{16}", row["annotation_id"]) for row in form)
    assert {row["annotation_id"] for row in form} == {row["annotation_id"] for row in primary}
    form_by_id = {row["annotation_id"]: row for row in form}
    nonempty = [row for row in primary if row["visible_reasoning_text"]]
    empty = [row for row in primary if not row["visible_reasoning_text"]]
    assert len(nonempty) == 11
    assert all(form_by_id[row["annotation_id"]]["reasoning_language"] in ALLOWED for row in nonempty)
    assert all(form_by_id[row["annotation_id"]]["language_review_complete"] == "true" for row in nonempty)
    assert len(empty) == 1
    empty_form = form_by_id[empty[0]["annotation_id"]]
    assert empty_form["reasoning_language"] == "unavailable"
    assert empty_form["language_review_complete"] == "false"
    assert empty_form["language_reviewer_notes"] == ""
    assert not ({"call_id", "scenario_id", "prompt_language", "final_text", "blinding_compromised"} & set(form[0]))
