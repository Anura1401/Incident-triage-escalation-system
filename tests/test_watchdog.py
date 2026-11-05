"""
Integration Tests for Simulated SLA Watchdog.
Verifies first-run breach detection, state update, and second-run deduplication.
"""

from pathlib import Path
import pandas as pd
import pytest

from src.watchdog import run_watchdog, ESCALATED_CSV, TICKETS_CSV
from src.generate_tickets import generate_dataset


def test_watchdog_escalation_and_deduplication(tmp_path, monkeypatch):
    # Ensure tickets.csv exists
    if not TICKETS_CSV.exists():
        df = generate_dataset(num_tickets=200, seed=42)
        TICKETS_CSV.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(TICKETS_CSV, index=False)

    # Clean up any existing escalated CSV before test
    if ESCALATED_CSV.exists():
        ESCALATED_CSV.unlink()

    now_eval = "2026-11-05T18:00:00Z"

    # Sweep 1: Should find open breached tickets and escalate them
    escalated_1, total_breached = run_watchdog(now_str=now_eval)
    assert escalated_1 > 0, "First sweep should escalate at least one overdue ticket"
    assert ESCALATED_CSV.exists(), "tickets_escalated.csv should be created"

    # Verify escalated file content
    df_esc = pd.read_csv(ESCALATED_CSV)
    assert "Escalated" in df_esc.columns
    assert "Escalated At" in df_esc.columns
    escalated_count_in_file = df_esc["Escalated"].apply(lambda x: str(x).lower() == "true").sum()
    assert escalated_count_in_file == escalated_1

    # Sweep 2: Should find 0 new tickets (strict deduplication)
    escalated_2, _ = run_watchdog(now_str=now_eval)
    assert escalated_2 == 0, f"Second sweep should escalate 0 tickets due to deduplication, but escalated {escalated_2}"

