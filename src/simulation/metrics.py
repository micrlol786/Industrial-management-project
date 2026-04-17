"""
metrics.py – Lean KPI calculations as described in the paper.
All formulae reference equation numbers from Kovács (2020).
"""

from __future__ import annotations
import math
from typing import Dict, Tuple


# ──────────────────────────────────────────────────────────────
# Eq. (2) – Takt-time
# ──────────────────────────────────────────────────────────────
def takt_time(available_time: float, demand: float) -> float:
    """
    T_takt = T_A / Q   [min/unit]

    Parameters
    ----------
    available_time : total available working time per shift (min)
    demand         : customer demand per shift (units)
    """
    if demand <= 0:
        raise ValueError("Customer demand must be > 0")
    return available_time / demand


# ──────────────────────────────────────────────────────────────
# Eq. (3) – Ideal number of operators / workstations
# ──────────────────────────────────────────────────────────────
def ideal_num_operators(total_cycle_time: float, t_takt: float) -> float:
    """
    N_Op,Ws = T_T / T_takt

    Parameters
    ----------
    total_cycle_time : sum of all individual cycle times (min)
    t_takt           : takt-time (min/unit)
    """
    return total_cycle_time / t_takt


# ──────────────────────────────────────────────────────────────
# Eq. (1) – Material Workflow
# ──────────────────────────────────────────────────────────────
def material_workflow(
    flow_matrix: Dict[Tuple[int, int], float],
    positions: Dict[int, Tuple[float, float]],
) -> float:
    """
    E_MWF = Σ_i Σ_j  q_ij * l_ij   [UL·m]

    Parameters
    ----------
    flow_matrix : {(i, j): q_ij}   unit loads per shift
    positions   : {ws_id: (x, y)}  metres
    """
    emwf = 0.0
    for (i, j), q in flow_matrix.items():
        if i in positions and j in positions:
            xi, yi = positions[i]
            xj, yj = positions[j]
            l_ij = math.sqrt((xi - xj) ** 2 + (yi - yj) ** 2)
            emwf += q * l_ij
    return emwf


# ──────────────────────────────────────────────────────────────
# Eq. (4) – Material Handling Cost
# ──────────────────────────────────────────────────────────────
def material_handling_cost(emwf: float, cmh: float) -> float:
    """
    C_MH = E_MWF * c_mh   [€]

    Parameters
    ----------
    emwf : material workflow (UL·m)
    cmh  : specific material handling cost (€ / UL·m)
    """
    return emwf * cmh


# ──────────────────────────────────────────────────────────────
# Eq. (5) – Labour Cost
# ──────────────────────────────────────────────────────────────
def labour_cost(n_operators: int, c_labour: float) -> float:
    """
    C_L = N_Op * c_L   [€]

    Parameters
    ----------
    n_operators : number of operators
    c_labour    : specific labour cost per operator per shift (€)
    """
    return n_operators * c_labour


# ──────────────────────────────────────────────────────────────
# Productivity
# ──────────────────────────────────────────────────────────────
def productivity(available_time: float, bottleneck_cycle_time: float) -> float:
    """
    Productivity = T_A / CT_bottleneck   [units / shift]
    """
    return available_time / bottleneck_cycle_time


# ──────────────────────────────────────────────────────────────
# Travel distance
# ──────────────────────────────────────────────────────────────
def total_travel_distance(
    flow_matrix: Dict[Tuple[int, int], float],
    positions: Dict[int, Tuple[float, float]],
) -> float:
    """Sum of distances for all active material flow paths (m)."""
    total = 0.0
    for (i, j) in flow_matrix:
        if i in positions and j in positions:
            xi, yi = positions[i]
            xj, yj = positions[j]
            total += math.sqrt((xi - xj) ** 2 + (yi - yj) ** 2)
    return total


# ──────────────────────────────────────────────────────────────
# Bottleneck detection
# ──────────────────────────────────────────────────────────────
def find_bottleneck(cycle_times: Dict[int, float]) -> Tuple[int, float]:
    """Return (workstation_id, cycle_time) of the bottleneck."""
    bot_id = max(cycle_times, key=cycle_times.get)
    return bot_id, cycle_times[bot_id]


# ──────────────────────────────────────────────────────────────
# Line Balance Efficiency
# ──────────────────────────────────────────────────────────────
def line_balance_efficiency(
    cycle_times: Dict[int, float], t_takt: float
) -> float:
    """
    LBE = (Σ CT_i) / (N * T_takt)   where N = number of active stations
    """
    active = {k: v for k, v in cycle_times.items() if v > 0}
    n = len(active)
    if n == 0 or t_takt <= 0:
        return 0.0
    return sum(active.values()) / (n * t_takt)


# ──────────────────────────────────────────────────────────────
# Compare two scenarios
# ──────────────────────────────────────────────────────────────
def compare_scenarios(original: dict, improved: dict) -> dict:
    """
    Returns a dict of KPI name → {'original', 'improved', 'change_pct'}
    """
    results = {}
    for key in original:
        if key in improved:
            orig_val = original[key]
            impr_val = improved[key]
            if orig_val != 0:
                pct = (impr_val - orig_val) / orig_val * 100
            else:
                pct = 0.0
            results[key] = {
                "original": orig_val,
                "improved": impr_val,
                "change_pct": round(pct, 2),
            }
    return results
