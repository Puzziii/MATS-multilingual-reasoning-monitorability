# Pilot execution protocol v1.0

**Status:** Frozen v1.0 — 2026-08-11T15:52:53+00:00
**Scope:** Pre-data operational addendum

## Relationship to the frozen research design

The research design remains frozen at tag `prereg-v1.0` and commit `196f5bcb3ba9589490b1429ca7558085e5682d14`. This addendum fixes timeout, retry, ordering, artifact, and resume mechanics that were omitted from the original preregistration.

No experimental result was observed before choosing these rules. This addendum changes no prompt, hypothesis, metric, exclusion, condition, grading rule, normalization rule, or analysis rule.

## Pinned inputs

- Frozen preregistration SHA-256: `5d9c9fd877e391fe9f6c38bccc8eed9cc829e19e2f05c83bb04c95c548555f77`
- Frozen pilot dataset SHA-256: `1782cdfdcc0c27cbf48b579809d64cf4fc14b4a8f4d03820ce75baa9dddbac4a`
- Provider configuration: the fixed configuration recorded in the frozen preregistration, including model `sarvam-105b` and the fixed request parameters.
- Execution-protocol SHA-256 is intentionally not embedded in this file; it is recorded in the finalization report and post-freeze time ledger.

## Fixed execution plan

1. Construct the same 12 verified scenario-language units and the same 48 frozen condition calls.
2. Deterministically shuffle only the 12 unit order with `random.Random(20260811)`.
3. Preserve this within-unit order exactly: `clean`, `trusted`, `injected_non_think`, `injected_think`.
4. Execute sequentially only; concurrency is prohibited.
5. Use a 120-second request timeout.
6. Enforce at least 2.1 seconds between request start times.
7. Set `max_retries=0`: one network attempt per unique call, no automatic retry for any HTTP or transport failure, and at most 48 network attempts.

### Ordered scenario-language units

1. `P3:ta`
2. `P4:ta`
3. `P3:tanglish`
4. `P4:en`
5. `P4:tanglish`
6. `P1:tanglish`
7. `P2:tanglish`
8. `P1:ta`
9. `P3:en`
10. `P2:ta`
11. `P2:en`
12. `P1:en`

The complete ordered call list is the above unit order expanded with the fixed within-unit order. It contains exactly 48 unique call IDs.

## Manifest and append-only events

The first event in a new output artifact must be a manifest containing:

- frozen preregistration commit and tag;
- preregistration, execution-protocol, and pilot-data hashes;
- fixed model parameters;
- execution-order seed `20260811`;
- the complete ordered list of 48 call IDs;
- `planned_unique_calls=48`; and
- `maximum_network_attempts=48`.

Before each request, append a `request_started` event. After a valid response, append a `response` event immediately. Preserve raw provider responses, visible reasoning, final output, usage, timestamps, finish reason, grading, and attempt metadata. Credentials and request headers must never be persisted.

On an explicit HTTP or transport failure, append a sanitized `failure` or `uncertain` event immediately and halt the entire run. A schema mismatch, credential error, unexpected reasoning-mode behavior, or artifact corruption also halts the run.

## Uncertain calls, deviations, and resume

A timeout, `OSError`, `HTTPException`, connection interruption, or unmatched `request_started` event is uncertain and must never be repeated automatically.

Any future decision to repeat a failed or uncertain call requires a dated protocol-deviation note before making that request.

Resume requires an explicit flag and the original output artifact. Before resuming, verify the manifest; preregistration, execution-protocol, and pilot-data hashes; fixed provider configuration; and ordered call IDs.

Resume skips calls with exactly one valid completed response. It must stop for manual review when:

- a `request_started` event has no terminal event;
- a call has multiple successful responses;
- the manifest or any pinned hash differs; or
- a failure or uncertain event lacks a documented deviation.

The run must never execute more than 48 unique experimental calls or 48 total network attempts.
