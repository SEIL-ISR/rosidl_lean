@# Included from rosidl_generator_lean/resource/_idl_support.c.em
@{
from rosidl_generator_lean.generate_lean_impl import c_accessor_name
from rosidl_generator_lean.generate_lean_impl import c_constructor_args
from rosidl_generator_lean.generate_lean_impl import c_from_lean_lines
from rosidl_generator_lean.generate_lean_impl import c_nested_declarations
from rosidl_generator_lean.generate_lean_impl import c_self_type
from rosidl_generator_lean.generate_lean_impl import c_to_lean_lines
from rosidl_generator_lean.generate_lean_impl import c_type_name
from rosidl_generator_lean.generate_lean_impl import lean_c_type
from rosidl_generator_lean.generate_lean_impl import members_of

namespaced_type = message.structure.namespaced_type
c_name = c_type_name(namespaced_type)
type_support_args = ', '.join(namespaced_type.namespaced_name())
members = members_of(message)
constructor_args = c_constructor_args(message)
nested = c_nested_declarations(message, declared)
self_type = c_self_type(message)
}@
@[if nested]@

// Nested types, converted through their own package's generated code
@[  for nested_name in nested]@
bool @(nested_name)__from_lean(b_lean_obj_arg lean_message, void * ros_message);
lean_obj_res @(nested_name)__to_lean(const void * ros_message);
@[  end for]@
@[end if]@

// Exported by the Lean module of @('/'.join(namespaced_type.namespaced_name()))
@[for member in members]@
@(lean_c_type(message, member.type)) @(c_accessor_name(message, member))(@(self_type));
@[end for]@
lean_object * @(c_name)__mk(@(constructor_args));

bool @(c_name)__from_lean(b_lean_obj_arg lean_message, void * ros_message_void)
{
  @(c_name) * ros_message = (@(c_name) *)ros_message_void;
@[for line in c_from_lean_lines(message)]@
@(line)
@[end for]@
  return true;
}

lean_obj_res @(c_name)__to_lean(const void * ros_message_void)
{
  const @(c_name) * ros_message = (const @(c_name) *)ros_message_void;
@[for line in c_to_lean_lines(message)]@
@(line)
@[end for]@
}

static bool @(c_name)__lean_init(void * ros_message)
{
  return @(c_name)__init((@(c_name) *)ros_message);
}

static void @(c_name)__lean_fini(void * ros_message)
{
  @(c_name)__fini((@(c_name) *)ros_message);
}

static rosidl_runtime_lean_message_type_t @(c_name)__lean_record = {
  ROSIDL_RUNTIME_LEAN_MESSAGE_MAGIC,
  NULL,
  sizeof(@(c_name)),
  @(c_name)__lean_init,
  @(c_name)__lean_fini,
  @(c_name)__from_lean,
  @(c_name)__to_lean
};

// The type support handle comes from a function call, so it is no constant
// initialiser; it is written on every use, always with the same value.
static const rosidl_runtime_lean_message_type_t * @(c_name)__lean_bind(void)
{
  @(c_name)__lean_record.type_support =
    ROSIDL_GET_MSG_TYPE_SUPPORT(@(type_support_args));
  return &@(c_name)__lean_record;
}

LEAN_EXPORT lean_object * @(c_name)__lean_type_support(void)
{
  return lean_io_result_mk_ok(
    rosidl_runtime_lean_box_message_type(@(c_name)__lean_bind()));
}
