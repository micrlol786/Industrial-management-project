"""
plots.py – Matplotlib visualisations for the Lean+FLD simulation.

Figures produced:
  1. layout_comparison()     – Original vs Improved shop floor
  2. cycle_time_chart()      – Bar chart vs takt-time (Fig 3 & 4 replica)
  3. kpi_comparison()        – Side-by-side bar chart of all KPIs
  4. utilisation_heatmap()   – Workstation utilisation heatmap
  5. wip_timeline()          – WIP level over shift
  6. throughput_timeline()   – Cumulative units over time
  7. convergence_plot()      – FLD optimiser convergence
  8. material_flow_diagram() – Sankey-style flow overlay on layout
"""

from __future__ import annotations
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.cm as cm
from matplotlib.patches import FancyArrowPatch
from typing import Dict, Tuple, List, Optional

# ── colour palette ──────────────────────────────────────────────────────
C_ORIGINAL = "#E05C5C"
C_IMPROVED = "#4A9EDB"
C_TAKT     = "#2ECC71"
C_FIXED    = "#E67E22"
C_MOVEABLE = "#95A5A6"
C_BG       = "#F8F9FA"
C_GRID     = "#DEE2E6"


# ══════════════════════════════════════════════════════════════
#  1. Layout Comparison
# ══════════════════════════════════════════════════════════════
def layout_comparison(
    orig_positions: Dict[int, Tuple[float, float]],
    impr_positions: Dict[int, Tuple[float, float]],
    orig_flow: Dict[Tuple[int, int], float],
    impr_flow: Dict[Tuple[int, int], float],
    fixed_orig: set,
    fixed_impr: set,
    save_path: Optional[str] = None,
):
    fig, axes = plt.subplots(1, 2, figsize=(18, 8), facecolor=C_BG)

    for ax, positions, flow, fixed, title in [
        (axes[0], orig_positions, orig_flow, fixed_orig, "ORIGINAL Layout  (14 WS)"),
        (axes[1], impr_positions, impr_flow, fixed_impr, "IMPROVED Layout  (12 WS, U-Cell)"),
    ]:
        ax.set_facecolor(C_BG)
        ax.set_title(title, fontsize=13, fontweight="bold", pad=12)

        # Grid
        for x in np.arange(0, 26, 0.5):
            ax.axvline(x, color=C_GRID, lw=0.3, zorder=0)
        for y in np.arange(0, 14, 0.5):
            ax.axhline(y, color=C_GRID, lw=0.3, zorder=0)

        # Flow arrows
        max_q = max(flow.values()) if flow else 1
        for (i, j), q in flow.items():
            if i in positions and j in positions:
                xi, yi = positions[i]
                xj, yj = positions[j]
                alpha = 0.3 + 0.5 * (q / max_q)
                ax.annotate(
                    "", xy=(xj, yj), xytext=(xi, yi),
                    arrowprops=dict(
                        arrowstyle="-|>",
                        color=C_ORIGINAL if ax == axes[0] else C_IMPROVED,
                        lw=0.8 + 1.5*(q/max_q),
                        alpha=alpha,
                        connectionstyle="arc3,rad=0.1",
                    ),
                    zorder=1,
                )
                # Flow label
                mx, my = (xi+xj)/2, (yi+yj)/2
                ax.text(mx, my, f"{int(q)}UL", fontsize=6, ha="center",
                        color="#555", zorder=3)

        # Workstation circles
        for ws_id, (x, y) in positions.items():
            colour = C_FIXED if ws_id in fixed else C_MOVEABLE
            circle = plt.Circle((x, y), 0.6, color=colour, zorder=4, ec="white", lw=1.5)
            ax.add_patch(circle)
            ax.text(x, y, str(ws_id), ha="center", va="center",
                    fontsize=9, fontweight="bold", color="white", zorder=5)

        # Legend
        handles = [
            mpatches.Patch(color=C_FIXED,    label="Fixed WS"),
            mpatches.Patch(color=C_MOVEABLE, label="Moveable WS"),
        ]
        ax.legend(handles=handles, loc="lower right", fontsize=8)
        ax.set_xlim(-1, 25)
        ax.set_ylim(-1, 13)
        ax.set_xlabel("X (m)", fontsize=9)
        ax.set_ylabel("Y (m)", fontsize=9)
        ax.set_aspect("equal")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


# ══════════════════════════════════════════════════════════════
#  2. Cycle-Time Chart  (replicates Fig 3 & 4 of the paper)
# ══════════════════════════════════════════════════════════════
def cycle_time_chart(
    original_ct: Dict[int, float],
    improved_ct: Dict[int, float],
    takt_time: float,
    save_path: Optional[str] = None,
):
    ws_ids  = sorted(original_ct.keys())
    orig_vals = [original_ct[w] for w in ws_ids]
    impr_vals = [improved_ct.get(w, 0) for w in ws_ids]

    x = np.arange(len(ws_ids))
    width = 0.38

    fig, ax = plt.subplots(figsize=(14, 5), facecolor=C_BG)
    ax.set_facecolor(C_BG)

    bars_o = ax.bar(x - width/2, orig_vals, width, label="Original CT",
                    color=C_ORIGINAL, alpha=0.85, zorder=3)
    bars_i = ax.bar(x + width/2, impr_vals, width, label="Improved CT",
                    color=C_IMPROVED, alpha=0.85, zorder=3)

    ax.axhline(takt_time, color=C_TAKT, lw=2.2, ls="--",
               label=f"Takt-time ({takt_time:.2f} min)", zorder=4)

    # Highlight eliminated workstations
    for idx, w in enumerate(ws_ids):
        if improved_ct.get(w, 0) == 0:
            ax.axvspan(idx - 0.5, idx + 0.5, color="#FFE0E0", alpha=0.4, zorder=1)
            ax.text(idx, 0.2, "ELIM.", ha="center", va="bottom",
                    fontsize=7, color=C_ORIGINAL, rotation=90, zorder=5)

    ax.set_xticks(x)
    ax.set_xticklabels([f"WS{w}" for w in ws_ids], fontsize=9)
    ax.set_ylabel("Cycle time (min/unit)", fontsize=10)
    ax.set_title("Cycle-Time Analysis: Original vs Improved  |  Paper Fig. 3–4 Replica",
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.set_ylim(0, max(orig_vals)*1.25)
    ax.grid(axis="y", color=C_GRID, zorder=0)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


# ══════════════════════════════════════════════════════════════
#  3. KPI Comparison Dashboard
# ══════════════════════════════════════════════════════════════
def kpi_comparison(
    paper_results: dict,
    save_path: Optional[str] = None,
):
    quant_keys = [
        "longest_cycle_time", "productivity", "num_workstations",
        "num_operators", "wip_inventory", "space_used",
        "material_workflow", "travel_distance",
        "material_handling_cost", "labour_cost",
    ]
    labels = [
        "Longest CT\n(min)", "Productivity\n(u/shift)", "# Workstations",
        "# Operators", "WIP (%)", "Space (m²)",
        "Mat.Workflow\n(UL·m)", "Travel Dist\n(m)",
        "MH Cost (%)", "Labour Cost (%)",
    ]

    orig_vals = [paper_results[k]["original"] for k in quant_keys]
    impr_vals = [paper_results[k]["improved"] for k in quant_keys]

    x = np.arange(len(quant_keys))
    width = 0.38

    fig, ax = plt.subplots(figsize=(16, 6), facecolor=C_BG)
    ax.set_facecolor(C_BG)

    ax.bar(x - width/2, orig_vals, width, label="Original",
           color=C_ORIGINAL, alpha=0.9, zorder=3)
    ax.bar(x + width/2, impr_vals, width, label="Improved",
           color=C_IMPROVED, alpha=0.9, zorder=3)

    # Improvement annotations
    for i, (o, m) in enumerate(zip(orig_vals, impr_vals)):
        pct = (m - o) / o * 100 if o != 0 else 0
        sign = "+" if pct > 0 else ""
        color = C_IMPROVED if pct < 0 else C_ORIGINAL
        if i == 1:   # productivity — positive is good
            color = C_IMPROVED
        ax.text(x[i], max(o, m) * 1.03, f"{sign}{pct:.1f}%",
                ha="center", va="bottom", fontsize=7.5,
                color=color, fontweight="bold", zorder=5)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_title("KPI Comparison: Original vs Improved  (Table 3 of Kovács 2020)",
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(axis="y", color=C_GRID, zorder=0)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


# ══════════════════════════════════════════════════════════════
#  4. Utilisation Heatmap
# ══════════════════════════════════════════════════════════════
def utilisation_heatmap(
    positions: Dict[int, Tuple[float, float]],
    utilisation: Dict[int, float],
    title: str = "Workstation Utilisation",
    save_path: Optional[str] = None,
):
    fig, ax = plt.subplots(figsize=(10, 7), facecolor=C_BG)
    ax.set_facecolor("#ECEFF1")

    cmap = cm.RdYlGn
    norm = plt.Normalize(0, 1)

    for ws_id, (x, y) in positions.items():
        u = utilisation.get(ws_id, 0)
        colour = cmap(norm(u))
        circle = plt.Circle((x, y), 0.8, color=colour, zorder=3, ec="white", lw=2)
        ax.add_patch(circle)
        ax.text(x, y + 0.05, f"WS{ws_id}", ha="center", va="center",
                fontsize=8, fontweight="bold", color="black", zorder=4)
        ax.text(x, y - 0.35, f"{u*100:.0f}%", ha="center", va="center",
                fontsize=7, color="white", zorder=4)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    plt.colorbar(sm, ax=ax, label="Utilisation", shrink=0.6)

    ax.set_xlim(-1, 24)
    ax.set_ylim(-1, 13)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel("X (m)"); ax.set_ylabel("Y (m)")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


# ══════════════════════════════════════════════════════════════
#  5. WIP Timeline
# ══════════════════════════════════════════════════════════════
def wip_timeline(
    wip_history_orig: List[Tuple[float, int]],
    wip_history_impr: List[Tuple[float, int]],
    save_path: Optional[str] = None,
):
    fig, ax = plt.subplots(figsize=(13, 4), facecolor=C_BG)
    ax.set_facecolor(C_BG)

    if wip_history_orig:
        t_o, w_o = zip(*wip_history_orig)
        ax.step(t_o, w_o, color=C_ORIGINAL, lw=1.5, label="Original WIP",
                where="post", alpha=0.8)

    if wip_history_impr:
        t_i, w_i = zip(*wip_history_impr)
        ax.step(t_i, w_i, color=C_IMPROVED, lw=1.5, label="Improved WIP",
                where="post", alpha=0.8)

    ax.set_xlabel("Time (min)", fontsize=10)
    ax.set_ylabel("WIP Level (units)", fontsize=10)
    ax.set_title("Work-in-Process (WIP) Over One Shift", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(color=C_GRID, zorder=0)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


# ══════════════════════════════════════════════════════════════
#  6. Throughput Timeline
# ══════════════════════════════════════════════════════════════
def throughput_timeline(
    timeline_orig: List[Tuple[float, int]],
    timeline_impr: List[Tuple[float, int]],
    save_path: Optional[str] = None,
):
    fig, ax = plt.subplots(figsize=(13, 4), facecolor=C_BG)
    ax.set_facecolor(C_BG)

    if timeline_orig:
        t_o, u_o = zip(*timeline_orig)
        ax.plot(t_o, u_o, color=C_ORIGINAL, lw=2, label="Original", marker=".", ms=3)
    if timeline_impr:
        t_i, u_i = zip(*timeline_impr)
        ax.plot(t_i, u_i, color=C_IMPROVED, lw=2, label="Improved", marker=".", ms=3)

    ax.set_xlabel("Time (min)", fontsize=10)
    ax.set_ylabel("Cumulative Units Completed", fontsize=10)
    ax.set_title("Throughput: Cumulative Production Over Shift", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(color=C_GRID, zorder=0)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


# ══════════════════════════════════════════════════════════════
#  7. FLD Convergence Plot
# ══════════════════════════════════════════════════════════════
def convergence_plot(
    iterations: List[int],
    emwf_values: List[float],
    save_path: Optional[str] = None,
):
    fig, ax = plt.subplots(figsize=(9, 4), facecolor=C_BG)
    ax.set_facecolor(C_BG)

    ax.plot(iterations, emwf_values, color=C_IMPROVED, lw=2.2, marker="o",
            ms=4, markevery=max(1, len(iterations)//15))
    ax.axhline(min(emwf_values), color=C_TAKT, lw=1.5, ls="--",
               label=f"Best: {min(emwf_values):.1f} UL·m")

    ax.set_xlabel("Iteration", fontsize=10)
    ax.set_ylabel("Material Workflow  E_MWF (UL·m)", fontsize=10)
    ax.set_title("FLD Optimisation Convergence", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(color=C_GRID, zorder=0)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig
