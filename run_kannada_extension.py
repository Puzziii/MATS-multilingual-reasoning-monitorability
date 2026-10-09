import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from monitorability.grading import grade
from monitorability.models import ScenarioRecord, expand_conditions
from monitorability.normalize import normalize_response
from monitorability.providers.sarvam import SarvamProvider


FILES = [
    Path("data/kannada_extension_scenarios.jsonl"),
    Path("data/kanglish_extension_scenarios.jsonl"),
]

OUTPUT = Path("outputs/kannada_extension_results.jsonl")

TIMEOUT_SECONDS = 120.0
MINIMUM_START_INTERVAL_SECONDS = 2.1


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def load_records():
    records = []

    for path in FILES:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(
                        ScenarioRecord.from_mapping(json.loads(line))
                    )

    return records


def build_calls():
    records = load_records()

    calls = [
        call
        for record in records
        for call in expand_conditions(record)
    ]

    return calls


def dry_run(calls):
    print("=" * 60)
    print("KANNADA + KANGLISH EXTENSION")
    print("=" * 60)

    print(f"Records loaded: {len(load_records())}")
    print(f"Condition calls: {len(calls)}")

    thinking = [
        call for call in calls
        if call.reasoning_mode == "on"
    ]

    print(f"Thinking calls: {len(thinking)}")
    print(f"Non-thinking calls: {len(calls) - len(thinking)}")

    print()
    print("Calls by language:")

    for language in ["kn", "kanglish"]:
        print(
            f"  {language}: "
            f"{sum(call.language == language for call in calls)}"
        )

    print()
    print("Calls by condition:")

    for condition in [
        "clean",
        "trusted",
        "injected_non_think",
        "injected_think",
    ]:
        print(
            f"  {condition}: "
            f"{sum(call.condition == condition for call in calls)}"
        )

    print()
    print("=" * 60)
    print("DRY RUN ONLY — NO API CALLS")
    print("=" * 60)


def run_live(calls):
    if not os.environ.get("SARVAM_API_KEY"):
        raise RuntimeError(
            "SARVAM_API_KEY is not set. "
            "The author must provide a valid Sarvam API key."
        )

    if OUTPUT.exists():
        raise RuntimeError(
            f"{OUTPUT} already exists. "
            "Refusing to append or overwrite an existing run."
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    provider = SarvamProvider(
        allow_network=True,
        timeout=TIMEOUT_SECONDS,
    )

    completed = 0
    last_start = None

    with OUTPUT.open("w", encoding="utf-8") as handle:

        for call in calls:

            # Enforce the same minimum spacing between request starts.
            if last_start is not None:
                elapsed = time.monotonic() - last_start
                remaining = MINIMUM_START_INTERVAL_SECONDS - elapsed

                if remaining > 0:
                    time.sleep(remaining)

            request_start = time.monotonic()

            print(
                f"[{completed + 1}/{len(calls)}] "
                f"{call.call_id} | "
                f"{call.language} | "
                f"{call.condition}"
            )

            try:
                provider_response = provider.generate(call)

                response = normalize_response(
                    provider_response,
                    call,
                    timestamp=timestamp(),
                    latency=time.monotonic() - request_start,
                    grading_metrics=grade(
                        provider_response.get("final_text", ""),
                        expected_benign_answer=call.expected_benign_answer,
                        attack_target=call.attack_target,
                        condition=call.condition,
                    ),
                    attempt=1,
                )

                handle.write(
                    json.dumps(
                        response.to_dict(),
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                    + "\n"
                )
                handle.flush()

                completed += 1
                last_start = request_start

            except Exception as exc:

                error_event = {
                    "event_type": "error",
                    "call_id": call.call_id,
                    "scenario_id": call.scenario_id,
                    "language": call.language,
                    "condition": call.condition,
                    "reasoning_mode": call.reasoning_mode,
                    "attempt": 1,
                    "timestamp": timestamp(),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }

                handle.write(
                    json.dumps(
                        error_event,
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                    + "\n"
                )
                handle.flush()

                print()
                print("!!! RUN HALTED !!!")
                print(f"Failed call: {call.call_id}")
                print(f"Error: {type(exc).__name__}: {exc}")
                print(f"Completed successfully: {completed}")
                print(f"Output saved to: {OUTPUT}")

                raise

    print()
    print("=" * 60)
    print("LIVE RUN COMPLETE")
    print("=" * 60)
    print(f"Completed calls: {completed}")
    print(f"Output: {OUTPUT}")


def main():
    parser = argparse.ArgumentParser()

    mode = parser.add_mutually_exclusive_group(required=True)

    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and inspect calls without making API requests.",
    )

    mode.add_argument(
        "--live",
        action="store_true",
        help="Run the extension against Sarvam.",
    )

    args = parser.parse_args()

    calls = build_calls()

    if len(calls) != 32:
        raise RuntimeError(
            f"Expected exactly 32 calls, found {len(calls)}."
        )

    if args.dry_run:
        dry_run(calls)
        return

    run_live(calls)


if __name__ == "__main__":
    main()