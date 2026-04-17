"""
facility_layout.py – Facility Layout Design (FLD) module.

Implements the optimisation procedure described in Section 2.3.1 of
Kovács (2020): minimise total material workflow E_MWF = Σ q_ij * l_ij
by searching candidate layouts via a greedy / local-search approach.
"""

from __future__ import annotations
import math
import copy
import random
import itertools
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass, field


@dataclass
class LayoutSolution:
    positions: Dict[int, Tuple[float, float]]
    emwf: float
    travel_distance: float
    generation: int = 0

    def __repr__(self) -> str:
        return f"Layout(emwf={self.emwf:.1f} UL·m, dist={self.travel_distance:.1f} m)"


class FacilityLayoutDesigner:
    """
    Optimises workstation positions to minimise material workflow.

    Approach
    --------
    1. Start from an initial layout (e.g. original positions).
    2. For each pair of moveable workstations, swap positions and check
       if E_MWF improves.
    3. Accept improvements greedily; repeat until convergence.

    Fixed workstations are never moved (design constraint in the paper).
    """

    def __init__(
        self,
        initial_positions: Dict[int, Tuple[float, float]],
        flow_matrix: Dict[Tuple[int, int], float],
        fixed_ws: set,
        grid_size: float = 0.5,
        max_iterations: int = 500,
        random_seed: int = 42,
    ):
        self.positions = copy.deepcopy(initial_positions)
        self.flow_matrix = flow_matrix
        self.fixed_ws = fixed_ws
        self.grid_size = grid_size
        self.max_iterations = max_iterations
        self.moveable_ws = [k for k in initial_positions if k not in fixed_ws]
        self.history: List[LayoutSolution] = []
        random.seed(random_seed)

    # ------------------------------------------------------------------ #
    def _calc_emwf(self, positions: Dict[int, Tuple[float, float]]) -> float:
        emwf = 0.0
        for (i, j), q in self.flow_matrix.items():
            if i in positions and j in positions:
                xi, yi = positions[i]
                xj, yj = positions[j]
                emwf += q * math.sqrt((xi-xj)**2 + (yi-yj)**2)
        return emwf

    def _calc_travel(self, positions: Dict[int, Tuple[float, float]]) -> float:
        total = 0.0
        for (i, j) in self.flow_matrix:
            if i in positions and j in positions:
                xi, yi = positions[i]
                xj, yj = positions[j]
                total += math.sqrt((xi-xj)**2 + (yi-yj)**2)
        return total

    # ------------------------------------------------------------------ #
    def optimise(self) -> LayoutSolution:
        """Run greedy pairwise-swap optimisation."""
        best_positions = copy.deepcopy(self.positions)
        best_emwf = self._calc_emwf(best_positions)
        iteration = 0
        improved = True

        self.history.append(LayoutSolution(
            positions=copy.deepcopy(best_positions),
            emwf=best_emwf,
            travel_distance=self._calc_travel(best_positions),
            generation=0,
        ))

        while improved and iteration < self.max_iterations:
            improved = False
            pairs = list(itertools.combinations(self.moveable_ws, 2))
            random.shuffle(pairs)

            for ws_a, ws_b in pairs:
                candidate = copy.deepcopy(best_positions)
                # Swap positions
                candidate[ws_a], candidate[ws_b] = candidate[ws_b], candidate[ws_a]
                candidate_emwf = self._calc_emwf(candidate)

                if candidate_emwf < best_emwf - 1e-6:
                    best_positions = candidate
                    best_emwf = candidate_emwf
                    improved = True

            iteration += 1
            self.history.append(LayoutSolution(
                positions=copy.deepcopy(best_positions),
                emwf=best_emwf,
                travel_distance=self._calc_travel(best_positions),
                generation=iteration,
            ))

        return LayoutSolution(
            positions=best_positions,
            emwf=best_emwf,
            travel_distance=self._calc_travel(best_positions),
            generation=iteration,
        )

    # ------------------------------------------------------------------ #
    def optimise_simulated_annealing(
        self,
        T_initial: float = 100.0,
        T_final: float = 0.1,
        cooling: float = 0.97,
    ) -> LayoutSolution:
        """
        Simulated Annealing variant — escapes local optima.
        Better suited for larger layouts with many moveable stations.
        """
        current = copy.deepcopy(self.positions)
        current_emwf = self._calc_emwf(current)
        best = copy.deepcopy(current)
        best_emwf = current_emwf
        T = T_initial
        iteration = 0

        self.history = [LayoutSolution(
            positions=copy.deepcopy(best),
            emwf=best_emwf,
            travel_distance=self._calc_travel(best),
            generation=0,
        )]

        while T > T_final and iteration < self.max_iterations:
            # Random swap of two moveable workstations
            if len(self.moveable_ws) < 2:
                break
            ws_a, ws_b = random.sample(self.moveable_ws, 2)
            candidate = copy.deepcopy(current)
            candidate[ws_a], candidate[ws_b] = candidate[ws_b], candidate[ws_a]
            candidate_emwf = self._calc_emwf(candidate)

            delta = candidate_emwf - current_emwf
            if delta < 0 or random.random() < math.exp(-delta / T):
                current = candidate
                current_emwf = candidate_emwf

                if current_emwf < best_emwf:
                    best = copy.deepcopy(current)
                    best_emwf = current_emwf

            T *= cooling
            iteration += 1

            if iteration % 20 == 0:
                self.history.append(LayoutSolution(
                    positions=copy.deepcopy(best),
                    emwf=best_emwf,
                    travel_distance=self._calc_travel(best),
                    generation=iteration,
                ))

        return LayoutSolution(
            positions=best,
            emwf=best_emwf,
            travel_distance=self._calc_travel(best),
            generation=iteration,
        )

    # ------------------------------------------------------------------ #
    def convergence_data(self) -> Tuple[List[int], List[float]]:
        """Returns (iterations, emwf_values) for plotting convergence."""
        iters = [s.generation for s in self.history]
        emwfs = [s.emwf for s in self.history]
        return iters, emwfs
