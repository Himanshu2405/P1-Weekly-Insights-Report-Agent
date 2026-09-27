# Guard review: golden run v1 (prompt v1, Claude Opus 5, 16 weeks, 2026-09-25)

## What happened
The first golden run (`summary.md`) looked bad: 6 of 16 weeks passed on the first attempt, 5 passed after a retry, 5 fell back. Before blaming the prompt, every one of the 15 blocked attempts was read by hand.

## Every block, classified

| Week | Attempt | Guard | Sentence (short) | Verdict |
|---|---|---|---|---|
| 2026-02-09 | 1 | causal claim | "Revenue fell faster than orders ... as a result of the lower value per order" | False alarm: arithmetic (revenue = orders x AOV), not a business cause |
| 2026-03-16 | 1 | numbers | "the 2.1 pp rise across the streak" | **Real**: Claude calculated 16.4 - 14.3 |
| 2026-03-23 | 1 | numbers | "revenue 9.8% short of the weekly target" | **Real**: Claude calculated 100 - 90.2 |
| 2026-03-23 | 2 | direction | "The week fell $6,650 short of target even though orders finished ahead" | False alarm: "fell short of target" is a target gap, not a direction |
| 2026-03-30 | 1 | causal claim | "reported for the mature week of 16 Mar because the two most recent weeks are not yet mature" | False alarm: explains the data |
| 2026-03-30 | 2 | direction | "North America's gain is what kept the overall order decline to just 4 orders" | False alarm: segment up, total down, both true |
| 2026-04-06 | 1 | causal claim | "because the two most recent weeks are not yet mature" | False alarm: explains the data |
| 2026-04-13 | 1 | causal claim | "because the two most recent weeks are not yet mature" | False alarm: explains the data |
| 2026-04-13 | 2 | direction | "The two largest regions held up, so the shortfall sits with EMEA and LATAM" | False alarm: "held up" is an idiom |
| 2026-04-20 | 1 | numbers | "beat last year by over 80%" | **Real**: the brief says 81.0%; Claude rounded |
| 2026-04-20 | 2 | direction | "The largest region pulled the total down and was offset by gains elsewhere" | False alarm: true (APAC -63, total +6) |
| 2026-05-11 | 1 | causal claim | "because the two most recent weeks are not yet mature" | False alarm: explains the data |
| 2026-06-01 | 1 | causal claim | "which matters because gross revenue does not subtract returns" | False alarm: explains a definition |
| 2026-06-01 | 2 | direction | "Only EMEA grew faster than the 75% growth the targets assume" | False alarm: a YoY statement checked against the WoW change |
| 2026-06-15 | 1 | numbers | "13.6% ahead of the weekly target" | **Real**: Claude calculated 113.6 - 100 |

**Guard precision: 4 of 15 blocks were real (27%).** All 5 fallbacks and most retries were caused by false alarms; roughly 40% of the run's $3.90 went on retries that should not have happened.

## Fixes (each sentence kept as a regression test in `tests/test_guards.py`)
1. Causal check targets business causes only ("because of", "due to", "thanks to", "as a result of a campaign/price/..."). Bare "because" explaining data or definitions is allowed.
2. Direction check only judges unambiguous sentences: one KPI or one named segment, no target-gap wording ("short of target"), no total-vs-segment mixing, no unnamed segments ("the largest region"), idioms removed ("held up", "kept ... to"). Segment sentences about last year or target growth are checked against the YoY change, not WoW. Mixed sentences are left to the LLM judge.

## Result: same 16 saved outputs, re-checked offline (no new calls)

| | Before fix | After fix |
|---|---|---|
| Passed on first attempt | 6 | 12 |
| Passed after one retry | 5 | 4 |
| Fallback | 5 | 0 |
| Blocks that were real | 4 of 15 (27%) | 4 of 4 (100%) |

## What is left for prompt v2
- The only real blocking failure type in 16 weeks: **Claude calculating or rounding numbers** (4 weeks). Prompt v2 needs a sharper rule with examples ("write 90.2% of target, never 9.8% short of target").
- Quality issues (repetition, density, weak so-whats, priorities) are warnings or judge territory; the judge scores them next against the answer keys.

## Caveat
The guard fixes were designed on these same 16 weeks, so 100% precision here is optimistic. The held-out production replay (Jul 6 to Aug 3) is the honest test of the fixed guards.
