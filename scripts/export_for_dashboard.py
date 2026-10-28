"""Export dashboard-ready marts to CSV (for Tableau Public / Power BI) and render
static preview charts for the README.

Run after `dbt build`:
    python scripts/export_for_dashboard.py
"""
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "dbt_project" / "recruiting.duckdb"
DATA_OUT = ROOT / "dashboard" / "data"
IMG_OUT = ROOT / "dashboard" / "img"

EXPORTS = {
    "kpi_stage_conversion": "kpis.kpi_stage_conversion",
    "kpi_stage_dropoff": "kpis.kpi_stage_dropoff",
    "kpi_time_to_fill": "kpis.kpi_time_to_fill",
    "kpi_time_to_hire": "kpis.kpi_time_to_hire",
    "kpi_offer_acceptance": "kpis.kpi_offer_acceptance",
    "kpi_source_effectiveness": "kpis.kpi_source_effectiveness",
    "kpi_pipeline_aging": "kpis.kpi_pipeline_aging",
    "kpi_recruiter_workload": "kpis.kpi_recruiter_workload",
    "dq_upstream_gap_report": "data_quality.dq_upstream_gap_report",
    "dq_scorecard": "data_quality.dq_scorecard",
    "dim_requisition": "core.dim_requisition",
}

INK, MUTED, GRID = "#1f2937", "#6b7280", "#e5e7eb"
BLUE, BLUE_LIGHT, ORANGE, RED, GREEN = "#2563eb", "#93c5fd", "#ea580c", "#dc2626", "#16a34a"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
    "axes.titleweight": "bold", "axes.titlesize": 12, "axes.titlelocation": "left", "figure.dpi": 150,
})

STAGE_LABELS = {
    "applied": "Applied", "recruiter_screen": "Recruiter screen", "hiring_manager_screen": "HM screen",
    "onsite": "Onsite", "offer": "Offer", "hired": "Hired",
}


def funnel(con):
    df = con.sql("""
        select from_stage, entered, conversion_rate from kpis.kpi_stage_conversion
        where source_name = 'All sources' order by stage_order
    """).df()
    hires = con.sql("select count(*) from core.fct_applications where is_hired").fetchall()[0][0]
    labels = [STAGE_LABELS[s] for s in df.from_stage] + ["Hired"]
    counts = list(df.entered) + [hires]
    rates = list(df.conversion_rate)
    worst = min(range(1, len(rates)), key=lambda i: rates[i])  # ignore the top-of-funnel screen

    fig, ax = plt.subplots(figsize=(8, 4))
    y = range(len(labels))[::-1]
    ax.barh(list(y), counts, color=BLUE, height=0.62, log=True)
    for yi, c in zip(y, counts):
        ax.text(c * 1.12, yi, f"{c:,}", va="center", color=INK, fontsize=9)
    for i, r in enumerate(rates):
        color = RED if i == worst else MUTED
        ax.text(1.4, list(y)[i] - 0.5, f"↓ {r:.0%} advance", va="center", fontsize=8.5, color=color,
                fontweight="bold" if i == worst else "normal")
    ax.set_yticks(list(y), labels)
    ax.set_xscale("log"); ax.set_xlim(1, max(counts) * 4)
    ax.xaxis.set_visible(False); ax.spines["bottom"].set_visible(False)
    ax.set_title("Hiring funnel — candidates reaching each stage (log scale)")
    fig.tight_layout(); fig.savefig(IMG_OUT / "funnel.png"); plt.close(fig)


def time_to_fill(con):
    df = con.sql("""
        select filled_month, median_time_to_fill_days, requisitions_filled from kpis.kpi_time_to_fill
        where department_name = 'All departments'
          and filled_month >= date '2024-07-01'  -- earlier months only contain fast fills (data starts Jan 2024)
        order by 1
    """).df()
    df["rolling_3m"] = df.median_time_to_fill_days.rolling(3, min_periods=1).mean()
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.plot(df.filled_month, df.median_time_to_fill_days, color=BLUE_LIGHT, lw=1, marker="o", ms=3, label="Monthly median")
    ax.plot(df.filled_month, df.rolling_3m, color=BLUE, lw=2.2, label="3-month rolling")
    ax.set_ylabel("Days, req open → filled")
    ax.grid(axis="y", color=GRID); ax.set_ylim(0, None)
    ax.legend(frameon=False, loc="lower right")
    ax.set_title("Time to fill")
    fig.tight_layout(); fig.savefig(IMG_OUT / "time_to_fill.png"); plt.close(fig)


def sources(con):
    df = con.sql("""
        select source_name, hires_per_1k_applications, cost_per_hire_usd, source_type
        from kpis.kpi_source_effectiveness where source_id <> 'UNKNOWN'
        order by hires_per_1k_applications
    """).df()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
    colors = [ORANGE if t == "job_board" else BLUE for t in df.source_type]
    a1.barh(df.source_name, df.hires_per_1k_applications, color=colors)
    for i, v in enumerate(df.hires_per_1k_applications):
        a1.text(v + 0.3, i, f"{v:.1f}", va="center", fontsize=8.5, color=INK)
    a1.set_title("Hires per 1,000 applications"); a1.xaxis.set_visible(False); a1.spines["bottom"].set_visible(False)
    a2.barh(df.source_name, df.cost_per_hire_usd, color=colors)
    for i, v in enumerate(df.cost_per_hire_usd):
        a2.text(v + 300, i, f"${v:,.0f}", va="center", fontsize=8.5, color=INK)
    a2.set_title("Cost per hire"); a2.xaxis.set_visible(False); a2.spines["bottom"].set_visible(False)
    fig.text(0.01, 0.01, "Orange = job boards", color=ORANGE, fontsize=8.5)
    fig.tight_layout(); fig.savefig(IMG_OUT / "source_effectiveness.png"); plt.close(fig)


def dq(con):
    df = con.sql("""
        select issue_type, pct_affected, records_affected, severity, source_system
        from data_quality.dq_upstream_gap_report order by pct_affected
    """).df()
    sev = {"high": RED, "medium": ORANGE, "low": MUTED}
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(df.issue_type.str.replace("_", " "), df.pct_affected, color=[sev[s] for s in df.severity])
    for i, (p, n, sysname) in enumerate(zip(df.pct_affected, df.records_affected, df.source_system)):
        ax.text(p + 0.15, i, f"{p:.1f}%  ({n:,} records · {sysname})", va="center", fontsize=8.5, color=INK)
    ax.xaxis.set_major_locator(mtick.MultipleLocator(5))
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.set_xlim(0, df.pct_affected.max() * 1.9)
    ax.set_title("Upstream data gaps: % of records affected")
    fig.text(0.01, 0.01, "Red = high severity · orange = medium · grey = low", color=MUTED, fontsize=8.5)
    ax.grid(axis="x", color=GRID)
    fig.tight_layout(); fig.savefig(IMG_OUT / "data_quality.png"); plt.close(fig)


def main():
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    IMG_OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB), read_only=True)
    for name, rel in EXPORTS.items():
        con.sql(f"select * from {rel}").df().to_csv(DATA_OUT / f"{name}.csv", index=False)
        print(f"exported {name}")
    funnel(con); time_to_fill(con); sources(con); dq(con)
    print(f"charts written to {IMG_OUT}")


if __name__ == "__main__":
    main()
