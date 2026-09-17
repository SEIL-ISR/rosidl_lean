/-!
# Type handles

Opaque handles for the records `rosidl_generator_lean` emits, one per message,
service and action type.  A handle wraps a `const *` to static storage in the
generated package, so it holds no resource and needs no teardown.

Generated code produces these through `@[extern]`; rcllean consumes them.
-/

namespace RosidlRuntimeLean

private opaque MessageTypePointed : NonemptyType

/-- A boxed `rosidl_runtime_lean_message_type_t *`. -/
def MessageType : Type := MessageTypePointed.type

instance : Nonempty MessageType := MessageTypePointed.property

private opaque ServiceTypePointed : NonemptyType

/-- A boxed `rosidl_runtime_lean_service_type_t *`. -/
def ServiceType : Type := ServiceTypePointed.type

instance : Nonempty ServiceType := ServiceTypePointed.property

private opaque ActionTypePointed : NonemptyType

/-- A boxed `rosidl_runtime_lean_action_type_t *`. -/
def ActionType : Type := ActionTypePointed.type

instance : Nonempty ActionType := ActionTypePointed.property

end RosidlRuntimeLean
