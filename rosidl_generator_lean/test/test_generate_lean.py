"""Expand the templates over real interface definitions and read the output."""

import pathlib

from rosidl_generator_lean.generate_lean_impl import c_accessor_name
from rosidl_generator_lean.generate_lean_impl import c_type_name
from rosidl_generator_lean.generate_lean_impl import file_module_name
from rosidl_generator_lean.generate_lean_impl import members_of
from rosidl_generator_lean.generate_lean_impl import messages_of
from rosidl_generator_lean.generate_lean_impl import package_module_name

from rosidl_parser.definition import IdlLocator
from rosidl_parser.parser import parse_idl_file


def read(output_dir, *parts):
    path = output_dir.joinpath(*parts)
    assert path.is_file(), '%s was not generated' % path
    return path.read_text()


def test_root_module_imports_every_interface(generated):
    package_name, idl_tuples, output_dir = generated
    root = read(output_dir, package_module_name(package_name) + '.lean')
    for idl_tuple in idl_tuples:
        relative = pathlib.Path(idl_tuple.rsplit(':', 1)[1])
        module = file_module_name(package_name, relative)
        assert 'import %s\n' % module in root


def test_lakefile_requires_the_runtime(generated):
    _, _, output_dir = generated
    lakefile = read(output_dir, 'lakefile.lean')
    assert 'require rosidl_runtime_lean from envVar ' \
        '"AMENT_LEAN_PKG_ROSIDL_RUNTIME_LEAN"' in lakefile
    assert 'target leanC pkg : FilePath' in lakefile


def test_every_field_is_reachable_from_c(generated):
    package_name, idl_tuples, output_dir = generated
    for idl_tuple in idl_tuples:
        relative = pathlib.Path(idl_tuple.rsplit(':', 1)[1])
        module = file_module_name(package_name, relative)
        lean = read(output_dir, *(module.split('.')[:-1] +
                                  [module.split('.')[-1] + '.lean']))
        content = parse_idl_file(IdlLocator(*idl_tuple.rsplit(':', 1))).content
        for message in messages_of(content):
            name = message.structure.namespaced_type.name
            symbol = c_type_name(message.structure.namespaced_type)
            assert 'structure %s where' % name in lean
            assert '@[extern "%s__lean_type_support"]' % symbol in lean
            assert 'RosidlRuntimeLean.RosMessage %s' % name in lean
            assert '@[export %s__mk]' % symbol in lean
            for member in members_of(message):
                assert '@[export %s__get_%s]' % (symbol, member.name) in lean
                assert 'def %s.get_%s ' % (name, member.name) in lean


def test_c_defines_the_record_and_calls_the_accessors(generated):
    package_name, idl_tuples, output_dir = generated
    for idl_tuple in idl_tuples:
        relative = pathlib.Path(idl_tuple.rsplit(':', 1)[1])
        from rosidl_pycommon import convert_camel_case_to_lower_case_underscore
        stem = convert_camel_case_to_lower_case_underscore(relative.stem)
        source = read(output_dir, relative.parent.name, '_%s_s.c' % stem)
        content = parse_idl_file(IdlLocator(*idl_tuple.rsplit(':', 1))).content
        for message in messages_of(content):
            symbol = c_type_name(message.structure.namespaced_type)
            assert 'bool %s__from_lean(' % symbol in source
            assert 'lean_obj_res %s__to_lean(' % symbol in source
            assert '%s__lean_type_support(void)' % symbol in source
            assert 'sizeof(%s)' % symbol in source
            for member in members_of(message):
                # A message that is a Lean trivial structure hands the
                # accessor the unboxed scalar, not `lean_message`.
                assert '%s(' % c_accessor_name(message, member) in source


def test_services_and_actions_carry_their_own_record(generated):
    package_name, idl_tuples, output_dir = generated
    from rosidl_parser.definition import Action
    from rosidl_parser.definition import Service
    for idl_tuple in idl_tuples:
        relative = pathlib.Path(idl_tuple.rsplit(':', 1)[1])
        module = file_module_name(package_name, relative)
        lean = read(output_dir, *(module.split('.')[:-1] +
                                  [module.split('.')[-1] + '.lean']))
        content = parse_idl_file(IdlLocator(*idl_tuple.rsplit(':', 1))).content
        for service in content.get_elements_of_type(Service):
            name = service.namespaced_type.name
            assert 'RosidlRuntimeLean.RosService %s where' % name in lean
        for action in content.get_elements_of_type(Action):
            name = action.namespaced_type.name
            assert 'RosidlRuntimeLean.RosAction %s where' % name in lean
