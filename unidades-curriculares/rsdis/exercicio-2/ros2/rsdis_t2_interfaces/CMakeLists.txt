cmake_minimum_required(VERSION 3.8)
project(rsdis_t2_interfaces)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Radiation.msg"
  "msg/SensorData.msg"
  "srv/R2D.srv"
  "srv/D2R.srv"
  "srv/G2ECEF.srv"
  "srv/ECEF2G.srv"
  DEPENDENCIES
    std_msgs
    sensor_msgs
)

ament_export_dependencies(rosidl_default_runtime)

ament_package()
