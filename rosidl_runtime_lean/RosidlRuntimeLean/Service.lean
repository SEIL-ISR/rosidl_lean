import RosidlRuntimeLean.Message

/-!
# Services

`RosService S` names a service's request and response types together with its
own type record.  Both payload types carry their own `RosMessage` instance.
-/

namespace RosidlRuntimeLean

/-- `S` is a ROS service type with generated bindings. -/
class RosService (S : Type) where
  /-- `"example_interfaces/srv/AddTwoInts"` -/
  serviceName : String
  /-- The request payload. -/
  Request : Type
  /-- The response payload. -/
  Response : Type
  [requestMsg : RosMessage Request]
  [responseMsg : RosMessage Response]
  /-- The generated type record, boxed. -/
  typeSupport : IO ServiceType

-- Reducibility first: registering the instance checks it, and a
-- semireducible class-typed definition warns.
attribute [instance_reducible] RosService.requestMsg RosService.responseMsg
attribute [instance] RosService.requestMsg RosService.responseMsg

end RosidlRuntimeLean
