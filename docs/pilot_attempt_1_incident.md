# Pilot attempt 1 incident record

**Status:** Preserved halted attempt; no valid experimental responses collected.

## Frozen references

- Frozen preregistration: `prereg-v1.0` / `196f5bcb3ba9589490b1429ca7558085e5682d14`
- Frozen execution protocol: `execution-protocol-v1.0` / `94f985bf45760d318073ed73bbd4c7892a7a5cff`
- Executable pilot runner: `pilot-runner-v1.0` / `f9c40bfd8f85cecd458989738ce103e9b947d321`

## Preserved artifact

- Path: `outputs/pilot_results.jsonl`
- SHA-256: `5901d31fee80bc3a811b4e2e63f6c579682ca48d0a0b4081819e23bff095dcd2`
- No prompts, data, research code, protocols, or raw artifact bytes were changed during diagnosis.

## Event counts

| Event type | Count |
|---|---:|
| manifest | 1 |
| request_started | 1 |
| response | 0 |
| failure | 1 |
| uncertain | 0 |

The manifest contains 48 unique planned call IDs. The only started call, `P3:ta:clean`, has one terminal failure event; there are no unmatched starts, duplicate successes, or valid experimental responses.

## Root-cause evidence

The sanitized terminal event records `RuntimeError` with the message `SARVAM_API_KEY is required for live Sarvam transport`.

The matching and only `raise RuntimeError` site is `src/monitorability/providers/sarvam.py:136`, inside `SarvamProvider._post_json`. The raising condition is a missing or empty `SARVAM_API_KEY` after live transport has been enabled but before the provider constructs headers, creates an HTTPS connection, sends a request, receives a status, or reads response bytes.

Call path:

`monitorability.pilot_run.main` → `run_fresh` → `_execute_remaining` → `SarvamProvider.generate` → `SarvamProvider._post_json` → local credential check at line 136.

The recorded attempt number was already `1` in the durable `request_started` event before `runtime.transport(call)` ran. A local mock reproduction with `SARVAM_API_KEY` removed and a fake connection factory produced the same `RuntimeError` with zero fake-connection invocations. Therefore:

- live authorization was passed by `pilot_run` with `SarvamProvider(allow_network=True, timeout=120.0)`;
- the generic provider guard blocks only when `allow_network` is false; its older schema-smoke wording does not restrict the explicitly authorized pilot caller;
- no HTTP response status or bytes were received;
- no socket or HTTPS request execution was reached; and
- `actual_provider_request_reached_network=false`.

No retry or resume was performed.

## Potential operational repair (not implemented)

The minimal potential repair is operational credential provisioning: ensure `SARVAM_API_KEY` is present in the live execution environment before a future authorized fresh attempt. No source, prompt, provider configuration, pilot data, research metric, or protocol content needs to change for that condition.

Before any new live attempt, a dated documented protocol deviation is required because the frozen execution protocol permits at most 48 network attempts and this preserved attempt already contains one terminal failure. The deviation should define the status of the halted call and any replacement execution plan before a request is made.

Required tests before any operational change would cover preflight credential availability without logging the credential, absence of connection-factory use when the credential is missing, and preservation of the 48-call/no-retry cap.
