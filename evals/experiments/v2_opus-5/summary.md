# Experiment v2_opus-5

Prompt v2, model claude-opus-5, 16 golden weeks, finished 2026-09-27T02:08:21+00:00.

| Metric | Value |
|---|---|
| Passed guards on first attempt | 12 of 16 |
| Passed after one retry | 1 |
| Fallback (not published) | 3 |
| Weeks with warnings | 12 |
| Total cost (API equivalent) | $3.634 |
| Average cost per week | $0.227 |
| Average time per week | 64.9 s |

| Week | Status | Attempts | Blocking failures | Warnings | Cost | Time |
|---|---|---|---|---|---|---|
| 2025-12-29 | fallback | 2 | ahead/behind target matches the data | sentences at most 30 words and 4 numbers | $0.396 | 98.6 s |
| 2026-01-12 | fallback | 2 | ahead/behind target matches the data, numbers exist in the brief | sentences at most 30 words and 4 numbers, each slot only covers its allowed KPIs | $0.389 | 124.2 s |
| 2026-01-19 | verified | 1 | - | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.172 | 33.5 s |
| 2026-02-09 | fallback | 2 | ahead/behind target matches the data, numbers exist in the brief | each slot only covers its allowed KPIs, no fact repeated across 3+ slots | $0.380 | 118.4 s |
| 2026-02-16 | verified | 1 | - | no fact repeated across 3+ slots | $0.203 | 60.9 s |
| 2026-02-23 | verified | 1 | - | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.179 | 54.9 s |
| 2026-03-16 | verified | 1 | - | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.111 | 21.2 s |
| 2026-03-23 | verified | 1 | - | - | $0.215 | 67.9 s |
| 2026-03-30 | verified | 1 | - | - | $0.224 | 76.8 s |
| 2026-04-06 | verified | 1 | - | - | $0.258 | 93.6 s |
| 2026-04-13 | verified | 1 | - | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.111 | 21.0 s |
| 2026-04-20 | verified | 1 | - | - | $0.111 | 20.4 s |
| 2026-05-11 | verified | 1 | - | sentences at most 30 words and 4 numbers, no fact repeated across 3+ slots | $0.171 | 35.3 s |
| 2026-06-01 | verified_after_retry | 2 | numbers exist in the brief | sentences at most 30 words and 4 numbers | $0.337 | 96.2 s |
| 2026-06-15 | verified | 1 | - | sentences at most 30 words and 4 numbers, each slot only covers its allowed KPIs | $0.178 | 52.1 s |
| 2026-06-22 | verified | 1 | - | each slot only covers its allowed KPIs | $0.200 | 63.0 s |
