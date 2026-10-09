import json
from pathlib import Path

FILES = [
    Path("data/kannada_extension_scenarios.jsonl"),
    Path("data/kanglish_extension_scenarios.jsonl"),
]

EXPECTED_LANGUAGES = {"kn", "kanglish"}
EXPECTED_SCENARIOS = {"P5", "P6", "P7", "P8"}

REQUIRED_FIELDS = {
    "scenario_id",
    "attack_family",
    "carrier",
    "language",
    "system_prompt",
    "task_prompt",
    "trusted_context",
    "trusted_instruction_prefix",
    "untrusted_content_template",
    "neutral_insert",
    "attack_payload",
    "expected_benign_answer",
    "attack_target",
    "human_verified",
}


def load_records():
    records = []

    for path in FILES:
        with path.open("r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                if not line.strip():
                    continue

                record = json.loads(line)
                records.append((path, line_number, record))

    return records


records = load_records()

errors = []

# --------------------------------------------------
# Basic record checks
# --------------------------------------------------

for path, line_number, record in records:
    prefix = f"{path}:{line_number}"

    missing = REQUIRED_FIELDS - set(record)
    if missing:
        errors.append(f"{prefix}: missing fields: {sorted(missing)}")

    if record.get("language") not in EXPECTED_LANGUAGES:
        errors.append(
            f"{prefix}: invalid language {record.get('language')!r}"
        )

    if record.get("scenario_id") not in EXPECTED_SCENARIOS:
        errors.append(
            f"{prefix}: unexpected scenario {record.get('scenario_id')!r}"
        )

    if record.get("human_verified") is not False:
        errors.append(
            f"{prefix}: human_verified must currently be False"
        )

    template = record.get("untrusted_content_template", "")

    if template.count("{{INSERT}}") != 1:
        errors.append(
            f"{prefix}: untrusted_content_template must contain "
            "{{INSERT}} exactly once"
        )

    for field, value in record.items():
        if isinstance(value, str):
            if "{{" in value or "}}" in value:
                if field != "untrusted_content_template":
                    errors.append(
                        f"{prefix}: placeholder found in {field}"
                    )


# --------------------------------------------------
# Duplicate scenario/language pairs
# --------------------------------------------------

pairs = [
    (record["scenario_id"], record["language"])
    for _, _, record in records
]

if len(pairs) != len(set(pairs)):
    errors.append("duplicate scenario/language pair found")


# --------------------------------------------------
# Every scenario must have both languages
# --------------------------------------------------

for scenario_id in EXPECTED_SCENARIOS:
    languages = {
        record["language"]
        for _, _, record in records
        if record["scenario_id"] == scenario_id
    }

    missing = EXPECTED_LANGUAGES - languages

    if missing:
        errors.append(
            f"{scenario_id}: missing languages {sorted(missing)}"
        )


# --------------------------------------------------
# Kannada and Kanglish must match structurally
# --------------------------------------------------

for scenario_id in EXPECTED_SCENARIOS:
    matching = [
        record
        for _, _, record in records
        if record["scenario_id"] == scenario_id
    ]

    if len(matching) != 2:
        continue

    kannada = next(
        r for r in matching if r["language"] == "kn"
    )

    kanglish = next(
        r for r in matching if r["language"] == "kanglish"
    )

    for field in [
        "attack_family",
        "carrier",
        "expected_benign_answer",
        "attack_target",
    ]:
        if kannada[field] != kanglish[field]:
            errors.append(
                f"{scenario_id}: {field} differs between Kannada and Kanglish"
            )


# --------------------------------------------------
# Result
# --------------------------------------------------

if errors:
    print("❌ EXTENSION VALIDATION FAILED")
    print()

    for error in errors:
        print("-", error)

    raise SystemExit(1)

print("=" * 60)
print("EXTENSION VALIDATION PASSED")
print("=" * 60)

print(f"Scenarios: {sorted(EXPECTED_SCENARIOS)}")
print("Languages: Kannada + Kanglish")
print(f"Records: {len(records)}")
print("No duplicate scenario/language pairs.")
print("Kannada/Kanglish structural checks passed.")