"""tests/test_metrics.py – Unit tests for all KPI formulae."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import math
from src.simulation.metrics import (
    takt_time, ideal_num_operators, material_workflow,
    material_handling_cost, labour_cost, productivity,
    total_travel_distance, find_bottleneck, line_balance_efficiency,
)


class TestTaktTime:
    def test_paper_value(self):
        tt = takt_time(450, 80)
        assert abs(tt - 5.625) < 0.001

    def test_zero_demand_raises(self):
        with pytest.raises(ValueError):
            takt_time(450, 0)


class TestIdealOperators:
    def test_paper_case(self):
        """Paper: TT=60.7, takt=5.625 → N≈10.8"""
        n = ideal_num_operators(60.7, 5.625)
        assert abs(n - 10.79) < 0.05


class TestMaterialWorkflow:
    def test_simple(self):
        flow = {(1, 2): 10}
        pos  = {1: (0.0, 0.0), 2: (3.0, 4.0)}  # dist = 5
        emwf = material_workflow(flow, pos)
        assert abs(emwf - 50.0) < 0.01

    def test_empty(self):
        assert material_workflow({}, {}) == 0.0


class TestMaterialHandlingCost:
    def test_linear(self):
        assert material_handling_cost(365, 0.05) == pytest.approx(18.25)


class TestLabourCost:
    def test_basic(self):
        assert labour_cost(14, 150) == 2100
        assert labour_cost(12, 150) == 1800


class TestProductivity:
    def test_original(self):
        """6.1 min bottleneck → 450/6.1 ≈ 73.8"""
        p = productivity(450, 6.1)
        assert abs(p - 73.77) < 0.1

    def test_improved(self):
        """5.4 min → 450/5.4 ≈ 83.3"""
        p = productivity(450, 5.4)
        assert abs(p - 83.33) < 0.1


class TestBottleneck:
    def test_finds_correct(self):
        cts = {1: 4.6, 2: 3.9, 9: 6.1, 11: 5.2}
        bot_id, bot_ct = find_bottleneck(cts)
        assert bot_id == 9
        assert bot_ct == 6.1


class TestLineBalanceEfficiency:
    def test_perfect_balance(self):
        """If all CTs equal takt-time, LBE = 1.0"""
        cts = {1: 5.625, 2: 5.625}
        lbe = line_balance_efficiency(cts, 5.625)
        assert abs(lbe - 1.0) < 0.001

    def test_paper_original(self):
        """Should be < 1 due to imbalance."""
        from config.plant_config import ORIGINAL_CYCLE_TIMES, TAKT_TIME
        lbe = line_balance_efficiency(ORIGINAL_CYCLE_TIMES, TAKT_TIME)
        assert 0.5 < lbe < 1.0
