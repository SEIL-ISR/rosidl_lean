# Included by rosidl_generate_interfaces() into an interface package's own
# CMake scope, once per package, through the "rosidl_generate_idl_interfaces"
# extension point.
#
# Two steps: run bin/rosidl_generator_lean over the .idl files, then build the
# Lake package it wrote.  Everything about the Lean install layout lives in
# colcon-ros-lake; this file only drives its `lake-ament-build` command.

find_package(ament_cmake_python REQUIRED)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
find_package(rcutils REQUIRED)
find_package(rosidl_runtime_c REQUIRED)
find_package(rosidl_typesupport_c REQUIRED)
find_package(rosidl_typesupport_interface REQUIRED)

find_program(_lean_ament_build lake-ament-build)
if(NOT _lean_ament_build)
  message(STATUS
    "rosidl_generator_lean: lake-ament-build (from colcon-ros-lake) is not "
    "on PATH; not generating Lean interfaces for '${PROJECT_NAME}'.")
  return()
endif()

set(_lean_runtime_dir "$ENV{AMENT_LEAN_PKG_ROSIDL_RUNTIME_LEAN}")
if(NOT _lean_runtime_dir)
  message(STATUS
    "rosidl_generator_lean: no installed rosidl_runtime_lean in the "
    "environment (AMENT_LEAN_PKG_ROSIDL_RUNTIME_LEAN is unset); not "
    "generating Lean interfaces for '${PROJECT_NAME}'.")
  return()
endif()

# snake_case to PascalCase, the module root the generator writes for a package.
# The two have to agree or the generated sources do not import.
function(_rosidl_generator_lean_pascal_case var snake)
  string(REPLACE "_" ";" _parts "${snake}")
  set(_out "")
  foreach(_part ${_parts})
    string(SUBSTRING "${_part}" 0 1 _first)
    string(TOUPPER "${_first}" _first)
    string(SUBSTRING "${_part}" 1 -1 _rest)
    string(APPEND _out "${_first}${_rest}")
  endforeach()
  set(${var} "${_out}" PARENT_SCOPE)
endfunction()

# The include directories of a set of ament packages, from their targets or
# from the classic variables their extras set.
function(_rosidl_generator_lean_include_dirs var)
  set(_dirs "")
  foreach(_pkg ${ARGN})
    foreach(_target ${${_pkg}_TARGETS})
      if(TARGET "${_target}")
        get_target_property(_inc ${_target} INTERFACE_INCLUDE_DIRECTORIES)
        if(_inc)
          list(APPEND _dirs ${_inc})
        endif()
      endif()
    endforeach()
    if(DEFINED ${_pkg}_INCLUDE_DIRS)
      list(APPEND _dirs ${${_pkg}_INCLUDE_DIRS})
    endif()
  endforeach()
  if(_dirs)
    list(REMOVE_DUPLICATES _dirs)
  endif()
  set(${var} "${_dirs}" PARENT_SCOPE)
endfunction()

_rosidl_generator_lean_pascal_case(_lean_pascal_pkg "${PROJECT_NAME}")
set(_lean_output_path
  "${CMAKE_CURRENT_BINARY_DIR}/rosidl_generator_lean/${PROJECT_NAME}")
set(_lean_build_path "${CMAKE_CURRENT_BINARY_DIR}/rosidl_generator_lean/build")
file(MAKE_DIRECTORY "${_lean_output_path}")

# What the generator will write, so the custom command has real outputs: one
# Lean module and one C file per .idl file, plus the module root and the
# lakefile.
set(_lean_generated_lean_files
  "${_lean_output_path}/${_lean_pascal_pkg}.lean"
  "${_lean_output_path}/lakefile.lean")
set(_lean_generated_c_files "")
foreach(_abs_idl_file ${rosidl_generate_interfaces_ABS_IDL_FILES})
  get_filename_component(_parent_folder "${_abs_idl_file}" DIRECTORY)
  get_filename_component(_parent_folder "${_parent_folder}" NAME)
  get_filename_component(_idl_name "${_abs_idl_file}" NAME_WE)
  string_camel_case_to_lower_case_underscore("${_idl_name}" _module_name)
  _rosidl_generator_lean_pascal_case(_lean_folder "${_parent_folder}")
  list(APPEND _lean_generated_lean_files
    "${_lean_output_path}/${_lean_pascal_pkg}/${_lean_folder}/${_idl_name}.lean")
  list(APPEND _lean_generated_c_files
    "${_lean_output_path}/${_parent_folder}/_${_module_name}_s.c")
endforeach()

set(_lean_dependency_files "")
set(_lean_dependencies "")
foreach(_pkg_name ${rosidl_generate_interfaces_DEPENDENCY_PACKAGE_NAMES})
  foreach(_idl_file ${${_pkg_name}_IDL_FILES})
    set(_abs_idl_file "${${_pkg_name}_DIR}/../${_idl_file}")
    normalize_path(_abs_idl_file "${_abs_idl_file}")
    list(APPEND _lean_dependency_files "${_abs_idl_file}")
    list(APPEND _lean_dependencies "${_pkg_name}:${_abs_idl_file}")
  endforeach()
endforeach()

set(_lean_target_dependencies
  "${rosidl_generator_lean_BIN}"
  ${rosidl_generator_lean_GENERATOR_FILES}
  "${rosidl_generator_lean_TEMPLATE_DIR}/_action.lean.em"
  "${rosidl_generator_lean_TEMPLATE_DIR}/_idl.lean.em"
  "${rosidl_generator_lean_TEMPLATE_DIR}/_idl_support.c.em"
  "${rosidl_generator_lean_TEMPLATE_DIR}/_msg.lean.em"
  "${rosidl_generator_lean_TEMPLATE_DIR}/_msg_support.c.em"
  "${rosidl_generator_lean_TEMPLATE_DIR}/_pkg.lean.em"
  "${rosidl_generator_lean_TEMPLATE_DIR}/_srv.lean.em"
  "${rosidl_generator_lean_TEMPLATE_DIR}/lakefile.lean.em"
  ${rosidl_generate_interfaces_ABS_IDL_FILES}
  ${_lean_dependency_files})
foreach(_dep ${_lean_target_dependencies})
  if(NOT EXISTS "${_dep}")
    message(FATAL_ERROR "Target dependency '${_dep}' does not exist")
  endif()
endforeach()

set(_lean_arguments_file
  "${CMAKE_CURRENT_BINARY_DIR}/rosidl_generator_lean__arguments.json")
rosidl_write_generator_arguments(
  "${_lean_arguments_file}"
  PACKAGE_NAME "${PROJECT_NAME}"
  IDL_TUPLES "${rosidl_generate_interfaces_IDL_TUPLES}"
  ROS_INTERFACE_DEPENDENCIES "${_lean_dependencies}"
  OUTPUT_DIR "${_lean_output_path}"
  TEMPLATE_DIR "${rosidl_generator_lean_TEMPLATE_DIR}"
  TARGET_DEPENDENCIES ${_lean_target_dependencies}
)

# Unlike other generators this depends on the target and not the .idl files:
# for .action files they are themselves generated, and CMake will not let
# add_custom_command() depend on files generated in another subdirectory.
add_custom_command(
  OUTPUT ${_lean_generated_lean_files} ${_lean_generated_c_files}
  COMMAND Python3::Interpreter ${rosidl_generator_lean_BIN}
  --generator-arguments-file "${_lean_arguments_file}"
  DEPENDS ${_lean_target_dependencies} ${rosidl_generate_interfaces_TARGET}
  COMMENT "Generating Lean code for ROS interfaces"
  VERBATIM
)

set(_lean_target_suffix "__lean")
add_custom_target(
  ${rosidl_generate_interfaces_TARGET}${_lean_target_suffix}_generate
  DEPENDS ${_lean_generated_lean_files} ${_lean_generated_c_files}
)

# The Lake build compiles the generated C, which includes the struct headers
# rosidl_generator_c writes into this package's build directory.
_rosidl_generator_lean_include_dirs(_lean_include_dirs
  rosidl_runtime_c rosidl_typesupport_interface rcutils
  ${rosidl_generate_interfaces_DEPENDENCY_PACKAGE_NAMES})
set(_lean_include_dirs
  "${CMAKE_CURRENT_BINARY_DIR}/rosidl_generator_c" ${_lean_include_dirs})
string(ASCII 9 _lean_tab)
string(REPLACE ";" "${_lean_tab}" _lean_include_arg "${_lean_include_dirs}")

# Interface packages this one's definitions name types from.  Only those
# installed with Lean bindings count; one built without them is skipped, and
# the bindings that need it fail to compile with the import named.
set(_lean_interface_deps "")
set(_lean_update_args "--update" "rosidl_runtime_lean")
foreach(_dep ${rosidl_generate_interfaces_DEPENDENCY_PACKAGE_NAMES})
  string(TOUPPER "${_dep}" _lean_dep_upper)
  if(NOT "$ENV{AMENT_LEAN_PKG_${_lean_dep_upper}}" STREQUAL "")
    list(APPEND _lean_interface_deps "${_dep}")
    list(APPEND _lean_update_args "--update" "${_dep}")
  endif()
endforeach()

# The toolchain is the one rosidl_runtime_lean was built with: Lean's object
# format is tied to the compiler version.
configure_file(
  "${_lean_runtime_dir}/lean-toolchain"
  "${_lean_output_path}/lean-toolchain"
  COPYONLY)

set(_lean_target "${rosidl_generate_interfaces_TARGET}${_lean_target_suffix}")
add_custom_target(${_lean_target} ALL
  COMMAND ${CMAKE_COMMAND} -E env
    "ROSIDL_LEAN_INCLUDE_DIRS=${_lean_include_arg}"
    "${_lean_ament_build}" build
    --source-dir "${_lean_output_path}"
    --build-dir "${_lean_build_path}"
    ${_lean_update_args}
  DEPENDS ${_lean_generated_lean_files} ${_lean_generated_c_files}
  COMMENT "Building Lean interfaces for '${PROJECT_NAME}' with Lake"
  VERBATIM
  USES_TERMINAL
)
# One way only: the generate step already depends on the interface target, so
# making that target depend back on the Lake build closes a cycle.  `ALL` is
# what gets the bindings built.
add_dependencies(${_lean_target}
  ${rosidl_generate_interfaces_TARGET}${_lean_target_suffix}_generate
  ${rosidl_generate_interfaces_TARGET}__rosidl_generator_c)

if(NOT rosidl_generate_interfaces_SKIP_INSTALL)
  # The stub package and the hooks are known at configure time; the archives
  # and .olean files only after the build, so those go through the tool at
  # install time.
  set(_lean_stage "${CMAKE_CURRENT_BINARY_DIR}/rosidl_generator_lean/ament")
  set(_lean_stub_args "")
  foreach(_dep rosidl_runtime_lean ${_lean_interface_deps})
    list(APPEND _lean_stub_args "--dependency" "${_dep}")
  endforeach()
  execute_process(
    COMMAND "${_lean_ament_build}" stub
      --package "${PROJECT_NAME}"
      --out "${_lean_stage}/lean"
      --toolchain "${_lean_output_path}/lean-toolchain"
      ${_lean_stub_args}
    COMMAND_ERROR_IS_FATAL ANY)
  # What `nm -u` on the archive leaves undefined beyond the Lean library:
  # the C structs, the type support handles and rcutils.
  execute_process(
    COMMAND "${_lean_ament_build}" hook
      --package "${PROJECT_NAME}"
      --library "${_lean_pascal_pkg}"
      # argparse reads a bare `-l...` as an option, so these are `=` joined.
      "--link-arg=-l${PROJECT_NAME}_lean_c"
      "--link-arg=-l${PROJECT_NAME}__rosidl_generator_c"
      "--link-arg=-l${PROJECT_NAME}__rosidl_typesupport_c"
      "--link-arg=-lrosidl_runtime_c"
      "--link-arg=-lrosidl_typesupport_c"
      "--link-arg=-lrcutils"
      --out "${_lean_stage}/ament_lean.sh"
    COMMAND_ERROR_IS_FATAL ANY)
  # Both forms of the same hook: colcon reads the .dsv, ament's shell
  # local_setup.sh reads the .sh.
  file(WRITE "${_lean_stage}/lean_path.sh"
    "ament_prepend_unique_value LEAN_PATH \"$AMENT_CURRENT_PREFIX/lib/lean\"\n")
  file(WRITE "${_lean_stage}/lean_path.dsv"
    "prepend-non-duplicate;LEAN_PATH;lib/lean\n")

  install(
    DIRECTORY "${_lean_stage}/lean/"
    DESTINATION "share/${PROJECT_NAME}/lean"
  )
  # The generated sources too, for reading and for debugging a binding.
  install(
    DIRECTORY "${_lean_output_path}/${_lean_pascal_pkg}"
    DESTINATION "share/${PROJECT_NAME}/lean"
    FILES_MATCHING PATTERN "*.lean"
  )
  install(
    FILES "${_lean_output_path}/${_lean_pascal_pkg}.lean"
    DESTINATION "share/${PROJECT_NAME}/lean"
  )
  install(CODE "
    execute_process(
      COMMAND \"${_lean_ament_build}\" install
        --package \"${PROJECT_NAME}\"
        --source-dir \"${_lean_output_path}\"
        --build-dir \"${_lean_build_path}\"
        --install-base \"\${CMAKE_INSTALL_PREFIX}\"
      COMMAND_ERROR_IS_FATAL ANY)
  ")
  ament_environment_hooks(
    "${_lean_stage}/ament_lean.sh"
    "${_lean_stage}/lean_path.sh"
    "${_lean_stage}/lean_path.dsv")
  # Marks this prefix as carrying Lean bindings, for anything enumerating them
  # through the ament index.
  ament_index_register_resource("lean_packages")
endif()
