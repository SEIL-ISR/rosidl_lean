// The ABI between generated interface bindings and rcllean.  A generated
// package defines one static record per message, service and action type and
// hands Lean a boxed pointer to it; rcllean unboxes the pointer and calls
// through the function pointers.  Header-only; nothing links against this
// package.

#ifndef ROSIDL_RUNTIME_LEAN__TYPE_SUPPORT_H_
#define ROSIDL_RUNTIME_LEAN__TYPE_SUPPORT_H_

#include <lean/lean.h>

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include <rosidl_runtime_c/action_type_support_struct.h>
#include <rosidl_runtime_c/message_type_support_struct.h>
#include <rosidl_runtime_c/service_type_support_struct.h>

// Tags in the first word of each record.  A consumer checks the tag before
// trusting the pointer it unboxed.
#define ROSIDL_RUNTIME_LEAN_MESSAGE_MAGIC 0x524c4d53u  // "RLMS"
#define ROSIDL_RUNTIME_LEAN_SERVICE_MAGIC 0x524c5356u  // "RLSV"
#define ROSIDL_RUNTIME_LEAN_ACTION_MAGIC 0x524c4143u   // "RLAC"

// One generated record per message type.  Generated code builds one static
// instance and hands Lean a boxed pointer to it; rcllean reads it back.
//
// `init` and `fini` are the interface package's own C functions.  `from_lean`
// fills a ros_message the caller has already `init`ed, and returns false only
// on allocation failure.  `to_lean` returns a Lean IO result, `ok(value)` or
// `error`, so a wire value violating a field's bound raises a Lean exception
// instead of crashing.
typedef struct rosidl_runtime_lean_message_type_s {
  uint32_t magic;  // ROSIDL_RUNTIME_LEAN_MESSAGE_MAGIC
  const rosidl_message_type_support_t *type_support;
  size_t size;                      // sizeof the C struct
  bool (*init)(void *ros_message);  // <pkg>__msg__<Msg>__init
  void (*fini)(void *ros_message);  // <pkg>__msg__<Msg>__fini
  bool (*from_lean)(b_lean_obj_arg lean_message, void *ros_message);
  lean_obj_res (*to_lean)(const void *ros_message);
} rosidl_runtime_lean_message_type_t;

// One generated record per service type.  `request` and `response` point at
// the records of the two generated message types.
typedef struct rosidl_runtime_lean_service_type_s {
  uint32_t magic;  // ROSIDL_RUNTIME_LEAN_SERVICE_MAGIC
  const rosidl_service_type_support_t *type_support;
  const rosidl_runtime_lean_message_type_t *request;
  const rosidl_runtime_lean_message_type_t *response;
} rosidl_runtime_lean_service_type_t;

// One generated record per action type.  An action is three services and two
// topics, so it carries eight message records: the three payloads written
// against directly, and the five protocol wrappers.
typedef struct rosidl_runtime_lean_action_type_s {
  uint32_t magic;  // ROSIDL_RUNTIME_LEAN_ACTION_MAGIC
  const rosidl_action_type_support_t *type_support;
  const rosidl_runtime_lean_message_type_t *goal;
  const rosidl_runtime_lean_message_type_t *result;
  const rosidl_runtime_lean_message_type_t *feedback;
  const rosidl_runtime_lean_message_type_t *send_goal_request;
  const rosidl_runtime_lean_message_type_t *send_goal_response;
  const rosidl_runtime_lean_message_type_t *get_result_request;
  const rosidl_runtime_lean_message_type_t *get_result_response;
  const rosidl_runtime_lean_message_type_t *feedback_message;
} rosidl_runtime_lean_action_type_t;

// The records are static storage owned by the generated package, so the boxed
// object owns nothing: the finalizer and the foreach both do nothing.
static inline void rosidl_runtime_lean_finalize(void *data) { (void)data; }

static inline void rosidl_runtime_lean_foreach(void *data, b_lean_obj_arg fn) {
  (void)data;
  (void)fn;
}

// The class is registered once per translation unit, so a record boxed in the
// generated package and one boxed in rcllean carry different class pointers.
// Class identity says nothing; check the magic field instead.
static inline lean_external_class *rosidl_runtime_lean_class(void) {
  static lean_external_class *cls = NULL;
  if (cls == NULL) {
    cls = lean_register_external_class(rosidl_runtime_lean_finalize,
                                       rosidl_runtime_lean_foreach);
  }
  return cls;
}

static inline lean_obj_res rosidl_runtime_lean_box_message_type(
    const rosidl_runtime_lean_message_type_t *type) {
  return lean_alloc_external(rosidl_runtime_lean_class(), (void *)type);
}

static inline lean_obj_res rosidl_runtime_lean_box_service_type(
    const rosidl_runtime_lean_service_type_t *type) {
  return lean_alloc_external(rosidl_runtime_lean_class(), (void *)type);
}

static inline lean_obj_res rosidl_runtime_lean_box_action_type(
    const rosidl_runtime_lean_action_type_t *type) {
  return lean_alloc_external(rosidl_runtime_lean_class(), (void *)type);
}

// Unboxing: NULL when the object does not carry a record of that kind.
static inline const rosidl_runtime_lean_message_type_t *
rosidl_runtime_lean_message_type_of(b_lean_obj_arg obj) {
  const rosidl_runtime_lean_message_type_t *type =
      (const rosidl_runtime_lean_message_type_t *)lean_get_external_data(obj);
  if (type == NULL || type->magic != ROSIDL_RUNTIME_LEAN_MESSAGE_MAGIC) {
    return NULL;
  }
  return type;
}

static inline const rosidl_runtime_lean_service_type_t *
rosidl_runtime_lean_service_type_of(b_lean_obj_arg obj) {
  const rosidl_runtime_lean_service_type_t *type =
      (const rosidl_runtime_lean_service_type_t *)lean_get_external_data(obj);
  if (type == NULL || type->magic != ROSIDL_RUNTIME_LEAN_SERVICE_MAGIC) {
    return NULL;
  }
  return type;
}

static inline const rosidl_runtime_lean_action_type_t *
rosidl_runtime_lean_action_type_of(b_lean_obj_arg obj) {
  const rosidl_runtime_lean_action_type_t *type =
      (const rosidl_runtime_lean_action_type_t *)lean_get_external_data(obj);
  if (type == NULL || type->magic != ROSIDL_RUNTIME_LEAN_ACTION_MAGIC) {
    return NULL;
  }
  return type;
}

#endif  // ROSIDL_RUNTIME_LEAN__TYPE_SUPPORT_H_
