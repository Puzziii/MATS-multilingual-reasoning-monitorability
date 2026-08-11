# Pilot Attempt 2 Incident Review

## Overview
- **Runner/Deviation Commit:** `bf37f9e612be184424e4d280d8f3c9ed16695ff7` (tag: `pilot-runner-v1.1`)
- **Artifact Hash:** `43268dfcfdd4761aa64718a69b77f17db9bce344f7daef14eba7d770d1c5a64c`
- **Exit Status:** 2
- **Safe Between-Call Boundary:** Yes

## Integrity Event Counts
- `manifest`: 1
- `request_started`: 12
- `response`: 11
- `failure`: 1
- `uncertain`: 0

## Execution State
- **Last Completed Call:** `P3:tanglish:injected_non_think`
- **Next Planned Call:** `P3:tanglish:injected_think`

## Root Cause Evidence
The 12th call (`P3:tanglish:injected_think`) was sent to the provider. The provider returned a 200 OK response, but the `reasoning_content` field was empty despite the request specifying `reasoning_effort="medium"`. 

The `SarvamProvider` parser enforces strict schema validation and requires `reasoning_content` to be a non-empty string when `reasoning_mode == "on"`. This deviation raised a `SarvamResponseError("Sarvam think response requires non-empty reasoning_content")`. The exception was safely caught by the runner, durably recorded as a `failure` event, and `PilotExecutionHalted` was raised. The main entry point caught this, blocked further execution, and exited with status 2. 

This behavior perfectly matches the designed fail-closed, guarded execution model.

## Minimal Potential Fix
No code fix is strictly necessary if we intend to strictly enforce the schema contract. The runner correctly identified a provider deviation, recorded it safely, and halted for manual review without corrupting data or leaking credentials.

If we want the pilot to tolerate occasional model failures to produce reasoning blocks, the minimal fix is to modify `parse_chat_completion` in `src/monitorability/providers/sarvam.py` to allow empty/null reasoning content, or to raise `RetryableProviderError` instead of `SarvamResponseError` so it can be retried (though retries are currently disabled in the frozen protocol).

*Note: No outcome analysis or reasoning inspection was performed during this diagnosis.*
