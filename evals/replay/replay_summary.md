# Held-out production replay (prompt in production, Jul 6 to Aug 3)

| Week | Status | Attempts | So-whats real implications | Quality fails | Warnings | Cost (report + judge) |
|---|---|---|---|---|---|---|
| 2026-07-06 | verified | 1 | 94% | no_speculation | 0 | $0.349 |
| 2026-07-13 | verified_after_retry | 2 | 88% | - | 2 | $0.452 |
| 2026-07-20 | verified | 1 | 88% | - | 2 | $0.240 |
| 2026-07-27 | verified | 1 | 69% | no_speculation | 0 | $0.313 |
| 2026-08-03 | verified_after_retry | 2 | 71% | - | 1 | $0.575 |

## Findings (held-out: these weeks were never used to tune the prompt, guards, or judge)

- **Published every week**: 5 of 5, no fallbacks. Both retries (Jul 13, Aug 3) were guard false alarms from new wording ("order quality is weaker", "the gain came despite LATAM"). With the fixed guards, all 5 weeks pass on the first attempt (re-checked offline).
- **So-whats**: 94%, 88%, 88%, 69%, 71% real implications (82% on average) vs 88% on the golden set. A drop on unseen weeks: prompt v2 is slightly tuned to the golden weeks. Main weak pattern: so-whats that describe a contrast between two KPIs without saying what it means.
- **Speculation**: 2 flags. Jul 6: an ambiguous comparison (true YoY, false WoW, basis not stated). Jul 27: a true claim the judge could not verify because it only sees the commentary, not the brief.
- **Guards**: 3 new false alarms found on held-out weeks and fixed (order quality vs order volume, contrast sentences, and a regression the first fix caused on golden week 2026-04-20). Re-checking every saved run after each guard change caught that regression before it shipped.
- **Cost**: report + judge $0.24 to $0.58 a week; retries caused by false alarms roughly doubled the cost of those weeks.

## Backlog from the replay
1. Prompt v3: say WoW or YoY when comparing two KPIs; a contrast between two KPIs needs an implication, not a description.
2. Judge v4: give the judge the brief so it can verify factual claims.
3. Guards: keep re-checking all saved runs (golden + replay) after every change.
