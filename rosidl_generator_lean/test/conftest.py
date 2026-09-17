"""Generate every fixture package once, in one uninterrupted step.

EmPy installs a proxy over `sys.stdout` and looks for it again when it shuts an
interpreter down.  pytest swaps stdout between modules, so generating from two
module-scoped fixtures loses the proxy; one session-scoped fixture does not.
"""

import json
import pathlib

from ament_index_python import get_package_share_directory
from ament_index_python import PackageNotFoundError

import pytest

from rosidl_adapter.action import convert_action_to_idl
from rosidl_adapter.msg import convert_msg_to_idl
from rosidl_adapter.srv import convert_srv_to_idl

from rosidl_generator_lean import generate_lean

CONVERTERS = {
    '.msg': convert_msg_to_idl,
    '.srv': convert_srv_to_idl,
    '.action': convert_action_to_idl,
}

TEMPLATE_DIR = pathlib.Path(__file__).parent.parent / 'resource'
FIXTURE_DIR = pathlib.Path(__file__).parent / 'fixtures'

TRIVIAL_SCALAR_PACKAGE = 'trivial_scalar_msgs'
INTERFACE_PACKAGE = 'fixture_interfaces'


def find_interface_fixtures():
    """Return `(package name, package directory)` to generate bindings from.

    `test_interface_files` covers every type rosidl can express and is what
    upstream tests against.  Without it, the bundled fixtures cover a nested
    message with a fixed array and a string, a service and an action.
    """
    try:
        share = pathlib.Path(get_package_share_directory('test_interface_files'))
        return 'test_interface_files', share
    except PackageNotFoundError:
        return INTERFACE_PACKAGE, FIXTURE_DIR / INTERFACE_PACKAGE


def generate(package_name, package_dir, idl_dir, output_dir):
    """Adapt a package's definitions to .idl and generate Lean bindings."""
    idl_tuples = []
    for suffix, converter in sorted(CONVERTERS.items()):
        subfolder = suffix[1:]
        for definition in sorted((package_dir / subfolder).glob('*' + suffix)):
            destination = idl_dir / subfolder
            destination.mkdir(parents=True, exist_ok=True)
            converter(package_dir, package_name,
                      definition.relative_to(package_dir), destination)
            idl_tuples.append('%s:%s/%s.idl' % (
                idl_dir, subfolder, definition.stem))

    arguments_file = output_dir / 'arguments.json'
    arguments_file.write_text(json.dumps({
        'package_name': package_name,
        'idl_tuples': idl_tuples,
        'ros_interface_dependencies': [],
        'output_dir': str(output_dir),
        'template_dir': str(TEMPLATE_DIR),
        'target_dependencies': [str(arguments_file)],
    }))
    generate_lean(str(arguments_file))
    return package_name, idl_tuples, output_dir


@pytest.fixture(scope='session')
def generated_packages(tmp_path_factory):
    """Generate the interface fixtures and the trivial-structure fixtures."""
    results = {}

    package_name, package_dir = find_interface_fixtures()
    results['interfaces'] = generate(
        package_name, package_dir,
        tmp_path_factory.mktemp('interfaces_idl'),
        tmp_path_factory.mktemp('interfaces_out'))

    results['trivial'] = generate(
        TRIVIAL_SCALAR_PACKAGE, FIXTURE_DIR / TRIVIAL_SCALAR_PACKAGE,
        tmp_path_factory.mktemp('trivial_idl'),
        tmp_path_factory.mktemp('trivial_out'))
    return results


@pytest.fixture(scope='session')
def generated(generated_packages):
    """Return the bindings generated from real interface definitions."""
    return generated_packages['interfaces']


@pytest.fixture(scope='session')
def trivial_generated(generated_packages):
    """Return the bindings generated from the trivial-structure fixtures."""
    return generated_packages['trivial'][2]
