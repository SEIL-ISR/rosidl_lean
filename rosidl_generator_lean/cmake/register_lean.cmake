macro(rosidl_generator_lean_extras BIN GENERATOR_FILES TEMPLATE_DIR)
  find_package(ament_cmake_core QUIET REQUIRED)
  # Make sure extension points are registered in order: the generated C reads
  # the structs rosidl_generator_c writes and the handles rosidl_typesupport_c
  # registers.
  find_package(rosidl_generator_c QUIET REQUIRED)
  find_package(rosidl_typesupport_c QUIET REQUIRED)

  ament_register_extension(
    "rosidl_generate_idl_interfaces"
    "rosidl_generator_lean"
    "rosidl_generator_lean_generate_interfaces.cmake")

  normalize_path(BIN "${BIN}")
  set(rosidl_generator_lean_BIN "${BIN}")

  set(rosidl_generator_lean_GENERATOR_FILES "")
  foreach(_generator_file ${GENERATOR_FILES})
    normalize_path(_generator_file "${_generator_file}")
    list(APPEND rosidl_generator_lean_GENERATOR_FILES "${_generator_file}")
  endforeach()

  normalize_path(TEMPLATE_DIR "${TEMPLATE_DIR}")
  set(rosidl_generator_lean_TEMPLATE_DIR "${TEMPLATE_DIR}")
endmacro()
