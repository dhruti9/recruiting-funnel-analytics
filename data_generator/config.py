"""Static reference data and tuning knobs for the synthetic ATS generator.

Everything that shapes the "story" in the data (source quality, stage pass
rates, how much mess to inject) lives here so it can be tuned without
touching the simulation logic.
"""
from datetime import date

SEED = 42
START_DATE = date(2024, 1, 1)
AS_OF_DATE = date(2026, 9, 30)  # snapshot date of the ATS extract

N_REQUISITIONS = 760
MEAN_APPS_PER_REQ = 72  # ~50K applications in total
N_RECRUITERS = 28

# Ordered hiring funnel. Index = stage order.
STAGES = ["applied", "recruiter_screen", "hiring_manager_screen", "onsite", "offer", "hired"]

# Base probability of moving from stage[i] to stage[i+1]
BASE_PASS_RATES = {
    "applied": 0.27,
    "recruiter_screen": 0.52,
    "hiring_manager_screen": 0.50,
    "onsite": 0.27,        # deliberately the biggest drop-off
    "offer": 0.82,         # offer acceptance
}

# Probability a candidate withdraws while sitting in a stage
# Probability an application is never reviewed (sits in a stage until the req closes)
STALL_RATES = {"applied": 0.05, "recruiter_screen": 0.03, "hiring_manager_screen": 0.02}

WITHDRAW_RATES = {
    "applied": 0.02,
    "recruiter_screen": 0.05,
    "hiring_manager_screen": 0.05,
    "onsite": 0.04,
}

# Days spent in each stage before a decision: (min, max)
STAGE_DAYS = {
    "applied": (1, 12),
    "recruiter_screen": (2, 9),
    "hiring_manager_screen": (3, 12),
    "onsite": (5, 16),
    "offer": (2, 9),
}

DEPARTMENTS = [
    # name, share of requisitions
    ("Software Engineering", 0.17),
    ("Vehicle Engineering", 0.12),
    ("Manufacturing", 0.16),
    ("Supply Chain", 0.08),
    ("Energy Products", 0.07),
    ("Sales & Delivery", 0.10),
    ("Service", 0.09),
    ("Data & AI", 0.06),
    ("Finance", 0.04),
    ("People", 0.04),
    ("Legal", 0.02),
    ("IT", 0.05),
]

LOCATIONS = ["Austin, TX", "Fremont, CA", "Palo Alto, CA", "Sparks, NV", "Buffalo, NY", "Remote - US"]

LEVELS = {
    # level: (share, salary_min, salary_max)
    "P1": (0.18, 70_000, 95_000),
    "P2": (0.30, 95_000, 130_000),
    "P3": (0.27, 125_000, 170_000),
    "P4": (0.17, 160_000, 215_000),
    "P5": (0.08, 205_000, 280_000),
}

# source_id, name, type, share of applications, quality multiplier,
# cost per application (USD), flat fee per hire (USD), fee as % of base salary
SOURCES = [
    ("SRC01", "Employee Referral", "referral", 0.08, 1.70, 0.0, 3000.0, 0.0),
    ("SRC02", "Careers Site", "inbound", 0.20, 1.00, 2.0, 0.0, 0.0),
    ("SRC03", "LinkedIn Jobs", "job_board", 0.22, 0.90, 14.0, 0.0, 0.0),
    ("SRC04", "Indeed", "job_board", 0.25, 0.75, 7.0, 0.0, 0.0),
    ("SRC05", "Outbound Sourcing", "sourced", 0.09, 1.35, 22.0, 0.0, 0.0),
    ("SRC06", "Agency", "agency", 0.04, 1.45, 0.0, 0.0, 0.20),
    ("SRC07", "University Recruiting", "campus", 0.08, 0.95, 18.0, 0.0, 0.0),
    ("SRC08", "Internal Mobility", "internal", 0.04, 1.80, 0.0, 0.0, 0.0),
]

REJECT_REASONS = {
    "applied": ["Does not meet minimum qualifications", "Location / work authorization mismatch", "Duplicate application"],
    "recruiter_screen": ["Compensation misalignment", "Not a fit for role", "Unresponsive to outreach"],
    "hiring_manager_screen": ["Insufficient technical depth", "Experience level mismatch"],
    "onsite": ["Did not pass technical interview", "Did not pass values interview", "Stronger candidate selected"],
}

INTERVIEWS_PER_STAGE = {
    "recruiter_screen": [("phone_screen", 1)],
    "hiring_manager_screen": [("hiring_manager", 1)],
    "onsite": [("technical", 2), ("cross_functional", 1), ("values", 1)],
}

# ---------------------------------------------------------------------------
# Deliberate data-quality problems (share of eligible records affected)
# ---------------------------------------------------------------------------
MESS = {
    "missing_reject_reason": 0.11,       # rejected applications with NULL reason
    "out_of_order_transitions": 0.015,   # applications with a backwards timestamp
    "duplicate_transition_rows": 0.006,  # exact duplicate rows from a re-sync
    "duplicate_candidates": 0.04,        # same person, second candidate_id
    "null_hire_date": 0.025,             # hired applications with NULL hired_at
    "offer_without_interviews": 0.012,   # offers whose interview records are missing
    "hire_without_accepted_offer": 0.015,  # offer stuck in 'pending' after hire
    "missing_source": 0.02,              # applications with NULL source_id
    "filled_req_missing_date": 0.03,     # 'filled' reqs with NULL filled_at
}
