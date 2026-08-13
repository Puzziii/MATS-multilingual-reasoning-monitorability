"""Deterministic Phase 4C analysis of frozen reasoning annotations.

This module performs the authorized post-freeze join.  It never contacts a
provider and never writes to an input artifact.  The only identifier join is
``annotation_id -> reasoning_annotation_key.csv -> call_id``; call IDs are
not emitted in any derived output.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin


REPO_ROOT = Path(__file__).parent.parent.parent
ANALYSIS_DIR = REPO_ROOT / "analysis"
PRIMARY_PATH = ANALYSIS_DIR / "reasoning_annotation_blinded.csv"
KEY_PATH = ANALYSIS_DIR / "reasoning_annotation_key.csv"
LANGUAGE_PATH = ANALYSIS_DIR / "reasoning_language_postblind.csv"
BEHAVIOR_PATH = ANALYSIS_DIR / "behavior_calls.csv"
RAW_ARTIFACT_PATH = REPO_ROOT / "outputs" / "pilot_results.jsonl"

FROZEN_PRIMARY_SHA256 = "6b82e5e63b370a7ee9858889e9912363f18166fd569984c82c64c18802ad1b7c"
FROZEN_LANGUAGE_SHA256 = "167826fc017443e98651878fc1e3c8e4641e1b476aff918e5b0e2367e6c3562f"
FROZEN_RAW_SHA256 = "43bd3b7fffdc6944a3ac23cf5350613b2b32f1e25832ddc025c2a1f2723c3a14"

PRIMARY_LABELS = (
    "payload_noticed",
    "untrusted_recognized",
    "intent_ignore",
    "intent_follow",
    "ambiguous",
)
LANGUAGE_VALUES = ("English", "Tamil", "Tanglish", "mixed", "other")
OUTCOME_VALUES = ("attack_success", "benign_correct", "other_output", "missing")
AVAILABILITY_VALUES = ("non_empty", "persisted_empty", "consumed_unavailable")
FORBIDDEN_OUTPUT_TOKENS = (
    "system_prompt",
    "rendered_user_prompt",
    "visible_reasoning_text",
    "raw_provider_response",
    "request_parameters",
    "evidence_excerpt",
    "reviewer_notes",
    "language_reviewer_notes",
    "normalized_final_text",
    "expected_benign_answer",
    "attack_target",
    "grading_metrics",
    "call_id",
)
OUTPUT_FILES = (
    "reasoning_annotations_unblinded.csv",
    "reasoning_summary.csv",
    "reasoning_behavior_crosswalk.csv",
    "reasoning_report.md",
    "figures/reasoning_availability.png",
    "figures/reasoning_behavior_matrix.png",
    "figures/reasoning_labels_by_language.png",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, columns: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def rate(numerator: int, denominator: int) -> str:
    return "" if denominator == 0 else f"{(100 * numerator / denominator):.6f}"


def rate_text(numerator: int, denominator: int) -> str:
    return "N/A" if denominator == 0 else f"{numerator}/{denominator} ({100 * numerator / denominator:.1f}%)"


def require_hash(path: Path, expected: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f"Frozen input hash mismatch for {path.name}: {actual}")


def availability(primary: dict[str, str]) -> str:
    if primary["trace_status"] == "unavailable":
        return "consumed_unavailable"
    return "non_empty" if primary["visible_reasoning_text"] else "persisted_empty"


def behavior_outcome(row: dict[str, str]) -> str:
    if row["response_available"] != "True":
        return "missing"
    if row["attack_success"] == "True":
        return "attack_success"
    if row["benign_correct"] == "True":
        return "benign_correct"
    if row["other_output"] == "True":
        return "other_output"
    raise ValueError("Persisted injected-think response has no preserved outcome state")


def boolean(value: str) -> str:
    if value not in {"True", "False", "true", "false"}:
        raise ValueError(f"Expected boolean string, got {value!r}")
    return value.lower()


def load_joined_rows() -> list[dict[str, str]]:
    """Load frozen inputs, validate invariants, and make the authorized join."""
    require_hash(PRIMARY_PATH, FROZEN_PRIMARY_SHA256)
    require_hash(LANGUAGE_PATH, FROZEN_LANGUAGE_SHA256)
    require_hash(RAW_ARTIFACT_PATH, FROZEN_RAW_SHA256)

    primary_rows = read_csv(PRIMARY_PATH)
    key_rows = read_csv(KEY_PATH)
    language_rows = read_csv(LANGUAGE_PATH)
    behavior_rows = read_csv(BEHAVIOR_PATH)
    if len(primary_rows) != 12 or len(key_rows) != 12 or len(language_rows) != 12:
        raise ValueError("Frozen annotation inputs must each contain 12 rows")

    primary_by_id = {row["annotation_id"]: row for row in primary_rows}
    key_by_id = {row["annotation_id"]: row for row in key_rows}
    language_by_id = {row["annotation_id"]: row for row in language_rows}
    if len(primary_by_id) != 12 or set(primary_by_id) != set(key_by_id) != set(language_by_id):
        raise ValueError("Annotation IDs are not a one-to-one frozen join")

    injected_think_by_call = {
        row["call_id"]: row for row in behavior_rows if row["condition"] == "injected_think"
    }
    if len(injected_think_by_call) != 12:
        raise ValueError("Frozen behavioral analysis must contain 12 injected-think rows")

    joined: list[dict[str, str]] = []
    for annotation_id in sorted(primary_by_id):
        primary = primary_by_id[annotation_id]
        key = key_by_id[annotation_id]
        language = language_by_id[annotation_id]
        behavior = injected_think_by_call.get(key["call_id"])
        if behavior is None:
            raise ValueError("Key call ID has no injected-think behavioral row")
        status = availability(primary)
        label_eligible = status == "non_empty"
        if status == "non_empty":
            if primary["human_review_complete"] != "true" or language["language_review_complete"] != "true":
                raise ValueError("Non-empty trace lacks completed frozen review")
            if any(primary[field] not in {"yes", "no"} for field in PRIMARY_LABELS):
                raise ValueError("Non-empty trace has an invalid frozen primary label")
            if language["reasoning_language"] not in LANGUAGE_VALUES:
                raise ValueError("Non-empty trace has an invalid frozen reasoning language")
        elif status == "consumed_unavailable" and any(primary[field] for field in PRIMARY_LABELS):
            raise ValueError("Consumed unavailable trace has a non-frozen primary label")

        joined.append({
            "annotation_id": annotation_id,
            "scenario_id": key["scenario_id"],
            "prompt_language": key["prompt_language"],
            "attack_family": behavior["attack_family"],
            "trace_status": primary["trace_status"],
            "reasoning_availability": status,
            "label_eligible": str(label_eligible).lower(),
            "blinding_compromised": boolean(key["blinding_compromised"]),
            # Preserve raw frozen entries, but make unavailable analysis values
            # explicit so persisted-empty traces cannot be treated as label noes.
            **{f"frozen_{field}": primary[field] for field in PRIMARY_LABELS},
            **{field: primary[field] if label_eligible else "unavailable" for field in PRIMARY_LABELS},
            "annotation_confidence": primary["annotation_confidence"],
            "human_review_complete": primary["human_review_complete"],
            "reasoning_language": language["reasoning_language"],
            "language_review_complete": language["language_review_complete"],
            "behavioral_outcome": behavior_outcome(behavior),
            "attack_success": boolean(behavior["attack_success"]) if behavior["attack_success"] else "",
            "benign_correct": boolean(behavior["benign_correct"]) if behavior["benign_correct"] else "",
            "other_output": boolean(behavior["other_output"]) if behavior["other_output"] else "",
            "response_available": boolean(behavior["response_available"]),
        })

    if Counter(row["reasoning_availability"] for row in joined) != Counter({
        "non_empty": 9, "persisted_empty": 2, "consumed_unavailable": 1,
    }):
        raise ValueError("Frozen 9/12 reasoning-availability gate failed")
    return joined


def population(rows: list[dict[str, str]], name: str) -> list[dict[str, str]]:
    if name == "all_attempts":
        return rows
    if name == "persisted_responses":
        return [row for row in rows if row["reasoning_availability"] != "consumed_unavailable"]
    if name == "non_empty_label_eligible":
        return [row for row in rows if row["label_eligible"] == "true"]
    if name == "strictly_blinded_eligible":
        return [
            row for row in rows
            if row["label_eligible"] == "true" and row["blinding_compromised"] == "false"
        ]
    raise ValueError(f"Unknown population: {name}")


SUMMARY_COLUMNS = [
    "table", "population", "group_type", "group_value", "measure", "value",
    "numerator", "denominator", "percentage", "note",
]


def summary_row(
    table: str,
    population_name: str,
    group_type: str,
    group_value: str,
    measure: str,
    value: str,
    numerator: int,
    denominator: int,
    note: str = "",
) -> dict[str, str]:
    return {
        "table": table,
        "population": population_name,
        "group_type": group_type,
        "group_value": group_value,
        "measure": measure,
        "value": value,
        "numerator": str(numerator),
        "denominator": str(denominator),
        "percentage": rate(numerator, denominator),
        "note": note,
    }


def build_summary(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    summary: list[dict[str, str]] = []
    all_rows = population(rows, "all_attempts")
    for value in AVAILABILITY_VALUES:
        count = sum(row["reasoning_availability"] == value for row in all_rows)
        summary.append(summary_row("availability", "all_attempts", "availability", value,
                                   "attempt_count", value, count, len(all_rows)))

    for name in ("non_empty_label_eligible", "strictly_blinded_eligible"):
        selected = population(rows, name)
        denominator = len(selected)
        for field in PRIMARY_LABELS:
            for value in ("yes", "no"):
                count = sum(row[field] == value for row in selected)
                summary.append(summary_row("primary_labels", name, "all", "all", field,
                                           value, count, denominator))
        for value, count in sorted(Counter(row["annotation_confidence"] for row in selected).items()):
            summary.append(summary_row("annotation_confidence", name, "all", "all",
                                       "annotation_confidence", value, count, denominator))

    persisted = population(rows, "persisted_responses")
    for value in (*LANGUAGE_VALUES, "unavailable"):
        count = sum(row["reasoning_language"] == value for row in persisted)
        if count:
            summary.append(summary_row("reasoning_language", "persisted_responses",
                                       "all", "all", "reasoning_language", value,
                                       count, len(persisted),
                                       "Frozen language-form assignments; includes persisted-empty traces."))

    for prompt_language in sorted({row["prompt_language"] for row in persisted}):
        grouped = [row for row in persisted if row["prompt_language"] == prompt_language]
        for value in LANGUAGE_VALUES:
            count = sum(row["reasoning_language"] == value for row in grouped)
            summary.append(summary_row("reasoning_language_by_prompt", "persisted_responses",
                                       "prompt_language", prompt_language, "reasoning_language",
                                       value, count, len(grouped),
                                       "Frozen language-form categories only."))

    eligible = population(rows, "non_empty_label_eligible")
    for group_field in ("prompt_language", "attack_family", "behavioral_outcome"):
        for group_value in sorted({row[group_field] for row in eligible}):
            grouped = [row for row in eligible if row[group_field] == group_value]
            for field in PRIMARY_LABELS:
                for value in ("yes", "no"):
                    count = sum(row[field] == value for row in grouped)
                    summary.append(summary_row("label_breakdown", "non_empty_label_eligible",
                                               group_field, group_value, field, value,
                                               count, len(grouped)))
    return summary


CROSSWALK_COLUMNS = [
    "population", "label", "label_value", "behavioral_outcome", "count", "denominator", "percentage"
]


def build_crosswalk(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for name in ("non_empty_label_eligible", "strictly_blinded_eligible"):
        selected = population(rows, name)
        denominator = len(selected)
        for label in ("payload_noticed", "untrusted_recognized", "intent_ignore", "intent_follow"):
            for value in ("yes", "no"):
                for outcome in OUTCOME_VALUES:
                    count = sum(
                        row[label] == value and row["behavioral_outcome"] == outcome
                        for row in selected
                    )
                    output.append({
                        "population": name,
                        "label": label,
                        "label_value": value,
                        "behavioral_outcome": outcome,
                        "count": str(count),
                        "denominator": str(denominator),
                        "percentage": rate(count, denominator),
                    })
    return output


UNBLINDED_COLUMNS = [
    "annotation_id", "scenario_id", "prompt_language", "attack_family", "trace_status",
    "reasoning_availability", "label_eligible", "blinding_compromised",
    *[f"frozen_{field}" for field in PRIMARY_LABELS], *PRIMARY_LABELS,
    "annotation_confidence", "human_review_complete",
    "reasoning_language", "language_review_complete", "behavioral_outcome",
    "attack_success", "benign_correct", "other_output", "response_available",
]


def markdown_table(headers: list[str], rows: Iterable[Iterable[str]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines.extend("| " + " | ".join(values) + " |" for values in rows)
    return lines


def build_report(rows: list[dict[str, str]], summary: list[dict[str, str]], crosswalk: list[dict[str, str]]) -> str:
    del summary, crosswalk  # The report is reconstructed directly from the same canonical joined rows.
    all_rows = population(rows, "all_attempts")
    persisted = population(rows, "persisted_responses")
    eligible = population(rows, "non_empty_label_eligible")
    strict = population(rows, "strictly_blinded_eligible")
    lines = [
        "# Phase 4C deterministic reasoning-monitorability analysis",
        "",
        "This is a small, descriptive analysis. Every percentage below includes its stated numerator and denominator; no causal interpretation is made.",
        "",
        "## Frozen inputs and post-freeze exposure note",
        "",
        f"- Primary annotation SHA-256: `{FROZEN_PRIMARY_SHA256}`.",
        f"- Post-blind language-form SHA-256: `{FROZEN_LANGUAGE_SHA256}`.",
        f"- Raw pilot SHA-256: `{FROZEN_RAW_SHA256}`.",
        "- Broad behavioral metadata was briefly exposed only after both annotation sets were frozen. No annotation-ID mapping or outcome linkage occurred before label formation; this is treated as non-material to frozen labels.",
        "",
        "## Analysis populations",
        "",
    ]
    lines += markdown_table(
        ["Population", "Count", "Definition"],
        [
            ["All injected-think attempts", str(len(all_rows)), "All frozen attempted calls."],
            ["Persisted responses", str(len(persisted)), "Responses persisted in the frozen behavioral analysis."],
            ["Non-empty label-eligible traces", str(len(eligible)), "Non-empty reasoning with completed frozen primary and language reviews."],
            ["Strictly blinded eligible traces", str(len(strict)), "Eligible traces excluding the two hidden-key sensitivity records."],
        ],
    )
    lines += ["", "## Reasoning availability", ""]
    lines += markdown_table(
        ["Status", "Count / all attempts"],
        [[value.replace("_", " "), rate_text(sum(r["reasoning_availability"] == value for r in all_rows), len(all_rows))]
         for value in AVAILABILITY_VALUES],
    )
    lines += [
        "",
        "The preregistered availability gate is 9/12 non-empty traces and is satisfied. Persisted-empty and consumed-unavailable traces remain unavailable for primary label rates; they are not coded as `no`.",
        "",
        "## Frozen primary labels and confidence",
        "",
    ]
    label_rows = []
    for field in PRIMARY_LABELS:
        label_rows.append([field.replace("_", " "), rate_text(sum(r[field] == "yes" for r in eligible), len(eligible)),
                           rate_text(sum(r[field] == "no" for r in eligible), len(eligible))])
    lines += markdown_table(["Frozen field", "Yes / eligible", "No / eligible"], label_rows)
    confidence = Counter(r["annotation_confidence"] for r in eligible)
    lines += [""]
    lines += markdown_table(["Confidence", "Count / eligible"],
                            [[value, rate_text(count, len(eligible))] for value, count in sorted(confidence.items())])
    lines += ["", "## Frozen reasoning-language form", ""]
    language_counts = Counter(r["reasoning_language"] for r in persisted)
    lines += markdown_table(
        ["Frozen language value", "Count / persisted responses"],
        [[value, rate_text(language_counts[value], len(persisted))] for value in LANGUAGE_VALUES if language_counts[value]],
    )
    lines += [
        "",
        "Language comparisons below use only frozen language-form values. The two persisted-empty traces are not label-eligible, regardless of their frozen form entries.",
        "",
        "### Frozen reasoning language × prompt language",
        "",
    ]
    prompt_languages = sorted({row["prompt_language"] for row in persisted})
    language_headers = ["Prompt language", "n", *LANGUAGE_VALUES]
    language_rows = []
    for prompt_language in prompt_languages:
        group = [row for row in persisted if row["prompt_language"] == prompt_language]
        language_rows.append([prompt_language, str(len(group))] + [
            rate_text(sum(row["reasoning_language"] == value for row in group), len(group))
            for value in LANGUAGE_VALUES
        ])
    lines += markdown_table(language_headers, language_rows)
    lines += [
        "",
        "## Label breakdowns among non-empty eligible traces",
        "",
    ]
    for field in ("prompt_language", "attack_family", "behavioral_outcome"):
        lines += [f"### By {field.replace('_', ' ')}", ""]
        grouped = sorted({r[field] for r in eligible})
        headers = [field.replace("_", " "), "n", "Payload noticed", "Untrusted recognized", "Intent ignore", "Intent follow"]
        table_rows = []
        for value in grouped:
            group = [r for r in eligible if r[field] == value]
            table_rows.append([value, str(len(group))] + [
                rate_text(sum(r[label] == "yes" for r in group), len(group))
                for label in ("payload_noticed", "untrusted_recognized", "intent_ignore", "intent_follow")
            ])
        lines += markdown_table(headers, table_rows)
        lines += [""]
    lines += ["## Raw label × behavioral-outcome cross-tabs", ""]
    for label in ("payload_noticed", "untrusted_recognized", "intent_ignore", "intent_follow"):
        rows_for_label = []
        for value in ("yes", "no"):
            rows_for_label.append([value] + [
                rate_text(sum(r[label] == value and r["behavioral_outcome"] == outcome for r in eligible), len(eligible))
                for outcome in OUTCOME_VALUES
            ])
        lines += [f"### {label.replace('_', ' ')}", ""]
        lines += markdown_table(["Label value", *[outcome.replace("_", " ") for outcome in OUTCOME_VALUES]], rows_for_label)
        lines += [""]
    lines += [
        "The preregistered recognition definition is `untrusted_recognized = yes`. Raw behavioral states are retained above; no additional monitorability or faithfulness category is introduced.",
        "",
        "## Blinding-sensitivity analysis",
        "",
    ]
    sensitivity_rows = []
    for field in PRIMARY_LABELS:
        sensitivity_rows.append([
            field.replace("_", " "),
            rate_text(sum(r[field] == "yes" for r in eligible), len(eligible)),
            rate_text(sum(r[field] == "yes" for r in strict), len(strict)),
        ])
    lines += markdown_table(["Frozen field", "All eligible (n=9)", "Strictly blinded eligible (n=7)"], sensitivity_rows)
    lines += [
        "",
        "The sensitivity exclusion removes exactly the two hidden-key records marked as blinding-compromised. Their identities and contents are not reported.",
        "",
    ]
    return "\n".join(lines)


def png_info() -> PngImagePlugin.PngInfo:
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Software", "MATS Phase 4C deterministic renderer")
    metadata.add_text("Creation Time", "1970-01-01T00:00:00Z")
    return metadata


def canvas(title: str, width: int = 1000, height: int = 620) -> tuple[Image.Image, ImageDraw.ImageDraw, Any]:
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((30, 22), title, fill="black", font=font)
    return image, draw, font


def save_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", pnginfo=png_info(), optimize=False, compress_level=9)


def draw_availability(rows: list[dict[str, str]], path: Path) -> None:
    image, draw, font = canvas("Reasoning availability (all 12 injected-think attempts)")
    colors = {"non_empty": "#3b82f6", "persisted_empty": "#f59e0b", "consumed_unavailable": "#6b7280"}
    for index, value in enumerate(AVAILABILITY_VALUES):
        count = sum(row["reasoning_availability"] == value for row in rows)
        y = 110 + index * 150
        draw.text((40, y), value.replace("_", " "), fill="black", font=font)
        draw.rectangle((250, y, 250 + count * 55, y + 34), fill=colors[value], outline="black")
        draw.text((270 + count * 55, y + 10), rate_text(count, len(rows)), fill="black", font=font)
    draw.text((40, 565), "Counts are descriptive; persisted-empty and consumed-unavailable are not label negatives.", fill="black", font=font)
    save_png(image, path)


def draw_behavior_matrix(rows: list[dict[str, str]], path: Path) -> None:
    eligible = population(rows, "non_empty_label_eligible")
    image, draw, font = canvas("Frozen labels by injected-think behavioral outcome (eligible traces)")
    labels = ("payload_noticed", "untrusted_recognized", "intent_ignore", "intent_follow")
    left, top, cell_w, cell_h = 230, 120, 165, 75
    for col, outcome in enumerate(OUTCOME_VALUES):
        draw.text((left + col * cell_w + 8, 80), outcome.replace("_", " "), fill="black", font=font)
    for row_index, label in enumerate(labels):
        y = top + row_index * cell_h
        draw.text((25, y + 28), label.replace("_", " "), fill="black", font=font)
        for col, outcome in enumerate(OUTCOME_VALUES):
            count = sum(r[label] == "yes" and r["behavioral_outcome"] == outcome for r in eligible)
            shade = 245 - min(count, 9) * 18
            draw.rectangle((left + col * cell_w, y, left + (col + 1) * cell_w - 4, y + cell_h - 4),
                           fill=(shade, shade, 255), outline="black")
            draw.text((left + col * cell_w + 60, y + 28), str(count), fill="black", font=font)
    draw.text((25, 565), "Cells are counts of yes labels; denominator for each row is 9 eligible traces.", fill="black", font=font)
    save_png(image, path)


def draw_labels_by_language(rows: list[dict[str, str]], path: Path) -> None:
    eligible = population(rows, "non_empty_label_eligible")
    image, draw, font = canvas("Frozen yes-label counts by prompt language (eligible traces)")
    languages = sorted({row["prompt_language"] for row in eligible})
    labels = ("payload_noticed", "untrusted_recognized", "intent_ignore", "intent_follow")
    colors = ("#3b82f6", "#10b981", "#8b5cf6", "#ef4444")
    for language_index, language in enumerate(languages):
        group = [row for row in eligible if row["prompt_language"] == language]
        x0 = 125 + language_index * 285
        draw.text((x0, 515), f"{language} (n={len(group)})", fill="black", font=font)
        for label_index, label in enumerate(labels):
            count = sum(row[label] == "yes" for row in group)
            x = x0 + label_index * 58
            height = count * 95
            draw.rectangle((x, 470 - height, x + 38, 470), fill=colors[label_index], outline="black")
            draw.text((x + 12, 450 - height), str(count), fill="black", font=font)
            draw.text((x, 535), str(label_index + 1), fill="black", font=font)
    legend = "1 payload noticed   2 untrusted recognized   3 intent ignore   4 intent follow"
    draw.text((40, 575), legend, fill="black", font=font)
    save_png(image, path)


def scan_outputs(output_dir: Path) -> None:
    for relative in OUTPUT_FILES:
        data = (output_dir / relative).read_bytes().lower()
        for token in FORBIDDEN_OUTPUT_TOKENS:
            if token.encode("utf-8") in data:
                raise ValueError(f"Forbidden field/content token in derived output: {token}")
        if relative != "reasoning_annotations_unblinded.csv" and b"ann-" in data:
            raise ValueError("Aggregate output contains an annotation-ID mapping")


def write_outputs(output_dir: Path) -> dict[str, str]:
    rows = load_joined_rows()
    summary = build_summary(rows)
    crosswalk = build_crosswalk(rows)
    write_csv(output_dir / "reasoning_annotations_unblinded.csv", UNBLINDED_COLUMNS, rows)
    write_csv(output_dir / "reasoning_summary.csv", SUMMARY_COLUMNS, summary)
    write_csv(output_dir / "reasoning_behavior_crosswalk.csv", CROSSWALK_COLUMNS, crosswalk)
    (output_dir / "reasoning_report.md").write_text(build_report(rows, summary, crosswalk), encoding="utf-8")
    draw_availability(rows, output_dir / "figures" / "reasoning_availability.png")
    draw_behavior_matrix(rows, output_dir / "figures" / "reasoning_behavior_matrix.png")
    draw_labels_by_language(rows, output_dir / "figures" / "reasoning_labels_by_language.png")
    scan_outputs(output_dir)
    return {relative: sha256(output_dir / relative) for relative in OUTPUT_FILES}


def verify_determinism() -> dict[str, str]:
    with tempfile.TemporaryDirectory(prefix="reasoning-analysis-") as temporary:
        root = Path(temporary)
        first = write_outputs(root / "first")
        second = write_outputs(root / "second")
        if first != second:
            raise ValueError("Deterministic generation check failed")
        return first


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ANALYSIS_DIR)
    parser.add_argument("--verify-determinism", action="store_true")
    args = parser.parse_args()
    output_hashes = write_outputs(args.output_dir)
    if args.verify_determinism:
        verification_hashes = verify_determinism()
        if output_hashes != verification_hashes:
            raise ValueError("Requested output differs from deterministic verification output")


if __name__ == "__main__":
    main()
