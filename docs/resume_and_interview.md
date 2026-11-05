# Operations Portfolio: Resume Bullets & Interview Preparation
**Candidate Guide | Robot-Teleoperation Field Incident Triage & Escalation System**  
*Notice: All operational figures and system designs are derived strictly from simulated synthetic testing.*

---

## 1. Resume Bullets (Max 20 Words Each)

> *Guidelines: Tailored for an Operations Intern application at a robotics/hardware startup. Placeholders `[ ]` indicate metrics to verify in your own Airtable/Make execution runs.*

- **Bullet 1 (Triage & Architecture)**:  
  *Built an automated triage system routing 200 simulated teleop robot incidents across 4 priority levels using Make.com and Airtable.*  
  *(19 words)*

- **Bullet 2 (SLA Watchdog & Monitoring)**:  
  *Engineered an SLA watchdog sweep tracking response deadlines across 25 robots, achieving `[100%]` duplicate-free escalation in testing.*  
  *(17 words)*

- **Bullet 3 (Voice-of-Customer & Backlog)**:  
  *Automated weekly VoC analytics synthesizing fleet failure modes into Notion engineering backlog items, surfacing a `[73%]` firmware latency regression.*  
  *(18 words)*

---

## 2. Technical Skills Line

**Operations & Workflow Automation:** Python (Pandas, Pytest), Airtable (Relational Schema, Formulas, Views), Make.com (Integrations, Triage Logic), Notion (VoC Databases), SLA Management, Incident Routing.

---

## 3. Six Targeted Interview Questions & Honest Answer Frameworks

### Q1: Where did your SLA thresholds (e.g., 15 minutes for P1, 2 hours for P2) come from?
> **Honest Answer**:  
> "They are explicit design assumptions I established for this simulation project, not commercial policies. In remote robot teleoperation, safety stops and obstacle collisions demand rapid intervention within 15 minutes because idle robots directly halt customer fulfillment lanes, whereas ergonomics suggestions can wait 120 hours. In an actual operations role, I would calibrate these thresholds against real customer service level agreements (SLAs), operator shift coverage, and hardware telemetry availability."

### Q2: You embedded deliberate patterns into your dataset. Why, and what does the analysis show?
> **Honest Answer**:  
> "I seeded 200 tickets with three non-obvious operational anomalies to demonstrate a complete Voice-of-Customer review loop:
> 1. **Component Friction**: Gripper slippage accounted for 32% of all incidents.
> 2. **Firmware Regression**: Robots running firmware v2.3 generated 73% of all latency tickets.
> 3. **Site Variance**: Site Beta in Detroit generated 1.73x its fair share of high-severity P1/P2 incidents.  
> The weekly VoC review automatically converts these findings into engineering asks—such as reverting video streaming buffer changes on v2.3 and scheduling a physical site audit at Site Beta."

### Q3: Why did you use a single Set Variable module in Make.com rather than a multi-branch Router?
> **Honest Answer**:  
> "In Make.com, routers evaluate each branch independently and execute all branches whose filter conditions evaluate to true. If an incident contains both a safety term and a hardware degradation keyword, a router would fire multiple branches, causing race conditions, multiple updates to Airtable, and duplicate alert emails. Using a single nested `if(...)` expression inside a Set Variable module guarantees deterministic, single-branch classification, saves operations, and ensures atomic Airtable updates."

### Q4: How does your SLA Watchdog prevent sending repeated duplicate alerts?
> **Honest Answer**:  
> "The watchdog queries Airtable using an exact filter formula: `AND({Status} != 'Resolved', NOT({Escalated}), OR({Response Breached} = 1, {Resolution Breached} = 1))`. When an overdue record is flagged, the automation dispatches the alert and immediately sets `Escalated = True` and records `Escalated At`. On the next sweep 15 minutes later, the record no longer matches `NOT({Escalated})` and is ignored. In my Python simulation, the first sweep escalated 12 overdue tickets, and the second sweep escalated zero, verifying duplicate-free behavior."

### Q5: What would you change if you were deploying this with real teleoperation fleet data?
> **Honest Answer**:  
> "Four key architectural upgrades:
> 1. **Direct Edge Webhooks**: Transition from manual form intake to automated ROS2 telemetry webhooks firing directly from the robot edge compute when an e-stop or latency spike occurs.
> 2. **LLM Semantic Parsing**: Supplement regex keyword matching with an LLM classifier to interpret messy, free-text operator comments.
> 3. **Notification Channels**: Route high-priority P1 alerts to PagerDuty or Slack on-call channels instead of personal email.
> 4. **Shift Schedule Awareness**: Integrate operational calendar logic into SLA formulas so that business-hours SLAs don't falsely breach over non-operating overnight hours."

### Q6: How did you ensure data integrity and consistency between your Python scripts and Airtable?
> **Honest Answer**:  
> "I built `config/rules.yaml` as the single source of truth for all priorities, SLA durations, and keyword taxonomies. The Python SLA module (`src/sla.py`) and the Airtable formula fields implement the exact same mathematical logic. Additionally, I wrote a test suite of 35 automated pytest cases that validate rule precedence, verify SLA calculations against fixed hand-calculated timestamps, and ensure that every generated ticket matches the classification engine."

