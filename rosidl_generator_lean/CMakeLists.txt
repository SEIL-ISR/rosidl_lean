cmake_minimum_required(VERSION 3.12)
project(rosidl_generator_lean NONE)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# The entry point for `rosidl_cli generate -t lean` comes from setup.cfg, which
# ament_python_install_package turns into the installed egg-info.
ament_python_install_package(${PROJECT_NAME})

# rosidl_core_generators enumerates this resource and find_package()s each name
# it finds, so an interface package picks this generator up without naming it.
# The file is empty; only its name matters.
ament_index_register_resource("rosidl_generator_packages")

install(
  PROGRAMS bin/rosidl_generator_lean
  DESTINATION lib/${PROJECT_NAME}
)
install(
  FILES cmake/rosidl_generator_lean_generate_interfaces.cmake
  DESTINATION share/${PROJECT_NAME}/cmake
)
install(
  DIRECTORY resource
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(generator test)
endif()

ament_package(
  CONFIG_EXTRAS
    "cmake/register_lean.cmake"
    "cmake/rosidl_generator_lean-extras.cmake.in"
)
