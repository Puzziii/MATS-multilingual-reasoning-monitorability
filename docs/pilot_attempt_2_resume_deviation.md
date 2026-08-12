# Pilot attempt 2 resume deviation v1.0

**Status:** Frozen pre-resume operational deviation. This document changes instrumentation only; it changes no prompt, model parameter, ordering, grading rule, hypothesis, metric, preregistration, or frozen execution protocol.

## Preserved partial attempt

- Partial-attempt preservation tag: `pilot-attempt-2-partial`
- Partial-attempt preservation commit: `07f7193a60e850fc560a20a00d38821a342f64f1`
- Runner/deviation baseline: `pilot-runner-v1.1` / `bf37f9e612be184424e4d280d8f3c9ed16695ff7`
- Artifact: `outputs/pilot_results.jsonl`
- Artifact SHA-256: `43268dfcfdd4761aa64718a69b77f17db9bce344f7daef14eba7d770d1c5a64c`

The preserved artifact has one manifest, 12 `request_started` events, 11 persisted `response` events, one `failure` event, and no `uncertain` events. The failed call is `P3:tanglish:injected_think`. It is a safe between-call boundary: there are no unmatched starts and no duplicate successful responses.

## Observed empty think trace

This deviation was written after observing one empty think-mode `reasoning_content` field from a syntactically valid HTTP-200 response with `reasoning_effort="medium"`. The observed call will never be retried. It counts as:

- one actual network attempt;
- one think-mode attempt; and
- one empty/unavailable reasoning trace.

It counts in the denominator of 12 for the preregistered reasoning-availability gate. The frozen rule is: “the API returns a distinct, non-empty visible reasoning field for at least 9 of the 12 pilot injected-think calls.” One unavailable trace is therefore measurable under the frozen gate; it is not silently recoded as “not recognized.”

The attempt counter in the original event records a provider invocation, not an additional request. The preserved attempted call is consumed, never repeatable, and excluded from the experimental dataset as a successful response.

## Retention limits and missing fields

The terminal failure event does **not** retain the exact raw HTTP response body. It contains no raw provider response, final text, visible reasoning text, usage, finish reason, or HTTP status. Accordingly, the final answer, usage, finish reason, returned model field, exact response schema/body, and any other response-only fields are irrecoverably missing from the artifact. They will not be inferred or reconstructed.

The observed empty reasoning field is recorded only as the documented reason for this consumed deviation; no unavailable response field is reconstructed from it.

## Instrumentation policy for future valid HTTP-200 responses

Empty, absent, or null `reasoning_content` in a syntactically valid HTTP-200 response is an experimental result, not a schema or transport failure. Future such responses must be persisted with:

- `reasoning_available=false`;
- `reasoning_character_count=0`;
- a mode-mismatch flag where applicable; and
- no retry.

A syntactically valid response with empty or null final content must likewise be preserved and graded as incorrect/missing, not retried. A non-think response that unexpectedly contains reasoning must be preserved and flagged as a mode mismatch, not retried.

Only failures that prevent faithful persistence remain fatal: invalid JSON; missing `choices` or `message` structure; wrong field types that prevent faithful persistence; and credential, HTTP, or transport failures.

## Authorized resume boundary

Pilot attempt 1 remains excluded from the experimental dataset. Resume is authorized only for the 36 never-attempted calls. It must:

1. retain and verify the original manifest;
2. skip the 11 successfully persisted calls;
3. treat `P3:tanglish:injected_think` as consumed and never repeat it;
4. begin at the next planned call, `P4:en:clean`;
5. retain the original maximum of 48 actual network attempts; and
6. allow final integrity of 47 persisted successful responses plus one documented consumed deviation.

No retry is authorized. No scientific design choice changes. Implementation of this instrumentation and resume handling is deliberately deferred until after this deviation is frozen.
