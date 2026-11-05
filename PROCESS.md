# Field Incident Triage & Escalation Operational Process
**Standard Operating Procedure (SOP) | Simulated Teleoperation Fleet**  
*Notice: All operational data, customer facilities, and robot hardware logs are 100% synthetic for portfolio demonstration.*

---

## 1. System Purpose & Objectives
In remote robot-teleoperation operations, field teams encounter issues spanning minor telemetry delays to severe safety barrier stops. This system establishes:
1. **Deterministic Severity Classification**: Triage incoming incidents into P1–P4 priorities within seconds.
2. **SLA Management**: Real-time formula computation of response and resolution deadlines.
3. **Automated Escalation Routing**: Immediate email paging for critical incidents while routing non-critical issues to weekly review digests.
4. **Closed-Loop Feedback**: Continuous aggregation of field friction into structured engineering sprint backlog asks.

---

## 2. Priority & SLA Framework
> *Note: SLA thresholds below are design assumptions for this simulation project, not commercial policies.*

| Priority | Level Name | Response SLA | Target Resolution SLA | Escalation Owner Role | Notification Protocol |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **P1** | Critical / Safety | 15 Minutes (0.25h) | 4 Hours | Site Operations Lead & On-Call Robotics Lead | Instant Alert Dispatch |
| **P2** | Major Degradation | 2 Hours (120m) | 12 Hours | Hardware/Network Support Specialist | Instant Alert Dispatch |
| **P3** | Minor / Workaround | 8 Hours (480m) | 48 Hours | Field Support Queue Lead | Queued for Weekly VoC Digest |
| **P4** | Enhancement | 24 Hours (1440m) | 120 Hours | Product / Operations Analyst | Queued for Weekly VoC Digest |

### Triage Classification Hierarchy
Classification operates under strict first-match precedence (`R0` -> `R1` -> `R2` -> `R3` -> `R4`):
- **Rule 0 (Safety Override)**: `Safety Stop` category OR any mention of `injury`, `collision`, `safety`, `e-stop`, `hazard`, `near-miss` -> **P1**.
- **Rule 1 (Software Blocker)**: `Software Crash` with `hang`, `deadlock`, `frozen`, `blackout`, or `segmentation fault` -> **P1**.
- **Rule 2 (Core Degradation)**: `Gripper / End-Effector`, `Latency / Connectivity`, or `Navigation` with `slip`, `drop`, `spike`, `packet loss`, `drift`, `jitter`, `stuck`, `timeout`, or `high ping` -> **P2**.
- **Rule 3 (Enhancement)**: `Feature Request / Enhancement` category OR mention of `request`, `suggestion`, `shortcut`, `enhancement` -> **P4**.
- **Rule 4 (Fallback Queue)**: All other reports default to **P3**. Reports lacking recognized operational keywords are tagged `Needs Review = True` for manual dispatcher audit.

---

## 3. Automation Architecture: Code vs. No-Code Partitioning

```
FIELD INTAKE               AUTOMATION LAYER                   ANALYSIS & SPRINT SYNC
┌────────────────┐        ┌────────────────────────┐         ┌─────────────────────────┐
│ Airtable Form  │───────▶│ Make.com Scenario 1    │────────▶│ P1/P2 Instant Alert     │
│ (Operators &   │        │ (Priority Triage Engine│         │ (Email Dispatch)        │
│ Field Engs)    │        │ via Set Variable)      │         └─────────────────────────┘
└────────────────┘        └────────────────────────┘
                                    │
                                    ▼
                          ┌────────────────────────┐         ┌─────────────────────────┐
                          │ Make.com Scenario 2    │────────▶│ Escalation Dispatch     │
                          │ (SLA Watchdog Sweep    │         │ (Deduplicated Alerts)   │
                          │ every 15 minutes)      │         └─────────────────────────┘
                          └────────────────────────┘
                                    │
                                    ▼
                          ┌────────────────────────┐         ┌─────────────────────────┐
                          │ Python / Make VoC Sync │────────▶│ Notion Weekly VoC Board │
                          │ (Trailing 7-Day        │         │ & Engineering Backlog   │
                          │ Statistical Metrics)   │         │ (Sprint Prioritization) │
                          └────────────────────────┘         └─────────────────────────┘
```

- **No-Code Components (Airtable / Make.com / Notion)**:
  - Airtable acts as the live system of record, hosting dynamic SLA formulas, role views, and intake forms.
  - Make.com provides event-driven triage upon record creation and scheduled sweep auditing for SLA breaches.
  - Notion hosts the executive Weekly VoC Review dashboard and sprint backlog linkages.
- **Code Components (Python 3.11 / Pytest / PyAirtable)**:
  - `config/rules.yaml`: Single source of truth for priority and keyword taxonomy.
  - `src/sla.py` & `src/rules.py`: Local deterministic implementations guaranteeing data integrity.
  - `src/generate_tickets.py`: Seeded synthetic dataset generator producing realistic fleet patterns.
  - `src/watchdog.py`: Local simulator for validating breach escalation and deduplication logic.
  - `src/voc_report.py`: Automated markdown report compiler calculating fleet performance statistics.

---

## 4. Weekly Voice-of-Customer (VoC) Review Cadence
Every Monday, Operations and Robotics Engineering conduct a 30-minute operational review using the Notion VoC board:
1. **Failure Mode Trend Audit**: Review top recurring categories against recent operational shifts.
2. **Firmware Regression Analysis**: Cross-tabulate latency incidents against active fleet firmware builds.
3. **Facility Hotspot Inspection**: Identify physical environment hazards if a facility exhibits abnormal P1/P2 density.
4. **Engineering Ticket Creation**: Convert verified operational patterns into formal Engineering Backlog items (`ENG-BACKLOG-XX`) with linked incident IDs.

---

## 5. System Limitations & Assumptions
1. **Synthetic Data**: All 200 tickets are synthetically generated to model fleet dynamics without exposing proprietary data.
2. **Deterministic Rules Engine**: Classification employs case-insensitive keyword heuristics rather than an LLM parser.
3. **Free-Tier Design**: Built entirely within free-tier quotas of Airtable, Make.com, and Notion.

