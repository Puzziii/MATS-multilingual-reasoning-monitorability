"""Prepare the deterministic, outcome-blinded Phase 6A follow-up annotation packet."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from pathlib import Path

from monitorability import followup_run
from monitorability.prepare_reasoning_annotation import (
    BLINDED_COLUMNS, KEY_COLUMNS, POSTBLIND_LANGUAGE_COLUMNS,
    _annotation_id, _available_row, _unavailable_row, _sha256_text
)

_REPO_ROOT = Path(__file__).parent.parent.parent
ARTIFACT_PATH = _REPO_ROOT / "outputs" / "followup_results.jsonl"
OUTPUT_DIR = _REPO_ROOT / "analysis"
REQUIRED_ARTIFACT_SHA256 = "ec2293b1da27f4972acbd251d4a7b08c880850ae3061a24cfee3f3b25f86b385"
RANDOMIZATION_SEED = 20260812  # Frozen policy seed

def _verify_artifact(path: Path) -> None:
    if hashlib.sha256(path.read_bytes()).hexdigest() != REQUIRED_ARTIFACT_SHA256:
        raise ValueError("raw follow-up artifact hash does not match the frozen reference")

def _load_events(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]

def build_rows(artifact: Path = ARTIFACT_PATH):
    _verify_artifact(artifact)
    events = _load_events(artifact)
    response_map = {
        event["call_id"]: event
        for event in events
        if event.get("event_type") == "response" and event.get("condition") == "injected_think"
    }
    failure_ids = {
        event["call_id"]
        for event in events
        if event.get("event_type") == "failure" and event.get("condition") == "injected_think"
    }
    
    plan = followup_run.build_plan(require_clean_worktree=False)
    source_rows = []
    
    for call in plan.calls:
        if call.condition != "injected_think":
            continue
        annotation_id = _annotation_id(call.call_id)
        response = response_map.get(call.call_id)
        if response is not None:
            reasoning = response.get("visible_reasoning_text")
            if not isinstance(reasoning, str):
                raise ValueError("persisted injected-think response lacks a string reasoning field")
            # The prompt says: "Apply the frozen codebook's existing treatment for persisted-empty reasoning."
            # In Phase 4B, persisted-empty had trace_status="available" but visible_reasoning_text="".
            source_rows.append({
                "annotation_id": annotation_id,
                "call_id": call.call_id,
                "scenario_id": call.scenario_id,
                "prompt_language": call.language,
                "source_response_available": "true",
                "blinding_compromised": "false",
                "system_prompt": call.system_prompt,
                "rendered_user_prompt": call.user_prompt,
                "visible_reasoning_text": reasoning,
                "trace_status": "available",
            })
        elif call.call_id in failure_ids:
            source_rows.append({
                "annotation_id": annotation_id,
                "call_id": call.call_id,
                "scenario_id": call.scenario_id,
                "prompt_language": call.language,
                "source_response_available": "false",
                "blinding_compromised": "false",
                "system_prompt": call.system_prompt,
                "rendered_user_prompt": call.user_prompt,
                "visible_reasoning_text": "",
                "trace_status": "unavailable",
            })
        else:
            raise ValueError("injected-think plan call has neither response nor consumed failure")

    if len(source_rows) != 12:
        raise ValueError("expected exactly 12 injected-think annotation rows")
    if sum(row["source_response_available"] == "true" for row in source_rows) != 12:
        # Wait, the prompt says: "12 persisted responses; 11 non-empty, label-eligible traces; 1 persisted-empty trace; no consumed/unavailable"
        # In pilot, there was 1 unavailable. Here it's 12 persisted responses, 0 unavailable.
        raise ValueError("expected exactly 12 persisted injected-think responses")
    if sum(row["trace_status"] == "unavailable" for row in source_rows) != 0:
        raise ValueError("expected exactly 0 unavailable injected-think traces")
        
    rng = random.Random(RANDOMIZATION_SEED)
    rng.shuffle(source_rows)
    
    blinded_rows = []
    key_rows = []
    language_rows = []
    for source in source_rows:
        if source["trace_status"] == "available":
            blinded_rows.append(_available_row(
                source["annotation_id"],
                source["system_prompt"],
                source["rendered_user_prompt"],
                source["visible_reasoning_text"],
            ))
            language_rows.append({
                "annotation_id": source["annotation_id"],
                "reasoning_language": "",
                "language_review_complete": "false",
                "language_reviewer_notes": "",
            })
        else:
            blinded_rows.append(_unavailable_row(
                source["annotation_id"],
                source["system_prompt"],
                source["rendered_user_prompt"],
            ))
            language_rows.append({
                "annotation_id": source["annotation_id"],
                "reasoning_language": "unavailable",
                "language_review_complete": "false",
                "language_reviewer_notes": "",
            })
        key_rows.append({column: source[column] for column in KEY_COLUMNS})

    _verify_artifact(artifact)
    return blinded_rows, key_rows, language_rows

def _write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

def run(artifact: Path = ARTIFACT_PATH, output_dir: Path = OUTPUT_DIR) -> None:
    blinded_rows, key_rows, language_rows = build_rows(artifact)
    _write_csv(output_dir / "followup_reasoning_annotation_blinded.csv", blinded_rows, BLINDED_COLUMNS)
    _write_csv(output_dir / "followup_reasoning_annotation_key.csv", key_rows, KEY_COLUMNS)
    _write_csv(output_dir / "followup_reasoning_language_postblind.csv", language_rows, POSTBLIND_LANGUAGE_COLUMNS)
    _verify_artifact(artifact)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    args = parser.parse_args(argv)
    run()
    return 0

if __name__ == "__main__":
    sys.exit(main())
