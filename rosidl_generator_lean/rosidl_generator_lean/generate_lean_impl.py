from ast import literal_eval
import os
import pathlib

from rosidl_parser.definition import AbstractGenericString
from rosidl_parser.definition import AbstractNestedType
from rosidl_parser.definition import AbstractSequence
from rosidl_parser.definition import AbstractString
from rosidl_parser.definition import AbstractWString
from rosidl_parser.definition import Action
from rosidl_parser.definition import Array
from rosidl_parser.definition import BasicType
from rosidl_parser.definition import BoundedSequence
from rosidl_parser.definition import BoundedString
from rosidl_parser.definition import BoundedWString
from rosidl_parser.definition import EMPTY_STRUCTURE_REQUIRED_MEMBER_NAME
from rosidl_parser.definition import FLOATING_POINT_TYPES
from rosidl_parser.definition import IdlLocator
from rosidl_parser.definition import Message
from rosidl_parser.definition import NamespacedType
from rosidl_parser.definition import Service
from rosidl_parser.parser import parse_idl_file
from rosidl_pycommon import convert_camel_case_to_lower_case_underscore
from rosidl_pycommon import expand_template
from rosidl_pycommon import generate_files
from rosidl_pycommon import get_newest_modification_time
from rosidl_pycommon import read_generator_arguments

# Scalar ROS types as Lean writes them.  Every name is `_root_`-qualified:
# interface packages define types called `String`, `Bool` and `UInt8`, so a bare
# `String` inside `StdMsgs.Msg` would be the generated message.
BASIC_IDL_TYPES_TO_LEAN = {
    'boolean': '_root_.Bool',
    'octet': '_root_.UInt8',
    'char': '_root_.UInt8',
    'wchar': '_root_.UInt16',
    'uint8': '_root_.UInt8',
    'int8': '_root_.Int8',
    'uint16': '_root_.UInt16',
    'int16': '_root_.Int16',
    'uint32': '_root_.UInt32',
    'int32': '_root_.Int32',
    'uint64': '_root_.UInt64',
    'int64': '_root_.Int64',
    'float': '_root_.Float32',
    'double': '_root_.Float',
    'long double': '_root_.Float',
}

# The C type Lean uses for each scalar at the FFI boundary.  Lean's signed
# integers are single-field structures over the unsigned ones, so they cross as
# the unsigned C type.
BASIC_IDL_TYPES_TO_LEAN_C = {
    'boolean': 'uint8_t',
    'octet': 'uint8_t',
    'char': 'uint8_t',
    'wchar': 'uint16_t',
    'uint8': 'uint8_t',
    'int8': 'uint8_t',
    'uint16': 'uint16_t',
    'int16': 'uint16_t',
    'uint32': 'uint32_t',
    'int32': 'uint32_t',
    'uint64': 'uint64_t',
    'int64': 'uint64_t',
    'float': 'float',
    'double': 'double',
    'long double': 'double',
}

# Boxing and unboxing for the same scalars, used on array elements.
BASIC_IDL_TYPES_TO_LEAN_BOX = {
    'boolean': ('lean_box((size_t)', 'lean_unbox('),
    'octet': ('lean_box((size_t)', 'lean_unbox('),
    'char': ('lean_box((size_t)', 'lean_unbox('),
    'wchar': ('lean_box((size_t)', 'lean_unbox('),
    'uint8': ('lean_box((size_t)', 'lean_unbox('),
    'int8': ('lean_box((size_t)', 'lean_unbox('),
    'uint16': ('lean_box((size_t)', 'lean_unbox('),
    'int16': ('lean_box((size_t)', 'lean_unbox('),
    'uint32': ('lean_box_uint32(', 'lean_unbox_uint32('),
    'int32': ('lean_box_uint32(', 'lean_unbox_uint32('),
    'uint64': ('lean_box_uint64(', 'lean_unbox_uint64('),
    'int64': ('lean_box_uint64(', 'lean_unbox_uint64('),
    'float': ('lean_box_float32(', 'lean_unbox_float32('),
    'double': ('lean_box_float(', 'lean_unbox_float('),
    'long double': ('lean_box_float(', 'lean_unbox_float('),
}

# Names rosidl_generator_c already defines on every message type, which a field
# of the same name would collide with at link time.
RESERVED_C_ACCESSORS = (
    'individual_type_description_source', 'type_description',
    'type_description_sources', 'type_hash',
)

# Sequences of these are carried as one `ByteArray` rather than boxed elements.
BYTE_LIKE_IDL_TYPES = ('char', 'octet', 'uint8')

# The suffixes rosidl appends to a service or action name, longest first, so a
# generated type can be traced back to the file it came from.
INTERFACE_SUFFIXES = (
    '_SendGoal_Request', '_SendGoal_Response', '_SendGoal_Event',
    '_GetResult_Request', '_GetResult_Response', '_GetResult_Event',
    '_FeedbackMessage', '_Request', '_Response', '_Event',
    '_Goal', '_Result', '_Feedback',
)

# Every identifier-shaped Lean token, which a ROS field or constant name could
# collide with.  A name that collides is guillemet-quoted rather than renamed.
# Regenerate after a toolchain bump from `Lean.Parser.getTokenTable`.
LEAN_TOKENS = frozenset([
    'Prop', 'Sort', 'StateRefT', 'Type', '_', 'abbrev', 'add_decl_doc',
    'assert_not_exists', 'assert_not_imported', 'at', 'attribute', 'aux_def',
    'axiom', 'bif', 'binder_predicate', 'break', 'builtin_cbv_simproc',
    'builtin_cbv_simproc_decl', 'builtin_dsimproc', 'builtin_dsimproc_decl',
    'builtin_grind_propagator', 'builtin_initialize', 'builtin_simproc',
    'builtin_simproc_decl', 'by', 'by_elab', 'calc', 'catch', 'cbv_eval',
    'cbv_simproc', 'cbv_simproc_decl', 'class', 'coinductive',
    'coinductive_fixpoint', 'continue', 'dbg_trace',
    'declare_bitwise_int_theorems', 'declare_bitwise_uint_theorems',
    'declare_command_config_elab', 'declare_command_config_elab_legacy',
    'declare_config_elab', 'declare_config_elab_legacy',
    'declare_core_config_elab', 'declare_eval_bin', 'declare_eval_bin_bitwise',
    'declare_eval_bin_bool_pred', 'declare_int_theorems',
    'declare_simp_like_tactic', 'declare_sint_simprocs', 'declare_syntax_cat',
    'declare_term_config_elab', 'declare_uint_simprocs',
    'declare_uint_theorems', 'decreasing_by', 'def', 'def_eval_config_item',
    'deprecated_module', 'deprecated_syntax', 'deriving', 'do',
    'docs_to_verso', 'dsimproc', 'dsimproc_decl', 'elab', 'elab_rules',
    'elab_stx_quot', 'else', 'end', 'eval_prec', 'eval_prio', 'example',
    'exists', 'export', 'extends', 'finally', 'for', 'forall', 'from', 'fun',
    'generalizing', 'grind_annotated', 'grind_pattern', 'grind_propagator',
    'have', 'haveI', 'hiding', 'idbg', 'if', 'import', 'in', 'include',
    'include_str', 'inductive', 'inductive_fixpoint', 'inferInstanceAs',
    'infix', 'infixl', 'infixr', 'init_grind_norm', 'init_quot', 'initialize',
    'instance', 'leading_parser', 'let', 'letI', 'let_delayed', 'let_expr',
    'let_fun', 'let_tmp', 'local', 'logNamedError', 'logNamedErrorAt',
    'logNamedWarning', 'logNamedWarningAt', 'macro', 'macro_rules', 'match',
    'match_expr', 'matches', 'max_prec', 'meta', 'mod_cast', 'mut', 'mutual',
    'namespace', 'nat_lit', 'no_index', 'nofun', 'nomatch', 'noncomputable',
    'nonrec', 'norm_cast_add_elim', 'notation', 'omit', 'opaque', 'open',
    'partial', 'partial_fixpoint', 'postfix', 'prefix', 'private', 'protected',
    'public', 'recommended_spelling', 'register_builtin_option',
    'register_error_explanation', 'register_grind_attr', 'register_label_attr',
    'register_linter_set', 'register_option', 'register_parser_alias',
    'register_simp_attr', 'register_sym_dsimp', 'register_sym_simp',
    'register_sym_simp_attr', 'register_tactic_tag', 'renaming', 'repeat',
    'reprove', 'return', 'run_cmd', 'run_elab', 'run_meta', 'scoped', 'seal',
    'section', 'set_library_suggestions', 'set_option', 'show',
    'show_panel_widgets', 'show_term', 'show_term_elab', 'simproc',
    'simproc_decl', 'sorry', 'structure', 'suffices', 'syntax', 'tactic_alt',
    'tactic_extension', 'tactic_name', 'tactic_tag', 'termination_by',
    'test_extern', 'then', 'theorem', 'throwError', 'throwErrorAt',
    'throwNamedError', 'throwNamedErrorAt', 'trailing_parser', 'try',
    'unif_hint', 'universe', 'unless', 'unlock_limits', 'unsafe', 'unseal',
    'until', 'using', 'variable', 'where', 'while', 'with',
    'with_annotate_term', 'with_weak_namespace', 'without_expected_type',
])


# A message with exactly one field whose runtime value is a scalar is a Lean
# trivial structure: the message IS that scalar, unboxed, wherever Lean's
# generated code names it.  The registry answers that question for any type a
# message nests, parsing the .idl file it came from on demand.
_SCALAR_MESSAGES = {}
_IDL_FILES = {}
_PARSED_FILES = set()


def reset_type_registry():
    """Forget what earlier packages taught the trivial-structure registry."""
    _SCALAR_MESSAGES.clear()
    _IDL_FILES.clear()
    _PARSED_FILES.clear()


def register_idl_files(args):
    """Record where this package's and its dependencies' .idl files live."""
    package_name = args['package_name']
    for entry in args.get('idl_tuples', []):
        base, relative = entry.rsplit(':', 1)
        path = pathlib.Path(relative)
        _IDL_FILES[(package_name, path.parent.name, path.stem)] = (
            base, relative)
    for dependency in args.get('ros_interface_dependencies', []):
        name, _, absolute = dependency.partition(':')
        path = pathlib.Path(absolute)
        _IDL_FILES[(name, path.parent.name, path.stem)] = (
            str(path.parent.parent), '%s/%s' % (path.parent.name, path.name))


def _load_idl_file(namespaced_type):
    """Classify every message of the .idl file a type came from."""
    package_name, subfolder = namespaced_type.namespaces[:2]
    stem = namespaced_type.name
    if subfolder in ('srv', 'action'):
        for suffix in INTERFACE_SUFFIXES:
            if stem.endswith(suffix) and len(stem) > len(suffix):
                stem = stem[:-len(suffix)]
                break
    key = (package_name, subfolder, stem)
    if key in _PARSED_FILES or key not in _IDL_FILES:
        return
    _PARSED_FILES.add(key)
    content = parse_idl_file(IdlLocator(*_IDL_FILES[key])).content
    for message in messages_of(content):
        name = c_type_name(message.structure.namespaced_type)
        if name not in _SCALAR_MESSAGES:
            _SCALAR_MESSAGES[name] = scalar_message_typename(message)


def scalar_message_typename(message):
    """Return the IDL scalar a message is represented by, or None."""
    members = members_of(message)
    if len(members) != 1:
        return None
    return scalar_type_typename(members[0].type)


def scalar_type_typename(type_):
    """Return the IDL scalar a field is represented by, or None."""
    if isinstance(type_, BasicType):
        return type_.typename
    if isinstance(type_, NamespacedType):
        return nested_scalar_typename(type_)
    return None


def nested_scalar_typename(namespaced_type):
    """Return the IDL scalar a nested message is represented by, or None."""
    name = c_type_name(namespaced_type)
    if name not in _SCALAR_MESSAGES:
        _load_idl_file(namespaced_type)
    return _SCALAR_MESSAGES.get(name)


def generate_lean(generator_arguments_file):
    """Generate the Lean bindings and their C support for one package."""
    args = read_generator_arguments(generator_arguments_file)
    reset_type_registry()
    register_idl_files(args)

    generated_files = generate_files(
        generator_arguments_file, {'_idl_support.c.em': '_%s_s.c'})

    package_name = args['package_name']
    output_dir = args['output_dir']
    template_dir = pathlib.Path(args['template_dir'])
    minimum_timestamp = get_newest_modification_time(args['target_dependencies'])

    modules = []
    for idl_tuple in args.get('idl_tuples', []):
        idl_parts = idl_tuple.rsplit(':', 1)
        assert len(idl_parts) == 2
        idl_rel_path = pathlib.Path(idl_parts[1])
        idl_file = parse_idl_file(IdlLocator(*idl_parts))

        module = file_module_name(package_name, idl_rel_path)
        generated_file = os.path.join(output_dir, *module.split('.')) + '.lean'
        expand_template(
            '_idl.lean.em',
            {
                'package_name': package_name,
                'interface_path': idl_rel_path,
                'content': idl_file.content,
            },
            generated_file, minimum_timestamp=minimum_timestamp,
            template_basepath=template_dir)
        generated_files.append(generated_file)
        modules.append(module)

    root_module = package_module_name(package_name)
    generated_file = os.path.join(output_dir, root_module + '.lean')
    expand_template(
        '_pkg.lean.em',
        {'package_name': package_name, 'modules': sorted(modules)},
        generated_file, minimum_timestamp=minimum_timestamp,
        template_basepath=template_dir)
    generated_files.append(generated_file)

    generated_file = os.path.join(output_dir, 'lakefile.lean')
    expand_template(
        'lakefile.lean.em',
        {
            'package_name': package_name,
            'root_module': root_module,
            'dependencies': lean_dependencies(args),
        },
        generated_file, minimum_timestamp=minimum_timestamp,
        template_basepath=template_dir)
    generated_files.append(generated_file)

    return generated_files


def lean_dependencies(args):
    """Return the interface packages this one depends on that carry Lean bindings.

    A dependency installed without them exports no `AMENT_LEAN_PKG_<DEP>`, and
    the modules that need it fail to compile with the missing import named.
    """
    packages = []
    for dependency in args.get('ros_interface_dependencies', []):
        name = dependency.split(':', 1)[0]
        if name not in packages and os.environ.get(package_env_var(name)):
            packages.append(name)
    return sorted(packages)


def package_env_var(package_name):
    """Return the name of the variable holding a package's stub directory."""
    return 'AMENT_LEAN_PKG_' + package_name.upper()


# Naming


def pascal_case(value):
    """`std_msgs` becomes `StdMsgs`."""
    return ''.join(part[:1].upper() + part[1:] for part in value.split('_'))


def package_module_name(package_name):
    """Return the Lean module root of a package, one per ROS package."""
    return pascal_case(package_name)


def file_module_name(package_name, interface_path):
    """Return the Lean module one .idl file becomes, e.g. `StdMsgs.Msg.String`."""
    subfolder = pascal_case(interface_path.parent.name)
    return '.'.join([package_module_name(package_name), subfolder,
                     interface_path.stem])


def lean_namespace(package_name, interface_path):
    """Return the namespace an interface file's declarations live in."""
    return '.'.join([package_module_name(package_name),
                     pascal_case(interface_path.parent.name)])


def lean_type_name(namespaced_type):
    """Return the fully qualified Lean name of a generated structure."""
    package_name, subfolder = namespaced_type.namespaces[:2]
    return '.'.join([package_module_name(package_name), pascal_case(subfolder),
                     namespaced_type.name])


def lean_module_of(namespaced_type):
    """Return the module holding a type; one per .idl file, so suffixes come off."""
    package_name, subfolder = namespaced_type.namespaces[:2]
    stem = namespaced_type.name
    for suffix in INTERFACE_SUFFIXES:
        if stem.endswith(suffix) and len(stem) > len(suffix):
            stem = stem[:-len(suffix)]
            break
    return '.'.join([package_module_name(package_name), pascal_case(subfolder),
                     stem])


def is_plain_ident(name):
    """Return whether Lean reads this as a plain atomic identifier."""
    if not name or not (name[0].isalpha() or name[0] == '_'):
        return False
    return all(c.isalnum() or c in "_'" for c in name)


def escape_lean_ident(name):
    """Guillemet-quote an identifier Lean would not accept bare."""
    if is_plain_ident(name) and name not in LEAN_TOKENS:
        return name
    return '«%s»' % name


def c_type_name(namespaced_type):
    """Return the rosidl C struct name, e.g. `std_msgs__msg__String`."""
    return '__'.join(namespaced_type.namespaced_name())


def c_include_base(package_name, interface_path):
    """Return the `<pkg>/<sub>/detail/<snake>` prefix of an .idl file's headers."""
    parts = [package_name] + list(interface_path.parent.parts)
    return '/'.join(parts + [
        'detail',
        convert_camel_case_to_lower_case_underscore(interface_path.stem)])


# The AST, flattened


def messages_of(content):
    """Return every message an .idl file yields, in an order that resolves names.

    A message that names another from the same file comes after it, which the
    Lean modules need: a structure cannot refer forward.
    """
    messages = list(content.get_elements_of_type(Message))
    for service in content.get_elements_of_type(Service):
        messages += messages_of_service(service)
    for action in content.get_elements_of_type(Action):
        messages += [action.goal, action.result, action.feedback]
        messages += messages_of_service(action.send_goal_service)
        messages += messages_of_service(action.get_result_service)
        messages.append(action.feedback_message)
    return messages


def messages_of_service(service):
    """Return the three messages a service definition yields."""
    return [service.request_message, service.response_message,
            service.event_message]


def members_of(message):
    """Return the members a Lean structure carries.

    rosidl gives an otherwise empty message a placeholder byte so its C struct
    has a member; the Lean structure stays empty and the C sets it to zero.
    """
    if is_empty_message(message):
        return []
    return list(message.structure.members)


def is_empty_message(message):
    """Return whether a message holds nothing but rosidl's placeholder member."""
    members = message.structure.members
    return (len(members) == 1 and
            members[0].name == EMPTY_STRUCTURE_REQUIRED_MEMBER_NAME)


def nested_types_of(message):
    """Return the nested message types a message names, each once."""
    found = []
    for member in message.structure.members:
        type_ = member.type
        if isinstance(type_, AbstractNestedType):
            type_ = type_.value_type
        if isinstance(type_, NamespacedType):
            if c_type_name(type_) not in [c_type_name(t) for t in found]:
                found.append(type_)
    return found


def imported_modules(content, own_module):
    """Return the modules an interface file's Lean module imports."""
    modules = set()
    for message in messages_of(content):
        for type_ in nested_types_of(message):
            module = lean_module_of(type_)
            if module != own_module:
                modules.add(module)
    return sorted(modules)


# Lean types


def is_byte_like(type_):
    """Return whether a sequence of this element type is packed into bytes."""
    return isinstance(type_, BasicType) and type_.typename in BYTE_LIKE_IDL_TYPES


def is_bounded_string(type_):
    """Return whether a string type carries its bound in the Lean type."""
    return isinstance(type_, (BoundedString, BoundedWString))


def utf16_length_name(message):
    """Return the per-message helper counting UTF-16 code units of a `wstring`."""
    return '%s.utf16Length' % message.structure.namespaced_type.name


def string_bound_predicate(message, type_, subject):
    """Return the Lean proposition a bounded string of this type satisfies."""
    if isinstance(type_, BoundedWString):
        return '%s %s ≤ %d' % (
            utf16_length_name(message), subject, type_.maximum_size)
    return '%s.utf8ByteSize ≤ %d' % (subject, type_.maximum_size)


def lean_element_type(message, type_):
    """Return the Lean type of one element of a field."""
    if isinstance(type_, NamespacedType):
        return lean_type_name(type_)
    if is_bounded_string(type_):
        return '{ s : _root_.String // %s }' % string_bound_predicate(
            message, type_, 's')
    if isinstance(type_, AbstractGenericString):
        return '_root_.String'
    assert isinstance(type_, BasicType), str(type_)
    return BASIC_IDL_TYPES_TO_LEAN[type_.typename]


def lean_field_type(message, type_):
    """Return the Lean type of a field; sizes stated in the .msg are in the type."""
    if not isinstance(type_, AbstractNestedType):
        return lean_element_type(message, type_)
    value_type = type_.value_type
    element = lean_element_type(message, value_type)
    if isinstance(type_, Array):
        if is_byte_like(value_type):
            return '{ b : _root_.ByteArray // b.size = %d }' % type_.size
        return '_root_.Vector %s %d' % (element, type_.size)
    if isinstance(type_, BoundedSequence):
        if is_byte_like(value_type):
            return '{ b : _root_.ByteArray // b.size ≤ %d }' % type_.maximum_size
        return '{ a : _root_.Array %s // a.size ≤ %d }' % (
            element, type_.maximum_size)
    if is_byte_like(value_type):
        return '_root_.ByteArray'
    return '_root_.Array %s' % element


def lean_accessor_type(message, type_):
    """Return the plain FFI type a field is read as, with no bound proofs."""
    if not isinstance(type_, AbstractNestedType):
        if isinstance(type_, AbstractGenericString):
            return '_root_.String'
        return lean_element_type(message, type_)
    value_type = type_.value_type
    if is_byte_like(value_type):
        return '_root_.ByteArray'
    if isinstance(value_type, AbstractGenericString):
        return '_root_.Array _root_.String'
    return '_root_.Array %s' % lean_element_type(message, value_type)


def lean_accessor_expr(type_, expr):
    """Read a field out of a message as its plain FFI type."""
    if not isinstance(type_, AbstractNestedType):
        return expr + '.val' if is_bounded_string(type_) else expr
    value_type = type_.value_type
    if isinstance(type_, Array):
        expr += '.val' if is_byte_like(value_type) else '.toArray'
    elif isinstance(type_, BoundedSequence):
        expr += '.val'
    if is_bounded_string(value_type):
        return '%s.map (·.val)' % expr
    return expr


def lean_constructor_lines(message, member):
    """Return the statements checking one constructor argument against its bounds.

    Each is a `let` rebinding the argument, so the structure is built from the
    names the signature declares.
    """
    name = escape_lean_ident(member.name)
    type_ = member.type
    interface = ros_interface_name(message)
    lines = []
    if isinstance(type_, AbstractNestedType) and is_bounded_string(type_.value_type):
        element = lean_element_type(message, type_.value_type)
        lines += [
            '  let %s ← %s.mapM fun x =>' % (name, name),
            '    if h : %s then' % string_bound_predicate(
                message, type_.value_type, 'x'),
            '      pure (⟨x, h⟩ : %s)' % element,
            '    else throw (IO.userError',
            '      "%s: an element of field \'%s\' %s")' % (
                interface, member.name, bound_message(type_.value_type)),
        ]
    check = lean_bound_check(message, type_, name)
    if check is not None:
        condition, target = check
        lines += [
            '  let %s ← if h : %s then' % (name, condition),
            '      pure (⟨%s, h⟩ : %s)' % (name, target),
            '    else throw (IO.userError',
            '      "%s: field \'%s\' %s")' % (
                interface, member.name, bound_message(type_)),
        ]
    return lines


def lean_bound_check(message, type_, name):
    """Return the runtime condition and target type of a field's bound, if any."""
    if not isinstance(type_, AbstractNestedType):
        if is_bounded_string(type_):
            return (string_bound_predicate(message, type_, name),
                    lean_element_type(message, type_))
        return None
    target = lean_field_type(message, type_)
    if isinstance(type_, Array):
        return ('%s.size = %d' % (name, type_.size), target)
    if isinstance(type_, BoundedSequence):
        return ('%s.size ≤ %d' % (name, type_.maximum_size), target)
    return None


def bound_message(type_):
    """Return how a violated bound reads in the exception the constructor throws."""
    if isinstance(type_, BoundedWString):
        return 'is longer than %d UTF-16 code units' % type_.maximum_size
    if isinstance(type_, BoundedString):
        return 'is longer than %d bytes' % type_.maximum_size
    if isinstance(type_, Array):
        unit = 'bytes' if is_byte_like(type_.value_type) else 'elements'
        return 'needs exactly %d %s' % (type_.size, unit)
    if isinstance(type_, BoundedSequence):
        unit = 'bytes' if is_byte_like(type_.value_type) else 'elements'
        return 'holds more than %d %s' % (type_.maximum_size, unit)
    return 'is out of bounds'


def ros_interface_name(message):
    """Return the ROS name of a message, e.g. `std_msgs/msg/String`."""
    return '/'.join(message.structure.namespaced_type.namespaced_name())


# Lean literals


def lean_default(message, member):
    """Return the field's default: the one the definition states, or the ROS zero."""
    if member.has_annotation('default'):
        value = member.get_annotation_value('default')['value']
        return lean_value(message, member.type, value)
    return lean_zero(message, member.type)


def lean_zero(message, type_):
    """Return the ROS zero value of a field, as Lean source."""
    if not isinstance(type_, AbstractNestedType):
        return lean_element_zero(message, type_)
    value_type = type_.value_type
    if isinstance(type_, Array):
        if is_byte_like(value_type):
            return ('⟨_root_.ByteArray.mk (Array.replicate %d 0), '
                    'by simp [ByteArray.size]⟩' % type_.size)
        return '_root_.Vector.replicate %d %s' % (
            type_.size, lean_element_zero(message, value_type))
    if isinstance(type_, BoundedSequence):
        if is_byte_like(value_type):
            return ('⟨_root_.ByteArray.empty, '
                    'by simp [ByteArray.size]⟩')
        return '⟨#[], by simp⟩'
    if is_byte_like(value_type):
        return '_root_.ByteArray.empty'
    return '#[]'


def lean_element_zero(message, type_):
    """Return the ROS zero value of one element."""
    if isinstance(type_, NamespacedType):
        return '{}'
    if isinstance(type_, BoundedWString):
        # `utf16Length` folds over the characters, so `decide` settles it while
        # `simp` has nothing to rewrite with.
        return '⟨"", by decide⟩'
    if isinstance(type_, BoundedString):
        return '⟨"", by simp⟩'
    if isinstance(type_, AbstractGenericString):
        return '""'
    assert isinstance(type_, BasicType), str(type_)
    if type_.typename == 'boolean':
        return 'false'
    if type_.typename in FLOATING_POINT_TYPES:
        return '0.0'
    return '0'


def lean_value(message, type_, value):
    """Return a default stated in the definition, as Lean source."""
    if not isinstance(type_, AbstractNestedType):
        return lean_element_value(message, type_, value)
    value_type = type_.value_type
    value = literal_eval(value)
    if is_byte_like(value_type):
        literal = '_root_.ByteArray.mk #[%s]' % ', '.join(
            str(int(v)) for v in value)
    else:
        literal = '#[%s]' % ', '.join(
            lean_element_value(message, value_type, v) for v in value)
    if isinstance(type_, Array):
        if is_byte_like(value_type):
            return '⟨%s, by simp [ByteArray.size]⟩' % literal
        return '⟨%s, by decide⟩' % literal
    if isinstance(type_, BoundedSequence):
        if is_byte_like(value_type):
            return '⟨%s, by simp [ByteArray.size]⟩' % literal
        return '⟨%s, by decide⟩' % literal
    return literal


def lean_element_value(message, type_, value):
    """Return one primitive value, as Lean source."""
    if isinstance(type_, AbstractGenericString):
        literal = lean_string_literal(value)
        if is_bounded_string(type_):
            return '⟨%s, by decide⟩' % literal
        return literal
    assert isinstance(type_, BasicType), str(type_)
    if type_.typename == 'boolean':
        return 'true' if value else 'false'
    if type_.typename in FLOATING_POINT_TYPES:
        return lean_float_literal(value)
    return str(int(value))


def lean_string_literal(value):
    """Return a Lean string literal, with the escapes Lean's lexer wants."""
    out = ['"']
    for char in str(value):
        if char in '\\"':
            out.append('\\' + char)
        elif char == '\n':
            out.append('\\n')
        elif char == '\r':
            out.append('\\r')
        elif char == '\t':
            out.append('\\t')
        elif ord(char) < 0x20 or ord(char) == 0x7f:
            out.append('\\x%02x' % ord(char))
        else:
            out.append(char)
    out.append('"')
    return ''.join(out)


def lean_float_literal(value):
    """Return a Lean float literal.

    Lean's lexer wants a digit either side of the point and rejects `1e-3`;
    `inf` and `nan` have no literal and become the quotients that produce them.
    """
    text = repr(float(value))
    if text in ('inf', '-inf'):
        return '(%s1.0 / 0.0)' % ('-' if text.startswith('-') else '')
    if text == 'nan':
        return '(0.0 / 0.0)'
    mantissa, _, exponent = text.partition('e')
    if '.' not in mantissa:
        mantissa += '.0'
    return mantissa + ('e' + exponent if exponent else '')


def constant_value_to_lean(type_, value):
    """Return a constant's value as Lean source; a bounded string loses its bound."""
    if isinstance(type_, AbstractGenericString):
        return lean_string_literal(value)
    assert isinstance(type_, BasicType), str(type_)
    if type_.typename == 'boolean':
        return 'true' if value else 'false'
    if type_.typename in FLOATING_POINT_TYPES:
        return lean_float_literal(value)
    return str(int(value))


def constant_type_to_lean(type_):
    """Return a constant's Lean type."""
    if isinstance(type_, AbstractGenericString):
        return '_root_.String'
    return BASIC_IDL_TYPES_TO_LEAN[type_.typename]


# C at the boundary


def lean_c_type(message, type_):
    """Return the C type a field crosses the FFI boundary as."""
    if isinstance(type_, (AbstractNestedType, AbstractGenericString)):
        return 'lean_object *'
    typename = scalar_type_typename(type_)
    if typename is None:
        return 'lean_object *'
    return BASIC_IDL_TYPES_TO_LEAN_C[typename]


def c_self_type(message):
    """Return the C type the message itself has in its accessors."""
    typename = scalar_message_typename(message)
    if typename is None:
        return 'lean_object *'
    return BASIC_IDL_TYPES_TO_LEAN_C[typename]


def c_value_type(type_):
    """Return the rosidl C type of a scalar or of one sequence element."""
    from rosidl_generator_c import BASIC_IDL_TYPES_TO_C
    if isinstance(type_, AbstractString):
        return 'rosidl_runtime_c__String'
    if isinstance(type_, AbstractWString):
        return 'rosidl_runtime_c__U16String'
    if isinstance(type_, NamespacedType):
        return c_type_name(type_)
    return BASIC_IDL_TYPES_TO_C[type_.typename]


def c_sequence_type(type_):
    """Return the rosidl C sequence type of an element type."""
    if isinstance(type_, AbstractString):
        return 'rosidl_runtime_c__String'
    if isinstance(type_, AbstractWString):
        return 'rosidl_runtime_c__U16String'
    if isinstance(type_, NamespacedType):
        return c_type_name(type_)
    return 'rosidl_runtime_c__' + type_.typename


def c_box(type_, expr):
    """Return one scalar boxed as a Lean array element."""
    return c_box_typename(type_.typename, expr)


def c_unbox(type_, expr):
    """Return one Lean array element unboxed as a scalar."""
    return c_unbox_typename(type_.typename, expr)


def c_box_typename(typename, expr):
    """Return one scalar of this IDL type, boxed."""
    return '%s%s)' % (BASIC_IDL_TYPES_TO_LEAN_BOX[typename][0], expr)


def c_unbox_typename(typename, expr):
    """Return one boxed value of this IDL type, unboxed."""
    return '%s%s)' % (BASIC_IDL_TYPES_TO_LEAN_BOX[typename][1], expr)


def c_to_lean_scalar(type_, expr):
    """Return a scalar from the C struct, cast to what the Lean side takes."""
    if type_.typename == 'boolean':
        return '(uint8_t)(%s ? 1 : 0)' % expr
    return '(%s)%s' % (BASIC_IDL_TYPES_TO_LEAN_C[type_.typename], expr)


def c_from_lean_scalar(type_, expr):
    """Return a scalar handed over by Lean, cast to what the C struct holds."""
    if type_.typename == 'boolean':
        return '(%s != 0)' % expr
    return '(%s)%s' % (c_value_type(type_), expr)


def has_wstring(message):
    """Return whether any member of a message is or holds a wstring."""
    for member in message.structure.members:
        type_ = member.type
        if isinstance(type_, AbstractNestedType):
            type_ = type_.value_type
        if isinstance(type_, AbstractWString):
            return True
    return False


def sequence_headers(message):
    """Return the rosidl_runtime_c headers a message's members need."""
    headers = []
    for member in message.structure.members:
        type_ = member.type
        if isinstance(type_, AbstractNestedType):
            type_ = type_.value_type
            headers += ['rosidl_runtime_c/primitives_sequence.h',
                        'rosidl_runtime_c/primitives_sequence_functions.h']
        if isinstance(type_, AbstractString):
            headers += ['rosidl_runtime_c/string.h',
                        'rosidl_runtime_c/string_functions.h']
        if isinstance(type_, AbstractWString):
            headers += ['rosidl_runtime_c/u16string.h',
                        'rosidl_runtime_c/u16string_functions.h']
    ordered = []
    for header in headers:
        if header not in ordered:
            ordered.append(header)
    return ordered


def is_sequence(type_):
    """Return whether a nested type is a sequence rather than a fixed array."""
    return isinstance(type_, AbstractSequence)


def c_file_include_base(namespaced_type):
    """Return the header prefix of the .idl file a generated type came from."""
    package_name, subfolder = namespaced_type.namespaces[:2]
    stem = namespaced_type.name
    if subfolder in ('srv', 'action'):
        for suffix in INTERFACE_SUFFIXES:
            if stem.endswith(suffix) and len(stem) > len(suffix):
                stem = stem[:-len(suffix)]
                break
    return '/'.join([package_name, subfolder, 'detail',
                     convert_camel_case_to_lower_case_underscore(stem)])


def c_accessor_name(message, member):
    """Return the C symbol a field's accessor exports."""
    typename = c_type_name(message.structure.namespaced_type)
    if member.name in RESERVED_C_ACCESSORS:
        return '%s__get_field_%s' % (typename, member.name)
    return '%s__get_%s' % (typename, member.name)


def c_from_lean_lines(message):
    """Return the body of `<msg>__from_lean`, filling the struct from Lean."""
    if is_empty_message(message):
        return ['  (void)lean_message;',
                '  ros_message->%s = 0;' % message.structure.members[0].name]
    lines = []
    for member in message.structure.members:
        lines.append('  {  // %s' % member.name)
        lines += ['    ' + line for line in _from_lean_member(message, member)]
        lines.append('  }')
    return lines


def _from_lean_member(message, member):
    """Fill one struct member from the exported accessor."""
    getter = c_accessor_name(message, member)
    field = 'ros_message->%s' % member.name
    type_ = member.type
    # A message represented by a scalar arrives boxed, since rcllean's externs
    # are polymorphic, and its accessor takes that scalar rather than a pointer.
    self_typename = scalar_message_typename(message)
    if self_typename is None:
        lines = ['lean_inc(lean_message);']
        call = '%s(lean_message)' % getter
    else:
        lines = []
        call = '%s(%s)' % (
            getter, c_unbox_typename(self_typename, 'lean_message'))
    if isinstance(type_, BasicType):
        lines.append('%s = %s;' % (field, c_from_lean_scalar(type_, call)))
        return lines
    nested_typename = scalar_type_typename(type_)
    if nested_typename is not None:
        # The nested message is a scalar too; its own from_lean takes it boxed.
        lines.append('lean_object * field = %s;' % c_box_typename(
            nested_typename, call))
    else:
        lines.append('lean_object * field = %s;' % call)
    if isinstance(type_, (AbstractGenericString, NamespacedType)):
        lines += _from_lean_scalar_object(type_, field, 'field')
        lines.append('lean_dec(field);')
        lines += ['if (!ok) {', '  return false;', '}']
        return lines
    value_type = type_.value_type
    if is_byte_like(value_type):
        lines.append('size_t size = lean_sarray_size(field);')
        if isinstance(type_, Array):
            lines += ['if (size != %d) {' % type_.size,
                      '  lean_dec(field);',
                      '  return false;',
                      '}',
                      'memcpy(%s, lean_sarray_cptr(field), size);' % field]
        else:
            lines += ['if (!%s__Sequence__init(&%s, size)) {' % (
                          c_sequence_type(value_type), field),
                      '  lean_dec(field);',
                      '  return false;',
                      '}',
                      'if (size > 0) {',
                      '  memcpy(%s.data, lean_sarray_cptr(field), size);' % field,
                      '}']
        lines.append('lean_dec(field);')
        return lines
    lines.append('size_t size = lean_array_size(field);')
    if isinstance(type_, Array):
        lines += ['if (size != %d) {' % type_.size,
                  '  lean_dec(field);',
                  '  return false;',
                  '}']
        destination = field
    else:
        lines += ['if (!%s__Sequence__init(&%s, size)) {' % (
                      c_sequence_type(value_type), field),
                  '  lean_dec(field);',
                  '  return false;',
                  '}']
        destination = field + '.data'
    lines += ['%s * dest = %s;' % (c_value_type(value_type), destination),
              'lean_object * const * items = lean_array_cptr(field);',
              'for (size_t i = 0; i < size; ++i) {']
    if isinstance(value_type, BasicType):
        lines.append('  dest[i] = %s;' % c_from_lean_scalar(
            value_type, c_unbox(value_type, 'items[i]')))
    else:
        lines += ['  ' + line
                  for line in _from_lean_scalar_object(
                      value_type, 'dest[i]', 'items[i]')]
        lines += ['  if (!ok) {',
                  '    lean_dec(field);',
                  '    return false;',
                  '  }']
    lines += ['}', 'lean_dec(field);']
    return lines


def _from_lean_scalar_object(type_, destination, source):
    """Fill one string, wstring or nested message, leaving `ok` in scope."""
    if isinstance(type_, AbstractWString):
        return ['bool ok = rosidl_generator_lean__assign_u16string(',
                '  &%s, lean_string_cstr(%s), lean_string_size(%s) - 1);' % (
                    destination, source, source)]
    if isinstance(type_, AbstractGenericString):
        return ['bool ok = rosidl_runtime_c__String__assignn(',
                '  &%s, lean_string_cstr(%s), lean_string_size(%s) - 1);' % (
                    destination, source, source)]
    return ['bool ok = %s__from_lean(%s, &%s);' % (
        c_type_name(type_), source, destination)]


def c_to_lean_lines(message):
    """Return the body of `<msg>__to_lean`, which calls the constructor."""
    typename = c_type_name(message.structure.namespaced_type)
    if is_empty_message(message):
        return ['  (void)ros_message;', '  return %s__mk();' % typename]
    lines = []
    arguments = []
    for member in message.structure.members:
        block, argument = _to_lean_member(member)
        lines += block
        arguments.append(argument)
    lines.append('  return %s__mk(%s);' % (typename, ', '.join(arguments)))
    return lines


def _to_lean_member(member):
    """Build one constructor argument, returning its lines and the expression."""
    field = 'ros_message->%s' % member.name
    name = 'lf_%s' % member.name
    type_ = member.type
    if isinstance(type_, BasicType):
        return [], c_to_lean_scalar(type_, field)
    if isinstance(type_, (AbstractGenericString, NamespacedType)):
        lines, expression = _to_lean_scalar_object(type_, field, name)
        return ['  ' + line for line in lines], expression
    value_type = type_.value_type
    if isinstance(type_, Array):
        size, source = str(type_.size), field
    else:
        size, source = field + '.size', field + '.data'
    lines = ['size_t %s_size = %s;' % (name, size)]
    if is_byte_like(value_type):
        lines += ['lean_object * %s = lean_alloc_sarray(1, %s_size, %s_size);' % (
                      name, name, name),
                  'if (%s_size > 0) {' % name,
                  '  memcpy(lean_sarray_cptr(%s), %s, %s_size);' % (
                      name, source, name),
                  '}']
        return ['  ' + line for line in lines], name
    lines += ['const %s * %s_src = %s;' % (c_value_type(value_type), name, source),
              'lean_object * %s = lean_mk_empty_array_with_capacity('
              'lean_box(%s_size));' % (name, name),
              'for (size_t %s_i = 0; %s_i < %s_size; ++%s_i) {' % (
                  name, name, name, name)]
    element = '%s_src[%s_i]' % (name, name)
    if isinstance(value_type, BasicType):
        lines.append('  %s = lean_array_push(%s, %s);' % (
            name, name, c_box(value_type, element)))
    elif isinstance(value_type, NamespacedType):
        lines += ['  lean_object * %s_item = %s__to_lean(&%s);' % (
                      name, c_type_name(value_type), element),
                  '  if (!lean_io_result_is_ok(%s_item)) {' % name,
                  '    lean_dec(%s);' % name,
                  '    return %s_item;' % name,
                  '  }',
                  '  %s = lean_array_push(%s, lean_io_result_take_value(%s_item));' % (
                      name, name, name)]
    else:
        lines.append('  %s = lean_array_push(%s, %s);' % (
            name, name, _to_lean_string_expr(value_type, element)))
    lines.append('}')
    return ['  ' + line for line in lines], name


def _to_lean_scalar_object(type_, field, name):
    """Build one string, wstring or nested message value."""
    if isinstance(type_, NamespacedType):
        lines = [
            'lean_object * %s_result = %s__to_lean(&%s);' % (
                name, c_type_name(type_), field),
            'if (!lean_io_result_is_ok(%s_result)) {' % name,
            '  return %s_result;' % name,
            '}',
            'lean_object * %s_value = lean_io_result_take_value(%s_result);' % (
                name, name),
        ]
        typename = nested_scalar_typename(type_)
        if typename is None:
            lines.append('lean_object * %s = %s_value;' % (name, name))
            return lines, name
        # The nested message is a scalar, so the constructor takes it unboxed.
        lines += [
            '%s %s = %s;' % (BASIC_IDL_TYPES_TO_LEAN_C[typename], name,
                             c_unbox_typename(typename, '%s_value' % name)),
            'lean_dec(%s_value);' % name,
        ]
        return lines, name
    return (['lean_object * %s = %s;' % (
        name, _to_lean_string_expr(type_, field))], name)


def _to_lean_string_expr(type_, field):
    """Return one string or wstring as a Lean string."""
    if isinstance(type_, AbstractWString):
        return 'rosidl_generator_lean__u16string_to_lean(&%s)' % field
    return ('lean_mk_string_from_bytes(%s.data ? %s.data : "", %s.size)'
            % (field, field, field))


def has_byte_arrays(content):
    """Return whether any message in an .idl file carries a `ByteArray` field."""
    for message in messages_of(content):
        for member in message.structure.members:
            if isinstance(member.type, AbstractNestedType) and \
                    is_byte_like(member.type.value_type):
                return True
    return False


def has_wstrings(content):
    """Return whether any message in an .idl file carries a wstring."""
    for message in messages_of(content):
        if has_wstring(message):
            return True
    return False


def has_bounded_wstring(message):
    """Return whether a message needs the per-message UTF-16 length helper."""
    for member in message.structure.members:
        type_ = member.type
        if isinstance(type_, AbstractNestedType):
            type_ = type_.value_type
        if isinstance(type_, BoundedWString):
            return True
    return False


def lean_constructor_signature(message):
    """Return the constructor's parameters, one per field, in plain FFI types."""
    parts = []
    for member in members_of(message):
        parts.append(' (%s : %s)' % (escape_lean_ident(member.name),
                                     lean_accessor_type(message, member.type)))
    return ''.join(parts)


def lean_structure_literal(message):
    """Return the structure instance the constructor returns."""
    parts = []
    for member in members_of(message):
        name = escape_lean_ident(member.name)
        parts.append('%s := %s' % (name, name))
    return '{ %s }' % ', '.join(parts) if parts else '{}'


def lean_constructor_checks(message):
    """Return every bound check the constructor runs, in field order."""
    lines = []
    for member in members_of(message):
        lines += lean_constructor_lines(message, member)
    return lines


def c_constructor_args(message):
    """Return the exported constructor's parameter types, for its C prototype."""
    parts = []
    for member in members_of(message):
        parts.append(lean_c_type(message, member.type))
    return ', '.join(parts) or 'void'


def c_nested_declarations(message, declared):
    """Nested types needing a local prototype, marking them as declared."""
    names = []
    for nested_type in nested_types_of(message):
        name = c_type_name(nested_type)
        if name not in declared:
            declared.add(name)
            names.append(name)
    declared.add(c_type_name(message.structure.namespaced_type))
    return names


def c_nested_headers(content, include_base):
    """Return the `__functions.h` headers of nested types from other .idl files."""
    headers = []
    own = include_base + '__functions.h'
    for message in messages_of(content):
        for nested_type in nested_types_of(message):
            header = c_file_include_base(nested_type) + '__functions.h'
            if header != own and header not in headers:
                headers.append(header)
    return sorted(headers)


def c_sequence_headers(content):
    """Return the rosidl_runtime_c headers every message in an .idl file needs."""
    headers = []
    for message in messages_of(content):
        for header in sequence_headers(message):
            if header not in headers:
                headers.append(header)
    return headers
