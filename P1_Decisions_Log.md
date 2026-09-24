# P1 Decisions Log

Newest on top. Index: [../README.md](../README.md). PRD: [PRD.md](PRD.md). Tech spec: [TECH_SPEC.md](TECH_SPEC.md). Plan: [PLAN.md](PLAN.md).

## 2026-09-24

- CHANGED (user request): merged weekly_kpis.sql and weekly_cuts.sql into ONE query, `weekly_facts.sql` (grain: week x country x traffic_source, under 10k rows). Python sums it for weekly KPIs and filters it for cuts (`split_facts`). Same results (orders 2,344, revenue $169,732), cost halved from 63 MB to 31 MB billed. Every CTE commented. New test: cuts add up to weekly totals.
- PHASE 1 BUILT (steps 1 to 7): src/weekly_report package (config, weeks, bq, rules, targets, models, brief), 2 SQL files, scripts (generate_targets, build_brief), 15 unit tests passing, JSON Schema export. First real brief: `briefs/brief_2026-09-14.json`, all 6 data-quality gates pass, 63 MB billed.
- VERIFIED: brief revenue ($169,732), cancellation rate (14.4%), 14-Day Return Rate (9.4%, week of Aug 31) and new signups (1,528) match independent SQL exactly; orders (2,344) match a direct count.
- FINDING: the public dataset is REGENERATED DAILY (modified 2026-09-24 03:35 UTC, 125,176 -> 124,778 orders). Week of 2026-09-14 changed from 2,950 to 2,344 orders; week of 2026-09-07 from 1,686 to 1,662. Validates frozen targets and frozen-brief evals. The "spike" is now 1.7x the 8-week average (below the 2x anomaly rule); new signups flagged as anomaly instead.
- FINDING: 26,814 order items fall in a different week than their order. DECIDED: revenue is attributed to the week the ORDER was placed (keeps AOV = revenue / orders consistent). TECH_SPEC KPI 2 updated.
- FINDING: source has future-dated events (420 returns, 863 shipments after "now"). DECIDED: SQL ignores anything after the reporting week's end.
- DECIDED: quarter membership uses the week's Thursday (ISO convention); 2026 plan has 53 weeks. Same week last year = 364 days back (same weekday alignment).
- DECIDED: BigQuery hard cap of 500 MB billed per query (maximum_bytes_billed).
- RENAMED: so_what_facts.q3_remaining_to_plan -> quarter_remaining_to_plan (works for any quarter); layout so_what_facts now reference brief keys.
- KNOWN LIMITATION: cancellation status has no timestamp, so backfilled briefs use today's status.

- REPO: created public GitHub repo https://github.com/Himanshu2405/P1-Weekly-Insights-Report-Agent (local folder = repo root). First commit: all design docs, .gitignore (venv, .env, credentials excluded), requirements.txt, README for interviewers. Phase 1 started.
- DRAFTED: data brief schema v1.0 (TECH_SPEC section 6) + illustrative `briefs/example_brief.json` (~2k tokens). Blocks: meta, data_quality, kpis (pre-computed direction and good/bad assessment), targets, cuts, history_8wk, flags (code rules), so_what_facts. Chart data kept out of the prompt in a separate chart_data.json. Thresholds: notable |WoW|>=10% or >=1pp or outside 8-wk range; anomaly >2x or <0.5x 8-wk avg; streak 3+ bad-direction weeks.
- WROTE: report_layout.yaml v1.0 (page structure from mockup v2): 9-KPI display registry (format, polarity, change unit, mature week), 10 sections with components, 5 commentary slots (min/max points, so-what required, allowed KPIs/cuts, so-what facts), global commentary rules. Validated: parses, all KPI/slot references resolve.
- DECIDED (models): commentary default Claude Opus 5; Sonnet 5 and Haiku 4.5 are eval challengers; judge Claude Opus 5. User rule: no Claude Fable models anywhere. Eval-run cost target raised to under $5. PRD v0.5, TECH_SPEC section 10, mockup trust panel updated.
- MOCKUP v2 (user feedback): removed region mix chart (not useful); added YoY everywhere (cards, tables, last-year lines on health charts, YoY-by-segment chart vs plan +75%); future targets shown through Dec 2026 plus next week's target and full-quarter plan; watch-outs moved to top; all AI commentary as bullet points with a grounded "So what" per point. PRD v0.4, business_context v0.2, TECH_SPEC updated (commentary format, new guard, new golden trap).
- CHANGED: report upgraded from 3 visuals to an exec-grade 10-section layout (user: must impress interviewers). Commentary split into 5 per-section AI slots (easier to guard and eval). Layout to be config-driven via `report_layout.yaml`; LLM output schema derived from its commentary slots. Mockup built: `mockup/report_mockup.html` (illustrative numbers, Plotly, light/dark, mobile-checked). Added code-computed watch-out: QTD attainment excluding the flagged week.
- RESTRUCTURED: old combined spec split into TECH_SPEC.md (how it works) and PLAN.md (phases, prerequisites, checklist). Old file removed. Also corrected Phase 5: P1 ships via GitHub Actions + Pages, so it needs Module 7.3 (+7.4 concepts), not FastAPI/Docker/Cloud Run (moved to P2).
- CLARIFIED: 14-Day Return Rate = customer returned the order within 14 days of ordering (`orders.returned_at - created_at <= 14 days`), nothing to do with inventory. Verified in data: returns are whole-order (0 partial returns, 0 mixed item statuses), and returned_at is always after delivered_at. Wording fixed in business_context.md and spec.
- PRD v0.3: delivery is GitHub Pages only, no Slack or email ever.
- DRAFTED: business_context.md v0.1 (LLM runtime context). Rule: it holds stable facts only, never weekly numbers, and never mentions specific known anomalies (like the September spike), so the golden set tests whether the model reacts to brief flags rather than memorized context. Writing instructions and output schema go in the prompt file.
- PRD v0.2: open questions resolved. Pages only in v1 (Slack headline + link as v2 option); models chosen by eval (Haiku vs Sonnet for commentary, strong model for judge); commentary descriptive only, with a watch-outs section, no recommendations.
- DRAFTED: PRD.md v0.1 (problem, users, goals, non-goals, requirements, reliability acceptance targets, milestones). Doc set agreed: PRD.md, tech spec, business_context.md (LLM runtime), data brief JSON (generated weekly), prompts/*.md (versioned), targets CSV.
- APPROVED and LOCKED: KPI Spec v1 in the spec (section "KPI Spec v1"). 6 core KPIs with self-explaining names, 3 target KPIs, cuts by traffic source and region, 3 plots, 6 golden-set scenarios.
- ADDED: simulated targets for orders and revenue (user request). Method: same week last year x (1 + 75% planned growth), frozen in `targets/weekly_targets_2026.csv`, never regenerated from live data.
- FINDING: return lag median 5.5 days, p95 8.6, max ~11 days, so Weekly Order Return Rate is reported with a 2-week lag. Yearly orders: 2023 13,935; 2024 19,760; 2025 29,385; 2026 YTD 41,730.
- CHANGED: KPI 5 renamed to "14-Day Return Rate" (returned within 14 days / orders placed). Incomplete (immature) weeks are never reported.
- DECIDED: hosting = GitHub Actions scheduled workflow builds static HTML and publishes to GitHub Pages (public repo, keys in GitHub secrets, GCP via Workload Identity Federation). P2 will use Streamlit on Cloud Run.
- DECIDED: schedule = Monday 8:00 AM US Eastern. GitHub cron is UTC with no daylight-saving support, so two triggers (12:00 and 13:00 UTC Monday) plus a Python guard that only runs when America/New_York local hour is 8, and an idempotency check (skip if this week's report already exists).
- User direction: minimize time on report/KPIs, go deep on evaluated, traced, guarded, observable, cost-tracked.

## 2026-09-23 (update)

- FINDING: public `thelook_ecommerce.orders` is rolling, latest `created_at` is today (user verified with a query). Unknown whether historical rows get rewritten. Implications: use complete Monday-Sunday weeks only, and freeze a snapshot into `master-chariot-413216.thelook_raw` (US multi-region) for reproducible evals. Snapshot date and MIN/MAX/COUNT baseline pending.
- BASELINE (queried 2026-09-23): `orders` min created_at 2019-01-10, max 2026-09-23 00:45 UTC, 125,176 rows (~404 weeks, ~310 orders/week average, likely uneven). Latest completed week: Mon 2026-09-14 to Sun 2026-09-20. Next: weekly counts and status mix queries, then user picks metrics/plots/cuts/lookback.
- SETUP DONE: gcloud CLI installed (brew), ADC login completed with the personal account, venv at `P1-Weekly Insights Report/.venv` with google-cloud-bigquery, pandas, db-dtypes. Queries run from Python against project `master-chariot-413216`, about 10 MB billed per small query. Quota-project warning is harmless (optional: `gcloud auth application-default set-quota-project master-chariot-413216`).
- FINDINGS (2026-09-23): weekly orders grow steadily from about 500/week (early 2025) to about 1,200/week (Aug 2026), then spike to 1,686 (wk 09-07), 2,950 (wk 09-14, latest complete), 2,831 (wk 09-21, partial, 2-3 days). Spike looks like a data-generation change, not verified. Good candidate for an error-analysis test case. Status mix: Shipped 37,723, Complete 31,279, Processing 24,911, Cancelled 18,792, Returned 12,471. Status is CURRENT state, so recent weeks skew to Processing/Shipped; revenue metric definition must account for this (to decide with user).
- PROPOSED KPIs (pending approval): orders, revenue (excl. cancelled), AOV, cancellation rate, return rate (maturity caveat), new customers. Cuts: traffic source (5) and REGION (user request, replaces top-5 countries). Plots: 52-week trend, WoW KPI table, traffic-source breakdown.
- REGION MAPPING (proposed): APAC = China, South Korea, Japan, Australia (~44%); North America = United States (~23%); EMEA = France, UK, Germany, Spain, Belgium, Poland, Austria, plus variants "España" and "Deutschland" (~19%); LATAM = Brasil, Colombia (~14.5%). Data-quality gate: any unmapped country fails the run.
- OPEN: investigate the spike, choose lookback (default proposal 52 weeks), user's metrics/plots/cuts.
- DECIDED (supersedes snapshot plan above): NO snapshot. Query public tables in place, up to the latest completed Monday-Sunday week (cutoff computed in code). Eval stays reproducible by freezing data BRIEFS (not raw data) as golden fixtures. Record run date on every report because history may drift.
- Budget alert: user was configuring it (monthly, $5, all projects). Confirmation of save pending.
- DECIDED: P1 uses `master-chariot-413216` (Option B). User confirmed it is personal, idle, and has no cost. Budget alert still pending on this project.
- CORRECTION (earlier in day): `master-chariot-413216` ("My First Project") is an OLDER project of the user's, not one created for P1. `bigquery-public-data` is Google's shared read-only project, only starred in Explorer. P1 project decision pending: Option A new dedicated project (recommended) or Option B reuse the old one after confirming it is personal, not employer-related.
- Budget alert: NOT set yet, to be set on whichever project P1 uses. To do: Billing > Budgets & alerts > $5 budget scoped to this project. Optional: BigQuery "Query usage per day" quota of about 50 GB as a hard cap.
- Dataset explored in console: `bigquery-public-data.thelook_ecommerce` is starred and visible (tables: orders, order_items, users, products, events, inventory_items, distribution_centers, graph).

## 2026-09-23

- Repo/folder location: `~/Documents/AI learnings/Projects/P1-Weekly Insights Report`.
- LLM provider: Anthropic.
- GCP: personal project created (project ID to be recorded here once shared). Budget alert of $5 still to confirm.
- Data source: BigQuery public dataset `bigquery-public-data.thelook_ecommerce`.
- Working agreement: user reviews the raw data first, then chooses metrics, plots, and cuts. No pipeline code until that is agreed.
- Next step: data exploration (user-led), then metrics/plots/cuts spec.
