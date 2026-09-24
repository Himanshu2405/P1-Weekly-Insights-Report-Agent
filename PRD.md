# PRD: Weekly Business Insights Report with Reliable AI Commentary

| Field | Value |
|---|---|
| Owner | Himanshu Dubey |
| Status | v0.5 (2026-09-24) |
| Tech spec | [TECH_SPEC.md](TECH_SPEC.md) |
| Plan | [PLAN.md](PLAN.md) |
| Decisions log | [P1_Decisions_Log.md](P1_Decisions_Log.md) |
| Data | `bigquery-public-data.thelook_ecommerce` (fictional online clothing store "TheLook") |

## 1. Problem

- Leadership at TheLook needs a weekly view of business health: orders, revenue, customer growth, and progress against plan.
- Today (simulated baseline) an analyst pulls numbers, builds charts, and writes commentary by hand every Monday. This takes 2 to 3 hours a week, arrives late, and the quality of the commentary depends on who wrote it.
- An LLM can write the commentary in seconds, but an unchecked LLM can quote wrong numbers, call bad news good, or invent causes. One wrong number in a leadership report destroys trust in the whole report.
- The real problem is not "generate commentary". It is "generate commentary that is trustworthy enough to publish without a human rewriting it, and prove it".

## 2. Users and stakeholders (simulated)

| User | Need | Uses the report to |
|---|---|---|
| Head of E-commerce (primary) | Is the business on track this week? | Decide where to focus the team |
| Marketing lead | Which channels and regions drive growth? | Shift spend between traffic sources |
| Finance / planning | Are we on plan for the quarter? | Flag risk to the quarterly forecast |
| Analyst (report owner) | Stop hand-writing the report | Spend time on deep dives instead |

## 3. Goals

- G1. Publish a weekly report automatically every Monday by 8:00 AM US Eastern, with no manual step.
- G2. Commentary is factually grounded: every number in the prose matches the computed data.
- G3. Commentary is useful: it states performance vs last week and vs plan, calls out anomalies, and names the biggest drivers by channel and region.
- G4. The AI layer is measurable and observable: every run is evaluated, traced, and cost-tracked, and failures are visible, not silent.

## 4. Non-goals

- No interactive dashboard or chatbot (that is Project 2).
- No causal explanations ("orders rose BECAUSE of the campaign"). The report describes what changed and where, not why.
- No forecasting or target setting. Targets are an input from the plan file.
- No RAG. All context fits in one prompt.
- No real-time data. Weekly grain only.

## 5. Scope

In scope (v1):
- 9 KPIs: Weekly Orders Placed, Weekly Gross Revenue (excl. cancelled), Weekly Average Order Value, Weekly Order Cancellation Rate, 14-Day Return Rate, Weekly New Customer Signups, Weekly Orders vs Target, Weekly Gross Revenue vs Target, Quarter-to-Date Gross Revenue vs Target. Full definitions in the tech spec.
- Cuts by traffic source (5) and region (APAC, North America, EMEA, LATAM).
- 3 charts, 1 KPI table, AI-written commentary.
- Static HTML report on GitHub Pages with an archive of past weeks.

Out of scope: product and category cuts, web funnel (`events` table), any delivery channel other than GitHub Pages (no email, no Slack).

## 6. User stories

- As the Head of E-commerce, I open one link on Monday morning and understand in 2 minutes whether last week was good or bad and why it matters.
- As Finance, I see whether we are ahead or behind plan for the week and for the quarter, stated plainly.
- As Marketing, I see which traffic source and region contributed most to the change.
- As the report owner, I get alerted when the AI commentary fails checks, instead of finding out from a stakeholder.

## 7. Functional requirements

| ID | Requirement |
|---|---|
| F1 | Run automatically every Monday at 8:00 AM US Eastern; support manual rerun |
| F2 | Report the latest completed Monday to Sunday week only; never a partial week |
| F3 | Compute all KPIs in code (SQL/Python); the LLM never calculates numbers |
| F4 | Report the 14-Day Return Rate only for mature weeks, clearly labeled with the week it refers to |
| F5 | Compare each KPI to the prior week (WoW), the same week last year (YoY), and, where available, the plan target. Show future targets through year end |
| F6 | Produce commentary as bullet points with a "So what" per point, in fixed slots: executive summary, watch-outs, performance vs plan, growth drivers, customer health |
| F7 | Flag anomalies detected by code (for example a KPI far outside its recent range) |
| F8 | Publish HTML to GitHub Pages and keep an archive of past reports |
| F9 | Stop the run if input data fails quality checks (missing target row, unmapped country, empty week) |

## 8. Reliability requirements (the core of this project)

| Area | Requirement | Initial acceptance target (to calibrate) |
|---|---|---|
| Guarded | Every number in the commentary exists in the data brief (within rounding) | 100% on published reports (enforced by guard, not hoped for) |
| Guarded | Direction words match the sign and polarity of the change (for example "worsened" for a rising cancellation rate) | 100% on published reports |
| Guarded | Output matches the required JSON schema | 100%; retry, then template fallback |
| Evaluated | Golden set of historical weeks with hand-labeled expectations, including hard scenarios (spike week, target miss in a growth week, quiet week, good week in a bad quarter) | 25 or more examples |
| Evaluated | LLM-as-judge scores faithfulness and usefulness, calibrated against human labels | Judge agrees with human labels on 85% or more |
| Evaluated | Every prompt or model change runs the eval suite in CI and cannot merge if scores drop | Pass rate 90% or more on golden set |
| Traced | Every run records input brief, prompt version, model, output, guard results, retries | 100% of runs traced (LangSmith) |
| Observable | Per-run metrics: latency, tokens, cost, guard pass/fail, retries, fallback used | Visible in a run history log and on the report footer |
| Cost-tracked | Cost per weekly report and per eval run recorded; Opus 5 vs Sonnet 5 vs Haiku 4.5 compared | Under $0.10 per report, under $5 per full eval run |
| Resilient | On guard failure after retries: publish numbers with template commentary, label it, and open an alert | Zero wrong numbers published, ever |

## 9. Success metrics

- Reliability: zero published reports with a wrong number or wrong direction word.
- Quality: golden-set pass rate of 90% or more; judge-to-human agreement of 85% or more.
- Operations: report published on time on 95% or more of Mondays; fallback used on 10% or fewer of runs.
- Cost: under $0.10 per report; total project LLM spend in low single-digit dollars.
- Evidence: a before/after error-analysis write-up showing specific failure types found and fixed.

## 10. Constraints and assumptions

- Public data only; no employer data, code, prompts, or names.
- Data is rolling and rewritten daily; history may drift slightly. Every report records its run date. Evals use frozen briefs, not live data.
- Targets are simulated (same week last year x 1.75) and frozen in a versioned file.
- Budget: GCP free tier with a $5 alert; Anthropic API pay-as-you-go.
- Stack: Python, BigQuery, Anthropic API, LangSmith (free tier), GitHub Actions, GitHub Pages.

## 11. Risks and mitigations

| Risk | Mitigation |
|---|---|
| LLM quotes a wrong or invented number | Number-grounding guard, retry, template fallback |
| LLM misreads a data anomaly as real growth (September spike) | Code-computed anomaly flags in the brief; golden-set scenario for it |
| Immature return data looks like an improvement | 14-Day Return Rate only on mature weeks, labeled |
| Source data changes shape or breaks | Data-quality gates stop the run before the LLM step |
| Scheduler runs late or twice | Timezone guard and idempotency check |
| Cost creep during eval iteration | Cost logged per run; budget alert; small golden set run on every change, full set before release |

## 12. Milestones (mapped to the learning plan)

| Milestone | Deliverable | Needs from plan |
|---|---|---|
| M0 Setup | Environment, BigQuery access | Done |
| M1 Data | SQL, KPIs, targets file, data brief | Modules 1, 2, 2.5 (done) |
| M2 Commentary | Business context file, prompt, automated LLM call, schema output | Module 3 (done) |
| M3 Reliability | Guards, golden set, judge, tracing, error analysis | Module 5 (in progress) |
| M4 Ship | HTML report, GitHub Actions schedule, Pages, alerts, run metrics | Modules 7.3, 7.4 |
| M5 Story | README and slides for interviews | All of the above |

## 13. Decisions (resolved 2026-09-24)

- Delivery: GitHub Pages only. No Slack or email, now or later.
- Models: commentary default is Claude Opus 5 (`claude-opus-5`). Claude Sonnet 5 and Claude Haiku 4.5 are eval challengers: if one passes the same golden set and guards, switch to it and report the savings. Judge: Claude Opus 5 (at least as capable as the model it grades). No Claude Fable models anywhere in this project.
- Commentary style: bullet points, never long paragraphs. Every point = what happened + a "So what" (the business implication). A "So what" must be grounded in code-computed facts in the brief (plan impact, quarter outlook, revenue value of a change, comparison between KPIs, data caveats). Still no causes and no action recommendations such as "increase spend", because they cannot be verified from the data and invite invented causes.

## 14. Open questions

- None at this time.
