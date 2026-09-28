# Plan: P1 Weekly Insights Report

| Field | Value |
|---|---|
| Updated | 2026-09-28 |
| Learning plan | [AI_Automation_Engineering_Plan.md](../../AI_Automation_Engineering_Plan.md) |
| PRD | [PRD.md](PRD.md) |
| Tech spec | [TECH_SPEC.md](TECH_SPEC.md) |
| Decisions log | [P1_Decisions_Log.md](P1_Decisions_Log.md) |

This document covers WHEN and WHAT TO LEARN FIRST. How the system works lives in the tech spec.

Legend: DONE = covered by a completed module. PREREQ = must learn first. GAP = small skill not in the plan, learn just-in-time. OPTIONAL = only if evals show a need.

## Phases

### Phase 0: Setup (DONE)
- Needs: Module 1 (venv, files, requests, unit testing). DONE.
- Done: gcloud CLI, ADC login, project `master-chariot-413216`, venv with BigQuery client.
- Done: git repo + `.gitignore`, public GitHub repo created.
- Done: $5 monthly GCP budget alert confirmed saved (2026-09-28), triggers at 50/90/100/150% of spend. Covers GCP/BigQuery cost only; Anthropic API spend is tracked separately in the Anthropic console and in `runs/run_log.jsonl`.
- GAP: git/GitHub basics. Confirm comfortable.

### Phase 1: Data and metrics (DONE)
- Needs: Module 1 (Python, JSON), Module 2 (classes), Module 2.5 (NumPy). DONE.
- GAP: pandas (assumed from DS background).
- Tasks: data brief schema, SQL, targets file, KPI calc, cuts, data-quality gates, data brief writer, Plotly charts.

### Phase 2: Automated LLM narrative (DONE)
- Needs: Module 3 (LLM APIs, structured outputs). DONE. Module 2.5 (token/cost intuition). DONE.
- GAP: Pydantic for schema validation (also used in Module 7.1).
- Tasks: prompt v1, structured JSON output, retries with backoff, token and cost logging, first guards.

### Phase 3: Drill-down tools (OPTIONAL)
- Needs: Modules 3 and 4. DONE.
- Only if evals show the brief misses insights: let the model call `get_breakdown(metric, segment)`.

### Phase 4: Evaluation, reliability (core of the project) (DONE)
- Needs: Module 3, Module 4. DONE.
- Done: golden set (16 weeks), 10 deterministic guards, LLM-as-judge (judge_v1 to v4, calibrated), error analysis (`guard_review.md`), retry with feedback, fallback, held-out replay, eval-in-CI (`.github/workflows/tests.yml`, Phase 5 work).
- DECIDED (2026-09-27): LangSmith tracing/dashboard deferred to P2. P1 is a manual weekly batch job, not live production traffic, so the homegrown stack (guards, judge, `run_log.jsonl`) is the final observability/eval answer here, not a placeholder for LangSmith. P2's chatbot has the real production-traffic use case for a tracing UI. See `P1_Decisions_Log.md` 2026-09-27 and Module 5 in the learning plan.

### Phase 5: Ship and operate (DONE)
- PREREQ: Module 7.3 (GitHub Actions). Module 7.4 (observability concepts) for run metrics. Both done.
- Not needed for P1: 7.1 FastAPI, 7.2 Docker, 7.5 Cloud Run (those go to P2).
- Done: `.github/workflows/weekly-report.yml` (8am-ET schedule guard, GCP auth via Workload Identity Federation, guards/tests before publishing, GitHub Pages deploy, failure files a GitHub issue), `.github/workflows/tests.yml` (eval-in-CI), run metrics on the report footer (built in Phase 2).
- BLOCKER FOUND AND FIXED (2026-09-28): GitHub Actions has no access to the local Claude Code subscription login local runs use. Added a second `llm.py` backend (`_anthropic_api`, real ANTHROPIC_API_KEY as a GitHub secret, ~$0.15/run) used only in CI; picked automatically, local dev unaffected. Two real-run bugs found and fixed: the Messages API's structured-output schema mode rejects `maxItems` outright and only allows `minItems` of 0 or 1 (the CLI's `--json-schema` has neither limit) - `_api_schema()` strips both before the API call, still enforced locally by Pydantic and stated in the prompt.
- First fully successful scheduled-workflow test run (2026-09-28, manual `workflow_dispatch`, the third live attempt after the two bugs above): verified, 1 attempt, 10/10 checks passed, $0.1537, published live at https://himanshu2405.github.io/P1-Weekly-Insights-Report-Agent/.

### Not used in P1
- Module 6 (RAG): deliberately unused. Explain why in the interview.

## Recommended order

- Phases 1, 2, 4, and 5 are all complete.
- Remaining: README + slides deliverable (below). Phase 3 stays optional/skipped.

## Deliverables

- Repo README: objective, why, what, how, architecture, data, eval results, cost table, failure taxonomy, lessons.
- Eval report: before/after error analysis.
- Slides (later): problem, architecture, reliability loop, results, cost, demo.

## Checklist

- [x] Phase 0 Setup (budget alert confirmed)
- [x] PRD v0.3
- [x] business_context.md v0.1
- [x] KPI Spec v1 locked
- [x] Phase 1 Data and metrics (brief pipeline, charts, HTML report with commentary placeholders)
- [x] Phase 2 AI commentary: prompt v1, output format, Claude headless call, guards, retry with feedback, fallback, cache, run log, page
- [ ] Phase 3 Drill-down tools (optional, skipped)
- [x] Phase 4 Evaluation, reliability (incl. eval in CI)
- [x] Module 7.3 completed (prereq for Phase 5)
- [x] Phase 5 Ship and operate (scheduled workflow, WIF, Pages, failure alert, verified live)
- [ ] README + slides
