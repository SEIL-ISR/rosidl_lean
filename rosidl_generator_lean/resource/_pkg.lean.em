-- generated from rosidl_generator_lean/resource/_pkg.lean.em
-- with input from @(package_name)
-- generated code does not contain a copyright notice
@
@#######################################################################
@# The package's module root: every interface of @(package_name) under one
@# import.  Lean takes the first LEAN_PATH entry holding a root's directory
@# and looks no further, so a package gets a root of its own.
@#
@# Context:
@#  - package_name (string)
@#  - modules (list of module names)
@#######################################################################
@[for module in modules]@
import @(module)
@[end for]@
