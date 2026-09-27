# How the weekly report is built

One command runs everything for one week: `python scripts/build_report.py --week 2026-08-03`.

Colors: green = built, grey = Phase 4 and 5 (later). Phase 2 completed 2026-09-25.

Browser view: open `docs/architecture.html` (regenerate it after editing `docs/architecture.mmd` with `python scripts/build_architecture_html.py`).

```mermaid
flowchart TD
    %% ---------- inputs ----------
    subgraph IN["Inputs"]
        BQ[("BigQuery public data<br/>orders, order_items, users")]
        TGT["targets/weekly_targets_2026.csv<br/>frozen weekly targets"]
        LAY["report_layout.yaml<br/>page sections + AI slots"]
        CTX["business_context.md<br/>business facts for Claude"]
        PR["prompts/commentary_v1.md<br/>instructions for Claude"]
    end

    %% ---------- data: phase 1 ----------
    subgraph DATA["1. Data (build the numbers)"]
        S1["Step 1: Pick the weeks<br/>weeks.py"]
        S2["Step 2: Run one SQL query<br/>weekly_facts.sql via bq.py"]
        S3["Step 3: Weekly totals + cuts<br/>split_facts, add_kpis"]
        S4["Step 4: Build the data brief<br/>KPIs, targets, cuts, flags, so-what facts"]
        S5{"Step 5: 6 data-quality checks<br/>all pass?"}
        STOP(["Stop: no report"])
        S6["Step 6: Save the brief<br/>briefs/brief_week.json"]
    end

    %% ---------- AI: phase 2 ----------
    subgraph AI["2. AI commentary (write the text)"]
        S7["Step 7: Assemble the prompt<br/>prompt + business context + brief + output format"]
        S8["Step 8: Call Claude (headless)<br/>returns JSON + tokens, time, cost"]
        S9{"Step 9: Guards<br/>numbers, direction words,<br/>so-what, banned words"}
        S9R["Retry once"]
        S9F["Template fallback<br/>labelled 'commentary unavailable'"]
        S10["Step 10: Log the run<br/>checks, model, tokens, cost"]
    end

    %% ---------- page: phase 1 ----------
    subgraph PAGE["3. Page (show it)"]
        S11["Step 11: Chart data<br/>chart_data.py, never sent to Claude"]
        S12["Step 12: Render HTML<br/>render.py + template + layout"]
        OUT["site/reports/report_week.html<br/>+ site/index.html"]
    end

    %% ---------- later ----------
    subgraph LATER["4. Prove it + 5. Publish"]
        EV["Phase 4: Evals<br/>run steps 7 to 9 on ~25 saved briefs,<br/>score, error analysis, prompt v2, v3"]
        TR["Phase 4: Traces<br/>LangSmith records every call"]
        PUB["Phase 5: GitHub Pages<br/>public link for interviewers"]
    end

    BQ --> S2
    S1 --> S2 --> S3 --> S4
    TGT --> S4
    S4 --> S5
    S5 -- "no" --> STOP
    S5 -- "yes" --> S6
    S6 --> S7
    PR --> S7
    CTX --> S7
    LAY -- "slots become the output format" --> S7
    S7 --> S8 --> S9
    S9 -- "pass" --> S10
    S9 -- "fail" --> S9R --> S8
    S9R -. "fails again" .-> S9F --> S10
    S10 --> S12
    S3 --> S11 --> S12
    LAY --> S12
    S12 --> OUT
    S6 -. "saved briefs = golden set" .-> EV
    S8 -. "every call" .-> TR
    OUT -.-> PUB

    classDef done fill:#e7f5ea,stroke:#1d6b33,color:#0b0b0b
    classDef next fill:#fff4d6,stroke:#b07d00,color:#0b0b0b
    classDef later fill:#f0efec,stroke:#898781,color:#52514e
    classDef input fill:#eef4fc,stroke:#2a78d6,color:#0b0b0b
    class BQ,TGT,LAY,CTX input
    class PR input
    class S1,S2,S3,S4,S5,S6,S7,S8,S9,S9R,S9F,S10,S11,S12,OUT,STOP done
    class EV,TR,PUB later
```

## Step by step

| Step | What happens | Code / file | Why it exists | Status |
|---|---|---|---|---|
| 1 | Work out the reporting week, prior week, same week last year, mature week (for returns), quarter and fiscal-year weeks | `weeks.py` | Every number depends on picking the right weeks | Built |
| 2 | Run one SQL query: orders, cancellations, 14-day returns, revenue, signups per week x country x traffic source | `sql/weekly_facts.sql`, `bq.py` | One scan (~31 MB), capped at 500 MB so a mistake can never cost money | Built |
| 3 | Sum the rows into weekly totals; keep 3 weeks for region and traffic cuts; derive AOV and rates | `brief.py` (`split_facts`, `add_kpis`) | Rates and AOV are computed once, rounded exactly as shown | Built |
| 4 | Build the data brief: 6 KPIs with WoW, YoY, ITPY and good/bad; weekly, QTD, YTD and monthly vs target; cuts; flags; so-what facts | `brief.py`, `rules.py`, `targets.py` | The brief is the only thing Claude sees, so every number and judgement is decided here by code | Built |
| 5 | Run 6 data-quality checks (week complete, no missing weeks, targets present, countries mapped, row count sane, mature week ready) | `brief.py` (`quality_checks`) | Bad data stops the run before any AI or page is produced | Built |
| 6 | Validate the brief against its schema and save it | `models.py`, `briefs/` | A malformed brief can never reach Claude; saved briefs become the golden set for evals | Built |
| 7 | Assemble the prompt: instructions + business context + brief + output format (from the layout's AI slots) | `prompts/commentary_v1.md`, `commentary_schema.py`, `report_layout.yaml` | Versioned prompt, so we can show which version scored better; the output format always matches the page's boxes | Built |
| 8 | Call Claude headless once; get JSON commentary plus tokens, time and cost | `llm.py` (`generate()`), `scripts/generate_commentary.py` | Clean, measurable call; can be swapped for the API later | Built |
| 9 | Guards check the text: every number in the brief, direction words match, every point has a so-what, no causes, recommendations or "plan". Fail: retry once, then a labelled template | `guards.py`, `commentary.py` | A wrong number is never published | Built |
| 10 | Log the run: checks passed, model, prompt version, tokens, cost, time | `commentary.log_run` -> `runs/run_log.jsonl` | Observability and cost tracking; feeds the trust panel | Built |
| 11 | Build chart series from the weekly data and targets | `chart_data.py` | Charts need 52 weeks and future targets; Claude never sees this | Built |
| 12 | Render the HTML page from the layout, brief, charts and commentary | `render.py`, `templates/` | The report leadership reads | Built |
| Evals | Run steps 7 to 9 on ~25 saved briefs at once; score, read failures, improve the prompt | Phase 4 | Proves reliability with evidence | Later |
| Traces | Record every Claude call in LangSmith | Phase 4 | See exactly what Claude saw and said | Later |
| Publish | Put `site/` on GitHub Pages | Phase 5 | A link to share | Later |
