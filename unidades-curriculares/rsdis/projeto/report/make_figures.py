"""Figures from retained observations; map geometry is explicitly illustrative."""

import argparse
import csv
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle

ROOT = Path(__file__).resolve().parent


def architecture():
    fig, ax = plt.subplots(figsize=(3.5, 2.4))
    ax.set(xlim=(0, 10), ylim=(0, 7))
    ax.axis("off")
    boxes = [
        (0.3, 5.3, "Gazebo Harmonic\nphysics, RGB, lidar, odometry"),
        (5.3, 5.3, "Adapted Space ROS plugins\nbattery and rendered solar"),
        (0.3, 2.8, "Per-rover ROS nodes\ndetector, agent, power governor"),
        (5.3, 2.8, "Mission gateway\ndelay, loss, retries and expiry"),
        (0.3, 0.3, "Operator and observers\nconsole, audit, recording"),
        (5.3, 0.3, "Coordinator\nallocation and leases\naccepted mission state"),
    ]
    for i, (x, y, text) in enumerate(boxes):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                4.3,
                1.2,
                boxstyle="round,pad=0.08",
                facecolor="#eef2f6" if i in (0, 1) else "#fff",
                edgecolor="#263e53",
                linewidth=1,
            )
        )
        ax.text(x + 2.15, y + 0.6, text, ha="center", va="center", fontsize=6)
    for a, b in [
        ((2.45, 5.25), (2.45, 4.08)),
        ((7.45, 5.25), (3.1, 4.08)),
        ((4.7, 3.4), (5.1, 3.4)),
        ((7.45, 2.65), (7.45, 1.65)),
        ((5.1, 0.9), (4.7, 0.9)),
        ((2.45, 2.65), (2.45, 1.65)),
    ]:
        ax.annotate("", b, a, arrowprops=dict(arrowstyle="<->", color="#263e53", lw=1))
    ax.text(2.45, 4.65, "ros_gz", fontsize=6, ha="center", backgroundcolor="white")
    ax.text(7.55, 2.05, "typed\nmessages", fontsize=5.5)
    fig.tight_layout(pad=0.1)
    fig.savefig(ROOT / "figures/architecture.pdf", bbox_inches="tight")
    fig.savefig(ROOT / "figures/architecture.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def power(directory):
    fig, axes = plt.subplots(2, 1, figsize=(3.5, 2.2), sharex=True, layout="constrained")
    for i, path in enumerate(sorted(directory.glob("rover*_power.csv"))):
        with path.open() as f:
            rows = list(csv.DictReader(f))
        t = [float(r["time"]) for r in rows]
        colour = ("#246293", "#b57213")[i]
        axes[0].plot(t, [100 * float(r["soc"]) for r in rows], label=f"Rover {i + 1}", color=colour)
        axes[1].plot(t, [float(r["solar_w"]) for r in rows], color=colour)
    axes[0].set(ylabel="State of charge (%)")
    axes[0].legend(frameon=False, fontsize=6, ncol=2, loc="upper left")
    axes[1].set(ylabel="Solar supply (W)", xlabel="Gazebo world time (s)")
    for ax in axes:
        ax.grid(alpha=0.2)
        ax.tick_params(labelsize=6)
        ax.xaxis.label.set_size(7)
        ax.yaxis.label.set_size(7)
    fig.savefig(ROOT / "figures/native_power.pdf", bbox_inches="tight")
    fig.savefig(ROOT / "figures/native_power.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def map_figure():
    import json
    import sys

    sys.path.insert(0, str(ROOT.parent / "src/rsdis_lunar"))
    from rsdis_lunar.planning import plan_path

    config = json.loads((ROOT.parent / "src/rsdis_lunar/config/mission.json").read_text())
    fig, ax = plt.subplots(figsize=(3.5, 2.7), layout="constrained")
    obstacles = [(*h["position"], h["radius"]) for h in config["hazards"]]
    for h in config["hazards"]:
        ax.add_patch(
            Circle(
                h["position"],
                h["radius"],
                facecolor="#84909a" if h["id"].startswith("ridge_") else "#d0cbc1",
                edgecolor="#555",
                lw=0.35,
            )
        )
    for t in config["targets"]:
        ax.scatter(*t["position"], s=12, c=[t["colour"][:3]], edgecolor="#555", lw=0.2, zorder=5)
        ax.annotate(t["id"], t["position"], xytext=(3, 4), textcoords="offset points", fontsize=5.5)
    obstacles += [(*t["position"], config["marker_diameter"] / 2 + 0.25) for t in config["targets"]]
    for r, c in zip(config["rovers"], ("#246293", "#b57213")):
        points = [r["spawn"][:2], *r["waypoints"], r["spawn"][:2]]
        for a, b in zip(points, points[1:]):
            route = plan_path(a, b, obstacles, clearance=1, bounds=config["map_bounds"])
            if route:
                ax.plot(*zip(*route), color=c, lw=0.65, alpha=0.8)
        ax.scatter(*points[0], s=20, marker="s", facecolor="none", edgecolor=c, linewidth=0.8)
    ax.set(
        xlim=(-40, 40), ylim=(-30, 30), aspect="equal", xlabel="World x (m)", ylabel="World y (m)"
    )
    ax.tick_params(labelsize=6)
    ax.xaxis.label.set_size(7)
    ax.yaxis.label.set_size(7)
    ax.grid(alpha=0.15)
    fig.savefig(ROOT / "figures/map.pdf", bbox_inches="tight")
    fig.savefig(ROOT / "figures/map.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--power-bench", type=Path)
    args = parser.parse_args()
    (ROOT / "figures").mkdir(exist_ok=True)
    architecture()
    map_figure()
    if args.power_bench:
        power(args.power_bench)
