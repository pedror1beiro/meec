cmake_minimum_required(VERSION 3.8)
project(rsdis_t3b)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

add_executable(explorer
  src/explorer.cpp
)

ament_target_dependencies(explorer
  rclcpp
  sensor_msgs
  geometry_msgs
)

add_executable(cylinder_detector
  src/cylinder_detector.cpp
)

ament_target_dependencies(cylinder_detector
  rclcpp
  sensor_msgs
)

install(
  TARGETS
    explorer
    cylinder_detector
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
