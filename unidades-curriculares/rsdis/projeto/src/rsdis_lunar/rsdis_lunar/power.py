"""Power-interface contract shared by generated models and the ROS governor."""

import math

DEFAULT_POWER = dict(
    capacity_ah=0.25,
    voltage_v=24.0,
    avionics_w=10.0,
    drive_w_per_mps=100.0,
    turn_w_per_radps=15.0,
    solar_nominal_w=12.0,
    dock_w=550.0,
)


def power_config(config):
    values = {**DEFAULT_POWER, **config.get("power", {})}
    for key, value in values.items():
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"power.{key} must be finite and nonnegative")
    if not values["capacity_ah"] or not values["voltage_v"]:
        raise ValueError("Battery capacity and voltage must be positive")
    return values


def motion_load(power, speed, yaw_rate):
    return (
        power["avionics_w"]
        + power["drive_w_per_mps"] * min(1.0, abs(speed))
        + power["turn_w_per_radps"] * min(2.0, abs(yaw_rate))
    )


def dock_power(power, pose, home, speed, yaw_rate, mode, enabled=True):
    return (
        power["dock_w"]
        if enabled
        and mode in ("charging", "parked", "depleted")
        and math.dist(pose[:2], home[:2]) < 0.3
        and abs(speed) < 0.03
        and abs(yaw_rate) < 0.03
        else 0.0
    )


def energy_plugins(parent, spec, config, panel_link):
    """Use the same plugin contract in SDF models and adapted upstream URDFs."""
    from .world import element

    if config.get("energy_source") != "gazebo":
        return
    p = power_config(config)
    name = spec["id"]
    battery = element(
        parent,
        "plugin",
        filename="libRsdisRechargeableBatteryPlugin.so",
        name="simulation::RechargeableBatteryPlugin",
    )
    for key, value in {
        "battery_name": name + "_battery",
        "voltage": p["voltage_v"],
        "open_circuit_voltage_constant_coef": p["voltage_v"],
        "open_circuit_voltage_linear_coef": -2.0,
        "initial_charge": p["capacity_ah"] * spec["battery"],
        "capacity": p["capacity_ah"],
        "resistance": 0.01,
        "smooth_current_tau": 0.1,
        "power_load": p["avionics_w"],
        "power_load_topic": f"/{name}/energy/load_w",
        "start_draining": "true",
    }.items():
        element(battery, key, value)
    for source in (panel_link + "/solar_panel_output", "energy/dock_w"):
        element(battery, "power_source", source)
    solar = element(
        parent,
        "plugin",
        filename="libRsdisSolarPanelPlugin.so",
        name="simulation::SolarPanelPlugin",
    )
    element(solar, "link_name", panel_link)
    element(solar, "nominal_power", p["solar_nominal_w"])


def power_bridges(name, panel_link):
    """Return one-way bridges and clean ROS topic remappings."""
    battery = f"/model/{name}/battery/{name}_battery"
    topics = [
        (
            battery + "/state",
            f"/{name}/battery",
            "sensor_msgs/msg/BatteryState",
            "gz.msgs.BatteryState",
            "[",
        ),
        (
            battery + "/total_power_supply",
            f"/{name}/energy/supply_w",
            "std_msgs/msg/Float32",
            "gz.msgs.Float",
            "[",
        ),
        (
            battery + "/total_power_consumption",
            f"/{name}/energy/load_actual_w",
            "std_msgs/msg/Float32",
            "gz.msgs.Float",
            "[",
        ),
        (
            f"/model/{name}/{panel_link}/solar_panel_output",
            f"/{name}/energy/solar_w",
            "std_msgs/msg/Float32",
            "gz.msgs.Float",
            "[",
        ),
        (
            f"/model/{name}/energy/dock_w",
            f"/{name}/energy/dock_w",
            "std_msgs/msg/Float32",
            "gz.msgs.Float",
            "]",
        ),
        (
            f"/{name}/energy/load_w",
            f"/{name}/energy/load_w",
            "std_msgs/msg/Float32",
            "gz.msgs.Float",
            "]",
        ),
    ]
    return (
        [f"{gz}@{ros_type}{direction}{gz_type}" for gz, _, ros_type, gz_type, direction in topics],
        [(gz, ros) for gz, ros, *_ in topics if gz != ros],
    )
