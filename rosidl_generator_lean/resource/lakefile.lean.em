import Lake
open Lake DSL System

/-! Lake package for the generated Lean bindings of `@(package_name)`.

Written by `rosidl_generator_lean` into the interface package's build
directory.  Do not edit; regenerated on every configure.
-/
@
@#######################################################################
@# Context:
@#  - package_name (string)
@#  - root_module (string, the PascalCase module root)
@#  - dependencies (list of interface packages carrying Lean bindings)
@#######################################################################
@{
upper_names = [(dependency, dependency.upper()) for dependency in dependencies]
}@

-- Lake configuration fields are pure, so the environment is read through an
-- `opaque` backed by an unsafe implementation.
private unsafe def envImpl (key : String) : String :=
  match unsafeBaseIO (IO.getEnv key) with
  | some v => v
  | none => ""

@@[implemented_by envImpl]
opaque envVar (key : String) : String

/-- The separator inside the environment's flag lists.  A tab, since a flag may
carry a path containing spaces. -/
def amentArgSep : String := "\t"

def amentEnvList (key : String) : Array String :=
  ((envVar key).splitOn amentArgSep |>.filter (!·.isEmpty)).toArray

def amentBuildDir : String :=
  let d := envVar "AMENT_LEAN_BUILD_DIR"
  if d.isEmpty then ".lake/build" else d

/-- `-I` flags for the rosidl C headers, set by the CMake driving this build:
this package's own `rosidl_generator_c` output and every dependency's. -/
def rosidlIncludeFlags : Array String :=
  (amentEnvList "ROSIDL_LEAN_INCLUDE_DIRS").map ("-I" ++ ·)

/-- `rosidl_runtime_lean` is header-only; its header sits next to the stub
package the install wrote. -/
def runtimeLeanInclude : String :=
  envVar "AMENT_LEAN_PKG_ROSIDL_RUNTIME_LEAN" ++ "/../include"

require rosidl_runtime_lean from envVar "AMENT_LEAN_PKG_ROSIDL_RUNTIME_LEAN"
@[for dependency, upper in upper_names]@
require @(dependency) from envVar "AMENT_LEAN_PKG_@(upper)"
@[end for]@

package «@(package_name)» where
  buildDir := amentBuildDir
  extraDepTargets := #[`leanC]

/-- All interfaces of `@(package_name)` under their own module root. -/
@@[default_target]
lean_lib «@(root_module)» where
  srcDir := "."
  roots := #[`@(root_module)]
  globs := #[.andSubmodules `@(root_module)]

/-- Compile every generated `_*_s.c` and archive them into
`lib@(package_name)_lean_c.a`.  The archive holds the type records and the
conversions; the Lean library holds the accessors they call. -/
target leanC pkg : FilePath := do
  let leanInc ← getLeanIncludeDir
  let cflags := #["-fPIC", "-O2", "-std=gnu11", "-Wall", "-Wextra",
                  s!"-I{leanInc}", s!"-I{runtimeLeanInclude}"] ++
                rosidlIncludeFlags
  let mut sources : Array (String × FilePath) := #[]
  for subfolder in ["msg", "srv", "action"] do
    let dir := pkg.dir / subfolder
    if ← dir.pathExists then
      for entry in (← dir.readDir) do
        if entry.path.extension == some "c" then
          sources := sources.push (subfolder, entry.path)
  sources := sources.qsort (fun a b => a.2.toString < b.2.toString)
  let mut objects : Array (Job FilePath) := #[]
  for (subfolder, source) in sources do
    let stem := source.fileStem.getD "obj"
    let oFile := pkg.buildDir / "src" / s!"{subfolder}_{stem}.o"
    objects := objects.push (← buildO oFile (← inputTextFile source) #[] cflags "cc")
  buildStaticLib
    (pkg.staticLibDir / (nameToStaticLib "@(package_name)_lean_c")) objects
