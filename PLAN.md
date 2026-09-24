# Plan: P1 Weekly Insights Report

| Field | Value |
|---|---|
| Updated | 2026-09-24 |
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
- Remaining: confirm $5 budget alert is saved.
- GAP: git/GitHub basics. Confirm comfortable.

### Phase 1: Data and metrics (IN PROGRESS)
- Needs: Module 1 (Python, JSON), Module 2 (classes), Module 2.5 (NumPy). DONE.
- GAP: pandas (assumed from DS background).
- Tasks: data brief schema, SQL, targets file, KPI calc, cuts, data-quality gates, data brief writer, Plotly charts.

### Phase 2: Automated LLM narrative
- Needs: Module 3 (LLM APIs, structured outputs). DONE. Module 2.5 (token/cost intuition). DONE.
- GAP: Pydantic for schema validation (also used in Module 7.1).
- Tasks: prompt v1, structured JSON output, retries with backoff, token and cost logging, first guards.

### Phase 3: Drill-down tools (OPTIONAL)
- Needs: Modules 3 and 4. DONE.
- Only if evals show the brief misses insights: let the model call `get_breakdown(metric, segment)`.

### Phase 4: Evaluation, tracing, reliability (core of the project)
- PREREQ: Module 5.
  - [x] Hamel Husain / Peter Yang evals video.
  - [ ] LangChain Academy, Building Reliable Agents (LangSmith, tracing, judge).
- Tasks: golden set (25+), deterministic checks, LLM-as-judge calibrated on your labels, error analysis with failure taxonomy, LangSmith tracing, template fallback, eval in CI.

### Phase 5: Ship and operate
- PREREQ: Module 7.3 (GitHub Actions). Module 7.4 (observability concepts) for run metrics.
- Not needed for P1: 7.1 FastAPI, 7.2 Docker, 7.5 Cloud Run (those go to P2).
- Tasks: scheduled workflow, Workload Identity Federation, GitHub Pages publish with archive, failure alert via GitHub issue, run metrics on report footer.

### Not used in P1
- Module 6 (RAG): deliberately unused. Explain why in the interview.

## Recommended order

- Now: Phases 1 and 2 (only completed modules needed), with the LangChain Academy course in parallel.
- Phase 4 after Module 5 is complete.
- Phase 5 after Module 7.3.

## Deliverables

- Repo README: objective, why, what, how, architecture, data, eval results, cost table, failure taxonomy, lessons.
- Eval report: before/after error analysis.
- Slides (later): problem, architecture, reliability loop, results, cost, demo.

## Checklist

- [x] Phase 0 Setup (budget alert confirmation pending)
- [x] PRD v0.3
- [x] business_context.md v0.1
- [x] KPI Spec v1 locked
- [~] Phase 1 Data and metrics (brief pipeline done; charts and HTML rendering next)
- [ ] Phase 2 Automated LLM narrative
- [ ] Phase 3 Drill-down tools (optional)
- [ ] Module 5 completed (prereq for Phase 4)
- [ ] Phase 4 Evaluation, tracing, reliability
- [ ] Module 7.3 completed (prereq for Phase 5)
- [ ] Phase 5 Ship and operate
- [ ] README + slides
