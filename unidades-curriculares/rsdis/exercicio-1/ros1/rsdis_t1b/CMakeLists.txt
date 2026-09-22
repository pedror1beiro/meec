cmake_minimum_required(VERSION 3.0.2)
project(rsdis_t1b)

find_package(catkin REQUIRED COMPONENTS
  roscpp
  geometry_msgs
)

catkin_package()

include_directories(
  ${catkin_INCLUDE_DIRS}
)

add_executable(talker_t1b src/talker.cpp)
target_link_libraries(talker_t1b ${catkin_LIBRARIES})

add_executable(listener_t1b src/listener.cpp)
target_link_libraries(listener_t1b ${catkin_LIBRARIES})
