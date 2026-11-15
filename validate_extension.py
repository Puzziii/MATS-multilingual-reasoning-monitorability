"""Structural validator for the Kannada + Kanglish extension.

A pass means "structurally validated" and nothing more: it cannot show that the
Kannada or Kanglish text is natural or means the same thing as the English
original. That needs a fluent human reviewer.

Errors block a live run. Warnings are judgement items for the reviewer;
--strict turns them into failures.
"""
import argparse
import sys

from monitorability.kn_extension import validate


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true",
                        help="treat warnings as failures")
    args = parser.parse_args()

    report = validate()

    for message in report.errors:
        print("ERROR  ", message)
    for message in report.warnings:
        print("WARNING", message)

    failed = bool(report.errors) or (args.strict and bool(report.warnings))
    print()
    print("=" * 60)
    print("EXTENSION VALIDATION " + ("FAILED" if failed else "PASSED (structural only)"))
    print("=" * 60)
    print(f"Records: {report.records}   Planned calls: {report.calls}")
    print(f"Errors: {len(report.errors)}   Warnings (reviewer items): {len(report.warnings)}")
    print("Status: structurally validated. NOT linguistically reviewed; "
          "human_verified stays False.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
