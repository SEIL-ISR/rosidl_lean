@# Included from rosidl_generator_lean/resource/_idl.lean.em
@{
from rosidl_generator_lean.generate_lean_impl import c_type_name

TEMPLATE(
    '_msg.lean.em',
    package_name=package_name, interface_path=interface_path,
    message=action.goal)
TEMPLATE(
    '_msg.lean.em',
    package_name=package_name, interface_path=interface_path,
    message=action.result)
TEMPLATE(
    '_msg.lean.em',
    package_name=package_name, interface_path=interface_path,
    message=action.feedback)
TEMPLATE(
    '_srv.lean.em',
    package_name=package_name, interface_path=interface_path,
    service=action.send_goal_service)
TEMPLATE(
    '_srv.lean.em',
    package_name=package_name, interface_path=interface_path,
    service=action.get_result_service)
TEMPLATE(
    '_msg.lean.em',
    package_name=package_name, interface_path=interface_path,
    message=action.feedback_message)

name = action.namespaced_type.name
ros_name = '/'.join(action.namespaced_type.namespaced_name())
c_name = c_type_name(action.namespaced_type)
send_goal = action.send_goal_service
get_result = action.get_result_service
}@

/-- `@(ros_name)`.  Three services and two topics; this marker names all
eight payload types and the generated record. -/
structure @(name) where
deriving Repr

instance : Inhabited @(name) := ⟨{}⟩

@@[extern "@(c_name)__lean_type_support"]
opaque @(name).typeSupport : IO RosidlRuntimeLean.ActionType

instance : RosidlRuntimeLean.RosAction @(name) where
  actionName := "@(ros_name)"
  Goal := @(action.goal.structure.namespaced_type.name)
  Result := @(action.result.structure.namespaced_type.name)
  Feedback := @(action.feedback.structure.namespaced_type.name)
  SendGoalRequest := @(send_goal.request_message.structure.namespaced_type.name)
  SendGoalResponse := @(send_goal.response_message.structure.namespaced_type.name)
  GetResultRequest := @(get_result.request_message.structure.namespaced_type.name)
  GetResultResponse := @(get_result.response_message.structure.namespaced_type.name)
  FeedbackMessage := @(action.feedback_message.structure.namespaced_type.name)
  typeSupport := @(name).typeSupport
