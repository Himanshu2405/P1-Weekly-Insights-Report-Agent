# Tech Spec: Weekly Business Insights Report with Reliable AI Commentary

| Field | Value |
|---|---|
| Version | v1.0 (2026-09-24) |
| PRD (what and why) | [PRD.md](PRD.md) |
| Plan (when and learning map) | [PLAN.md](PLAN.md) |
| LLM runtime context | [business_context.md](business_context.md) |
| Decisions log | [P1_Decisions_Log.md](P1_Decisions_Log.md) |

This document describes HOW the system works. Sections marked "TBD" are designed when we reach that phase.

## 1. Design principles

- Numbers come from code, never from the LLM. The LLM only narrates the data brief, and guards check it against the brief.
- No RAG: the whole context (business context, data brief with 8 weeks of history, targets) fits in one prompt. Retrieval would add cost and failure modes for no gain.
- Fail safe, not silent: bad input stops the run; bad LLM output falls back to a template and raises an alert.
- Everything reproducible: prompts versioned, targets frozen, eval runs on frozen briefs.

## 2. Data

- Source: BigQuery public dataset `bigquery-public-data.thelook_ecommerce`, queried in place (no snapshot), billed to personal project `master-chariot-413216`.
- Tables used: `orders`, `order_items`, `users`. Not used in v1: `products`, `events`, `inventory_items`, `distribution_centers`.
- History: orders from 2019-01-10 to today (rolling, rewritten daily). Report uses the last 52 completed weeks.
- Known quirks (each one is a deliberate test case): recent volume spike (Sep 2026), partial current week, return maturity, country names in local language ("España", "Deutschland").
- No employer data, SQL, prompts, or names.

## 3. KPI Spec v1 (LOCKED 2026-09-24)

### Reporting conventions
- Reporting week: Monday 00:00 to Sunday 23:59:59 UTC. Report always covers the latest COMPLETED week, computed in code, never hard-coded.
- Comparisons per KPI: week over week (WoW), year over year (YoY, same ISO week last year), vs target (where a target exists), and a 52-week trend.
- Future targets (through Dec 2026) are shown on plan charts and as "next week's target" and "full-quarter plan".
- Money in USD, rounded to whole dollars in prose, 2 decimals in tables. Rates as % with 1 decimal. Changes in percentage points (pp) for rates, % for counts and money.

### Core KPIs

| # | KPI name | Definition / formula | Source | Good direction | Reliability trap it tests |
|---|---|---|---|---|---|
| 1 | Weekly Orders Placed | Count of distinct `order_id` with `created_at` in the week, all statuses | `orders` | Up | Baseline number grounding: every quoted number must match the brief |
| 2 | Weekly Gross Revenue (excl. cancelled) | Sum of `order_items.sale_price` (item status != Cancelled) for orders PLACED in the week (week of `orders.created_at`, not the item timestamp; 26,814 items fall in a different week than their order). Returns NOT subtracted (tracked by KPI 5) | `order_items` | Up | Definition fidelity: LLM must not call it "net" or imply returns are removed |
| 3 | Weekly Average Order Value (AOV) | KPI 2 / count of non-cancelled orders in the week | `orders`, `order_items` | Up | Ratio trap: LLM must quote code-computed AOV, never derive its own |
| 4 | Weekly Order Cancellation Rate | Cancelled orders / Weekly Orders Placed | `orders` | Down | Direction trap: an increase is bad news, wording must match sign and polarity |
| 5 | 14-Day Return Rate | Orders with `orders.returned_at` within 14 days of `orders.created_at` / orders placed in the week. Customer return behavior, not inventory. Returns are whole-order in this data (no partial returns; returned_at always after delivered_at). Only reported for MATURE weeks (every order has had 14 full days); on a Monday run this is the week ending 2 weeks before the reporting week. Incomplete weeks are never reported | `orders` | Down | Maturity trap: customers return up to ~11 days after ordering (median 5.5, p95 8.6). Brief must label which week this KPI refers to; LLM must not mix it with the reporting week |
| 6 | Weekly New Customer Signups | Count of `users` with `created_at` in the week | `users` | Up | Second source table; tests cross-table consistency and "growth" claims |

### Target KPIs (simulated plan)

| # | KPI name | Definition / formula | Good direction | Reliability trap it tests |
|---|---|---|---|---|
| 7 | Weekly Orders vs Target (attainment %) | KPI 1 / weekly orders target x 100. Also report the gap (actual minus target) | Up | "Above/below target" wording must match attainment vs 100% |
| 8 | Weekly Gross Revenue vs Target (attainment %) | KPI 2 / weekly revenue target x 100, plus the gap in USD | Up | Same as above, plus mixing up WoW growth with target attainment |
| 9 | Quarter-to-Date (QTD) Gross Revenue vs Target | Sum of KPI 2 from quarter start through reporting week / sum of weekly targets for the same weeks | Up | Cumulative vs weekly confusion: a good week can still leave the quarter behind plan |

### How targets are simulated (the "plan")
- Real companies get targets from Finance once per year. We mimic that with a frozen plan file, not a live calculation.
- Method: weekly target = same ISO week last year actual x (1 + planned YoY growth). Using last year's same week keeps seasonality.
- Planned YoY growth: 75% for 2026 (config value). Rationale: actual growth was ~50% early 2026 and ~100% by August, so the plan produces a realistic story (behind plan in H1, ahead in H2, far ahead during the September spike).
- Generated once by a script into `targets/weekly_targets_2026.csv` (columns: week_start, orders_target, revenue_target, target_version). Never regenerated from live data.
- Data-quality gate: every reporting week must have a target row, else the run fails.

### Cuts (applied to KPIs 1 and 2 only)
- Traffic source: Search, Organic, Facebook, Email, Display (from `users.traffic_source` of the ordering user).
- Region (from `users.country`):
  - APAC: China, South Korea, Japan, Australia (~44% of users)
  - North America: United States (~23%)
  - EMEA: France, United Kingdom, Germany, Spain, Belgium, Poland, Austria, plus "España" and "Deutschland" (~19%)
  - LATAM: Brasil, Colombia (~14.5%)
- Data-quality gate: any unmapped country fails the run instead of silently dropping users.
- "Biggest driver" = segment with the largest contribution to the total change (not the largest % change).

### Report layout (exec-grade, see `mockup/report_mockup.html`)
10 sections, top to bottom. Driven by [`report_layout.yaml`](report_layout.yaml) (v1.0).
1. Header: title, reporting week, publish time, data freshness, AI-verified status badge.
2. Executive summary: 3 plan-attainment tiles (with next week's target / full-quarter plan) + AI headline and points.
3. Watch-outs: code-detected flags + verified AI notes, each with a "So what", status icons. Placed on top so readers see caveats before numbers.
4. KPI scorecard: 9 cards (value, polarity-aware WoW and YoY deltas, prior week and last year values, 8-week sparkline; target cards show next week's target).
5. Performance vs plan: orders vs target and revenue vs target (52 weeks + future targets to Dec 2026, "Today" marker), QTD cumulative actual vs plan to quarter end + AI points.
6. Growth drivers: WoW waterfall by region and by traffic source, YoY growth by segment vs the plan's +75% + AI points.
7. Customer health: AOV, cancellation rate, 14-Day Return Rate (mature weeks only), new signups, each with a last-year line + AI points.
8. Detail tables: region and traffic source breakdowns with WoW and YoY (collapsible).
9. Trust panel: reliability checks this run, model, prompt version, tokens, cost, latency, retries, fallback, trace link, definitions.
10. Archive of previous weeks.
Totals: 11 charts, 9 KPI cards, 3 tiles, 2 tables, 5 AI commentary slots.

### Commentary format
- Every slot is a list of points; each point = `what` (fact) + `so_what` (implication). No paragraphs.
- The brief must carry the code-computed facts a "So what" can use: next week's targets, full-quarter plan and remaining gap, QTD attainment excluding flagged weeks, revenue value of 1 pp of cancellations, 8-week averages, share of change by segment.
- New guard: every point has a non-empty `so_what` that contains no causal or recommendation language.
- New golden-set trap: YoY growth vs the plan's assumed 75% growth vs target attainment (three different comparisons that are easy to mix up).

## 4. Architecture

```
GitHub Actions (Mon 8 AM ET)
  -> timezone + idempotency guard
  -> BigQuery SQL -> KPIs, cuts, 52-week history (pandas)
  -> data-quality gates (targets present, countries mapped, week complete)
  -> data brief JSON (+ anomaly flags, notable-change markers)
  -> prompt = versioned template + business_context.md + brief
  -> Claude API (structured JSON output)
  -> guards: schema, number grounding, direction words, banned claims
       fail -> retry -> template fallback + GitHub issue alert
  -> Plotly charts + narrative -> static HTML -> GitHub Pages (with archive)
  -> trace (LangSmith) + run metrics log (latency, tokens, cost, guard results)
```

- Scheduling: cron at 12:00 and 13:00 UTC Monday (GitHub cron has no daylight saving), Python guard continues only when America/New_York hour is 8; skip if this week's report already exists. Manual rerun via `workflow_dispatch`.
- Secrets: Anthropic and LangSmith keys in GitHub secrets; BigQuery via Workload Identity Federation (no JSON key file).
- Failure path: guards fail after retries -> publish numbers with template narrative, label "commentary unavailable", open a GitHub issue.

## 5. File formats

| File | Format | Written by | Changes |
|---|---|---|---|
| `business_context.md` | Markdown | Human | Rarely |
| `prompts/narrative_vN.md` | Markdown template | Human | Versioned |
| `targets/weekly_targets_2026.csv` | CSV | Script, once | Frozen |
| `briefs/brief_YYYY-MM-DD.json` | JSON | Pipeline, weekly | Every run |
| Report page | HTML | Pipeline, weekly | Every run |

## 6. Data brief schema (v1.0)

The data brief is the ONLY data the LLM sees. It is generated by code every run, saved as `briefs/brief_<week_start>.json`, and frozen copies become golden-set fixtures. Full illustrative example: [briefs/example_brief.json](briefs/example_brief.json) (mockup numbers, not real data). Implemented as Pydantic models in `src/weekly_report/models.py`; JSON Schema export in `schemas/data_brief.schema.json`.

### Design rules
- Everything the commentary may say is pre-computed here: values, changes, directions, and whether a change is good or bad. The LLM never infers polarity or does arithmetic.
- Everything a "So what" may use is pre-computed in `so_what_facts` (matches `so_what_facts` in `report_layout.yaml`).
- Only what the commentary needs. Chart data (52 weeks, future targets) goes to a separate `chart_data.json` for rendering, not into the prompt. Keeps the prompt small (~2k tokens for the brief) and cheap.
- No personal data (no names, emails, addresses).
- Versioned (`brief_version`). A schema change bumps the version; golden fixtures record which version they use.

### Top-level structure

| Block | Purpose | Key fields |
|---|---|---|
| `brief_version` | Schema version | "1.0" |
| `meta` | Which weeks and sources this brief describes | `run_id`, `generated_at_utc`, `reporting_week` {start, end, quarter, week_of_quarter, weeks_in_quarter}, `mature_week` {start, end, used_for}, `data_through_utc`, `source`, `target_version`, `layout_version`, `plan_growth_pct` |
| `data_quality` | Gate results; the LLM step never runs if `all_passed` is false | `all_passed`, `checks[]` {name, passed, detail} |
| `kpis` | The 6 core KPIs | per KPI: `name`, `format`, `higher_is_good`, `change_unit`, `week_ref` (reporting or mature), `value`, `prior_week`, `wow_change`, `wow_direction`, `wow_assessment` (good, bad, flat), `last_year`, `yoy_change`, `yoy_direction`, `yoy_assessment`, `avg_8wk` (where used), `notable`, `notable_reason` |
| `targets` | The 3 target KPIs | `actual`, `target`, `attainment_pct`, `gap`, `status` (ahead, behind), `next_week_target`; QTD adds `target_to_date`, `full_quarter_plan`, `remaining_to_full_quarter_plan`, `weeks_left` |
| `cuts` | Orders by region and traffic source | per segment: `value`, `prior_week`, `wow_pct`, `last_year`, `yoy_pct`, `share_pct`, `contribution`, `share_of_change_pct` |
| `history_8wk` | Short context for trends and streaks | `week_start[]`, `orders[]`, `cancellation_rate[]`, `return_rate_14d[]` (null for immature weeks) |
| `flags` | Code-detected watch-outs | `id`, `type` (anomaly, streak, plan_context, maturity), `severity` (serious, warning), `kpi`, `detected_by: code`, `facts` {values + the rule that fired} |
| `so_what_facts` | Pre-computed implications | `next_week_targets`, `full_quarter_plan`, `quarter_remaining_to_plan`, `qtd_attainment_excl_flagged_pct`, `revenue_per_pp_cancellation`, `avg_8wk`, `top_contributor`, `yoy_vs_plan_growth`, `signups_vs_orders_growth`, `segments_all_growing` |

### Rules computed by code (config values, tunable)
- Notable change: |WoW| >= 10% for counts and money, >= 1.0 pp for rates, or value outside its 8-week min to max range.
- Anomaly flag: value > 2.0x or < 0.5x its 8-week average.
- Streak flag: 3 or more consecutive weekly moves in the bad direction.
- Plan-context flag: when an anomaly affects a plan KPI, also compute QTD attainment excluding the flagged week.
- Maturity: `return_rate_14d` uses the latest week where every order has had 14 days; immature weeks are null.
- Rounding: money to whole dollars (AOV to cents), rates and percentages to 1 decimal. The number-grounding guard compares against these rounded values.

### How other parts use the brief
- Prompt: brief JSON + `business_context.md` + prompt template.
- Guards: every number in the output must match a value in the brief (after rounding); every direction word must match `*_direction` and `*_assessment`; each slot may only mention KPIs allowed in `report_layout.yaml`.
- Golden set: frozen briefs from chosen historical weeks + hand-written expectations.

## 7. Prompt and output schema

TBD (Phase 2).

## 8. Guards

TBD (Phase 2/4). Planned: schema validation, number grounding (tolerance for rounding), direction/polarity check, banned claims (causal language, "net revenue", recommendations).

## 9. Evaluation design

TBD (Phase 4). Golden-set scenarios already chosen:
- Spike week (week of 2026-09-14): flag the anomaly, no naive "orders up 75%" story.
- Partial week: pipeline excludes the in-progress week.
- Return maturity: 14-Day Return Rate refers to the mature week, labeled correctly.
- Quiet week: small changes not overstated.
- Target miss in a growth week (H1 2026): "up WoW but behind plan" stated correctly.
- Good week, bad quarter: QTD behind plan despite a strong week.

## 10. Observability and cost

TBD (Phase 4/5). Models: commentary `claude-opus-5` (default), challengers `claude-sonnet-5` and `claude-haiku-4-5`; judge `claude-opus-5`. No Fable models. Starting estimate: ~6k input + ~2k output tokens per report (~$0.08 on Opus 5 at $5/$25 per 1M tokens, plus thinking tokens); eval run = golden set x (commentary + judge), ~$4 for 25 goldens on Opus 5. Actuals tracked per run.

## 11. Repo structure

```
src/weekly_report/
  config.py        settings and rule thresholds (single place to tune)
  weeks.py         reporting / prior / last-year / mature week, quarter (Thursday rule)
  bq.py            BigQuery runner: SQL files, typed params, 500 MB bytes-billed cap
  sql/             weekly_kpis.sql, weekly_cuts.sql
  rules.py         pure functions: change, polarity, notable, anomaly, streak
  targets.py       plan generation (one-time) and loading
  models.py        data brief schema (Pydantic, extra fields forbidden)
  brief.py         assembles the brief + data-quality gates
scripts/
  generate_targets.py   one-time, refuses to overwrite the frozen plan
  build_brief.py        weekly run or --week backfill; exit code 2 if a gate fails
targets/weekly_targets_2026.csv   frozen plan (53 weeks)
briefs/                           generated briefs (golden-set fixtures come from here)
schemas/data_brief.schema.json    exported JSON Schema
tests/                            unit tests (no BigQuery needed)
```

### Data handling rules found in Phase 1
- Events after the reporting week's end are ignored (source has future-dated returns and shipments).
- Cancellation status has no timestamp, so historical briefs use the current status (known limitation).
- The public dataset is regenerated daily and history changes (week of 2026-09-14 went from 2,950 to 2,344 orders overnight). Every brief records its run time; evals use frozen briefs.
