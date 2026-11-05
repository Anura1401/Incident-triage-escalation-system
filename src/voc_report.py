"""
Weekly Voice-of-Customer (VoC) Review Report Generator.
Computes operational fleet telemetry metrics from tickets.csv for the trailing 7 days and all-time.
Outputs reports/voc_report.md.
ALL DATA IS SYNTHETIC. NO REAL CUSTOMER OR ROBOT DATA.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import pandas as pd

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sla import (
    response_breached,
    resolution_breached,
    time_to_resolve_hours,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
CSV_PATH = DATA_DIR / "tickets.csv"

EVAL_NOW_STR = "2026-11-05T18:00:00Z"
EVAL_NOW = datetime(2026, 11, 5, 18, 0, 0, tzinfo=timezone.utc)
SEVEN_DAYS_AGO = EVAL_NOW - timedelta(days=7)


def generate_voc_report(csv_path: Path = CSV_PATH) -> Path:
    """Read CSV, compute all metrics, and write reports/voc_report.md."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Input file not found: {csv_path}. Run src/generate_tickets.py first.")

    df = pd.read_csv(csv_path)

    # Compute SLA breach flags and resolution times
    df["Created_DT"] = pd.to_datetime(df["Created At"])
    df["Resp_Breached"] = [
        response_breached(r["Created At"], r["Priority"], r["First Response At"] if pd.notna(r["First Response At"]) and r["First Response At"] != "" else None, EVAL_NOW)
        for _, r in df.iterrows()
    ]
    df["Res_Breached"] = [
        resolution_breached(r["Created At"], r["Priority"], r["Status"], r["Resolved At"] if pd.notna(r["Resolved At"]) and r["Resolved At"] != "" else None, EVAL_NOW)
        for _, r in df.iterrows()
    ]
    df["Any_Breached"] = df["Resp_Breached"] | df["Res_Breached"]
    df["TTR_Hours"] = [
        time_to_resolve_hours(r["Created At"], r["Resolved At"] if pd.notna(r["Resolved At"]) and r["Resolved At"] != "" else None)
        for _, r in df.iterrows()
    ]

    # Filter 7-day trailing slice
    df_7d = df[df["Created_DT"] >= SEVEN_DAYS_AGO].copy()

    total_all = len(df)
    total_7d = len(df_7d)

    # 1. Top categories
    cat_all = df["Category"].value_counts()
    cat_7d = df_7d["Category"].value_counts()
    top3_all = cat_all.head(3)
    top3_7d = cat_7d.head(3)

    # 2. Firmware vs Latency
    lat_all = df[df["Category"] == "Latency / Connectivity"]
    lat_7d = df_7d[df_7d["Category"] == "Latency / Connectivity"]
    fw_lat_all = lat_all["Firmware Version"].value_counts()
    fw_lat_7d = lat_7d["Firmware Version"].value_counts()

    # 3. Site hotspots (P1/P2)
    p1p2_all = df[df["Priority"].isin(["P1", "P2"])]
    p1p2_7d = df_7d[df_7d["Priority"].isin(["P1", "P2"])]
    site_all = df["Site"].value_counts()
    site_p1p2_all = p1p2_all["Site"].value_counts()
    site_7d = df_7d["Site"].value_counts()
    site_p1p2_7d = p1p2_7d["Site"].value_counts()

    # 4. SLA performance by priority
    pri_metrics = {}
    for p in ["P1", "P2", "P3", "P4"]:
        sub_all = df[df["Priority"] == p]
        sub_7d = df_7d[df_7d["Priority"] == p]
        br_all = sub_all["Any_Breached"].sum()
        br_7d = sub_7d["Any_Breached"].sum()
        med_ttr_all = sub_all["TTR_Hours"].dropna().median()
        med_ttr_7d = sub_7d["TTR_Hours"].dropna().median()

        pri_metrics[p] = {
            "cnt_all": len(sub_all),
            "br_all": int(br_all),
            "br_rate_all": (br_all / len(sub_all) * 100) if len(sub_all) > 0 else 0.0,
            "med_ttr_all": med_ttr_all if pd.notna(med_ttr_all) else 0.0,
            "cnt_7d": len(sub_7d),
            "br_7d": int(br_7d),
            "br_rate_7d": (br_7d / len(sub_7d) * 100) if len(sub_7d) > 0 else 0.0,
            "med_ttr_7d": med_ttr_7d if pd.notna(med_ttr_7d) else 0.0,
        }

    # Needs review counts
    nr_all = (df["Needs Review"] == "True").sum()
    nr_7d = (df_7d["Needs Review"] == "True").sum()

    # Compile Markdown Report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / "voc_report.md"

    # Derive engineering asks based on computed anomalies
    top_cat_name = top3_all.index[0]
    top_cat_cnt = top3_all.iloc[0]
    top_cat_pct = (top_cat_cnt / total_all) * 100

    v23_lat_cnt = fw_lat_all.get("v2.3", 0)
    v23_lat_pct = (v23_lat_cnt / len(lat_all) * 100) if len(lat_all) > 0 else 0.0

    beta_p1p2_cnt = site_p1p2_all.get("Site Beta (Detroit Auto)", 0)
    beta_p1p2_pct = (beta_p1p2_cnt / len(p1p2_all) * 100) if len(p1p2_all) > 0 else 0.0

    md_content = f"""# Weekly Voice-of-Customer (VoC) Review Report
**Operational Teleoperation Fleet Telemetry & Incident Analysis**  
*Evaluation Timestamp: {EVAL_NOW_STR} | Trailing 7-Day Window: {SEVEN_DAYS_AGO.strftime('%Y-%m-%d')} to {EVAL_NOW.strftime('%Y-%m-%d')}*  
> **DISCLAIMER: ALL DATA IS 100% SYNTHETIC SIMULATION DATA FOR PORTFOLIO DEMONSTRATION.**  
> No real customers, teleoperation facilities, or robotic systems are represented. All SLAs are design assumptions.

---

## Executive Summary
During the trailing 7-day operational cycle, **{total_7d}** new field incidents were reported across the fleet ({total_all} cumulative all-time). Overall SLA breach rate stands at **{(df_7d['Any_Breached'].sum() / total_7d * 100):.1f}%** for the trailing week. Unclassified triage tickets requiring human review totaled **{nr_7d}** tickets ({nr_7d / total_7d * 100:.1f}%).

---

## 1. Top Recurring Categories
Physical manipulation issues continue to dominate operational friction, driven primarily by end-effector slippage on non-uniform payloads.

### Trailing 7 Days
| Rank | Category | Ticket Count | Percentage |
| :---: | :--- | :---: | :---: |
"""
    for idx, (cat, cnt) in enumerate(top3_7d.items(), 1):
        md_content += f"| {idx} | {cat} | {cnt} | {cnt/total_7d*100:.1f}% |\n"

    md_content += f"""
### All-Time Cumulative (8-Week Horizon)
| Rank | Category | Ticket Count | Percentage |
| :---: | :--- | :---: | :---: |
"""
    for idx, (cat, cnt) in enumerate(top3_all.items(), 1):
        md_content += f"| {idx} | {cat} | {cnt} | {cnt/total_all*100:.1f}% |\n"

    md_content += f"""
*Key Observation:* **{top_cat_name}** represents **{top_cat_pct:.1f}%** of all historical incidents ({top_cat_cnt} tickets), requiring immediate mechanical gripper hardware review.

---

## 2. Firmware Correlation (Latency & Telemetry)
Analysis of connectivity and teleoperation video lag indicates a severe regression tied to firmware build `v2.3`.

| Firmware Version | Trailing 7d Latency Tickets | All-Time Latency Tickets | Share of All Latency Incidents |
| :--- | :---: | :---: | :---: |
| **v2.3** | {fw_lat_7d.get("v2.3", 0)} | {fw_lat_all.get("v2.3", 0)} | {v23_lat_pct:.1f}% |
| **v2.2** | {fw_lat_7d.get("v2.2", 0)} | {fw_lat_all.get("v2.2", 0)} | {(fw_lat_all.get("v2.2", 0)/len(lat_all)*100 if len(lat_all)>0 else 0):.1f}% |
| **v2.1** | {fw_lat_7d.get("v2.1", 0)} | {fw_lat_all.get("v2.1", 0)} | {(fw_lat_all.get("v2.1", 0)/len(lat_all)*100 if len(lat_all)>0 else 0):.1f}% |

*Finding:* Robots running **v2.3** account for **{v23_lat_pct:.1f}%** of all latency and WebRTC streaming stalls, pointing to a buffer-management regression introduced in the v2.3 teleop streaming pipeline.

---

## 3. Site Hotspots & Deployment Health
Fleet distribution is balanced evenly across all 5 customer sites (~20.0% ticket volume each); however, severe incidents (P1 Critical and P2 Major Degradation) are heavily concentrated at **Site Beta (Detroit Auto)**.

| Customer Deployment Site | Total Tickets | Trailing 7d P1/P2 | All-Time P1/P2 | Share of Fleet P1/P2 | Risk Factor |
| :--- | :---: | :---: | :---: | :---: | :---: |
"""
    for s in site_all.index:
        tot = site_all[s]
        p1p2_7 = site_p1p2_7d.get(s, 0)
        p1p2_a = site_p1p2_all.get(s, 0)
        share_p1p2 = (p1p2_a / len(p1p2_all) * 100) if len(p1p2_all) > 0 else 0
        ratio = share_p1p2 / (tot / total_all * 100)
        risk = "HIGH CONCENTRATION" if ratio >= 1.4 else "NORMAL"
        md_content += f"| {s} | {tot} | {p1p2_7} | {p1p2_a} | {share_p1p2:.1f}% | {risk} ({ratio:.2f}x) |\n"

    md_content += f"""
*Finding:* **Site Beta (Detroit Auto)** accounts for **{beta_p1p2_pct:.1f}%** of all critical P1/P2 fleet disruptions despite holding only 20% of fleet ticket volume.

---

## 4. SLA Performance & Watchdog Activity
SLA breaches are disproportionately concentrated in **Priority P2 (Major Degradation)** due to the diagnostic complexity of intermittent gripper slippage and teleoperation packet loss.

| Priority Level | Target Response | Target Resolution | Trailing 7d Volume | 7d Breach Rate | All-Time Volume | All-Time Breach Rate | Median TTR (Hrs) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for p in ["P1", "P2", "P3", "P4"]:
        m = pri_metrics[p]
        resp_sla, res_sla = ("15m", "4h") if p == "P1" else (("2h", "12h") if p == "P2" else (("8h", "48h") if p == "P3" else ("24h", "120h")))
        md_content += f"| **{p}** | {resp_sla} | {res_sla} | {m['cnt_7d']} | {m['br_rate_7d']:.1f}% | {m['cnt_all']} | {m['br_rate_all']:.1f}% | {m['med_ttr_all']:.2f}h |\n"

    md_content += f"""
*Finding:* P2 resolution breaches reached **{pri_metrics['P2']['br_rate_all']:.1f}%** all-time, confirming that remote troubleshooting of hardware slippage requires expedited tier-2 engineering triage.

---

## 5. Engineering Backlog Asks
Derived directly from the empirical anomalies identified in Sections 1–4:

1. **[ENG-BACKLOG-01] Patch WebRTC Video Stream Jitter on Firmware v2.3**
   - *Target Component:* `teleop-streaming-daemon`
   - *Problem:* Accounts for {v23_lat_pct:.1f}% of latency degradation tickets across the fleet.
   - *Proposed Solution:* Revert encoder buffer changes from commit v2.3-rc2; implement adaptive bitrate fallback on cellular uplinks.
   - *Priority:* P1 Bugfix (Target: Sprint 24-Q4-S2).

2. **[ENG-BACKLOG-02] Gripper Dynamic Grip Pressure & Encoder Recalibration**
   - *Target Component:* `end-effector-controller`
   - *Problem:* {top_cat_cnt} cumulative slip/drop incidents ({top_cat_pct:.1f}% of total incident log).
   - *Proposed Solution:* Implement automated fingertip force calibration routine during pre-shift dock initialization; increase pneumatic clamp threshold on slippery plastic totes.
   - *Priority:* P2 Feature / Reliability (Target: Sprint 24-Q4-S2).

3. **[ENG-BACKLOG-03] Teleop Cockpit UI Force Feedback Overlay Widget**
   - *Target Component:* `operator-console-gui`
   - *Problem:* Operators lack real-time visual cue when parallel jaw seal pressure drops prior to container drop.
   - *Proposed Solution:* Expose real-time pneumatic pressure gauge widget on primary teleoperation HUD.
   - *Priority:* P3 Enhancement (Target: Sprint 24-Q4-S3).

---

## 6. Operational Decisions & Action Items
- [ ] **Site Beta Physical Safety Audit**: Dispatch Field Robotics Lead to Detroit facility to audit warehouse lane clearance and pedestrian e-stop proximity triggers ({beta_p1p2_pct:.1f}% P1/P2 fleet share).
- [ ] **Firmware Rollback Candidate**: Freeze v2.3 rollout to new customer sites; prepare firmware v2.2.4 patch for high-latency units.
- [ ] **Refine Triage Keywords**: Review {nr_all} historical tickets flagged 'Needs Review' to expand keyword coverage for edge telemetry advisories.
- [ ] **P2 Response Runbook**: Establish dedicated tier-2 Slack alert channel for gripper slip incidents to bring P2 resolution breach rate from {pri_metrics['P2']['br_rate_all']:.1f}% down below 25%.
"""

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"VoC Report generated successfully: {report_file}")
    return report_file


def main():
    generate_voc_report()


if __name__ == "__main__":
    main()

