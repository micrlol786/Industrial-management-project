"""
material_workflow.py
--------------------
Facility Layout Design (FLD) objective function and analysis.

Implements:
  • Equation 1  — Material Workflow (E_MWF = Σ q_ij * l_ij)
  • Equation 4  — Material Handling Cost
  • Equation 5  — Labour Cost
  • Full KPI comparison table (Table 3 from the paper)

Kovács (2020), Section 2.3 and 4.3.
"""

import numpy as np
from typing import List, Dict, Any, Optional


# ──────────────────────────────────────────────────────────────────────────────
#  Core FLD objective function  (Equation 1)
#  E_MWF = Σ_i Σ_j q_ij * l_ij
# ──────────────────────────────────────────────────────────────────────────────

def material_workflow(
    flow_matrix: List[List[float]],
    distance_matrix: List[List[float]],
) -> float:
    """
    Calculate total material workflow [UL·m].

    Parameters
    ----------
    flow_matrix     : n×n matrix — q_ij = flow from station i to j [UL/shift]
    distance_matrix : n×n matrix — l_ij = distance from i to j [m]

    Returns
    -------
    E_MWF in UL·m
    """
    Q = np.array(flow_matrix, dtype=float)
    L = np.array(distance_matrix, dtype=float)
    return round(float(np.sum(Q * L)), 2)


def total_travel_distance(
    flow_matrix: List[List[float]],
    distance_matrix: List[List[float]],
) -> float:
    """
    Sum of distances where material actually flows (q_ij > 0) [m].
    """
    Q = np.array(flow_matrix, dtype=float)
    L = np.array(distance_matrix, dtype=float)
    mask = Q > 0
    return round(float(np.sum(L[mask])), 2)


# ──────────────────────────────────────────────────────────────────────────────
#  Material Handling Cost  (Equation 4)
#  C_MH = E_MWF * c_mh
# ──────────────────────────────────────────────────────────────────────────────

def material_handling_cost(
    emwf: float,
    specific_cost_euro_per_ul_m: float,
) -> float:
    """
    C_MH = E_MWF * c_mh

    Parameters
    ----------
    emwf                         : material workflow [UL·m]
    specific_cost_euro_per_ul_m  : c_mh [€/(UL·m)]

    Returns
    -------
    cost in €
    """
    return round(emwf * specific_cost_euro_per_ul_m, 4)


# ──────────────────────────────────────────────────────────────────────────────
#  Labour Cost  (Equation 5)
#  C_L = N_Op * c_L
# ──────────────────────────────────────────────────────────────────────────────

def labour_cost(
    num_operators: int,
    specific_labour_cost_euro_per_person: float,
) -> float:
    """
    C_L = N_Op * c_L

    Parameters
    ----------
    num_operators                          : N_Op
    specific_labour_cost_euro_per_person   : c_L [€/person]

    Returns
    -------
    cost in €
    """
    return round(num_operators * specific_labour_cost_euro_per_person, 2)


# ──────────────────────────────────────────────────────────────────────────────
#  Pairwise material flow analysis
# ──────────────────────────────────────────────────────────────────────────────

def flow_analysis(
    flow_matrix: List[List[float]],
    distance_matrix: List[List[float]],
    station_names: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Return sorted list of station pairs by their contribution to E_MWF.
    Useful for identifying the highest-impact flows to target.
    """
    Q = np.array(flow_matrix, dtype=float)
    L = np.array(distance_matrix, dtype=float)
    n = Q.shape[0]

    if station_names is None:
        station_names = [f"WS{i+1}" for i in range(n)]

    results = []
    for i in range(n):
        for j in range(n):
            if Q[i, j] > 0:
                results.append({
                    "from": station_names[i],
                    "to": station_names[j],
                    "flow_ul": Q[i, j],
                    "distance_m": L[i, j],
                    "contribution_ul_m": round(Q[i, j] * L[i, j], 2),
                })

    return sorted(results, key=lambda x: x["contribution_ul_m"], reverse=True)


# ──────────────────────────────────────────────────────────────────────────────
#  Full KPI comparison (Table 3 from the paper)
# ──────────────────────────────────────────────────────────────────────────────

PAPER_RESULTS = {
    "longest_cycle_time":     {"original": 6.1,   "improved": 5.4,    "unit": "min",    "change_pct": -11.47},
    "productivity":           {"original": 73,     "improved": 83,     "unit": "u/shift","change_pct": +13.70},
    "num_workstations":       {"original": 14,     "improved": 12,     "unit": "pcs",    "change_pct": -14.28},
    "num_operators":          {"original": 14,     "improved": 12,     "unit": "person", "change_pct": -14.28},
    "wip_inventory":          {"original": 100,    "improved": 64,     "unit": "%",      "change_pct": -36.00},
    "floor_space":            {"original": 250,    "improved": 193.75, "unit": "m²",     "change_pct": -22.50},
    "material_workflow":      {"original": 365,    "improved": 348,    "unit": "UL·m",   "change_pct": -4.66},
    "travel_distance":        {"original": 63,     "improved": 55,     "unit": "m",      "change_pct": -12.70},
    "material_handling_cost": {"original": 100,    "improved": 95.34,  "unit": "%",      "change_pct": -4.66},
    "labour_cost":            {"original": 100,    "improved": 85.72,  "unit": "%",      "change_pct": -14.28},
}


def compute_fld_comparison(
    orig_flow: List[List[float]],
    orig_dist: List[List[float]],
    new_flow: List[List[float]],
    new_dist: List[List[float]],
) -> Dict[str, Any]:
    """
    Compute E_MWF and travel distance for both layouts and report comparison.
    """
    orig_emwf = material_workflow(orig_flow, orig_dist)
    new_emwf  = material_workflow(new_flow,  new_dist)
    orig_dist_total = total_travel_distance(orig_flow, orig_dist)
    new_dist_total  = total_travel_distance(new_flow,  new_dist)

    return {
        "original": {
            "material_workflow_ul_m": orig_emwf,
            "travel_distance_m": orig_dist_total,
        },
        "improved": {
            "material_workflow_ul_m": new_emwf,
            "travel_distance_m": new_dist_total,
        },
        "reduction": {
            "material_workflow_ul_m": round(orig_emwf - new_emwf, 2),
            "material_workflow_pct": round((orig_emwf - new_emwf) / orig_emwf * 100, 2),
            "travel_distance_m": round(orig_dist_total - new_dist_total, 2),
            "travel_distance_pct": round((orig_dist_total - new_dist_total) / orig_dist_total * 100, 2),
        },
    }


def print_kpi_table() -> None:
    """Print Table 3 from the paper."""
    print("\n" + "=" * 75)
    print("  KPI COMPARISON TABLE  (Kovács 2020 — Table 3 reproduction)")
    print("=" * 75)
    print(f"  {'Indicator':<30} {'Original':>10} {'Improved':>10} {'Change':>10}  Unit")
    print("  " + "-" * 71)

    for key, vals in PAPER_RESULTS.items():
        name = key.replace("_", " ").title()
        sign = "+" if vals["change_pct"] > 0 else ""
        print(
            f"  {name:<30} {vals['original']:>10.2f} {vals['improved']:>10.2f} "
            f"{sign}{vals['change_pct']:>8.2f}%  {vals['unit']}"
        )

    print()
    print("  Qualitative indicators (all improved):")
    qualitative = [
        "Reliability of continuous component supply",
        "Quality of processes and final products",
        "Transparency of processes",
        "Standardisation of processes",
        "Workplace ergonomics and worker satisfaction",
    ]
    for q in qualitative:
        print(f"    ✓ {q}")
    print()
