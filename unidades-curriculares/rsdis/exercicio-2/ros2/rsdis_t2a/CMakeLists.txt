cmake_minimum_required(VERSION 3.8)
project(rsdis_t2a)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(rsdis_t2_interfaces REQUIRED)

add_executable(talker_t2a src/talker.cpp)

ament_target_dependencies(talker_t2a
  rclcpp
  sensor_msgs
  rsdis_t2_interfaces
)

install(TARGETS
  talker_t2a
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
