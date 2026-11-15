"""Runner for the Kannada + Kanglish exploratory extension (v1.1 addendum).

Differences from v1.0 (all documented in
docs/kannada_kanglish_extension_deviation_v1.1.md):
  * 38 calls: P6-LOC added (Option C), its clean call skipped
  * fixed-seed shuffled order, recorded in a manifest event
  * manifest with SHA-256 of data and protocol files, git commit, parameters
  * request_started and raw_response events; raw response saved BEFORE grading
  * hard schema check instead of .get("final_text", "")
  * finish_reason and token usage logged; outcome classification added
  * a halted run is preserved and never edited; a rerun is a NEW output file
    labelled with --rerun-of (no selective resume)
"""
import argparse
import os
import sys
import uuid
from pathlib import Path

from monitorability.kn_extension import (
    DEFAULT_OUTPUT,
    EXPECTED_CALLS,
    ORDER_SEED,
    TIMEOUT_SECONDS,
    build_calls,
    build_manifest,
    load_records,
    ordered_calls,
    run_calls,
    validate,
)
from monitorability.providers.sarvam import SarvamProvider


def dry_run(ordered, report) -> None:
    print("=" * 60)
    print("KANNADA + KANGLISH EXTENSION (v1.1)")
    print("=" * 60)
    print(f"Records loaded: {report.records}")
    print(f"Condition calls: {len(ordered)} (expected {EXPECTED_CALLS})")
    print(f"Thinking calls: {sum(c.reasoning_mode == 'on' for c in ordered)}")
    print(f"Order seed: {ORDER_SEED}")
    print(f"Validation errors: {len(report.errors)}   reviewer warnings: {len(report.warnings)}")
    print()
    for index, call in enumerate(ordered, start=1):
        print(f"  {index:2d}. {call.call_id}")
    print()
    print("=" * 60)
    print("DRY RUN ONLY - NO API CALLS")
    print("=" * 60)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--live", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="new file; an existing file is never overwritten")
    parser.add_argument("--rerun-of", default=None,
                        help="run_id of the halted or earlier run this repeats")
    parser.add_argument("--exploratory-unreviewed", action="store_true",
                        help="required for --live while any record has human_verified=False; "
                             "recorded in the manifest")
    args = parser.parse_args()

    report = validate()
    if report.errors:
        for message in report.errors:
            print("ERROR", message)
        print("Validation failed; refusing to continue.")
        return 1

    records = load_records()
    calls = build_calls(records)
    if len(calls) != EXPECTED_CALLS:
        raise RuntimeError(f"Expected exactly {EXPECTED_CALLS} calls, found {len(calls)}.")
    ordered = ordered_calls(calls)

    if args.dry_run:
        dry_run(ordered, report)
        return 0

    if not os.environ.get("SARVAM_API_KEY"):
        raise RuntimeError("SARVAM_API_KEY is not set. The author must provide a valid key.")
    unreviewed = any(not r.human_verified for r in records)
    if unreviewed and not args.exploratory_unreviewed:
        raise RuntimeError(
            "Records have human_verified=False. Re-run with --exploratory-unreviewed to "
            "label this run as exploratory with unreviewed language, or record a human "
            "review first.")
    status = "unreviewed_exploratory" if unreviewed else "human_verified"

    manifest = build_manifest(ordered, run_id=uuid.uuid4().hex[:12],
                              language_review_status=status, rerun_of=args.rerun_of)
    provider = SarvamProvider(allow_network=True, timeout=TIMEOUT_SECONDS)
    print(f"run_id={manifest['run_id']} output={args.output}")
    try:
        completed = run_calls(ordered, provider, args.output, manifest)
    except Exception as exc:  # noqa: BLE001
        print()
        print("!!! RUN HALTED !!!")
        print(f"{type(exc).__name__}: {exc}")
        print(f"Partial output preserved at {args.output}. Do not edit it.")
        print("A rerun must use a new --output and --rerun-of " + manifest["run_id"])
        return 2
    print(f"LIVE RUN COMPLETE: {completed} calls -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
