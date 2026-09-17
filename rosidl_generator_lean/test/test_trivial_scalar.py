"""A message with one scalar field is a Lean trivial structure.

Its runtime value is the field, so `@[export]` compiles the accessor and the
constructor against the unboxed scalar rather than a `lean_object *`.  Getting
that wrong puts a pointer on the wire, so the generated C is read back here.
"""

import pytest

PACKAGE = 'trivial_scalar_msgs'

# The C type and the boxing each scalar crosses a polymorphic boundary with.
SCALARS = {
    'OneInt64': ('int64', 'uint64_t', 'lean_unbox_uint64', 'lean_box_uint64'),
    'OneFloat64': ('float64', 'double', 'lean_unbox_float', 'lean_box_float'),
    'OneBool': ('bool', 'uint8_t', 'lean_unbox', 'lean_box'),
    'OneInt8': ('int8', 'uint8_t', 'lean_unbox', 'lean_box'),
}


def read_c(output_dir, stem):
    path = output_dir / 'msg' / ('_%s_s.c' % stem)
    assert path.is_file(), '%s was not generated' % path
    return path.read_text()


@pytest.mark.parametrize('name', sorted(SCALARS))
def test_scalar_message_crosses_unboxed(trivial_generated, name):
    _, c_type, unbox, _ = SCALARS[name]
    source = read_c(trivial_generated, {
        'OneInt64': 'one_int64', 'OneFloat64': 'one_float64',
        'OneBool': 'one_bool', 'OneInt8': 'one_int8'}[name])
    symbol = '%s__msg__%s' % (PACKAGE, name)
    # The accessor takes the message, which is the scalar itself.
    assert '%s %s__get_value(%s);' % (c_type, symbol, c_type) in source
    assert 'lean_object * %s__mk(%s);' % (symbol, c_type) in source
    # rcllean's externs are polymorphic, so the value arrives boxed.
    assert '%s(lean_message)' % unbox in source
    assert 'lean_inc(lean_message);' not in source


def test_nested_scalar_message_is_boxed_at_the_seam(trivial_generated):
    source = read_c(trivial_generated, 'wrapper')
    symbol = '%s__msg__Wrapper' % PACKAGE
    nested = '%s__msg__OneInt64' % PACKAGE
    # Wrapper holds two fields, so Wrapper itself stays an object.
    assert 'uint64_t %s__get_inner(lean_object *);' % symbol in source
    assert 'lean_object * %s__get_label(lean_object *);' % symbol in source
    assert 'lean_object * %s__mk(uint64_t, lean_object *);' % symbol in source
    # The nested conversions keep the fixed record signature, so the scalar is
    # boxed on the way in and unboxed on the way out.
    assert 'lean_box_uint64(%s__get_inner(lean_message))' % symbol in source
    assert '%s__from_lean(field, &ros_message->inner)' % nested in source
    assert 'uint64_t lf_inner = lean_unbox_uint64(lf_inner_value);' in source


def test_lean_side_is_unchanged(trivial_generated):
    lean = (trivial_generated / 'TrivialScalarMsgs' / 'Msg' / 'OneInt64.lean').read_text()
    assert 'def OneInt64.get_value (m : OneInt64) : _root_.Int64 := m.value' \
        in lean
    assert '@[export %s__msg__OneInt64__get_value]' % PACKAGE in lean
