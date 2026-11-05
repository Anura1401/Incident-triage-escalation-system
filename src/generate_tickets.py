"""
Synthetic Ticket Dataset Generator for Teleoperation Operations Simulation.
ALL DATA IS SYNTHETIC. NO REAL CUSTOMER, ROBOT, OR INCIDENT DATA.
"""

import sys
from pathlib import Path

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timedelta
import random
from typing import Dict, List
import pandas as pd

from src.rules import classify
from src.sla import response_breached, resolution_breached

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Fixed seed for reproducibility
RANDOM_SEED = 42

TOTAL_TICKETS = 200
END_DATE = datetime(2026, 11, 5, 18, 0, 0)
START_DATE = END_DATE - timedelta(weeks=8)

# 5 Fictional Sites
SITES = [
    "Site Alpha (Austin Logistics)",
    "Site Beta (Detroit Auto)",
    "Site Gamma (Reno Fulfillment)",
    "Site Delta (Phoenix Parcel)",
    "Site Epsilon (Seattle Depots)",
]

# Fixed Robot-to-Site Map: 25 robots, exactly 5 robots per site
SITE_ROBOT_MAP: Dict[str, List[str]] = {
    "Site Alpha (Austin Logistics)": [f"ROBOT-10{i}" for i in range(1, 6)],
    "Site Beta (Detroit Auto)": [f"ROBOT-10{i}" for i in range(6, 10)] + ["ROBOT-110"],
    "Site Gamma (Reno Fulfillment)": [f"ROBOT-11{i}" for i in range(1, 6)],
    "Site Delta (Phoenix Parcel)": [f"ROBOT-11{i}" for i in range(6, 10)] + ["ROBOT-120"],
    "Site Epsilon (Seattle Depots)": [f"ROBOT-12{i}" for i in range(1, 6)],
}

ROLES = ["Field Engineer", "Customer Ops", "Teleoperation Operator"]
FIRMWARE_VERSIONS = ["v2.1", "v2.2", "v2.3"]

# 9 Categories
CATEGORIES = [
    "Safety Stop",
    "Gripper / End-Effector",
    "Latency / Connectivity",
    "Navigation",
    "Camera / Sensor",
    "Software Crash",
    "Operator Tool UI",
    "Data Capture Quality",
    "Feature Request / Enhancement",
]

# Category realistic descriptions with embedded keywords
CATEGORY_DESCRIPTIONS = {
    "Safety Stop": [
        "Emergency e-stop triggered when pedestrian entered 2m exclusion envelope near picking cell.",
        "Safety stop engaged automatically after obstacle proximity sensor threshold tripped on aisle 4.",
        "Operator initiated safety shutdown due to unexpected pallet de-stacking collision risk.",
        "Laser safety scanner intermittent warning triggered hardware safety latch during pallet turn.",
        "Near-miss incident reported when autonomous mobile base paused abruptly near crossing aisle.",
    ],
    "Gripper / End-Effector": [
        "Pneumatic gripper lost pressure mid-stroke causing carton drop into reject bin.",
        "Parallel jaw slip detected while grasping slippery plastic container at workstation.",
        "Suction cup seal drop on uneven corrugated cardboard surface during depalletizing.",
        "Gripper encoder reported false open status during heavy payload pick, causing slip.",
        "Fingertip force sensor calibration drift caused gripper to slip and abort item transfer.",
    ],
    "Latency / Connectivity": [
        "Teleop round-trip latency spike to 620ms caused operator motion overshooting during docking.",
        "Cellular uplink packet loss exceeding 8% forced teleop video stream frame drops.",
        "WebRTC video stream high ping and jitter caused 4-second freeze during warehouse traverse.",
        "Network jitter caused control command buffering and sudden robot jerk motion in bay 2.",
        "Command packet timeout between control console and base controller during fine manipulation.",
    ],
    "Navigation": [
        "AMR wheel odometry drift caused robot to fail dock approach by 15cm at charging station.",
        "Robot got stuck in main corridor due to dynamic ghost obstacle reflection from wet floor.",
        "Path planner timeout during high-density pedestrian congestion near packing station.",
        "LiDAR localization drift detected in wide open aisle with minimal static landmarks.",
    ],
    "Camera / Sensor": [
        "Overhead mast camera feed flickering over Gigabit Ethernet connection.",
        "Depth sensor point cloud saturation under direct warehouse skylight illumination.",
        "Wrist camera lens soiled by cardboard dust obscuring grasp target alignment.",
        "IMU sensor drift flag raised during stationary idle period at inspection cell.",
    ],
    "Software Crash": [
        "Teleop daemon crashed with segmentation fault on edge compute node during grasp.",
        "Motor controller driver deadlock following rapid forward-reverse velocity toggle.",
        "Telemetry logging process hung with 100% CPU usage causing system freeze.",
        "Edge navigation container experienced deadlock during dynamic map re-localization.",
    ],
    "Operator Tool UI": [
        "Cockpit UI failed to render real-time gripper force gauge overlay on operator monitor.",
        "Virtual joystick control widget sluggish on secondary teleoperation workstation.",
        "Audio feedback stream missing when operator triggered warning chime alert.",
        "Secondary camera stream window unclosable after cockpit layout profile reset.",
    ],
    "Data Capture Quality": [
        "Training data bagfile dropped depth sensor frames during grasp phase recording.",
        "Compressed video stream compression artifacts degrade post-mission vision telemetry.",
        "LiDAR timestamp desync detected against wheel encoder log stream.",
    ],
    "Feature Request / Enhancement": [
        "Operator request for keyboard shortcut to toggle mast illumination light levels.",
        "Suggestion to add haptic rumble feedback on joystick controller during slip warning.",
        "Request bird-eye view perspective camera stitching in teleoperation console UI.",
        "Enhancement request: add one-click auto-centering button for pan-tilt-zoom camera.",
    ],
}

# Ambiguous descriptions with NO keywords for the R4 fallback
AMBIGUOUS_DESCRIPTIONS = [
    "Operator observed irregular operational cadence during standard shift turnover.",
    "System log showed informational telemetry code 404 during idle standby mode.",
    "Routine physical inspection noted cosmetic scuff marks on lower bumper shroud.",
    "Shift handover note: robot completed assigned task queue with normal diagnostics.",
    "Auxiliary diagnostic interface displayed advisory notice upon morning power cycling.",
    "General inquiry regarding telemetry retention schedule for historical missions.",
]


def generate_dataset(num_tickets: int = TOTAL_TICKETS, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Generate reproducible synthetic tickets dataset."""
    random.seed(seed)
    records = []
    total_seconds = int((END_DATE - START_DATE).total_seconds())

    # Exactly 40 tickets per site for 200 tickets (20% share each)
    site_targets = {s: num_tickets // len(SITES) for s in SITES}
    rem = num_tickets - sum(site_targets.values())
    for s in SITES[:rem]:
        site_targets[s] += 1

    site_pool = []
    for s, count in site_targets.items():
        site_pool.extend([s] * count)
    random.shuffle(site_pool)

    # We want ~64-66 Gripper tickets total (32-33% of 200)
    # Site Beta gets 18 Gripper, other 4 sites get ~48 Gripper (~12 each)
    gripper_target_beta = 18
    gripper_target_others = 46
    gripper_count_beta = 0
    gripper_count_others = 0

    # Pick 6 indices for ambiguous descriptions across non-Beta sites to test R4 fallback
    non_beta_indices = [idx for idx, s in enumerate(site_pool) if s != "Site Beta (Detroit Auto)"]
    ambiguous_indices = set(random.sample(non_beta_indices, k=6))

    for i in range(1, num_tickets + 1):
        ticket_id = f"TIC-{1000 + i}"
        site = site_pool[i - 1]
        robot_id = random.choice(SITE_ROBOT_MAP[site])
        role = random.choice(ROLES)

        is_ambiguous = (i - 1) in ambiguous_indices

        if is_ambiguous:
            # R4 Fallback: Category is minor, description has NO keywords
            cat = random.choice(["Camera / Sensor", "Operator Tool UI", "Data Capture Quality"])
            desc = random.choice(AMBIGUOUS_DESCRIPTIONS)
            fw = random.choice(FIRMWARE_VERSIONS)
        elif site == "Site Beta (Detroit Auto)":
            # Pattern C: Beta gets high P1/P2 concentration via Safety Stop, Software Crash with deadlock, Gripper, Latency
            # Target: ~35-37 P1/P2 out of 40 (~90%)
            if gripper_count_beta < gripper_target_beta:
                cat = "Gripper / End-Effector"
                gripper_count_beta += 1
            else:
                cat = random.choices(
                    ["Safety Stop", "Software Crash", "Latency / Connectivity", "Camera / Sensor"],
                    weights=[0.45, 0.35, 0.15, 0.05]
                )[0]
            desc = random.choice(CATEGORY_DESCRIPTIONS[cat])
            if cat == "Latency / Connectivity":
                fw = random.choices(FIRMWARE_VERSIONS, weights=[0.18, 0.14, 0.68])[0]
            else:
                fw = random.choice(FIRMWARE_VERSIONS)
        else:
            # Other sites: produce healthy mix of P3 (UI, Camera, Data Capture), P4 (Feature Request),
            # and their share of Gripper / Latency / Navigation
            if gripper_count_others < gripper_target_others and random.random() < 0.40:
                cat = "Gripper / End-Effector"
                gripper_count_others += 1
            else:
                cat = random.choices(
                    [
                        "Operator Tool UI",
                        "Camera / Sensor",
                        "Feature Request / Enhancement",
                        "Data Capture Quality",
                        "Latency / Connectivity",
                        "Navigation",
                        "Safety Stop",
                        "Software Crash",
                    ],
                    weights=[0.24, 0.22, 0.16, 0.14, 0.12, 0.08, 0.02, 0.02]
                )[0]
            desc = random.choice(CATEGORY_DESCRIPTIONS[cat])

            # Pattern B: Latency tickets are mostly v2.3 (~68-72%)
            if cat == "Latency / Connectivity":
                fw = random.choices(FIRMWARE_VERSIONS, weights=[0.18, 0.14, 0.68])[0]
            else:
                fw = random.choice(FIRMWARE_VERSIONS)

        # STRICTLY CLASSIFY USING src.rules.classify
        priority, needs_review, _ = classify(cat, desc)

        # Status distribution: ~90% Resolved, ~10% Open or In Progress
        # For open tickets, place their creation time within the last 1 to 4 days so they reflect active fleet operations
        status_dice = random.random()
        if status_dice < 0.90:
            status = "Resolved"
            offset_sec = random.randint(0, total_seconds)
            created_at = START_DATE + timedelta(seconds=offset_sec)
        elif status_dice < 0.96:
            status = "In Progress"
            # Active in progress tickets created within last 36 hours
            recent_sec = random.randint(1800, 36 * 3600)
            created_at = END_DATE - timedelta(seconds=recent_sec)
        else:
            status = "Open"
            # Newly opened tickets created within last 18 hours
            recent_sec = random.randint(600, 18 * 3600)
            created_at = END_DATE - timedelta(seconds=recent_sec)

        # Pattern D: SLA breaches concentrated in P2 (~40-50%), lower for P1 (~15-25%), P3/P4 (<15%)
        # Response SLA (hours): P1: 0.25, P2: 2.0, P3: 8.0, P4: 24.0
        # Resolution SLA (hours): P1: 4, P2: 12, P3: 48, P4: 120
        if priority == "P1":
            breach_target = (random.random() < 0.18)
            if breach_target:
                resp_hours = random.uniform(0.26, 0.45)
                res_hours = random.uniform(4.2, 6.5)
            else:
                resp_hours = random.uniform(0.04, 0.21)
                res_hours = random.uniform(0.8, 3.5)
        elif priority == "P2":
            breach_target = (random.random() < 0.35)
            if breach_target:
                resp_hours = random.uniform(2.1, 4.0)
                res_hours = random.uniform(12.5, 22.0)
            else:
                resp_hours = random.uniform(0.2, 1.7)
                res_hours = random.uniform(2.5, 11.0)
        elif priority == "P3":
            breach_target = (random.random() < 0.08)
            if breach_target:
                resp_hours = random.uniform(8.3, 13.0)
                res_hours = random.uniform(49.0, 70.0)
            else:
                resp_hours = random.uniform(0.8, 7.0)
                res_hours = random.uniform(6.0, 40.0)
        else:  # P4
            breach_target = (random.random() < 0.05)
            if breach_target:
                resp_hours = random.uniform(24.5, 34.0)
                res_hours = random.uniform(122.0, 145.0)
            else:
                resp_hours = random.uniform(1.5, 20.0)
                res_hours = random.uniform(18.0, 100.0)

        first_resp_dt = created_at + timedelta(hours=resp_hours)

        if status == "Resolved":
            resolved_dt = first_resp_dt + timedelta(hours=max(0.25, res_hours - resp_hours))
        else:
            resolved_dt = None
            if random.random() < 0.40:
                first_resp_dt = None

        records.append({
            "Ticket ID": ticket_id,
            "Created At": created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Reporter Role": role,
            "Site": site,
            "Robot ID": robot_id,
            "Category": cat,
            "Description": desc,
            "Firmware Version": fw,
            "Priority": priority,
            "Status": status,
            "First Response At": first_resp_dt.strftime("%Y-%m-%dT%H:%M:%SZ") if first_resp_dt else "",
            "Resolved At": resolved_dt.strftime("%Y-%m-%dT%H:%M:%SZ") if resolved_dt else "",
            "Needs Review": str(needs_review),
            "Synthetic Data Label": "SIMULATED SYNTHETIC DATA",
        })

    df = pd.DataFrame(records)
    df = df.sort_values(by="Created At").reset_index(drop=True)
    return df


def print_summary(df: pd.DataFrame) -> None:
    """Print statistical breakdown confirming dataset patterns A-D."""
    print("=" * 65)
    print("SYNTHETIC INCIDENT DATASET PATTERN VERIFICATION SUMMARY")
    print("=" * 65)
    total = len(df)
    print(f"Total Synthetic Records: {total}")

    # Pattern A
    print("\n--- Pattern A: Category Frequency (Gripper Dominance) ---")
    cat_counts = df["Category"].value_counts()
    for cat, cnt in cat_counts.items():
        print(f"  {cat:<32}: {cnt:>3} ({cnt/total*100:5.1f}%)")

    # Pattern B
    print("\n--- Pattern B: Latency Tickets vs Firmware Version ---")
    latency_df = df[df["Category"] == "Latency / Connectivity"]
    fw_lat = latency_df["Firmware Version"].value_counts()
    for fw, cnt in fw_lat.items():
        print(f"  {fw:<10}: {cnt:>3} ({cnt/len(latency_df)*100:5.1f}% of latency tickets)")

    # Pattern C
    print("\n--- Pattern C: Site Ticket Share vs P1/P2 Incident Share ---")
    high_pri = df[df["Priority"].isin(["P1", "P2"])]
    site_all = df["Site"].value_counts()
    site_high = high_pri["Site"].value_counts()
    for s in SITES:
        total_site = site_all.get(s, 0)
        high_site = site_high.get(s, 0)
        overall_share = total_site / total * 100
        p1p2_share = high_site / len(high_pri) * 100
        ratio = p1p2_share / overall_share if overall_share > 0 else 0
        print(f"  {s:<30}: Total={total_site} ({overall_share:4.1f}%), P1/P2={high_site} ({p1p2_share:4.1f}%), Ratio={ratio:4.2f}x")

    # Pattern D
    print("\n--- Pattern D: SLA Breach Rate by Priority ---")
    # Compute breach flags using sla.py logic
    breach_data = []
    for _, row in df.iterrows():
        r_br = response_breached(row["Created At"], row["Priority"], row["First Response At"] or None, END_DATE)
        res_br = resolution_breached(row["Created At"], row["Priority"], row["Status"], row["Resolved At"] or None, END_DATE)
        breached = r_br or res_br
        breach_data.append(breached)
    df["Any_Breached"] = breach_data

    for p in ["P1", "P2", "P3", "P4"]:
        sub = df[df["Priority"] == p]
        br_cnt = sub["Any_Breached"].sum()
        rate = (br_cnt / len(sub) * 100) if len(sub) > 0 else 0
        print(f"  {p:<5}: {len(sub):>3} tickets | Breached={br_cnt:>2} ({rate:5.1f}%)")

    # Needs review
    nr_cnt = (df["Needs Review"] == "True").sum()
    print(f"\nTickets Flagged 'Needs Review': {nr_cnt} ({nr_cnt/total*100:4.1f}%)")
    print("=" * 65)


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = generate_dataset()
    csv_path = DATA_DIR / "tickets.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved dataset to: {csv_path}")
    print_summary(df)


if __name__ == "__main__":
    main()
