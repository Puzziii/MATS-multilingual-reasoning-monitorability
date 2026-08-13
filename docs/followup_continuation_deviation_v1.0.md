# Follow-up continuation deviation v1.0

**Status:** Frozen operational recovery deviation for the Phase 5 follow-up.

## Incident disposition

The HTTP 403 call `P7:ta:clean` recorded in
`outputs/followup_results_attempt1_403.jsonl` is a consumed unavailable study
attempt. Its SHA-256 is
`16f31be5bf7fe9d9f58ab3a0321603f06e38b4323bad6860f757e93566e4a4b4`.
It counts toward the original 48-attempt study ceiling and will never be
retried or replaced.

Authorization was subsequently verified using one explicitly non-study
arithmetic smoke request recorded in `outputs/followup_auth_smoke.jsonl`.
Its SHA-256 is
`da52c7445445c3582fd7d5cbb3a9cc57c1867b9057988f28fcf9b072e44c4e9f`.
The smoke request returned exactly `420` from `sarvam-105b`. It is excluded
from all study accounting.

## Authorized continuation

Exactly 47 study calls remain authorized. The first remaining call is
`P7:ta:trusted`; the last is `P8:ta:injected_think`. The continuation preserves
the remainder of the frozen order and excludes `P7:ta:clean`.

The maximum total study network attempts across the failed-attempt and
continuation artifacts remains 48: one consumed failure plus at most 47
continuation attempts. The continuation is sequential, uses the frozen timeout
and request-spacing values, writes append-only fsynced events, and has zero
retries. It must halt after any failure. No retry, replacement, resume, or
second continuation is authorized.

The final analysis must merge the failed-attempt artifact and continuation
artifact deterministically. `P7:ta:clean` remains unavailable in behavioral
analyses.

This is an operational recovery deviation, not a hypothesis or
outcome-dependent analytical change. The frozen follow-up dataset and protocol
remain unmodified.
