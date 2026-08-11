# Pilot attempt 2 operational deviation

**Status:** Authorized pre-data operational deviation for a fresh attempt; no scientific design change.

## Preserved attempt 1

- Preservation commit: `9cf63133048c6c89d7a9b02221897d969c637614`
- Preservation tag: `pilot-attempt-1-failed`
- Preserved artifact: `outputs/pilot_results_attempt1_failed.jsonl`
- Artifact SHA-256: `5901d31fee80bc3a811b4e2e63f6c579682ca48d0a0b4081819e23bff095dcd2`

Attempt 1 halted with the sanitized exception `RuntimeError: SARVAM_API_KEY is required for live Sarvam transport`. The source was `src/monitorability/providers/sarvam.py:136` in `SarvamProvider._post_json`, at the missing-or-empty credential check.

The provider transport method was entered with live authorization, but HTTPS/socket transport was not reached: the credential check occurred before connection creation, request transmission, response status receipt, or response-byte read. No API request, response, completion, or experimental result occurred. The internal `attempt: 1` event represented a local provider invocation, not a network request.

Attempt 1 is excluded from the experimental dataset. Its artifact is retained unchanged and must not be resumed.

## Authorized fresh attempt 2

A fresh attempt is authorized instead of resume. It retains the original frozen limit of exactly 48 unique calls and 48 actual network attempts, with no retries. No prompt, dataset, model parameter, ordering, hypothesis, metric, grading rule, preregistration, or frozen execution-protocol choice changes.

The only code change is moving non-empty `SARVAM_API_KEY` validation after the existing frozen hash/tag/worktree/data preflight checks and before any output artifact, manifest, request-started event, attempt counter, provider construction, or transport. The provider's existing local credential check remains as defence in depth.
