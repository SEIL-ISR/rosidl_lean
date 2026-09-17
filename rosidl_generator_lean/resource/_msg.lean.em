@# Included from rosidl_generator_lean/resource/_idl.lean.em
@{
from rosidl_generator_lean.generate_lean_impl import c_accessor_name
from rosidl_generator_lean.generate_lean_impl import c_type_name
from rosidl_generator_lean.generate_lean_impl import constant_type_to_lean
from rosidl_generator_lean.generate_lean_impl import constant_value_to_lean
from rosidl_generator_lean.generate_lean_impl import escape_lean_ident
from rosidl_generator_lean.generate_lean_impl import lean_accessor_expr
from rosidl_generator_lean.generate_lean_impl import lean_accessor_type
from rosidl_generator_lean.generate_lean_impl import has_bounded_wstring
from rosidl_generator_lean.generate_lean_impl import lean_constructor_checks
from rosidl_generator_lean.generate_lean_impl import lean_constructor_signature
from rosidl_generator_lean.generate_lean_impl import lean_default
from rosidl_generator_lean.generate_lean_impl import lean_structure_literal
from rosidl_generator_lean.generate_lean_impl import lean_field_type
from rosidl_generator_lean.generate_lean_impl import members_of
from rosidl_generator_lean.generate_lean_impl import ros_interface_name
from rosidl_generator_lean.generate_lean_impl import utf16_length_name

namespaced_type = message.structure.namespaced_type
name = namespaced_type.name
ros_name = ros_interface_name(message)
c_name = c_type_name(namespaced_type)
members = members_of(message)
bounded_wstrings = has_bounded_wstring(message)
signature = lean_constructor_signature(message)
literal = lean_structure_literal(message)
checks = lean_constructor_checks(message)
}@
@[if bounded_wstrings]@

/-- UTF-16 code units of `s`, the unit rosidl bounds a `wstring` in. -/
def @(utf16_length_name(message)) (s : _root_.String) : Nat :=
  s.toList.foldl (fun n c => n + if c.val < 0x10000 then 1 else 2) 0
@[end if]@

/-- `@(ros_name)` -/
structure @(name) where
@[for member in members]@
  @(escape_lean_ident(member.name)) : @(lean_field_type(message, member.type)) := @(lean_default(message, member))
@[end for]@
deriving Repr

-- `deriving Inhabited` ignores the field defaults, and a field whose type
-- carries a bound proof has no bare default.
instance : Inhabited @(name) := ⟨{}⟩
@[if message.constants]@

namespace @(name)
@[  for constant in message.constants]@
def @(escape_lean_ident(constant.name)) : @(constant_type_to_lean(constant.type)) := @(constant_value_to_lean(constant.type, constant.value))
@[  end for]@
end @(name)
@[end if]@
@[for member in members]@

@@[export @(c_accessor_name(message, member))]
def @(name).get_@(member.name) (m : @(name)) : @(lean_accessor_type(message, member.type)) := @(lean_accessor_expr(member.type, 'm.' + escape_lean_ident(member.name)))
@[end for]@

@@[export @(c_name)__mk]
@[if checks]@
def @(name).mk'@(signature) : IO @(name) := do
@[  for line in checks]@
@(line)
@[  end for]@
  return @(literal)
@[else]@
def @(name).mk'@(signature) : IO @(name) := pure @(literal)
@[end if]@

@@[extern "@(c_name)__lean_type_support"]
opaque @(name).typeSupport : IO RosidlRuntimeLean.MessageType

instance : RosidlRuntimeLean.RosMessage @(name) := ⟨"@(ros_name)", @(name).typeSupport⟩
