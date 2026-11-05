# Airtable Base Schema Specification
**Base Name:** `Robot Ops Incident & Escalation System`  
> **DISCLAIMER: ALL DATA IS 100% SYNTHETIC SIMULATION DATA FOR PORTFOLIO DEMONSTRATION.**  
> No real customer data, facilities, or robots are used. All SLA parameters are design assumptions.

---

## 1. Table Architectures

### Table 1: `Tickets` (Core System of Record)

| Field Name | Field Type | Notes & Format |
| :--- | :--- | :--- |
| `Ticket ID` | Single line text | **Primary Field**. e.g., `TIC-1041` |
| `Submitted Time` | **Created time** | Automatic Airtable timestamp. **Used as the Make.com trigger** to detect new form records. |
| `Created At` | Date (Include time, GMT) | Standardized incident timestamp. For imported CSV rows, this preserves historical timestamps; for new form submissions, Make copies `Submitted Time` into `Created At`. |
| `Reporter Role` | Single select | Options: `Field Engineer`, `Customer Ops`, `Teleoperation Operator` |
| `Site` | Single select | Options: `Site Alpha (Austin Logistics)`, `Site Beta (Detroit Auto)`, `Site Gamma (Reno Fulfillment)`, `Site Delta (Phoenix Parcel)`, `Site Epsilon (Seattle Depots)` |
| `Robot ID` | Single line text | e.g., `ROBOT-104` |
| `Category` | Single select | 9 categories: `Safety Stop`, `Gripper / End-Effector`, `Latency / Connectivity`, `Navigation`, `Camera / Sensor`, `Software Crash`, `Operator Tool UI`, `Data Capture Quality`, `Feature Request / Enhancement` |
| `Description` | Long text | Symptom description and teleop logs |
| `Firmware Version` | Single select | Options: `v2.1`, `v2.2`, `v2.3` |
| `Priority` | Single select | Options: `P1`, `P2`, `P3`, `P4` (Populated by Make.com auto-triage; hidden on intake form) |
| `Status` | Single select | Options: `Open`, `In Progress`, `Resolved` (Default: `Open`) |
| `First Response At` | Date (Include time, GMT) | Timestamp of first operator touch |
| `Resolved At` | Date (Include time, GMT) | Timestamp of incident resolution |
| `Needs Review` | Checkbox | Checked if triage fell back to default R4 (no recognized keywords) |
| `Escalated` | Checkbox | Checked by SLA Watchdog upon escalation |
| `Escalated At` | Date (Include time, GMT) | Timestamp of watchdog alert dispatch |
| `Synthetic Data Label` | Single line text | Default: `SIMULATED SYNTHETIC DATA` |

#### Calculated Formula Fields (Mirroring `src/sla.py` exactly)

- **`SLA Response Due`** (Formula, result formatted as Date with time GMT):
```airtable
IF(
  AND({Created At}, {Priority}),
  DATEADD(
    {Created At},
    SWITCH(
      {Priority},
      "P1", 15,
      "P2", 120,
      "P3", 480,
      "P4", 1440,
      480
    ),
    'minutes'
  ),
  BLANK()
)
```

- **`SLA Resolution Due`** (Formula, result formatted as Date with time GMT):
```airtable
IF(
  AND({Created At}, {Priority}),
  DATEADD(
    {Created At},
    SWITCH(
      {Priority},
      "P1", 4,
      "P2", 12,
      "P3", 48,
      "P4", 120,
      48
    ),
    'hours'
  ),
  BLANK()
)
```

- **`Response Breached`** (Formula, result integer 1 or 0):
```airtable
IF(
  OR({Priority} = BLANK(), {Created At} = BLANK()),
  0,
  IF(
    {First Response At} = BLANK(),
    IF(NOW() > {SLA Response Due}, 1, 0),
    IF({First Response At} > {SLA Response Due}, 1, 0)
  )
)
```

- **`Resolution Breached`** (Formula, result integer 1 or 0):
```airtable
IF(
  OR({Priority} = BLANK(), {Created At} = BLANK()),
  0,
  IF(
    {Status} = "Resolved",
    IF({Resolved At} = BLANK(), 0, IF({Resolved At} > {SLA Resolution Due}, 1, 0)),
    IF(NOW() > {SLA Resolution Due}, 1, 0)
  )
)
```

- **`Time to Resolve (hours)`** (Formula, decimal precision 2):
```airtable
IF(
  AND({Created At}, {Resolved At}),
  ROUND(DATETIME_DIFF({Resolved At}, {Created At}, 'minutes') / 60, 2),
  BLANK()
)
```

- **`Age (hours)`** (Formula, decimal precision 1):
```airtable
IF(
  {Status} != "Resolved",
  ROUND(DATETIME_DIFF(NOW(), {Created At}, 'minutes') / 60, 1),
  BLANK()
)
```

---

### Table 2: `Priority Rules` (SLA Reference Catalog)

| Priority | Level Name | Response SLA (Hours) | Resolution SLA (Hours) | Escalation Role | Notification Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **P1** | Critical / Safety | 0.25 (15 min) | 4 | Site Operations Lead & On-Call Robotics Lead | Instant Alert Dispatch |
| **P2** | Major Degradation | 2.00 (120 min) | 12 | Hardware/Network Support Specialist | Instant Alert Dispatch |
| **P3** | Minor / Workaround | 8.00 (480 min) | 48 | Field Support Queue Lead | Queued for VoC Digest |
| **P4** | Enhancement | 24.00 (1440 min) | 120 | Product / Operations Analyst | Queued for VoC Digest |

---

### Table 3: `Engineering Backlog` (VoC Action Pipeline)

| Field Name | Field Type | Configuration / Purpose |
| :--- | :--- | :--- |
| `Item ID` | Single line text | Primary Field (e.g., `ENG-BACKLOG-01`) |
| `Title` | Single line text | Short feature / defect title |
| `Category` | Single select | Same 9 categories as Tickets table |
| `Target Firmware` | Single select | `v2.1`, `v2.2`, `v2.3`, `v2.4` |
| `Linked Tickets` | Link to another record | Links to `Tickets` table (Allow linking multiple records) |
| `Ticket Count` | Rollup | Rollup on `Linked Tickets` -> field `Ticket ID` -> formula `COUNTA(values)` |
| `Status` | Single select | `Backlog`, `In Sprint`, `Testing`, `Shipped` |
| `Sprint` | Single line text | e.g., `Sprint 24-Q4-S2` |

---

## 2. Intake Form Configuration
1. In `Tickets`, create a **Form view** titled `Field Incident Intake Form`.
2. Add banner description:
   ```text
   TELEOPERATION FLEET FIELD INCIDENT REPORTING PORTAL
   NOTE: ALL SUBMISSIONS ENTER SIMULATION DATASET.
   Priority and SLA targets are computed automatically upon intake.
   ```
3. Expose these fields as required:
   - `Reporter Role` (Required)
   - `Site` (Required)
   - `Robot ID` (Required)
   - `Firmware Version` (Required)
   - `Category` (Required)
   - `Description` (Required)
4. **HIDDEN FIELDS** (Do NOT expose on form): `Priority`, `Status`, `First Response At`, `Resolved At`, `Needs Review`, `Escalated`, `Escalated At`, and all formula fields.

---

## 3. Required Airtable Views

1. **`Open by Priority`**:
   - Filter: `Status` is not `Resolved`
   - Group by: `Priority` (Descending: P1, P2, P3, P4)
   - Sort: `Created At` (Ascending / oldest first)
2. **`SLA Breaches`**:
   - Filter: `Response Breached = 1` OR `Resolution Breached = 1`
   - Group by: `Priority`
   - Sort: `Created At` (Descending)
3. **`Recently Created`**:
   - Filter: None
   - Sort: `Created At` (Descending)
4. **`Gallery by Category`**:
   - View Type: Gallery
   - Group by: `Category`
   - Visible card fields: `Ticket ID`, `Priority`, `Site`, `Firmware Version`, `Status`
5. **`Untriaged Tickets`** (For Make.com trigger):
   - Filter: `Priority` is empty

---

## 4. Hand-Calculation Verification Reference Table
Verify your Airtable formulas against these 5 actual records from `data/tickets.csv` (evaluated at `now = 2026-11-05T18:00:00Z`):

| Ticket ID | Priority | Created At | Status | SLA Response Due | SLA Resolution Due | Response Breached | Resolution Breached | Time to Resolve (h) | Age (h) |
| :--- | :---: | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **TIC-1041** | P2 | 2026-09-12 17:29:19Z | Resolved | 2026-09-12 19:29:19Z | 2026-09-13 05:29:19Z | 0 | 0 | 6.53 | — |
| **TIC-1033** | P3 | 2026-10-31 08:42:59Z | Resolved | 2026-10-31 16:42:59Z | 2026-11-02 08:42:59Z | 0 | 0 | 20.96 | — |
| **TIC-1172** | P1 | 2026-11-04 09:43:19Z | In Progress | 2026-11-04 09:58:19Z | 2026-11-04 13:43:19Z | 0 | 1 | — | 32.3 |
| **TIC-1015** | P2 | 2026-11-04 10:41:40Z | In Progress | 2026-11-04 12:41:40Z | 2026-11-04 22:41:40Z | 1 | 1 | — | 31.3 |
| **TIC-1008** | P3 | 2026-11-05 07:17:23Z | Open | 2026-11-05 15:17:23Z | 2026-11-07 07:17:23Z | 1 | 0 | — | 10.7 |

