"""
Integration Tests for Synthetic Ticket Dataset Generator.
Verifies dataset size, schema integrity, chronological ordering, and statistical patterns A-D.
"""

from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import pytest

from src.generate_tickets import generate_dataset, SITE_ROBOT_MAP, END_DATE
from src.rules import classify
from src.sla import response_breached, resolution_breached


@pytest.fixture(scope="module")
def df_generated():
    return generate_dataset(num_tickets=200, seed=42)


def test_dataset_size_and_columns(df_generated):
    assert len(df_generated) == 200
    expected_cols = [
        "Ticket ID",
        "Created At",
        "Reporter Role",
        "Site",
        "Robot ID",
        "Category",
        "Description",
        "Firmware Version",
        "Priority",
        "Status",
        "First Response At",
        "Resolved At",
        "Needs Review",
        "Synthetic Data Label",
    ]
    for col in expected_cols:
        assert col in df_generated.columns


def test_priority_values_valid(df_generated):
    valid_priorities = {"P1", "P2", "P3", "P4"}
    actual_priorities = set(df_generated["Priority"].unique())
    assert actual_priorities.issubset(valid_priorities)


def test_every_priority_matches_rules_engine(df_generated):
    # Strict requirement: Every ticket priority MUST equal classify() output
    for _, row in df_generated.iterrows():
        expected_pri, expected_nr, _ = classify(row["Category"], row["Description"])
        assert row["Priority"] == expected_pri
        assert str(row["Needs Review"]) == str(expected_nr)


def test_timestamp_integrity(df_generated):
    for _, row in df_generated.iterrows():
        created = datetime.fromisoformat(row["Created At"].replace("Z", "+00:00"))
        status = row["Status"]

        if row["First Response At"] != "":
            first_resp = datetime.fromisoformat(row["First Response At"].replace("Z", "+00:00"))
            assert first_resp >= created, f"First response before created in {row['Ticket ID']}"

        if status == "Resolved":
            assert row["Resolved At"] != "", f"Resolved ticket missing Resolved At in {row['Ticket ID']}"
            assert row["First Response At"] != "", f"Resolved ticket missing First Response At in {row['Ticket ID']}"
            resolved = datetime.fromisoformat(row["Resolved At"].replace("Z", "+00:00"))
            first_resp = datetime.fromisoformat(row["First Response At"].replace("Z", "+00:00"))
            assert resolved >= first_resp, f"Resolved before first response in {row['Ticket ID']}"
        else:
            assert row["Resolved At"] == "", f"Open ticket has Resolved At in {row['Ticket ID']}"


def test_robot_belongs_to_one_site_only(df_generated):
    # Verify fixed robot-to-site mapping: 25 robots, each belongs to exactly one site
    robot_sites = df_generated.groupby("Robot ID")["Site"].nunique()
    assert (robot_sites == 1).all()

    # Verify site mapping against master SITE_ROBOT_MAP
    for _, row in df_generated.iterrows():
        expected_robots = SITE_ROBOT_MAP[row["Site"]]
        assert row["Robot ID"] in expected_robots


def test_pattern_a_gripper_dominance(df_generated):
    # Pattern A: Gripper / End-Effector is 25-40% of all tickets
    gripper_count = (df_generated["Category"] == "Gripper / End-Effector").sum()
    gripper_pct = (gripper_count / len(df_generated)) * 100
    assert 25.0 <= gripper_pct <= 40.0, f"Gripper share was {gripper_pct:.1f}%"


def test_pattern_b_latency_firmware_v23_correlation(df_generated):
    # Pattern B: Latency tickets are mostly v2.3 (at least 55%)
    latency_df = df_generated[df_generated["Category"] == "Latency / Connectivity"]
    assert len(latency_df) > 0
    v23_count = (latency_df["Firmware Version"] == "v2.3").sum()
    v23_pct = (v23_count / len(latency_df)) * 100
    assert v23_pct >= 55.0, f"v2.3 share of latency was {v23_pct:.1f}%"


def test_pattern_c_beta_p1p2_hotspot(df_generated):
    # Pattern C: Site Beta has ~20% total share, but P1/P2 share is at least 1.4x its fair share
    total = len(df_generated)
    beta_total = (df_generated["Site"] == "Site Beta (Detroit Auto)").sum()
    beta_overall_share = beta_total / total * 100

    high_pri = df_generated[df_generated["Priority"].isin(["P1", "P2"])]
    beta_high = (high_pri["Site"] == "Site Beta (Detroit Auto)").sum()
    beta_high_share = beta_high / len(high_pri) * 100

    ratio = beta_high_share / beta_overall_share
    assert ratio >= 1.40, f"Beta P1/P2 ratio was {ratio:.2f}x (expected >= 1.40x)"


def test_pattern_d_p2_highest_breach_rate(df_generated):
    # Pattern D: P2 breach rate highest among priorities
    breach_rates = {}
    for p in ["P1", "P2", "P3", "P4"]:
        sub = df_generated[df_generated["Priority"] == p]
        breaches = 0
        for _, r in sub.iterrows():
            r_br = response_breached(r["Created At"], r["Priority"], r["First Response At"] or None, END_DATE)
            res_br = resolution_breached(r["Created At"], r["Priority"], r["Status"], r["Resolved At"] or None, END_DATE)
            if r_br or res_br:
                breaches += 1
        breach_rates[p] = (breaches / len(sub) * 100) if len(sub) > 0 else 0.0

    assert breach_rates["P2"] > breach_rates["P1"]
    assert breach_rates["P2"] > breach_rates["P3"]
    assert breach_rates["P2"] > breach_rates["P4"]

