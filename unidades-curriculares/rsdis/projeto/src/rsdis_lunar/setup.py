from glob import glob
from setuptools import find_packages, setup

setup(
    name="rsdis_lunar",
    version="0.1.0",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/rsdis_lunar"]),
        ("share/rsdis_lunar", ["package.xml"]),
        ("share/rsdis_lunar/launch", glob("launch/*.launch.py")),
        ("share/rsdis_lunar/config", glob("config/*.json")),
        ("share/rsdis_lunar/rviz", glob("rviz/*.rviz")),
        ("share/rsdis_lunar/web", glob("web/*.html")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="RSDIS project team",
    maintainer_email="maintainer@example.com",
    description="Cooperative lunar exploration prototype",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "rover_agent = rsdis_lunar.agent_node:main",
            "mission_manager = rsdis_lunar.coordinator_node:main",
            "target_detector = rsdis_lunar.detector_node:main",
            "mission_monitor = rsdis_lunar.monitor_node:main",
            "viper_driver = rsdis_lunar.viper_driver_node:main",
            "mission_dashboard = rsdis_lunar.dashboard_node:main",
        ]
    },
)
