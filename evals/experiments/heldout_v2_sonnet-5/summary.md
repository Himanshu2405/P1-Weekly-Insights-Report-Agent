# Experiment heldout_v2_sonnet-5

Prompt v2, model claude-sonnet-5, 10 heldout weeks, finished 2026-09-27T18:33:05+00:00.

| Metric | Value |
|---|---|
| Passed guards on first attempt | 8 of 10 |
| Passed after one retry | 1 |
| Fallback (not published) | 1 |
| Weeks with warnings | 6 |
| Total cost (API equivalent) | $1.751 |
| Average cost per week | $0.175 |
| Average time per week | 125.7 s |

| Week | Status | Attempts | Blocking failures | Warnings | Cost | Time |
|---|---|---|---|---|---|---|
| 2026-01-05 | verified | 1 | - | - | $0.232 | 132.8 s |
| 2026-01-26 | verified | 1 | - | no fact repeated across 3+ slots | $0.142 | 102.0 s |
| 2026-02-02 | verified | 1 | - | - | $0.169 | 139.7 s |
| 2026-03-02 | verified | 1 | - | no fact repeated across 3+ slots | $0.090 | 58.6 s |
| 2026-03-09 | verified | 1 | - | no fact repeated across 3+ slots | $0.136 | 102.9 s |
| 2026-04-27 | verified | 1 | - | - | $0.175 | 143.1 s |
| 2026-05-04 | verified | 1 | - | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.074 | 41.1 s |
| 2026-05-18 | verified | 1 | - | - | $0.146 | 129.3 s |
| 2026-05-25 | verified_after_retry | 2 | no causes, recommendations, 'plan', or 'net revenue' | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.355 | 246.9 s |
| 2026-06-08 | fallback | 2 | direction words match the data, no causes, recommendations, 'plan', or 'net revenue' | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.230 | 160.3 s |
