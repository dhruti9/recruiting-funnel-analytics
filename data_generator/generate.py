"""Generate a realistic, deliberately messy ATS extract.

Simulates requisitions opening, candidates applying and moving through the
hiring funnel, interviews, offers and hires, then injects the kinds of data
problems real ATS / HRIS integrations produce.

Usage:
    python data_generator/generate.py --out data/raw
"""
from __future__ import annotations

import argparse
import random
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

import config as C

rng = np.random.default_rng(C.SEED)
random.seed(C.SEED)
fake = Faker("en_US")
Faker.seed(C.SEED)

AS_OF = datetime.combine(C.AS_OF_DATE, datetime.max.time()).replace(microsecond=0)
STAGE_IDX = {s: i for i, s in enumerate(C.STAGES)}


def rand_dt(start: datetime, days_min: float, days_max: float) -> datetime:
    """Random business-hours timestamp between start+days_min and start+days_max."""
    d = start + timedelta(days=float(rng.uniform(days_min, days_max)))
    return d.replace(hour=int(rng.integers(8, 19)), minute=int(rng.integers(0, 60)), second=0, microsecond=0)


# ---------------------------------------------------------------------------
# Reference tables
# ---------------------------------------------------------------------------
def build_departments() -> pd.DataFrame:
    rows = []
    for i, (name, _) in enumerate(C.DEPARTMENTS, start=1):
        rows.append({
            "department_id": f"D{i:02d}",
            "department_name": name,
            "department_head": fake.name(),
            "cost_center": f"CC-{1000 + i * 10}",
        })
    return pd.DataFrame(rows)


def build_recruiters(depts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    dept_ids = depts["department_id"].tolist()
    weights = np.array([w for _, w in C.DEPARTMENTS])
    for i in range(1, C.N_RECRUITERS + 1):
        first, last = fake.first_name(), fake.last_name()
        rows.append({
            "recruiter_id": f"R{i:03d}",
            "recruiter_name": f"{first} {last}",
            "email": f"{first}.{last}@example.com".lower(),
            "primary_department_id": str(rng.choice(dept_ids, p=weights / weights.sum())),
            "title": str(rng.choice(["Recruiter", "Senior Recruiter", "Technical Recruiter", "Lead Recruiter"], p=[0.35, 0.3, 0.25, 0.1])),
            "start_date": fake.date_between(date(2019, 1, 1), date(2024, 6, 1)).isoformat(),
            "is_active": bool(rng.random() > 0.08),
        })
    return pd.DataFrame(rows)


def build_sources() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "source_id": sid, "source_name": name, "source_type": stype,
            "cost_per_application_usd": cpa, "fee_per_hire_usd": fph, "fee_pct_of_base_salary": pct,
        }
        for sid, name, stype, _share, _q, cpa, fph, pct in C.SOURCES
    ])


# ---------------------------------------------------------------------------
# Funnel simulation
# ---------------------------------------------------------------------------
def simulate_journey(applied_at: datetime, quality: float) -> list[tuple[str, datetime]]:
    """Return the list of (stage_or_terminal, timestamp) an application would take,
    ignoring requisition fill / cancellation and the snapshot date."""
    events = [("applied", applied_at)]
    t = applied_at
    for stage in C.STAGES[:-1]:
        lo, hi = C.STAGE_DAYS[stage]
        t = rand_dt(t, lo, hi)
        if rng.random() < C.STALL_RATES.get(stage, 0):
            return events  # nobody ever actioned it
        if stage != "offer" and rng.random() < C.WITHDRAW_RATES[stage]:
            events.append(("withdrawn", t))
            return events
        exponent = 0.6 if stage == "applied" else 0.35
        p = min(0.95, C.BASE_PASS_RATES[stage] * quality ** exponent)
        if rng.random() < p:
            events.append((C.STAGES[STAGE_IDX[stage] + 1], t))
        else:
            events.append(("declined" if stage == "offer" else "rejected", t))
            return events
    return events


def build_requisitions_and_applications(depts, recruiters, sources):
    dept_ids = depts["department_id"].tolist()
    dept_w = np.array([w for _, w in C.DEPARTMENTS]); dept_w = dept_w / dept_w.sum()
    levels = list(C.LEVELS)
    level_w = np.array([C.LEVELS[l][0] for l in levels]); level_w = level_w / level_w.sum()
    src_ids = [s[0] for s in C.SOURCES]
    src_w = np.array([s[3] for s in C.SOURCES]); src_w = src_w / src_w.sum()
    src_quality = {s[0]: s[4] for s in C.SOURCES}

    rec_by_dept = recruiters.groupby("primary_department_id")["recruiter_id"].apply(list).to_dict()
    all_recs = recruiters["recruiter_id"].tolist()

    window_days = (C.AS_OF_DATE - C.START_DATE).days
    reqs, apps, transitions = [], [], []
    app_seq = 0

    for r in range(1, C.N_REQUISITIONS + 1):
        req_id = f"REQ-{10000 + r}"
        dept = str(rng.choice(dept_ids, p=dept_w))
        level = str(rng.choice(levels, p=level_w))
        opened = datetime.combine(C.START_DATE, datetime.min.time()) + timedelta(days=float(rng.uniform(0, window_days - 20)))
        opened = opened.replace(hour=9, minute=0, second=0, microsecond=0)
        pool = rec_by_dept.get(dept, all_recs)
        recruiter = str(rng.choice(pool)) if rng.random() < 0.85 else str(rng.choice(all_recs))
        headcount = 2 if rng.random() < 0.12 else 1
        title = f"{fake.job()}".split(",")[0][:60]

        # simulate candidate journeys for this req
        n_apps = max(8, int(rng.lognormal(np.log(C.MEAN_APPS_PER_REQ) - 0.18, 0.6)))
        candidates = []
        for _ in range(n_apps):
            applied_at = rand_dt(opened, 0, 75)
            src = str(rng.choice(src_ids, p=src_w))
            candidates.append((applied_at, src, simulate_journey(applied_at, src_quality[src])))

        # who would be hired, in order of hire date
        hire_times = sorted(ev[-1][1] for _, _, ev in candidates if ev[-1][0] == "hired" and ev[-1][1] <= AS_OF)
        filled_at = hire_times[headcount - 1] if len(hire_times) >= headcount else None
        cancelled_at = None
        if filled_at is None and (AS_OF - opened).days > 200 and rng.random() < 0.55:
            cancelled_at = rand_dt(opened, 120, 190)
            if cancelled_at > AS_OF:
                cancelled_at = None
        close_at = filled_at or cancelled_at
        status = "filled" if filled_at else ("cancelled" if cancelled_at else "open")
        hires_so_far = 0

        for applied_at, src, events in sorted(candidates, key=lambda c: c[0]):
            if close_at and applied_at > close_at + timedelta(days=14):
                continue  # posting was taken down
            if applied_at > AS_OF:
                continue
            app_seq += 1
            app_id = f"APP-{app_seq:06d}"
            kept: list[tuple[str, datetime]] = []
            terminal_reason = None
            for stage, ts in events:
                if stage == "applied":
                    kept.append((stage, ts)); continue
                if stage == "hired" and hires_so_far >= headcount:
                    kept.append(("rejected", ts)); terminal_reason = "Position filled"; break
                if close_at and ts > close_at and stage not in ("rejected", "withdrawn", "declined"):
                    t_close = max(close_at, kept[-1][1] if kept else applied_at) + timedelta(hours=int(rng.integers(2, 72)))
                    if t_close <= AS_OF:
                        kept.append(("rejected", t_close))
                        terminal_reason = "Position filled" if status == "filled" else "Requisition cancelled"
                    break
                if ts > AS_OF:
                    break  # still in flight at the snapshot
                kept.append((stage, ts))
                if stage == "hired":
                    hires_so_far += 1

            # stalled application on a req that has since closed -> bulk-rejected at close
            if kept[-1][0] in STAGE_IDX and kept[-1][0] != "hired" and close_at and close_at <= AS_OF \
                    and len(kept) == len(events):
                t_close = max(close_at, kept[-1][1]) + timedelta(hours=int(rng.integers(2, 72)))
                if t_close <= AS_OF:
                    kept.append(("rejected", t_close))
                    terminal_reason = "Position filled" if status == "filled" else "Requisition cancelled"

            last_stage, last_ts = kept[-1]
            stages_reached = [s for s, _ in kept if s in STAGE_IDX]
            current_stage = stages_reached[-1]
            if last_stage in ("rejected", "withdrawn", "declined", "hired"):
                app_status = {"declined": "offer_declined"}.get(last_stage, last_stage)
            else:
                app_status = "active"

            reason = None
            if app_status == "rejected":
                if terminal_reason:
                    reason = terminal_reason
                else:
                    opts = C.REJECT_REASONS[current_stage]
                    w = np.array([0.6, 0.3, 0.1][:len(opts)]); w = w / w.sum()
                    reason = str(rng.choice(opts, p=w))
            elif app_status == "withdrawn":
                reason = "Candidate withdrew"
            elif app_status == "offer_declined":
                reason = str(rng.choice(["Accepted competing offer", "Compensation", "Relocation", "Counter-offer from current employer"]))

            apps.append({
                "application_id": app_id, "requisition_id": req_id, "source_id": src,
                "applied_at": applied_at, "current_stage": current_stage, "status": app_status,
                "reject_reason": reason,
                "hired_at": last_ts if app_status == "hired" else None,
                "last_activity_at": last_ts, "level": level,
            })
            prev = None
            for stage, ts in kept:
                transitions.append({"application_id": app_id, "from_stage": prev, "to_stage": stage, "transitioned_at": ts})
                prev = stage

        reqs.append({
            "requisition_id": req_id, "job_title": title, "department_id": dept, "recruiter_id": recruiter,
            "hiring_manager": fake.name(), "location": str(rng.choice(C.LOCATIONS)), "job_level": level,
            "headcount": headcount, "opened_at": opened, "status": status,
            "filled_at": filled_at if status == "filled" else None,
            "closed_at": close_at,
        })

    return pd.DataFrame(reqs), pd.DataFrame(apps), pd.DataFrame(transitions)


def build_candidates(apps: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Assign people to applications (some apply to several reqs)."""
    n_apps = len(apps)
    n_people = int(n_apps * 0.84)
    person_for_app = np.concatenate([np.arange(n_people), rng.integers(0, n_people, n_apps - n_people)])
    rng.shuffle(person_for_app)
    apps = apps.copy()
    apps["candidate_id"] = [f"CAN-{p + 1:06d}" for p in person_for_app]

    first_seen = apps.groupby("candidate_id")["applied_at"].min()
    rows = []
    for cid, created in first_seen.items():
        first, last = fake.first_name(), fake.last_name()
        rows.append({
            "candidate_id": cid, "first_name": first, "last_name": last,
            "email": f"{first}.{last}{rng.integers(1, 999)}@{rng.choice(['gmail.com', 'outlook.com', 'yahoo.com', 'icloud.com'])}".lower(),
            "phone": fake.numerify("(###) ###-####"),
            "city": fake.city(), "state": fake.state_abbr(),
            "created_at": created - timedelta(minutes=int(rng.integers(1, 30))),
        })
    return pd.DataFrame(rows), apps


def build_interviews_and_offers(apps, trans, recruiters, reqs):
    interviews, offers = [], []
    int_seq = off_seq = 0
    level_by_req = reqs.set_index("requisition_id")["job_level"].to_dict()
    trans_by_app = {k: v for k, v in trans.groupby("application_id")}
    interviewers = [fake.name() for _ in range(400)]

    for app in apps.itertuples():
        t = trans_by_app[app.application_id].sort_values("transitioned_at")
        rows = list(t.itertuples())
        for i, row in enumerate(rows):
            stage = row.to_stage
            if stage in C.INTERVIEWS_PER_STAGE:
                stage_end = rows[i + 1].transitioned_at if i + 1 < len(rows) else AS_OF
                if i + 1 >= len(rows):
                    continue  # still waiting to be scheduled
                for itype, n in C.INTERVIEWS_PER_STAGE[stage]:
                    for _ in range(n):
                        int_seq += 1
                        span = max((stage_end - row.transitioned_at).total_seconds() / 86400, 0.2)
                        sched = row.transitioned_at + timedelta(days=float(rng.uniform(0.1, span * 0.9)))
                        interviews.append({
                            "interview_id": f"INT-{int_seq:07d}", "application_id": app.application_id,
                            "interview_stage": stage, "interview_type": itype,
                            "scheduled_at": sched.replace(second=0, microsecond=0),
                            "interviewer_name": str(rng.choice(interviewers)),
                            "score": int(rng.choice([1, 2, 3, 4], p=[0.15, 0.3, 0.35, 0.2])),
                            "feedback_submitted": bool(rng.random() > 0.06),
                        })
            if stage == "offer":
                off_seq += 1
                lvl = level_by_req[app.requisition_id]
                _, lo, hi = C.LEVELS[lvl]
                nxt = rows[i + 1] if i + 1 < len(rows) else None
                if nxt is None:
                    status, responded = "pending", None
                elif nxt.to_stage == "hired":
                    status, responded = "accepted", row.transitioned_at + (nxt.transitioned_at - row.transitioned_at) * float(rng.uniform(0.3, 0.9))
                elif nxt.to_stage == "declined":
                    status, responded = "declined", nxt.transitioned_at
                else:
                    status, responded = "rescinded", nxt.transitioned_at
                offers.append({
                    "offer_id": f"OFF-{off_seq:06d}", "application_id": app.application_id,
                    "extended_at": row.transitioned_at, "responded_at": responded, "offer_status": status,
                    "base_salary_usd": int(round(rng.uniform(lo, hi), -3)),
                    "sign_on_bonus_usd": int(rng.choice([0, 0, 5000, 10000, 15000])),
                })
    return pd.DataFrame(interviews), pd.DataFrame(offers)


# ---------------------------------------------------------------------------
# Mess injection
# ---------------------------------------------------------------------------
def inject_mess(cands, apps, trans, interviews, offers, reqs):
    M = C.MESS
    log = {}

    # 1. missing reject reasons
    rej = apps.index[apps["status"] == "rejected"]
    idx = rng.choice(rej, int(len(rej) * M["missing_reject_reason"]), replace=False)
    apps.loc[idx, "reject_reason"] = None
    log["missing_reject_reason"] = len(idx)

    # 2. missing source
    idx = rng.choice(apps.index, int(len(apps) * M["missing_source"]), replace=False)
    apps.loc[idx, "source_id"] = None
    log["missing_source"] = len(idx)

    # 3. null hire dates (the 'hired' stage transition still exists, so it is recoverable)
    hired = apps.index[apps["status"] == "hired"]
    idx = rng.choice(hired, max(1, int(len(hired) * M["null_hire_date"])), replace=False)
    apps.loc[idx, "hired_at"] = None
    log["null_hire_date"] = len(idx)

    # 4. hires whose offer is still 'pending' (offer system never synced)
    hired_ids = set(apps.loc[apps["status"] == "hired", "application_id"])
    acc = offers.index[(offers["offer_status"] == "accepted") & offers["application_id"].isin(hired_ids)]
    idx = rng.choice(acc, max(1, int(len(acc) * M["hire_without_accepted_offer"])), replace=False)
    offers.loc[idx, ["offer_status", "responded_at"]] = ["pending", None]
    log["hire_without_accepted_offer"] = len(idx)

    # 5. offers with no interview records
    off_apps = offers["application_id"].unique()
    drop_apps = set(rng.choice(off_apps, max(1, int(len(off_apps) * M["offer_without_interviews"])), replace=False))
    interviews = interviews[~interviews["application_id"].isin(drop_apps)].reset_index(drop=True)
    log["offer_without_interviews"] = len(drop_apps)

    # 6. out-of-order stage timestamps: push a later stage before the previous one
    multi = trans.groupby("application_id").size()
    eligible = multi[multi >= 3].index.to_numpy()
    bad_apps = rng.choice(eligible, int(len(eligible) * M["out_of_order_transitions"]), replace=False)
    for a in bad_apps:
        rows = trans.index[trans["application_id"] == a]
        target = rows[-1] if rng.random() < 0.5 else rows[len(rows) // 2]
        prev_ts = trans.loc[rows[list(rows).index(target) - 1], "transitioned_at"]
        trans.loc[target, "transitioned_at"] = prev_ts - timedelta(days=float(rng.uniform(1, 6)))
    log["out_of_order_transitions"] = len(bad_apps)

    # 7. exact duplicate transition rows (re-sync)
    dup = trans.sample(frac=M["duplicate_transition_rows"], random_state=C.SEED)
    trans = pd.concat([trans, dup]).sort_values(["application_id", "transitioned_at"], kind="stable").reset_index(drop=True)
    log["duplicate_transition_rows"] = len(dup)

    # 8. duplicate candidates: a second profile for the same person
    multi_app = apps.groupby("candidate_id").size()
    multi_app = multi_app[multi_app >= 2].index.to_numpy()
    n_dup = int(len(cands) * M["duplicate_candidates"])
    dup_ids = rng.choice(multi_app, min(n_dup, len(multi_app)), replace=False)
    new_rows = []
    next_id = len(cands) + 1
    for cid in dup_ids:
        orig = cands.loc[cands["candidate_id"] == cid].iloc[0].to_dict()
        new_id = f"CAN-{next_id:06d}"; next_id += 1
        variant = orig.copy()
        variant["candidate_id"] = new_id
        variant["email"] = rng.choice([orig["email"].upper(), f" {orig['email']} ", orig["email"].capitalize()])
        variant["phone"] = orig["phone"].replace("(", "").replace(") ", "-")
        variant["created_at"] = orig["created_at"] + timedelta(days=int(rng.integers(5, 200)))
        new_rows.append(variant)
        # move this person's latest application to the duplicate profile
        their_apps = apps.index[apps["candidate_id"] == cid]
        latest = apps.loc[their_apps, "applied_at"].idxmax()
        apps.loc[latest, "candidate_id"] = new_id
        variant["created_at"] = min(variant["created_at"], apps.loc[latest, "applied_at"])
    cands = pd.concat([cands, pd.DataFrame(new_rows)], ignore_index=True)
    log["duplicate_candidates"] = len(new_rows)

    # 9. filled requisitions missing filled_at
    filled = reqs.index[reqs["status"] == "filled"]
    idx = rng.choice(filled, int(len(filled) * M["filled_req_missing_date"]), replace=False)
    reqs.loc[idx, "filled_at"] = None
    log["filled_req_missing_date"] = len(idx)

    return cands, apps, trans, interviews, offers, reqs, log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/raw")
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    depts = build_departments()
    recruiters = build_recruiters(depts)
    sources = build_sources()
    reqs, apps, trans = build_requisitions_and_applications(depts, recruiters, sources)
    cands, apps = build_candidates(apps)
    interviews, offers = build_interviews_and_offers(apps, trans, recruiters, reqs)
    cands, apps, trans, interviews, offers, reqs, log = inject_mess(cands, apps, trans, interviews, offers, reqs)

    trans.insert(0, "transition_id", [f"TR-{i:07d}" for i in range(1, len(trans) + 1)])
    apps = apps[["application_id", "candidate_id", "requisition_id", "source_id", "applied_at", "current_stage",
                 "status", "reject_reason", "hired_at", "last_activity_at"]]

    tables = {
        "departments": depts, "recruiters": recruiters, "sources": sources, "requisitions": reqs,
        "candidates": cands, "applications": apps, "stage_transitions": trans,
        "interviews": interviews, "offers": offers,
    }
    for name, df in tables.items():
        df.to_csv(out / f"{name}.csv", index=False)
        print(f"  {name:<18} {len(df):>8,} rows")
    print("Injected data-quality issues:")
    for k, v in log.items():
        print(f"  {k:<30} {v:>6,}")


if __name__ == "__main__":
    main()
