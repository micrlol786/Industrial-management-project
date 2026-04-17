
from typing import Dict, List, Any


# ──────────────────────────────────────────────────────────────────────────────
#  Seven wastes (Muda) categorisation
# ──────────────────────────────────────────────────────────────────────────────

WASTE_TYPES = {
    "overproduction":   "Producing more than needed — leads to excess WIP",
    "waiting":          "Operators/machines idle due to upstream delays",
    "unnecessary_motion": "Excess movement of operators on the floor",
    "transportation":   "Unnecessary movement of materials/goods",
    "inventory":        "WIP stock between stations beyond 1-piece-flow ideal",
    "overprocessing":   "More steps than required by the customer",
    "defects":          "Rework, scrap — non-conforming parts",
}


def identify_wastes_original() -> List[Dict[str, Any]]:
    """
    Wastes identified in the Current State of the paper's case study.
    """
    return [
        {
            "type": "waiting",
            "location": "WS9 (bottleneck)",
            "description": "Cycle time 6.1 min > takt time 5.62 min; units pile up",
            "severity": "HIGH",
        },
        {
            "type": "inventory",
            "location": "Between WS7→WS8→WS9→WS10",
            "description": "Linear layout causes large WIP buffer at bottleneck",
            "severity": "HIGH",
        },
        {
            "type": "transportation",
            "location": "WS6→WS12 (long distance 5m, 11 UL/shift)",
            "description": "Material crosses the shop floor diagonally",
            "severity": "MEDIUM",
        },
        {
            "type": "unnecessary_motion",
            "location": "Operators walking between WS7–WS14 linear line",
            "description": "Linear layout forces long operator walking routes",
            "severity": "MEDIUM",
        },
        {
            "type": "overproduction",
            "location": "WS3,4,7,8,10 (underloaded stations)",
            "description": "Short cycle times cause local over-production and idle",
            "severity": "LOW",
        },
        {
            "type": "overprocessing",
            "location": "WS4, WS7",
            "description": "Tasks can be merged into adjacent stations",
            "severity": "MEDIUM",
        },
    ]


# ──────────────────────────────────────────────────────────────────────────────
#  VSM process metrics
# ──────────────────────────────────────────────────────────────────────────────

def compute_vsm_metrics(
    cycle_times: Dict[int, float],
    takt_time: float,
    shift_duration: float = 450.0,
    avg_wip_between_stations: float = 2.0,
) -> Dict[str, Any]:
    """
    Compute standard VSM metrics for a given layout state.

    Parameters
    ----------
    cycle_times                 : {station_id: cycle_time_min}
    takt_time                   : target cycle time per unit [min]
    shift_duration              : working time per shift [min]
    avg_wip_between_stations    : average WIP queue size between each station
    """
    active_cts = {k: v for k, v in cycle_times.items() if v > 0}
    total_processing_time = sum(active_cts.values())
    n_stations = len(active_cts)
    max_ct = max(active_cts.values())
    bottleneck_id = max(active_cts, key=active_cts.get)

    throughput = int(shift_duration / max_ct)   # limited by bottleneck
    process_lead_time = total_processing_time   # pure processing (no wait)

    # WIP introduces waiting — simplified: each unit waits avg_wip × cycle_time
    # at each station on average
    queue_wait_per_unit = avg_wip_between_stations * max_ct
    total_lead_time = process_lead_time + queue_wait_per_unit * n_stations

    value_added_time = total_processing_time
    non_value_added_time = total_lead_time - value_added_time
    pceff = round(value_added_time / total_lead_time * 100, 2)   # process cycle efficiency

    return {
        "n_active_stations": n_stations,
        "takt_time_min": takt_time,
        "bottleneck_station": bottleneck_id,
        "bottleneck_cycle_time": max_ct,
        "total_value_added_time_min": round(total_processing_time, 2),
        "total_lead_time_min": round(total_lead_time, 2),
        "non_value_added_time_min": round(non_value_added_time, 2),
        "process_cycle_efficiency_pct": pceff,
        "throughput_units_per_shift": throughput,
    }


# ──────────────────────────────────────────────────────────────────────────────
#  Current State vs Future State comparison
# ──────────────────────────────────────────────────────────────────────────────

ORIGINAL_CYCLE_TIMES = {
    1: 4.6, 2: 3.9, 3: 3.4, 4: 3.5,
    5: 5.1, 6: 4.7, 7: 3.2, 8: 3.4,
    9: 6.1, 10: 3.4, 11: 5.2, 12: 4.1,
    13: 5.1, 14: 5.0,
}

IMPROVED_CYCLE_TIMES = {
    1: 4.6, 2: 5.4, 3: 5.4,
    5: 5.1, 6: 4.7, 8: 5.4,
    9: 5.4, 10: 5.3, 11: 5.2, 12: 4.1,
    13: 5.1, 14: 5.0,
}


def csm_to_fsm_comparison(takt_time: float = 5.625) -> Dict[str, Any]:
    """
    Produce a structured Current State Map → Future State Map comparison,
    matching the paper's analysis exactly.
    """
    csm = compute_vsm_metrics(ORIGINAL_CYCLE_TIMES, takt_time)
    fsm = compute_vsm_metrics(IMPROVED_CYCLE_TIMES, takt_time)
    wastes = identify_wastes_original()

    return {
        "current_state": csm,
        "future_state": fsm,
        "wastes_identified": wastes,
        "improvement_actions": [
            "Line Balancing: eliminate WS4 and WS7",
            "Cellular Design: U-shaped cell for WS6–WS12",
            "Kanban + Supermarket: controlled material supply",
            "One-piece flow: remove WIP buffers",
            "5S + Visual Management: workplace organisation",
            "Pull system: demand-driven production",
            "JIT: synchronise supply with takt time",
            "Standardisation: document best-known methods",
        ],
        "kpi_deltas": {
            "lead_time_reduction_pct": round(
                (csm["total_lead_time_min"] - fsm["total_lead_time_min"])
                / csm["total_lead_time_min"] * 100, 2
            ),
            "pce_improvement_pp": round(
                fsm["process_cycle_efficiency_pct"] - csm["process_cycle_efficiency_pct"], 2
            ),
            "throughput_gain": fsm["throughput_units_per_shift"] - csm["throughput_units_per_shift"],
        },
    }


def print_vsm_report() -> None:
    result = csm_to_fsm_comparison()

    print("\n" + "=" * 65)
    print("  VALUE STREAM MAPPING REPORT")
    print("=" * 65)

    print("\n  ── WASTES IDENTIFIED (Current State) ──")
    for w in result["wastes_identified"]:
        print(f"  [{w['severity']:6s}] {w['type'].upper():22s} @ {w['location']}")
        print(f"           {w['description']}")

    for label, state in [("CURRENT STATE", result["current_state"]),
                          ("FUTURE STATE",  result["future_state"])]:
        print(f"\n  ── {label} ──")
        print(f"  Active stations         : {state['n_active_stations']}")
        print(f"  Bottleneck              : WS{state['bottleneck_station']} ({state['bottleneck_cycle_time']} min)")
        print(f"  Throughput              : {state['throughput_units_per_shift']} units/shift")
        print(f"  Value-added time        : {state['total_value_added_time_min']} min")
        print(f"  Total lead time         : {state['total_lead_time_min']} min")
        print(f"  Process Cycle Eff.      : {state['process_cycle_efficiency_pct']}%")

    d = result["kpi_deltas"]
    print(f"\n  ── CSM → FSM IMPROVEMENTS ──")
    print(f"  Lead time reduction     : {d['lead_time_reduction_pct']}%")
    print(f"  PCE gain                : +{d['pce_improvement_pp']} pp")
    print(f"  Throughput gain         : +{d['throughput_gain']} units/shift")
    print(f"\n  Improvement actions applied:")
    for action in result["improvement_actions"]:
        print(f"    ✓ {action}")
    print()
