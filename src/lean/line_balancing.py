

from typing import List, Dict, Any


# ──────────────────────────────────────────────────────────────────────────────
#  Takt-Time calculation  (Equation 2 from the paper)
#  T_takt = T_A / Q   [min/unit]
# ──────────────────────────────────────────────────────────────────────────────

def calculate_takt_time(
    available_time_min: float,
    customer_demand: int,
) -> float:
    """
    T_takt = T_A / Q

    Parameters
    ----------
    available_time_min : total available working time per shift [min]
    customer_demand    : units demanded per shift

    Returns
    -------
    takt_time in min/unit
    """
    if customer_demand <= 0:
        raise ValueError("Customer demand must be > 0")
    return round(available_time_min / customer_demand, 4)


# ──────────────────────────────────────────────────────────────────────────────
#  Ideal number of operators/workstations  (Equation 3 from the paper)
#  N_Op,Ws = T_T / T_takt
# ──────────────────────────────────────────────────────────────────────────────

def ideal_num_stations(
    cycle_times: List[float],
    takt_time: float,
) -> float:
    """
    N_Op,Ws = T_T / T_takt
    where T_T = sum of all cycle times (total time to produce one unit).
    Returns the theoretical ideal (may be non-integer).
    """
    total_time = sum(cycle_times)
    return round(total_time / takt_time, 2)


# ──────────────────────────────────────────────────────────────────────────────
#  Bottleneck detection
# ──────────────────────────────────────────────────────────────────────────────

def find_bottlenecks(
    cycle_times: Dict[int, float],
    takt_time: float,
) -> List[int]:
    """
    Return list of workstation IDs where cycle_time > takt_time.
    """
    return [ws_id for ws_id, ct in cycle_times.items() if ct > takt_time]


def find_underloaded(
    cycle_times: Dict[int, float],
    takt_time: float,
    threshold: float = 0.80,
) -> List[int]:
    """
    Return workstation IDs where cycle_time < threshold * takt_time
    (unutilised resources).
    """
    return [
        ws_id for ws_id, ct in cycle_times.items()
        if ct < threshold * takt_time
    ]


# ──────────────────────────────────────────────────────────────────────────────
#  Full takt-time analysis report
# ──────────────────────────────────────────────────────────────────────────────

def takt_time_analysis(
    cycle_times: Dict[int, float],
    available_time_min: float = 450.0,
    customer_demand: int = 80,
) -> Dict[str, Any]:
    """
    Full takt-time analysis reproducing Section 4.2.2 of the paper.

    Returns a dict with all computed values.
    """
    takt = calculate_takt_time(available_time_min, customer_demand)
    total_ct = sum(cycle_times.values())
    ideal_n = ideal_num_stations(list(cycle_times.values()), takt)
    bottlenecks = find_bottlenecks(cycle_times, takt)
    underloaded = find_underloaded(cycle_times, takt)

    station_status = {}
    for ws_id, ct in cycle_times.items():
        if ct > takt:
            status = "BOTTLENECK"
        elif ct < 0.80 * takt:
            status = "UNDERLOADED"
        else:
            status = "OK"
        station_status[ws_id] = {
            "cycle_time": ct,
            "takt_time": takt,
            "ratio": round(ct / takt, 3),
            "status": status,
        }

    return {
        "takt_time_min": takt,
        "available_time_min": available_time_min,
        "customer_demand_per_shift": customer_demand,
        "total_cycle_time_min": round(total_ct, 2),
        "ideal_num_stations": ideal_n,
        "bottleneck_stations": bottlenecks,
        "underloaded_stations": underloaded,
        "station_analysis": station_status,
    }


# ──────────────────────────────────────────────────────────────────────────────
#  Line balancing (Section 4.2.3)
# ──────────────────────────────────────────────────────────────────────────────

# Paper-defined rebalanced cycle times (Table 2)
ORIGINAL_CYCLE_TIMES = {
    1: 4.6, 2: 3.9, 3: 3.4, 4: 3.5,
    5: 5.1, 6: 4.7, 7: 3.2, 8: 3.4,
    9: 6.1, 10: 3.4, 11: 5.2, 12: 4.1,
    13: 5.1, 14: 5.0,
}

BALANCED_CYCLE_TIMES = {
    1: 4.6, 2: 5.4, 3: 5.4, 4: 0.0,   # WS4 eliminated → task → WS2,WS3
    5: 5.1, 6: 4.7, 7: 0.0, 8: 5.4,   # WS7 eliminated → task → WS8
    9: 5.4, 10: 5.3, 11: 5.2, 12: 4.1,
    13: 5.1, 14: 5.0,
}

ELIMINATED_STATIONS = {4, 7}   # eliminated by line balancing


def apply_line_balancing(
    cycle_times: Dict[int, float],
    takt_time: float,
) -> Dict[str, Any]:
    """
    Apply line balancing as described in Section 4.2.3 of the paper.
    Uses the paper's predetermined rebalancing (WS4 and WS7 eliminated).

    Returns a report dict including before/after comparison.
    """
    original_ct = ORIGINAL_CYCLE_TIMES.copy()
    balanced_ct = {k: v for k, v in BALANCED_CYCLE_TIMES.items() if v > 0}

    original_max_ct = max(original_ct.values())
    balanced_max_ct = max(balanced_ct.values())

    original_productivity = int(450 / original_max_ct)
    balanced_productivity = int(450 / balanced_max_ct)

    original_idle = {
        ws: round(takt_time - ct, 3)
        for ws, ct in original_ct.items()
        if ct < takt_time
    }
    balanced_idle = {
        ws: round(takt_time - ct, 3)
        for ws, ct in balanced_ct.items()
        if ct < takt_time
    }

    efficiency_before = round(
        sum(original_ct.values()) / (len(original_ct) * takt_time) * 100, 2
    )
    efficiency_after = round(
        sum(balanced_ct.values()) / (len(balanced_ct) * takt_time) * 100, 2
    )

    return {
        "takt_time": takt_time,
        "eliminated_stations": list(ELIMINATED_STATIONS),
        "original": {
            "num_stations": len(original_ct),
            "cycle_times": original_ct,
            "max_cycle_time": original_max_ct,
            "bottleneck": max(original_ct, key=original_ct.get),
            "productivity_units_per_shift": original_productivity,
            "line_efficiency_pct": efficiency_before,
            "idle_times": original_idle,
        },
        "balanced": {
            "num_stations": len(balanced_ct),
            "cycle_times": balanced_ct,
            "max_cycle_time": balanced_max_ct,
            "bottleneck": max(balanced_ct, key=balanced_ct.get),
            "productivity_units_per_shift": balanced_productivity,
            "line_efficiency_pct": efficiency_after,
            "idle_times": balanced_idle,
        },
        "improvement": {
            "stations_eliminated": len(ELIMINATED_STATIONS),
            "productivity_gain_pct": round(
                (balanced_productivity - original_productivity) / original_productivity * 100, 2
            ),
            "max_ct_reduction_pct": round(
                (original_max_ct - balanced_max_ct) / original_max_ct * 100, 2
            ),
            "efficiency_gain_pct": round(efficiency_after - efficiency_before, 2),
        },
    }


def print_line_balance_report(result: Dict[str, Any]) -> None:
    """Pretty-print the line balance report."""
    print("\n" + "=" * 65)
    print("  LINE BALANCING REPORT  (Kovács 2020 — Table 2 reproduction)")
    print("=" * 65)
    print(f"  Takt time : {result['takt_time']} min/unit")
    print(f"  Eliminated workstations: {result['eliminated_stations']}")

    for label in ("original", "balanced"):
        d = result[label]
        print(f"\n  ── {label.upper()} ──")
        print(f"  Stations     : {d['num_stations']}")
        print(f"  Bottleneck   : WS{d['bottleneck']} ({d['max_cycle_time']} min)")
        print(f"  Productivity : {d['productivity_units_per_shift']} units/shift")
        print(f"  Efficiency   : {d['line_efficiency_pct']} %")
        print(f"  Cycle times  :")
        for ws, ct in d["cycle_times"].items():
            flag = " ← BOTTLENECK" if ws == d["bottleneck"] else ""
            print(f"    WS{ws:2d}: {ct:.1f} min{flag}")

    imp = result["improvement"]
    print(f"\n  ── IMPROVEMENT SUMMARY ──")
    print(f"  Stations eliminated      : {imp['stations_eliminated']}")
    print(f"  Productivity gain        : +{imp['productivity_gain_pct']}%")
    print(f"  Max cycle time reduction : {imp['max_ct_reduction_pct']}%")
    print(f"  Line efficiency gain     : +{imp['efficiency_gain_pct']} pp")
    print()
