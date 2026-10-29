FROM ros:jazzy-ros-base
SHELL ["/bin/bash", "-c"]
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-ros-gz ros-jazzy-cv-bridge python3-opencv python3-numpy \
    ros-jazzy-rosidl-default-generators ros-jazzy-visualization-msgs ros-jazzy-xacro \
    python3-colcon-common-extensions python3-pytest \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY src/ src/
RUN source /opt/ros/jazzy/setup.bash && colcon build
COPY docker/entrypoint.sh /rsdis-entrypoint.sh
ENTRYPOINT ["/bin/bash", "/rsdis-entrypoint.sh"]
CMD ["ros2", "launch", "rsdis_lunar", "prototype.launch.py", "headless:=true"]
