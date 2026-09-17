import RosidlRuntimeLean.TypeSupport

/-!
# Messages

`RosMessage α` marks a Lean type as a ROS message with generated bindings.
The conversion functions live in C, reached through the boxed type record, so
the class carries only the name and the record.
-/

namespace RosidlRuntimeLean

/-- `α` is a ROS interface type with generated bindings. -/
class RosMessage (α : Type) where
  /-- `"std_msgs/msg/String"` -/
  typeName : String
  /-- The generated type record, boxed. -/
  typeSupport : IO MessageType

export RosMessage (typeName)

end RosidlRuntimeLean
