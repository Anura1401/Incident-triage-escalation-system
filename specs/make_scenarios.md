# Make.com Scenarios Specification
**Automations Architecture for Triage, Watchdog, and VoC Sync**  
> **DISCLAIMER: ALL INCIDENTS AND METRICS ARE 100% SYNTHETIC SIMULATION DATA.**  
> Note: Every Make expression, module configuration, and UI label in this document is labeled as **untested in your specific workspace, verify in the Make.com scenario editor** as automation platforms frequently update UI terminology.

---

> [!WARNING]
> ### Mandatory Action: Verify Plan Limits Yourself
> Before configuring scenario schedules or bulk webhooks, check your account's current free-plan quotas directly in the Make, Airtable, and Notion dashboards:
> - **Make.com**: Check **Organization > Subscription** for monthly operation limits and minimum execution intervals (e.g., free tiers may restrict scheduled intervals to 15 minutes).
> - **Airtable**: Check your workspace plan for monthly automation runs and base record caps.
> - **Design within your active limits**: Run scenarios manually via the **"Run once"** button during testing to avoid depleting monthly operations.

---

## Scenario 1: Automated Incident Intake & Triage

### Architecture & Design Decision
*Why a single Set Variable module instead of a multi-branch Router?*  
In Make.com, standard routers evaluate and execute **all branches whose filter conditions evaluate to true**. If an incident matches both a safety keyword and a hardware keyword, a router will execute multiple branches simultaneously, causing race conditions, duplicate Airtable updates, and multiple paged emails. By computing priority using a single nested `if(...)` expression inside a **Set Variable** module and executing **one** Airtable update, execution remains deterministic, idempotent, and saves Make operations.

### Flow Diagram
```
[Airtable: Watch Records] 
         │
         ▼
[Tools: Set Variables] 
  ├── createdAt (fallback: Submitted Time)
  ├── priority (nested if-expression)
  └── needsReview (fallback flag)
         │
         ▼
[Airtable: Update a Record]
  (Priority, Created At, Needs Review)
         │
         ▼
[Filter: Priority is P1 or P2]
         │
         ▼
[Email: Send an Email] (Alert on-call lead)
```

### Module Configurations

#### Module 1: Airtable `Watch Records` *(untested, verify in editor)*
- **Connection**: Connect your Airtable Personal Access Token (PAT).
- **Base**: `Robot Ops Incident & Escalation System`
- **Table**: `Tickets`
- **Trigger Field**: `Submitted Time` *(Created time field)*
- **View**: `Untriaged Tickets` *(Filter: Priority is empty)*
- **Max Records**: `5`

#### Module 2: Tools `Set Variables` *(untested, verify in editor)*
Create the following three variables:

1. **`createdAt`**:
   - Value: `if(empty(1.`Created At`); 1.`Submitted Time`; 1.`Created At`)`
2. **`priority`** (Generated directly by `src/make_expression.py` from `config/rules.yaml`):
   ```text
   if((lower(1.Category) = "safety stop" | contains(lower(1.Description); "injury") | contains(lower(1.Description); "collision") | contains(lower(1.Description); "safety") | contains(lower(1.Description); "e-stop") | contains(lower(1.Description); "hazard") | contains(lower(1.Description); "near-miss")); "P1"; if((lower(1.Category) = "software crash" & (contains(lower(1.Description); "hang") | contains(lower(1.Description); "deadlock") | contains(lower(1.Description); "frozen") | contains(lower(1.Description); "blackout") | contains(lower(1.Description); "segmentation fault"))); "P1"; if(((lower(1.Category) = "gripper / end-effector" | lower(1.Category) = "latency / connectivity" | lower(1.Category) = "navigation") & (contains(lower(1.Description); "slip") | contains(lower(1.Description); "drop") | contains(lower(1.Description); "spike") | contains(lower(1.Description); "packet loss") | contains(lower(1.Description); "drift") | contains(lower(1.Description); "jitter") | contains(lower(1.Description); "stuck") | contains(lower(1.Description); "timeout") | contains(lower(1.Description); "high ping"))); "P2"; if((lower(1.Category) = "feature request / enhancement" | contains(lower(1.Description); "request") | contains(lower(1.Description); "suggestion") | contains(lower(1.Description); "shortcut") | contains(lower(1.Description); "enhancement")); "P4"; "P3"))))
   ```
3. **`needsReview`**:
   - Value: `if(2.priority = "P3" & not(contains(lower(1.Description); "glitch") | contains(lower(1.Description); "flicker") | contains(lower(1.Description); "sluggish") | contains(lower(1.Description); "soiled") | contains(lower(1.Description); "drift") | contains(lower(1.Description); "artifact")); true; false)`

#### Module 3: Airtable `Update a Record` *(untested, verify in editor)*
- **Record ID**: `1.id`
- **Fields to Update**:
  - `Priority`: `2.priority`
  - `Created At`: `2.createdAt`
  - `Needs Review`: `2.needsReview`
  - `Status`: `Open`

#### Error Handler Route on Module 3:
- Right-click Module 3 -> **Add error handler** -> Select **Commit** or **Resume** directive.
- Attach an email alert or log entry to notify the operator if an update fails.

#### Module 4: Email Dispatch *(untested, verify in editor)*
- **Filter between Module 3 and Module 4**:
  - Condition: `2.priority` Equal to `P1` **OR** `2.priority` Equal to `P2`
- **Recommended Module**: Make's built-in **Email > Send an Email** (Requires zero OAuth permissions).
  - *Alternative*: **Gmail > Send an Email** (Requires Google OAuth consent setup).
- **To**: `[Your email address for testing]`
- **Subject**: `[{{2.priority}} ALERT] Robot Incident {{1.`Ticket ID`}} at {{1.Site}}`
- **Content (HTML)**:
  ```html
  <h3>INCIDENT ESCALATION DISPATCH</h3>
  <p><strong>SIMULATED INCIDENT DATA - FOR TESTING</strong></p>
  <ul>
    <li><strong>Ticket ID:</strong> {{1.`Ticket ID`}}</li>
    <li><strong>Priority:</strong> {{2.priority}}</li>
    <li><strong>Site:</strong> {{1.Site}}</li>
    <li><strong>Robot ID:</strong> {{1.`Robot ID`}}</li>
    <li><strong>Category:</strong> {{1.Category}}</li>
    <li><strong>Created At:</strong> {{2.createdAt}}</li>
  </ul>
  <p><strong>Description:</strong><br>{{1.Description}}</p>
  ```

---

## Scenario 2: SLA Watchdog (Scheduled Sweep)

### Architecture
Runs on a scheduled interval (e.g., every 15 minutes or via "Run once" manual trigger) to identify overdue, unescalated tickets. Dispatches a high-priority alert and stamps `Escalated = True` to prevent alert duplication.

### Flow Diagram
```
[Schedule Trigger] 
         │
         ▼
[Airtable: Search Records] (Filter: Breached, Unresolved, NOT Escalated)
         │
         ▼
[Email: Send an Email] (Alert On-Call Lead)
         │
         ▼
[Airtable: Update a Record] (Escalated = True, Escalated At = now)
```

### Module Configurations

#### Module 1: Schedule Trigger
- Schedule: Every 15 minutes (or manual "Run once").

#### Module 2: Airtable `Search Records` *(untested, verify in editor)*
- **Base**: `Robot Ops Incident & Escalation System`
- **Table**: `Tickets`
- **Filter Formula** *(Exact Airtable formula to paste)*:
  ```airtable
  AND(
    {Status} != "Resolved",
    NOT({Escalated}),
    OR(
      {Response Breached} = 1,
      {Resolution Breached} = 1
    )
  )
  ```
- **Limit**: `10`

#### Module 3: Email `Send an Email` *(untested, verify in editor)*
- **To**: `[Your email address for testing]`
- **Subject**: `[ESCALATION BREACH] {{2.Priority}} Ticket {{2.`Ticket ID`}} Exceeded SLA`
- **Content (HTML)**:
  ```html
  <h2 style="color: #b30000;">SLA BREACH DETECTED BY WATCHDOG</h2>
  <p><strong>SIMULATED OPERATIONS ALERT</strong></p>
  <p>Ticket <strong>{{2.`Ticket ID`}}</strong> at <strong>{{2.Site}}</strong> has exceeded its SLA threshold without resolution.</p>
  <p><strong>Priority:</strong> {{2.Priority}}<br>
  <strong>Category:</strong> {{2.Category}}<br>
  <strong>Robot ID:</strong> {{2.`Robot ID`}}<br>
  <strong>Description:</strong> {{2.Description}}</p>
  <p><em>Record has been marked as Escalated in Airtable.</em></p>
  ```

#### Module 4: Airtable `Update a Record` *(untested, verify in editor)*
- **Record ID**: `2.id`
- **Fields to Update**:
  - `Escalated`: `true` (Checked)
  - `Escalated At`: `{{now}}`

#### Verification Note:
Compare your Make execution counts directly against `python src/watchdog.py`. Both evaluate the exact same formula logic.

---

## Scenario 3: Weekly VoC Review Digest (Optional)

> **Implementation Note**: The Python pipeline (`src/voc_report.py` and `src/push_voc_to_notion.py`) is the primary, reliable path for computing multi-dimensional statistics (e.g. median resolution times, firmware cross-tabs) without consuming Make operations. Use this Make scenario only if you prefer an automated no-code trigger.

### Minimal Make Flow
1. **Trigger**: Schedule > Every Monday at 08:00 AM.
2. **Airtable Search Records**: Pull records where `IS_AFTER({Created At}, DATEADD(TODAY(), -7, 'days'))`.
3. **Numeric Aggregator**: Count total records and records where `Resolution Breached = 1`.
4. **Notion Create a Database Item**: Create an entry in `Weekly VoC Reviews` database populated with the aggregated metrics.

