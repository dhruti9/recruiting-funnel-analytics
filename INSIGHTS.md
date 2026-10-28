# Recruiting Funnel Review — What the Data Says

**To:** Head of Talent Acquisition  **Period:** Jan 2024 – Sep 2026  **Scope:** 50,268 applications · 760 requisitions · 445 hires

> Figures come from the synthetic dataset in this repo and are reproducible with `make all`. The structure of the memo is what I would send a recruiting leader after a funnel review.

---

## The short version

1. **Referrals are our best source by a wide margin.** Referred candidates are hired at **4.9x the rate of job-board applicants** (23 vs. 5 hires per 1,000 applications). Referrals and internal moves are 12% of applicants but **31% of hires**.
2. **The onsite is where the process leaks.** Only **24% of candidates who complete an onsite get an offer**, the lowest pass rate of any interview stage. Each onsite candidate costs about 6 interviews, so roughly **10,700 interviews** went to candidates who did not get an offer. Half of onsite rejections are for failing the technical interview.
3. **Agencies take half the budget for 6% of hires.** Agency fees were **53% of sourcing spend** ($774K of $1.47M) for 28 hires, or **$27.6K per hire** versus $3.0K for a referral.
4. **The pipeline needs cleaning.** **55% of active applications** (553 of 997) have not been touched in over 60 days, and **151 of 228 open requisitions** have been open for more than six months.

## What I recommend

| # | Action | Owner | Expected impact |
|---|---|---|---|
| 1 | Raise the referral bonus and run a quarterly referral drive for the hardest-to-fill roles | TA leadership | At historical conversion rates, moving 5% of applicants from job boards to referrals would have produced about 47 more hires (+10%) from the same applicant volume |
| 2 | Add a short technical assessment **before** the onsite for engineering roles; recalibrate hiring-manager screens against onsite outcomes | Hiring managers + recruiting ops | Lift onsite→offer conversion and give back interviewer hours |
| 3 | Use agencies only for named hard-to-fill roles, with a cap per quarter | TA leadership + finance | Most of the $774K is addressable |
| 4 | Close or re-approve every req open for more than 180 days; bulk-disposition applications older than 60 days | Recruiters | Accurate workload numbers and a better candidate experience |

## Supporting numbers

**Funnel (all sources)**

| Stage | Candidates | Advance to next stage |
|---|---:|---:|
| Applied | 50,268 | 23% |
| Recruiter screen | 11,365 | 48% |
| Hiring-manager screen | 5,349 | 45% |
| **Onsite** | **2,357** | **24%** |
| Offer | 552 | 81% accept |
| Hired | 445 | |

**Speed.** Median time to fill is **64 days** from requisition open to hire, and it has held flat over the last 12 months (63 days). Legal and Finance are the slowest at about 76 days. Median time to hire is **35 days** from application, with little difference between sources.

**Offers.** **86% of offers are accepted.** Declines are spread across relocation (21), counter-offers (19), competing offers (16) and compensation (15). No single cause dominates, so a broad compensation change is not indicated.

## A caveat on data quality

Some of these numbers are less precise than they should be because of gaps in our source systems. The full list, with owners and fixes, is in `dq_upstream_gap_report`.

- **11% of rejections have no reason recorded.** This is the biggest blind spot in the drop-off analysis. *Ask:* make rejection reason a required field in the ATS (Talent Systems).
- **2% of applications have no source.** These are reported as "Unattributed" so they are counted, not dropped. *Ask:* require source on application create.
- **1,694 duplicate candidate profiles.** These are merged on email before counting, so candidate counts are correct.
- **6 hires show a "pending" offer** in Offer Management. These are corrected using the ATS hire record. *Ask:* fix the offer-status sync (Total Rewards Systems).

None of these change the conclusions above, but fixing the first two would make the next review sharper.
