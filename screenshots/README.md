# Portfolio Evidence Checklist (Screenshots)
**Evidence Artifacts to Capture After Completing No-Code Configuration**  
> **SECURITY NOTICE: NEVER EXPOSE SECRETS IN SCREENSHOTS.**  
> Before capturing images, blur or crop out Airtable Personal Access Tokens (PAT), Make webhook URLs, and personal API tokens.

---

## Required Screenshot Deliverables

Capture these 6 clean images and place them in this `screenshots/` directory:

| Filename | Subject Matter | What to Highlight |
| :--- | :--- | :--- |
| `01_airtable_base_schema.png` | **Airtable Grid View** | Open the `Tickets` table in Airtable. Show calculated formula columns (`SLA Response Due`, `Response Breached`, `Time to Resolve (hours)`) with populated rows. |
| `02_airtable_intake_form.png` | **Intake Form View** | Open the public share link of `Field Incident Intake Form`. Show the user-facing inputs and the synthetic data notice banner. |
| `03_make_scenario1_canvas.png` | **Make Scenario 1 Canvas** | Open Scenario 1 in the Make editor. Capture the full canvas flow: Airtable trigger -> Set Variables -> Airtable Update -> Email module. |
| `04_make_scenario1_execution.png` | **Make Execution History** | Open the **History** tab of Scenario 1. Click a completed execution to show green checkmarks and processed record bundles. |
| `05_p1_alert_email.png` | **High-Priority Alert Dispatch** | Open the `[P1 ALERT]` email received in your inbox. Show the formatted incident breakdown and escalation details. |
| `06_notion_voc_page.png` | **Notion VoC Review Board** | Open your Notion `Weekly VoC Reviews` database or page. Show the 6 structured review sections and engineering backlog items. |

---

## Verification Guidelines
1. Ensure all displayed data clearly bears the `SIMULATED SYNTHETIC DATA` label.
2. Confirm formula outputs match the verification reference table in `specs/airtable_schema.md`.
3. Keep filenames exactly as listed above for direct linking in your GitHub README.

