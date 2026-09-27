# v2_opus-5 vs v3_sonnet-5

Same weeks, same answer keys (if any), same judge (judge_v4), guards re-checked with today's rules.

| Measure | v2_opus-5 | v3_sonnet-5 |
|---|---|---|
| **Quality (LLM judge)** | | |
| Must-say items conveyed | 100% (35/35) | 100% (35/35) |
| Must-not-say items avoided | 100% (18/18) | 100% (18/18) |
| So-whats that are real implications | 96% (260/270) | 95% (250/264) ⚠️ |
| Weeks passing: headline has verdict | 100% (16/16) | 100% (16/16) |
| Weeks passing: watchouts are risks | 100% (16/16) | 100% (16/16) |
| Weeks passing: no speculation | 81% (13/16) | 69% (11/16) ⚠️ |
| **Safety (guards, today's rules)** | | |
| Passed on first attempt | 16 of 16 | 13 of 16 ⚠️ |
| Passed after one retry | 0 | 3 ⚠️ |
| Fallback (not published) | 0 | 0 |
| Weeks with warnings | 11 | 10 ✅ |
| Warning count (density, repetition, ...) | 22 | 21 ✅ |
| **Cost (API equivalent)** | | |
| Average cost of a first attempt | $0.188 | $0.187 ✅ |
| Judge cost | $1.373 | $1.364 ✅ |

## So-whats by week (share that are real implications)

| Week | v2_opus-5 | v3_sonnet-5 |
|---|---|---|
| 2025-12-29 | 88% (15/17) | 88% (15/17) |
| 2026-01-12 | 100% (17/17) | 100% (16/16) |
| 2026-01-19 | 94% (16/17) | 87% (13/15) ⚠️ |
| 2026-02-09 | 100% (17/17) | 94% (16/17) ⚠️ |
| 2026-02-16 | 88% (15/17) | 94% (15/16) ✅ |
| 2026-02-23 | 88% (14/16) | 100% (17/17) ✅ |
| 2026-03-16 | 88% (15/17) | 94% (16/17) ✅ |
| 2026-03-23 | 100% (17/17) | 100% (17/17) |
| 2026-03-30 | 100% (17/17) | 100% (17/17) |
| 2026-04-06 | 100% (16/16) | 100% (16/16) |
| 2026-04-13 | 100% (17/17) | 94% (16/17) ⚠️ |
| 2026-04-20 | 100% (17/17) | 93% (14/15) ⚠️ |
| 2026-05-11 | 94% (16/17) | 88% (15/17) ⚠️ |
| 2026-06-01 | 100% (17/17) | 100% (17/17) |
| 2026-06-15 | 100% (17/17) | 81% (13/16) ⚠️ |
| 2026-06-22 | 100% (17/17) | 100% (17/17) |

## Judge failures by week

| Week | v2_opus-5 | v3_sonnet-5 |
|---|---|---|
| 2026-02-09 | - | no_speculation |
| 2026-02-16 | - | no_speculation |
| 2026-03-16 | - | no_speculation |
| 2026-03-23 | no_speculation | - |
| 2026-03-30 | - | no_speculation |
| 2026-04-06 | no_speculation | - |
| 2026-04-20 | - | no_speculation |
| 2026-06-15 | no_speculation | - |

Run totals as recorded: v2_opus-5 $3.634, v3_sonnet-5 $3.247 (v2_opus-5 ran with older, stricter guards, so its recorded total includes avoidable retries).
