"""
manufacturing_plant.py
Discrete-event simulation of the automotive assembly plant described in:
  Kovács (2020) IJPR 58(10), 2916-2936.

Two scenarios are supported:
  • "original"  – 14 workstations, linear layout
  • "improved"  – 12 workstations, U-shaped cellular layout
"""

from __future__ import annotations
import simpy
import random
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

from src.simulation.workstation import Workstation


# ══════════════════════════════════════════════════════════════
# Result container
# ══════════════════════════════════════════════════════════════
@dataclass
class SimulationResults:
    scenario: str
    sim_duration: float
    units_completed: int
    productivity: float                  # units / shift
    avg_cycle_time: float                # min (longest WS drives throughput)
    bottleneck_ws: int
    bottleneck_ct: float
    wip_avg: float
    material_workflow: float             # UL·m
    travel_distance: float              # m
    material_handling_cost: float
    labour_cost: float
    num_workstations: int
    num_operators: int
    throughput_per_min: float
    ws_utilisation: Dict[int, float] = field(default_factory=dict)
    timeline: List[Tuple[float, int]] = field(default_factory=list)  # (time, cumulative units)

    def summary(self) -> str:
        lines = [
            f"\n{'='*55}",
            f"  Scenario : {self.scenario.upper()}",
            f"{'='*55}",
            f"  Workstations / Operators : {self.num_workstations} / {self.num_operators}",
            f"  Units completed          : {self.units_completed}",
            f"  Productivity             : {self.productivity:.1f} units/shift",
            f"  Bottleneck WS {self.bottleneck_ws}          : {self.bottleneck_ct:.2f} min",
            f"  Avg WIP                  : {self.wip_avg:.1f} units",
            f"  Material Workflow        : {self.material_workflow:.1f} UL·m",
            f"  Travel Distance          : {self.travel_distance:.1f} m",
            f"  Material Handling Cost   : {self.material_handling_cost:.2f} €",
            f"  Labour Cost              : {self.labour_cost:.2f} €",
            f"{'='*55}",
        ]
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
# Plant simulation
# ══════════════════════════════════════════════════════════════
class ManufacturingPlant:
    """
    Simulates production flow through a sequence of workstations.

    Parameters
    ----------
    scenario      : "original" | "improved"
    sim_duration  : simulation time in minutes (default = one shift)
    random_seed   : reproducibility
    cmh           : specific material handling cost  (€ / UL·m)
    cl            : specific labour cost             (€ / person / shift)
    """

    SHIFT = 450  # minutes

    def __init__(
        self,
        scenario: str = "original",
        sim_duration: float = 450,
        random_seed: int = 42,
        cmh: float = 0.05,
        cl: float = 150,
    ):
        from config.plant_config import (
            ORIGINAL_CYCLE_TIMES, ORIGINAL_POSITIONS, ORIGINAL_MATERIAL_FLOW,
            IMPROVED_CYCLE_TIMES, IMPROVED_POSITIONS, IMPROVED_MATERIAL_FLOW,
            TAKT_TIME,
        )

        if scenario not in ("original", "improved"):
            raise ValueError("scenario must be 'original' or 'improved'")

        self.scenario = scenario
        self.sim_duration = sim_duration
        self.cmh = cmh
        self.cl = cl
        self.takt_time = TAKT_TIME
        random.seed(random_seed)

        if scenario == "original":
            self.cycle_times = ORIGINAL_CYCLE_TIMES
            self.positions    = ORIGINAL_POSITIONS
            self.mat_flow     = ORIGINAL_MATERIAL_FLOW
        else:
            self.cycle_times = IMPROVED_CYCLE_TIMES
            self.positions    = IMPROVED_POSITIONS
            self.mat_flow     = IMPROVED_MATERIAL_FLOW

        # Active workstation IDs (cycle_time > 0)
        self.active_ws = [k for k, v in self.cycle_times.items() if v > 0]
        self.active_ws.sort()

        self.env = simpy.Environment()
        self.workstations: Dict[int, Workstation] = {}
        self._wip_level = 0
        self._wip_history: List[Tuple[float, int]] = []
        self._completed_timeline: List[Tuple[float, int]] = []
        self._total_completed = 0

    # ------------------------------------------------------------------ #
    def _build_workstations(self):
        for ws_id in self.active_ws:
            self.workstations[ws_id] = Workstation(
                env=self.env,
                ws_id=ws_id,
                cycle_time=self.cycle_times[ws_id],
                position=self.positions[ws_id],
            )

    # ------------------------------------------------------------------ #
    def _unit_process(self, unit_id: int):
        """Generator: one unit travels through all workstations in sequence."""
        arrival = self.env.now
        self._wip_level += 1
        self._wip_history.append((self.env.now, self._wip_level))

        for ws_id in self.active_ws:
            ws = self.workstations[ws_id]
            yield from ws.process(unit_id, arrival)

        self._wip_level -= 1
        self._wip_history.append((self.env.now, self._wip_level))
        self._total_completed += 1
        self._completed_timeline.append((self.env.now, self._total_completed))

    # ------------------------------------------------------------------ #
    def _arrival_generator(self):
        """Generate new units at takt-time intervals."""
        unit_id = 0
        while True:
            self.env.process(self._unit_process(unit_id))
            unit_id += 1
            yield self.env.timeout(self.takt_time)

    # ------------------------------------------------------------------ #
    def run(self) -> SimulationResults:
        self._build_workstations()
        self.env.process(self._arrival_generator())
        self.env.run(until=self.sim_duration)

        return self._collect_results()

    # ------------------------------------------------------------------ #
    def _collect_results(self) -> SimulationResults:
        # Bottleneck = WS with longest cycle time
        bottleneck_id = max(self.active_ws, key=lambda w: self.cycle_times[w])
        bottleneck_ct = self.cycle_times[bottleneck_id]

        # Productivity (units per shift)
        productivity = self._total_completed * (self.SHIFT / self.sim_duration)

        # Average WIP
        wip_avg = self._average_wip()

        # Material workflow  EMWF = Σ q_ij * l_ij
        emwf = self._calc_material_workflow()

        # Total travel distance = Σ l_ij  where flow > 0
        travel_dist = self._calc_travel_distance()

        # Costs
        mh_cost = emwf * self.cmh
        n_ops   = len(self.active_ws)
        lab_cost = n_ops * self.cl

        ws_util = {ws_id: ws.utilisation
                   for ws_id, ws in self.workstations.items()}

        return SimulationResults(
            scenario=self.scenario,
            sim_duration=self.sim_duration,
            units_completed=self._total_completed,
            productivity=productivity,
            avg_cycle_time=sum(self.cycle_times[w] for w in self.active_ws) / len(self.active_ws),
            bottleneck_ws=bottleneck_id,
            bottleneck_ct=bottleneck_ct,
            wip_avg=wip_avg,
            material_workflow=emwf,
            travel_distance=travel_dist,
            material_handling_cost=mh_cost,
            labour_cost=lab_cost,
            num_workstations=len(self.active_ws),
            num_operators=len(self.active_ws),
            throughput_per_min=self._total_completed / self.sim_duration,
            ws_utilisation=ws_util,
            timeline=self._completed_timeline,
        )

    # ------------------------------------------------------------------ #
    def _average_wip(self) -> float:
        if len(self._wip_history) < 2:
            return 0.0
        total = 0.0
        for i in range(len(self._wip_history) - 1):
            t0, w0 = self._wip_history[i]
            t1, _  = self._wip_history[i + 1]
            total += w0 * (t1 - t0)
        return total / self.sim_duration

    def _calc_material_workflow(self) -> float:
        emwf = 0.0
        for (i, j), q in self.mat_flow.items():
            # Use active workstation IDs; map original → active if needed
            pi = self.positions.get(i)
            pj = self.positions.get(j)
            if pi and pj:
                dist = math.sqrt((pi[0]-pj[0])**2 + (pi[1]-pj[1])**2)
                emwf += q * dist
        return round(emwf, 2)

    def _calc_travel_distance(self) -> float:
        total = 0.0
        for (i, j) in self.mat_flow:
            pi = self.positions.get(i)
            pj = self.positions.get(j)
            if pi and pj:
                total += math.sqrt((pi[0]-pj[0])**2 + (pi[1]-pj[1])**2)
        return round(total, 2)
