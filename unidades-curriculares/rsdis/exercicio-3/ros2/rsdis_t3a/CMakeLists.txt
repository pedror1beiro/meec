cmake_minimum_required(VERSION 3.8)
project(rsdis_t3a)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

add_executable(vacuum_robot
  src/vacuum_robot.cpp
)

ament_target_dependencies(vacuum_robot
  rclcpp
  sensor_msgs
  geometry_msgs
)

install(
  TARGETS vacuum_robot
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
