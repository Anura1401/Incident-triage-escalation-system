# Teleoperation Fleet Field Incident Triage & Escalation System
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](#)
[![Tests: 35 Passed](https://img.shields.io/badge/pytest-35%20passed-brightgreen.svg)](#)
[![Data: 100% Synthetic](https://img.shields.io/badge/Data-100%25%20Synthetic-orange.svg)](#)

> **CRITICAL DISCLAIMER: ALL DATA IS 100% SYNTHETIC SIMULATION DATA**  
> This repository was built as an operations automation portfolio project demonstrating incident triage, SLA tracking, automated escalation, and closed-loop Voice-of-Customer (VoC) analysis for a remote robot-teleoperation company.  
> **No real companies, customer facilities, operational data, or robotic systems are represented.** All customer sites, robot IDs, ticket logs, and corporate parameters are entirely synthetic simulations. All SLA thresholds are design assumptions, not official commercial service level agreements.

---

## What is Real vs. What is Simulated

| Component | Status | Implementation Details |
| :--- | :--- | :--- |
| **Triage Rules Engine** | **Real & Tested** | `src/rules.py` loaded from `config/rules.yaml` with strict precedence (`R0`–`R4`) and case-insensitive keyword parsing. |
| **SLA Calculation Engine** | **Real & Tested** | `src/sla.py` computing response due times, resolution due times, breach status flags, time to resolve, and age metrics. |
| **Test Suite** | **Real & Tested** | 35 automated `pytest` tests validating rules, SLA math, statistical pattern assertions, and watchdog deduplication. |
| **Watchdog Simulator** | **Real & Tested** | `src/watchdog.py` auditing overdue open tickets and executing deduplicated escalation sweeps. |
| **VoC Report Pipeline** | **Real & Tested** | `src/voc_report.py` dynamically calculating trailing 7-day and all-time metrics into `reports/voc_report.md`. |
| **Integration Scripts** | **Real & Tested** | `src/push_to_airtable.py` (batch upload) and `src/push_voc_to_notion.py` (REST API page publisher). |
| **Make Expression Generator**| **Real & Tested** | `src/make_expression.py` compiling YAML rules into atomic Make.com `if(...)` formulas. |
| **Fleet Incident Data** | **Simulated** | 200 synthetic incident records generated over an 8-week horizon across 25 robots at 5 customer facilities. |
| **No-Code Platform Layer** | **Manual Spec** | Detailed setup specifications (`specs/`) for Airtable base schema, Make.com scenario canvases, and Notion databases. |

---

## Assumptions

- **Notification Channel**: Defaulted to standard Gmail / Email modules for high-priority dispatch.
- **Timezone**: Defaulted to India Standard Time (IST, UTC+5:30) for schedule context, with raw data stored in ISO 8601 UTC (`Z`).
- **Plan Limits**: Designed strictly within free-tier quotas of Airtable (<1,000 records), Make.com (15-min min scheduling), and Notion.
- **Tool Stack**: Built on Python 3.11+, pandas, pyairtable, requests, and pyyaml. Ticketing platforms such as Zendesk or Freshdesk were deliberately skipped.
- **Triage Architecture**: Used a single nested Set Variable expression in Make.com rather than a multi-branch Router to prevent duplicate Airtable updates and race conditions.

---

## Repository Structure

```text
teleop-incident-triage/
├── README.md                      # Project documentation and replication guide
├── PROCESS.md                     # Operational process SOP and triage hierarchy
├── requirements.txt               # Lightweight Python dependencies
├── .gitignore                     # Git ignore rules for virtual environments and secrets
├── .env.example                   # Template for Airtable and Notion API credentials
├── pytest.ini                     # Pytest root configuration
├── config/
│   └── rules.yaml                 # Single source of truth: priorities, SLAs, keywords
├── src/
│   ├── rules.py                   # Rule classification module (classify -> priority, needs_review)
│   ├── sla.py                     # SLA math module mirroring Airtable formulas
│   ├── generate_tickets.py        # Seeded synthetic ticket generator (200 records)
│   ├── watchdog.py                # SLA watchdog sweep simulator with deduplication
│   ├── voc_report.py              # Automated VoC metrics compiler (reports/voc_report.md)
│   ├── push_to_airtable.py        # Batch uploader to Airtable via pyairtable (10 records/batch)
│   ├── push_voc_to_notion.py      # Optional Notion database page publisher via REST API
│   └── make_expression.py         # Make.com Set Variable formula generator from rules.yaml
├── data/
│   └── tickets.csv                # Generated dataset of 200 synthetic incident tickets
├── reports/
│   └── voc_report.md              # Dynamically computed weekly VoC review report
├── specs/
│   ├── airtable_schema.md         # Airtable tables, formulas, views, and verification table
│   ├── make_scenarios.md          # Make.com scenario architectures and module configurations
│   └── notion_voc.md              # Notion VoC review database schema and page template
├── tests/
│   ├── test_rules.py              # Unit tests for rule precedence and keyword classification
│   ├── test_sla.py                # Hand-calculated tests for SLA due times and breach logic
│   ├── test_generator.py          # Schema integrity and statistical pattern assertions (A–D)
│   └── test_watchdog.py           # Watchdog escalation and deduplication integration tests
├── screenshots/
│   └── README.md                  # Checklist of manual evidence screenshots to capture
└── docs/
    └── resume_and_interview.md    # 3 resume bullets (≤20 words) and 6 interview Q&A frameworks
```

---

## Quickstart & Replication Guide

### 1. Environment Setup
Clone the repository and install the lightweight requirements:
```bash
git clone https://github.com/your-username/teleop-incident-triage.git
cd teleop-incident-triage
pip install -r requirements.txt
```

### 2. Run the Automated Test Suite
Run all 35 unit and integration tests using pytest:
```bash
pytest -v
```
*Expected Result: 35 passed in ~1 second.*

### 3. Generate the Synthetic Dataset
Generate `data/tickets.csv` with seeded statistical anomalies:
```bash
python src/generate_tickets.py
```
This script outputs verification tables confirming the 4 embedded fleet patterns:
- **Pattern A (Component Failure)**: Gripper slippage accounts for ~32% of all incidents.
- **Pattern B (Firmware Regression)**: Robots running firmware `v2.3` generate >70% of all teleop latency tickets.
- **Pattern C (Site Hotspot)**: `Site Beta (Detroit Auto)` exhibits 1.73x its fair share of P1/P2 incidents.
- **Pattern D (SLA Concentration)**: P2 Major Degradation incidents suffer the highest SLA breach rate (~47%).

### 4. Execute the SLA Watchdog Sweep
Run the watchdog simulator to identify overdue open tickets:
```bash
# First sweep: Identifies overdue tickets, dispatches alerts, records escalation
python src/watchdog.py --now "2026-11-05T18:00:00Z"

# Second sweep: Demonstrates deduplication (0 new tickets escalated)
python src/watchdog.py --now "2026-11-05T18:00:00Z"
```

### 5. Compile the Weekly VoC Review Report
Generate the weekly markdown report (`reports/voc_report.md`):
```bash
python src/voc_report.py
```

### 6. Generate the Make.com Triage Expression
Inspect the generated nested formula for the Make.com Set Variable module:
```bash
python src/make_expression.py
```

### 7. (Optional) Push Data to Airtable & Notion
To connect live tools:
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Populate `AIRTABLE_PAT`, `AIRTABLE_BASE_ID`, `NOTION_TOKEN`, and `NOTION_DATABASE_ID`.
3. Validate Airtable upload in dry-run mode:
   ```bash
   python src/push_to_airtable.py --dry-run --limit 10
   ```
4. Execute batch upload (10 records per batch with automatic rate limiting):
   ```bash
   python src/push_to_airtable.py
   ```
5. Publish VoC report to Notion:
   ```bash
   python src/push_voc_to_notion.py
   ```

---

## Manual No-Code Build Checklist

Follow the specification documents in `specs/` to complete the no-code setup:
1. **Airtable**: Create the base, 3 tables (`Tickets`, `Priority Rules`, `Engineering Backlog`), paste the formulas from `specs/airtable_schema.md`, and verify with the 5-row hand-calculation table.
2. **Make.com Scenario 1 (Auto-Triage)**: Build the intake flow using `specs/make_scenarios.md`. Use the expression from `python src/make_expression.py` in the Set Variable module.
3. **Make.com Scenario 2 (SLA Watchdog)**: Configure the 15-minute search sweep with the deduplication formula from `specs/make_scenarios.md`.
4. **Notion**: Create the `Weekly VoC Reviews` database using `specs/notion_voc.md`.
5. **Screenshots**: Capture the 6 evidence screenshots listed in `screenshots/README.md` (remembering to hide tokens and webhooks).

