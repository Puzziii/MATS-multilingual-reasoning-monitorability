# Phase 5D Follow-up Attempt 1 Incident Record

**Timestamp:** 2026-08-13T13:27:48Z (Execution halt) / 2026-08-13T13:39:33Z (Record creation)
**Runner Tag:** `followup-runner-v1.0` (commit `5cd037b0b9f213c3c6fe2d0e1b966fcbc03670f9`)

## Frozen Input Hashes
- **Dataset (`data/followup_scenarios.jsonl`)**: `5e36606a6919d67ea837af3a2402ad289e151d7d018d320af440ec3b94849e19`
- **Protocol (`docs/followup_protocol_v1.0.md`)**: `1bd7ad09f1fcfefe470dc1b5545d188c6142b484f187390767def930f15a9082`

## Incident Details
- **Network attempts:** Exactly 1
- **Consumed call:** `P7:ta:clean`
- **Failure classification:** HTTP 403. The credential preflight confirmed `SARVAM_API_KEY` was non-empty. The HTTP 403 indicates the request reached Sarvam but authorization was refused.
- **Responses:** No response received.
- **Retry/Resume:** No retries or resume attempts were made.
- **Credential leakage:** No credential leakage was found in the artifact.

## Preservation and Remediation
- The partial artifact has been preserved byte-for-byte as `outputs/followup_results_attempt1_403.jsonl` (SHA-256: `16f31be5bf7fe9d9f58ab3a0321603f06e38b4323bad6860f757e93566e4a4b4`).
- `outputs/followup_results.jsonl` is absent after preservation.
- The consumed call `P7:ta:clean` must **not** be attempted again in any subsequent resumption.
