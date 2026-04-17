"""
scenarios.py
------------
Builds the Original and Improved WorkstationNetwork objects
from config/settings.json, exactly matching the Kovács (2020) case study.
"""

import json
import os
from src.models.workstation import Workstation, WorkstationNetwork


def _load_config() -> dict:
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cfg_path = os.path.join(base, "config", "settings.json")
    with open(cfg_path) as f:
        return json.load(f)


def build_original_scenario() -> WorkstationNetwork:
    """Return the Original 14-workstation layout from the paper."""
    cfg = _load_config()
    orig = cfg["original"]

    workstations = [
        Workstation(
            id=ws["id"],
            name=ws["name"],
            cycle_time=ws["cycle_time"],
            x=ws["x"],
            y=ws["y"],
            fixed=ws["fixed"],
            active=True,
        )
        for ws in orig["workstations"]
    ]

    return WorkstationNetwork(
        name="Original",
        workstations=workstations,
        flow_matrix=orig["material_flow_ul"],
        distance_matrix=orig["distance_matrix_m"],
        takt_time=cfg["shift"]["takt_time_min"],
        layout_type=orig["layout_type"],
    )


def build_improved_scenario() -> WorkstationNetwork:
    """Return the Improved 12-workstation U-shaped cellular layout."""
    cfg = _load_config()
    impr = cfg["improved"]

    workstations = [
        Workstation(
            id=ws["id"],
            name=ws["name"],
            cycle_time=ws["cycle_time"],
            x=ws["x"],
            y=ws["y"],
            fixed=ws["fixed"],
            active=True,
        )
        for ws in impr["workstations"]
    ]

    return WorkstationNetwork(
        name="Improved",
        workstations=workstations,
        flow_matrix=impr["material_flow_ul"],
        distance_matrix=impr["distance_matrix_m"],
        takt_time=cfg["shift"]["takt_time_min"],
        layout_type=impr["layout_type"],
    )


def get_kpi_targets() -> dict:
    """Return ground-truth KPI comparison dict from the paper."""
    return _load_config()["kpi_comparison"]


def get_shift_info() -> dict:
    return _load_config()["shift"]


def get_lean_tools() -> list:
    return _load_config()["lean_tools_applied"]
