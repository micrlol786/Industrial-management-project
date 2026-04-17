"""
dashboard.py  -  KPI dashboard.
NOTE: matplotlib.use("Agg") is set in main.py before this is imported.
"""

import matplotlib.pyplot as plt
import numpy as np
import os
from src.fld.material_workflow import PAPER_RESULTS

COLOURS = {
    "background": "#1a1a2e",
    "grid":       "#16213e",
    "text":       "#eaeaea",
    "takt":       "#f5a623",
    "original":   "#e74c3c",
    "improved":   "#2ecc71",
    "neutral":    "#3498db",
    "accent":     "#9b59b6",
}


def _style_ax(ax, title):
    ax.set_facecolor(COLOURS["background"])
    ax.set_title(title, color=COLOURS["text"], fontsize=9,
                 fontweight="bold", pad=6)
    ax.tick_params(colors=COLOURS["text"], labelsize=7)
    for spine in ax.spines.values():
        spine.set_color(COLOURS["grid"])


def _productivity_gauge(ax, orig, impr, target=80):
    _style_ax(ax, "Productivity (units/shift)")
    labels = ["Original", "Improved", "Target\n(Demand)"]
    values = [orig, impr, target]
    colors = [COLOURS["original"], COLOURS["improved"], COLOURS["takt"]]
    bars = ax.bar(labels, values, color=colors, width=0.5, alpha=0.85)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.5,
                str(val), ha="center", va="bottom",
                color=COLOURS["text"], fontsize=9, fontweight="bold")
    ax.axhline(target, color=COLOURS["takt"], linewidth=1.5,
               linestyle="--", alpha=0.6)
    ax.set_ylim(0, max(values) * 1.25)
    ax.set_ylabel("units/shift", color=COLOURS["text"], fontsize=7)
    ax.grid(True, axis="y", color=COLOURS["grid"], linewidth=0.4)


def _wip_reduction(ax, wip_orig, wip_impr):
    _style_ax(ax, "WIP Inventory Reduction")
    theta = np.linspace(0, 2 * np.pi, 100)
    for val, color, label in [
        (100,     COLOURS["original"], f"Original  100%"),
        (wip_impr, COLOURS["improved"], f"Improved  {wip_impr:.0f}%"),
    ]:
        r = np.sqrt(val)
        ax.fill(r * np.cos(theta), r * np.sin(theta),
                color=color, alpha=0.35, label=label)
        ax.plot(r * np.cos(theta), r * np.sin(theta),
                color=color, linewidth=1.5)
    ax.set_aspect("equal")
    ax.set_xlim(-12, 12)
    ax.set_ylim(-12, 12)
    ax.axis("off")
    ax.legend(loc="lower center", fontsize=7,
              facecolor=COLOURS["grid"], labelcolor=COLOURS["text"])
    ax.text(0, 0, f"-{100-wip_impr:.0f}%", ha="center", va="center",
            color=COLOURS["text"], fontsize=12, fontweight="bold")


def _utilisation_chart(ax, orig_result, impr_result):
    _style_ax(ax, "Workstation Utilisation (%)")
    orig_util = orig_result.utilisation
    impr_util = impr_result.utilisation
    all_ws = sorted(set(list(orig_util.keys()) + list(impr_util.keys())))
    x, w = np.arange(len(all_ws)), 0.35
    ax.bar(x - w/2, [orig_util.get(n, 0) for n in all_ws], w,
           color=COLOURS["original"], label="Original", alpha=0.8)
    ax.bar(x + w/2, [impr_util.get(n, 0) for n in all_ws], w,
           color=COLOURS["improved"], label="Improved", alpha=0.8)
    ax.axhline(100, color=COLOURS["takt"], linewidth=1,
               linestyle="--", alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(all_ws, rotation=45, fontsize=6,
                       color=COLOURS["text"])
    ax.set_ylabel("%", color=COLOURS["text"], fontsize=7)
    ax.set_ylim(0, 115)
    ax.legend(fontsize=7, facecolor=COLOURS["grid"],
              labelcolor=COLOURS["text"])
    ax.grid(True, axis="y", color=COLOURS["grid"], linewidth=0.4)


def _lead_time_distribution(ax, orig_result, impr_result):
    _style_ax(ax, "Lead Time Distribution")
    orig_lt = [p.lead_time for p in orig_result.products if p.lead_time]
    impr_lt = [p.lead_time for p in impr_result.products if p.lead_time]
    ax.hist(orig_lt, bins=20, color=COLOURS["original"], alpha=0.65,
            label=f"Original  mean={np.mean(orig_lt):.1f}m")
    ax.hist(impr_lt, bins=20, color=COLOURS["improved"], alpha=0.65,
            label=f"Improved  mean={np.mean(impr_lt):.1f}m")
    ax.set_xlabel("Lead time [min]", color=COLOURS["text"], fontsize=7)
    ax.set_ylabel("Frequency", color=COLOURS["text"], fontsize=7)
    ax.legend(fontsize=7, facecolor=COLOURS["grid"],
              labelcolor=COLOURS["text"])
    ax.grid(True, color=COLOURS["grid"], linewidth=0.4)


def _fld_comparison_bar(ax):
    _style_ax(ax, "FLD Metrics: Workflow & Travel Distance")
    categories = ["Workflow\n(UL.m)", "Travel Dist\n(m)"]
    orig_vals  = [365, 63]
    impr_vals  = [348, 55]
    x, w = np.arange(len(categories)), 0.3
    ax.bar(x - w/2, orig_vals, w, color=COLOURS["original"],
           label="Original", alpha=0.85)
    ax.bar(x + w/2, impr_vals, w, color=COLOURS["improved"],
           label="Improved", alpha=0.85)
    for xi, (o, i) in enumerate(zip(orig_vals, impr_vals)):
        ax.text(xi - w/2, o + 2, str(o), ha="center",
                fontsize=7.5, color=COLOURS["text"])
        ax.text(xi + w/2, i + 2, str(i), ha="center",
                fontsize=7.5, color=COLOURS["text"])
    ax.set_xticks(x)
    ax.set_xticklabels(categories, color=COLOURS["text"], fontsize=8)
    ax.legend(fontsize=7, facecolor=COLOURS["grid"],
              labelcolor=COLOURS["text"])
    ax.grid(True, axis="y", color=COLOURS["grid"], linewidth=0.4)


def _throughput_over_time(ax, orig_result, impr_result):
    _style_ax(ax, "Cumulative Throughput Over Shift")
    for result, color, label in [
        (orig_result, COLOURS["original"], "Original"),
        (impr_result, COLOURS["improved"], "Improved"),
    ]:
        times = sorted([p.departure_time for p in result.products
                        if p.departure_time is not None])
        ax.plot(times, range(1, len(times)+1),
                color=color, linewidth=1.8, label=label, alpha=0.9)
    ax.axhline(80, color=COLOURS["takt"], linewidth=1.2, linestyle="--",
               alpha=0.7, label="Demand (80 u/shift)")
    ax.set_xlabel("Simulation time [min]", color=COLOURS["text"], fontsize=7)
    ax.set_ylabel("Units completed", color=COLOURS["text"], fontsize=7)
    ax.legend(fontsize=7, facecolor=COLOURS["grid"],
              labelcolor=COLOURS["text"])
    ax.grid(True, color=COLOURS["grid"], linewidth=0.4)


def _va_ratio_comparison(ax, orig_result, impr_result):
    _style_ax(ax, "Value-Added Ratio (%)")
    labels = ["Original", "Improved"]
    values = [orig_result.avg_value_added_ratio,
              impr_result.avg_value_added_ratio]
    colors = [COLOURS["original"], COLOURS["improved"]]
    bars = ax.bar(labels, values, color=colors, width=0.4, alpha=0.85)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.3,
                f"{val:.1f}%", ha="center", fontsize=9,
                color=COLOURS["text"], fontweight="bold")
    ax.set_ylim(0, 110)
    ax.set_ylabel("VA ratio (%)", color=COLOURS["text"], fontsize=7)
    ax.grid(True, axis="y", color=COLOURS["grid"], linewidth=0.4)


def render_dashboard(orig_result, impr_result, output_dir="outputs"):
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "kpi_dashboard.png")

    fig = plt.figure(figsize=(22, 15), facecolor=COLOURS["background"])
    fig.suptitle(
        "Lean + FLD Manufacturing Simulation Dashboard\n"
        "Kovacs (2020): Combined Efficiency Improvement Method",
        color=COLOURS["text"], fontsize=14, fontweight="bold",
    )

    gs = fig.add_gridspec(3, 4, hspace=0.50, wspace=0.38)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[0, 2])
    ax4 = fig.add_subplot(gs[0, 3])
    ax5 = fig.add_subplot(gs[1, 0:2])
    ax6 = fig.add_subplot(gs[1, 2:4])
    ax7 = fig.add_subplot(gs[2, 0:2])
    ax8 = fig.add_subplot(gs[2, 2])
    ax9 = fig.add_subplot(gs[2, 3])

    _productivity_gauge(ax1, orig_result.productivity, impr_result.productivity)
    _wip_reduction(ax2, 100, 64)
    _fld_comparison_bar(ax3)
    _va_ratio_comparison(ax4, orig_result, impr_result)
    _utilisation_chart(ax5, orig_result, impr_result)
    _throughput_over_time(ax6, orig_result, impr_result)
    _lead_time_distribution(ax7, orig_result, impr_result)

    # Stats text panel
    ax8.set_facecolor(COLOURS["background"])
    ax8.axis("off")
    ax8.set_title("Simulation Stats", color=COLOURS["text"],
                  fontsize=9, fontweight="bold")
    stats_text = (
        f"ORIGINAL SCENARIO\n"
        f"  Units:         {orig_result.units_completed}\n"
        f"  Avg lead time: {orig_result.avg_lead_time:.1f} min\n"
        f"  Avg WIP:       {orig_result.avg_wip:.1f} units\n"
        f"  MWF:           {orig_result.material_workflow} UL.m\n"
        f"  Travel dist:   {orig_result.travel_distance} m\n\n"
        f"IMPROVED SCENARIO\n"
        f"  Units:         {impr_result.units_completed}\n"
        f"  Avg lead time: {impr_result.avg_lead_time:.1f} min\n"
        f"  Avg WIP:       {impr_result.avg_wip:.1f} units\n"
        f"  MWF:           {impr_result.material_workflow} UL.m\n"
        f"  Travel dist:   {impr_result.travel_distance} m"
    )
    ax8.text(0.05, 0.95, stats_text, transform=ax8.transAxes,
             color=COLOURS["text"], fontsize=7.5, va="top",
             fontfamily="monospace",
             bbox=dict(boxstyle="round", facecolor=COLOURS["grid"],
                       alpha=0.5))

    # Lean tools panel
    ax9.set_facecolor(COLOURS["background"])
    ax9.axis("off")
    ax9.set_title("13 Lean Tools Applied", color=COLOURS["text"],
                  fontsize=9, fontweight="bold")
    tools = [
        "  Value Stream Mapping",
        "  Takt-Time Analysis",
        "  Line Balancing",
        "  Cellular Design (U-cell)",
        "  5S",
        "  Workplace Ergonomics",
        "  Pull System",
        "  Just In Time (JIT)",
        "  Kanban",
        "  Supermarket",
        "  One-piece Flow",
        "  Visual Management",
        "  Standardisation",
        "+ FLD Optimisation",
    ]
    ax9.text(0.05, 0.97, "\n".join(tools), transform=ax9.transAxes,
             color=COLOURS["text"], fontsize=7.5, va="top",
             bbox=dict(boxstyle="round", facecolor=COLOURS["grid"],
                       alpha=0.5))

    fig.savefig(out_path, dpi=150, bbox_inches="tight",
                facecolor=COLOURS["background"])
    plt.close(fig)
    print(f"  Dashboard saved -> {out_path}")
    return out_path
