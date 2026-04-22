cmake_minimum_required(VERSION 3.8)
project(mensabot_hardware)

# =========================
# Dependencies zuerst!
# =========================
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(pluginlib REQUIRED)

# =========================
# Compiler Optionen
# =========================
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# =========================
# Include Pfad
# =========================
include_directories(include)

# =========================
# Library
# =========================
add_library(mensabot_hardware SHARED
  src/mensabot_hardware.cpp
)

ament_target_dependencies(mensabot_hardware
  rclcpp
  hardware_interface
  pluginlib
)

# =========================
# Plugin export
# =========================
pluginlib_export_plugin_description_file(hardware_interface plugin.xml)

# =========================
# Install
# =========================
install(TARGETS mensabot_hardware
  DESTINATION lib
)

install(DIRECTORY include/
  DESTINATION include/
)

install(FILES plugin.xml
  DESTINATION share/${PROJECT_NAME}
)

# =========================
# Testing (optional)
# =========================
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

# =========================
# Finalize
# =========================
ament_package()