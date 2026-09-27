# Experiment v1_opus-5

Prompt v1, model claude-opus-5, 16 golden weeks, finished 2026-09-25T22:13:16+00:00.

| Metric | Value |
|---|---|
| Passed guards on first attempt | 6 of 16 |
| Passed after one retry | 5 |
| Fallback (not published) | 5 |
| Weeks with warnings | 16 |
| Total cost (API equivalent) | $3.901 |
| Average cost per week | $0.244 |
| Average time per week | 55.9 s |

| Week | Status | Attempts | Blocking failures | Warnings | Cost | Time |
|---|---|---|---|---|---|---|
| 2025-12-29 | verified | 1 | - | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.126 | 27.2 s |
| 2026-01-12 | verified | 1 | - | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.177 | 32.4 s |
| 2026-01-19 | verified | 1 | - | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.126 | 28.0 s |
| 2026-02-09 | verified_after_retry | 2 | no causes, recommendations, 'plan', or 'net revenue' | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.240 | 75.9 s |
| 2026-02-16 | verified | 1 | - | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.127 | 38.4 s |
| 2026-02-23 | verified | 1 | - | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.194 | 59.4 s |
| 2026-03-16 | verified_after_retry | 2 | numbers exist in the brief | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.251 | 54.3 s |
| 2026-03-23 | fallback | 2 | direction words match the data, numbers exist in the brief | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.264 | 59.7 s |
| 2026-03-30 | fallback | 2 | direction words match the data, no causes, recommendations, 'plan', or 'net revenue' | sentences at most 30 words and 4 numbers | $0.245 | 51.6 s |
| 2026-04-06 | verified_after_retry | 2 | no causes, recommendations, 'plan', or 'net revenue' | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.316 | 62.0 s |
| 2026-04-13 | fallback | 2 | direction words match the data, no causes, recommendations, 'plan', or 'net revenue' | sentences at most 30 words and 4 numbers | $0.353 | 72.0 s |
| 2026-04-20 | fallback | 2 | direction words match the data, numbers exist in the brief | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.360 | 78.9 s |
| 2026-05-11 | verified_after_retry | 2 | no causes, recommendations, 'plan', or 'net revenue' | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.441 | 104.8 s |
| 2026-06-01 | fallback | 2 | direction words match the data, no causes, recommendations, 'plan', or 'net revenue' | sentences at most 30 words and 4 numbers | $0.277 | 62.3 s |
| 2026-06-15 | verified_after_retry | 2 | numbers exist in the brief | sentences at most 30 words and 4 numbers | $0.270 | 57.5 s |
| 2026-06-22 | verified | 1 | - | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.134 | 30.7 s |
