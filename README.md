# Weekly Insights Report Agent

An automated weekly business report for a (fictional) online retailer, where every KPI is computed by code and the AI-written commentary is **evaluated, traced, guarded, observable, and cost-tracked** before it is published.

> Status: design complete, Phase 1 (data and metrics) in progress.

## The problem

- An LLM can write a weekly business commentary in seconds, but an unchecked LLM can quote wrong numbers, call bad news good, or invent causes.
- One wrong number in a leadership report destroys trust in the whole report.
- This project is not about generating commentary. It is about generating commentary that is **safe to publish without a human rewriting it, and proving it**.

## How it works (short version)

```
Monday 8 AM ET (GitHub Actions)
  -> BigQuery: compute 9 KPIs, cuts, targets        (code, never the LLM)
  -> data-quality gates                              (bad data stops the run)
  -> data brief JSON                                 (the only thing the LLM sees)
  -> Claude writes commentary: points + "So what"    (structured output)
  -> guards: numbers, direction words, banned claims (fail -> retry -> safe fallback)
  -> static HTML report on GitHub Pages              (with a "how this was made" trust panel)
  -> trace + run metrics (tokens, cost, latency)
```

## Documents

| Doc | What it answers |
|---|---|
| [PRD.md](PRD.md) | What and why: problem, users, goals, reliability requirements, success metrics |
| [TECH_SPEC.md](TECH_SPEC.md) | How it works: data, KPI definitions, targets, architecture, data brief schema |
| [PLAN.md](PLAN.md) | When: phases, checklist |
| [business_context.md](business_context.md) | Stable business facts the LLM reads every week |
| [report_layout.yaml](report_layout.yaml) | Page structure and AI commentary slots (drives rendering, output schema, and guards) |
| [briefs/example_brief.json](briefs/example_brief.json) | Example data brief (illustrative numbers) |
| [mockup/report_mockup.html](mockup/report_mockup.html) | Report layout mockup (illustrative numbers) |
| [P1_Decisions_Log.md](P1_Decisions_Log.md) | Every design decision and why |

## Data

- BigQuery public dataset `bigquery-public-data.thelook_ecommerce` (fictional e-commerce store). No private or employer data.

## Stack

Python, BigQuery, Anthropic Claude API, LangSmith, GitHub Actions, GitHub Pages.
