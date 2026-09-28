# Tech Spec: Weekly Business Insights Report with Reliable AI Commentary

| Field | Value |
|---|---|
| Version | v1.1 (2026-09-28) |
| PRD (what and why) | [PRD.md](PRD.md) |
| Plan (when and learning map) | [PLAN.md](PLAN.md) |
| LLM runtime context | [business_context.md](business_context.md) |
| Decisions log | [P1_Decisions_Log.md](P1_Decisions_Log.md) |

This document describes HOW the system works.

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
- Reporting clock: frozen at `config.AS_OF_WEEK` = week of 2026-08-03 (last week of steady data; accelerating growth from 2026-08-10 and a data break at 2026-09-14). Set to None to report the latest completed week. The schedule re-publishes the as-of week; an 8-week archive is backfilled once with `build_report.py --backfill`.
- Fiscal year: Jan to Dec. Weeks belong to the month and quarter of their Thursday.
- Reporting week: Monday 00:00 to Sunday 23:59:59 UTC. Report always covers the latest COMPLETED week, computed in code, never hard-coded.
- Comparisons per KPI: week over week (WoW), year over year (YoY, same ISO week last year), vs target (where a target exists), and a 52-week trend.
- Future targets (through Dec 2026) are shown on target charts and as "next week's target" and "full-quarter target".
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

### Target KPIs (simulated targets)

| # | KPI name | Definition / formula | Good direction | Reliability trap it tests |
|---|---|---|---|---|
| 7 | Weekly Orders vs Target (attainment %) | KPI 1 / weekly orders target x 100. Also report the gap (actual minus target) | Up | "Above/below target" wording must match attainment vs 100% |
| 8 | Weekly Gross Revenue vs Target (attainment %) | KPI 2 / weekly revenue target x 100, plus the gap in USD | Up | Same as above, plus mixing up WoW growth with target attainment |
| 9 | Quarter-to-Date (QTD) Gross Revenue vs Target | Sum of KPI 2 from quarter start through reporting week / sum of weekly targets for the same weeks | Up | Cumulative vs weekly confusion: a good week can still leave the quarter behind target |
| 10 | Year-to-Date (YTD) Gross Revenue vs Target | Same as KPI 9 for the fiscal year (Jan to Dec). Also: full-year target, remaining to target, required weekly run-rate = (FY target - YTD actual) / weeks left, current 8-week run-rate | Up | Run-rate confusion: "ahead YTD" does not mean the remaining target is achievable |

Also computed: ITPY (index to prior year) for orders and revenue = value / same week last year x 100; target index = 175. Monthly revenue vs target per fiscal month (weeks assigned by their Thursday; current month is month-to-date).

### How targets are simulated
- Real companies get targets from Finance once per year. We mimic that with a frozen targets file, not a live calculation.
- Method: weekly target = same ISO week last year actual x (1 + target YoY growth). Using last year's same week keeps seasonality.
- Target YoY growth: 75% for 2026 (config value). Rationale: actual growth was ~50% early 2026 and ~100% by August, so the targets produce a realistic story (behind target in H1, ahead in H2, far ahead during the September spike).
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

### Report layout (leadership style, driven by `report_layout.yaml` v1.1)
1. Header: title, reporting week, data-check badge, AI status, build time, data cutoff.
2. Executive summary: 4 tiles (weekly orders, weekly revenue, QTD, YTD) with attainment, a light status pill, the gap, and what comes next (next week's target, quarter target, required weekly run-rate) + AI points.
3. Watch-outs: code-detected flags (deterministic text) + AI notes.
4. KPI scorecard: 9 cards with WoW and YoY delta pills (light green / light red by business meaning) and 8-week sparklines.
5. Performance vs target (FY2026): orders and revenue vs target for the fiscal year (Jan to Dec) with light quarter bands and a report-week marker; monthly revenue variance waterfall (YTD target -> month variances -> YTD actual); path-to-target bridge (YTD actual -> remaining months at target -> FY outlook vs FY target line, with required vs current run-rate); ITPY chart (orders and revenue vs target index 175); QTD burn-up + AI points.
6. Growth drivers: WoW waterfalls by region and traffic source (zoomed y-axis), YoY by segment vs target +75% + AI points.
7. Customer health: AOV, cancellation rate, 14-Day Return Rate, new signups, each with last year + AI points.
8. Detail tables, 9. Trust panel, 10. Archive (earlier weeks only).
Charts are half width (two per row) unless `width: full`. Light palette: tinted tiles, pastel waterfall fills (gains, losses, totals, future target).

### Commentary format
- Every slot is a list of points; each point = `what` (fact) + `so_what` (implication). No paragraphs.
- The brief must carry the code-computed facts a "So what" can use: next week's targets, full-quarter target and remaining gap, QTD attainment excluding flagged weeks, revenue value of 1 pp of cancellations, 8-week averages, share of change by segment.
- New guard: every point has a non-empty `so_what` that contains no causal or recommendation language.
- New golden-set trap: YoY growth vs the targets' assumed 75% growth vs target attainment (three different comparisons that are easy to mix up).

## 4. Architecture

```
GitHub Actions (Mon 12:00 and 13:00 UTC)
  -> guard job: schedule.is_scheduled_run() - proceed only if this is actually 8am America/New_York
  -> build-and-publish job:
       -> pytest (guards, judge, schema, schedule tests) must pass before anything runs
       -> GCP auth via Workload Identity Federation (no JSON key file)
       -> BigQuery SQL -> KPIs, cuts, 52-week history (pandas)
       -> data-quality gates (targets present, countries mapped, week complete)
       -> data brief JSON (+ anomaly flags, notable-change markers)
       -> prompt = versioned template + business_context.md + brief
       -> Claude (Anthropic API in CI; Claude Code headless locally) -> structured JSON output
       -> guards: schema, number grounding, direction words, banned claims
            fail -> retry -> template fallback
       -> Plotly charts + narrative -> static HTML -> GitHub Pages
       -> commit runs/run_log.jsonl (latency, tokens, cost, guard results)
  -> alert-on-failure job: any failure in the two jobs above -> open a GitHub issue
```

- Scheduling: two cron triggers (12:00 and 13:00 UTC Monday) bracket 8am America/New_York across EST and EDT, since GitHub cron is UTC-only with no daylight-saving support. `weekly_report/schedule.is_scheduled_run()` lets only the one that actually lands on 8am ET proceed; the other exits as a no-op (tested for both EST and EDT). No separate "does this week's report already exist" check: `AS_OF_WEEK` is frozen, so every run targets the same week by design (see section 3). Manual rerun via `workflow_dispatch` (a `force` input skips the time guard).
- Secrets: `ANTHROPIC_API_KEY` (CI-only Claude backend, the one real stored secret) in GitHub secrets; BigQuery via Workload Identity Federation instead of a key file (`scripts/setup_gcp_wif.sh`, a Workload Identity Pool + OIDC provider scoped to this exact repo, impersonating a service account with only `roles/bigquery.jobUser`).
- Failure path: guards fail after retries -> publish numbers with template narrative, label "commentary unavailable", still enforced blocking (this happened on the first real scheduled test run, see section 7). A workflow-level failure (not a guard failure) opens a GitHub issue automatically.

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
- Brief v1.1 adds `targets.ytd_revenue_vs_target`, `targets.monthly_revenue`, `kpis.*.itpy`, and FY run-rate facts in `so_what_facts`. Everything the commentary may say is pre-computed here: values, changes, directions, and whether a change is good or bad. The LLM never infers polarity or does arithmetic.
- Everything a "So what" may use is pre-computed in `so_what_facts` (matches `so_what_facts` in `report_layout.yaml`).
- Only what the commentary needs. Chart data (52 weeks, future targets) goes to a separate `chart_data.json` for rendering, not into the prompt. Keeps the prompt small (~2k tokens for the brief) and cheap.
- No personal data (no names, emails, addresses).
- Versioned (`brief_version`). A schema change bumps the version; golden fixtures record which version they use.

### Top-level structure

| Block | Purpose | Key fields |
|---|---|---|
| `brief_version` | Schema version | "1.0" |
| `meta` | Which weeks and sources this brief describes | `run_id`, `generated_at_utc`, `reporting_week` {start, end, quarter, week_of_quarter, weeks_in_quarter}, `mature_week` {start, end, used_for}, `data_through_utc`, `source`, `target_version`, `layout_version`, `target_growth_pct` |
| `data_quality` | Gate results; the LLM step never runs if `all_passed` is false | `all_passed`, `checks[]` {name, passed, detail} |
| `kpis` | The 6 core KPIs | per KPI: `name`, `format`, `higher_is_good`, `change_unit`, `week_ref` (reporting or mature), `value`, `prior_week`, `wow_change`, `wow_direction`, `wow_assessment` (good, bad, flat), `last_year`, `yoy_change`, `yoy_direction`, `yoy_assessment`, `avg_8wk` (where used), `notable`, `notable_reason` |
| `targets` | The 3 target KPIs | `actual`, `target`, `attainment_pct`, `gap`, `status` (ahead, behind), `next_week_target`; QTD adds `target_to_date`, `full_quarter_target`, `remaining_to_full_quarter_target`, `weeks_left` |
| `cuts` | Orders by region and traffic source | per segment: `value`, `prior_week`, `wow_pct`, `last_year`, `yoy_pct`, `share_pct`, `contribution`, `share_of_change_pct` |
| `history_8wk` | Short context for trends and streaks | `week_start[]`, `orders[]`, `cancellation_rate[]`, `return_rate_14d[]` (null for immature weeks) |
| `flags` | Code-detected watch-outs | `id`, `type` (anomaly, streak, target_context, maturity), `severity` (serious, warning), `kpi`, `detected_by: code`, `facts` {values + the rule that fired} |
| `so_what_facts` | Pre-computed implications | `next_week_targets`, `full_quarter_target`, `quarter_remaining_to_target`, `qtd_attainment_excl_flagged_pct`, `revenue_per_pp_cancellation`, `avg_8wk`, `top_contributor`, `yoy_vs_target_growth`, `signups_vs_orders_growth`, `segments_all_growing` |

### Rules computed by code (config values, tunable)
- Notable change: |WoW| >= 10% for counts and money, >= 1.0 pp for rates, or value outside its 8-week min to max range.
- Anomaly flag: value > 2.0x or < 0.5x its 8-week average.
- Streak flag: 3 or more consecutive weekly moves in the bad direction.
- Target-context flag: when an anomaly affects a target KPI, also compute QTD attainment excluding the flagged week.
- Maturity: `return_rate_14d` uses the latest week where every order has had 14 days; immature weeks are null.
- Rounding: money to whole dollars (AOV to cents), rates and percentages to 1 decimal. The number-grounding guard compares against these rounded values.

### How other parts use the brief
- Prompt: brief JSON + `business_context.md` + prompt template.
- Guards: every number in the output must match a value in the brief (after rounding); every direction word must match `*_direction` and `*_assessment`; each slot may only mention KPIs allowed in `report_layout.yaml`.
- Golden set: frozen briefs from chosen historical weeks + hand-written expectations.

## 7. Commentary engine, prompt and output schema

### Engine (decided 2026-09-25; second backend added 2026-09-28)
- Local runs: **Claude Code headless** (`claude -p`), called by the Python pipeline once per brief. Uses the user's Claude subscription login; no Anthropic API key.
- Scheduled/CI runs: GitHub Actions has no access to that local login, so `llm.call_structured()` switches to the **Anthropic API** (`llm._anthropic_api`) whenever `ANTHROPIC_API_KEY` is set in the environment (only true inside the workflow). Both backends return the same internal dict shape, so nothing downstream (`generate()`, guards, retry, fallback, logging) knows or cares which one ran; the page's trust panel labels the engine used per run.
- Cost on the API path is computed locally from Anthropic's published per-token pricing (input/output/cache-write/cache-read), since the API response has no `total_cost_usd` field the way the CLI's JSON output does.
- The API path needed one adjustment the CLI path didn't: the Messages API's `output_config.format` structured-outputs schema mode rejects `maxItems` outright and only allows `minItems` of 0 or 1, but the commentary schema's per-section point-count limits use 2-4. `llm._api_schema()` strips both before the API call; the count is still enforced locally by `commentary_model()` after every response and still stated in the prompt text and the schema's `description` field, so nothing is left unchecked. Found on the first real scheduled-run test (published the fallback template both times before the fix).
- Isolation flags (CLI path): run from an empty folder, `--system-prompt` (replaces the Claude Code agent prompt), `--tools ""`, `--setting-sources ""`, `--strict-mcp-config`, `--no-session-persistence`, `--disable-slash-commands`, `--model claude-sonnet-5`, `--json-schema`, stdin from /dev/null.
- Known limitation: the CLI always adds the account email and an environment block (working folder, today's date). No personal CLAUDE.md, memory, tools, or skills are loaded (verified). The prompt states the reporting week explicitly; guards catch wrong dates.
- Every call returns tokens, duration, and a cost figure (API-equivalent for the CLI, real for the API path), logged per run.

### Isolation and feasibility test (2026-09-25)
- Probe in an empty folder: no CLAUDE.md, memory, formatting rules, tools, or skills leaked. 10.2 s, $0.029 equivalent.
- Real brief (week of 2026-08-03) with JSON schema: valid structured output, all spot-checked numbers match the brief, no causes or recommendations. 14.1 s, ~9.6k input / 1.2k output tokens, $0.125 equivalent, of which ~75% was a one-time prompt-cache write.
- First failure types seen: "so what" restates facts instead of an implication; points too long for leadership; topics mixed across slots.

### Prompt (built 2026-09-25)
- `prompts/commentary_v1.md`: role, 9 rules (numbers only from the brief, good/bad from the brief, one-sentence what + so what, no causes or recommendations, "target" not "plan", name the mature return week, mention anomalies, under 30 words, slot KPI limits), the 5 slots, and a `{{business_context}}` placeholder filled at run time. Versioned: v2, v3 are new files, so eval results can be tied to a version.

### Output format (built 2026-09-25)
- `src/weekly_report/commentary_schema.py` generates it from `commentary_slots` in `report_layout.yaml`: one object per slot (summary, watchouts, vs_target, drivers, health), each with `points` (min/max from the layout) of `{what, so_what}`; `summary` also has a `headline`. Extra fields are rejected.
- Used twice: passed to Claude (`--json-schema`) so the answer has the page's shape, and used to validate the answer before the guards run.
- Exported for reading at `schemas/commentary_output.schema.json` (references inlined, self-contained).
- Sentence length capped at 240 characters in the schema; the exact 30-word rule is a guard.

## 8. Guards (built 2026-09-25, `src/weekly_report/guards.py`)

Plain-code checks on the commentary before publishing. **Block** = publishing would put something wrong in front of leadership (retry, then fallback). **Warn** = quality issue (logged, shown in evals, does not stop publishing).

| Check | Severity | What it catches | From error analysis |
|---|---|---|---|
| Numbers exist in the brief | block | Any number (dates excluded) not found in the brief at its written precision | Core rule |
| Direction words match the data | block | "rose/fell/improved/worsened" contradicting the brief's direction and good/bad fields (single-KPI sentences; multi-KPI sentences go to the judge) | Core rule |
| Ahead/behind target matches | block | "ahead of target" when nothing is ahead, and vice versa | Core rule |
| No causes, recommendations, "plan", "net revenue" | block | "because of", "due to", "should", "recommend", "plan", ... ("because the value..." explaining a flag is allowed) | Core rule |
| Return rate names its mature week | block | 14-Day Return Rate quoted without its week | Core rule |
| Anomaly acknowledged in summary | block | Anomaly flag in the brief but not mentioned | Core rule |
| Sentence length and density | warn | > 30 words or > 4 numbers in a sentence | G |
| Slot scope | warn | A slot's facts mention KPIs outside its allowed list (so-whats may link to other KPIs) | C |
| Repetition | warn | The same specific number in 3+ slots | C |
| So-what differs from what | warn | So-what mostly repeating the what (word overlap > 60%) | A (partial; the judge handles the rest) |

First run on real output (week of 2026-08-03, prompt v1): all blocking checks pass; warnings for density (3), repetition (95.1%, 12.0%, 11.0% in 3 slots). Two false positives found and fixed ("because the value..." flagged as causal; revenue in a health so-what flagged as off-scope). Guard precision is itself something to measure in Phase 4.

Wiring (built 2026-09-25, `commentary.py`): generate -> guards -> on a blocking failure, one retry with the exact failures fed back to Claude -> if still blocked, fallback ("commentary unavailable", numbers still published). Infrastructure errors (CLI crash, timeout, bad JSON) get their own retries with exponential backoff (5 s, 10 s) inside `llm.generate`, so they never use up the content retry. Every attempt, including rejected ones, is saved with its text and guard findings for error analysis. Commentary is cached by a hash of the brief's content + prompt version + model: an unchanged week re-renders with no new call.

False positives found on the first real runs (all fixed, each kept as a regression test): "because the value..." read as a cause; a revenue link in a health so-what read as off-scope; "LATAM slipped" checked against total orders instead of the segment; "should not be read as..." read as a recommendation; "Jan to Apr were behind target" checked against week/quarter/year status only. In the first 3 end-to-end runs, 5 of 6 blocks were guard false positives and 1 was a real violation (Claude calculated "49 additional orders" and a "combined 10.7% share"). Lesson: guards need their own error analysis, or they cost money and availability.

## 9. Evaluation design

Golden set: 16 frozen weeks from Jan to Jun 2026 in `evals/golden/` (see its README for the list and why each week is there). 10 weeks (Jan to Jun, not in the golden set) held out in `evals/heldout/`. Original scenario ideas:
- Spike week (week of 2026-09-14): flag the anomaly, no naive "orders up 75%" story.
- Partial week: pipeline excludes the in-progress week.
- Return maturity: 14-Day Return Rate refers to the mature week, labeled correctly.
- Quiet week: small changes not overstated.
- Target miss in a growth week (H1 2026): "up WoW but behind target" stated correctly.
- Good week, bad quarter: QTD behind target despite a strong week.

### Results (final, 2026-09-27)
- Judge iterated v1 -> v4, calibrated against 20 hand labels (v1: 85% agreement; v2, after fixing the two vaguest rules: 100% on that same sample, an optimistic number since it's the data the fix was tuned on, not a fresh held-out check).
- Prompt v1 -> v2 (judge_v3, golden set, same judge for both): so-what real-implication rate 68% -> 88%. v2 promoted to production on this result.
- Held-out replay (v2, judge_v4, a later judge revision than the 68%/88% pair above so not directly comparable to it): 9 of 10 published (1 fallback), so-what real-implications 96% on golden vs 83% on the 10-week held-out set never used to tune anything, a real but modest generalization gap.
- Prompt v3 held-out generation run (8/10 first-attempt, 2 after retry, $1.65 total): judging it, and a same-model v2-vs-v3 held-out comparison, were deliberately not run. The dataset is synthetic with no ground truth for "correct" commentary, so further iteration past this point would spend tokens chasing a score rather than adding a real lesson. Full numbers and reasoning: `P1_Decisions_Log.md` 2026-09-27.
- Guard error analysis found most early "failures" were guard false positives, not real violations (see section 8); fixing guard precision mattered more for reliability than any single prompt change.

## 10. Observability and cost

- **Run log** `runs/run_log.jsonl`: one line per run with week, brief id and hash, status (verified, verified_after_retry, fallback), cache hit, prompt version, model, attempts, LLM cost (API equivalent), LLM time, tokens (input, cache write/read, output, thinking), BigQuery MB, checks passed, blocking failures, warning details, errors.
- **Page**: header badge ("AI commentary verified: 6 of 6 checks passed, 2 warnings" or "Commentary unavailable"), trust panel listing every data and AI check with warning details, plus model, prompt version, engine, attempts, tokens, cost, time.
- **Terminal**: one status line per run with any failures and warnings.
- **Cost, local dev (Sonnet 5, Claude Code headless)**: about $0.15-0.19 for one clean attempt; more with a retry. Most input cost is the prompt-cache write of the fixed instructions.
- **Cost, scheduled run (Sonnet 5, Anthropic API)**: $0.1537 on the first fully successful scheduled test run, the third live attempt after two real bugs were found and fixed on the first two (1 attempt, 12,197 input / 12,928 output tokens, 10/10 checks passed). In line with the local estimate.
- Observability is deliberately homegrown, not a hosted platform: `run_log.jsonl` + the trust panel + guard/judge error analysis. LangSmith was evaluated and deferred to P2 (a live chatbot with continuous traffic is the tracing platform's actual use case; see `P1_Decisions_Log.md` 2026-09-27).

## 11. Repo structure

```
src/weekly_report/
  config.py        settings and rule thresholds (single place to tune)
  weeks.py         reporting / prior / last-year / mature week, quarter (Thursday rule)
  schedule.py      is_scheduled_run(): the 8am-ET guard for the double cron trigger
  bq.py            BigQuery runner: SQL files, typed params, 500 MB bytes-billed cap
  sql/             weekly_facts.sql (single query: week x country x traffic source)
  rules.py         pure functions: change, polarity, notable, anomaly, streak
  targets.py       target generation (one-time) and loading
  models.py        data brief schema (Pydantic, extra fields forbidden)
  brief.py         assembles the brief + data-quality gates
  pipeline.py      one run: query once -> KPIs, cuts, targets, brief
  llm.py           call_structured(): Claude Code headless locally, Anthropic API in CI
  commentary.py    generate -> guards -> retry -> fallback -> log, cache by brief hash
  guards.py        10 deterministic checks (6 blocking, 4 warn)
  judge.py         LLM-as-judge (calibrated), used for eval, not for publish-time gating
  chart_data.py    chart series per layout component (never sent to the LLM)
  render.py        builds the HTML page from layout + brief + chart data
templates/         report.html.j2 (Jinja, loops over layout sections) + report.css
scripts/
  generate_targets.py   one-time, refuses to overwrite the frozen targets
  build_brief.py        brief only; weekly run or --week backfill; exit code 2 if a gate fails
  build_report.py       full run: brief + AI commentary + HTML report (not rendered if a gate fails)
  should_run_now.py     exits 0 only at the scheduled hour; called by weekly-report.yml
  setup_gcp_wif.sh      one-time GCP Workload Identity Federation setup (run by hand, not by CI)
  run_golden.py, judge_golden.py, replay.py, compare_experiments.py   eval batch runners
.github/workflows/
  tests.yml           eval-in-CI: pytest on every push, no credentials needed
  weekly-report.yml   guard -> build -> GCP auth -> tests -> Pages deploy -> failure issue
site/                             generated report pages (git-ignored; published live by weekly-report.yml)
targets/weekly_targets_2026.csv   frozen targets (53 weeks)
briefs/                           generated briefs (golden-set fixtures come from here)
evals/                            golden set, held-out set, judge prompts, experiment results
runs/run_log.jsonl                one line per run: status, cost, tokens, checks (tracked in git)
schemas/data_brief.schema.json    exported JSON Schema
tests/                            unit tests (no BigQuery needed; 61 passing, all offline)
```

### Data handling rules found in Phase 1
- Events after the reporting week's end are ignored (source has future-dated returns and shipments).
- Cancellation status has no timestamp, so historical briefs use the current status (known limitation).
- The public dataset is regenerated daily and history changes (week of 2026-09-14 went from 2,950 to 2,344 orders overnight). Every brief records its run time; evals use frozen briefs.
