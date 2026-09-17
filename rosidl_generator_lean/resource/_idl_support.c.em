// generated from rosidl_generator_lean/resource/_idl_support.c.em
// with input from @(package_name):@(interface_path)
// generated code does not contain a copyright notice
@
@#######################################################################
@# EmPy template for generating _<idl>_s.c files
@#
@# One static record per message, service and action type, wired to the
@# rosidl C functions and to the accessors the Lean module exports.
@#
@# Context:
@#  - package_name (string)
@#  - interface_path (Path relative to the directory named after the package)
@#  - content (IdlContent, list of elements, e.g. Messages or Services)
@#######################################################################
@{
from rosidl_generator_lean.generate_lean_impl import c_include_base
from rosidl_generator_lean.generate_lean_impl import c_nested_headers
from rosidl_generator_lean.generate_lean_impl import c_sequence_headers
from rosidl_generator_lean.generate_lean_impl import c_type_name
from rosidl_generator_lean.generate_lean_impl import has_wstrings
from rosidl_generator_lean.generate_lean_impl import messages_of
from rosidl_parser.definition import Action
from rosidl_parser.definition import Service

messages = messages_of(content)
include_base = c_include_base(package_name, interface_path)
wstrings = has_wstrings(content)
headers = c_sequence_headers(content)
nested_headers = c_nested_headers(content, include_base)
declared = set()
}@

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include <lean/lean.h>

#include "rosidl_runtime_lean/type_support.h"

#include "@(include_base)__struct.h"
#include "@(include_base)__functions.h"
#include "@(include_base)__type_support.h"
@[for header in headers]@
#include "@(header)"
@[end for]@
@[if nested_headers]@

// Nested types, for their sequence functions
@[  for header in nested_headers]@
#include "@(header)"
@[  end for]@
@[end if]@
@[if wstrings]@

// rosidl stores a wstring as UTF-16; Lean hands over UTF-8.  The two helpers
// below are the whole conversion, and only appear in files that need them.
static bool rosidl_generator_lean__assign_u16string(
  rosidl_runtime_c__U16String * str, const char * utf8, size_t size)
{
  // Worst case one code unit per input byte, plus the terminator.
  uint16_t * buffer = (uint16_t *)malloc((size + 1) * sizeof(uint16_t));
  if (!buffer) {
    return false;
  }
  size_t length = 0;
  size_t i = 0;
  while (i < size) {
    unsigned char lead = (unsigned char)utf8[i];
    uint32_t code;
    size_t extra;
    if (lead < 0x80u) {
      code = lead;
      extra = 0;
    } else if ((lead & 0xe0u) == 0xc0u) {
      code = lead & 0x1fu;
      extra = 1;
    } else if ((lead & 0xf0u) == 0xe0u) {
      code = lead & 0x0fu;
      extra = 2;
    } else {
      code = lead & 0x07u;
      extra = 3;
    }
    ++i;
    while (extra > 0 && i < size) {
      code = (code << 6) | ((unsigned char)utf8[i] & 0x3fu);
      ++i;
      --extra;
    }
    if (code >= 0x10000u) {
      code -= 0x10000u;
      buffer[length++] = (uint16_t)(0xd800u + (code >> 10));
      buffer[length++] = (uint16_t)(0xdc00u + (code & 0x3ffu));
    } else {
      buffer[length++] = (uint16_t)code;
    }
  }
  buffer[length] = 0;
  bool ok = rosidl_runtime_c__U16String__assignn(str, buffer, length);
  free(buffer);
  return ok;
}

static lean_obj_res rosidl_generator_lean__u16string_to_lean(
  const rosidl_runtime_c__U16String * str)
{
  // Worst case three bytes per code unit; a surrogate pair costs four for two.
  char * buffer = (char *)malloc(str->size * 3 + 1);
  if (!buffer) {
    return lean_mk_string("");
  }
  size_t length = 0;
  for (size_t i = 0; i < str->size; ++i) {
    uint32_t code = str->data[i];
    if (code >= 0xd800u && code < 0xdc00u && i + 1 < str->size &&
      str->data[i + 1] >= 0xdc00u && str->data[i + 1] < 0xe000u)
    {
      ++i;
      code = 0x10000u + ((code - 0xd800u) << 10) + (str->data[i] - 0xdc00u);
    }
    if (code < 0x80u) {
      buffer[length++] = (char)code;
    } else if (code < 0x800u) {
      buffer[length++] = (char)(0xc0u | (code >> 6));
      buffer[length++] = (char)(0x80u | (code & 0x3fu));
    } else if (code < 0x10000u) {
      buffer[length++] = (char)(0xe0u | (code >> 12));
      buffer[length++] = (char)(0x80u | ((code >> 6) & 0x3fu));
      buffer[length++] = (char)(0x80u | (code & 0x3fu));
    } else {
      buffer[length++] = (char)(0xf0u | (code >> 18));
      buffer[length++] = (char)(0x80u | ((code >> 12) & 0x3fu));
      buffer[length++] = (char)(0x80u | ((code >> 6) & 0x3fu));
      buffer[length++] = (char)(0x80u | (code & 0x3fu));
    }
  }
  lean_object * result = lean_mk_string_from_bytes(buffer, length);
  free(buffer);
  return result;
}
@[end if]@
@[for message in messages]@
@{
TEMPLATE(
    '_msg_support.c.em',
    package_name=package_name, interface_path=interface_path,
    message=message, declared=declared)
}@
@[end for]@
@
@#######################################################################
@# Service records: the type support handle plus the two message records
@#######################################################################
@[for service in content.get_elements_of_type(Service)]@
@{
srv_c_name = c_type_name(service.namespaced_type)
srv_request = c_type_name(service.request_message.structure.namespaced_type)
srv_response = c_type_name(service.response_message.structure.namespaced_type)
srv_args = ', '.join(service.namespaced_type.namespaced_name())
}@

static rosidl_runtime_lean_service_type_t @(srv_c_name)__lean_record = {
  ROSIDL_RUNTIME_LEAN_SERVICE_MAGIC, NULL, NULL, NULL
};

LEAN_EXPORT lean_object * @(srv_c_name)__lean_type_support(void)
{
  @(srv_c_name)__lean_record.type_support =
    ROSIDL_GET_SRV_TYPE_SUPPORT(@(srv_args));
  @(srv_c_name)__lean_record.request = @(srv_request)__lean_bind();
  @(srv_c_name)__lean_record.response = @(srv_response)__lean_bind();
  return lean_io_result_mk_ok(
    rosidl_runtime_lean_box_service_type(&@(srv_c_name)__lean_record));
}
@[end for]@
@
@#######################################################################
@# Action records: three services and two topics, eight message records
@#######################################################################
@[for action in content.get_elements_of_type(Action)]@
@{
act_c_name = c_type_name(action.namespaced_type)
act_args = ', '.join(
    [action.namespaced_type.namespaces[0], action.namespaced_type.name])
act_members = [
    ('goal', action.goal),
    ('result', action.result),
    ('feedback', action.feedback),
    ('send_goal_request', action.send_goal_service.request_message),
    ('send_goal_response', action.send_goal_service.response_message),
    ('get_result_request', action.get_result_service.request_message),
    ('get_result_response', action.get_result_service.response_message),
    ('feedback_message', action.feedback_message),
]
}@

static rosidl_runtime_lean_action_type_t @(act_c_name)__lean_record = {
  ROSIDL_RUNTIME_LEAN_ACTION_MAGIC, NULL,
  NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
};

LEAN_EXPORT lean_object * @(act_c_name)__lean_type_support(void)
{
  @(act_c_name)__lean_record.type_support =
    ROSIDL_GET_ACTION_TYPE_SUPPORT(@(act_args));
@[  for field, message in act_members]@
  @(act_c_name)__lean_record.@(field) =
    @(c_type_name(message.structure.namespaced_type))__lean_bind();
@[  end for]@
  return lean_io_result_mk_ok(
    rosidl_runtime_lean_box_action_type(&@(act_c_name)__lean_record));
}
@[end for]@
