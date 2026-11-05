"""
Triage Rules Engine for Simulated Teleoperation Incident Management.
Single source of truth loaded from config/rules.yaml.
ALL DATA IS SYNTHETIC. NO REAL CUSTOMER OR ROBOT DATA.
"""

from pathlib import Path
from typing import Any, Dict, Tuple
import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "rules.yaml"


def load_rules(config_path: Path = CONFIG_PATH) -> Dict[str, Any]:
    """Load and parse the YAML rules configuration."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


_RULES_CONFIG = load_rules()


def get_rules_config() -> Dict[str, Any]:
    """Return the cached rules configuration."""
    return _RULES_CONFIG


def classify(category: str, description: str) -> Tuple[str, bool, str]:
    """
    Classify an incident into a priority level based on category and description keywords.
    Strict precedence: R0 -> R1 -> R2 -> R3 -> R4. Case-insensitive.

    Returns:
        (priority, needs_review, matched_rule_id)
    """
    cat_clean = (category or "").strip()
    desc_clean = (description or "").strip().lower()

    # R0 Override: Safety Stop category OR safety / collision / injury keywords
    r0_keywords = ["injury", "collision", "safety", "e-stop", "hazard", "near-miss"]
    if cat_clean == "Safety Stop" or any(kw in desc_clean for kw in r0_keywords):
        return ("P1", False, "R0")

    # R1: Software Crash with critical hang / deadlock / frozen keywords
    r1_keywords = ["hang", "deadlock", "frozen", "blackout", "segmentation fault"]
    if cat_clean == "Software Crash" and any(kw in desc_clean for kw in r1_keywords):
        return ("P1", False, "R1")

    # R2: Hardware / Teleop degradation categories with degradation keywords
    r2_categories = ["Gripper / End-Effector", "Latency / Connectivity", "Navigation"]
    r2_keywords = ["slip", "drop", "spike", "packet loss", "drift", "jitter", "stuck", "timeout", "high ping"]
    if cat_clean in r2_categories and any(kw in desc_clean for kw in r2_keywords):
        return ("P2", False, "R2")

    # R3: Feature request category OR enhancement keywords
    r3_keywords = ["request", "suggestion", "shortcut", "enhancement"]
    if cat_clean == "Feature Request / Enhancement" or any(kw in desc_clean for kw in r3_keywords):
        return ("P4", False, "R3")

    # R4 Fallback: Everything else -> P3.
    # If no keyword matched across any category/rule, needs_review = True
    r4_keywords = ["glitch", "flicker", "sluggish", "drift", "artifact", "soiled", "missing", "telemetry", "audio", "wear", "saturation"]
    all_keywords = r0_keywords + r1_keywords + r2_keywords + r3_keywords + r4_keywords
    matched_any_kw = any(kw in desc_clean for kw in all_keywords)

    if matched_any_kw:
        return ("P3", False, "R4")
    return ("P3", True, "R4")


def get_priority_sla(priority: str) -> Tuple[int, int]:
    """
    Return (response_sla_minutes, resolution_sla_hours) for a given priority.
    """
    pri_info = _RULES_CONFIG.get("priorities", {}).get(priority)
    if not pri_info:
        raise ValueError(f"Unknown priority: {priority}")
    return pri_info["response_sla_minutes"], pri_info["resolution_sla_hours"]
