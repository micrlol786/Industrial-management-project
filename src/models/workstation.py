
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Workstation:
    """
    Represents a single workstation on the shop floor.

    Attributes:
        id          : unique integer identifier (1-based, matching the paper)
        name        : display label e.g. "WS1"
        cycle_time  : processing time per unit [min]
        x, y        : position on the shop floor grid [m]
        fixed       : True if the WS is monument-type (cannot be moved)
        active      : False if eliminated by line balancing
        queue       : number of WIP units waiting in front of this station
        units_done  : total units completed during the simulation
        total_idle  : accumulated idle time [min]
        total_busy  : accumulated busy time [min]
    """
    id: int
    name: str
    cycle_time: float          # min / unit
    x: float
    y: float
    fixed: bool = False
    active: bool = True

    # runtime stats (mutable — not part of equality / hashing)
    queue: int = field(default=0, compare=False, repr=False)
    units_done: int = field(default=0, compare=False, repr=False)
    total_idle: float = field(default=0.0, compare=False, repr=False)
    total_busy: float = field(default=0.0, compare=False, repr=False)

    # ------------------------------------------------------------------ #
    #  Derived metrics                                                     #
    # ------------------------------------------------------------------ #

    @property
    def utilisation(self) -> float:
        """Fraction of time the station was busy (0–1)."""
        total = self.total_busy + self.total_idle
        return self.total_busy / total if total > 0 else 0.0

    @property
    def is_bottleneck(self, takt_time: float = 5.625) -> bool:
        """True when cycle time exceeds takt time."""
        return self.cycle_time > takt_time

    def reset_stats(self) -> None:
        """Clear runtime counters (call before each simulation run)."""
        self.queue = 0
        self.units_done = 0
        self.total_idle = 0.0
        self.total_busy = 0.0

    def __repr__(self) -> str:
        status = "FIXED" if self.fixed else ("ACTIVE" if self.active else "ELIMINATED")
        return (
            f"Workstation(id={self.id}, name={self.name!r}, "
            f"ct={self.cycle_time:.1f}min, pos=({self.x},{self.y}), {status})"
        )


@dataclass
class WorkstationNetwork:
    """
    Collection of workstations and the material-flow edges between them.
    Represents either the Original or the Improved layout.
    """
    name: str                              # "Original" or "Improved"
    workstations: list                     # List[Workstation]
    flow_matrix: list                      # n×n list[list[float]] — UL per shift
    distance_matrix: list                  # n×n list[list[float]] — metres
    takt_time: float = 5.625              # min
    layout_type: str = "traditional"

    # ------------------------------------------------------------------ #
    #  Lookup helpers                                                      #
    # ------------------------------------------------------------------ #

    def get(self, ws_id: int) -> Optional[Workstation]:
        for ws in self.workstations:
            if ws.id == ws_id:
                return ws
        return None

    @property
    def active_stations(self) -> list:
        return [ws for ws in self.workstations if ws.active]

    @property
    def bottlenecks(self) -> list:
        return [ws for ws in self.active_stations if ws.cycle_time > self.takt_time]

    # ------------------------------------------------------------------ #
    #  Material workflow (Equation 1 from the paper)                       #
    #  E_MWF = Σ_i Σ_j q_ij * l_ij                                       #
    # ------------------------------------------------------------------ #

    def material_workflow(self) -> float:
        total = 0.0
        n = len(self.flow_matrix)
        for i in range(n):
            for j in range(n):
                total += self.flow_matrix[i][j] * self.distance_matrix[i][j]
        return round(total, 2)

    def total_travel_distance(self) -> float:
        """Sum of distances where there IS material flow (q_ij > 0)."""
        total = 0.0
        n = len(self.flow_matrix)
        for i in range(n):
            for j in range(n):
                if self.flow_matrix[i][j] > 0:
                    total += self.distance_matrix[i][j]
        return round(total, 2)

    def reset_all_stats(self) -> None:
        for ws in self.workstations:
            ws.reset_stats()

    def summary(self) -> dict:
        return {
            "layout": self.name,
            "num_workstations": len(self.active_stations),
            "bottlenecks": [ws.name for ws in self.bottlenecks],
            "material_workflow_ul_m": self.material_workflow(),
            "travel_distance_m": self.total_travel_distance(),
        }
