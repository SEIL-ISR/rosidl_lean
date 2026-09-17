import RosidlRuntimeLean.Message

/-!
# Actions

An action is three services and two topics, with the goal, result and feedback
wrapped in protocol messages.  `RosAction A` names all eight payload types so
generated bindings describe an action the way they describe a service.
-/

namespace RosidlRuntimeLean

/-- `A` is a ROS action type with generated bindings.  `Goal`, `Result` and
`Feedback` are written against directly; the rest are the protocol's
wrappers. -/
class RosAction (A : Type) where
  /-- `"example_interfaces/action/Fibonacci"` -/
  actionName : String
  /-- The goal payload. -/
  Goal : Type
  /-- The result payload. -/
  Result : Type
  /-- The feedback payload. -/
  Feedback : Type
  /-- Request of the send-goal service. -/
  SendGoalRequest : Type
  /-- Response of the send-goal service. -/
  SendGoalResponse : Type
  /-- Request of the get-result service. -/
  GetResultRequest : Type
  /-- Response of the get-result service. -/
  GetResultResponse : Type
  /-- The feedback topic's message. -/
  FeedbackMessage : Type
  [goalMsg : RosMessage Goal]
  [resultMsg : RosMessage Result]
  [feedbackMsg : RosMessage Feedback]
  [sendGoalRequestMsg : RosMessage SendGoalRequest]
  [sendGoalResponseMsg : RosMessage SendGoalResponse]
  [getResultRequestMsg : RosMessage GetResultRequest]
  [getResultResponseMsg : RosMessage GetResultResponse]
  [feedbackMessageMsg : RosMessage FeedbackMessage]
  /-- The generated type record, boxed. -/
  typeSupport : IO ActionType

-- Reducibility first: registering the instance checks it, and a
-- semireducible class-typed definition warns.
attribute [instance_reducible] RosAction.goalMsg RosAction.resultMsg
  RosAction.feedbackMsg RosAction.sendGoalRequestMsg
  RosAction.sendGoalResponseMsg RosAction.getResultRequestMsg
  RosAction.getResultResponseMsg RosAction.feedbackMessageMsg
attribute [instance] RosAction.goalMsg RosAction.resultMsg
  RosAction.feedbackMsg RosAction.sendGoalRequestMsg
  RosAction.sendGoalResponseMsg RosAction.getResultRequestMsg
  RosAction.getResultResponseMsg RosAction.feedbackMessageMsg

end RosidlRuntimeLean
