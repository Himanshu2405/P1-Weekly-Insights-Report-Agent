# Judge calibration: v1_opus-5

Labelled by Claude (acting as reviewer, at Himanshu's request, 2026-09-26) after reading each week's full commentary, not only the quote. Himanshu can override any row.
Then we measure how often the judge agrees with you. Target: 85% or more before trusting it.

| # | Week | Item | Kind | Judge | Evidence | Judge's reason | Your verdict |
|---|---|---|---|---|---|---|---|
| 1 | 2025-12-29 | streak_as_good | must_not_say | pass | the direction matters even while the YoY comparison is favourable | The rising cancellation rate is consistently treated as a worsening risk, not an improvement. | pass |
| 2 | 2025-12-29 | headline_has_verdict | quality | fail | landed behind target in the first week of 2026, though both remain well ahead of last year. | Verdict is clear, but the headline omits the week's key issue, the three-week cancellation rise, and ends on positives. | pass (disagree) |
| 3 | 2025-12-29 | so_what_is_implication | quality | pass | With AOV no longer contributing, revenue growth depends on order volume, which fell this week. | Nearly all so_whats explain meaning for target, quarter, year or how to read another number. | fail (disagree) |
| 4 | 2026-01-12 | headline_has_verdict | quality | pass | Orders and revenue eased slightly and stayed well behind target | Headline gives a behind-target verdict and names the revenue shortfall as the issue. | pass |
| 5 | 2026-01-12 | no_speculation | quality | fail | The customer base is not expanding in line with the 48.4% year-on-year growth in orders. | Infers causes beyond the data, also claiming order growth "is not coming from new accounts". | fail |
| 6 | 2026-01-12 | watchouts_are_risks | quality | fail | The cancellation rate move of -2.1 pp is flagged as notable, above the 1.0 pp threshold. | An improvement in cancellations is good news, not a risk, yet listed as a watch-out. | fail |
| 7 | 2026-01-19 | headline_has_verdict | quality | fail | Orders jumped to 745, the highest in eight weeks, but revenue slipped slightly and the quarter remains behind target at 85.5%. | Headline gives quarter attainment, not the week's verdict, and omits the big cancellation jump. | fail |
| 8 | 2026-02-09 | watchouts_are_risks | quality | fail | The cancellation rate fell 1.3 pp to 14.8%, a notable move rated good. | A good-news improvement is listed as a watch-out, which is not a risk or caveat. | fail |
| 9 | 2026-02-16 | strong_week | must_not_say | fail | Orders jumped 13.4% to 789, a strong week, but revenue stayed behind target | The headline explicitly calls it a strong week, which the key forbids. | fail |
| 10 | 2026-02-16 | watchouts_are_risks | quality | pass | Quarter-to-date revenue is $415,309 against a target of $473,740, a shortfall of $58,431 | All three watchouts are risks or maturity caveats, and the cancellation risk is included. | pass |
| 11 | 2026-02-23 | quarter_on_track | must_not_say | pass | One strong week has not closed the quarter gap; $296,595 is still needed | Commentary consistently presents quarter and year as behind target, never implying either is on track. | pass |
| 12 | 2026-04-06 | headline_has_verdict | quality | pass | Strong week: orders and revenue both above target and above their 8-week range, but the year to date remains behind target. | States ahead of target and names the year-to-date shortfall as the key issue. | pass |
| 13 | 2026-04-13 | so_what_is_implication | quality | fail | so_what: "The week came in below the 8-week average revenue of $60,216." | Several so_whats merely restate the fact or add another number without saying what it means. | fail |
| 14 | 2026-04-20 | behind_target | must_say | pass | Weekly orders hit 91.4% of target (840 vs 919) and weekly revenue 90.7% ($61,965 vs $68,310); both are behind. | Both attainment figures match the key exactly and the week is called behind target. | pass |
| 15 | 2026-05-11 | wrong_return_week | must_not_say | pass | Return behaviour for the reporting week of 11 May is not yet known, so this measure lags the rest of the report by two weeks. | Commentary consistently attributes the return rate to the mature 27 Apr week, not 11 May. | pass |
| 16 | 2026-05-11 | headline_has_verdict | quality | fail | Orders fell 3.6% to 914 while revenue rose 3.3% to $68,099; both beat the weekly target, but the quarter and year stay behind. | Verdict is present but the headline omits the week's key issue, the three-week return rate rise. | pass (disagree) |
| 17 | 2026-06-01 | dramatized | must_not_say | pass | These gains cushioned the week, holding the total order decline to 2.8% rather than a steeper fall. | Tone stays measured and all three watch-outs are genuine caveats or trends, not invented drama. | pass |
| 18 | 2026-06-01 | behind_target | must_say | pass | Orders reached 93.6% of the weekly target (gap of 64 orders) and revenue 90.2% (gap of $7,380), both behind. | Both attainment figures and the 8.7% revenue decline are stated and match the key. | pass |
| 19 | 2026-06-01 | no_speculation | quality | fail | Customer acquisition is shrinking against last year while orders grew 70.3%, so growth is leaning on existing customers. | Concludes growth leans on existing customers, an interpretation not readable from the stated facts. | fail |
| 20 | 2026-06-22 | watchouts_are_risks | quality | fail | this is a meaningful improvement in order quality | The cancellation-rate watch-out presents good news as a risk rather than a risk or caveat. | fail |

## Agreement: 17 of 20 (85%)

| # | Judge | Reviewer | Why the reviewer disagrees |
|---|---|---|---|
| 2 | fail | pass | Headline gives the verdict (behind target) and the week's main issue (the target miss). The judge demanded a specific issue (the cancellation streak), which the rule does not require. |
| 3 | pass | fail | At least 4 so-whats only restate facts or definitions (e.g. "next week's targets step up to 810 orders", "Search holds 71.5% of orders"); the rule says 2 or more is a fail. The judge was too lenient. |
| 16 | fail | pass | Headline says the week beat target and names the quarter and year still behind, a valid main issue. Again the judge demanded one specific issue (the return-rate streak). |

## What this means

- 85% is exactly at the trust threshold. The disagreements are not random: they come from two vague rules.
- **headline_has_verdict** (2 of 3): the judge reads "names the single most important issue" as "names the one issue I think matters most". Fix: accept any of the target gap, the quarter/year position, or a flagged risk.
- **so_what_is_implication** (1 of 3): "nearly every" is fuzzy, so the judge does not count. Fix: tell it to count restating so-whats and fail at 2 or more, with examples.
- Caveat: these labels come from Claude, not a human, so this is a consistency check, not ground truth. A human spot-check of rows 2, 3 and 16 would settle the rule wording.
