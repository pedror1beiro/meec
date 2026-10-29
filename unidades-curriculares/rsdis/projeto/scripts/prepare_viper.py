#!/usr/bin/env python3
"""Prepare the real Space ROS rover assets, optionally checking Gazebo conversion."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/rsdis_lunar"))
from rsdis_lunar.common import load_config
from rsdis_lunar.viper import adapt_urdf, expand_upstream, profile
from rsdis_lunar.world import build_world


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulation", type=Path, default=ROOT / "third_party/simulation")
    parser.add_argument("--config", type=Path, default=ROOT / "src/rsdis_lunar/config/mission.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results/prepared_viper")
    parser.add_argument(
        "--validate-sdf",
        action="store_true",
        help="Use installed Gazebo to convert and parse both URDFs",
    )
    args = parser.parse_args()
    config = profile(load_config(args.config))
    expanded = expand_upstream(args.simulation)
    robots = {
        r["id"]: adapt_urdf(expanded, args.simulation, r["id"], config) for r in config["rovers"]
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "mission.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    (args.output / "world.sdf").write_text(
        build_world(config, include_rovers=False), encoding="utf-8"
    )
    report = {
        "model_profile": config["model_profile"],
        "mesh_files_materialized": True,
        "gazebo_conversion_checked": False,
        "physical_runtime_checked": False,
        "robots": {},
    }
    for name, xml in robots.items():
        file = args.output / (name + ".urdf")
        file.write_text(xml, encoding="utf-8")
        robot = ET.fromstring(xml)
        report["robots"][name] = {
            "links": len(robot.findall("link")),
            "joints": len(robot.findall("joint")),
            "plugins": len(robot.findall("gazebo/plugin")),
        }
        if args.validate_sdf:
            converted = subprocess.run(
                ["gz", "sdf", "-p", str(file.resolve())], check=True, text=True, capture_output=True
            )
            sdf = ET.fromstring(converted.stdout)
            model = sdf.find("model")
            if model is None or model.attrib.get("name") != name:
                raise RuntimeError("Gazebo conversion did not preserve the rover model")
            (args.output / (name + ".sdf")).write_text(converted.stdout, encoding="utf-8")
            report["robots"][name]["conversion_diagnostics"] = converted.stderr
    report["gazebo_conversion_checked"] = args.validate_sdf
    (args.output / "preflight.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    print("Generated files contain host-specific mesh paths. Regenerate on the Linux PC.")


if __name__ == "__main__":
    main()
