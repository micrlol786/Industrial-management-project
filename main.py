"""
main.py  -  Lean + FLD Manufacturing Simulation
Run: python main.py
"""

# Force non-interactive backend BEFORE any other matplotlib import
import matplotlib
matplotlib.use("Agg")

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.simulation.scenarios import (
    build_original_scenario,
    build_improved_scenario,
    get_shift_info,
    get_lean_tools,
)
from src.simulation.engine import run_simulation
from src.lean.line_balancing import (
    apply_line_balancing, print_line_balance_report, ORIGINAL_CYCLE_TIMES,
)
from src.lean.value_stream import print_vsm_report
from src.fld.material_workflow import print_kpi_table, compute_fld_comparison
from src.visualization.layout_viz import render_static_comparison, render_animation
from src.visualization.dashboard import render_dashboard


def header(text):
    print(f"\n{'='*65}")
    print(f"  {text}")
    print(f"{'='*65}")


def run_full(output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)
    abs_out = os.path.abspath(output_dir)
    print(f"\n  Output folder: {abs_out}")

    header("LEAN + FLD MANUFACTURING SIMULATION")
    print("  Paper: Kovacs (2020) - IJPR 58(10), 2916-2936")
    shift = get_shift_info()
    print(f"  Shift: {shift['total_available_time_min']} min | "
          f"Demand: {shift['customer_demand_per_shift']} u/shift | "
          f"Takt: {shift['takt_time_min']} min/u")
    print(f"  Lean tools applied: {len(get_lean_tools())}")

    header("1/5  VALUE STREAM MAPPING")
    print_vsm_report()

    header("2/5  TAKT-TIME & LINE BALANCING")
    lb = apply_line_balancing(ORIGINAL_CYCLE_TIMES, shift["takt_time_min"])
    print_line_balance_report(lb)

    header("3/5  KPI TABLE (Paper Table 3)")
    print_kpi_table()

    header("4/5  DISCRETE-EVENT SIMULATION")
    print("\n  Running Original scenario ...")
    orig_result = run_simulation(build_original_scenario(), seed=42)
    orig_result.print_summary()

    print("  Running Improved scenario ...")
    impr_result = run_simulation(build_improved_scenario(), seed=42)
    impr_result.print_summary()

    print(f"\n  {'Metric':<35} {'Original':>10} {'Improved':>10} {'Delta':>8}")
    print("  " + "-" * 67)
    for name, o, i in [
        ("Units completed",       orig_result.units_completed,      impr_result.units_completed),
        ("Avg lead time (min)",   orig_result.avg_lead_time,         impr_result.avg_lead_time),
        ("Avg WIP",               orig_result.avg_wip,               impr_result.avg_wip),
        ("VA ratio (%)",          orig_result.avg_value_added_ratio, impr_result.avg_value_added_ratio),
        ("Material workflow",     orig_result.material_workflow,     impr_result.material_workflow),
        ("Travel distance (m)",   orig_result.travel_distance,       impr_result.travel_distance),
    ]:
        delta = f"{(i-o)/o*100:+.1f}%" if o > 0 else "N/A"
        print(f"  {name:<35} {o:>10.2f} {i:>10.2f} {delta:>8}")

    header("5/5  GENERATING VISUAL OUTPUTS")
    print()

    outputs_created = []

    try:
        p = render_static_comparison(output_dir)
        outputs_created.append(p)
        print(f"  [OK] {os.path.abspath(p)}")
    except Exception as e:
        print(f"  [FAIL] layout_comparison.png: {e}")

    try:
        p = render_dashboard(orig_result, impr_result, output_dir)
        outputs_created.append(p)
        print(f"  [OK] {os.path.abspath(p)}")
    except Exception as e:
        print(f"  [FAIL] kpi_dashboard.png: {e}")

    try:
        p = render_animation(output_dir, scenario="improved")
        outputs_created.append(p)
        print(f"  [OK] {os.path.abspath(p)}")
    except Exception as e:
        print(f"  [FAIL] animation_improved.gif: {e}")

    try:
        p = render_animation(output_dir, scenario="original")
        outputs_created.append(p)
        print(f"  [OK] {os.path.abspath(p)}")
    except Exception as e:
        print(f"  [FAIL] animation_original.gif: {e}")

    print(f"\n  {len(outputs_created)} file(s) saved to: {abs_out}")
    header("SIMULATION COMPLETE")


def run_kpi_only():
    print_kpi_table()


def run_layout_only(output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)
    render_static_comparison(output_dir)


def run_sim_only():
    for _, builder in [("Original", build_original_scenario),
                       ("Improved", build_improved_scenario)]:
        run_simulation(builder(), seed=42).print_summary()


def run_compare():
    print_vsm_report()
    print_line_balance_report(apply_line_balancing(ORIGINAL_CYCLE_TIMES, 5.625))
    print_kpi_table()
    orig = build_original_scenario()
    impr = build_improved_scenario()
    fld  = compute_fld_comparison(
        orig.flow_matrix, orig.distance_matrix,
        impr.flow_matrix, impr.distance_matrix,
    )
    print(f"  MWF  orig/impr: {fld['original']['material_workflow_ul_m']} / "
          f"{fld['improved']['material_workflow_ul_m']} UL.m")
    print(f"  Dist orig/impr: {fld['original']['travel_distance_m']} / "
          f"{fld['improved']['travel_distance_m']} m")


def run_animate(output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)
    render_animation(output_dir, "original")
    render_animation(output_dir, "improved")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lean+FLD Simulation")
    parser.add_argument("--mode",
                        choices=["full","kpi","layout","sim","compare","animate"],
                        default="full")
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()

    {
        "full":    lambda: run_full(args.output_dir),
        "kpi":     run_kpi_only,
        "layout":  lambda: run_layout_only(args.output_dir),
        "sim":     run_sim_only,
        "compare": run_compare,
        "animate": lambda: run_animate(args.output_dir),
    }[args.mode]()
