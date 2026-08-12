"""Prepare the deterministic, outcome-blinded Phase 4B annotation packet.

This offline module reads only the fields required to construct the blinded
packet and its restricted key.  It never prints prompts, reasoning, final
answers, outcomes, or key mappings.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).parent.parent.parent
ARTIFACT_PATH = _REPO_ROOT / "outputs" / "pilot_results.jsonl"
FIXTURE_PATH = _REPO_ROOT / "tests" / "fixtures" / "synthetic_partial_artifact.jsonl"
OUTPUT_DIR = _REPO_ROOT / "analysis"
REQUIRED_ARTIFACT_SHA256 = "43bd3b7fffdc6944a3ac23cf5350613b2b32f1e25832ddc025c2a1f2723c3a14"
RANDOMIZATION_SEED = 20260812

BLINDED_COLUMNS = [
    "annotation_id",
    "system_prompt",
    "rendered_user_prompt",
    "visible_reasoning_text",
    "trace_status",
    "payload_noticed",
    "untrusted_recognized",
    "intent_ignore",
    "intent_follow",
    "ambiguous",
    "annotation_confidence",
    "evidence_excerpt",
    "reviewer_notes",
    "human_review_complete",
]

KEY_COLUMNS = [
    "annotation_id",
    "call_id",
    "scenario_id",
    "prompt_language",
    "source_response_available",
    "blinding_compromised",
]

POSTBLIND_LANGUAGE_COLUMNS = [
    "annotation_id",
    "reasoning_language",
    "language_review_complete",
    "language_reviewer_notes",
]

_PRIMARY_ANNOTATION_COLUMNS = [
    "payload_noticed",
    "untrusted_recognized",
    "intent_ignore",
    "intent_follow",
    "ambiguous",
]


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _verify_artifact(path: Path) -> None:
    if hashlib.sha256(path.read_bytes()).hexdigest() != REQUIRED_ARTIFACT_SHA256:
        raise ValueError("raw pilot artifact hash does not match the frozen reference")


def _load_events(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _compromised_trace_hashes(fixture: Path) -> set[str]:
    """Return non-semantic hashes of non-empty fixture reasoning fields only."""
    hashes: set[str] = set()
    for event in _load_events(fixture):
        if event.get("event_type") != "response":
            continue
        reasoning = event.get("visible_reasoning_text")
        if isinstance(reasoning, str) and reasoning:
            hashes.add(_sha256_text(reasoning))
    return hashes


def _annotation_id(call_id: str) -> str:
    """Create a deterministic opaque identifier without exposing the source ID."""
    digest = hashlib.sha256(f"{RANDOMIZATION_SEED}:{call_id}".encode("utf-8")).hexdigest()
    return f"ann-{digest[:16]}"


def _available_row(
    annotation_id: str,
    system_prompt: str,
    user_prompt: str,
    reasoning: str,
) -> dict[str, str]:
    row = {
        "annotation_id": annotation_id,
        "system_prompt": system_prompt,
        "rendered_user_prompt": user_prompt,
        "visible_reasoning_text": reasoning,
        "trace_status": "available",
        "annotation_confidence": "",
        "evidence_excerpt": "",
        "reviewer_notes": "",
        "human_review_complete": "false",
    }
    row.update({column: "" for column in _PRIMARY_ANNOTATION_COLUMNS})
    return row


def _unavailable_row(annotation_id: str, system_prompt: str, user_prompt: str) -> dict[str, str]:
    row = _available_row(annotation_id, system_prompt, user_prompt, "")
    row.update({
        "trace_status": "unavailable",
        "annotation_confidence": "unavailable",
        "reviewer_notes": "Reasoning unavailable",
    })
    return row


def build_rows(
    artifact: Path = ARTIFACT_PATH,
    fixture: Path = FIXTURE_PATH,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    """Build blinded, restricted-key, and post-blind language rows without output."""
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

    from monitorability import pilot_run

    plan = pilot_run.build_plan(require_clean_worktree=False)
    source_rows: list[dict[str, str]] = []
    compromised_hashes = _compromised_trace_hashes(fixture)
    for call in plan.calls:
        if call.condition != "injected_think":
            continue
        annotation_id = _annotation_id(call.call_id)
        response = response_map.get(call.call_id)
        if response is not None:
            reasoning = response.get("visible_reasoning_text")
            if not isinstance(reasoning, str):
                raise ValueError("persisted injected-think response lacks a string reasoning field")
            source_rows.append({
                "annotation_id": annotation_id,
                "call_id": call.call_id,
                "scenario_id": call.scenario_id,
                "prompt_language": call.language,
                "source_response_available": "true",
                "blinding_compromised": str(_sha256_text(reasoning) in compromised_hashes).lower(),
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
    if sum(row["source_response_available"] == "true" for row in source_rows) != 11:
        raise ValueError("expected exactly 11 persisted injected-think responses")
    if sum(row["trace_status"] == "unavailable" for row in source_rows) != 1:
        raise ValueError("expected exactly one unavailable injected-think trace")
    if sum(row["blinding_compromised"] == "true" for row in source_rows) != 2:
        raise ValueError("expected exactly two pre-codebook compromised trace identities")

    rng = random.Random(RANDOMIZATION_SEED)
    rng.shuffle(source_rows)

    blinded_rows: list[dict[str, str]] = []
    key_rows: list[dict[str, str]] = []
    language_rows: list[dict[str, str]] = []
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


def run(
    artifact: Path = ARTIFACT_PATH,
    output_dir: Path = OUTPUT_DIR,
    fixture: Path = FIXTURE_PATH,
) -> None:
    """Generate files silently so no trace or prompt reaches terminal output."""
    blinded_rows, key_rows, language_rows = build_rows(artifact, fixture)
    _write_csv(output_dir / "reasoning_annotation_blinded.csv", blinded_rows, BLINDED_COLUMNS)
    _write_csv(output_dir / "reasoning_annotation_key.csv", key_rows, KEY_COLUMNS)
    _write_csv(
        output_dir / "reasoning_language_postblind.csv",
        language_rows,
        POSTBLIND_LANGUAGE_COLUMNS,
    )
    _verify_artifact(artifact)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare Phase 4B blinded reasoning annotation materials")
    parser.add_argument("--artifact", type=Path, default=ARTIFACT_PATH)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--fixture", type=Path, default=FIXTURE_PATH)
    args = parser.parse_args(argv)
    run(args.artifact, args.output_dir, args.fixture)
    return 0


if __name__ == "__main__":
    sys.exit(main())
