"""Summarize an extension results JSONL (old v1.0 or new v1.1 format).

Counts attack_success / benign_correct / other. Empty and truncated responses
are 'other' and are never counted as defense.

Usage: python summarize_extension.py outputs/kannada_extension_results.jsonl
"""
import argparse
import json
import sys
from pathlib import Path

from monitorability.kn_extension import render_summary, summarize


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    events = [json.loads(line)
              for line in args.results.read_text(encoding="utf-8").splitlines()
              if line.strip()]
    print(render_summary(summarize(events)), end="")


if __name__ == "__main__":
    main()
