"""tests/test_simulation.py – Integration tests for the DES simulation."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.simulation.manufacturing_plant import ManufacturingPlant


class TestManufacturingPlant:
    def test_original_runs(self):
        plant = ManufacturingPlant(scenario="original", random_seed=42)
        res = plant.run()
        assert res.units_completed > 0
        assert res.num_workstations == 14

    def test_improved_runs(self):
        plant = ManufacturingPlant(scenario="improved", random_seed=42)
        res = plant.run()
        assert res.units_completed > 0
        assert res.num_workstations == 12

    def test_improved_higher_productivity(self):
        orig = ManufacturingPlant("original", random_seed=42).run()
        impr = ManufacturingPlant("improved", random_seed=42).run()
        assert impr.productivity > orig.productivity

    def test_improved_lower_bottleneck(self):
        orig = ManufacturingPlant("original", random_seed=42).run()
        impr = ManufacturingPlant("improved", random_seed=42).run()
        assert impr.bottleneck_ct < orig.bottleneck_ct

    def test_invalid_scenario(self):
        with pytest.raises(ValueError):
            ManufacturingPlant(scenario="bad")

    def test_utilisation_in_range(self):
        plant = ManufacturingPlant("original", random_seed=42)
        res = plant.run()
        for ws_id, util in res.ws_utilisation.items():
            assert 0.0 <= util <= 1.0, f"WS{ws_id} utilisation {util} out of range"

    def test_material_workflow_reduced(self):
        orig = ManufacturingPlant("original", random_seed=42).run()
        impr = ManufacturingPlant("improved", random_seed=42).run()
        assert impr.material_workflow < orig.material_workflow

    def test_travel_distance_reduced(self):
        orig = ManufacturingPlant("original", random_seed=42).run()
        impr = ManufacturingPlant("improved", random_seed=42).run()
        assert impr.travel_distance < orig.travel_distance


class TestFLDOptimiser:
    def test_greedy_does_not_increase_emwf(self):
        from src.layout.facility_layout import FacilityLayoutDesigner
        from config.plant_config import (
            ORIGINAL_POSITIONS, ORIGINAL_MATERIAL_FLOW,
            FIXED_WORKSTATIONS_ORIGINAL,
        )
        from src.simulation.metrics import material_workflow

        init_emwf = material_workflow(ORIGINAL_MATERIAL_FLOW, ORIGINAL_POSITIONS)
        designer = FacilityLayoutDesigner(
            initial_positions=ORIGINAL_POSITIONS,
            flow_matrix=ORIGINAL_MATERIAL_FLOW,
            fixed_ws=FIXED_WORKSTATIONS_ORIGINAL,
        )
        sol = designer.optimise()
        assert sol.emwf <= init_emwf + 0.01  # must not be worse
