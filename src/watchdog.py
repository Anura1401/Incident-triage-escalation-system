"""
SLA Watchdog Simulation for Teleoperation Incident Management.
Finds open, breached tickets and escalates them with strict deduplication.
ALL DATA IS SYNTHETIC. NO REAL CUSTOMER OR ROBOT DATA.
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple
import pandas as pd

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sla import response_breached, resolution_breached

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TICKETS_CSV = DATA_DIR / "tickets.csv"
ESCALATED_CSV = DATA_DIR / "tickets_escalated.csv"


def run_watchdog(now_str: str = "2026-11-05T18:00:00Z") -> Tuple[int, int]:
    """
    Run the watchdog escalation sweep.

    Returns:
        (newly_escalated_count, total_breached_open_count)
    """
    source_csv = ESCALATED_CSV if ESCALATED_CSV.exists() else TICKETS_CSV
    if not source_csv.exists():
        raise FileNotFoundError(f"Input file not found: {source_csv}. Run src/generate_tickets.py first.")

    df = pd.read_csv(source_csv)

    # Ensure Escalated columns exist
    if "Escalated" not in df.columns:
        df["Escalated"] = False
    else:
        # Normalize boolean values
        df["Escalated"] = df["Escalated"].apply(lambda x: str(x).strip().lower() in ("true", "1", "yes"))

    if "Escalated At" not in df.columns:
        df["Escalated At"] = ""

    newly_escalated = []
    total_breached_open = 0

    print("=" * 65)
    print("SLA WATCHDOG EXECUTION LOG")
    print(f"Sweep Timestamp: {now_str}")
    print(f"Reading from   : {source_csv.name}")
    print("=" * 65)

    for idx, row in df.iterrows():
        status = str(row.get("Status", "")).strip()
        if status.lower() == "resolved":
            continue

        created_at = row["Created At"]
        priority = row["Priority"]
        first_resp = row.get("First Response At")
        first_resp = str(first_resp) if pd.notna(first_resp) and str(first_resp).strip() != "" else None
        resolved_at = row.get("Resolved At")
        resolved_at = str(resolved_at) if pd.notna(resolved_at) and str(resolved_at).strip() != "" else None

        r_breached = response_breached(created_at, priority, first_resp, now_str)
        res_breached = resolution_breached(created_at, priority, status, resolved_at, now_str)

        if r_breached or res_breached:
            total_breached_open += 1
            is_already_escalated = bool(row["Escalated"])

            if not is_already_escalated:
                newly_escalated.append(idx)
                breach_reasons = []
                if r_breached:
                    breach_reasons.append("FIRST-RESPONSE SLA EXCEEDED")
                if res_breached:
                    breach_reasons.append("RESOLUTION SLA EXCEEDED")

                print(f"[ESCALATION ALERT] Ticket {row['Ticket ID']} | Priority: {priority} | Site: {row['Site']}")
                print(f"  Robot ID     : {row['Robot ID']}")
                print(f"  Category     : {row['Category']}")
                print(f"  Created At   : {created_at}")
                print(f"  Breach Type  : {' & '.join(breach_reasons)}")
                print(f"  Description  : {row['Description']}")
                print(f"  Action       : Escalation dispatched to On-Call Lead. Marked Escalated=True.\n")

    if newly_escalated:
        # Mark as escalated
        df.loc[newly_escalated, "Escalated"] = True
        df.loc[newly_escalated, "Escalated At"] = now_str
        df.to_csv(ESCALATED_CSV, index=False)
        print(f"Summary: {len(newly_escalated)} ticket(s) newly escalated. Saved to {ESCALATED_CSV.name}.")
    else:
        print("Summary: 0 new tickets escalated. Deduplication active (all current breached tickets already escalated).")

    print("=" * 65)
    return len(newly_escalated), total_breached_open


def main():
    parser = argparse.ArgumentParser(description="Run simulated SLA Watchdog sweep.")
    parser.add_argument(
        "--now",
        type=str,
        default="2026-11-05T18:00:00Z",
        help="Evaluation timestamp (ISO format, e.g., 2026-11-05T18:00:00Z)"
    )
    args = parser.parse_args()
    run_watchdog(now_str=args.now)


if __name__ == "__main__":
    main()

