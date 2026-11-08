cmake_minimum_required(VERSION 3.16)
project(rsdis_energy_plugins)
find_package(ament_cmake REQUIRED)
find_package(gz_sim_vendor REQUIRED)
find_package(gz-sim REQUIRED)
find_package(gz_plugin_vendor REQUIRED)
find_package(gz-plugin REQUIRED COMPONENTS register)
find_package(gz_common_vendor REQUIRED)
find_package(gz-common REQUIRED COMPONENTS profiler)
find_package(gz_rendering_vendor REQUIRED)
find_package(gz-rendering REQUIRED)

foreach(plugin RechargeableBatteryPlugin SolarPanelPlugin)
  add_library(Rsdis${plugin} SHARED src/${plugin}.cc)
  target_compile_features(Rsdis${plugin} PRIVATE cxx_std_17)
  target_link_libraries(Rsdis${plugin} PRIVATE
    gz-sim${gz-sim_VERSION_MAJOR}::gz-sim${gz-sim_VERSION_MAJOR}
    gz-plugin${gz-plugin_VERSION_MAJOR}::gz-plugin${gz-plugin_VERSION_MAJOR}
    gz-common${gz-common_VERSION_MAJOR}::gz-common${gz-common_VERSION_MAJOR}
    gz-common${gz-common_VERSION_MAJOR}::profiler
    gz-rendering${gz-rendering_VERSION_MAJOR}::gz-rendering${gz-rendering_VERSION_MAJOR})
  install(TARGETS Rsdis${plugin} LIBRARY DESTINATION lib)
endforeach()
ament_environment_hooks(hooks/rsdis_energy_plugins.dsv.in)
install(FILES LICENSE UPSTREAM.md UPSTREAM.json DESTINATION share/${PROJECT_NAME})
ament_package()
