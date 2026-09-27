# Plan: P1 Weekly Insights Report

| Field | Value |
|---|---|
| Updated | 2026-09-27 |
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

### Phase 4: Evaluation, reliability (core of the project) (DONE except eval in CI)
- Needs: Module 3, Module 4. DONE.
- Done: golden set (16 weeks), 10 deterministic guards, LLM-as-judge (judge_v1 to v4, calibrated), error analysis (`guard_review.md`), retry with feedback, fallback, held-out replay.
- DECIDED (2026-09-27): LangSmith tracing/dashboard deferred to P2. P1 is a manual weekly batch job, not live production traffic, so the homegrown stack (guards, judge, `run_log.jsonl`) is the final observability/eval answer here, not a placeholder for LangSmith. P2's chatbot has the real production-traffic use case for a tracing UI. See `P1_Decisions_Log.md` 2026-09-27 and Module 5 in the learning plan.
- Remaining: eval in CI (needs Module 7.3, folded into Phase 5 below).

### Phase 5: Ship and operate
- PREREQ: Module 7.3 (GitHub Actions). Module 7.4 (observability concepts) for run metrics.
- Not needed for P1: 7.1 FastAPI, 7.2 Docker, 7.5 Cloud Run (those go to P2).
- Tasks: scheduled workflow, Workload Identity Federation, GitHub Pages publish with archive, failure alert via GitHub issue, run metrics on report footer.

### Not used in P1
- Module 6 (RAG): deliberately unused. Explain why in the interview.

## Recommended order

- Now: Phases 1 and 2 (only completed modules needed).
- Phase 4 done except eval in CI, which lands with Phase 5.
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
- [x] Phase 1 Data and metrics (brief pipeline, charts, HTML report with commentary placeholders)
- [x] Phase 2 AI commentary: prompt v1, output format, Claude headless call, guards, retry with feedback, fallback, cache, run log, page
- [ ] Phase 3 Drill-down tools (optional)
- [x] Phase 4 Evaluation, reliability (eval in CI still open, folded into Phase 5)
- [ ] Module 7.3 completed (prereq for Phase 5)
- [ ] Phase 5 Ship and operate
- [ ] README + slides
