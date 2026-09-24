# Business Context: TheLook Weekly Report

Version: v0.2 (2026-09-24)
Purpose: this file is loaded into the LLM prompt every week. It holds stable facts about the business and the KPIs. It never contains this week's numbers (those come only from the data brief). Writing instructions and the output format live in the prompt file, not here.

## 1. The business

- TheLook is an online clothing retailer selling men's and women's apparel and accessories.
- Customers are worldwide. The largest customer bases are in APAC and North America, followed by EMEA and LATAM.
- Customers arrive through five traffic sources: Search (the largest by far), Organic, Facebook, Email, and Display.
- An order contains 1 to 4 items. An order moves through these statuses: Processing, Shipped, Complete, and it may end as Cancelled or Returned.

## 2. Audience for the report

- Readers: Head of E-commerce (primary), Marketing lead, Finance and planning.
- They read the report on Monday morning and want to know within 2 minutes: was last week good or bad, are we on plan, and what should we keep an eye on.
- They are business readers, not analysts. Plain language, no statistical jargon.

## 3. Reporting conventions

- Reporting week: Monday 00:00 to Sunday 23:59 UTC. The report always covers the latest completed week.
- "WoW" means the reporting week compared with the week before it.
- "YoY" means the reporting week compared with the same week last year. YoY growth can be compared with the 75% growth the plan assumed.
- Changes in counts and money are shown in percent (%). Changes in rates are shown in percentage points (pp). Example: a cancellation rate moving from 14.0% to 15.5% is "+1.5 pp", not "+10.7%".
- Money is in US dollars.

## 4. KPI glossary

| KPI | What it means | Higher is |
|---|---|---|
| Weekly Orders Placed | Number of orders customers placed in the week, whatever their later status | Good |
| Weekly Gross Revenue (excl. cancelled) | Value of items sold in the week, excluding cancelled items. Returns are NOT subtracted, so this is not net revenue | Good |
| Weekly Average Order Value (AOV) | Average revenue per non-cancelled order | Good |
| Weekly Order Cancellation Rate | Share of the week's orders that were cancelled | Bad |
| 14-Day Return Rate | Share of the week's orders that the customer returned within 14 days of placing the order (order date to return date). Customer behavior only, nothing to do with inventory or warehouse receipt. Reported for an EARLIER week (about 2 weeks before the reporting week), so every order in that week has had the full 14 days to be returned. It always refers to the week named in the data brief, never the reporting week | Bad |
| Weekly New Customer Signups | Number of new customer accounts created in the week | Good |
| Weekly Orders vs Target | Orders as a percentage of the plan target for the week. Above 100% means ahead of plan | Good |
| Weekly Gross Revenue vs Target | Revenue as a percentage of the plan target for the week. Above 100% means ahead of plan | Good |
| Quarter-to-Date (QTD) Gross Revenue vs Target | Revenue so far this quarter as a percentage of the plan for the same weeks | Good |

## 5. Targets (the plan)

- Targets come from the annual plan, set at the start of the year. They are not forecasts and are not updated during the year.
- The 2026 plan assumes 75% growth over the same week last year, so targets follow last year's seasonal pattern.
- Growth vs last week and performance vs plan are different questions. A week can be up WoW and still behind plan, or down WoW and still ahead of plan.
- A strong week does not mean the quarter is on track. QTD attainment is the measure for the quarter.
- Targets exist for every week through the end of 2026, so next week's target and the full-quarter plan are known in advance.

## 6. Cuts

- Traffic source: Search, Organic, Facebook, Email, Display. A customer's traffic source is how they originally arrived at the site.
- Region:
  - APAC: China, South Korea, Japan, Australia
  - North America: United States
  - EMEA: France, United Kingdom, Germany, Spain, Belgium, Poland, Austria
  - LATAM: Brazil, Colombia
- Cuts are shown for Weekly Orders Placed and Weekly Gross Revenue only.
- "Biggest driver" means the segment with the largest contribution to the total change, as given in the data brief. It is not necessarily the segment with the largest percent change (small segments can swing a lot in percent while contributing little).

## 7. How to interpret the data

- Anomaly flags in the data brief are computed by code. When a flag is present, treat the movement as unusual and say so. Do not present it as normal business growth or decline.
- Small changes are normal week-to-week noise. The data brief marks which changes are notable; do not dramatize changes it does not mark.
- The data describes what happened, not why. There is no information about campaigns, pricing, promotions, stock levels, or competitors, so causes cannot be stated.
- A "So what" is the business implication of a fact: what it means for the plan, the quarter, revenue, or how to read other numbers. It must follow from facts in the data brief (for example the revenue value of one percentage point of cancellations, the amount still needed to reach the quarterly plan, or a comparison between two KPIs). It is never a cause and never an instruction to act.
- Recent orders are still being processed and shipped. Status-based measures other than cancellations and the 14-Day Return Rate are not reported for this reason.
