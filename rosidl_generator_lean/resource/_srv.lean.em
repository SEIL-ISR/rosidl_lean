@# Included from rosidl_generator_lean/resource/_idl.lean.em
@{
from rosidl_generator_lean.generate_lean_impl import c_type_name
from rosidl_generator_lean.generate_lean_impl import lean_type_name

TEMPLATE(
    '_msg.lean.em',
    package_name=package_name, interface_path=interface_path,
    message=service.request_message)
TEMPLATE(
    '_msg.lean.em',
    package_name=package_name, interface_path=interface_path,
    message=service.response_message)
TEMPLATE(
    '_msg.lean.em',
    package_name=package_name, interface_path=interface_path,
    message=service.event_message)

name = service.namespaced_type.name
ros_name = '/'.join(service.namespaced_type.namespaced_name())
c_name = c_type_name(service.namespaced_type)
request = service.request_message.structure.namespaced_type.name
response = service.response_message.structure.namespaced_type.name
}@

/-- `@(ros_name)`.  A service carries no value of its own; this marker names
the request and response types and the generated record. -/
structure @(name) where
deriving Repr

instance : Inhabited @(name) := ⟨{}⟩

@@[extern "@(c_name)__lean_type_support"]
opaque @(name).typeSupport : IO RosidlRuntimeLean.ServiceType

instance : RosidlRuntimeLean.RosService @(name) where
  serviceName := "@(ros_name)"
  Request := @(request)
  Response := @(response)
  typeSupport := @(name).typeSupport
