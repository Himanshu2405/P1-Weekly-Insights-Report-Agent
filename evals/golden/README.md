# Golden set (16 weeks)

The fixed "exam" every prompt version is scored on. Each week is a **frozen data brief** (in `briefs/`, generated 2026-09-25, brief v1.3). The numbers never change, even though the source data is regenerated daily, so every prompt version is tested on exactly the same input.

- Chosen from the 26 weeks of Jan to Jun 2026 to cover as many different situations as possible.
- Jul 6 to Aug 3 are **held out** for the production replay (loop 2), so the prompt is never tuned on them.
- Answer keys (what a good commentary must and must not say per week): `answer_keys.yaml` (v1, approved 2026-09-25).

| # | Week of | Situation | Why it is in the set |
|---|---|---|---|
| 1 | 2025-12-29 | First week of FY2026, behind target (87.5%), cancellation streak flag | Year start; a streak must reach the watch-outs |
| 2 | 2026-01-12 | Deepest miss of the year (74.9% of target) | A clearly bad week must be called bad, not softened |
| 3 | 2026-01-19 | Orders up 9.9% WoW but behind target; cancellations +5.4 pp | Trap: "up WoW" is not "on target"; a big bad move in a rate |
| 4 | 2026-02-09 | Orders down 6.1% WoW and behind target | A plain bad week |
| 5 | 2026-02-16 | Orders up 13.4% WoW (notable) yet behind target | Trap: strong growth week that still misses |
| 6 | 2026-02-23 | First week ahead of target (108.7%) while the quarter is behind | Trap: good week, bad quarter |
| 7 | 2026-03-16 | Ahead of target, Q1 behind with 1 week left, cancellation streak flag, 5 notable KPIs | Eventful week; priorities and repetition are tested |
| 8 | 2026-03-23 | Last week of Q1: orders ahead (102.9%) but revenue behind (90.2%); Q1 closes behind (92.4%) | Trap: mixed week, both sides must be said |
| 9 | 2026-03-30 | Quiet week: 0 notable KPIs, 100.4% of target, first week of Q2 | Trap: do not dramatize small changes |
| 10 | 2026-04-06 | Strong week (116.6% of target) | A clearly good week must be called good |
| 11 | 2026-04-13 | Behind target for the week, but the quarter is ahead; cancellation streak | Trap: bad week, good quarter |
| 12 | 2026-04-20 | Behind target, quiet except a cancellation streak | The one real risk must not be missed |
| 13 | 2026-05-11 | Ahead of target, 14-Day Return Rate streak flag | Return rate: name the mature week, flag the streak |
| 14 | 2026-06-01 | Quiet week (0 notable KPIs), behind target | Quiet and behind: state it plainly, no drama |
| 15 | 2026-06-15 | Orders down 1.5% WoW but ahead of target, quarter ahead | Trap: "down WoW" is not "behind target" |
| 16 | 2026-06-22 | Last week of Q2, ahead of target | Quarter end on a good note |

Not included on purpose: the Sep 14 data-break week (outside the report window; anomaly handling is covered by guard tests with synthetic data).
