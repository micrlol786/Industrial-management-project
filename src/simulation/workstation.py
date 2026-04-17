"""workstation.py – Individual workstation model for discrete-event simulation."""

from __future__ import annotations
import simpy
import random
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WorkstationStats:
    total_processed: int = 0
    total_busy_time: float = 0.0
    total_idle_time: float = 0.0
    total_wait_time: float = 0.0
    wip_samples: list = field(default_factory=list)


class Workstation:
    """
    A single workstation in the manufacturing plant.

    Parameters
    ----------
    env          : simpy.Environment
    ws_id        : int – workstation identifier
    cycle_time   : float – mean processing time (minutes)
    position     : tuple[float, float] – (x, y) on shop floor (metres)
    variation_pct: float – ±% random variation around mean cycle time
    """

    def __init__(
        self,
        env: simpy.Environment,
        ws_id: int,
        cycle_time: float,
        position: tuple[float, float],
        variation_pct: float = 0.05,
    ):
        self.env = env
        self.ws_id = ws_id
        self.cycle_time = cycle_time
        self.position = position
        self.variation_pct = variation_pct

        self.resource = simpy.Resource(env, capacity=1)
        self.stats = WorkstationStats()
        self._last_free_at: float = 0.0

    # ------------------------------------------------------------------ #
    def process(self, unit_id: int, arrival_time: float):
        """Process one unit through this workstation."""
        wait_start = self.env.now

        with self.resource.request() as req:
            yield req

            wait_time = self.env.now - wait_start
            self.stats.total_wait_time += wait_time

            # Idle time = gap since last unit finished
            idle = self.env.now - self._last_free_at
            if idle > 0:
                self.stats.total_idle_time += idle

            # Actual processing with ±variation
            actual_time = self._sample_cycle_time()
            yield self.env.timeout(actual_time)

            self.stats.total_busy_time += actual_time
            self.stats.total_processed += 1
            self._last_free_at = self.env.now

    # ------------------------------------------------------------------ #
    def _sample_cycle_time(self) -> float:
        delta = self.cycle_time * self.variation_pct
        return max(0.1, random.uniform(self.cycle_time - delta, self.cycle_time + delta))

    # ------------------------------------------------------------------ #
    @property
    def utilisation(self) -> float:
        elapsed = self.env.now
        if elapsed <= 0:
            return 0.0
        return min(1.0, self.stats.total_busy_time / elapsed)

    @property
    def avg_wait_time(self) -> float:
        if self.stats.total_processed == 0:
            return 0.0
        return self.stats.total_wait_time / self.stats.total_processed

    def __repr__(self) -> str:
        return (
            f"Workstation(id={self.ws_id}, ct={self.cycle_time:.1f}min, "
            f"processed={self.stats.total_processed})"
        )
