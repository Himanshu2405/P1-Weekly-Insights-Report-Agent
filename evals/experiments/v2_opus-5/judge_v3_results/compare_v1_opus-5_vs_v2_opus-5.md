# v1_opus-5 vs v2_opus-5

Same 16 golden weeks, same answer keys, same judge (judge_v3), guards re-checked with today's rules.

| Measure | v1_opus-5 | v2_opus-5 |
|---|---|---|
| **Quality (LLM judge)** | | |
| Must-say items conveyed | 100% (35/35) | 100% (35/35) |
| Must-not-say items avoided | 94% (17/18) | 100% (18/18) ✅ |
| So-whats that are real implications | 68% (186/272) | 88% (238/270) ✅ |
| Weeks passing: headline has verdict | 94% (15/16) | 100% (16/16) ✅ |
| Weeks passing: watchouts are risks | 75% (12/16) | 100% (16/16) ✅ |
| Weeks passing: no speculation | 50% (8/16) | 94% (15/16) ✅ |
| **Safety (guards, today's rules)** | | |
| Passed on first attempt | 12 of 16 | 16 of 16 ✅ |
| Passed after one retry | 4 | 0 ✅ |
| Fallback (not published) | 0 | 0 |
| Weeks with warnings | 16 | 11 ✅ |
| Warning count (density, repetition, ...) | 108 | 22 ✅ |
| **Cost (API equivalent)** | | |
| Average cost of a first attempt | $0.151 | $0.188 ⚠️ |
| Judge cost for 16 weeks | $1.952 | $1.777 ✅ |

## So-whats by week (share that are real implications)

| Week | v1_opus-5 | v2_opus-5 |
|---|---|---|
| 2025-12-29 | 71% (12/17) | 76% (13/17) ✅ |
| 2026-01-12 | 82% (14/17) | 94% (16/17) ✅ |
| 2026-01-19 | 65% (11/17) | 88% (15/17) ✅ |
| 2026-02-09 | 35% (6/17) | 82% (14/17) ✅ |
| 2026-02-16 | 59% (10/17) | 88% (15/17) ✅ |
| 2026-02-23 | 76% (13/17) | 94% (15/16) ✅ |
| 2026-03-16 | 59% (10/17) | 88% (15/17) ✅ |
| 2026-03-23 | 59% (10/17) | 94% (16/17) ✅ |
| 2026-03-30 | 76% (13/17) | 100% (17/17) ✅ |
| 2026-04-06 | 71% (12/17) | 75% (12/16) ✅ |
| 2026-04-13 | 53% (9/17) | 88% (15/17) ✅ |
| 2026-04-20 | 71% (12/17) | 94% (16/17) ✅ |
| 2026-05-11 | 82% (14/17) | 65% (11/17) ⚠️ |
| 2026-06-01 | 76% (13/17) | 94% (16/17) ✅ |
| 2026-06-15 | 82% (14/17) | 88% (15/17) ✅ |
| 2026-06-22 | 76% (13/17) | 100% (17/17) ✅ |

## Judge failures by week

| Week | v1_opus-5 | v2_opus-5 |
|---|---|---|
| 2026-01-12 | watchouts_are_risks, no_speculation | - |
| 2026-01-19 | headline_has_verdict, no_speculation | - |
| 2026-02-09 | watchouts_are_risks | - |
| 2026-02-16 | strong_week, no_speculation | - |
| 2026-02-23 | no_speculation | - |
| 2026-03-30 | no_speculation | - |
| 2026-06-01 | no_speculation | - |
| 2026-06-15 | watchouts_are_risks, no_speculation | no_speculation |
| 2026-06-22 | watchouts_are_risks, no_speculation | - |

Run totals as recorded: v1_opus-5 $3.901, v2_opus-5 $3.634 (v1_opus-5 ran with older, stricter guards, so its recorded total includes avoidable retries).
