# Final manual QA record

Date: 2026-08-13

- The deterministic pre-review grading-audit file had SHA-256 `50e6c795fc0bcd1c99e4d469884487b3bc29f3b5a1691c726bd59335e0918a2e`.
- All 12 grading-audit rows were manually checked against the raw output, normalized output, condition-specific target, and automatic label.
- Manual judgments agreed with automatic grading for 12 of 12 rows; there were zero disagreements.
- The deterministic pre-review qualitative-example file had SHA-256 `6359e7ffc8980d370776311e52bfb90cbbc50e73d9ad79e5af82a4ea170bfdb2`.
- All six fixed-seed qualitative examples were manually checked for faithful copying, completeness, misleading presentation, and credential or secret exposure.
- The six examples were not replaced or cherry-picked after review; only their existing review-status metadata was changed from pending to reviewed.
