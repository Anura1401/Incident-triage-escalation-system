"""
Unit Tests for Incident Triage Classification Rules Engine.
Validates precedence, case-insensitivity, keyword matching, and fallback review flags.
"""

import pytest
from src.rules import classify


def test_r0_safety_stop_category():
    # Category Safety Stop alone must yield P1
    p, nr, r = classify("Safety Stop", "Operator noticed routine sensor alert.")
    assert p == "P1"
    assert nr is False
    assert r == "R0"


def test_r0_safety_keyword_override():
    # Any category mentioning collision/injury becomes P1
    p, nr, r = classify("Operator Tool UI", "Near-miss collision with pallet rack.")
    assert p == "P1"
    assert nr is False
    assert r == "R0"


def test_r0_case_insensitivity():
    # Mixed case safety keywords
    p, nr, r = classify("camera / sensor", "E-STOP ACTIVATED DUE TO HAZARD ON FLOOR")
    assert p == "P1"
    assert nr is False
    assert r == "R0"


def test_r0_precedence_over_latency():
    # Precedence: A Safety Stop whose description contains "latency" or "spike" is P1, not P2
    p, nr, r = classify("Safety Stop", "Teleop latency spike caused safety barrier trip.")
    assert p == "P1"
    assert nr is False
    assert r == "R0"


def test_r1_software_crash_deadlock():
    # Software crash with deadlock keyword -> P1
    p, nr, r = classify("Software Crash", "Motor controller driver deadlock following toggled speed.")
    assert p == "P1"
    assert nr is False
    assert r == "R1"


def test_r1_software_crash_segmentation_fault():
    # Software crash with segmentation fault -> P1
    p, nr, r = classify("Software Crash", "Teleop daemon crashed with segmentation fault.")
    assert p == "P1"
    assert nr is False
    assert r == "R1"


def test_r2_gripper_slip():
    # Gripper category with slip keyword -> P2
    p, nr, r = classify("Gripper / End-Effector", "Parallel jaw slip detected while grasping container.")
    assert p == "P2"
    assert nr is False
    assert r == "R2"


def test_r2_latency_spike():
    # Latency category with spike keyword -> P2
    p, nr, r = classify("Latency / Connectivity", "Teleop round-trip latency spike to 620ms.")
    assert p == "P2"
    assert nr is False
    assert r == "R2"


def test_r2_navigation_stuck():
    # Navigation category with stuck keyword -> P2
    p, nr, r = classify("Navigation", "Robot got stuck in main corridor due to obstacle.")
    assert p == "P2"
    assert nr is False
    assert r == "R2"


def test_r2_non_matching_category_with_slip_keyword():
    # "slip" in Operator Tool UI does NOT trigger R2 (R2 requires Gripper/Latency/Nav)
    # It falls through to R4 -> P3
    p, nr, r = classify("Operator Tool UI", "Operator noted slipping grip on virtual slider control.")
    assert p == "P3"
    assert r == "R4"


def test_r3_feature_request_category():
    # Feature request category -> P4
    p, nr, r = classify("Feature Request / Enhancement", "Add dark mode to cockpit.")
    assert p == "P4"
    assert nr is False
    assert r == "R3"


def test_r3_enhancement_keyword():
    # Description contains shortcut/request -> P4
    p, nr, r = classify("Operator Tool UI", "Request keyboard shortcut for camera tilt.")
    assert p == "P4"
    assert nr is False
    assert r == "R3"


def test_r4_fallback_recognized_minor_keyword():
    # Known minor issue: Camera with soiled lens -> P3, needs_review is False
    p, nr, r = classify("Camera / Sensor", "Wrist camera lens soiled by cardboard dust.")
    assert p == "P3"
    assert nr is False
    assert r == "R4"


def test_r4_fallback_ambiguous_no_keywords():
    # Ambiguous description with NO keywords -> P3, needs_review is True
    p, nr, r = classify("Camera / Sensor", "Operator observed irregular operational cadence during standard shift.")
    assert p == "P3"
    assert nr is True
    assert r == "R4"


def test_empty_inputs_safe_fallback():
    # Empty strings handled safely
    p, nr, r = classify("", "")
    assert p == "P3"
    assert nr is True
    assert r == "R4"

