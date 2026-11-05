"""
Make.com Set Variable Priority Expression Generator.
Generates the copy-pasteable Make expression for automated triage directly from config/rules.yaml.
ALL DATA IS SYNTHETIC. NO REAL CUSTOMER OR ROBOT DATA.
"""

from pathlib import Path
import sys

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rules import load_rules


def generate_make_expression() -> str:
    """
    Generate a nested Make.com 'if(...)' formula string for the Priority variable.
    Make syntax: if(condition; value_if_true; value_if_false)
    Functions used: lower(), contains(), =
    Field references: 1.Description, 1.Category
    """
    rules_cfg = load_rules()
    rules = rules_cfg.get("rules", [])

    # We build the nested expression from innermost (fallback) outward
    # R4 Fallback: "P3"
    expr = '"P3"'

    # R3: Feature Request
    r3 = next(r for r in rules if r["id"] == "R3")
    r3_kw_checks = [f'contains(lower(1.Description); "{kw}")' for kw in r3["keywords"]]
    r3_cat_check = 'lower(1.Category) = "feature request / enhancement"'
    r3_cond = f"({r3_cat_check} | {' | '.join(r3_kw_checks)})"
    expr = f"if({r3_cond}; \"P4\"; {expr})"

    # R2: P2 Major Degradation
    r2 = next(r for r in rules if r["id"] == "R2")
    r2_cats = ["gripper / end-effector", "latency / connectivity", "navigation"]
    r2_cat_checks = [f'lower(1.Category) = "{c}"' for c in r2_cats]
    r2_kw_checks = [f'contains(lower(1.Description); "{kw}")' for kw in r2["keywords"]]
    r2_cond = f"(({' | '.join(r2_cat_checks)}) & ({' | '.join(r2_kw_checks)}))"
    expr = f"if({r2_cond}; \"P2\"; {expr})"

    # R1: Software Crash with critical keywords
    r1 = next(r for r in rules if r["id"] == "R1")
    r1_kw_checks = [f'contains(lower(1.Description); "{kw}")' for kw in r1["keywords"]]
    r1_cond = f'(lower(1.Category) = "software crash" & ({" | ".join(r1_kw_checks)}))'
    expr = f"if({r1_cond}; \"P1\"; {expr})"

    # R0: Safety Stop override
    r0 = next(r for r in rules if r["id"] == "R0")
    r0_kw_checks = [f'contains(lower(1.Description); "{kw}")' for kw in r0["keywords"]]
    r0_cond = f'(lower(1.Category) = "safety stop" | {" | ".join(r0_kw_checks)})'
    expr = f"if({r0_cond}; \"P1\"; {expr})"

    return expr


def main():
    expr = generate_make_expression()
    print("=" * 70)
    print("GENERATED MAKE.COM SET VARIABLE EXPRESSION FOR 'Priority'")
    print("=" * 70)
    print(expr)
    print("=" * 70)
    print("\nPaste this expression into Make Scenario 1 > Set Variable module > 'priority' field.")


if __name__ == "__main__":
    main()

