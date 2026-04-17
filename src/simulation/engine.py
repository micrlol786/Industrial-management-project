"""
engine.py
---------
Discrete-event simulation of the automotive component assembly line.
Pure Python — no SimPy required.

Uses an event-queue (min-heap) approach:
  • Each workstation has a "free_at" timestamp.
  • Each product is released every takt_time minutes.
  • Products queue at workstations and are processed as soon as the
    station is free.

Kovács (2020) case study: one 450-min shift, 80 units demanded.
"""

import heapq
import random
import statistics
from typing import List, Dict, Any, Optional

from src.models.workstation import WorkstationNetwork
from src.models.product import Product


# ──────────────────────────────────────────────────────────────────────────────
#  Event-queue simulation
# ──────────────────────────────────────────────────────────────────────────────

def _run_shift(
    network: WorkstationNetwork,
    shift_duration: float,
    rng: random.Random,
) -> List[Product]:
    """
    Simulate one shift using a station-by-station sequential model.

    Each product is injected at time = unit_id * takt_time.
    At each workstation the product waits until max(arrival, station_free_at),
    then occupies the station for cycle_time (±5 % jitter).
    """
    stations = network.active_stations
    # track when each station becomes free
    free_at: Dict[int, float] = {ws.id: 0.0 for ws in stations}

    products: List[Product] = []
    unit_id = 0
    release_time = 0.0

    while release_time < shift_duration:
        unit_id += 1
        product = Product(unit_id=unit_id, arrival_time=release_time)

        current_time = release_time
        for ws in stations:
            arrive_at_ws = current_time
            start_time   = max(arrive_at_ws, free_at[ws.id])
            wait          = start_time - arrive_at_ws

            ct = ws.cycle_time * rng.uniform(0.95, 1.05)
            finish_time = start_time + ct

            free_at[ws.id] = finish_time
            ws.total_busy  += ct
            ws.total_idle  += max(0.0, start_time - free_at[ws.id] + ct)  # approx
            ws.units_done  += 1
            ws.queue        = max(0, ws.queue - 1)

            product.record_step(ws.id, round(wait, 4), round(ct, 4))
            current_time = finish_time

        product.complete(current_time)
        products.append(product)
        release_time += network.takt_time

    return products


# ──────────────────────────────────────────────────────────────────────────────
#  Result container
# ──────────────────────────────────────────────────────────────────────────────

class SimulationResult:
    def __init__(
        self,
        scenario_name: str,
        products: List[Product],
        network: WorkstationNetwork,
        shift_duration: float,
    ) -> None:
        self.scenario_name = scenario_name
        self.products = [p for p in products if p.departure_time is not None]
        self.network = network
        self.shift_duration = shift_duration

    # ── throughput ────────────────────────────────────────────────────────────
    @property
    def units_completed(self) -> int:
        return len(self.products)

    @property
    def productivity(self) -> int:
        return self.units_completed

    # ── lead time ─────────────────────────────────────────────────────────────
    @property
    def avg_lead_time(self) -> float:
        lt = [p.lead_time for p in self.products if p.lead_time]
        return round(statistics.mean(lt), 3) if lt else 0.0

    # ── WIP (Little's Law) ───────────────────────────────────────────────────
    @property
    def avg_wip(self) -> float:
        rate = self.units_completed / self.shift_duration
        return round(rate * self.avg_lead_time, 2)

    # ── utilisation ───────────────────────────────────────────────────────────
    @property
    def utilisation(self) -> Dict[str, float]:
        result = {}
        for ws in self.network.active_stations:
            total_time = self.shift_duration
            util = min(100.0, ws.total_busy / total_time * 100)
            result[ws.name] = round(util, 1)
        return result

    # ── value-added ratio ─────────────────────────────────────────────────────
    @property
    def avg_value_added_ratio(self) -> float:
        ratios = [p.value_added_ratio for p in self.products if p.lead_time]
        return round(statistics.mean(ratios) * 100, 2) if ratios else 0.0

    # ── FLD metrics ───────────────────────────────────────────────────────────
    @property
    def material_workflow(self) -> float:
        return self.network.material_workflow()

    @property
    def travel_distance(self) -> float:
        return self.network.total_travel_distance()

    # ── summary ───────────────────────────────────────────────────────────────
    def summary(self) -> Dict[str, Any]:
        return {
            "scenario": self.scenario_name,
            "units_completed": self.units_completed,
            "avg_lead_time_min": self.avg_lead_time,
            "avg_wip": self.avg_wip,
            "avg_value_added_ratio_pct": self.avg_value_added_ratio,
            "material_workflow_ul_m": self.material_workflow,
            "travel_distance_m": self.travel_distance,
            "num_workstations": len(self.network.active_stations),
            "utilisation_pct": self.utilisation,
        }

    def print_summary(self) -> None:
        s = self.summary()
        print(f"\n{'='*60}")
        print(f"  Simulation Results — {s['scenario']}")
        print(f"{'='*60}")
        print(f"  Units completed        : {s['units_completed']}")
        print(f"  Avg lead time          : {s['avg_lead_time_min']:.2f} min")
        print(f"  Avg WIP                : {s['avg_wip']:.2f} units")
        print(f"  Value-added ratio      : {s['avg_value_added_ratio_pct']:.1f}%")
        print(f"  Material workflow      : {s['material_workflow_ul_m']} UL·m")
        print(f"  Travel distance        : {s['travel_distance_m']} m")
        print(f"  Active workstations    : {s['num_workstations']}")
        print(f"\n  Station utilisation:")
        for name, util in s["utilisation_pct"].items():
            bar = "█" * int(util / 5)
            print(f"    {name:6s}  {util:5.1f}%  {bar}")
        print()


# ──────────────────────────────────────────────────────────────────────────────
#  Public runner
# ──────────────────────────────────────────────────────────────────────────────

def run_simulation(
    network: WorkstationNetwork,
    shift_duration: float = 450.0,
    seed: int = 42,
) -> SimulationResult:
    """
    Simulate one shift for the given WorkstationNetwork.

    Parameters
    ----------
    network        : Original or Improved WorkstationNetwork
    shift_duration : available minutes per shift (default 450)
    seed           : RNG seed for reproducibility

    Returns
    -------
    SimulationResult
    """
    network.reset_all_stats()
    rng = random.Random(seed)
    products = _run_shift(network, shift_duration, rng)
    return SimulationResult(
        scenario_name=network.name,
        products=products,
        network=network,
        shift_duration=shift_duration,
    )
