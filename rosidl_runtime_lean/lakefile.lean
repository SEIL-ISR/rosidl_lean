import Lake
open Lake DSL

/-! # rosidl_runtime_lean

The Lean runtime that generated interface bindings depend on.  Nothing is
compiled or linked here beyond the Lean modules, so the preamble only reads
the build directory colcon-ros-lake sets, and falls back to ordinary Lake
behaviour when that variable is absent.
-/

-- Lake configuration fields are pure, so the environment is read through an
-- `opaque` backed by an unsafe implementation.
private unsafe def envImpl (key : String) : String :=
  match unsafeBaseIO (IO.getEnv key) with
  | some v => v
  | none => ""

@[implemented_by envImpl]
opaque amentEnv (key : String) : String

def amentBuildDir : String :=
  let d := amentEnv "AMENT_LEAN_BUILD_DIR"
  if d.isEmpty then ".lake/build" else d

package rosidl_runtime_lean where
  version := v!"0.1.0"
  description := "Lean runtime for generated ROS 2 interface bindings"
  keywords := #["ros2", "rosidl", "ffi"]
  buildDir := amentBuildDir

@[default_target]
lean_lib RosidlRuntimeLean where
  srcDir := "."
  roots := #[`RosidlRuntimeLean]
  globs := #[.andSubmodules `RosidlRuntimeLean]

/-- `include/rosidl_runtime_lean/type_support.h`, installed under
`share/rosidl_runtime_lean/include/`.  A consumer reaches it relative to the
stub package colcon-ros-lake writes at `share/rosidl_runtime_lean/lean`, i.e.
`$AMENT_LEAN_PKG_ROSIDL_RUNTIME_LEAN/../include`.

The name is guillemet-quoted because `include` is a Lean keyword; the target
name is still `include`, and so is the directory it reads. -/
@[default_target]
input_dir «include»
