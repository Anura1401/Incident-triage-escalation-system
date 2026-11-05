# Notion VoC Review Database Specification
**Database Title:** `Weekly VoC Reviews`  
> **DISCLAIMER: ALL DATA IS 100% SYNTHETIC SIMULATION DATA FOR PORTFOLIO DEMONSTRATION.**

---

## 1. Database Properties Schema

| Property Name | Property Type | Options / Configuration |
| :--- | :--- | :--- |
| `Review Title` | **Title** | e.g., `Weekly VoC Review - 2026-W45 (Simulated Fleet)` |
| `Review Date` | **Date** | ISO Date format |
| `Total Tickets (7d)` | **Number** | Integer format |
| `SLA Breaches (7d)` | **Number** | Integer format |
| `Top Category` | **Select** | `Gripper / End-Effector`, `Latency / Connectivity`, `Navigation`, `Camera / Sensor`, `Software Crash`, `Operator Tool UI`, `Data Capture Quality`, `Feature Request / Enhancement`, `Safety Stop` |
| `Problematic Firmware` | **Select** | `v2.1`, `v2.2`, `v2.3` |
| `Primary Hotspot Site` | **Select** | `Site Alpha (Austin Logistics)`, `Site Beta (Detroit Auto)`, `Site Gamma (Reno Fulfillment)`, `Site Delta (Phoenix Parcel)`, `Site Epsilon (Seattle Depots)` |
| `Data Disclaimer` | **Rich text** | Default text: `SIMULATED SYNTHETIC DATA` |

---

## 2. Standard VoC Review Page Template
Inside your database page template, structure the body with these 6 headings:

```markdown
# Weekly Voice-of-Customer (VoC) Review - Executive Summary
*Simulated Robotics Teleoperation Operations | Confidential Internal Briefing*

## 1. Top 3 Recurring Issue Categories
- Physical manipulation vs software/network breakdown.
- Primary failure root causes and customer impact.

## 2. Firmware Version Correlation
- Cross-tabulation of incidents across v2.1, v2.2, and v2.3.
- Focus: Latency and stream packet loss regression on v2.3.

## 3. Site Hotspots & Fleet Health
- Fleet deployment distribution across all 5 facilities.
- Focus: P1/P2 critical incident concentration at Site Beta (Detroit Auto).

## 4. SLA Performance & Watchdog Activity
- P1–P4 breach volumes and breach percentages.
- Mean / Median Time to Resolve (TTR).
- Automated watchdog escalation volume.

## 5. Engineering Backlog Asks
- Structured engineering tickets derived directly from incident patterns.
- e.g., WebRTC latency buffer patch, gripper force sensor recalibration.

## 6. Operational Decisions & Action Items
- Immediate operational runbook adjustments, site audits, and firmware rollout freezes.
```

