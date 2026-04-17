"""
layout_viz.py  -  Factory floor layout visualisation + animation.
NOTE: matplotlib.use("Agg") is set in main.py before this is imported.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np
import os

from src.simulation.scenarios import build_original_scenario, build_improved_scenario

TAKT_TIME = 5.625
WS_SIZE   = 0.7

COLOURS = {
    "background": "#1a1a2e",
    "grid":       "#16213e",
    "text":       "#eaeaea",
    "takt":       "#f5a623",
    "bottleneck": "#e74c3c",
    "ok":         "#2ecc71",
    "fixed":      "#9b59b6",
    "flow_arrow": "#3498db",
    "product":    "#f39c12",
    "free_space": "#1abc9c",
}


def _ct_colour(ct, takt):
    if ct > takt:
        return COLOURS["bottleneck"]
    return COLOURS["ok"] if ct / takt > 0.85 else "#f1c40f"


def _draw_layout(ax, network, title, show_free_space=False, free_space_bounds=None):
    ax.set_facecolor(COLOURS["background"])
    ax.set_title(title, color=COLOURS["text"], fontsize=11,
                 fontweight="bold", pad=10)

    if show_free_space and free_space_bounds:
        b = free_space_bounds
        rect = FancyBboxPatch(
            (b["x_min"], b["y_min"]),
            b["x_max"] - b["x_min"], b["y_max"] - b["y_min"],
            boxstyle="round,pad=0.1", linewidth=1,
            edgecolor=COLOURS["free_space"],
            facecolor=COLOURS["free_space"], alpha=0.12,
        )
        ax.add_patch(rect)
        ax.text(
            (b["x_min"] + b["x_max"]) / 2,
            (b["y_min"] + b["y_max"]) / 2,
            "Free Space\n+56 m2",
            ha="center", va="center",
            color=COLOURS["free_space"], fontsize=7.5, alpha=0.8,
        )

    Q = np.array(network.flow_matrix)
    ws_list = network.active_stations
    max_flow = Q.max() if Q.max() > 0 else 1

    for i, ws_i in enumerate(ws_list):
        for j, ws_j in enumerate(ws_list):
            if i < len(Q) and j < len(Q[0]) and Q[i][j] > 0:
                lw    = 0.5 + 2.5 * (Q[i][j] / max_flow)
                alpha = 0.3 + 0.5 * (Q[i][j] / max_flow)
                ax.annotate(
                    "",
                    xy=(ws_j.x, ws_j.y), xytext=(ws_i.x, ws_i.y),
                    arrowprops=dict(
                        arrowstyle="-|>",
                        color=COLOURS["flow_arrow"],
                        lw=lw, alpha=alpha,
                        connectionstyle="arc3,rad=0.1",
                    ),
                )
                mx = (ws_i.x + ws_j.x) / 2
                my = (ws_i.y + ws_j.y) / 2
                ax.text(mx, my, f"{int(Q[i][j])}UL",
                        color=COLOURS["flow_arrow"], fontsize=5.5,
                        alpha=0.7, ha="center", va="center")

    for ws in ws_list:
        color = COLOURS["fixed"] if ws.fixed else _ct_colour(ws.cycle_time, TAKT_TIME)
        rect = FancyBboxPatch(
            (ws.x - WS_SIZE, ws.y - WS_SIZE),
            2 * WS_SIZE, 2 * WS_SIZE,
            boxstyle="round,pad=0.07",
            linewidth=1.5, edgecolor="white",
            facecolor=color, alpha=0.85, zorder=3,
        )
        ax.add_patch(rect)
        ax.text(ws.x, ws.y + 0.15, ws.name,
                ha="center", va="center",
                color="white", fontsize=7, fontweight="bold", zorder=4)
        ax.text(ws.x, ws.y - 0.22, f"{ws.cycle_time:.1f}m",
                ha="center", va="center",
                color="white", fontsize=6, zorder=4)

    ax.set_xlim(-0.5, 13.5)
    ax.set_ylim(-0.5, 10.5)
    ax.set_aspect("equal")
    ax.tick_params(colors=COLOURS["text"], labelsize=7)
    for spine in ax.spines.values():
        spine.set_color(COLOURS["grid"])
    ax.grid(True, color=COLOURS["grid"], linewidth=0.4, alpha=0.5)
    ax.set_xlabel("x [m]", color=COLOURS["text"], fontsize=8)
    ax.set_ylabel("y [m]", color=COLOURS["text"], fontsize=8)

    legend_elements = [
        mpatches.Patch(color=COLOURS["bottleneck"], label=f"Bottleneck (CT > {TAKT_TIME}m)"),
        mpatches.Patch(color="#f1c40f",             label="Underloaded"),
        mpatches.Patch(color=COLOURS["ok"],         label="OK"),
        mpatches.Patch(color=COLOURS["fixed"],      label="Fixed (monument)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=6,
              facecolor=COLOURS["grid"], labelcolor=COLOURS["text"],
              framealpha=0.7)


def _draw_cycle_time_chart(ax, original_cts, balanced_cts, takt_time,
                           title="Cycle Times vs Takt Time"):
    ax.set_facecolor(COLOURS["background"])
    ax.set_title(title, color=COLOURS["text"], fontsize=10, fontweight="bold")

    ws_ids = sorted(set(list(original_cts.keys()) + list(balanced_cts.keys())))
    x     = np.arange(len(ws_ids))
    width = 0.35

    ax.bar(x - width/2,
           [original_cts.get(i, 0) for i in ws_ids], width,
           label="Original", color="#e74c3c", alpha=0.8, zorder=3)
    ax.bar(x + width/2,
           [balanced_cts.get(i,  0) for i in ws_ids], width,
           label="Balanced", color="#2ecc71", alpha=0.8, zorder=3)
    ax.axhline(takt_time, color=COLOURS["takt"], linewidth=2, linestyle="--",
               label=f"Takt = {takt_time} min", zorder=4)

    ax.set_xticks(x)
    ax.set_xticklabels([f"WS{i}" for i in ws_ids],
                       color=COLOURS["text"], fontsize=7, rotation=45)
    ax.tick_params(colors=COLOURS["text"], labelsize=8)
    ax.set_ylabel("Cycle time [min/unit]", color=COLOURS["text"], fontsize=8)
    ax.legend(fontsize=7, facecolor=COLOURS["grid"],
              labelcolor=COLOURS["text"], framealpha=0.8)
    for spine in ax.spines.values():
        spine.set_color(COLOURS["grid"])
    ax.grid(True, axis="y", color=COLOURS["grid"], linewidth=0.5, alpha=0.6)


def _draw_kpi_bars(ax, kpi_data):
    ax.set_facecolor(COLOURS["background"])
    ax.set_title("KPI Improvement Summary", color=COLOURS["text"],
                 fontsize=10, fontweight="bold")

    labels  = [k.replace("_", "\n").title() for k in kpi_data]
    changes = [v["change_pct"] for v in kpi_data.values()]
    colors  = [COLOURS["ok"] if c > 0 else COLOURS["bottleneck"] for c in changes]
    y_pos   = np.arange(len(labels))

    bars = ax.barh(y_pos, changes, color=colors, alpha=0.85, height=0.6)
    ax.axvline(0, color="white", linewidth=0.8)

    for bar, change in zip(bars, changes):
        sign = "+" if change >= 0 else ""
        ax.text(
            change + (0.3 if change >= 0 else -0.3),
            bar.get_y() + bar.get_height() / 2,
            f"{sign}{change:.1f}%",
            va="center", ha="left" if change >= 0 else "right",
            color="white", fontsize=7,
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, color=COLOURS["text"], fontsize=7)
    ax.tick_params(colors=COLOURS["text"])
    ax.set_xlabel("Change (%)", color=COLOURS["text"], fontsize=8)
    for spine in ax.spines.values():
        spine.set_color(COLOURS["grid"])
    ax.grid(True, axis="x", color=COLOURS["grid"], linewidth=0.4)


def render_static_comparison(output_dir="outputs"):
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "layout_comparison.png")

    original = build_original_scenario()
    improved = build_improved_scenario()

    from src.lean.line_balancing import ORIGINAL_CYCLE_TIMES, BALANCED_CYCLE_TIMES
    balanced_only = {k: v for k, v in BALANCED_CYCLE_TIMES.items() if v > 0}
    from src.fld.material_workflow import PAPER_RESULTS

    fig = plt.figure(figsize=(20, 14), facecolor=COLOURS["background"])
    fig.suptitle(
        "Lean + FLD Combined Process Improvement Simulation\n"
        "Kovacs (2020) - Int. Journal of Production Research",
        color=COLOURS["text"], fontsize=13, fontweight="bold", y=0.98,
    )

    gs = fig.add_gridspec(2, 3, hspace=0.4, wspace=0.35)
    ax_orig  = fig.add_subplot(gs[0, 0])
    ax_impr  = fig.add_subplot(gs[0, 1])
    ax_ct    = fig.add_subplot(gs[0, 2])
    ax_kpi   = fig.add_subplot(gs[1, 0:2])
    ax_table = fig.add_subplot(gs[1, 2])

    _draw_layout(ax_orig, original, "Original Layout  (14 WS, Linear)")
    _draw_layout(ax_impr, improved,
                 "Improved Layout  (12 WS, U-Cell)",
                 show_free_space=True,
                 free_space_bounds={"x_min": 0, "x_max": 3.5,
                                    "y_min": 0, "y_max": 9})
    _draw_cycle_time_chart(ax_ct, ORIGINAL_CYCLE_TIMES, balanced_only,
                           TAKT_TIME, title="Cycle Times vs Takt Time")
    _draw_kpi_bars(ax_kpi, PAPER_RESULTS)

    ax_table.set_facecolor(COLOURS["background"])
    ax_table.axis("off")
    short_names = {
        "longest_cycle_time":     "Max Cycle (min)",
        "productivity":           "Productivity",
        "num_workstations":       "Workstations",
        "num_operators":          "Operators",
        "wip_inventory":          "WIP (%)",
        "floor_space":            "Floor Space (m2)",
        "material_workflow":      "Workflow (UL.m)",
        "travel_distance":        "Travel Dist (m)",
        "material_handling_cost": "MH Cost (%)",
        "labour_cost":            "Labour Cost (%)",
    }
    table_rows = []
    for key, vals in PAPER_RESULTS.items():
        sign = "+" if vals["change_pct"] > 0 else ""
        table_rows.append([
            short_names.get(key, key),
            str(vals["original"]),
            str(vals["improved"]),
            f"{sign}{vals['change_pct']}%",
        ])

    tbl = ax_table.table(
        cellText=table_rows,
        colLabels=["KPI", "Orig.", "Impr.", "Delta"],
        cellLoc="center", loc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(7.5)
    tbl.scale(1, 1.4)
    for (row, col), cell in tbl.get_celld().items():
        cell.set_facecolor(COLOURS["background"] if row % 2 == 0
                           else COLOURS["grid"])
        cell.set_text_props(color=COLOURS["text"])
        cell.set_edgecolor(COLOURS["grid"])
        if row == 0:
            cell.set_facecolor("#16213e")
            cell.set_text_props(color=COLOURS["takt"], fontweight="bold")

    ax_table.set_title("Paper Results (Table 3)", color=COLOURS["text"],
                       fontsize=9, fontweight="bold")

    fig.savefig(out_path, dpi=150, bbox_inches="tight",
                facecolor=COLOURS["background"])
    plt.close(fig)
    print(f"  Layout comparison saved -> {out_path}")
    return out_path


def render_animation(output_dir="outputs", scenario="improved", n_frames=80):
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"animation_{scenario}.gif")

    network  = (build_improved_scenario() if scenario == "improved"
                else build_original_scenario())
    stations = network.active_stations
    waypoints = [(ws.x, ws.y) for ws in stations]

    fig, ax = plt.subplots(figsize=(10, 7),
                           facecolor=COLOURS["background"])
    _draw_layout(
        ax, network,
        f"Product Flow Animation - {network.name} Layout",
        show_free_space=(scenario == "improved"),
        free_space_bounds={"x_min": 0, "x_max": 3.5, "y_min": 0, "y_max": 9},
    )

    token,     = ax.plot([], [], "o", color=COLOURS["product"],
                         markersize=14, zorder=10)
    trail,     = ax.plot([], [], "-", color=COLOURS["product"],
                         linewidth=2, alpha=0.4, zorder=9)
    info_text  = ax.text(0.02, 0.97, "", transform=ax.transAxes,
                         color=COLOURS["text"], fontsize=8, va="top",
                         bbox=dict(boxstyle="round",
                                   facecolor=COLOURS["grid"], alpha=0.6))

    frames_per_seg = max(1, n_frames // max(len(waypoints) - 1, 1))
    positions = []
    for k in range(len(waypoints) - 1):
        x0, y0 = waypoints[k]
        x1, y1 = waypoints[k + 1]
        for f in range(frames_per_seg):
            t = f / frames_per_seg
            positions.append((x0 + t*(x1-x0), y0 + t*(y1-y0), k))
    positions.append((*waypoints[-1], len(waypoints)-1))

    trail_xs, trail_ys = [], []

    def update(frame_idx):
        if frame_idx >= len(positions):
            return token, trail, info_text
        px, py, ws_idx = positions[frame_idx]
        token.set_data([px], [py])
        trail_xs.append(px)
        trail_ys.append(py)
        trail.set_data(trail_xs[-30:], trail_ys[-30:])
        ws = stations[min(ws_idx, len(stations)-1)]
        info_text.set_text(
            f"Station: {ws.name}\n"
            f"Cycle time: {ws.cycle_time:.1f} min\n"
            f"Takt time: {TAKT_TIME} min"
        )
        return token, trail, info_text

    ani = FuncAnimation(fig, update, frames=len(positions),
                        interval=60, blit=True)
    ani.save(out_path, writer=PillowWriter(fps=16), dpi=100)
    plt.close(fig)
    print(f"  Animation saved -> {out_path}")
    return out_path
