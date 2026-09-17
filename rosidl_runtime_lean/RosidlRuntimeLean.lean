import RosidlRuntimeLean.TypeSupport
import RosidlRuntimeLean.Message
import RosidlRuntimeLean.Service
import RosidlRuntimeLean.Action

/-!
# rosidl_runtime_lean

The runtime `rosidl_generator_lean`'s output depends on: the opaque handles for
the generated type records, and the classes that mark a Lean type as a ROS
message, service or action.  No `@[extern]` declarations live here; generated
code declares the ones producing handles and rcllean the ones consuming them.
-/
