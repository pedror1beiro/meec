#!/usr/bin/env python3
"""Export the prior terrain map and illustrative planned routes, never fabricated run data."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/rsdis_lunar"))
from rsdis_lunar.common import load_config
from rsdis_lunar.planning import plan_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "src/rsdis_lunar/config/mission.json")
    parser.add_argument("--output", type=Path, default=ROOT / "output/map_obstacle_layout.png")
    args = parser.parse_args()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Rectangle
    from matplotlib.lines import Line2D

    config = load_config(args.config)
    fig, ax = plt.subplots(figsize=(12, 8.4), layout="constrained")
    fig.patch.set_facecolor("#f4f3ef")
    ax.set_facecolor("#e7e4dc")
    for h in config["hazards"]:
        colour = "#6c777f" if h["id"].startswith("ridge_") else "#aaa69e"
        if h["kind"] == "crater":
            colour = "#b7afa0"
        ax.add_patch(
            Circle(
                h["position"], h["radius"], facecolor=colour, edgecolor="#53534f", lw=0.7, zorder=3
            )
        )
        if h["kind"] in ("solar", "habitat"):
            ax.text(*h["position"], h["kind"], ha="center", va="center", fontsize=7, zorder=4)
        if h["id"].startswith("ridge_"):
            ax.add_patch(
                Circle(
                    h["position"],
                    h["radius"] + 1.0,
                    fill=False,
                    ls=":",
                    lw=0.6,
                    color="#6c777f",
                    alpha=0.65,
                    zorder=2,
                )
            )
    for t in config["targets"]:
        ax.scatter(
            *t["position"], s=65, c=[t["colour"][:3]], edgecolors="white", linewidth=1.2, zorder=6
        )
        ax.annotate(
            t["id"],
            t["position"],
            xytext=(6, 7),
            textcoords="offset points",
            fontsize=9,
            fontweight="bold",
            zorder=7,
        )
    obstacles = [(*h["position"], h["radius"]) for h in config["hazards"]]
    obstacles += [(*t["position"], config["marker_diameter"] / 2 + 0.25) for t in config["targets"]]
    colours = ["#2862a1", "#b76f13"]
    for i, r in enumerate(config["rovers"]):
        start = r["spawn"][:2]
        ax.add_patch(
            Rectangle(
                (start[0] - 1.2, start[1] - 1.2),
                2.4,
                2.4,
                facecolor="none",
                edgecolor=colours[i],
                lw=2,
                zorder=5,
            )
        )
        ax.text(
            start[0] - 2,
            start[1] - 2.2,
            r["id"] + " base",
            fontsize=8,
            color=colours[i],
            ha="center",
        )
        points = [start, *r["waypoints"], start]
        for k, (a, b) in enumerate(zip(points, points[1:])):
            route = plan_path(a, b, obstacles, clearance=1.0, bounds=config["map_bounds"])
            if route:
                ax.plot(
                    *zip(*route), color=colours[i], lw=1.4, alpha=0.85 if k < 3 else 0.35, zorder=4
                )
            if k < 3:
                ax.plot(
                    [a[0], b[0]],
                    [a[1], b[1]],
                    ls="--",
                    lw=0.7,
                    color=colours[i],
                    alpha=0.4,
                    zorder=1,
                )
    x0, x1, y0, y1 = config["map_bounds"]
    ax.set(
        xlim=(x0 - 1, x1 + 1),
        ylim=(y0 - 2, y1 + 2),
        xlabel="World x (m)",
        ylabel="World y (m)",
        aspect="equal",
    )
    ax.set_title(
        "Lunar outpost: rock corridors and collision-checked survey routes",
        loc="left",
        fontsize=15,
        pad=17,
    )
    ax.grid(alpha=0.16, color="#606060")
    handles = [
        Line2D([], [], color=colours[0], label="Rover 1 planned route"),
        Line2D([], [], color=colours[1], label="Rover 2 planned route"),
        Line2D([], [], color="#6c777f", marker="o", ls="", label="Added rock barrier"),
        Line2D([], [], color="#777", ls=":", label="Illustrative clearance margin"),
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=8, framealpha=0.92)
    ax.text(
        0.5,
        -0.12,
        "Layout illustration with known test geometry. Paths are planned, not a recorded mission.",
        transform=ax.transAxes,
        ha="center",
        fontsize=8,
        color="#555",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180, bbox_inches="tight")
    fig.savefig(args.output.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(args.output)


if __name__ == "__main__":
    main()
