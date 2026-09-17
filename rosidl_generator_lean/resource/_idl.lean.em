-- generated from rosidl_generator_lean/resource/_idl.lean.em
-- with input from @(package_name):@(interface_path)
-- generated code does not contain a copyright notice
@
@#######################################################################
@# EmPy template for generating <PascalPkg>/<Sub>/<Name>.lean files
@#
@# Context:
@#  - package_name (string)
@#  - interface_path (Path relative to the directory named after the package)
@#  - content (IdlContent, list of elements, e.g. Messages or Services)
@#######################################################################
@{
from rosidl_generator_lean.generate_lean_impl import file_module_name
from rosidl_generator_lean.generate_lean_impl import has_byte_arrays
from rosidl_generator_lean.generate_lean_impl import imported_modules
from rosidl_generator_lean.generate_lean_impl import lean_namespace
from rosidl_parser.definition import Action
from rosidl_parser.definition import Message
from rosidl_parser.definition import Service

module = file_module_name(package_name, interface_path)
namespace = lean_namespace(package_name, interface_path)
byte_arrays = has_byte_arrays(content)
}@
import RosidlRuntimeLean
@[for imported_module in imported_modules(content, module)]@
import @(imported_module)
@[end for]@

namespace @(namespace)
@[if byte_arrays]@

-- Core has no `Repr ByteArray`.  Local, so importing two generated modules
-- does not bring two instances into scope.
local instance instReprByteArray@(interface_path.stem) : Repr _root_.ByteArray where
  reprPrec b p := reprPrec b.toList p
@[end if]@
@
@#######################################################################
@# Handle messages
@#######################################################################
@[for message in content.get_elements_of_type(Message)]@
@{
TEMPLATE(
    '_msg.lean.em',
    package_name=package_name, interface_path=interface_path, message=message)
}@
@[end for]@
@
@#######################################################################
@# Handle services
@#######################################################################
@[for service in content.get_elements_of_type(Service)]@
@{
TEMPLATE(
    '_srv.lean.em',
    package_name=package_name, interface_path=interface_path, service=service)
}@
@[end for]@
@
@#######################################################################
@# Handle actions
@#######################################################################
@[for action in content.get_elements_of_type(Action)]@
@{
TEMPLATE(
    '_action.lean.em',
    package_name=package_name, interface_path=interface_path, action=action)
}@
@[end for]@

end @(namespace)
