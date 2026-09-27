# Experiment heldout_v3_sonnet-5

Prompt v3, model claude-sonnet-5, 10 heldout weeks, finished 2026-09-27T19:07:59+00:00.

| Metric | Value |
|---|---|
| Passed guards on first attempt | 8 of 10 |
| Passed after one retry | 2 |
| Fallback (not published) | 0 |
| Weeks with warnings | 7 |
| Total cost (API equivalent) | $1.652 |
| Average cost per week | $0.165 |
| Average time per week | 119.6 s |

| Week | Status | Attempts | Blocking failures | Warnings | Cost | Time |
|---|---|---|---|---|---|---|
| 2026-01-05 | verified | 1 | - | - | $0.187 | 128.1 s |
| 2026-01-26 | verified | 1 | - | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.109 | 77.2 s |
| 2026-02-02 | verified_after_retry | 2 | no causes, recommendations, 'plan', or 'net revenue' | no fact repeated across 3+ slots | $0.246 | 169.5 s |
| 2026-03-02 | verified | 1 | - | sentences at most 30 words and 4 numbers, each slot only covers its allowed KPIs, no fact repeated across 3+ slots | $0.081 | 48.8 s |
| 2026-03-09 | verified | 1 | - | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.183 | 145.1 s |
| 2026-04-27 | verified | 1 | - | - | $0.201 | 160.5 s |
| 2026-05-04 | verified_after_retry | 2 | ahead/behind target matches the data | no fact repeated across 3+ slots | $0.184 | 120.7 s |
| 2026-05-18 | verified | 1 | - | - | $0.170 | 131.0 s |
| 2026-05-25 | verified | 1 | - | no fact repeated across 3+ slots | $0.132 | 95.5 s |
| 2026-06-08 | verified | 1 | - | no fact repeated across 3+ slots | $0.159 | 119.9 s |
