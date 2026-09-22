cmake_minimum_required(VERSION 3.8)
project(rsdis_t1b)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)

add_executable(talker_t1b src/talker.cpp)
ament_target_dependencies(talker_t1b rclcpp geometry_msgs)

add_executable(listener_t1b src/listener.cpp)
ament_target_dependencies(listener_t1b rclcpp geometry_msgs)

install(TARGETS
  talker_t1b
  listener_t1b
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
